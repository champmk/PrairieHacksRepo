# GrinPath backend

A degree planner for Grinnell College: `plan = f(student, majors, edits, credit_cap)`.
Same input, same output. The API is defined in [`CONTRACT.md`](CONTRACT.md).

## Run

```
cd backend
python -m pip install --user -r requirements.txt
python -m uvicorn coursegraph.api:app --port 8100
```

Python 3.13, FastAPI, uvicorn, stdlib `sqlite3`. CORS allows `http://127.0.0.1:5320` and
`http://localhost:5320`. `data/students.db` is created and seeded from `data/students.json` on first
start; delete the file to reset the demo students.

Tests (stdlib `unittest`, no network, no HTTP client):

```
cd backend
python -m unittest discover -s tests
```

Environment overrides: `COURSEGRAPH_DB` (database file), `COURSEGRAPH_CATALOG` (catalog file).

## Routes

| Route | What it returns |
|---|---|
| `GET /api/catalog` | courses, programs with slots, divisions |
| `GET /api/students`, `GET /api/students/{id}` | student list; one record with term states and schedule |
| `GET /api/sections?term=2027SP` | sections for page 1 |
| `PUT /api/students/{id}/schedule` | saves next-term sections, returns clashes; 422 otherwise |
| `POST /api/plan` | terms, tablets, edges, warnings, progress, totals, unscheduled |
| `POST /api/options` | courses that can fill a tablet, eligible first |
| `GET /api/health` | which catalog file is loaded |

## Layout

```
coursegraph/
  terms.py       term ids, the eight terms, past / current / next / future
  catalog.py     load + normalize the catalog and sample files; slots and routes
  prereq.py      prerequisite trees: residue, text, chain depth
  ledger.py      1 Ledger      what counts
  matching.py    2 Match       slots <-> courses, route choice
  distribute.py  3 Distribute  unmatched slots -> terms
  validate.py    4 Validate    warnings, arrows, schedule gate, clashes
  plan.py        composes the four stages; edits; options
  db.py          sqlite3 student store
  api.py         FastAPI routes
  colss.py       offline COLSS snapshot importer
data/            catalog, sample, derived and seed files (see below)
tests/           unittest suites
tools/           generator for the sample (mock) data files
```

The four stages are pure: plain data in, plain data out. Only `db.py` and `api.py` touch files.

## How each stage works

**Ledger.** One row per enrollment. W, F and dropped earn nothing (`not_counted`, with the mark). A
course may be repeated only after a D or F; the latest attempt counts and the old D stops counting.
Any other repeat earns nothing and is an error. AP and transfer rows (`term: null`) are degree credit
that sits before every term. A grade below C, or S/D/F, never counts toward a major, and a D does not
clear a prerequisite. Cross-listed ids are one course. Credits past 48 in a department or 92 in a
division stop counting toward 124; AP credit is divisional, so it skips the department cap.

