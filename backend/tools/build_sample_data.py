"""Build the SAMPLE (mock) data files from ``sample_majors.py``.

    cd backend
    python tools/build_sample_data.py

Writes ``data/sample_courses.json``, ``data/sample_programs.json`` and
``data/sections.json``. Deterministic: the same inputs give the same files.
Nothing here touches ``grinnell_catalog.json`` (real) or ``students.json``.
"""
import json
import random
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sample_majors as M  # noqa: E402

DATA = ROOT / "data"
TERMS = {"2026FA": {"season": "Fall", "year": 2026}, "2027SP": {"season": "Spring", "year": 2027}}
OFFERED = {"F": ["Fall"], "S": ["Spring"], "FS": ["Fall", "Spring"]}
EXTRA_FIELDS = {
    "FYE-100": {"note": "The catalog policies name FYE-100 (S/D/F, typically the second semester, not "
                        "repeatable) but give no course page; the 1 credit and the offering terms here "
                        "are placeholders."},
    "MUS-120": {"repeatable": True},
}
EXTRA_DIVISIONS = {"EDU": "Social Studies", "FMS": "Interdisciplinary", "GDS": "Interdisciplinary",
                   "LAT": "Humanities", "GRE": "Humanities"}
CAPSTONE_SENTENCES = ["Normally taken in the senior year; the course ends with a public presentation.",
                      "Open to senior majors, who meet weekly to share work in progress.",
                      "Required of all majors and normally taken in the final year."]


def pick(seq, key):
    return seq[zlib.crc32(key.encode()) % len(seq)]


def dump(path, body):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(body, f, indent=1, ensure_ascii=False)
        f.write("\n")


# ---- courses ---------------------------------------------------------------------------

def parse_prereq(text):
    """``-`` | ``A & B`` | ``A or B``  ->  (raw prerequisite, COLSS-style text)."""
    text = text.strip()
    if text == "-":
        return None, "Prerequisite: None."
    for sep, kind, word in ((" & ", "all", " and "), (" or ", "any", " or ")):
        if sep in text:
            ids = [p.strip() for p in text.split(sep)]
            return {kind: ids}, "Prerequisite: " + word.join(ids) + "."
    return text, f"Prerequisite: {text}."


def describe(cid, title, sentence, style, cross):
    level = int(cid.split("-")[1][:3])
    capstone = level >= 400 and cid != "CHI-461" or title.startswith("Senior")
    if capstone:
        second = pick(CAPSTONE_SENTENCES, cid)
    else:
        bucket = "intro" if level < 200 else "mid" if level < 300 else "upper"
        second = pick(M.STYLE_SENTENCES[style][bucket], cid)
    parts = [sentence.strip(), second]
    if cross:
        parts.append(f"Cross-listed as {cross}.")
    return " ".join(parts)


def parse_courses(block, style, division):
    """One record per course id; a cross-listed line gives two records."""
    out = []
    for line in block.strip().splitlines():
        head, title, offered, prereq, sentence = [p.strip() for p in line.split(" | ")]
        credits = 4
        if head.endswith(")"):
            head, credits = head[:-1].split("(")
            credits = int(credits)
        ids = head.split("=")
        tree, text = parse_prereq(prereq)
        for cid in ids:
            cross = next((x for x in ids if x != cid), None)
            subject = cid.split("-")[0]
            div = EXTRA_DIVISIONS.get(subject, division)
            if cross and subject in MAJOR_DIVISION:
                div = MAJOR_DIVISION[subject]
            record = {
                "id": cid, "title": title, "credits": credits,
                "description": describe(ids[0], title, sentence, style, cross),
                "prereq_text": text, "prereq": tree, "offered": OFFERED[offered],
                "location": "Main Campus", "cross_listed_as": cross, "source_url": None,
                "division": None if subject in ("TUT", "FYE") else div, "origin": "sample"}
            record.update(EXTRA_FIELDS.get(cid, {}))
            out.append(record)
    return out


MAJOR_DIVISION = {m["id"]: m["division"] for m in M.MAJORS}


