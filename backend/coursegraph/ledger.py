"""Stage 1, Ledger: decide what counts.

Input is the raw enrollment list; output is one row per enrollment saying
whether it earns degree credit, whether it may count toward a major, and how
its tablet should look. No requirement logic lives here.
"""

GRADE_OK_FOR_MAJOR = ("A", "A-", "B+", "B", "B-", "C+", "C")
NO_CREDIT = {"withdrawn": "W", "failed": "F", "dropped": "DR"}
LIVE = ("completed", "in_progress", "planned")

GRAD_CREDITS = 124
DEPT_CAP = 48
DIVISION_CAP = 92


def build_ledger(enrollments, courses, identity, term_index):
    """Turn enrollments into ledger rows.

    Rules, in order:
    * withdrawn / failed / dropped earn nothing: ``status`` becomes
      ``not_counted`` and ``mark`` holds the letter.
    * A course (cross-listed ids are one course) may be repeated only after a
      D or an F, and then the latest attempt is the one that counts; the
      superseded D becomes ``not_counted``. Any other repeat keeps its tablet
      but earns nothing and is flagged ``repeat_not_allowed``.
    * AP / transfer rows (``term`` null) get index -1: degree credit that sits
      before every term.
    * ``major_ok`` is false for a grade below C and for S/D/F; for transfer
      rows it is left to the program (``major_reason == "transfer"``).
    * ``clears`` says whether the row satisfies prerequisites: any credit-
      bearing row except a D (the catalog asks for C or better; S is accepted).

    Returns rows in the input order.
    """
    rows = []
    for n, e in enumerate(enrollments):
        course = courses.get(e["course"]) or {}
        index = term_index.get(e.get("term"), -1) if e.get("term") else -1
        credits = e.get("credits")
        if credits is None:
            credits = course.get("credits") or 0
        rows.append({
            "course": e["course"], "term": e.get("term"), "index": index, "order": n,
            "raw_status": e["status"], "grade": e.get("grade"), "mode": e.get("mode") or "letter",
            "title": e.get("title") or course.get("title") or e["course"],
            "credits": credits, "status": e["status"], "mark": None,
            "credit": e["status"] in LIVE, "major_ok": False, "major_reason": None, "flags": [],
            "clears": e["status"] in LIVE and e.get("grade") != "D",
        })

    for row in rows:
        if row["raw_status"] in NO_CREDIT:
            row["status"] = "not_counted"
            row["mark"] = row["grade"] or NO_CREDIT[row["raw_status"]]

    standing = {}
    for row in sorted(rows, key=lambda r: (r["index"], r["order"])):
        if not row["credit"] or (courses.get(row["course"]) or {}).get("repeatable"):
            continue
        key = identity(row["course"])
        held = standing.get(key)
        if held is None:
            standing[key] = row
        elif held["grade"] == "D":
            held.update(status="not_counted", mark="D", credit=False)
            standing[key] = row
        else:
            row["credit"] = False
            row["flags"].append(("repeat_not_allowed", "error",
                                 f"{row['course']} was already taken; a course may be repeated "
                                 f"only after a D or an F, so this attempt earns no credit"))

    for row in rows:
        if not row["credit"]:
            continue
        if row["mode"] == "transfer":
            row["major_reason"] = "transfer"
        elif row["mode"] == "sdf":
            row["major_reason"] = "sdf"
        elif row["grade"] is not None and row["grade"] not in GRADE_OK_FOR_MAJOR:
            row["major_reason"] = "grade"
        else:
            row["major_ok"] = True
    return rows


def apply_caps(rows, dept_cap=DEPT_CAP, division_cap=DIVISION_CAP):
    """Credits that count toward the degree after the department/division caps.

    ``rows`` are ``(key, department, division, credits)`` in the order the
    credits are earned. Credits past 48 in one department or 92 in one
    division stop counting. A ``None`` department or division is not capped
    (AP credit is divisional only; some courses sit in no division).
    Returns ``(counted, events)``: ``counted[key]`` is what the row adds toward
    124, and each event is ``(key, "dept_cap" | "division_cap", name, lost)``.
    """
    by_dept, by_div, counted, events = {}, {}, {}, []
    for key, dept, div, credits in rows:
        allowed = credits
        if dept is not None:
            room = max(0, dept_cap - by_dept.get(dept, 0))
            if allowed > room:
                events.append((key, "dept_cap", dept, allowed - room))
                allowed = room
        if div is not None:
            room = max(0, division_cap - by_div.get(div, 0))
            if allowed > room:
                events.append((key, "division_cap", div, allowed - room))
                allowed = room
        if dept is not None:
            by_dept[dept] = by_dept.get(dept, 0) + allowed
        if div is not None:
            by_div[div] = by_div.get(div, 0) + allowed
        counted[key] = allowed
    return counted, events
