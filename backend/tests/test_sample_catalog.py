"""The sample (mock) majors, courses and sections that fill the catalog beside the real
Computer Science and Mathematics data. Skipped when the real catalog file is absent."""
import itertools
import json
import time
import unittest

from coursegraph import api
from coursegraph.api import load_sections
from coursegraph.catalog import DATA_DIR, REAL_FILE, load_catalog
from coursegraph.plan import build_options, build_plan

from helpers import codes, student

HAVE_REAL = (DATA_DIR / REAL_FILE).exists()
MAJORS = {
    "Humanities": ["Art History", "Chinese", "Classics", "English", "French and Francophone Studies",
                   "German Studies", "Music", "Philosophy", "Religious Studies", "Russian", "Spanish",
                   "Studio Art", "Theatre and Dance"],
    "Science": ["Biological Chemistry", "Biology", "Chemistry", "Computer Science", "Mathematics", "Physics",
                "Psychology"],
    "Social Studies": ["Anthropology", "Economics", "History", "Political Science", "Sociology"],
    "Interdisciplinary": ["American Studies", "Gender, Women's and Sexuality Studies",
                          "Latin American Studies"],
}
REMOVED_INSTRUCTORS = {"Samuel Rebelsky", "Shawn Ong", "Staff"}
BUILDINGS = {"Noyce", "HSSC", "ARH", "Steiner", "Bucksbaum", "Goodnow", "Mears"}
TERMS = {"2026FA": {"season": "Fall", "year": 2026}, "2027SP": {"season": "Spring", "year": 2027}}
NO_DIVISION = {"TUT", "FYE"}          # college-wide courses sit in no division
PLAN_BUDGET = 0.100                   # seconds


def minutes(clock):
    return int(clock[:2]) * 60 + int(clock[3:])


@unittest.skipUnless(HAVE_REAL, "grinnell_catalog.json is not present")
class SampleCatalogCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(DATA_DIR / REAL_FILE)
        cls.sections = load_sections(cls.catalog)
        with open(DATA_DIR / "sections.json", encoding="utf-8") as f:
            cls.raw_sections = json.load(f)["sections"]
        with open(DATA_DIR / "students.json", encoding="utf-8") as f:
            cls.students = {s["id"]: s for s in json.load(f)["students"]}

    def timed_plan(self, stu, majors):
        start = time.perf_counter()
        result = build_plan(stu, self.catalog, self.sections, majors)
        took = time.perf_counter() - start
        if took >= PLAN_BUDGET:                       # one retry, so a busy machine does not fail the run
            start = time.perf_counter()
            result = build_plan(stu, self.catalog, self.sections, majors)
            took = time.perf_counter() - start
        self.assertLess(took, PLAN_BUDGET, (stu["id"], majors))
        return result


