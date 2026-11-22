"""The HTTP layer against the seeded database and the loaded catalog.

Route functions are called directly (no HTTP client needed), with a throwaway
database file so the tests never touch data/students.db.
"""
import json
import os
import tempfile
import unittest

from fastapi import HTTPException

from coursegraph import api, db
from coursegraph.validate import detect_clashes

STUDENTS = ("alex", "sam", "jordan")
MAJOR_SETS = ([], ["CS"], ["MATH"], ["CS", "MATH"])
STATUSES_BY_STATE = {
    "past": {"completed", "not_counted"},
    "current": {"in_progress", "not_counted"},
    "next": {"planned", "projected", "open"},
    "future": {"projected", "open"},
}
WARNING_CODES = {
    "prereq_missing", "coreq_missing", "not_offered", "load_high", "load_low", "dept_cap",
    "division_cap", "duplicate", "repeat_not_allowed", "chain_too_long", "unscheduled",
    "grad_credits", "tutorial_missing", "fye_missing", "major_grade", "consent_required", "edit_ignored"}
TABLET_KEYS = {"id", "course", "title", "credits", "status", "mark", "required", "locked", "slot",
               "counts_for", "warnings"}


class ApiCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._dir = tempfile.TemporaryDirectory()
        cls._old = os.environ.get("COURSEGRAPH_DB")
        os.environ["COURSEGRAPH_DB"] = os.path.join(cls._dir.name, "students.db")
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        if cls._old is None:
            os.environ.pop("COURSEGRAPH_DB", None)
        else:
            os.environ["COURSEGRAPH_DB"] = cls._old
        cls._dir.cleanup()

    def plan(self, student_id, majors=None, edits=(), cap=None):
        return api.post_plan(api.PlanRequest(student_id=student_id, majors=majors, credit_cap=cap,
                                             edits=[api.Edit(**e) for e in edits]))

    def assert422(self, call):
        with self.assertRaises(HTTPException) as caught:
            call()
        self.assertEqual(caught.exception.status_code, 422)
        return caught.exception.detail


class ReadRoutes(ApiCase):
    def test_database_is_seeded_from_students_json(self):
        self.assertTrue(os.path.exists(os.environ["COURSEGRAPH_DB"]))
        listed = api.get_students()
        self.assertEqual([s["id"] for s in listed], list(STUDENTS))
        self.assertEqual(set(listed[0]), {"id", "name", "summary"})

    def test_student_record(self):
        alex = api.get_student("alex")
        self.assertEqual((alex["start_term"], alex["current_term"], alex["majors"]), ("2025FA", "2026FA", ["CS"]))
        self.assertEqual([t["state"] for t in alex["terms"]],
                         ["past", "past", "current", "next", "future", "future", "future", "future"])
        self.assertEqual(set(alex["terms"][0]) >= {"id", "label", "state"}, True)
        by_status = {}
        for e in alex["enrollments"]:
            by_status.setdefault(e["status"], []).append(e)
        self.assertEqual(len(by_status["withdrawn"]), 1)
        self.assertEqual(sum(1 for e in by_status["in_progress"]), 4)
        # planned rows exist only for the next term and come from the saved schedule
        self.assertEqual({e["term"] for e in by_status["planned"]}, {"2027SP"})
        self.assertEqual(len(by_status["planned"]), len(alex["schedule"]["2027SP"]))
        with self.assertRaises(HTTPException) as caught:
            api.get_student("nobody")
        self.assertEqual(caught.exception.status_code, 404)

    def test_seeded_students_match_the_brief(self):
        alex, sam, jordan = (api.get_student(s) for s in STUDENTS)
        in_progress = [e for e in api.get_student("alex")["enrollments"] if e["status"] == "in_progress"]
        credits = {c["id"]: c["credits"] for c in api.get_catalog()["courses"]}
        self.assertEqual(sum(credits[e["course"]] for e in in_progress), 13)
        self.assertIn("CSC-208", [e["course"] for e in in_progress])
        self.assertEqual(sam["majors"], [])
        self.assertNotIn("planned", {e["status"] for e in sam["enrollments"]})
        self.assertEqual(jordan["majors"], ["CS", "MATH"])
        self.assertEqual(jordan["off_campus"], ["2026SP"])
        self.assertTrue(any(e["term"] is None and e["mode"] == "transfer" for e in jordan["enrollments"]))
        grades = [e["grade"] for e in jordan["enrollments"] if e["course"] == "MAT-215"]
        self.assertEqual(grades, ["D", "B"])

    def test_catalog_shape(self):
        catalog = api.get_catalog()
        self.assertEqual(set(catalog) >= {"catalog_year", "courses", "programs", "divisions"}, True)
        course = next(c for c in catalog["courses"] if c["id"] == "CSC-161")
        self.assertEqual(set(course) >= {"id", "title", "credits", "department", "division", "level",
                                         "offered", "offered_note", "prereq_text", "prereq", "source_url"}, True)
        self.assertEqual((course["department"], course["level"], course["prereq"]),
                         ("CSC", 100, {"course": "CSC-151"}))
        self.assertEqual([p["id"] for p in catalog["programs"]][:2], ["CS", "MATH"])   # then the sample majors
        for program in catalog["programs"]:
            for slot in program["slots"]:
                self.assertEqual(set(slot) >= {"id", "label", "kind", "options", "route_term"}, True)
                self.assertIn(slot["kind"], ("course", "choose"))
        self.assertEqual(catalog["divisions"]["CSC"], "Science")
        json.dumps(catalog)

    def test_sections_by_term(self):
        spring = api.get_sections("2027SP")
        self.assertTrue(spring)
        self.assertEqual({s["term"] for s in spring}, {"2027SP"})
        first = next(s for s in spring if s["id"] == "2027SP-CSC-151-01")
        self.assertEqual(set(first) >= {"id", "course", "term", "number", "instructor", "available",
                                        "capacity", "meetings"}, True)
        self.assertEqual(first["meetings"][0],
                         {"days": ["M", "W", "F"], "start": "08:00", "end": "09:20", "room": "Noyce 3813"})
        self.assertEqual(api.get_sections("2031FA"), [])