**Match.** Every `all` course is a slot and a choose-n group is n slots. Courses are offered to a
maximum bipartite matching (Kuhn's augmenting paths) in tier order, completed, in progress, planned,
projected, then earlier term. A course that could fill two slots is moved to wherever it leaves the
other slot fillable, so CSC-211 and CSC-213 together fill Systems and the Elective. A course fills one
slot per major. Two majors may not share credits, so a course that is credit in one major can only
fill a cognate ("also required") slot in the other. Unmatched slots become requirement tablets (R).

**Route.** When a program has several sample routes, the one that best overlaps the record wins: 2
points for a course taken in the route's own term, 1 for any other term.

**Distribute.** List scheduling. Units are ordered by the longest chain of units still depending on
them, then route term. The target is the route term, pulled earlier when the unit's prerequisites
were finished early: `min(route term, latest prerequisite + the route's gap after it)`. Each unit
takes the first term at or after its target where it is not barred by a remove edit, it is offered
(season and even/odd year), its prerequisites are in strictly earlier terms, and the load fits. The
normal load (16) is tried first, then `credit_cap`. A choose slot with nothing chosen is `open`: it
waits for the prerequisites of its easiest option, and stands for whichever options the student could
really take there. If a required course needs a prerequisite nothing supplies and an open slot lists
it, the slot takes it (MAT-215 needs MAT-133, so a Mathematics elective becomes MAT-133). Units that
fit nowhere go to `unscheduled` with a reason and an error.

**Validate.** Checks planned and projected tablets only; history is never re-checked. A missing
prerequisite gives a warning and an edge from the tablet to the term just before it, even when that
term is past. Also: corequisites, offerings, load over 18 (MUS lessons and ensembles, PHE and FYE-100
excluded), load under 12 (current term, and a next term the student has started to schedule; later
terms are unfinished by nature), both caps, duplicates, chain too long, tutorial in term 1, FYE in term 2,
and 124 credits on the last term. Consent, placement and anything the data cannot state are reported,
never assumed.

**Edits** replay in order on next and future terms. `add` makes `add:<course>:<term>`. `remove`
deletes an added or planned tablet, or bars a requirement slot from that term. `swap` replaces a
course; on a requirement tablet the course must be one of the slot's options, and the slot is then
pinned to that term and checked rather than moved. Anything else is ignored with `edit_ignored`.

**Planned** exists only in the next term and only from the saved schedule. `PUT schedule` accepts the
next term only (the current term is registered and read-only), requires every section to exist in that
term and allows one section per course. Clashes are a shared day with overlapping times.

## Data: what is real, what is not

| File | Status | Source |
|---|---|---|
| `data/grinnell_catalog.json` | **Real.** CS and Mathematics programs, 55 courses, the two CS four-year plans, divisions, policies. Written by the catalog pass, not by this code. | Grinnell Academic Catalog 2026-27 (wording for CS and Math matches 2025-26), the CS and Mathematics advising guide pages, the Mathematics course-sequence page. URLs are in the file's `meta.sources` and on every record. |
| `data/derived.json` | **Derived.** One Mathematics route. The advising guide has four-year plans for CS only; this one follows the prerequisite chain on the course-sequence page, and the term placement is ours. | Flagged `origin: "derived"`. |
| `data/sample_courses.json` | **Sample (mock).** 335 courses outside CS and Math, about a dozen per major, each with a description, COLSS-style prerequisite text, offering terms and location. Its `descriptions` table holds mock descriptions for the 55 real courses. | Invented for the demo, not catalog facts. Flagged `origin: "sample"`. A real course with the same id always wins. Generated by `tools/build_sample_data.py`. |
| `data/sample_programs.json` | **Sample (mock).** A program and one four-year route for each of the 26 majors other than CS and Mathematics. Major names and divisions are real; requirements and routes are invented. | Flagged `origin: "sample"`. Generated. |
| `data/sections.json` | **Sample.** 656 Fall 2026 and Spring 2027 sections: every course offered in a term has one to three. Every instructor name is fictional. | Placeholders, flagged `origin: "sample"`. Generated. |
| `data/students.json` | **Fictional.** Three invented students. | No real people or records. |
| `data/fixture_catalog.json` | **Fixture.** Small stand-in with the real file's shape. Used by the unit tests, and as a fallback if the real file is missing. | Not catalog data. |

Slots derived from the catalog text (marked `derived: true` in `GET /api/catalog`):

- CS Electives is "4 credits", read as one slot; options under 4 credits are left out.
- The Mathematics sequence requirement is one slot whose options are the closing course of each
  sequence (MAT-314, 317, 322, 336, STA-336). The closer's prerequisite is the course before it.
- "Remaining credits to reach 32" is three elective slots; one is limited to 300/400-level options
  so the 16 upper-level credits are met.

Unknown stays unknown:

- `offered: ["Fall or Spring"]` means the term is not stated. It never blocks a placement and gives a
  soft `not_offered` warning asking the student to confirm.
- CSC-313 and CSC-315 are in the advising guide but not the catalog: credits default to 4
  (`credits_assumed: true`), prerequisites and offerings are unknown and reported.
- MAT-444 "varies by topic" is an unknown prerequisite. MAT-131's placement rule is a consent leaf.
- AP credit counts toward a major only where the program data lists it (`ap_major_credit`). Neither
  real program does, so an AP course gives a `major_grade` warning and the requirement stays open.
- FYE-100 is named by the catalog policies but has no course page: its credits and terms are sample.
- The catalog does not name the tutorial's semester; the first-term check is the advising convention
  and is a soft warning.

Not checked by the planner (kept as text in `rules`): 20 CSC credits at Grinnell, the 4-credit limit
on outside credit in the CS core, the CSC-208 / MAT-218 exclusion, GPA, residency, the 24-credit AP
limit, and the limits on practica, performance and individual-study credits.

## Sample data generator

`tools/sample_majors.py` is the hand-written source for the mock majors, courses, descriptions and
the pool of fictional instructor names. `tools/build_sample_data.py` turns it into the three sample
files above. It checks that every route can be walked (each course offered in its term, prerequisites
in earlier terms) and that no instructor name matches a known real one.

```
cd backend
python tools/build_sample_data.py
```

The run is deterministic. `tools/legacy_sections.json` holds the first 73 hand-made sections; their
ids, times and seat counts are kept because tests and the demo students' schedules refer to them.
Sample programs use the same shape as the real ones: `all` and `choose` groups, and "also required"
groups with no credits (cognates such as calculus for Physics), which two majors may share.

## COLSS snapshot importer (offline)

`coursegraph/colss.py` converts saved COLSS (Ellucian Self-Service) responses into `data/sections.json`.
It makes no network calls and handles no logins or cookies.

```
python -m coursegraph.colss import snapshot.json --out data/sections.json
```

A snapshot is `{"search": <PostSearchCriteria response>, "sections": {"<course Id>": <Sections
response>}}`. `sections_from_colss(search_json, sections_json_by_course)` is the pure function behind
it. The documented examples name `Meetings` and `FormattedMeetingTimes` but do not show their
contents, so the parser accepts the usual Ellucian field spellings and otherwise leaves `meetings`
empty. Importing replaces the sample sections; the seeded schedules refer to sample section ids, so
reset `data/students.db` after an import.