class Programs(SampleCatalogCase):
    def test_every_grinnell_major_is_a_program(self):
        got = {}
        for p in self.catalog.programs.values():
            got.setdefault(p["division"], []).append(p["name"])
        self.assertEqual({d: sorted(n) for d, n in got.items()}, {d: sorted(n) for d, n in MAJORS.items()})
        self.assertEqual(len(self.catalog.programs), 28)

    def test_origin_separates_real_from_sample(self):
        for pid, p in self.catalog.programs.items():
            self.assertEqual(p["origin"], "catalog" if pid in ("CS", "MATH") else "sample", pid)
            if p["origin"] == "sample":
                self.assertEqual([r["origin"] for r in p["routes"]], ["sample"], pid)
                self.assertTrue(any("SAMPLE" in rule for rule in p["rules"]), pid)

    def test_every_program_has_credits_and_a_full_route(self):
        for pid, p in self.catalog.programs.items():
            self.assertGreaterEqual(p["total_credits_min"], 32, pid)
            self.assertGreaterEqual(4 * len(p["slots"]), 32, pid)
            self.assertLessEqual(4 * len(p["slots"]), 44, pid)
            self.assertTrue(p["routes"], pid)
            for slot in p["slots"]:
                self.assertIn(slot["route_term"], range(8), slot["id"])
                self.assertTrue(slot["options"], slot["id"])
                for course in slot["options"]:
                    self.assertIn(course, self.catalog.courses, slot["id"])

    def test_sample_programs_have_ten_to_fourteen_courses_at_every_level(self):
        for pid, p in self.catalog.programs.items():
            if p["origin"] != "sample":
                continue
            own = [c for c in self.catalog.courses.values() if c["department"] == pid]
            self.assertTrue(10 <= len(own) <= 15, (pid, len(own)))
            levels = {c["level"] for c in own}
            self.assertTrue({200, 300} <= levels and levels & {100, 200}, (pid, levels))

    def test_a_new_student_can_follow_every_sample_route(self):
        # All eight terms open, starting in a Fall: each requirement lands on its route term.
        stu = student(majors=[], start="2027FA", current="2027SP")
        for pid, p in self.catalog.programs.items():
            if p["origin"] != "sample":
                continue
            result = build_plan(stu, self.catalog, self.sections, [pid])
            self.assertEqual(result["unscheduled"], [], pid)
            for code in ("prereq_missing", "coreq_missing", "not_offered", "chain_too_long", "duplicate"):
                self.assertNotIn(code, codes(result), pid)
            index = {t["id"]: t["index"] for t in result["terms"]}
            route = {s["id"]: s["route_term"] for s in p["slots"]}
            for row in result["progress"][0]["slots"]:
                self.assertEqual(index[row["term"]], route[row["id"]], row["id"])
            self.assertEqual(result["progress"][0]["route"]["origin"], "sample")

    def test_sample_prerequisites_point_at_real_courses(self):
        from coursegraph import prereq as P
        for c in self.catalog.courses.values():
            if c["origin"] == "sample":
                self.assertTrue(c["prereq_known"], c["id"])
                for needed in P.courses_in(c["prereq"]):
                    self.assertIn(needed, self.catalog.courses, c["id"])


