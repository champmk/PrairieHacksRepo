"""The planner: plan = f(student, majors, edits, credit_cap).

Composes the four pure stages and shapes the POST /api/plan response.

    Ledger      what counts (ledger.py)
    Match       slots <-> courses, route choice (matching.py)
    Distribute  unmatched slots -> terms (distribute.py)
    Validate    warnings and arrows (validate.py)

Nothing here reads a clock, a file or a database; the same arguments always
give the same response.
"""
from . import prereq as P
from .distribute import distribute
from .ledger import apply_caps, build_ledger
from .matching import choose_route, match_program, max_matching
from .terms import build_terms
from .validate import availability, check_course, split, validate

OPEN_CREDITS = 4          # nominal size of a requirement slot with no course chosen
PUBLIC_TABLET = ("id", "course", "title", "credits", "status", "mark", "required", "locked",
                 "slot", "counts_for", "warnings")
ELECTIVE_CREDITS = 4  # an open elective tablet stands for one ordinary course


class PlanError(ValueError):
    """Bad request data (unknown major, unknown term)."""


def _warn(warnings, severity, code, message, term=None, tablet=None):
    warnings.append({"severity": severity, "code": code, "message": message,
                     "term": term, "tablet": tablet})


def _is_open(term):
    return term["state"] in ("next", "future") and not term["off_campus"]


def apply_edits(edits, items, terms, catalog, slots_by_id, warnings):
    """Replay the student's edits, in order, on the projected terms.

    add     a new projected tablet ``add:<course>:<term>``.
    remove  deletes an added or planned tablet; for a requirement tablet it
            bars that slot from that term so the distributor moves it.
    swap    replaces a tablet's course; for a requirement tablet the course
            must be one of the slot's options, and the slot is then pinned to
            that term with that course.
    Anything aimed at a past, current or study-away term, a locked tablet, or
    something that does not exist is ignored and reported (``edit_ignored``).

    Open elective tablets (``open:<term>:<n>``) take any course: a swap adds
    that course to the term, a remove leaves one fewer elective there.

    Mutates ``items``; returns ``(choice, pin, barred, dropped)``: the first
    three keyed by slot id, ``dropped`` counts removed electives per term index.
    """
    open_terms = {t["id"]: t for t in terms if _is_open(t)}
    choice, pin, barred, dropped = {}, {}, {}, {}

    def new_tablet(course_id, term):
        course = catalog.courses[course_id]
        return {"id": f"add:{course_id}:{term['id']}", "course": course_id, "title": course["title"],
                "credits": course["credits"] or 0, "status": "projected", "mark": None,
                "required": False, "locked": False, "slot": None, "counts_for": [], "warnings": [],
                "_index": term["index"], "_credit": True, "_major_ok": True, "_major_reason": None,
                "_grade": None, "_origin": "add"}

    def in_term(course_id, term, skip=None):
        key = catalog.identity(course_id)
        return any(i["_index"] == term["index"] and i is not skip and i["status"] != "not_counted"
                   and catalog.identity(i["course"]) == key for i in items)

    for n, e in enumerate(edits, 1):
        op, term_id, tablet_id, course_id = e.get("op"), e.get("term"), e.get("tablet"), e.get("course")

        def ignore(why, term=None, tablet=None):
            _warn(warnings, "warning", "edit_ignored", f"Edit {n} ignored: {why}", term, tablet)

        term = open_terms.get(term_id)
        if term is None:
            ignore(f"{term_id} is not a term the plan can change", term_id, tablet_id)
            continue
        if op in ("add", "swap") and course_id not in catalog.courses:
            ignore(f"{course_id} is not in the catalog", term_id)
            continue
        if op == "add":
            if in_term(course_id, term):
                ignore(f"{course_id} is already in {term['label']}", term_id)
            else:
                items.append(new_tablet(course_id, term))
            continue
        if op not in ("remove", "swap") or not tablet_id:
            ignore(f"unknown edit {op!r}", term_id)
            continue
        if tablet_id.startswith("open:"):
            if op == "remove":
                dropped[term["index"]] = dropped.get(term["index"], 0) + 1
            elif in_term(course_id, term):
                ignore(f"{course_id} is already in {term['label']}", term_id)
            else:
                items.append(new_tablet(course_id, term))
            continue
        if tablet_id.startswith("slot:"):
            slot = slots_by_id.get(tablet_id[5:])
            if slot is None:
                ignore(f"{tablet_id} is not a requirement of the chosen majors", term_id)
            elif op == "remove":
                barred.setdefault(slot["id"], set()).add(term["index"])
                if pin.get(slot["id"]) == term["index"]:
                    del pin[slot["id"]]
            elif catalog.identity(course_id) not in {catalog.identity(c) for c in slot["options"]}:
                ignore(f"{course_id} is not an option for {slot['label']}", term_id, tablet_id)
            else:
                choice[slot["id"]] = course_id
                pin[slot["id"]] = term["index"]
                barred.get(slot["id"], set()).discard(term["index"])
            continue
        target = next((i for i in items if i["id"] == tablet_id and i["_index"] == term["index"]), None)
        if target is None:
            ignore(f"{tablet_id} is not in {term['label']}", term_id)
        elif target["locked"]:
            ignore(f"{tablet_id} is locked", term_id, tablet_id)
        elif op == "remove":
            items.remove(target)
        elif in_term(course_id, term, skip=target):
            ignore(f"{course_id} is already in {term['label']}", term_id)
        else:
            items[items.index(target)] = new_tablet(course_id, term)
    return choice, pin, barred, dropped


