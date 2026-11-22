"""COLSS (Ellucian Self-Service) snapshot importer. Offline only.

Turns saved JSON responses into our sections file. Nothing here opens a
network connection, logs in or handles cookies: someone saves the responses
by hand, this module only reshapes them.

Shapes follow ``docs/backend/examples/ellucian_master_developer_reference.py``:

* search response:   ``CourseFullModels[]`` with ``Id``, ``SubjectCode``,
  ``Number``, ``MatchingSectionIds``
* sections response: ``SectionsRetrieved.TermsAndSections[]`` with
  ``Term.Code`` (``2027/SP``) and ``Sections[]`` holding ``Section`` (``Id``,
  ``Number``, ``Available``, ``Capacity``), ``FacultyDisplay`` and, when
  present, ``Meetings`` or ``FormattedMeetingTimes``

The examples name the two meeting fields but do not show their contents, so
the meeting parser accepts the usual Ellucian spellings and otherwise leaves
``meetings`` empty. An unknown meeting time stays unknown.

CLI:  python -m coursegraph.colss import snapshot.json --out data/sections.json

A snapshot file is ``{"search": <search response>, "sections": {"<course Id>":
<sections response>, ...}}``.
"""
import argparse
import json
import re
import sys

DAY_LETTERS = {0: "U", 1: "M", 2: "T", 3: "W", 4: "R", 5: "F", 6: "S"}
DAY_WORDS = {"su": "U", "sun": "U", "m": "M", "mon": "M", "t": "T", "tu": "T", "tue": "T",
             "w": "W", "wed": "W", "th": "R", "thu": "R", "r": "R", "f": "F", "fri": "F",
             "sa": "S", "sat": "S"}


def term_id(code):
    """``2027/SP`` -> ``2027SP``."""
    return str(code).replace("/", "").replace(" ", "").upper()


def clock(value):
    """``8:00 AM``, ``08:00:00`` or ``13:10`` -> ``HH:MM``; None if unreadable."""
    m = re.search(r"(\d{1,2}):(\d{2})(?::\d{2})?\s*([AaPp][Mm])?", str(value or ""))
    if not m:
        return None
    hour, minute, half = int(m.group(1)), m.group(2), (m.group(3) or "").lower()
    if half == "pm" and hour < 12:
        hour += 12
    if half == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute}"


def _days(value):
    if isinstance(value, (list, tuple)):
        out = [DAY_LETTERS.get(d, None) if isinstance(d, int) else DAY_WORDS.get(str(d).lower()[:3])
               or DAY_WORDS.get(str(d).lower()) for d in value]
        return [d for d in out if d]
    text = str(value or "")
    if re.fullmatch(r"[MTWRFSU]+", text):
        return list(text)
    out = []
    for part in re.split(r"[^A-Za-z]+", text):
        letter = DAY_WORDS.get(part.lower()) or DAY_WORDS.get(part.lower()[:3])
        if letter and letter not in out:
            out.append(letter)
    return out


def _first(record, *names):
    for name in names:
        if record.get(name) not in (None, ""):
            return record[name]
    return None


def _meetings(entry, section):
    raw = _first(section, "Meetings", "FormattedMeetingTimes") \
        or _first(entry, "Meetings", "FormattedMeetingTimes") or []
    out = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        days = _days(_first(m, "Days", "DaysOfWeek", "DaysOfWeekDisplay"))
        start = clock(_first(m, "StartTime", "StartTimeDisplay", "StartTimeHour"))
        end = clock(_first(m, "EndTime", "EndTimeDisplay", "EndTimeHour"))
        if not days or not start or not end:
            continue
        building, room = _first(m, "BuildingDisplay", "Building"), _first(m, "RoomDisplay", "Room")
        place = " ".join(str(x) for x in (building, room) if x)
        out.append({"days": days, "start": start, "end": end, "room": place or None})
    return out


def sections_from_colss(search_json, sections_json_by_course):
    """Map saved COLSS responses to CONTRACT ``Section`` dicts.

    ``search_json`` is one PostSearchCriteria response;
    ``sections_json_by_course`` maps a course ``Id`` to its Sections response.
    Only sections listed in the course's ``MatchingSectionIds`` are kept (all
    of them when that list is absent). The section id is
    ``<term>-<course>-<number>``; the COLSS id is kept as ``colss_id``.
    Pure: same input, same output, sorted by id.
    """
    out = {}
    for course in (search_json or {}).get("CourseFullModels") or []:
        course_id = f"{course['SubjectCode']}-{course['Number']}"
        wanted = {str(x) for x in course.get("MatchingSectionIds") or []}
        response = (sections_json_by_course or {}).get(str(course["Id"])) or {}
        for block in (response.get("SectionsRetrieved") or {}).get("TermsAndSections") or []:
            term = term_id((block.get("Term") or {}).get("Code", ""))
            for entry in block.get("Sections") or []:
                section = entry.get("Section") or {}
                if wanted and str(section.get("Id")) not in wanted:
                    continue
                number = str(section.get("Number") or "")
                sid = f"{term}-{course_id}-{number}"
                out[sid] = {
                    "id": sid, "course": course_id, "term": term, "number": number,
                    "instructor": entry.get("FacultyDisplay") or "Staff",
                    "available": section.get("Available"), "capacity": section.get("Capacity"),
                    "meetings": _meetings(entry, section), "colss_id": str(section.get("Id"))}
    return [out[k] for k in sorted(out)]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m coursegraph.colss",
                                     description="Convert a saved COLSS snapshot (offline).")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="snapshot.json -> sections file")
    imp.add_argument("snapshot")
    imp.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    with open(args.snapshot, encoding="utf-8") as f:
        snapshot = json.load(f)
    sections = sections_from_colss(snapshot.get("search"), snapshot.get("sections"))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"origin": "colss", "note": f"Imported from {args.snapshot}", "sections": sections},
                  f, indent=1)
    print(f"Wrote {len(sections)} sections to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
