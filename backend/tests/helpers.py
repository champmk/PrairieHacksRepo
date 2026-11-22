"""Shared test helpers. Algorithm tests run on the small fixture catalog so
they do not move when the real catalog data is updated."""
import json

from coursegraph.catalog import DATA_DIR, load_catalog
from coursegraph.plan import build_plan

FIXTURE = load_catalog(DATA_DIR / "fixture_catalog.json")
with open(DATA_DIR / "sections.json", encoding="utf-8") as _f:
    SECTIONS = [s for s in json.load(_f)["sections"] if s["course"] in FIXTURE.courses]


def enr(course, term, status="completed", grade="B", mode="letter"):
    if status in ("in_progress", "planned"):
        grade = None
    return {"course": course, "term": term, "status": status, "grade": grade, "mode": mode}


def student(enrollments=(), majors=("CS",), start="2025FA", current="2026FA", schedule=None,
            off_campus=(), cap=18):
    """Terms: 2025FA 2026SP past, 2026FA current, 2027SP next, 2027FA.. future."""
    return {"id": "test", "name": "Test Student", "start_term": start, "current_term": current,
            "majors": list(majors), "credit_cap": cap, "off_campus": list(off_campus),
            "enrollments": list(enrollments), "schedule": schedule or {}}


# A CS student exactly on the fixture's "CS via CSC-208" route.
ON_ROUTE = [
    enr("TUT-100", "2025FA"), enr("CSC-151", "2025FA"), enr("MAT-131", "2025FA"),
    enr("CSC-161", "2026SP"), enr("CSC-208", "2026SP"), enr("FYE-100", "2026SP", grade="S", mode="sdf"),
    enr("CSC-207", "2026FA", "in_progress"), enr("PHI-101", "2026FA", "in_progress"),
    enr("ENG-120", "2026FA", "in_progress"),
]


def plan(stu, edits=(), majors=None, cap=None, catalog=FIXTURE, sections=SECTIONS):
    return build_plan(stu, catalog, sections, majors, list(edits), cap)


def tablets(result, include_prior=True):
    out = {}
    for t in result["terms"]:
        for tab in t["tablets"]:
            out[tab["id"]] = dict(tab, term=t["id"])
    if include_prior:
        for tab in result["prior"]:
            out[tab["id"]] = dict(tab, term=None)
    return out


def term_of(result, tablet_id):
    for t in result["terms"]:
        if any(tab["id"] == tablet_id for tab in t["tablets"]):
            return t["id"]
    return None


def codes(result, tablet=None, term=None):
    return [w["code"] for w in result["warnings"]
            if (tablet is None or w["tablet"] == tablet) and (term is None or w["term"] == term)]
