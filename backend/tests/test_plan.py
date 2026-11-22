"""Distribute, edits, Validate and the options list, on the fixture catalog."""
import json
import unittest

from coursegraph.plan import PlanError, build_options
from coursegraph.terms import build_terms

from helpers import FIXTURE, ON_ROUTE, SECTIONS, codes, enr, plan, student, tablets, term_of

# Took CSC-207 and CSC-211 one term ahead of the "CS via CSC-208" route.
EARLY = [enr("CSC-151", "2025FA"), enr("MAT-131", "2025FA"), enr("CSC-161", "2026SP"),
         enr("CSC-208", "2026SP"), enr("CSC-207", "2026SP"), enr("CSC-211", "2026FA", "in_progress")]


def options(stu, term, tablet=None, edits=(), majors=None):
    return build_options(stu, FIXTURE, SECTIONS, term, tablet, majors, list(edits))


class TermTests(unittest.TestCase):
    def test_states_follow_the_current_term(self):
        terms = build_terms("2025FA", "2026FA", ["2028SP"])
        self.assertEqual([t["id"] for t in terms],
                         ["2025FA", "2026SP", "2026FA", "2027SP", "2027FA", "2028SP", "2028FA", "2029SP"])
        self.assertEqual([t["state"] for t in terms],
                         ["past", "past", "current", "next", "future", "future", "future", "future"])
        self.assertTrue(terms[5]["off_campus"])