def build_courses():
    courses, primary = {}, {}
    blocks = [(m["courses"], m["style"], m["division"]) for m in M.MAJORS]
    blocks.append((M.EXTRAS["courses"], M.EXTRAS["style"], None))
    for block, style, division in blocks:
        for c in parse_courses(block, style, division):
            assert c["id"] not in courses, f"duplicate course {c['id']}"
            courses[c["id"]] = c
            if c["cross_listed_as"] and c["cross_listed_as"] not in primary:
                primary[c["id"]] = c["id"]
                primary[c["cross_listed_as"]] = c["id"]
    aliases = {cid for cid, first in primary.items() if cid != first}
    return courses, aliases


# ---- programs --------------------------------------------------------------------------

def build_programs(courses, real):
    programs, plans = [], []
    known = set(courses) | set(real)
    for m in M.MAJORS:
        groups, credit_slots, slots = [], 0, 0
        for kind, gid, label, count, options in m["groups"]:
            assert all(o in known for o in options), (gid, [o for o in options if o not in known])
            cognate = kind.startswith("also-")
            base = kind.replace("also-", "")
            n = len(options) if base == "all" else count
            slots += n
            credit_slots += 0 if cognate else n
            groups.append({"id": gid, "label": label, "kind": base,
                           "count": None if base == "all" else count,
                           "credits_min": None if cognate else 4 * n, "options": options,
                           "notes": "Also required; does not count toward the major's own credits."
                           if cognate else None})
        total = 4 * slots
        rules = [f"SAMPLE program for the demo: {total} credits ({slots} courses). The major name is real; "
                 f"the requirements, courses and route are illustrative, not the catalog's."]
        if credit_slots != slots:
            rules.append(f"{4 * credit_slots} credits are in the major itself; the 'also required' courses "
                         f"may also count toward another major.")
        programs.append({
            "id": m["id"], "name": m["name"], "department": m["name"], "division": m["division"],
            "origin": "sample", "total_credits_min": total, "requirement_groups": groups,
            "rules": rules, "source_url": None})
        terms = [seg.split() for seg in m["route"].split("/")]
        assert len(terms) == 8, m["id"]
        plans.append({
            "id": f"{m['id'].lower()}-sample-1", "program": m["id"], "origin": "sample",
            "label": f"Sample four-year route for {m['name']} (mock)", "source_url": None,
            "semesters": [{"year": i // 2 + 1, "term": "Fall" if i % 2 == 0 else "Spring",
                           "items": [x for x in items if x != "-"]} for i, items in enumerate(terms)]})
    return programs, plans


def leaves(tree):
    if tree is None:
        return []
    if isinstance(tree, str):
        return [tree]
    return [c for part in tree.get("all", tree.get("any", [])) for c in leaves(part)]


def met(tree, have):
    if tree is None:
        return True
    if isinstance(tree, str):
        return tree.startswith("placement:") or tree in have
    if "all" in tree:
        return all(met(t, have) for t in tree["all"])
    return any(met(t, have) for t in tree["any"])


def check_routes(programs, plans, courses, real):
    """Every route must be walkable: each requirement is in the route once, each
    course is offered in its term's season, and its prerequisites are in earlier
    terms. An open choose slot needs one option that can be taken there."""
    info = {**{c["id"]: (c.get("offered") or [], c.get("prereq")) for c in real.values()},
            **{cid: (c["offered"], c["prereq"]) for cid, c in courses.items()}}
    alias = {cid: c["cross_listed_as"] for cid, c in courses.items() if c["cross_listed_as"]}

    def expand(ids):
        return set(ids) | {alias[i] for i in ids if i in alias}

    for program, plan in zip(programs, plans):
        need = {}
        for g in program["requirement_groups"]:
            if g["kind"] == "all":
                for c in g["options"]:
                    need[c] = 1
            else:
                need[g["id"]] = g["count"]
        group = {g["id"]: g for g in program["requirement_groups"]}
        have = set()
        for sem in plan["semesters"]:
            season, gained = sem["term"], set()
            for item in sem["items"]:
                assert need.get(item, 0) > 0, f"{program['id']}: {item} is not a remaining requirement"
                need[item] -= 1
                options = group[item]["options"] if item in group else [item]
                takeable = [c for c in options
                            if (season in info[c][0] or "Fall or Spring" in info[c][0] or not info[c][0])
                            and met(info[c][1], have)]
                assert takeable, f"{program['id']}: nothing can fill {item} in {season} of year {sem['year']}"
                gained |= expand(takeable)
            have |= gained
        left = {k: v for k, v in need.items() if v}
        assert not left, f"{program['id']}: route leaves out {left}"
        for g in program["requirement_groups"]:       # every prerequisite is reachable
            for c in g["options"]:
                for p in leaves(info[c][1]):
                    assert p.startswith("placement:") or p in info, f"{c} needs unknown {p}"


