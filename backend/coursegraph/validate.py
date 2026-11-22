"""Stage 4, Validate: check the finished plan and explain what is wrong.

Works on plain tablets grouped by term index. Tablets that are locked history
(completed, in progress, not counted) are never re-checked; only planned and
projected tablets are. Returns warnings and the prerequisite edges (arrows).
"""
from . import prereq as P
from .terms import build_terms

CHECKED = ("planned", "projected")


def supplies(tablet, catalog):
    """Courses a course tablet makes available to later terms. A not-counted
    tablet supplies nothing, and neither does a D (prerequisites need a C)."""
    if tablet["status"] == "not_counted" or tablet.get("_clears") is False or not tablet["course"]:
        return set()
    return set(catalog.expand(tablet["course"]))


def availability(terms, plan, prior, catalog, skip=None):
    """term index -> courses supplied by that term (-1 holds AP / transfer).

    An open requirement slot stands for any one of its options, but only the
    options the student could really take in that term: offered then, with
    their own prerequisites in earlier terms.
    """
    have = {-1: set()}
    for t in prior:
        have[-1] |= supplies(t, catalog)
    for term in terms:
        index = term["index"]
        tablets = [t for t in plan.get(index, []) if t["id"] != skip]
        have[index] = set()
        for t in tablets:
            have[index] |= supplies(t, catalog)
        before, upto = split(have, index)
        for t in tablets:
            if t["status"] != "open" or not t["slot"]:
                continue                                # open electives promise no particular course
            for option in t["slot"]["options"]:
                tree = (catalog.courses.get(option) or {}).get("prereq")
                if catalog.offered(option, term) is not False and P.residue(tree, before, upto) is None:
                    have[index] |= catalog.expand(option)
    return have


def split(have, index):
    """(courses in strictly earlier terms, courses in this term or earlier)."""
    before, upto = set(), set()
    for j, cs in have.items():
        if j < index:
            before |= cs
        if j <= index:
            upto |= cs
    return before, upto


def check_course(course_id, term, have, catalog, check_offering=True):
    """Problems with taking ``course_id`` in ``term`` given what is available.

    Returns a list of ``(code, message, missing_ids)``. Consent is reported,
    never assumed; a prerequisite or offering the data does not state is
    reported as unknown.
    """
    course = catalog.courses.get(course_id)
    if course is None:
        return []
    out = []
    before, upto = split(have, term["index"])
    tree = course["prereq"]
    if tree is None and not course["prereq_known"]:
        note = f' ("{course["prereq_text"]}")' if course["prereq_text"] else ""
        out.append(("consent_required",
                    f"Prerequisites for {course_id} are not in the structured catalog data{note}; "
                    f"confirm with the department", []))
    elif P.residue(tree, before, upto, consent_ok=False) is not None:
        gap = P.residue(tree, before, upto, consent_ok=True)
        if gap is None:
            note = f': "{course["prereq_text"]}"' if course["prereq_text"] else ""
            out.append(("consent_required",
                        f"{course_id} needs consent or placement that the plan cannot check{note}", []))
        else:
            missing = P.courses_in(gap, ("course",))
            coreqs = P.courses_in(gap, ("coreq",))
            if missing:
                out.append(("prereq_missing",
                            f"{course_id} needs {P.text(gap)} before {term['label']}", missing))
            if coreqs:
                out.append(("coreq_missing",
                            f"{course_id} needs {' and '.join(coreqs)} in the same term or earlier",
                            coreqs))
    if check_offering:
        runs = catalog.offered(course_id, term)
        if runs is False:
            out.append(("not_offered", f"{course_id} is not offered in {term['label']} "
                                       f"({catalog.offered_text(course_id)})", []))
        elif runs is None:
            out.append(("not_offered", f"The catalog does not say which terms {course_id} runs; "
                                       f"confirm it is offered in {term['label']}", []))
    return out


