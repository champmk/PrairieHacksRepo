"""Student database: stdlib sqlite3, seeded from ``data/students.json``.

Three tables. ``students`` holds the profile, ``enrollments`` the record
(completed, in progress, withdrawn, failed, dropped, AP / transfer), and
``schedule`` the sections picked on page 1. Plan edits are not stored: the
front end sends them with every POST /api/plan, which keeps the planner pure.
"""
import json
import os
import sqlite3
from pathlib import Path

from .catalog import DATA_DIR

SEED_FILE = DATA_DIR / "students.json"

SCHEMA = """
CREATE TABLE students (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, summary TEXT, start_term TEXT NOT NULL,
    current_term TEXT NOT NULL, catalog_year TEXT, majors TEXT NOT NULL,
    credit_cap INTEGER NOT NULL, off_campus TEXT NOT NULL, position INTEGER NOT NULL);
CREATE TABLE enrollments (
    student TEXT NOT NULL REFERENCES students(id), position INTEGER NOT NULL,
    course TEXT NOT NULL, term TEXT, status TEXT NOT NULL, grade TEXT, mode TEXT NOT NULL,
    attempt INTEGER NOT NULL, title TEXT, credits REAL, note TEXT,
    PRIMARY KEY (student, position));
CREATE TABLE schedule (
    student TEXT NOT NULL REFERENCES students(id), term TEXT NOT NULL,
    position INTEGER NOT NULL, section_id TEXT NOT NULL,
    PRIMARY KEY (student, term, section_id));
"""


def db_path():
    return Path(os.environ.get("COURSEGRAPH_DB") or DATA_DIR / "students.db")


def connect(path=None):
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=None, seed_file=None):
    """Create and seed the database when the file does not exist yet."""
    path = Path(path or db_path())
    if path.exists():
        return path
    with open(seed_file or SEED_FILE, encoding="utf-8") as f:
        seed = json.load(f)
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
        for n, s in enumerate(seed["students"]):
            conn.execute(
                "INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?)",
                (s["id"], s["name"], s.get("summary"), s["start_term"], s["current_term"],
                 s.get("catalog_year"), json.dumps(s.get("majors") or []), s.get("credit_cap") or 18,
                 json.dumps(s.get("off_campus") or []), n))
            attempts = {}
            for i, e in enumerate(s.get("enrollments") or []):
                attempts[e["course"]] = attempts.get(e["course"], 0) + 1
                conn.execute(
                    "INSERT INTO enrollments VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (s["id"], i, e["course"], e.get("term"), e["status"], e.get("grade"),
                     e.get("mode") or "letter", attempts[e["course"]], e.get("title"),
                     e.get("credits"), e.get("note")))
            for term, ids in (s.get("schedule") or {}).items():
                for i, sid in enumerate(ids):
                    conn.execute("INSERT INTO schedule VALUES (?,?,?,?)", (s["id"], term, i, sid))
        conn.commit()
    finally:
        conn.close()
    return path


def list_students():
    conn = connect()
    try:
        rows = conn.execute("SELECT id, name, summary FROM students ORDER BY position").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student(student_id):
    """The stored student as plain data, or ``None``."""
    conn = connect()
    try:
        s = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if s is None:
            return None
        enrollments = []
        for e in conn.execute("SELECT * FROM enrollments WHERE student = ? ORDER BY position", (student_id,)):
            row = {"course": e["course"], "term": e["term"], "status": e["status"],
                   "grade": e["grade"], "mode": e["mode"], "attempt": e["attempt"]}
            for key in ("title", "credits", "note"):
                if e[key] is not None:
                    row[key] = e[key]
            if isinstance(row.get("credits"), float) and row["credits"].is_integer():
                row["credits"] = int(row["credits"])
            enrollments.append(row)
        schedule = {}
        for r in conn.execute("SELECT term, section_id FROM schedule WHERE student = ? "
                              "ORDER BY term, position", (student_id,)):
            schedule.setdefault(r["term"], []).append(r["section_id"])
        return {"id": s["id"], "name": s["name"], "summary": s["summary"],
                "start_term": s["start_term"], "current_term": s["current_term"],
                "catalog_year": s["catalog_year"], "majors": json.loads(s["majors"]),
                "credit_cap": s["credit_cap"], "off_campus": json.loads(s["off_campus"]),
                "enrollments": enrollments, "schedule": schedule}
    finally:
        conn.close()


def save_schedule(student_id, term, section_ids):
    conn = connect()
    try:
        conn.execute("DELETE FROM schedule WHERE student = ? AND term = ?", (student_id, term))
        for i, sid in enumerate(section_ids):
            conn.execute("INSERT INTO schedule VALUES (?,?,?,?)", (student_id, term, i, sid))
        conn.commit()
    finally:
        conn.close()
