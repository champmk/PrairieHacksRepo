"""Catalog loading: raw JSON files in, one normalized ``Catalog`` out.

Sources, in order of authority:
* ``data/grinnell_catalog.json``  real catalog data (CS and Mathematics).
  When it is missing, ``data/fixture_catalog.json`` (same shape) stands in.
* ``data/derived.json``           what we derived and the catalog does not
  state (the Mathematics route). Flagged ``derived``.
* ``data/sample_courses.json``    sample courses outside CS/Math, flagged
  ``sample``. They never override a real course.

Unknown stays unknown: an unstated offering term is ``None``, never "always",
and a prerequisite the data cannot express is marked ``prereq_known: False``.
"""
import json
import math
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REAL_FILE = "grinnell_catalog.json"
FIXTURE_FILE = "fixture_catalog.json"

# The API contract names the two majors CS and MATH.
PROGRAM_IDS = {"CSC-BA": "CS", "MAT-BA": "MATH"}
REAL_DIVISIONS = ("Humanities", "Science", "Social Studies")
SLOT_CREDITS = 4          # one requirement slot stands for one four-credit course

DEFAULT_POLICIES = {
    "graduation_credits": 124, "department_cap": 48, "division_cap": 92,
    "load_min": 12, "load_normal": 16, "load_max": 18,
    "tutorial": "TUT-100", "fye": "FYE-100", "fye_semester": 2,
    "load_exempt": ["MUS-101", "MUS-120", "MUS-122", "MUS-220", "MUS-221", "MUS-320",
                    "MUS-420", "PHE-100", "PHE-101", "FYE-100"],
}


def parse_prereq(raw):
    """Catalog prerequisite -> contract tree, plus whether it is fully known.

    The catalog file writes a course as a bare id, ``coreq:X`` for "before or
    at the same time", ``placement:...`` for a placement rule (kept as a
    consent leaf, so it is reported and never assumed), and ``varies_by_topic``
    for a prerequisite nobody can state (unknown). ``all`` / ``any`` nest.
    Returns ``(tree, known)``.
    """
    known = True

    def walk(node):
        nonlocal known
        if node is None:
            return None
        if isinstance(node, str):
            if node.startswith("coreq:"):
                return {"coreq": node[6:]}
            if node.startswith("placement:") or node == "consent":
                return {"consent": True}
            if node == "varies_by_topic" or "-" not in node:
                known = False
                return None
            return {"course": node}
        if "course" in node or "coreq" in node or "consent" in node:
            return dict(node)
        kind = "all" if "all" in node else "any"
        parts = [p for p in (walk(x) for x in node.get(kind) or []) if p]
        if not parts:
            return None
        return parts[0] if len(parts) == 1 else {kind: parts}

    return walk(raw), known


def parse_offered(raw):
    """``["Fall"]``, ``["even-year Spring"]`` ... -> ``(seasons, years)``.
    ``"Fall or Spring"`` means one of the two, not stated which: unknown."""
    seasons, years = [], None
    for entry in raw or []:
        words = str(entry).replace("-year", "").split()
        if "or" in words:
            return None, None
        for w in words:
            if w in ("Fall", "Spring") and w not in seasons:
                seasons.append(w)
            elif w in ("even", "odd"):
                years = w
    return (seasons or None), years


def _course(raw, origin, codes):
    cid = raw["id"]
    subject = cid.split("-")[0]
    code = codes.get(subject) or {}
    digits = "".join(ch for ch in cid.split("-")[-1] if ch.isdigit())
    tree, known = parse_prereq(raw.get("prereq"))
    seasons, years = parse_offered(raw.get("offered"))
    in_catalog = raw.get("catalog_status") != "not_in_catalog"
    note = raw.get("offered_catalog_note")
    if raw.get("offered") and seasons is None:
        note = " ".join(x for x in ("Term not stated (" + ", ".join(raw["offered"]) + ").", note) if x)
    cross = raw.get("cross_listed_as")
    return {
        "id": cid, "title": raw.get("title") or cid,
        "credits": raw["credits"] if raw.get("credits") is not None else SLOT_CREDITS,
        "credits_assumed": raw.get("credits") is None,
        "department": subject,
        "department_name": raw.get("department") or code.get("department") or subject,
        "division": code.get("division", raw.get("division")),
        "level": int(digits) // 100 * 100 if digits else None,
        "offered": seasons, "offered_years": years, "offered_note": note,
        "prereq_text": raw.get("prereq_text"), "prereq": tree,
        "prereq_known": known and in_catalog,
        "cross_listed": [cross] if isinstance(cross, str) else list(cross or []),
        "repeatable": raw.get("repeatable"), "sdf_only": bool(raw.get("sdf_only")),
        "source_url": raw.get("source_url"), "origin": raw.get("origin") or origin,
    }


