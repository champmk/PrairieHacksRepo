"""The loader and planner against data/grinnell_catalog.json (skipped when absent)."""
import json
import unittest

from coursegraph.api import load_sections
from coursegraph.catalog import DATA_DIR, REAL_FILE, load_catalog
from coursegraph.plan import build_options, build_plan

from helpers import codes, enr, student, tablets, term_of

HAVE_REAL = (DATA_DIR / REAL_FILE).exists()


@unittest.skipUnless(HAVE_REAL, "grinnell_catalog.json is not present")
class RealCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(DATA_DIR / REAL_FILE)
        cls.sections = load_sections(cls.catalog)
        with open(DATA_DIR / "students.json", encoding="utf-8") as f:
            cls.students = {s["id"]: s for s in json.load(f)["students"]}

    def plan(self, stu, majors=None, edits=()):
        return build_plan(stu, self.catalog, self.sections, majors, list(edits))

    def test_loader_reads_the_real_shape(self):
        c = self.catalog
        self.assertEqual((c.origin, c.catalog_year), ("catalog", "2026-27"))
        self.assertEqual(list(c.programs), ["CS", "MATH"])
        self.assertEqual(len(c.programs["CS"]["slots"]), 10)
        self.assertEqual(len(c.programs["MATH"]["slots"]), 8)        # 8 x 4 = the 32-credit minimum
        self.assertEqual([r["origin"] for r in c.programs["CS"]["routes"]], ["catalog", "catalog"])
        self.assertEqual([r["origin"] for r in c.programs["MATH"]["routes"]], ["derived"])
        self.assertEqual((c.policies["graduation_credits"], c.policies["department_cap"],
                          c.policies["division_cap"], c.policies["load_max"]), (124, 48, 92, 18))
        self.assertIn("FYE-100", c.policies["load_exempt"])

    def test_unknown_stays_unknown(self):
        c = self.catalog.courses
        self.assertIsNone(c["MAT-220"]["offered"])                    # "Fall or Spring": term not stated
        self.assertEqual((c["MAT-306"]["offered"], c["MAT-306"]["offered_years"]), (["Spring"], "even"))
        self.assertEqual((c["STA-340"]["offered"], c["STA-340"]["offered_years"]), (["Fall"], "odd"))
        self.assertEqual((c["CSC-313"]["credits"], c["CSC-313"]["credits_assumed"], c["CSC-313"]["prereq_known"]),
                         (4, True, False))
        self.assertFalse(c["MAT-444"]["prereq_known"])                # "varies by topic"
        self.assertEqual(c["MAT-131"]["prereq"], {"consent": True})   # placement: reported, never assumed
        self.assertIn({"coreq": "MAT-220"}, c["MAT-313"]["prereq"]["all"])
        self.assertEqual(self.catalog.identity("MAT-208"), self.catalog.identity("CSC-208"))
        self.assertEqual(c["PHI-101"]["origin"], "sample")
        self.assertEqual(c["CSC-151"]["origin"], "catalog")

    def test_corrected_prerequisites(self):
        c = self.catalog.courses
        self.assertEqual(c["CSC-213"]["prereq"], {"course": "CSC-161"})
        self.assertEqual(c["CSC-211"]["prereq"], {"course": "CSC-161"})
        self.assertEqual(c["MAT-316"]["prereq"], {"any": [{"course": "MAT-218"}, {"course": "MAT-222"}]})
        self.assertEqual(c["CSC-301"]["prereq"]["all"][0], {"course": "CSC-207"})

    def test_no_credit_is_shared_between_the_two_majors(self):
        # Academic Policies: a double major may not share credits. CSC-208 (= MAT-208) is an
        # elective in both majors, so it may be credit in one only; the CS "also required"
        # groups sit outside the 32 CS credits and may overlap.
        slots = {s["label"]: s for p in self.catalog.programs.values() for s in p["slots"]}
        stu = student([enr("CSC-151", "2025FA"), enr("MAT-215", "2025FA"), enr("CSC-208", "2026SP"),
                       enr("MAT-218", "2026SP")])
        for majors in (["CS", "MATH"], ["MATH", "CS"]):
            result = self.plan(stu, majors)
            for tab in tablets(result).values():
                credit = [c for c in tab["counts_for"] if slots[c.split(" · ", 1)[1]]["credit_bearing"]]
                self.assertLessEqual(len(credit), 1, (majors, tab["id"], tab["counts_for"]))
        # A cognate slot may still overlap: MAT-218 is the Mathematics bridge and the CS discrete course.
        both = tablets(self.plan(stu, ["CS", "MATH"]))["enr:MAT-218:2026SP"]["counts_for"]
        self.assertEqual(sorted(c.split(" · ")[0] for c in both), ["CS", "MATH"])

    def test_both_systems_courses_fill_systems_and_the_elective(self):
        stu = student([enr("CSC-151", "2025FA"), enr("CSC-161", "2026SP"),
                       enr("CSC-213", "2026FA", "in_progress")],
                      schedule={"2027SP": ["2027SP-CSC-211-01"]})
        result = self.plan(stu)
        slots = {s["id"]: s for s in result["progress"][0]["slots"]}
        self.assertEqual({slots["CS:csc-systems"]["course"], slots["CS:csc-elective"]["course"]},
                         {"CSC-211", "CSC-213"})

    def test_alex_redistribution_is_visible(self):
        result = self.plan(self.students["alex"])
        self.assertEqual(result["progress"][0]["route"]["id"], "csc-plan-1")
        route = {s["id"]: s["route_term"] for s in self.catalog.programs["CS"]["slots"]}
        index = {t["id"]: t["index"] for t in result["terms"]}
        # CSC-207 was taken a term early, so CSC-341 and CSC-301 each land a term before the route.
        self.assertEqual(index[term_of(result, "slot:CS:CSC-341")], route["CS:CSC-341"] - 1)
        self.assertEqual(index[term_of(result, "slot:CS:CSC-301")], route["CS:CSC-301"] - 1)
        tabs = tablets(result)
        self.assertEqual((tabs["enr:ECN-111:2026SP"]["status"], tabs["enr:ECN-111:2026SP"]["mark"]),
                         ("not_counted", "W"))
        self.assertEqual(result["totals"]["in_progress"], 13)
        self.assertEqual(sum(1 for t in tabs.values() if t["status"] == "planned"), 4)
        self.assertEqual(result["unscheduled"], [])
        self.assertNotIn("tutorial_missing", codes(result))
        self.assertNotIn("fye_missing", codes(result))

    def test_jordan_ap_repeat_and_study_away(self):
        result = self.plan(self.students["jordan"])
        tabs = tablets(result)
        self.assertEqual(tabs["enr:MAT-215:2025SP"]["mark"], "D")
        self.assertTrue(tabs["enr:MAT-215:2025FA"]["required"])
        self.assertIn("major_grade", codes(result, tablet="enr:MAT-131:prior"))
        away = next(t for t in result["terms"] if t["id"] == "2026SP")
        self.assertTrue(away["off_campus"])
        self.assertEqual(away["credits"], 16)
        self.assertEqual(result["unscheduled"], [])
        self.assertEqual(result["edges"], [])

    def test_prerequisite_pull_in_names_the_elective(self):
        # MAT-215 needs MAT-133, which is not a named Mathematics requirement: an elective slot takes it.
        result = self.plan(self.students["sam"], ["MATH"])
        pulled = [t for t in tablets(result).values() if t["course"] == "MAT-133"]
        self.assertEqual(len(pulled), 1)
        self.assertTrue(pulled[0]["id"].startswith("slot:MATH:mat-electives"))
        index = {t["id"]: t["index"] for t in result["terms"]}
        self.assertLess(index[pulled[0]["term"]], index[term_of(result, "slot:MATH:MAT-215")])
        self.assertNotIn("prereq_missing", codes(result))

    def test_unstated_offering_is_a_soft_hint(self):
        stu = student([enr("MAT-131", "2025FA"), enr("MAT-133", "2026SP"), enr("MAT-215", "2026FA", "in_progress")],
                      majors=[])
        result = self.plan(stu, edits=[{"op": "add", "term": "2027SP", "course": "MAT-220"}])
        hints = [w for w in result["warnings"] if w["tablet"] == "add:MAT-220:2027SP"]
        self.assertEqual([(w["code"], w["severity"]) for w in hints], [("not_offered", "warning")])
        got = build_options(stu, self.catalog, self.sections, "2027SP")
        row = next(o for o in got["options"] if o["course"] == "MAT-220")
        self.assertEqual((row["eligible"], row["reason"]), (True, "Offering terms unknown"))

    def test_sample_sections_agree_with_catalog_offerings(self):
        terms = {"2026FA": {"season": "Fall", "year": 2026}, "2027SP": {"season": "Spring", "year": 2027}}
        for s in self.sections:
            self.assertIsNot(self.catalog.offered(s["course"], terms[s["term"]]), False, s["id"])


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAVE_REAL, "grinnell_catalog.json is not present")
class OpenElectiveTests(unittest.TestCase):
    """Open elective tablets fill the plan toward 124 and take any course."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(DATA_DIR / REAL_FILE)
        cls.sections = load_sections(cls.catalog)
        with open(DATA_DIR / "students.json", encoding="utf-8") as f:
            cls.alex = {s["id"]: s for s in json.load(f)["students"]}["alex"]

    def plan(self, edits=()):
        return build_plan(self.alex, self.catalog, self.sections, ["CS"], list(edits))

    def opens(self, result):
        return [(t["id"], t["status"]) for term in result["terms"] for t in term["tablets"] if t["id"].startswith("open:")]

    def test_fill_reaches_124_without_overloading(self):
        r = self.plan()
        t = r["totals"]
        self.assertGreater(t["open"], 0)
        reach = t["counted"] + t["in_progress"] + t["planned"] + t["open"]
        # Either the plan reaches 124, or every open term is full and the shortfall is reported.
        if reach < 124:
            self.assertIn("grad_credits", codes(r))
        else:
            self.assertNotIn("grad_credits", codes(r))
        for term in r["terms"]:
            if term["state"] in ("next", "future"):
                self.assertLessEqual(term["credits"], 16 + 4)  # a planned overload is the student's own choice
        self.assertTrue(all(s == "open" for _, s in self.opens(r)))

    def test_open_tablet_ids_are_unique_and_stable(self):
        a, b = self.plan(), self.plan()
        ids = [i for i, _ in self.opens(a)]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, [i for i, _ in self.opens(b)])

    def test_removing_an_elective_moves_it(self):
        # Sam has spare room across terms, so a removed elective lands elsewhere.
        with open(DATA_DIR / "students.json", encoding="utf-8") as f:
            sam = {s["id"]: s for s in json.load(f)["students"]}["sam"]
        run = lambda edits=(): build_plan(sam, self.catalog, self.sections, [], list(edits))
        r = run()
        first = self.opens(r)[0][0]
        term = first.split(":")[1]
        after = run([{"op": "remove", "term": term, "tablet": first}])
        here = lambda res: sum(1 for t in next(x for x in res["terms"] if x["id"] == term)["tablets"] if t["id"].startswith("open:"))
        self.assertEqual(here(after), here(r) - 1)
        # Still needed: it lands in a term with room, or the shortfall is reported.
        if after["totals"]["open"] < r["totals"]["open"]:
            self.assertIn("grad_credits", codes(after))
        else:
            self.assertEqual(after["totals"]["open"], r["totals"]["open"])

    def test_swapping_an_elective_adds_the_course(self):
        r = self.plan()
        first = self.opens(r)[0][0]
        term = first.split(":")[1]
        after = self.plan([{"op": "swap", "term": term, "tablet": first, "course": "PHI-101"}])
        courses = [t["course"] for t in next(x for x in after["terms"] if x["id"] == term)["tablets"]]
        self.assertIn("PHI-101", courses)
        self.assertNotIn("edit_ignored", codes(after))

    def test_options_for_an_elective_list_any_course(self):
        r = self.plan()
        first = self.opens(r)[0][0]
        opts = build_options(self.alex, self.catalog, self.sections, first.split(":")[1], first, ["CS"])
        self.assertFalse(opts["required"])
        self.assertGreater(len(opts["options"]), 40)