# ---- sections --------------------------------------------------------------------------

MWF50 = [(["M", "W", "F"], s, e) for s, e in (("08:00", "08:50"), ("09:00", "09:50"), ("10:00", "10:50"),
                                              ("11:00", "11:50"), ("13:00", "13:50"), ("14:00", "14:50"),
                                              ("15:00", "15:50"))]
MWF80 = [(["M", "W", "F"], s, e) for s, e in (("08:00", "09:20"), ("10:00", "11:20"), ("13:00", "14:20"),
                                              ("14:30", "15:50"))]
TR80 = [(["T", "R"], s, e) for s, e in (("08:00", "09:20"), ("09:30", "10:50"), ("11:00", "12:20"),
                                        ("13:00", "14:20"), ("14:30", "15:50"))]
EVENING = [(["M"], "19:00", "21:50"), (["T"], "19:00", "21:50"), (["W"], "19:00", "21:50"),
           (["M", "W"], "19:00", "20:20"), (["T", "R"], "19:00", "20:20")]
LABS = [([d], s, e) for d in "TWR" for s, e in (("13:00", "15:50"), ("08:00", "10:50"))]
STUDIO = [(["M", "W"], "13:00", "15:50"), (["T", "R"], "13:00", "15:50"), (["T", "R"], "09:00", "11:50")]

ROOMS = {
    "Noyce": ["Noyce 1023", "Noyce 1245", "Noyce 1302", "Noyce 2022", "Noyce 2245", "Noyce 2401", "Noyce 2517",
              "Noyce 3813", "Noyce 3815", "Noyce 3819", "Noyce 3821"],
    "Noyce lab": ["Noyce 1401", "Noyce 1405", "Noyce 1502", "Noyce 1510", "Noyce 2415", "Noyce 2501",
                  "Noyce 2505", "Noyce 3401", "Noyce 3405", "Noyce 3501"],
    "HSSC": ["HSSC A1231", "HSSC A2231", "HSSC N1112", "HSSC N2112", "HSSC N3110", "HSSC S1325", "HSSC S2350",
             "HSSC S3325", "HSSC N1170", "HSSC S2310", "HSSC A3242", "HSSC N2116"],
    "ARH": ["ARH 102", "ARH 120", "ARH 223", "ARH 227", "ARH 318", "ARH 324"],
    "Steiner": ["Steiner 106", "Steiner 205", "Steiner 305", "Steiner 306"],
    "Mears": ["Mears 115", "Mears 202", "Mears 216", "Mears 304"],
    "Goodnow": ["Goodnow 105", "Goodnow 109", "Goodnow 201"],
    "Bucksbaum": ["Bucksbaum 131", "Bucksbaum 152", "Bucksbaum 154", "Bucksbaum 243", "Bucksbaum 263",
                  "Bucksbaum 269"],
}
BUILDING = {
    **dict.fromkeys(["BIO", "CHM", "BCM", "PHY", "PSY", "CSC", "MAT", "STA"], "Noyce"),
    **dict.fromkeys(["ECN", "HIS", "POL", "SOC", "LAS", "EDU", "GDS", "TUT", "FYE"], "HSSC"),
    **dict.fromkeys(["CHI", "FRN", "GRM", "RUS", "SPN", "CLS", "LAT", "GRE"], "ARH"),
    **dict.fromkeys(["PHI", "REL", "GWS", "AMS"], "Steiner"),
    "ENG": "Mears", "ANT": "Goodnow",
    **dict.fromkeys(["ARH", "ART", "MUS", "THD", "FMS"], "Bucksbaum"),
}
LAB_SUBJECTS = {"BIO", "CHM", "BCM", "PHY"}
LANGUAGES = {"CHI", "FRN", "GRM", "RUS", "SPN", "LAT", "GRE"}
POOL_OF = {"LAT": "CLS", "GRE": "CLS", "FYE": "TUT"}
POOL_SIZE = {"CSC": 6, "MAT": 6, "STA": 3, "EDU": 1, "FMS": 1, "GDS": 1, "TUT": 4}
REAL_ALIASES = {"STA-330", "STA-335", "STA-336"}      # taught as the MAT section of the same course