def required_leaves(tree):
    """Courses a prerequisite tree needs with no alternative (not under ``any``)."""
    if tree is None:
        return []
    if "course" in tree:
        return [tree["course"]]
    return [c for t in tree.get("all", []) for c in required_leaves(t)]


def build_units(programs, matched, routes, choice, pin, barred, catalog, have=frozenset()):
    """Turn the unmatched slots into units for the distributor.

    A slot with one option, or with a course chosen by a swap, becomes a
    course unit; two majors that need the same course share one unit (and one
    tablet). A course unit of one major may also fill an open choose slot of
    another major (second matching pass), but never as credit in both: two
    majors may not share credits. What is left are open units: choose slots
    with nothing chosen.

    Prerequisite pull-in: when a course unit needs a course that nothing in
    the plan supplies (``have`` is what the student holds), and an open slot
    lists that course, the open slot takes it. MAT-215 needs MAT-133, so a
    Mathematics elective slot becomes MAT-133 instead of staying blank. Only
    prerequisites with no alternative are pulled in; the student can swap.
    """
    identity = catalog.identity
    units, unit_of_course, open_slots = [], {}, []

    def attach(unit, p, slot):
        unit["slots"].append((p, slot))
        route = routes[p["id"]]
        rt = route["slot_terms"].get(slot["id"]) if route else None
        if rt is not None:
            unit["route_term"] = rt if unit["route_term"] is None else min(unit["route_term"], rt)
        if unit["pin"] is None:
            unit["pin"] = pin.get(slot["id"])
        unit["barred"] |= barred.get(slot["id"], set())

    def new_unit(slot, course_id):
        unit = {"id": slot["id"], "course": course_id, "options": list(slot["options"]), "slots": [],
                "route_term": None, "pin": None, "barred": set(), "order": len(units)}
        units.append(unit)
        return unit

    for p in programs:
        for slot in p["slots"]:
            if slot["id"] in matched[p["id"]]:
                continue
            course_id = choice.get(slot["id"]) or (slot["options"][0] if len(slot["options"]) == 1 else None)
            unit = unit_of_course.get(identity(course_id)) if course_id else None
            if unit is not None and any(q is p for q, _ in unit["slots"]):
                course_id, unit = None, None        # the same course chosen twice in one major
            if course_id is None:
                open_slots.append((p, slot))
                continue
            if unit is None:
                unit = unit_of_course[identity(course_id)] = new_unit(slot, course_id)
            attach(unit, p, slot)

    for p in programs:
        mine = [s for q, s in open_slots if q is p]
        foreign = [u for u in units if u["course"] and not any(q is p for q, _ in u["slots"])]
        owner = max_matching(
            foreign, mine,
            lambda u, s: identity(u["course"]) in {identity(c) for c in s["options"]}
            and not (s["credit_bearing"] and any(t["credit_bearing"] for _, t in u["slots"])))
        for j, i in owner.items():
            attach(foreign[i], p, mine[j])
            open_slots.remove((p, mine[j]))
    for p, slot in open_slots:
        attach(new_unit(slot, None), p, slot)

    supplied = set(have)
    for unit in units:
        if unit["course"]:
            supplied |= catalog.expand(unit["course"])
    queue = [u for u in units if u["course"]]
    while queue:
        unit = queue.pop(0)
        gap = P.residue((catalog.courses.get(unit["course"]) or {}).get("prereq"), supplied)
        for needed in required_leaves(gap):
            takers = sorted((u for u in units if u["course"] is None and needed in catalog.courses
                             and identity(needed) in {identity(c) for c in u["options"]}),
                            key=lambda u: (len(u["options"]), u["order"]))
            if takers and needed not in supplied:
                takers[0]["course"] = needed
                supplied |= catalog.expand(needed)
                queue.append(takers[0])

    for unit in units:
        if unit["course"]:
            unit["full_credits"] = catalog.courses[unit["course"]]["credits"] or 0
            unit["credits"] = catalog.load_credits(unit["course"], unit["full_credits"])
        else:
            sizes = {catalog.courses[c]["credits"] for c in unit["options"] if c in catalog.courses}
            sizes.discard(None)
            unit["full_credits"] = unit["credits"] = min(sizes) if sizes else OPEN_CREDITS
    return units