def validate(terms, plan, prior, catalog):
    """Check every planned / projected tablet, every term's load, and the
    first-year requirements.

    * A missing prerequisite gives a warning and an edge from the tablet to the
      term immediately before it, even when that term is already past.
    * Load: more than 18 credits (music lessons, PHE and FYE excluded) is
      ``load_high``. ``load_low`` (under 12) is reported for the current term
      and for a next term the student has started to schedule; later terms are
      unfinished by nature.
    * Tutorial belongs in the first term (advising convention, a soft
      warning) and FYE in the second (catalog: "typically").

    Returns ``(warnings, edges)``; warnings are dicts with severity, code,
    message, term and tablet.
    """
    warnings, edges = [], []
    policies = catalog.policies
    have = availability(terms, plan, prior, catalog)
    by_index = {t["index"]: t for t in terms}

    for term in terms:
        tablets = plan.get(term["index"], [])
        for tab in tablets:
            if tab["status"] not in CHECKED or not tab["course"]:
                continue
            for code, message, missing in check_course(tab["course"], term, have, catalog,
                                                       check_offering=tab["status"] == "projected"):
                warnings.append({"severity": "warning", "code": code, "message": message,
                                 "term": term["id"], "tablet": tab["id"]})
                if code == "prereq_missing" and term["index"] >= 1:
                    edges.append({"from_tablet": tab["id"], "from_term": term["id"],
                                  "to_term": by_index[term["index"] - 1]["id"], "kind": "prereq",
                                  "missing": missing, "message": message})

        if term["state"] == "past" or term["off_campus"]:
            continue
        live = [t for t in tablets if t["status"] != "not_counted"]
        load = sum(catalog.load_credits(t["course"], t["credits"]) for t in live)
        if load > policies["load_max"]:
            warnings.append({"severity": "warning", "code": "load_high", "term": term["id"], "tablet": None,
                             "message": f"{term['label']} carries {load} credits; more than "
                                        f"{policies['load_max']} needs Registrar approval"})
        started = term["state"] == "current" or (
            term["state"] == "next" and any(t["status"] == "planned" for t in live))
        total = sum(t["credits"] for t in live)
        if started and total < policies["load_min"]:
            warnings.append({"severity": "warning", "code": "load_low", "term": term["id"], "tablet": None,
                             "message": f"{term['label']} has {total} credits; full time is at least "
                                        f"{policies['load_min']}"})

    for code, key, position, name in (
            ("tutorial_missing", "tutorial", 0, "Tutorial"),
            ("fye_missing", "fye", (policies.get("fye_semester") or 2) - 1, "First-Year Experience")):
        course_id = policies.get(key)
        if not course_id or course_id not in catalog.courses or position >= len(terms):
            continue
        where = [i for i, tablets in plan.items()
                 for t in tablets if t["course"] == course_id and t["status"] != "not_counted"]
        term = terms[position]
        ordinal = "first" if position == 0 else "second"
        if position in where:
            continue
        if where:
            message = f"{name} ({course_id}) belongs in the {ordinal} semester, not {by_index[min(where)]['label']}"
        elif term["state"] in ("next", "future"):
            message = f"{name} ({course_id}) is not in {term['label']} yet; it belongs in the {ordinal} semester"
        else:
            message = f"{name} ({course_id}) is missing from the {ordinal} semester ({term['label']})"
        if key == "tutorial":
            message += " (advising convention; the catalog does not name the semester)"
        warnings.append({"severity": "warning", "code": code, "message": message,
                         "term": term["id"], "tablet": None})
    return warnings, edges


def detect_clashes(sections):
    """Pairs of sections that share a day and overlap in time.
    Times are ``HH:MM`` strings, so plain comparison orders them."""
    clashes = []
    for i, a in enumerate(sections):
        for b in sections[i + 1:]:
            if any(set(m["days"]) & set(n["days"]) and m["start"] < n["end"] and n["start"] < m["end"]
                   for m in a["meetings"] for n in b["meetings"]):
                x, y = sorted((a["id"], b["id"]))
                clashes.append({"a": x, "b": y})
    return sorted(clashes, key=lambda c: (c["a"], c["b"]))


def check_schedule(student, term, section_ids, sections):
    """The page 1 gate: may these sections be saved as the student's schedule?

    The term must be the student's next term (the current term is registered
    and read-only; nothing else can hold planned courses), every section must
    exist in that term, and a course may appear once. Returns
    ``(chosen_sections, None)`` or ``(None, reason)``.
    """
    terms = build_terms(student["start_term"], student["current_term"], student.get("off_campus") or ())
    state = next((t["state"] for t in terms if t["id"] == term), None)
    if state == "current":
        return None, f"{term} is the current term; its schedule is registered and read-only"
    if state != "next":
        return None, f"{term} is not this student's next term; only the next term can be scheduled"
    by_id = {s["id"]: s for s in sections if s["term"] == term}
    chosen, courses = [], set()
    for sid in dict.fromkeys(section_ids):
        section = by_id.get(sid)
        if section is None:
            return None, f"Section {sid!r} does not exist in {term}"
        if section["course"] in courses:
            return None, f"Only one section of {section['course']} is allowed"
        courses.add(section["course"])
        chosen.append(section)
    return chosen, None