def instructor_pools(subjects):
    """Fictional names, a fixed handful per department. Fails on any real name."""
    real = {n.strip().lower() for n in M.KNOWN_REAL}
    real_last = {n.split()[-1] for n in real}
    assert len(set(M.LAST_NAMES)) == len(M.LAST_NAMES) and len(set(M.FIRST_NAMES)) == len(M.FIRST_NAMES)
    names = []
    for i, last in enumerate(M.LAST_NAMES):
        name = f"{M.FIRST_NAMES[(i * 37 + 11) % len(M.FIRST_NAMES)]} {last}"
        assert name.lower() not in real and last.lower() not in real_last, name
        names.append(name)
    pools, at = {}, 0
    for subject in sorted(subjects):
        size = POOL_SIZE.get(subject, 4)
        assert at + size <= len(names), "not enough fictional names"
        pools[subject] = names[at:at + size]
        at += size
    return pools


def minutes(clock):
    return int(clock[:2]) * 60 + int(clock[3:])


class Calendar:
    """Who and what is busy when, per term, so no instructor or room is double-booked."""

    def __init__(self):
        self.busy = {}

    def free(self, term, who, meeting):
        days, start, end = meeting
        for d in days:
            for s, e in self.busy.get((term, who, d), []):
                if minutes(start) < e and s < minutes(end):
                    return False
        return True

    def book(self, term, who, meeting):
        days, start, end = meeting
        for d in days:
            self.busy.setdefault((term, who, d), []).append((minutes(start), minutes(end)))