class DistributeTests(unittest.TestCase):
    def test_slots_follow_the_route(self):
        result = plan(student(ON_ROUTE))
        self.assertEqual(term_of(result, "slot:CS:CSC-211"), "2027SP")
        self.assertEqual(term_of(result, "slot:CS:CSC-301"), "2027FA")
        self.assertEqual(term_of(result, "slot:CS:CSC-213"), "2028SP")
        self.assertEqual(term_of(result, "slot:CS:csc-elective:2"), "2029SP")
        self.assertEqual(result["unscheduled"], [])

    def test_specific_slots_are_projected_and_choose_slots_are_open(self):
        tabs = tablets(plan(student(ON_ROUTE)))
        self.assertEqual((tabs["slot:CS:CSC-301"]["status"], tabs["slot:CS:CSC-301"]["course"]),
                         ("projected", "CSC-301"))
        self.assertEqual((tabs["slot:CS:csc-elective:1"]["status"], tabs["slot:CS:csc-elective:1"]["course"]),
                         ("open", None))
        for tid in ("slot:CS:CSC-301", "slot:CS:csc-elective:1"):
            self.assertTrue(tabs[tid]["required"])
            self.assertFalse(tabs[tid]["locked"])

    def test_r_moves_to_a_course_planned_earlier_than_its_route_term(self):
        base = plan(student(ON_ROUTE))
        self.assertEqual(term_of(base, "slot:CS:CSC-301"), "2027FA")
        moved = plan(student(ON_ROUTE, schedule={"2027SP": ["2027SP-CSC-301-01"]}))
        tabs = tablets(moved)
        self.assertNotIn("slot:CS:CSC-301", tabs)                 # the later R is gone
        planned = tabs["enr:CSC-301:2027SP"]
        self.assertEqual((planned["status"], planned["required"], planned["locked"]), ("planned", True, False))
        self.assertEqual(planned["counts_for"], ["CS · CSC-301"])
        slot = next(s for s in moved["progress"][0]["slots"] if s["id"] == "CS:CSC-301")
        self.assertEqual((slot["status"], slot["term"]), ("planned", "2027SP"))

    def test_dependents_move_earlier_when_a_prerequisite_was_taken_early(self):
        on_time, early = plan(student(ON_ROUTE)), plan(student(EARLY))
        for slot, was, now in (("slot:CS:CSC-301", "2027FA", "2027SP"),
                               ("slot:CS:CSC-213", "2028SP", "2027FA"),
                               ("slot:CS:CSC-341", "2028SP", "2027FA")):
            self.assertEqual(term_of(on_time, slot), was)
            self.assertEqual(term_of(early, slot), now)

    def test_prerequisites_sit_in_strictly_earlier_terms(self):
        result = plan(student([], majors=["CS", "MATH"], start="2026SP", current="2026SP"))
        order = {t["id"]: t["index"] for t in result["terms"]}
        where = {tab["course"]: order[tab["term"]] for tab in tablets(result).values() if tab["course"]}
        for later, earlier in (("CSC-161", "CSC-151"), ("CSC-207", "CSC-161"), ("CSC-301", "CSC-207"),
                               ("MAT-133", "MAT-131"), ("MAT-215", "MAT-133"), ("MAT-218", "MAT-215")):
            if later in where:
                self.assertLess(where[earlier], where[later])
        self.assertNotIn("prereq_missing", codes(result))

    def test_load_stays_within_the_credit_cap(self):
        for cap in (12, 16, 18):
            result = plan(student([], majors=["CS", "MATH"], start="2026SP", current="2026SP"), cap=cap)
            for t in result["terms"]:
                self.assertLessEqual(t["credits"], cap)

    def test_offering_season_and_year_parity_are_respected(self):
        # MAT-306 runs in even-year springs only (2028SP here, never 2027SP or 2029SP).
        stu = student([enr("MAT-131", "2025FA"), enr("MAT-133", "2025FA"), enr("MAT-215", "2026SP"),
                       enr("MAT-220", "2026SP"), enr("MAT-218", "2026FA", "in_progress")], majors=["MATH"])
        result = plan(stu, [{"op": "swap", "term": "2028SP", "tablet": "slot:MATH:mat-elective:1", "course": "MAT-306"},
                            {"op": "remove", "term": "2028SP", "tablet": "slot:MATH:mat-elective:1"}])
        # Barred from its only season before graduation: nowhere left to go.
        self.assertIn("MATH:mat-elective:1", [u["slot"] for u in result["unscheduled"]])
        self.assertEqual(term_of(result, "slot:MATH:MAT-316"), "2027FA")      # fall only
        self.assertEqual(term_of(result, "slot:MATH:MAT-321"), "2028SP")      # spring only

    def test_slots_that_never_fit_are_unscheduled_with_errors(self):
        result = plan(student([], start="2023FA"))               # one term left
        self.assertIn("CS:CSC-301", [u["slot"] for u in result["unscheduled"]])
        self.assertTrue(all(u["reason"] for u in result["unscheduled"]))
        errors = [w for w in result["warnings"] if w["severity"] == "error"]
        self.assertIn("unscheduled", [w["code"] for w in errors])
        self.assertIn("chain_too_long", [w["code"] for w in errors])
        self.assertNotIn("slot:CS:CSC-301", tablets(result))

    def test_study_away_term_holds_no_slots(self):
        result = plan(student(ON_ROUTE, off_campus=["2027FA"]),
                      [{"op": "add", "term": "2027FA", "course": "PHI-101"}])
        away = next(t for t in result["terms"] if t["id"] == "2027FA")
        self.assertTrue(away["off_campus"])
        self.assertEqual(away["tablets"], [])
        self.assertIn("edit_ignored", codes(result))

    def test_a_swap_is_pinned_and_checked_not_moved(self):
        # The student puts CSC-395 (needs MAT-215) in the elective slot: it stays where they put
        # it and the missing prerequisite is reported.
        result = plan(student(EARLY), [{"op": "swap", "term": "2028SP", "tablet": "slot:CS:csc-elective:1",
                                        "course": "CSC-395"}])
        self.assertEqual(tablets(result)["slot:CS:csc-elective:1"]["course"], "CSC-395")
        self.assertIn("prereq_missing", codes(result, tablet="slot:CS:csc-elective:1"))