def compute(student, catalog, sections, majors=None, edits=(), credit_cap=None):
    """Run the whole pipeline. Returns ``(response, internals)``; the
    internals (terms, tablets by term index, prior credit) feed ``options``."""
    majors = list(student.get("majors") or []) if majors is None else list(dict.fromkeys(majors))
    for m in majors:
        if m not in catalog.programs:
            raise PlanError(f"Unknown major {m!r}; known: {sorted(catalog.programs)}")
    policies = catalog.policies
    cap = credit_cap or student.get("credit_cap") or policies["load_max"]
    identity = catalog.identity
    terms = build_terms(student["start_term"], student["current_term"], student.get("off_campus") or ())
    term_index = {t["id"]: t["index"] for t in terms}
    by_index = {t["index"]: t for t in terms}
    next_term = next((t for t in terms if t["state"] == "next"), None)
    warnings = []

    def term_id_of(index):
        return by_index[index]["id"] if index is not None and index >= 0 else None

    # ---- 1. Ledger -----------------------------------------------------------
    # "planned" comes only from the saved schedule of the next term.
    enrollments = [e for e in student.get("enrollments") or [] if e["status"] != "planned"]
    if next_term is not None and not next_term["off_campus"]:
        section_course = {s["id"]: s["course"] for s in sections}
        for sid in (student.get("schedule") or {}).get(next_term["id"], []):
            course_id = section_course.get(sid)
            if course_id and not any(e["course"] == course_id and e.get("term") == next_term["id"]
                                     for e in enrollments):
                enrollments.append({"course": course_id, "term": next_term["id"], "status": "planned",
                                    "grade": None, "mode": "letter"})
    items, used = [], set()
    for row in build_ledger(enrollments, catalog.courses, identity, term_index):
        tid = f"enr:{row['course']}:{row['term'] if row['index'] >= 0 else 'prior'}"
        while tid in used:
            tid += "+"
        used.add(tid)
        items.append({
            "id": tid, "course": row["course"], "title": row["title"], "credits": row["credits"],
            "status": row["status"], "mark": row["mark"], "required": False,
            "locked": row["status"] != "planned", "slot": None, "counts_for": [], "warnings": [],
            "_index": row["index"], "_credit": row["credit"], "_major_ok": row["major_ok"],
            "_major_reason": row["major_reason"], "_grade": row["grade"], "_origin": "enr",
            "_clears": row["clears"], "_transfer": row["mode"] == "transfer"})
        for code, severity, message in row["flags"]:
            _warn(warnings, severity, code, message, term_id_of(row["index"]), tid)

    # ---- Edits ---------------------------------------------------------------
    programs = [catalog.programs[m] for m in majors]
    slots_by_id = {s["id"]: s for p in programs for s in p["slots"]}
    choice, pin, barred, dropped = apply_edits(edits or [], items, terms, catalog, slots_by_id, warnings)

    # A course earns credit once. A later copy counts only as the repeat of a D.
    holder = {}
    for item in sorted(items, key=lambda i: i["_index"]):
        if not item["_credit"] or (catalog.courses.get(item["course"]) or {}).get("repeatable"):
            continue
        first = holder.setdefault(identity(item["course"]), item)
        if first is item:
            continue
        item["_credit"] = False
        if first["_grade"] != "D":
            item["_major_ok"] = False
            where = by_index[first["_index"]]["label"] if first["_index"] >= 0 else "prior credit"
            _warn(warnings, "warning", "duplicate", f"{item['course']} is already in the plan ({where})",
                  term_id_of(item["_index"]), item["id"])

    # ---- 2. Match ------------------------------------------------------------
    live = [i for i in items if i["status"] != "not_counted"]
    record_at = {}
    for i in live:
        if i["_origin"] == "enr":
            key = identity(i["course"])
            record_at[key] = min(record_at.get(key, i["_index"]), i["_index"])
    # Two majors may not share credits (Academic Policies). A course that fills a
    # credit-bearing slot of one major can fill only cognate ("also required")
    # slots of the next.
    matched, routes, route_of, spent = {}, {}, {}, set()
    for p in programs:
        eligible = [i for i in live if i["_major_ok"] or (
            i["_major_reason"] == "transfer" and catalog.transfer_counts(p["id"], i["course"]))]
        matched[p["id"]] = match_program(
            p["slots"], eligible, identity,
            lambda item, slot: not (slot["credit_bearing"] and item["id"] in spent))
        spent |= {item["id"] for sid, item in matched[p["id"]].items() if slots_by_id[sid]["credit_bearing"]}
        routes[p["id"]] = choose_route(p["routes"], record_at, identity)
        for course_id, t in (routes[p["id"]] or {}).get("course_terms", {}).items():
            for alias in catalog.expand(course_id):
                route_of[alias] = min(route_of.get(alias, t), t)
        for slot in p["slots"]:
            item = matched[p["id"]].get(slot["id"])
            if item is None:
                continue
            item["required"] = True
            item["counts_for"].append(f"{p['id']} · {slot['label']}")
            if item["slot"] is None:
                item["slot"] = {"id": slot["id"], "program": p["id"], "label": slot["label"],
                                "options": list(slot["options"])}

        # Record tablets that would fill a slot here but for the grade rules.
        wanted = {identity(c) for s in p["slots"] for c in s["options"]}
        for i in live:
            if i["_origin"] != "enr" or not i["_credit"] or identity(i["course"]) not in wanted:
                continue
            if i["_major_reason"] in ("grade", "sdf"):
                why = "was taken S/D/F" if i["_major_reason"] == "sdf" else f"has a grade of {i['_grade']}"
                message = (f"{i['course']} {why}, so it does not count toward {p['name']} "
                           f"(C or better, not S/D/F)")
            elif i["_major_reason"] == "transfer" and not catalog.transfer_counts(p["id"], i["course"]):
                message = (f"{i['course']} is AP / transfer credit; the catalog data does not say it "
                           f"counts toward {p['name']}, so the requirement stays open")
            else:
                continue
            _warn(warnings, "warning", "major_grade", message, term_id_of(i["_index"]), i["id"])

    # ---- 3. Distribute -------------------------------------------------------
    held = [{"course": i["course"], "index": i["_index"],
             "load": catalog.load_credits(i["course"], i["credits"])}
            for i in live if i.get("_clears", True)]
    have = set()
    for h in held:
        have |= catalog.expand(h["course"])
    units = build_units(programs, matched, routes, choice, pin, barred, catalog, have)
    placed, unplaced = distribute(units, held, terms, catalog.courses, catalog.expand, catalog.offered,
                                  credit_cap=cap, soft_cap=min(policies["load_normal"], cap), route_of=route_of)

    plan = {t["index"]: [] for t in terms}
    prior = [i for i in items if i["_index"] < 0]
    for i in items:
        if i["_index"] >= 0:
            plan[i["_index"]].append(i)
    for unit in units:
        if unit["id"] not in placed:
            continue
        p, slot = unit["slots"][0]
        course = catalog.courses.get(unit["course"]) if unit["course"] else None
        tablet = {
            "id": f"slot:{unit['id']}", "course": unit["course"],
            "title": course["title"] if course else slot["label"], "credits": unit["full_credits"],
            "status": "projected" if unit["course"] else "open", "mark": None, "required": True,
            "locked": False,
            "slot": {"id": slot["id"], "program": p["id"], "label": slot["label"],
                     "options": list(slot["options"])},
            "counts_for": [f"{q['id']} · {s['label']}" for q, s in unit["slots"]], "warnings": [],
            "_index": placed[unit["id"]], "_credit": True, "_origin": "slot", "_grade": None}
        first = holder.get(identity(unit["course"])) if unit["course"] else None
        if first is not None:
            tablet["_credit"] = False               # the course already earned its credit once
            if first["_grade"] != "D":
                _warn(warnings, "warning", "duplicate",
                      f"{unit['course']} is already on the record but does not count toward the major; "
                      f"check with the department before repeating it",
                      term_id_of(placed[unit["id"]]), tablet["id"])
        plan[placed[unit["id"]]].append(tablet)

    open_count = sum(1 for t in terms if _is_open(t))
    everything = set()
    for i in live:
        everything |= catalog.expand(i["course"])
    reason_of, unscheduled = {u["id"]: u["reason"] for u in unplaced}, []
    for unit in units:
        if unit["id"] not in reason_of:
            continue
        name = unit["course"] or unit["slots"][0][1]["label"]
        for p, slot in unit["slots"]:
            unscheduled.append({"slot": slot["id"], "label": slot["label"], "reason": reason_of[unit["id"]]})
        _warn(warnings, "error", "unscheduled",
              f"{name} does not fit before graduation: {reason_of[unit['id']]}")
        depth = P.chain_depth(unit["course"], catalog.courses, everything) if unit["course"] else 0
        if depth + 1 > open_count:
            _warn(warnings, "error", "chain_too_long",
                  f"{name} sits behind {depth} terms of prerequisites; with the course itself that is "
                  f"{depth + 1} terms and only {open_count} are left")

    # ---- Credit accounting: once per course, then the 48 / 92 caps --------------
    earning = [t for t in prior + [t for i in sorted(plan) for t in plan[i]]
               if t["status"] != "not_counted" and t["_credit"]]
    # AP / transfer credit is divisional: it is not held to the department cap.
    counted, events = apply_caps(
        [(t["id"], None if t.get("_transfer") else catalog.department(t["course"]),
          catalog.division(t["course"]), t["credits"]) for t in earning],
        policies["department_cap"], policies["division_cap"])
    tablet_by_id = {t["id"]: t for t in earning}
    for key, code, name, lost in events:
        t = tablet_by_id[key]
        limit = policies["department_cap"] if code == "dept_cap" else policies["division_cap"]
        kind = "department" if code == "dept_cap" else "division"
        _warn(warnings, "warning", code,
              f"{name} passes the {limit}-credit {kind} cap here; {lost} credits of {t['course']} "
              f"do not count toward {policies['graduation_credits']}", term_id_of(t["_index"]), key)
    totals = {"counted": 0, "in_progress": 0, "planned": 0, "required": policies["graduation_credits"],
              "by_department": {}, "by_division": {}}
    for t in earning:
        got = counted[t["id"]]
        totals[{"completed": "counted", "in_progress": "in_progress"}.get(t["status"], "planned")] += got
        if t["course"] and got:
            for name, table in ((catalog.subject(t["course"]), "by_department"),
                                (catalog.division(t["course"]), "by_division")):
                if name:
                    totals[table][name] = totals[table].get(name, 0) + got
    totals["by_department"] = dict(sorted(totals["by_department"].items()))
    totals["by_division"] = dict(sorted(totals["by_division"].items()))

    # ---- 4. Validate ---------------------------------------------------------
    found, edges = validate(terms, plan, prior, catalog)
    warnings += found

    # ---- 5. Open electives -----------------------------------------------------
    # Whatever the majors leave toward 124 becomes open tablets that take any
    # course. Round-robin over the open terms keeps loads even; each term fills
    # to the normal load (16) at most, minus electives the student removed.
    reach = totals["counted"] + totals["in_progress"] + totals["planned"]
    need = policies["graduation_credits"] - reach
    per_term = min(cap, policies["load_normal"])
    room = {}
    for t in terms:
        if not _is_open(t):
            continue
        load = sum(catalog.load_credits(x["course"], x["credits"]) if x["course"] else x["credits"]
                   for x in plan[t["index"]] if x["status"] != "not_counted")
        room[t["index"]] = max(0, (per_term - load) // ELECTIVE_CREDITS - dropped.get(t["index"], 0))
    filled, seq = 0, {}
    while need > 0 and any(room.values()):
        for index in sorted(room):
            if need <= 0 or room[index] <= 0:
                continue
            seq[index] = seq.get(index, 0) + 1
            plan[index].append({
                "id": f"open:{term_id_of(index)}:{seq[index]}", "course": None, "title": "Elective",
                "credits": ELECTIVE_CREDITS, "status": "open", "mark": None, "required": False,
                "locked": False, "slot": None, "counts_for": [], "warnings": [], "_index": index,
                "_credit": False, "_origin": "open", "_grade": None})
            room[index] -= 1
            need -= ELECTIVE_CREDITS
            filled += ELECTIVE_CREDITS
    totals["open"] = filled
    reach += filled
    if reach < policies["graduation_credits"]:
        room = sum(max(0, policies["load_max"] - sum(
            catalog.load_credits(x["course"], x["credits"])
            for x in plan[t["index"]] if x["status"] != "not_counted")) for t in terms if _is_open(t))
        short = policies["graduation_credits"] - reach
        _warn(warnings, "warning" if short <= room else "error", "grad_credits",
              f"The plan reaches {reach} of {policies['graduation_credits']} credits by "
              f"{terms[-1]['label']}; {short} more are needed", terms[-1]["id"])

    # ---- Shape the response ----------------------------------------------------
    all_tablets = {t["id"]: t for t in prior + [t for i in plan for t in plan[i]]}
    for n, w in enumerate(warnings, 1):
        w["id"] = f"w{n}"
        if w["tablet"] not in all_tablets:
            w["tablet"] = None
        if w["term"] not in term_index:
            w["term"] = None
        if w["tablet"]:
            all_tablets[w["tablet"]]["warnings"].append(w["id"])
    for n, e in enumerate(edges, 1):
        e["id"] = f"e{n}"

    def public(t):
        return {k: t[k] for k in PUBLIC_TABLET}

    out_terms = []
    for t in terms:
        tablets = plan[t["index"]]
        live_here = [x for x in tablets if x["status"] != "not_counted"]
        out_terms.append({
            "id": t["id"], "label": t["label"], "season": t["season"], "year": t["year"],
            "index": t["index"], "state": t["state"], "off_campus": t["off_campus"],
            "complete": t["state"] == "past" and all(x["status"] == "completed" for x in live_here),
            "credits": sum(x["credits"] for x in live_here),
            "tablets": [public(x) for x in tablets]})

    progress = []
    for p in programs:
        rows, tally = [], {"completed": 0, "in_progress": 0, "planned": 0}
        slot_unit = {s["id"]: u for u in units for q, s in u["slots"] if q is p}
        for slot in p["slots"]:
            item = matched[p["id"]].get(slot["id"])
            if item is not None:
                status, course_id, index = item["status"], item["course"], item["_index"]
            else:
                unit = slot_unit[slot["id"]]
                course_id, index = unit["course"], placed.get(unit["id"])
                status = "projected" if course_id and index is not None else "open"
            if status in ("completed", "in_progress"):
                tally[status] += 1
            elif index is not None:
                tally["planned"] += 1
            rows.append({"id": slot["id"], "label": slot["label"], "status": status,
                         "course": course_id, "term": term_id_of(index)})
        route = routes[p["id"]]
        progress.append({
            "program": p["id"], "name": p["name"], "total": len(p["slots"]),
            "done": tally["completed"], "in_progress": tally["in_progress"], "planned": tally["planned"],
            "slots": rows,
            "route": {"id": route["id"], "name": route["name"], "origin": route["origin"]} if route else None})

    response = {
        "student_id": student.get("id"), "majors": majors, "credit_cap": cap,
        "terms": out_terms, "prior": [public(t) for t in prior],
        "edges": [{k: e[k] for k in ("id", "from_tablet", "from_term", "to_term", "kind", "missing", "message")}
                  for e in edges],
        "warnings": [{k: w[k] for k in ("id", "severity", "code", "message", "term", "tablet")}
                     for w in warnings],
        "progress": progress, "totals": totals, "unscheduled": unscheduled}
    return response, {"terms": terms, "plan": plan, "prior": prior}


def build_plan(student, catalog, sections, majors=None, edits=(), credit_cap=None):
    """POST /api/plan: the response body for one student and one set of edits."""
    return compute(student, catalog, sections, majors, edits, credit_cap)[0]


def build_options(student, catalog, sections, term, tablet=None, majors=None, edits=(), credit_cap=None):
    """POST /api/options: the courses that can fill a tablet in ``term``.

    A requirement tablet lists only its slot's options. Any other tablet, or no
    tablet (the + button), lists every catalog course that is not already in
    the plan. Eligibility is computed for that term: the term must be open, the
    course offered then, and its prerequisites in earlier terms. Eligible
    courses come first, then by course id.
    """
    _, state = compute(student, catalog, sections, majors, edits, credit_cap)
    where = next((t for t in state["terms"] if t["id"] == term), None)
    if where is None:
        raise PlanError(f"{term!r} is not one of this student's terms")
    target = next((t for t in state["plan"][where["index"]] if t["id"] == tablet), None) if tablet else None
    identity = catalog.identity
    taken = set()
    for t in state["prior"] + [t for i in state["plan"] for t in state["plan"][i]]:
        if t is target or not t["course"] or t["status"] == "not_counted":
            continue
        if t["_grade"] == "D" and t["_credit"]:
            continue                                    # a D may be repeated
        taken.add(identity(t["course"]))
    required = bool(target and target["required"] and target["slot"])
    if required:
        candidates = list(target["slot"]["options"])
    else:
        candidates = sorted(c for c in catalog.courses if identity(c) not in taken)
    have = availability(state["terms"], state["plan"], state["prior"], catalog,
                        skip=target["id"] if target else None)
    before, upto = split(have, where["index"])
    rows = []
    for course_id in candidates:
        course = catalog.courses.get(course_id) or {}
        reason, eligible = None, True
        if not _is_open(where):
            eligible, reason = False, "This term cannot be changed"
        elif identity(course_id) in taken:
            eligible, reason = False, "Already in your plan"
        else:
            codes = [code for code, _, _ in check_course(course_id, where, have, catalog)]
            if catalog.offered(course_id, where) is False:
                text = catalog.offered_text(course_id)
                eligible, reason = False, text[0].upper() + text[1:]
            elif "prereq_missing" in codes or "coreq_missing" in codes:
                eligible = False
                reason = "Needs " + P.text(P.residue(course.get("prereq"), before, upto))
            elif "consent_required" in codes:
                reason = "Instructor consent or department check needed"
            elif "not_offered" in codes:
                reason = "Offering terms unknown"
        rows.append({"course": course_id, "title": course.get("title") or course_id,
                     "credits": course.get("credits"), "eligible": eligible, "reason": reason})
    rows.sort(key=lambda r: (not r["eligible"], r["course"]))
    return {"tablet": tablet if target else None, "term": term, "required": required,
            "label": target["slot"]["label"] if required else "Add a course", "options": rows}
