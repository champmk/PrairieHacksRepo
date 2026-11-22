"""Term arithmetic. A term id is ``YYYYFA`` or ``YYYYSP``; a student has eight."""

SEASONS = {"FA": "Fall", "SP": "Spring"}
TERM_COUNT = 8


def term_ord(term_id):
    """Sortable ordinal: 2026SP < 2026FA < 2027SP."""
    return int(term_id[:4]) * 2 + (1 if term_id[4:] == "FA" else 0)


def term_from_ord(n):
    return f"{n // 2}{'FA' if n % 2 else 'SP'}"


def is_term_id(value):
    return (isinstance(value, str) and len(value) == 6 and value[:4].isdigit()
            and value[4:] in SEASONS)


def build_terms(start_term, current_term, off_campus=()):
    """The student's eight terms with the state each one has today.

    past < current < next < future, computed from ``current_term`` alone.
    ``off_campus`` terms (study away) hold no Grinnell courses.
    """
    first, now = term_ord(start_term), term_ord(current_term)
    terms = []
    for i in range(TERM_COUNT):
        o = first + i
        tid = term_from_ord(o)
        state = ("past" if o < now else "current" if o == now
                 else "next" if o == now + 1 else "future")
        season = SEASONS[tid[4:]]
        terms.append({"id": tid, "label": f"{season} {tid[:4]}", "season": season,
                      "year": int(tid[:4]), "index": i, "state": state,
                      "off_campus": tid in set(off_campus)})
    return terms