def build_sections(catalog, aliases):
    with open(Path(__file__).resolve().parent / "legacy_sections.json", encoding="utf-8") as f:
        legacy = [s for s in json.load(f)["sections"] if s["course"] in catalog.courses]
    subjects = {POOL_OF.get(c["department"], c["department"]) for c in catalog.courses.values()}
    pools = instructor_pools(subjects)
    cal = Calendar()
    out, by_key = [], {}

    def pool(course_id):
        subject = catalog.courses[course_id]["department"]
        return pools[POOL_OF.get(subject, subject)]

    def room_for(term, subject, meeting, rng, lab=False):
        building = BUILDING.get(subject, "HSSC")
        choices = list(ROOMS["Noyce lab"] if lab else ROOMS[building])
        rng.shuffle(choices)
        spare = [r for name in sorted(ROOMS) if name != "Noyce lab" for r in ROOMS[name]]
        for room in choices + (ROOMS["Noyce"] if lab else []) + ROOMS["HSSC"] + spare:
            if cal.free(term, room, meeting):
                cal.book(term, room, meeting)
                return room
        raise AssertionError(f"no room for {subject} {meeting}")

    def instructor_for(term, course_id, meetings, rng, k):
        names = pool(course_id)
        start = zlib.crc32(course_id.encode()) + k
        for n in range(len(names)):
            name = names[(start + n) % len(names)]
            if all(cal.free(term, name, m) for m in meetings):
                for m in meetings:
                    cal.book(term, name, m)
                return name
        return None

    def add(section):
        out.append(section)
        by_key.setdefault((section["term"], section["course"]), []).append(section)

    # The legacy sections keep their ids, times and seats.
    for s in sorted(legacy, key=lambda s: s["id"]):
        rng = random.Random(zlib.crc32(s["id"].encode()))
        subject = s["course"].split("-")[0]
        meetings = [(m["days"], m["start"], m["end"]) for m in s["meetings"]]
        name = instructor_for(s["term"], s["course"], meetings, rng, int(s["number"]))
        assert name, s["id"]
        rooms = []
        for m, raw in zip(meetings, s["meetings"]):
            if raw["room"]:
                cal.book(s["term"], raw["room"], m)
                rooms.append(raw["room"])
            else:
                rooms.append(room_for(s["term"], subject, m, rng))
        add({"id": s["id"], "course": s["course"], "term": s["term"], "number": s["number"],
             "instructor": name, "available": s["available"], "capacity": s["capacity"],
             "meetings": [{"days": list(m[0]), "start": m[1], "end": m[2], "room": r}
                          for m, r in zip(meetings, rooms)]})

    def wanted(course, term_id):
        """How many sections a course gets in a term (0 when it does not run)."""
        cid, level = course["id"], course["level"] or 100
        state = catalog.offered(cid, TERMS[term_id])
        if state is False or not course["prereq_known"] and course["origin"] == "catalog" \
                and course["offered"] is None and course["credits_assumed"]:
            return 0
        if state is None:       # term not stated: one section, in one of the two terms
            return 1 if pick(sorted(TERMS), cid) == term_id else 0
        both = len(course["offered"]) == 2
        h = zlib.crc32((cid + term_id).encode())
        if cid == "TUT-100":
            return 3
        if level < 200:
            return 2 + h % 2 if both else 2
        if level < 300:
            return 1 + (h % 3 == 0)
        return 1

    def patterns(course, rng):
        cid, subject, level = course["id"], course["department"], course["level"] or 100
        seminar = level >= 300
        if course["credits"] < 4:
            return EVENING[3:] + TR80[3:] + MWF50[4:]
        if subject == "ART" and level < 400:
            return STUDIO + MWF80
        if subject in LANGUAGES and level < 300:
            return MWF50
        if subject in LAB_SUBJECTS and level < 400:
            return MWF50[:4] + TR80[:3]
        if seminar and rng.random() < 0.2:
            return EVENING[:3] + TR80
        if seminar:
            return TR80 + MWF80
        if level < 200:
            return MWF50 + TR80 + MWF80[:1]
        return MWF50 + MWF80 + TR80

    def seats(course, rng, lab):
        level, subject = course["level"] or 100, course["department"]
        if course["id"] == "TUT-100":
            capacity = 12
        elif course["id"] == "MUS-120":
            capacity = 32
        elif level >= 400:
            capacity = rng.choice([12, 14])
        elif level >= 300:
            capacity = rng.choice([12, 14, 15, 16, 18])
        elif subject in LANGUAGES:
            capacity = rng.choice([16, 18, 20])
        elif lab:
            capacity = rng.choice([20, 24])
        elif level >= 200:
            capacity = rng.choice([18, 20, 22, 24])
        else:
            capacity = rng.choice([24, 26, 28, 30, 32])
        available = 0 if rng.random() < 0.1 else rng.randint(1, max(2, capacity * 2 // 3))
        return available, capacity

    order = sorted(catalog.courses.values(),
                   key=lambda c: (c["id"] in aliases or c["id"] in REAL_ALIASES, c["id"]))
    for term_id in sorted(TERMS):
        for course in order:
            cid = course["id"]
            n = wanted(course, term_id)
            have = by_key.get((term_id, cid), [])
            twin = next((x for x in sorted(catalog.expand(cid)) if x != cid and by_key.get((term_id, x))), None)
            if (cid in aliases or cid in REAL_ALIASES) and twin and not have and n:
                for s in list(by_key[(term_id, twin)]):      # a cross-listed course is one class
                    add(dict(s, id=f"{term_id}-{cid}-{s['number']}", course=cid,
                             meetings=[dict(m) for m in s["meetings"]]))
                continue
            used = {s["number"] for s in have}
            for k in range(max(0, n - len(have))):
                number = next(f"{i:02d}" for i in range(1, 20) if f"{i:02d}" not in used)
                used.add(number)
                sid = f"{term_id}-{cid}-{number}"
                rng = random.Random(zlib.crc32(sid.encode()))
                lab = course["department"] in LAB_SUBJECTS and (course["level"] or 100) < 400
                choices = patterns(course, rng)
                rng.shuffle(choices)
                for main in choices:
                    meetings = [main]
                    if lab:
                        slot = next((x for x in rng.sample(LABS, len(LABS))
                                     if not set(x[0]) & set(main[0]) or minutes(x[1]) >= minutes(main[2])
                                     or minutes(main[1]) >= minutes(x[2])), None)
                        meetings.append(slot)
                    name = instructor_for(term_id, cid, meetings, rng, k)
                    if name:
                        break
                else:
                    raise AssertionError(f"no free instructor for {sid}")
                rooms = [room_for(term_id, course["department"], m, rng, lab=lab and i == 1)
                         for i, m in enumerate(meetings)]
                available, capacity = seats(course, rng, lab)
                add({"id": sid, "course": cid, "term": term_id, "number": number, "instructor": name,
                     "available": available, "capacity": capacity,
                     "meetings": [{"days": list(m[0]), "start": m[1], "end": m[2], "room": r}
                                  for m, r in zip(meetings, rooms)]})
    out.sort(key=lambda s: (s["term"], s["course"], s["number"]))
    return out


# ---- main ------------------------------------------------------------------------------

def main():
    with open(DATA / "grinnell_catalog.json", encoding="utf-8") as f:
        real = {c["id"]: c for c in json.load(f)["courses"]}
    courses, aliases = build_courses()
    missing = [cid for cid in real if cid not in M.CATALOG_DESCRIPTIONS]
    assert not missing, f"no description for {missing}"
    programs, plans = build_programs(courses, real)
    check_routes(programs, plans, courses, real)

    dump(DATA / "sample_courses.json", {
        "origin": "sample",
        "note": "SAMPLE (mock) data, generated by tools/build_sample_data.py. Every course in 'courses' is "
                "invented for the demo: titles, numbers, credits, offerings, prerequisites and descriptions "
                "are illustrative, not catalog facts. A course that is in grinnell_catalog.json always wins "
                "over a sample with the same id. 'descriptions' holds mock descriptions, written for the "
                "demo, for the real Computer Science, Mathematics and Statistics courses; the catalog facts "
                "for those courses stay in grinnell_catalog.json.",
        "courses": list(courses.values()),
        "descriptions": M.CATALOG_DESCRIPTIONS})
    dump(DATA / "sample_programs.json", {
        "origin": "sample",
        "note": "SAMPLE (mock) programs, generated by tools/build_sample_data.py. The major names and "
                "divisions are real; the requirement groups, credit totals and four-year routes are "
                "invented for the demo. Computer Science and Mathematics are not here: they come from "
                "grinnell_catalog.json.",
        "programs": programs, "sample_plans": plans})

    from coursegraph.catalog import load_catalog
    catalog = load_catalog(DATA / "grinnell_catalog.json")
    sections = build_sections(catalog, aliases)
    dump(DATA / "sections.json", {
        "origin": "sample",
        "note": "SAMPLE sections for Fall 2026 and Spring 2027, generated by tools/build_sample_data.py. "
                "Times, rooms and seat counts are placeholders and every instructor name is FICTIONAL. "
                "Replace this file with `python -m coursegraph.colss import <snapshot.json> --out "
                "data/sections.json`.",
        "sections": sections})
    print(f"{len(catalog.programs)} programs, {len(catalog.courses)} courses "
          f"({len(courses)} sample), {len(sections)} sections")


if __name__ == "__main__":
    main()
