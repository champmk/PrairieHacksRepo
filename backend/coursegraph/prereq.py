"""Prerequisite trees.

A tree is one of ``{"course": id}``, ``{"all": [...]}``, ``{"any": [...]}``,
``{"coreq": id}``, ``{"consent": True}`` or ``None`` (no prerequisite).
Everything here is pure: trees and sets in, trees and numbers out.
"""


def residue(tree, before, upto=None, consent_ok=True):
    """The part of ``tree`` that is still unmet, or ``None`` when it is met.

    ``before`` holds courses available in strictly earlier terms, ``upto``
    those available in the same term or earlier (corequisites). A consent leaf
    is met only when ``consent_ok`` is true, so the caller decides whether
    consent is assumed (placement) or reported (validation).
    """
    if tree is None:
        return None
    if "course" in tree:
        return None if tree["course"] in before else tree
    if "coreq" in tree:
        return None if tree["coreq"] in (before if upto is None else upto) else tree
    if "consent" in tree:
        return None if consent_ok else tree
    if "all" in tree:
        parts = [r for r in (residue(t, before, upto, consent_ok) for t in tree["all"]) if r]
        if not parts:
            return None
        return parts[0] if len(parts) == 1 else {"all": parts}
    parts = []
    for t in tree.get("any", []):
        r = residue(t, before, upto, consent_ok)
        if r is None:
            return None
        parts.append(r)
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else {"any": parts}


def courses_in(tree, kinds=("course",)):
    """Course ids named by the tree's leaves, in reading order, no repeats."""
    out = []

    def walk(t):
        if t is None:
            return
        for kind in ("course", "coreq"):
            if kind in t:
                if kind in kinds and t[kind] not in out:
                    out.append(t[kind])
                return
        for child in t.get("all", []) + t.get("any", []):
            walk(child)

    walk(tree)
    return out


def has_consent(tree):
    if tree is None:
        return False
    if "consent" in tree:
        return True
    return any(has_consent(t) for t in tree.get("all", []) + tree.get("any", []))


def text(tree):
    """Human text, for example ``CSC-207 and (CSC-208 or MAT-218)``."""
    if tree is None:
        return "None"
    if "course" in tree:
        return tree["course"]
    if "coreq" in tree:
        return f"{tree['coreq']} (may be taken at the same time)"
    if "consent" in tree:
        return "instructor consent"
    kind = "all" if "all" in tree else "any"
    parts = []
    for t in tree[kind]:
        s = text(t)
        nested = ("all" in t or "any" in t) and len(t.get("all", t.get("any", []))) > 1
        parts.append(f"({s})" if nested else s)
    return (" and " if kind == "all" else " or ").join(parts)


def chain_depth(course, courses, held, _stack=()):
    """How many terms of unmet prerequisites lie below ``course``.

    0 means it can be taken now. ``all`` takes the deepest branch, ``any`` the
    shallowest. A course missing from the catalog has no known prerequisites.
    """
    def depth(t):
        if t is None or "coreq" in t or "consent" in t:
            return 0
        if "course" in t:
            c = t["course"]
            if c in held or c in _stack:
                return 0
            return 1 + chain_depth(c, courses, held, _stack + (course,))
        if "all" in t:
            return max((depth(x) for x in t["all"]), default=0)
        return min((depth(x) for x in t.get("any", [])), default=0)

    return depth((courses.get(course) or {}).get("prereq"))