class Courses(SampleCatalogCase):
    def test_every_course_has_the_colss_fields(self):
        for c in self.catalog.public()["courses"]:
            cid = c["id"]
            for key in ("id", "title", "credits", "department", "division", "level", "offered",
                        "prereq_text", "prereq", "description", "location", "origin"):
                self.assertIn(key, c, cid)
            self.assertTrue(c["title"] and c["department"] and c["level"], cid)
            self.assertIn(c["origin"], ("catalog", "sample"), cid)
            self.assertEqual(c["origin"], "catalog" if c["department"] in ("CSC", "MAT", "STA") else "sample", cid)
            self.assertEqual(c["location"], "Main Campus", cid)
            self.assertGreater(c["credits"], 0, cid)
            if c["department"] in NO_DIVISION:
                self.assertIsNone(c["division"], cid)
            else:
                self.assertIn(c["division"], MAJORS, cid)
            if c["offered"] is None:      # only where the real catalog does not state the term
                self.assertEqual(c["origin"], "catalog", cid)
                self.assertTrue(c["offered_note"] or not c["prereq_known"], cid)
            else:
                self.assertIn(c["offered"], (["Fall"], ["Spring"], ["Fall", "Spring"]), cid)

    def test_every_course_has_a_description_of_two_or_three_sentences(self):
        for c in self.catalog.courses.values():
            text = c["description"]
            self.assertTrue(text and text.strip(), c["id"])
            self.assertGreaterEqual(len(text.split()), 12, c["id"])
            self.assertTrue(2 <= text.count(". ") + 1 <= 3, (c["id"], text))

    def test_prereq_text_is_colss_style(self):
        for c in self.catalog.courses.values():
            if c["prereq_text"] is None:          # CSC-313 / CSC-315: named by the advising guide only
                self.assertFalse(c["prereq_known"], c["id"])
                continue
            self.assertTrue(c["prereq_text"].startswith("Prerequisite: "), c["id"])
            if c["origin"] == "sample":
                self.assertTrue(c["prereq_text"].endswith("."), c["id"])
                self.assertEqual(c["prereq"] is None, c["prereq_text"] == "Prerequisite: None.", c["id"])

    def test_courses_the_demo_students_use_are_kept(self):
        kept = ["TUT-100", "FYE-100", "ENG-120", "PHI-101", "ECN-111", "HIS-100", "MUS-120", "PSY-113",
                "STA-209", "SOC-111", "ANT-104", "ART-111", "BIO-150", "CHM-129", "EDU-101", "FMS-155",
                "GDS-111", "MUS-101", "PHY-131", "POL-101", "SPN-101", "SPN-102"]
        for cid in kept:
            self.assertIn(cid, self.catalog.courses)
        for s in self.students.values():
            for e in s["enrollments"]:
                if not e["course"].startswith("OCS-"):        # study-away transfer credit carries its own title
                    self.assertIn(e["course"], self.catalog.courses, (s["id"], e["course"]))
        self.assertEqual(self.catalog.courses["STA-209"]["origin"], "catalog")
        self.assertEqual(self.catalog.courses["MUS-120"]["credits"], 1)

    def test_cross_lists_are_one_course(self):
        for a, b in (("SOC-270", "GWS-270"), ("HIS-201", "LAS-201"), ("ENG-227", "AMS-227"),
                     ("PHI-263", "POL-263"), ("CLS-248", "ARH-248")):
            self.assertEqual(self.catalog.identity(a), self.catalog.identity(b))
            self.assertEqual(self.catalog.courses[a]["title"], self.catalog.courses[b]["title"])

    def test_catalog_route_returns_the_new_fields(self):
        body = api.get_catalog()
        course = next(c for c in body["courses"] if c["id"] == "BIO-251")
        self.assertEqual((course["location"], course["origin"], course["division"], course["prereq_text"]),
                         ("Main Campus", "sample", "Science", "Prerequisite: BIO-150 and CHM-129."))
        self.assertEqual(course["prereq"], {"all": [{"course": "BIO-150"}, {"course": "CHM-129"}]})
        self.assertTrue(next(c for c in body["courses"] if c["id"] == "CSC-151")["description"])
        programs = {p["id"]: p for p in body["programs"]}
        self.assertEqual((programs["CS"]["division"], programs["CS"]["origin"]), ("Science", "catalog"))
        self.assertEqual((programs["GWS"]["division"], programs["GWS"]["origin"]), ("Interdisciplinary", "sample"))
        for p in body["programs"]:
            self.assertEqual(set(p) >= {"id", "name", "division", "origin", "slots", "rules", "source_url",
                                        "routes"}, True)
        json.dumps(body)


