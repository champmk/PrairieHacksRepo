"""CourseGraph backend: a pure degree planner behind a small FastAPI app.

plan = f(student, majors, edits, credit_cap). Same input, same output.
Pipeline: Ledger -> Match -> Distribute -> Validate (see plan.py).
"""