class EditTests(unittest.TestCase):
    def test_add_puts_a_course_in_a_term(self):
        result = plan(student(ON_ROUTE), [{"op": "add", "term": "2027FA", "course": "HIS-100"}])
        tab = tablets(result)["add:HIS-100:2027FA"]
        self.assertEqual((tab["term"], tab["status"], tab["required"], tab["locked"]),
                         ("2027FA", "projected", False, False))
        self.assertNotIn("edit_ignored", codes(result))

    def test_added_course_that_fills_a_slot_takes_the_r(self):
        result = plan(student(ON_ROUTE), [{"op": "add", "term": "2027SP", "course": "CSC-324"}])
        tabs = tablets(result)
        self.assertTrue(tabs["add:CSC-324:2027SP"]["required"])
        self.assertNotIn("slot:CS:CSC-324", tabs)

    def test_remove_bars_a_slot_from_that_term_and_it_moves(self):
        base = plan(student(ON_ROUTE))
        home = term_of(base, "slot:CS:CSC-301")
        moved = plan(student(ON_ROUTE), [{"op": "remove", "term": home, "tablet": "slot:CS:CSC-301"}])
        self.assertNotIn("edit_ignored", codes(moved))
        self.assertIsNotNone(term_of(moved, "slot:CS:CSC-301"))
        self.assertNotEqual(term_of(moved, "slot:CS:CSC-301"), home)
        twice = plan(student(ON_ROUTE), [{"op": "remove", "term": home, "tablet": "slot:CS:CSC-301"},
                                         {"op": "remove", "term": term_of(moved, "slot:CS:CSC-301"),
                                          "tablet": "slot:CS:CSC-301"}])
        self.assertNotIn(term_of(twice, "slot:CS:CSC-301"), (home, term_of(moved, "slot:CS:CSC-301")))

    def test_remove_deletes_an_added_tablet(self):
        edits = [{"op": "add", "term": "2027FA", "course": "HIS-100"},
                 {"op": "remove", "term": "2027FA", "tablet": "add:HIS-100:2027FA"}]
        result = plan(student(ON_ROUTE), edits)
        self.assertNotIn("add:HIS-100:2027FA", tablets(result))
        self.assertNotIn("edit_ignored", codes(result))

    def test_swap_on_a_requirement_is_restricted_to_the_slot_options(self):
        slot = "slot:CS:csc-elective:1"
        bad = plan(student(ON_ROUTE), [{"op": "swap", "term": "2028FA", "tablet": slot, "course": "PHI-101"}])
        self.assertEqual(codes(bad).count("edit_ignored"), 1)
        self.assertIsNone(tablets(bad)[slot]["course"])
        good = plan(student(ON_ROUTE), [{"op": "swap", "term": "2027FA", "tablet": slot, "course": "CSC-321"}])
        tab = tablets(good)[slot]
        self.assertEqual((tab["course"], tab["status"], tab["term"]), ("CSC-321", "projected", "2027FA"))
        self.assertNotIn("edit_ignored", codes(good))

    def test_swap_replaces_an_added_course(self):
        edits = [{"op": "add", "term": "2027FA", "course": "HIS-100"},
                 {"op": "swap", "term": "2027FA", "tablet": "add:HIS-100:2027FA", "course": "SOC-111"}]
        tabs = tablets(plan(student(ON_ROUTE), edits))
        self.assertIn("add:SOC-111:2027FA", tabs)
        self.assertNotIn("add:HIS-100:2027FA", tabs)

    def test_edits_outside_projected_terms_or_on_locked_tablets_are_ignored(self):
        edits = [{"op": "add", "term": "2025FA", "course": "HIS-100"},                       # past
                 {"op": "add", "term": "2026FA", "course": "HIS-100"},                       # current
                 {"op": "remove", "term": "2026FA", "tablet": "enr:CSC-207:2026FA"},         # locked
                 {"op": "swap", "term": "2026SP", "tablet": "enr:CSC-161:2026SP", "course": "HIS-100"},
                 {"op": "add", "term": "2027SP", "course": "NOPE-999"},                      # unknown course
                 {"op": "remove", "term": "2027SP", "tablet": "add:HIS-100:2027SP"},         # no such tablet
                 {"op": "remove", "term": "2031FA", "tablet": "slot:CS:CSC-301"},            # not a term
                 {"op": "teleport", "term": "2027SP"}]
        result = plan(student(ON_ROUTE), edits)
        self.assertEqual(codes(result).count("edit_ignored"), len(edits))
        def layout(r):
            return [(t["id"], [(x["id"], x["course"], x["status"]) for x in t["tablets"]]) for t in r["terms"]]
        self.assertEqual(layout(plan(student(ON_ROUTE))), layout(result))