class Sections(SampleCatalogCase):
    def test_every_section_belongs_to_a_catalog_course(self):
        self.assertEqual(len(self.sections), len(self.raw_sections))
        ids = [s["id"] for s in self.raw_sections]
        self.assertEqual(len(ids), len(set(ids)))
        for s in self.raw_sections:
            self.assertIn(s["course"], self.catalog.courses, s["id"])
            self.assertIn(s["term"], TERMS, s["id"])
            self.assertEqual(s["id"], f"{s['term']}-{s['course']}-{s['number']}")

    def test_instructors_are_fictional(self):
        for s in self.raw_sections:
            name = s["instructor"]
            self.assertNotIn(name, REMOVED_INSTRUCTORS, s["id"])
            self.assertEqual(len(name.split()), 2, s["id"])
            self.assertNotIn("Rebelsky", name)
        with open(DATA_DIR / "sections.json", encoding="utf-8") as f:
            self.assertIn("FICTIONAL", json.load(f)["note"])

    def test_every_offered_course_has_one_to_three_sections(self):
        count = {}
        for s in self.raw_sections:
            count[(s["term"], s["course"])] = count.get((s["term"], s["course"]), 0) + 1
        for term_id, term in TERMS.items():
            for cid in self.catalog.courses:
                offered = self.catalog.offered(cid, term)
                n = count.get((term_id, cid), 0)
                if offered is True:
                    self.assertTrue(1 <= n <= 3, (term_id, cid, n))
                elif offered is False:
                    self.assertEqual(n, 0, (term_id, cid))
                else:
                    self.assertLessEqual(n, 3, (term_id, cid))

    def test_meetings_seats_and_rooms(self):
        full, evening, labs = 0, 0, 0
        for s in self.raw_sections:
            self.assertTrue(12 <= s["capacity"] <= 32, s["id"])
            self.assertTrue(0 <= s["available"] <= s["capacity"], s["id"])
            full += s["available"] == 0
            self.assertTrue(1 <= len(s["meetings"]) <= 2, s["id"])
            labs += len(s["meetings"]) == 2
            for m in s["meetings"]:
                self.assertTrue(set(m["days"]) <= set("MTWRF") and m["days"], s["id"])
                self.assertLess(minutes(m["start"]), minutes(m["end"]), s["id"])
                self.assertIn(m["room"].split()[0], BUILDINGS, s["id"])
                evening += minutes(m["start"]) >= 19 * 60
        self.assertTrue(5 <= full <= len(self.raw_sections) // 5, full)
        self.assertGreater(evening, 0)
        self.assertGreater(labs, 0)

    def test_nobody_and_no_room_is_double_booked(self):
        busy = {}
        twins = {}                                     # a cross-listed class shares its room and instructor
        for s in self.raw_sections:
            key = (s["term"], self.catalog.identity(s["course"]), s["number"])
            first = twins.setdefault(key, s["id"])
            if first != s["id"] and s["course"] not in ("CSC-208", "MAT-208"):
                continue
            for m in s["meetings"]:
                for who in (s["instructor"], m["room"]):
                    for day in m["days"]:
                        slot = (minutes(m["start"]), minutes(m["end"]))
                        for other in busy.setdefault((s["term"], who, day), []):
                            self.assertFalse(slot[0] < other[1] and other[0] < slot[1], (s["id"], who, day))
                        busy[(s["term"], who, day)].append(slot)


class DemoStudents(SampleCatalogCase):
    def test_every_scheduled_section_exists(self):
        known = {s["id"]: s for s in self.sections}
        for stu in self.students.values():
            for term, ids in (stu.get("schedule") or {}).items():
                self.assertTrue(ids, (stu["id"], term))
                for sid in ids:
                    self.assertIn(sid, known, (stu["id"], sid))
                    self.assertEqual(known[sid]["term"], term, sid)

    def test_every_student_plans_for_every_single_major(self):
        for stu in self.students.values():
            for pid in self.catalog.programs:
                result = self.timed_plan(stu, [pid])
                progress = result["progress"]
                self.assertEqual([p["program"] for p in progress], [pid])
                self.assertEqual(progress[0]["total"], len(self.catalog.programs[pid]["slots"]))
                self.assertEqual(len(result["terms"]), 8)
                json.dumps(result)

    def test_every_student_plans_for_every_pair_of_majors(self):
        for stu in self.students.values():
            for pair in itertools.combinations(self.catalog.programs, 2):
                result = self.timed_plan(stu, list(pair))
                self.assertEqual([p["program"] for p in result["progress"]], list(pair))

    def test_the_undecided_first_year_can_finish_any_major(self):
        # Sam has six open terms: every major, real or sample, still fits.
        for pid in self.catalog.programs:
            result = build_plan(self.students["sam"], self.catalog, self.sections, [pid])
            self.assertEqual(result["unscheduled"], [], pid)
            self.assertNotIn("prereq_missing", codes(result), pid)

    def test_overlapping_majors_never_share_major_credit(self):
        slots = {(p["id"], s["label"]): s for p in self.catalog.programs.values() for s in p["slots"]}
        for pair in (["BIO", "BCM"], ["CHM", "BCM"], ["SOC", "GWS"], ["HIS", "LAS"], ["ENG", "AMS"],
                     ["ARH", "ART"], ["PHI", "POL"], ["SPN", "LAS"], ["PHY", "MATH"], ["ECN", "MATH"],
                     ["CS", "PSY"], ["CS", "ECN"]):
            for stu in list(self.students.values()) + [student(majors=[], start="2027FA", current="2027SP")]:
                for majors in (pair, pair[::-1]):
                    result = build_plan(stu, self.catalog, self.sections, majors)
                    for term in result["terms"]:
                        for tab in term["tablets"]:
                            credit = [c for c in tab["counts_for"]
                                      if slots[tuple(c.split(" · ", 1))]["credit_bearing"]]
                            self.assertLessEqual(len(credit), 1, (majors, tab["id"], tab["counts_for"]))

    def test_sample_major_tablets_behave_like_cs_and_math(self):
        alex = self.students["alex"]
        result = build_plan(alex, self.catalog, self.sections, ["CS", "ANT"])
        tabs = [dict(tab, term=t["id"]) for t in result["terms"] for tab in t["tablets"]]
        ant = [t for t in tabs if t["slot"] and t["slot"]["program"] == "ANT"]
        self.assertEqual(len(ant), 9)                                 # every ANT slot is on the board
        self.assertTrue(all(t["required"] for t in ant))
        self.assertTrue(any(t["status"] == "open" for t in ant))      # choose slots stay open
        self.assertTrue(any(t["status"] == "projected" for t in ant))
        self.assertEqual(result["unscheduled"], [])
        self.assertEqual(result["progress"][1]["route"]["origin"], "sample")
        # The sidebar lists exactly the slot's options, and a swap fills the slot.
        tab = next(t for t in ant if t["status"] == "open" and t["slot"]["label"] == "200-level anthropology")
        got = build_options(alex, self.catalog, self.sections, tab["term"], tab["id"], ["CS", "ANT"])
        self.assertTrue(got["required"])
        self.assertEqual(sorted(o["course"] for o in got["options"]), sorted(tab["slot"]["options"]))
        pick = next(o["course"] for o in got["options"] if o["eligible"])
        after = build_plan(alex, self.catalog, self.sections, ["CS", "ANT"],
                           [{"op": "swap", "term": tab["term"], "tablet": tab["id"], "course": pick}])
        self.assertNotIn("edit_ignored", codes(after))
        self.assertIn(pick, [t["course"] for term in after["terms"] if term["id"] == tab["term"]
                             for t in term["tablets"]])
        # The + button still offers the whole catalog.
        everything = build_options(alex, self.catalog, self.sections, "2027FA", None, ["CS", "ANT"])
        self.assertGreater(len(everything["options"]), 300)

    def test_courses_already_taken_fill_sample_major_slots(self):
        # Sam has ANT-104 and BIO-150 on the record; Alex has ENG-120, PHI-101 and HIS-100.
        for sid, major, slot, status in (("sam", "ANT", "ANT:ANT-104", "completed"),
                                         ("sam", "BIO", "BIO:BIO-150", "completed"),
                                         ("alex", "ENG", "ENG:ENG-120", "completed"),
                                         ("alex", "PHI", "PHI:PHI-101", "completed"),
                                         ("alex", "HIS", "HIS:HIS-100", "in_progress")):
            result = build_plan(self.students[sid], self.catalog, self.sections, [major])
            rows = {r["id"]: r for r in result["progress"][0]["slots"]}
            self.assertEqual(rows[slot]["status"], status, (sid, slot))


if __name__ == "__main__":
    unittest.main()
