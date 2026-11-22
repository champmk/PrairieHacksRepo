"""Stage 3, Distribute: put the unmatched requirement slots into terms.

List scheduling. Units (one per unmatched slot, or one shared by two majors
that need the same course) are taken in priority order and each is dropped
into the first term that satisfies every constraint. Pure function.
"""
from . import prereq as P

NO_ROUTE = 99


def distribute(units, held, terms, courses, expand, offered, credit_cap=18, soft_cap=16,
               route_of=None):
    """Place ``units`` into the open (next / future, on-campus) terms.

    units   ``{"id", "course" | None, "options", "credits", "route_term",
            "pin" | None, "barred": set(index), "order"}``. ``course`` is None
            for a choose slot with nothing chosen; such a unit stands for "one
            of its options" when a later course asks for a prerequisite, and
            itself waits for the prerequisites of its easiest option.
    held    courses already in the plan: ``{"course", "index", "load"}``
            (index -1 is AP / transfer credit).
    expand  course id -> set of ids it stands for (cross-lists).
    offered ``(course, term) -> True | False | None``; None (unknown) does not
            block placement, the validator reports it.
    route_of course identity -> term index in the chosen sample route.

    Priority: longest chain of units still depending on this one, then route
    term, then program order. Because a prerequisite always has a longer chain
    than its dependents, prerequisites are placed first.

    Target term: the route term, pulled earlier when a course unit's
    prerequisites were finished early. The route's spacing after its latest prerequisite is
    kept: target = min(route, latest prerequisite's actual term + route gap).
    The target is clamped so the chain hanging off the unit still fits.

    A unit takes the first term at or after its target (then, failing that, the
    nearest earlier one) where: the term is not barred by a remove edit, the
    course is offered, its prerequisites sit in strictly earlier terms
    (corequisites may share the term), and the load stays within the cap. The
    soft cap (about 16) is tried first, then ``credit_cap``. Pinned units (a
    swap the student made) stay where the student put them.

    Returns ``(placed, unscheduled)``: ``{unit_id: term_index}`` and a list of
    ``{"id", "reason"}`` for units that fit nowhere.
    """
    route_of = route_of or {}
    open_idx = [t["index"] for t in terms if t["state"] in ("next", "future") and not t["off_campus"]]
    term_at = {t["index"]: t for t in terms}
    if not open_idx:
        return {}, [{"id": u["id"], "reason": "No terms left"} for u in units]
    first, last = open_idx[0], open_idx[-1]
    soft_cap = min(soft_cap, credit_cap)

    def provides(u):
        out = set()
        for c in ([u["course"]] if u["course"] else u["options"]):
            out |= expand(c)
        return out

    def tree_of(u):
        """A course unit has its course's prerequisite. An open unit needs
        whatever its easiest option needs: nothing if any option is free."""
        if u["course"]:
            return (courses.get(u["course"]) or {}).get("prereq")
        trees = [(courses.get(o) or {}).get("prereq") for o in u["options"]]
        return None if not trees or any(t is None for t in trees) else {"any": trees}

    load = {i: 0 for i in open_idx}
    have = {}                       # term index -> courses available from that term
    actual = {}                     # course id -> term index where it is taken
    for h in held:
        have.setdefault(h["index"], set()).update(expand(h["course"]))
        for c in expand(h["course"]):
            actual[c] = min(actual.get(c, h["index"]), h["index"])
        if h["index"] in load:
            load[h["index"]] += h["load"]
    everything = set().union(*have.values()) if have else set()

    # Chain length: 1 + the longest chain of units that depend on this one.
    supplies = {u["id"]: provides(u) for u in units}
    needs = {u["id"]: set(P.courses_in(P.residue(tree_of(u), everything))) for u in units}
    dependents = {u["id"]: [v["id"] for v in units
                            if v is not u and supplies[u["id"]] & needs[v["id"]]] for u in units}
    level = {}

    def chain(uid, stack=()):
        if uid not in level:
            level[uid] = 1 + max((chain(d, stack + (uid,)) for d in dependents[uid]
                                  if d not in stack), default=0)
        return level[uid]

    for u in units:
        chain(u["id"])

    placed = {}

    def put(u, i):
        """Record the placement. An open unit supplies only the options the
        student could really take in that term (offered, prerequisites met)."""
        placed[u["id"]] = i
        gives = supplies[u["id"]]
        if not u["course"]:
            before, upto = available(i, False), available(i, True)
            gives = set()
            for o in u["options"]:
                if offered(o, term_at[i]) is not False and                         P.residue((courses.get(o) or {}).get("prereq"), before, upto) is None:
                    gives |= expand(o)
        have.setdefault(i, set()).update(gives)
        if i in load:
            load[i] += u["credits"]
        if u["course"]:
            for c in expand(u["course"]):
                actual[c] = min(actual.get(c, i), i)

    def prereq_ok(u, i):
        return P.residue(tree_of(u), available(i, False), available(i, True)) is None

    def target(u):
        r = u["route_term"] if u["route_term"] is not None else first
        t = r
        done = [p for p in P.courses_in(tree_of(u)) if p in actual and p in route_of]
        if done and u["course"]:
            gap = max(1, r - max(route_of[p] for p in done))
            t = min(r, max(actual[p] for p in done) + gap)
        return max(first, min(t, last - (level[u["id"]] - 1)))

    def available(i, inclusive):
        out = set()
        for j, cs in have.items():
            if j < i or (inclusive and j == i):
                out |= cs
        return out

    pinned = [u for u in units if u["pin"] is not None]
    for u in pinned:
        put(u, u["pin"])

    unscheduled = []
    queue = sorted((u for u in units if u["pin"] is None),
                   key=lambda u: (-level[u["id"]],
                                  NO_ROUTE if u["route_term"] is None else u["route_term"],
                                  u["order"]))
    for u in queue:
        t = target(u)
        deadline = max(t, last - (level[u["id"]] - 1))
        order = [i for i in open_idx if i >= t] + [i for i in reversed(open_idx) if i < t]
        allowed = [i for i in order if i not in u["barred"]]
        runs = [i for i in allowed
                if not u["course"] or offered(u["course"], term_at[i]) is not False]
        ready = [i for i in runs if prereq_ok(u, i)]
        spot = next((i for i in ready if i <= deadline and load[i] + u["credits"] <= soft_cap), None)
        if spot is None:
            spot = next((i for i in ready if load[i] + u["credits"] <= credit_cap), None)
        if spot is not None:
            put(u, spot)
            continue
        if not allowed:
            reason = "Removed from every remaining term"
        elif not runs:
            reason = "Not offered in the remaining terms"
        elif not ready:
            reason = "Prerequisites not met in time"
            reachable = everything.union(*supplies.values()) if supplies else everything
            gap = P.residue(tree_of(u), reachable)
            if gap is not None:
                reason = f"Needs {P.text(gap)}, which is not in the plan"
        else:
            reason = f"No room under the {credit_cap}-credit limit"
        unscheduled.append({"id": u["id"], "reason": reason})
    return placed, unscheduled
