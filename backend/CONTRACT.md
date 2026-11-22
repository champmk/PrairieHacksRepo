# CourseGraph API contract

The front end (`frontend/`) and the Python backend (`backend/`) both build against this file. Change it only with sign-off from both sides. All routes are under `/api`, JSON in and out. The dev server listens on `http://127.0.0.1:8100`, and Vite proxies `/api` to it.

Design reference: `docs/CourseGraph_Backend_Logic.html` (the one-page backend sheet).

## Terms

A term id is `YYYYFA` or `YYYYSP`, for example `2026FA`. Each student has eight terms, starting at `start_term`. The `state` of a term is computed from the student's `current_term`:

| state | meaning | what tablets can be |
|---|---|---|
| `past` | before the current term | `completed`, `not_counted` |
| `current` | in progress now | `in_progress`, `not_counted` |
| `next` | the term after the current one | `planned` (page 1 picks), `projected`, `open` |
| `future` | later terms | `projected`, `open` |

"Planned" exists only in the current or next term, and only for a course with a real section (picked on page 1, the Course Picker). Every later tablet is `projected` (a course the plan places) or `open` (a requirement slot with no course chosen).

## GET /api/catalog

```json
{
  "catalog_year": "2025-26",
  "courses": [
    {"id": "CSC-151", "title": "Functional Problem Solving", "credits": 4, "department": "CSC",
     "division": "Science", "level": 100, "offered": ["Fall", "Spring"], "offered_note": null,
     "prereq_text": "None", "prereq": null, "source_url": "https://..."}
  ],
  "programs": [
    {"id": "CS", "name": "Computer Science", "slots": [
      {"id": "CS:CSC-151", "label": "CSC-151", "kind": "course", "options": ["CSC-151"], "route_term": 0},
      {"id": "CS:elective:1", "label": "CS elective", "kind": "choose", "options": ["CSC-312", "..."], "route_term": 7}
    ], "rules": ["32 credits", "..."], "source_url": "https://..."}
  ],
  "divisions": {"CSC": "Science", "ENG": "Humanities"}
}
```

`prereq` is a tree: `{"course": "CSC-161"}`, `{"all": [...]}`, `{"any": [...]}`, `{"coreq": "MAT-220"}`, `{"consent": true}`, or `null`. `route_term` is the 0-based semester index where the department's sample plan puts the slot.

## GET /api/students and GET /api/students/{id}

`GET /api/students` returns `[{"id", "name", "summary"}]` for the student switcher. One student:

```json
{
  "id": "alex", "name": "Alex Rivera", "start_term": "2025FA", "current_term": "2026FA",
  "majors": ["CS"], "credit_cap": 18,
  "terms": [{"id": "2025FA", "label": "Fall 2025", "state": "past"}],
  "enrollments": [
    {"course": "CSC-151", "term": "2025FA", "status": "completed", "grade": "A-", "mode": "letter"},
    {"course": "MAT-215", "term": "2026SP", "status": "withdrawn", "grade": "W", "mode": "letter"},
    {"course": "CSC-208", "term": "2026FA", "status": "in_progress", "grade": null, "mode": "letter"},
    {"course": "MAT-131", "term": null, "status": "completed", "grade": "AP", "mode": "transfer"}
  ],
  "schedule": {"2026FA": ["2026FA-CSC-208-01"], "2027SP": ["2027SP-CSC-207-01"]}
}
```

Enrollment `status` is one of `completed`, `in_progress`, `planned`, `withdrawn`, `failed`, or `dropped`. `mode` is `letter`, `sdf`, or `transfer` (AP and transfer credit, `term: null`).

## GET /api/sections?term=2027SP

```json
[{"id": "2027SP-CSC-151-01", "course": "CSC-151", "term": "2027SP", "number": "01",
  "instructor": "Samuel Rebelsky", "available": 10, "capacity": 24,
  "meetings": [{"days": ["M", "W", "F"], "start": "08:00", "end": "09:20", "room": "Noyce 3813"}]}]
```

## PUT /api/students/{id}/schedule

Body: `{"term": "2027SP", "section_ids": ["2027SP-CSC-207-01", "..."]}`. The term must be the student's current or next term, or the request returns 422. Each section must exist for that term, and only one section per course is allowed. The response is the saved schedule plus clashes:

```json
{"term": "2027SP", "section_ids": ["..."], "clashes": [{"a": "2027SP-CSC-211-01", "b": "2027SP-MAT-321-01"}]}
```

For the current term the schedule is read-only (registered), so a PUT with `term` = current returns 422.