class ScheduleRoute(ApiCase):
    def put(self, student_id, term, ids):
        return api.put_schedule(student_id, api.ScheduleRequest(term=term, section_ids=ids))

    def test_current_term_is_read_only(self):
        detail = self.assert422(lambda: self.put("sam", "2026FA", ["2026FA-CSC-151-01"]))
        self.assertIn("read-only", detail)

    def test_only_the_next_term_can_be_scheduled(self):
        self.assert422(lambda: self.put("sam", "2027FA", []))
        self.assert422(lambda: self.put("sam", "2026SP", []))
        self.assert422(lambda: self.put("sam", "garbage", []))

    def test_unknown_section_is_rejected(self):
        self.assert422(lambda: self.put("sam", "2027SP", ["2027SP-CSC-999-01"]))
        self.assert422(lambda: self.put("sam", "2027SP", ["2026FA-CSC-207-01"]))     # wrong term
        self.assertEqual(api.get_student("sam")["schedule"].get("2027SP"), None)     # nothing was saved

    def test_one_section_per_course(self):
        self.assert422(lambda: self.put("sam", "2027SP", ["2027SP-CSC-161-01", "2027SP-CSC-161-02"]))

    def test_save_returns_clashes_and_the_plan_shows_planned(self):
        ids = ["2027SP-CSC-207-01", "2027SP-MAT-133-01", "2027SP-PHI-101-01"]
        try:
            saved = self.put("sam", "2027SP", ids)
            self.assertEqual((saved["term"], saved["section_ids"]), ("2027SP", ids))
            # CSC-207-01 and MAT-133-01 both meet MWF 09:00-09:50.
            self.assertEqual(saved["clashes"], [{"a": "2027SP-CSC-207-01", "b": "2027SP-MAT-133-01"}])
            self.assertEqual(api.get_student("sam")["schedule"]["2027SP"], ids)
            result = self.plan("sam", ["CS"])
            spring = next(t for t in result["terms"] if t["id"] == "2027SP")
            planned = {t["course"]: t for t in spring["tablets"] if t["status"] == "planned"}
            self.assertEqual(set(planned), {"CSC-207", "MAT-133", "PHI-101"})
            self.assertTrue(planned["CSC-207"]["required"])
            self.assertEqual(planned["CSC-207"]["id"], "enr:CSC-207:2027SP")
        finally:
            self.put("sam", "2027SP", [])
        self.assertEqual(api.get_student("sam")["schedule"].get("2027SP"), None)

    def test_clash_needs_a_shared_day_and_overlapping_time(self):
        def sec(sid, days, start, end):
            return {"id": sid, "meetings": [{"days": days, "start": start, "end": end}]}
        a = sec("a", ["M", "W", "F"], "09:00", "09:50")
        self.assertEqual(detect_clashes([a, sec("b", ["W"], "09:30", "10:50")]), [{"a": "a", "b": "b"}])
        self.assertEqual(detect_clashes([a, sec("b", ["T", "R"], "09:00", "09:50")]), [])    # no shared day
        self.assertEqual(detect_clashes([a, sec("b", ["M"], "09:50", "10:40")]), [])         # back to back
        self.assertEqual(detect_clashes([a, sec("b", ["F"], "08:00", "09:01")]), [{"a": "a", "b": "b"}])