def _closers(sequences):
    """The last course of each sequence. Taking it implies the sequence,
    because its prerequisite is the course before it."""
    out = []
    for seq in sequences:
        last = seq[-1]
        for c in (last["any"] if isinstance(last, dict) else [last]):
            if c not in out:
                out.append(c)
    return out


def build_slots(pid, program, courses):
    """Flatten a program's requirement groups into slots.

    * ``all`` group: one slot per course.
    * ``choose`` with a count: that many slots sharing the option list.
    * ``choose`` by credits (count null): credits / 4 slots; options worth
      fewer than four credits are left out (partial credit is not modeled).
    * a group with ``sequences``: one slot whose options are the closing
      course of each sequence.
    * ``choose`` with neither count nor credits ("remaining credits"): enough
      slots to reach the program's credit minimum; as many of them as the
      upper-level rule still needs are limited to 300/400-level options.

    Everything but the first two is our reading of the catalog text, so those
    slots carry ``derived: True``.
    """
    slots, remainder = [], []

    def add(sid, label, options, group, derived=False):
        # credit_bearing: the slot is part of the major's own credits. The CS "also required"
        # groups state no credits; they are cognates and may overlap with another major.
        slots.append({"id": sid, "label": label, "kind": "course" if len(options) == 1 else "choose",
                      "options": list(options), "group": group["id"], "route_term": None,
                      "credit_bearing": derived or group.get("credits_min") is not None,
                      "derived": derived})

    def add_n(group, n, options, derived, label=None):
        for k in range(1, n + 1):
            add(f"{pid}:{group['id']}" + (f":{k}" if n > 1 else ""), label or group["label"],
                options, group, derived)

    for group in program.get("requirement_groups") or []:
        if group.get("sequences"):
            add(f"{pid}:{group['id']}", group["label"], _closers(group["sequences"]), group, True)
        elif group["kind"] == "all":
            for c in group["options"]:
                add(f"{pid}:{c}", c, [c], group)
        elif group.get("count"):
            add_n(group, int(group["count"]), group["options"], False)
        elif group.get("credits_min"):
            whole = [c for c in group["options"]
                     if (courses.get(c) or {}).get("credits", SLOT_CREDITS) >= SLOT_CREDITS]
            add_n(group, math.ceil(group["credits_min"] / SLOT_CREDITS), whole, True)
        else:
            remainder.append(group)

    def is_upper(c, levels):
        return (courses.get(c) or {}).get("level") in levels

    for group in remainder:
        total = program.get("total_credits_min") or 0
        n = max(0, math.ceil((total - SLOT_CREDITS * sum(s["credit_bearing"] for s in slots)) / SLOT_CREDITS))
        rule = program.get("upper_level_rule") or {}
        levels = rule.get("levels") or []
        have_upper = sum(1 for s in slots if all(is_upper(c, levels) for c in s["options"]))
        need_upper = min(n, max(0, math.ceil(rule.get("min_credits", 0) / SLOT_CREDITS) - have_upper))
        upper = [c for c in group["options"] if is_upper(c, levels)]
        for k in range(1, n + 1):
            limited = k <= need_upper
            add(f"{pid}:{group['id']}:{k}",
                "Elective, 300 or 400 level" if limited else "Elective toward the credit minimum",
                upper if limited else group["options"], group, True)
    return slots