## POST /api/plan

Body:

```json
{"student_id": "alex", "majors": ["CS", "MATH"], "credit_cap": 18,
 "edits": [
   {"op": "add", "term": "2027FA", "course": "PHI-101"},
   {"op": "remove", "term": "2028SP", "tablet": "slot:CS:CSC-341"},
   {"op": "swap", "term": "2027FA", "tablet": "slot:CS:elective:1", "course": "CSC-321"}
 ]}
```

Edits apply in order to the student's projected terms only (`next` and `future`). Rules:

- `add` puts a course in a term.
- `remove` deletes a tablet the student added. For a requirement tablet, it bars that slot from that term, so the planner moves it to another term.
- `swap` fills or replaces a tablet's course. For a requirement tablet, the course must be one of the slot's options.
- An edit that targets a past or current term, or a locked tablet, is ignored and reported in `warnings` with code `edit_ignored`.

Response:

```json
{
  "terms": [
    {"id": "2027FA", "label": "Fall 2027", "season": "Fall", "year": 2027, "index": 4,
     "state": "future", "complete": false, "credits": 16,
     "tablets": [
       {"id": "slot:CS:CSC-301", "course": "CSC-301", "title": "Analysis of Algorithms", "credits": 4,
        "status": "projected", "mark": null, "required": true, "locked": false,
        "slot": {"id": "CS:CSC-301", "program": "CS", "label": "CSC-301", "options": ["CSC-301"]},
        "counts_for": ["CS · CSC-301"], "warnings": ["w3"]}
     ]}
  ],
  "edges": [
    {"id": "e1", "from_tablet": "slot:CS:CSC-341", "from_term": "2028SP", "to_term": "2027FA",
     "kind": "prereq", "missing": ["CSC-207"], "message": "CSC-341 needs CSC-207 before Spring 2028"}
  ],
  "warnings": [
    {"id": "w3", "severity": "warning", "code": "prereq_missing", "message": "...", "term": "2028SP", "tablet": "slot:CS:CSC-341"}
  ],
  "progress": [
    {"program": "CS", "name": "Computer Science", "total": 11, "done": 4, "in_progress": 1, "planned": 6,
     "slots": [{"id": "CS:CSC-151", "label": "CSC-151", "status": "completed", "course": "CSC-151", "term": "2025FA"}]}
  ],
  "totals": {"counted": 32, "in_progress": 13, "planned": 79, "required": 124,
             "by_department": {"CSC": 20}, "by_division": {"Science": 36}},
  "unscheduled": [{"slot": "CS:CSC-364", "label": "CSC-364", "reason": "Prerequisites not met in time"}]
}
```

Tablet fields:

- `id` is stable across recalculations: `enr:<course>:<term>` for record tablets, `slot:<slot id>` for requirement tablets, and `add:<course>:<term>` for added courses.
- `status` is one of `completed`, `not_counted` (W, F, dropped; `mark` holds the letter), `in_progress`, `planned`, `projected`, or `open` (a requirement with no course yet; `course` is null).
- `required` is true when the tablet fills a major slot (the R).
- `locked` is true for past, current, and not-counted tablets.

A term's `complete` is true when the term is past and every counted tablet is completed.

Warning `code` values:

- `prereq_missing`, which also creates an edge from the tablet to the previous term
- `coreq_missing`
- `not_offered`
- `load_high` (more than 18 credits) and `load_low` (fewer than 12)
- `dept_cap` (48) and `division_cap` (92)
- `duplicate`, `repeat_not_allowed`
- `chain_too_long`
- `unscheduled`
- `grad_credits` (fewer than 124 counted by the last term)
- `tutorial_missing`, `fye_missing`
- `major_grade` (below C or S/D/F, so it does not count for the major)
- `consent_required`
- `edit_ignored`

Severity is either `warning` or `error`.

## POST /api/options

This feeds the sidebar shown when a tablet is clicked. Body: the same fields as `/api/plan` plus `{"term": "2027FA", "tablet": "slot:CS:elective:1"}`. It returns the courses that can fill that tablet, ordered eligible first:

```json
{"tablet": "slot:CS:elective:1", "required": true, "label": "CS elective",
 "options": [{"course": "CSC-321", "title": "...", "credits": 4, "eligible": true, "reason": null},
             {"course": "CSC-322", "title": "...", "credits": 4, "eligible": false, "reason": "Spring only"}]}
```

A requirement tablet returns only that slot's options. A non-requirement tablet, or a `term` with no `tablet` (the + button), returns every catalog course not already in the plan.