class PlanRoute(ApiCase):
    def test_round_trip_for_every_student_and_major_set(self):
        for student_id in STUDENTS:
            for majors in MAJOR_SETS:
                with self.subTest(student=student_id, majors=majors):
                    result = self.plan(student_id, majors)
                    json.dumps(result)
                    self.assertEqual(set(result) >= {"terms", "edges", "warnings", "progress", "totals",
                                                     "unscheduled"}, True)
                    self.assertEqual(len(result["terms"]), 8)
                    ids = [t["id"] for term in result["terms"] for t in term["tablets"]]
                    ids += [t["id"] for t in result["prior"]]
                    self.assertEqual(len(ids), len(set(ids)), "tablet ids must be unique")
                    warning_ids = {w["id"] for w in result["warnings"]}
                    self.assertEqual(len(warning_ids), len(result["warnings"]))
                    for term in result["terms"]:
                        self.assertEqual(set(term) >= {"id", "label", "season", "year", "index", "state",
                                                       "complete", "credits", "tablets"}, True)
                        for tab in term["tablets"]:
                            self.assertEqual(set(tab), TABLET_KEYS)
                            self.assertIn(tab["status"], STATUSES_BY_STATE[term["state"]], tab["id"])
                            self.assertEqual(tab["course"] is None, tab["status"] == "open")
                            self.assertEqual(tab["locked"], term["state"] in ("past", "current"))
                            self.assertEqual(tab["mark"] is not None, tab["status"] == "not_counted")
                            self.assertTrue(set(tab["warnings"]) <= warning_ids)
                            if tab["required"]:
                                self.assertTrue(tab["counts_for"])
                                self.assertEqual(set(tab["slot"]), {"id", "program", "label", "options"})
                            self.assertIn(tab["id"].split(":")[0], ("enr", "slot", "add", "open"))
                            if tab["status"] == "open":
                                # an open requirement slot, or an open elective that takes any course
                                self.assertTrue(tab["id"].startswith(("slot:", "open:")))
                                self.assertEqual(tab["required"], tab["id"].startswith("slot:"))
                        if term["complete"]:
                            self.assertEqual(term["state"], "past")
                    for w in result["warnings"]:
                        self.assertIn(w["code"], WARNING_CODES)
                        self.assertIn(w["severity"], ("warning", "error"))
                        self.assertTrue(w["tablet"] is None or w["tablet"] in ids)
                    for e in result["edges"]:
                        self.assertIn(e["from_tablet"], ids)
                    self.assertEqual([p["program"] for p in result["progress"]], majors)
                    for p in result["progress"]:
                        self.assertEqual(p["total"], len(p["slots"]))
                        unplaced = sum(1 for u in result["unscheduled"] if u["slot"].startswith(p["program"] + ":"))
                        self.assertEqual(p["done"] + p["in_progress"] + p["planned"] + unplaced, p["total"])
                    totals = result["totals"]
                    self.assertEqual(totals["required"], 124)
                    self.assertEqual(sum(totals["by_department"].values()) <=
                                     totals["counted"] + totals["in_progress"] + totals["planned"], True)

    def test_majors_default_to_the_student_record(self):
        self.assertEqual([p["program"] for p in self.plan("jordan")["progress"]], ["CS", "MATH"])
        self.assertEqual(self.plan("sam")["progress"], [])

    def test_unknown_student_and_major(self):
        with self.assertRaises(HTTPException) as caught:
            self.plan("nobody")
        self.assertEqual(caught.exception.status_code, 404)
        self.assert422(lambda: self.plan("alex", ["BASKETRY"]))

    def test_edits_round_trip_and_determinism(self):
        edits = [{"op": "add", "term": "2027FA", "course": "PHI-101"},
                 {"op": "remove", "term": "2027FA", "tablet": "slot:CS:CSC-341"},
                 {"op": "swap", "term": "2028FA", "tablet": "slot:CS:csc-elective", "course": "CSC-312"},
                 {"op": "add", "term": "2025FA", "course": "PHI-101"}]
        first = self.plan("alex", ["CS", "MATH"], edits)
        second = self.plan("alex", ["CS", "MATH"], edits)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        where = {t["id"]: term["id"] for term in first["terms"] for t in term["tablets"]}
        self.assertNotEqual(where["slot:CS:CSC-341"], "2027FA")
        self.assertEqual(where["slot:CS:csc-elective"], "2028FA")
        self.assertEqual([w["code"] for w in first["warnings"]].count("edit_ignored"), 1)

    def test_options_route(self):
        slot = api.post_options(api.OptionsRequest(student_id="alex", term="2029SP", tablet="slot:CS:csc-elective"))
        cs = next(p for p in api.get_catalog()["programs"] if p["id"] == "CS")
        wanted = next(s for s in cs["slots"] if s["id"] == "CS:csc-elective")["options"]
        self.assertTrue(slot["required"])
        self.assertEqual(sorted(o["course"] for o in slot["options"]), sorted(wanted))
        for o in slot["options"]:
            self.assertEqual(set(o), {"course", "title", "credits", "eligible", "reason"})
        plus = api.post_options(api.OptionsRequest(student_id="alex", term="2027FA"))
        self.assertFalse(plus["required"])
        listed = {o["course"] for o in plus["options"]}
        in_plan = {t["course"] for term in self.plan("alex")["terms"] for t in term["tablets"]
                   if t["course"] and t["status"] != "not_counted"}
        self.assertEqual(listed & in_plan, set())
        self.assertIn("ECN-111", listed)                          # withdrawn, so it can be taken again
        self.assertGreater(len(listed), len(wanted))
        self.assert422(lambda: api.post_options(api.OptionsRequest(student_id="alex", term="1999FA")))


if __name__ == "__main__":
    unittest.main()