def build_route(plan, slots, origin):
    """Map a sample plan onto slots.

    Each plan item is a course id or a placeholder such as ``CSC elective``
    (matched to the group id ``csc-elective``). A course goes to the free slot
    with the fewest options that lists it, so CSC-208 lands on the discrete
    slot rather than the broad elective. Returns ``slot_terms`` (slot id ->
    term index), and ``course_terms`` (every course the plan names -> term
    index; used to score routes and to keep the route's spacing).
    """
    slot_terms, course_terms = {}, {}
    for sem in plan.get("semesters") or []:
        t = (sem["year"] - 1) * 2 + (0 if sem["term"] == "Fall" else 1)
        for item in sem.get("items") or []:
            free = sorted((s for s in slots if s["id"] not in slot_terms),
                          key=lambda s: len(s["options"]))
            token = item.lower().replace(" ", "-")
            by_group = next((s for s in free if token in (s["group"], s["id"].lower())), None)
            by_course = next((s for s in free if item in s["options"]), None)
            if by_group is None and "-" in item and item[-1].isdigit():
                course_terms.setdefault(item, t)
            hit = by_group or by_course
            if hit:
                slot_terms[hit["id"]] = t
    return {"id": plan.get("id"), "name": plan.get("label") or plan.get("id"),
            "source_url": plan.get("source_url"), "origin": plan.get("origin") or origin,
            "slot_terms": slot_terms, "course_terms": course_terms}


def _policies(raw):
    """The catalog's policy list -> the handful of numbers the planner uses."""
    out = dict(DEFAULT_POLICIES)
    values = {p["id"]: p.get("values") or {} for p in raw or [] if isinstance(p, dict)}
    for key, policy, field in (
            ("graduation_credits", "graduation-core", "min_total_credits"),
            ("department_cap", "max-department-credits", "max_credits_one_department"),
            ("division_cap", "max-division-credits", "max_credits_one_division"),
            ("load_min", "load-min-normal", "min_credits_per_semester"),
            ("load_normal", "load-min-normal", "normal_credits_per_semester"),
            ("load_max", "load-max", "approval_required_above"),
            ("load_exempt", "load-max", "excluded_from_count"),
            ("fye", "fye", "course"), ("fye_semester", "fye", "typical_semester")):
        if values.get(policy, {}).get(field) is not None:
            out[key] = values[policy][field]
    return out


