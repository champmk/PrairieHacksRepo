"""HTTP layer. Implements backend/CONTRACT.md; every route is under /api.

Run from ``backend/``:  python -m uvicorn coursegraph.api:app --port 8100
"""
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import db
from .catalog import DATA_DIR, load_catalog
from .plan import PlanError, build_options, build_plan
from .terms import build_terms
from .validate import check_schedule, detect_clashes


def load_sections(catalog, path=None):
    """Sections from ``data/sections.json`` for courses the catalog knows."""
    path = path or DATA_DIR / "sections.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    rows = raw["sections"] if isinstance(raw, dict) else raw
    return [s for s in rows if s["course"] in catalog.courses]


def student_view(student, sections):
    """The GET /api/students/{id} body: the stored record plus the computed
    term states and one ``planned`` enrollment per section saved for the next
    term (planned exists nowhere else)."""
    terms = build_terms(student["start_term"], student["current_term"], student["off_campus"])
    next_id = next((t["id"] for t in terms if t["state"] == "next"), None)
    course_of = {s["id"]: s["course"] for s in sections}
    enrollments = [e for e in student["enrollments"] if e["status"] != "planned"]
    for sid in student["schedule"].get(next_id, []):
        if sid in course_of:
            enrollments.append({"course": course_of[sid], "term": next_id, "status": "planned",
                                "grade": None, "mode": "letter", "section": sid})
    return {**student, "enrollments": enrollments,
            "terms": [{"id": t["id"], "label": t["label"], "state": t["state"],
                       "off_campus": t["off_campus"]} for t in terms]}


class Edit(BaseModel):
    op: str
    term: Optional[str] = None
    course: Optional[str] = None
    tablet: Optional[str] = None


class PlanRequest(BaseModel):
    student_id: str
    majors: Optional[list[str]] = None
    credit_cap: Optional[int] = None
    edits: list[Edit] = []


class OptionsRequest(PlanRequest):
    term: str
    tablet: Optional[str] = None


class ScheduleRequest(BaseModel):
    term: str
    section_ids: list[str]


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    yield


app = FastAPI(title="CourseGraph", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["http://127.0.0.1:5320", "http://localhost:5320"],
    allow_methods=["*"], allow_headers=["*"])


def _student(student_id):
    db.init_db()
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(404, f"Unknown student {student_id!r}")
    return student


@app.get("/api/health")
def health():
    catalog = load_catalog()
    return {"ok": True, "catalog": catalog.origin, "catalog_year": catalog.catalog_year}


@app.get("/api/catalog")
def get_catalog():
    return load_catalog().public()


@app.get("/api/students")
def get_students():
    db.init_db()
    return db.list_students()


@app.get("/api/students/{student_id}")
def get_student(student_id: str):
    return student_view(_student(student_id), load_sections(load_catalog()))


@app.get("/api/sections")
def get_sections(term: Optional[str] = None):
    sections = load_sections(load_catalog())
    return [s for s in sections if term is None or s["term"] == term]


@app.put("/api/students/{student_id}/schedule")
def put_schedule(student_id: str, body: ScheduleRequest):
    student = _student(student_id)
    sections = load_sections(load_catalog())
    chosen, error = check_schedule(student, body.term, body.section_ids, sections)
    if error:
        raise HTTPException(422, error)
    db.save_schedule(student_id, body.term, [s["id"] for s in chosen])
    return {"term": body.term, "section_ids": [s["id"] for s in chosen],
            "clashes": detect_clashes(chosen)}


@app.post("/api/plan")
def post_plan(body: PlanRequest):
    student = _student(body.student_id)
    catalog = load_catalog()
    try:
        return build_plan(student, catalog, load_sections(catalog), body.majors,
                          [e.model_dump() for e in body.edits], body.credit_cap)
    except PlanError as err:
        raise HTTPException(422, str(err))


@app.post("/api/options")
def post_options(body: OptionsRequest):
    student = _student(body.student_id)
    catalog = load_catalog()
    try:
        return build_options(student, catalog, load_sections(catalog), body.term, body.tablet,
                             body.majors, [e.model_dump() for e in body.edits], body.credit_cap)
    except PlanError as err:
        raise HTTPException(422, str(err))
