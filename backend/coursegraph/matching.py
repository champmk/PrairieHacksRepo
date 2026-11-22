"""Stage 2, Match: which courses fill which requirement slots.

Maximum bipartite matching by augmenting paths (Kuhn's algorithm). Courses are
offered to the matching in priority order, so the matched set is the best one
lexicographically: a completed course is never displaced by a planned one, and
a course that could fill two slots is moved to whichever leaves the other slot
fillable by someone else.
"""

TIER = {"completed": 0, "in_progress": 1, "planned": 2, "projected": 3}


def max_matching(items, slots, can_fill):
    """Match ``items`` (already in priority order) to ``slots``.

    ``can_fill(item, slot)`` says whether the pair is allowed. Returns
    ``{slot_index: item_index}``. Each item tries its slots narrowest first
    (fewest options, then program order), so specific slots win over
    choose-n slots when both are free.
    """
    order = sorted(range(len(slots)), key=lambda j: (len(slots[j]["options"]), j))
    adj = [[j for j in order if can_fill(item, slots[j])] for item in items]
    owner = {}

    def augment(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in owner or augment(owner[j], seen):
                owner[j] = i
                return True
        return False

    for i in range(len(items)):
        augment(i, set())
    return owner


def priority(item):
    """completed > in_progress > planned > projected, then the earlier term."""
    return (TIER.get(item["status"], 9), item.get("index", item.get("_index", 0)), item["course"])


def match_program(slots, items, identity, allowed=None):
    """Fill one program's slots from the student's courses.

    ``items`` are the courses eligible for this major (grade and transfer rules
    already applied). ``identity`` maps a course id to its cross-list identity,
    so MAT-208 fills a slot that lists CSC-208. ``allowed(item, slot)`` can
    veto a pair (used to keep two majors from sharing credits). One course
    fills at most one slot. Returns ``{slot_id: item}``.
    """
    ranked = sorted(items, key=priority)
    option_ids = [{identity(c) for c in s["options"]} for s in slots]
    index_of = {id(s): j for j, s in enumerate(slots)}
    owner = max_matching(
        ranked, slots,
        lambda item, slot: identity(item["course"]) in option_ids[index_of[id(slot)]]
        and (allowed is None or allowed(item, slot)))
    return {slots[j]["id"]: ranked[i] for j, i in owner.items()}


def choose_route(routes, held, identity):
    """Pick the sample route that best overlaps what the student has taken.

    ``held`` maps course identity -> term index for the student's record. A
    route scores 2 for every course it names that the student took in that
    very term and 1 for a course taken in any other term. Ties keep the
    catalog's order. Returns the route, or ``None`` when there are none.
    """
    best, best_score = None, -1
    for route in routes:
        score = 0
        for course, term in route["course_terms"].items():
            at = held.get(identity(course))
            if at is not None:
                score += 2 if at == term else 1
        if score > best_score:
            best, best_score = route, score
    return best