class Catalog:
    """Normalized catalog plus the small lookups the planner needs."""

    def __init__(self, raw, sample_courses=(), derived=None, origin="catalog"):
        derived = derived or {}
        self.origin = origin
        year = ((raw.get("meta") or {}).get("primary_catalog") or {}).get("year") or "2026-2027"
        self.catalog_year = f"{year[:4]}-{year[-2:]}"
        self.policies = _policies(raw.get("policies"))
        codes = (raw.get("divisions") or {}).get("codes") or {}
        self.courses = {}
        for c in raw.get("courses") or []:
            self.courses[c["id"]] = _course(c, origin, codes)
        for c in sample_courses:
            if c["id"] not in self.courses:
                self.courses[c["id"]] = _course(c, "sample", codes)
        self.divisions = {code: info.get("division") for code, info in codes.items()}
        for c in self.courses.values():
            self.divisions.setdefault(c["department"], c["division"])

        # Cross-lists: every id in a group shares one identity (the smallest id).
        groups = {}
        for c in self.courses.values():
            members = {c["id"], *c["cross_listed"]}
            for m in list(members):
                members |= groups.get(m, set())
            for m in members:
                groups[m] = members
        self._identity = {cid: min(members) for cid, members in groups.items()}
        self._aliases = {cid: frozenset(members) for cid, members in groups.items()}

        self.programs = {}
        plans = list(raw.get("sample_plans") or [])
        plans += [dict(p, origin="derived") for p in derived.get("sample_plans") or []]
        for p in raw.get("programs") or []:
            pid = PROGRAM_IDS.get(p["id"], p["id"])
            slots = build_slots(pid, p, self.courses)
            routes = [build_route(plan, slots, origin) for plan in plans if plan.get("program") == p["id"]]
            for s in slots:
                s["route_term"] = routes[0]["slot_terms"].get(s["id"]) if routes else None
            name = (p.get("name") or pid).replace(", B.A.", "").replace(" B.A.", "")
            self.programs[pid] = {
                "id": pid, "catalog_id": p["id"], "name": name, "slots": slots,
                "rules": list(p.get("rules") or []), "source_url": p.get("source_url"),
                "routes": routes, "ap_major_credit": p.get("ap_major_credit")}

    # ---- lookups -----------------------------------------------------------
    def identity(self, course_id):
        return self._identity.get(course_id, course_id)

    def expand(self, course_id):
        return self._aliases.get(course_id) or frozenset((course_id,))

    def subject(self, course_id):
        c = self.courses.get(course_id)
        return c["department"] if c else None

    def department(self, course_id):
        """The department a course counts under for the 48-credit cap.
        Chinese and Japanese count separately (Academic Policies)."""
        c = self.courses.get(course_id)
        if not c:
            return None
        return c["department"] if c["department"] in ("CHI", "JPN") else c["department_name"]

    def division(self, course_id):
        """Humanities, Science or Social Studies; None when the catalog does
        not place the course in a division (no cap applies)."""
        c = self.courses.get(course_id)
        return c["division"] if c and c["division"] in REAL_DIVISIONS else None

    def load_credits(self, course_id, credits):
        """Credits that count toward the over-18 load check."""
        return 0 if course_id in self.policies["load_exempt"] else credits

    def offered(self, course_id, term):
        """True / False when the catalog says, None when it does not."""
        c = self.courses.get(course_id)
        if not c or not c["offered"]:
            return None
        if term["season"] not in c["offered"]:
            return False
        if c["offered_years"]:
            return (term["year"] % 2 == 0) == (c["offered_years"] == "even")
        return True

    def offered_text(self, course_id):
        c = self.courses.get(course_id) or {}
        if not c.get("offered"):
            return "offering terms not stated"
        seasons = " and ".join(c["offered"])
        if c.get("offered_years"):
            return f"{seasons} of {c['offered_years']} years only"
        return f"{seasons} only" if len(c["offered"]) == 1 else seasons

    def transfer_counts(self, program_id, course_id):
        """Does AP / transfer credit for this course count toward the major?
        Only when the program data says so (``ap_major_credit``)."""
        listed = self.programs[program_id].get("ap_major_credit") or []
        return self.identity(course_id) in {self.identity(c) for c in listed}

    def public(self):
        """The GET /api/catalog body."""
        keys = ("id", "title", "credits", "department", "division", "level", "offered",
                "offered_note", "prereq_text", "prereq", "source_url",
                "offered_years", "cross_listed", "prereq_known", "credits_assumed", "origin")
        courses = [{k: c[k] for k in keys} for c in sorted(self.courses.values(), key=lambda c: c["id"])]
        programs = [{
            "id": p["id"], "name": p["name"],
            "slots": [{k: s[k] for k in ("id", "label", "kind", "options", "route_term", "derived")}
                      for s in p["slots"]],
            "rules": p["rules"], "source_url": p["source_url"],
            "routes": [{"id": r["id"], "name": r["name"], "origin": r["origin"],
                        "source_url": r["source_url"]} for r in p["routes"]],
        } for p in self.programs.values()]
        return {"catalog_year": self.catalog_year, "courses": courses, "programs": programs,
                "divisions": dict(sorted(self.divisions.items())), "data_origin": self.origin}


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_cache = {}


def load_catalog(path=None):
    """Load and normalize. ``path`` (or ``COURSEGRAPH_CATALOG``) overrides the
    catalog file; otherwise the real file is used when present and the fixture
    when not. Cached by file modification time."""
    path = path or os.environ.get("COURSEGRAPH_CATALOG")
    if path is None:
        real = DATA_DIR / REAL_FILE
        path = real if real.exists() else DATA_DIR / FIXTURE_FILE
    path = Path(path)
    extras = [DATA_DIR / "sample_courses.json", DATA_DIR / "derived.json"]
    key = (str(path), path.stat().st_mtime, tuple(e.stat().st_mtime if e.exists() else 0 for e in extras))
    if key not in _cache:
        raw = _read(path)
        is_fixture = bool(raw.get("fixture"))
        sample = _read(extras[0])["courses"] if extras[0].exists() else []
        derived = _read(extras[1]) if extras[1].exists() and not is_fixture else None
        _cache[key] = Catalog(raw, sample, derived, "fixture" if is_fixture else "catalog")
    return _cache[key]