class ValidateTests(unittest.TestCase):
    def test_missing_prerequisite_points_to_the_previous_term(self):
        stu = student([enr("CSC-151", "2025FA"), enr("CSC-161", "2026FA", "in_progress")], majors=[])
        result = plan(stu, [{"op": "add", "term": "2027SP", "course": "CSC-341"}])
        self.assertIn("prereq_missing", codes(result, tablet="add:CSC-341:2027SP"))
        (edge,) = result["edges"]
        self.assertEqual((edge["from_tablet"], edge["from_term"], edge["to_term"], edge["kind"]),
                         ("add:CSC-341:2027SP", "2027SP", "2026FA", "prereq"))   # 2026FA is the current term
        self.assertEqual(edge["missing"], ["CSC-207", "CSC-208", "MAT-218"])
        self.assertIn("CSC-207", edge["message"])
        warning = next(w for w in result["warnings"] if w["code"] == "prereq_missing")
        self.assertIn(warning["id"], tablets(result)["add:CSC-341:2027SP"]["warnings"])

    def test_in_progress_and_planned_courses_clear_prerequisites(self):
        stu = student([enr("CSC-151", "2025FA"), enr("CSC-161", "2026FA", "in_progress")], majors=[],
                      schedule={"2027SP": ["2027SP-CSC-207-01"]})
        result = plan(stu, [{"op": "add", "term": "2027FA", "course": "CSC-324"}])
        self.assertEqual(result["edges"], [])
        self.assertNotIn("prereq_missing", codes(result))

    def test_a_d_does_not_clear_a_prerequisite(self):
        stu = student([enr("CSC-151", "2025FA", grade="D")], majors=[])
        result = plan(stu, [{"op": "add", "term": "2027SP", "course": "CSC-161"}])
        self.assertIn("prereq_missing", codes(result, tablet="add:CSC-161:2027SP"))

    def test_corequisite_may_share_the_term(self):
        base = [enr("MAT-131", "2025FA"), enr("MAT-133", "2025FA"), enr("MAT-215", "2026SP")]
        alone = plan(student(base, majors=[]), [{"op": "add", "term": "2027FA", "course": "MAT-313"}])
        self.assertEqual(codes(alone, tablet="add:MAT-313:2027FA"), ["coreq_missing"])
        self.assertEqual(alone["edges"], [])
        together = plan(student(base, majors=[]), [{"op": "add", "term": "2027FA", "course": "MAT-313"},
                                                    {"op": "add", "term": "2027FA", "course": "MAT-220"}])
        self.assertEqual(codes(together, tablet="add:MAT-313:2027FA"), [])

    def test_not_offered(self):
        result = plan(student([], majors=[]), [{"op": "add", "term": "2027FA", "course": "CSC-322"},   # spring only
                                               {"op": "add", "term": "2027SP", "course": "MAT-306"},   # even springs
                                               {"op": "add", "term": "2028SP", "course": "MAT-306"},
                                               {"op": "add", "term": "2027SP", "course": "HIS-100"}])
        self.assertIn("not_offered", codes(result, tablet="add:CSC-322:2027FA"))
        self.assertIn("not_offered", codes(result, tablet="add:MAT-306:2027SP"))
        self.assertNotIn("not_offered", codes(result, tablet="add:MAT-306:2028SP"))
        self.assertEqual(codes(result, tablet="add:HIS-100:2027SP"), [])

    def test_unknown_offering_and_prerequisite_are_reported_not_assumed(self):
        result = plan(student([], majors=[]), [{"op": "add", "term": "2027SP", "course": "MAT-397"}])
        self.assertEqual(sorted(codes(result, tablet="add:MAT-397:2027SP")), ["consent_required", "not_offered"])

    def test_consent_is_a_warning(self):
        result = plan(student([], majors=[]), [{"op": "add", "term": "2027SP", "course": "CSC-499"}])
        self.assertEqual(codes(result, tablet="add:CSC-499:2027SP"), ["consent_required"])

    def test_load_high_ignores_music_and_fye(self):
        three = [{"op": "add", "term": "2027SP", "course": c} for c in ("HIS-100", "SOC-111", "ANT-104")]
        stu = student([enr("CSC-151", "2026FA", "in_progress")], majors=[],
                      schedule={"2027SP": ["2027SP-ECN-111-01"]})         # 4 planned + 12 added = 16
        self.assertNotIn("load_high", codes(plan(stu, three)))
        exempt = plan(stu, three + [{"op": "add", "term": "2027SP", "course": c}
                                    for c in ("MUS-101", "MUS-120", "FYE-100")])
        self.assertEqual(next(t for t in exempt["terms"] if t["id"] == "2027SP")["credits"], 22)
        self.assertNotIn("load_high", codes(exempt, term="2027SP"))   # the 6 extra credits are exempt
        over = plan(stu, three + [{"op": "add", "term": "2027SP", "course": "BIO-150"}])   # 20
        self.assertEqual(codes(over, term="2027SP"), ["load_high"])

    def test_load_low_on_the_current_term(self):
        result = plan(student([enr("CSC-151", "2026FA", "in_progress")], majors=[]))
        self.assertEqual(codes(result, term="2026FA"), ["load_low"])
        self.assertNotIn("load_low", codes(plan(student(ON_ROUTE))))

    def test_tutorial_and_fye(self):
        missing = plan(student([enr("CSC-151", "2025FA")], majors=[]))
        self.assertEqual(codes(missing, term="2025FA"), ["tutorial_missing"])
        self.assertEqual(codes(missing, term="2026SP"), ["fye_missing"])
        fine = plan(student(ON_ROUTE))
        self.assertNotIn("tutorial_missing", codes(fine))
        self.assertNotIn("fye_missing", codes(fine))

    def test_grad_credits_sits_on_the_last_term(self):
        result = plan(student(ON_ROUTE))
        (w,) = [w for w in result["warnings"] if w["code"] == "grad_credits"]
        self.assertEqual((w["term"], w["tablet"]), ("2029SP", None))
        t = result["totals"]
        self.assertLess(t["counted"] + t["in_progress"] + t["planned"], t["required"])
        self.assertEqual(t["required"], 124)

    def test_duplicate_course(self):
        result = plan(student(ON_ROUTE), [{"op": "add", "term": "2027FA", "course": "CSC-151"}])
        self.assertEqual(codes(result, tablet="add:CSC-151:2027FA"), ["duplicate"])

    def test_term_complete_flag(self):
        result = plan(student(ON_ROUTE + [enr("ECN-111", "2026SP", "withdrawn", "W")]))
        self.assertEqual([t["complete"] for t in result["terms"]][:4], [True, True, False, False])


class OptionsTests(unittest.TestCase):
    def test_requirement_tablet_lists_only_its_slot_options(self):
        got = options(student(ON_ROUTE), "2028FA", "slot:CS:csc-elective:1")
        self.assertTrue(got["required"])
        self.assertEqual(got["label"], "CS elective")
        self.assertEqual(sorted(o["course"] for o in got["options"]),
                         ["CSC-312", "CSC-321", "CSC-322", "CSC-364", "CSC-395"])
        by = {o["course"]: o for o in got["options"]}
        self.assertTrue(by["CSC-312"]["eligible"])                # fall course, CSC-207 in progress
        self.assertEqual((by["CSC-322"]["eligible"], by["CSC-322"]["reason"]), (False, "Spring only"))
        self.assertFalse(by["CSC-395"]["eligible"])               # spring only, and needs MAT-215
        flags = [o["eligible"] for o in got["options"]]
        self.assertEqual(flags, sorted(flags, reverse=True))      # eligible first

    def test_plus_button_lists_every_course_not_in_the_plan(self):
        stu = student(ON_ROUTE, schedule={"2027SP": ["2027SP-HIS-100-01"]})
        result = plan(stu)
        got = options(stu, "2027FA")
        listed = {o["course"] for o in got["options"]}
        in_plan = {t["course"] for t in tablets(result).values() if t["course"]}
        self.assertFalse(got["required"])
        self.assertEqual(listed & in_plan, set())
        self.assertNotIn("MAT-208", listed)                       # cross-listed with CSC-208, already taken
        self.assertEqual(listed, {c for c in FIXTURE.courses if FIXTURE.identity(c) not in
                                  {FIXTURE.identity(x) for x in in_plan}})
        by = {o["course"]: o for o in got["options"]}
        self.assertTrue(by["MAT-133"]["eligible"])
        self.assertEqual(by["MAT-215"]["reason"], "Needs MAT-133")
        self.assertEqual(by["SPN-102"]["reason"], "Spring only")

    def test_non_requirement_tablet_lists_all_courses(self):
        edits = [{"op": "add", "term": "2027FA", "course": "HIS-100"}]
        got = options(student(ON_ROUTE), "2027FA", "add:HIS-100:2027FA", edits)
        self.assertFalse(got["required"])
        self.assertIn("HIS-100", {o["course"] for o in got["options"]})   # its own course stays selectable
        self.assertGreater(len(got["options"]), 20)

    def test_a_withdrawn_course_can_be_picked_again(self):
        got = options(student([enr("ECN-111", "2026SP", "withdrawn", "W")], majors=[]), "2027SP")
        self.assertIn("ECN-111", {o["course"] for o in got["options"]})

    def test_locked_term_and_unknown_term(self):
        got = options(student(ON_ROUTE), "2025FA")
        self.assertTrue(all(not o["eligible"] for o in got["options"]))
        with self.assertRaises(PlanError):
            options(student(ON_ROUTE), "1999FA")


class DeterminismTests(unittest.TestCase):
    def test_same_input_same_output(self):
        edits = [{"op": "add", "term": "2027FA", "course": "HIS-100"},
                 {"op": "swap", "term": "2028FA", "tablet": "slot:CS:csc-elective:1", "course": "CSC-312"},
                 {"op": "remove", "term": "2027FA", "tablet": "slot:CS:CSC-301"}]
        runs = {json.dumps(plan(student(ON_ROUTE, majors=["CS", "MATH"]), edits), sort_keys=True)
                for _ in range(5)}
        self.assertEqual(len(runs), 1)

    def test_inputs_are_not_mutated(self):
        stu = student(ON_ROUTE)
        before = json.dumps(stu, sort_keys=True)
        edits = [{"op": "add", "term": "2027FA", "course": "HIS-100"}]
        plan(stu, edits)
        self.assertEqual(json.dumps(stu, sort_keys=True), before)
        self.assertEqual(edits, [{"op": "add", "term": "2027FA", "course": "HIS-100"}])

    def test_unknown_major_is_rejected(self):
        with self.assertRaises(PlanError):
            plan(student(ON_ROUTE), majors=["BASKETRY"])


if __name__ == "__main__":
    unittest.main()
