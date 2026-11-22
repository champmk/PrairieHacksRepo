"""Ledger (what counts) and Match (which tablets get an R)."""
import unittest

from coursegraph.ledger import apply_caps
from coursegraph.matching import choose_route, match_program, max_matching

from helpers import FIXTURE, ON_ROUTE, codes, enr, plan, student, tablets


class LedgerTests(unittest.TestCase):
    def test_withdrawn_and_failed_do_not_count_and_are_not_checked(self):
        # CSC-207 without CSC-161 would be a prerequisite problem if it were checked.
        result = plan(student([
            enr("CSC-151", "2025FA"),
            enr("CSC-161", "2026SP", "withdrawn", "W"),
            enr("CSC-207", "2026SP", "failed", "F"),
            enr("CSC-211", "2026SP", "dropped", None),
        ]))
        tabs = tablets(result)
        for tid, mark in (("enr:CSC-161:2026SP", "W"), ("enr:CSC-207:2026SP", "F"), ("enr:CSC-211:2026SP", "DR")):
            self.assertEqual(tabs[tid]["status"], "not_counted")
            self.assertEqual(tabs[tid]["mark"], mark)
            self.assertTrue(tabs[tid]["locked"])
            self.assertFalse(tabs[tid]["required"])
            self.assertEqual(codes(result, tablet=tid), [])
        self.assertEqual(result["totals"]["counted"], 4)
        self.assertEqual(result["terms"][1]["credits"], 0)
        # The requirements are still open: each comes back as an R tablet.
        for slot in ("slot:CS:CSC-161", "slot:CS:CSC-207", "slot:CS:CSC-211"):
            self.assertIn(slot, tabs)
        # A W does not clear a prerequisite either.
        self.assertGreater(result["terms"].index(next(t for t in result["terms"] if t["id"] == tabs["slot:CS:CSC-207"]["term"])),
                           result["terms"].index(next(t for t in result["terms"] if t["id"] == tabs["slot:CS:CSC-161"]["term"])))

    def test_repeat_after_d_counts_the_latest_attempt(self):
        result = plan(student([enr("CSC-151", "2025FA", grade="D"), enr("CSC-151", "2026SP", grade="B")]))
        tabs = tablets(result)
        self.assertEqual(tabs["enr:CSC-151:2025FA"]["status"], "not_counted")
        self.assertEqual(tabs["enr:CSC-151:2025FA"]["mark"], "D")
        self.assertEqual(tabs["enr:CSC-151:2026SP"]["status"], "completed")
        self.assertTrue(tabs["enr:CSC-151:2026SP"]["required"])
        self.assertEqual(result["totals"]["counted"], 4)
        self.assertNotIn("repeat_not_allowed", codes(result))

    def test_repeat_after_f_is_allowed(self):
        result = plan(student([enr("CSC-151", "2025FA", "failed", "F"), enr("CSC-151", "2026SP", grade="B")]))
        self.assertNotIn("repeat_not_allowed", codes(result))
        self.assertEqual(result["totals"]["counted"], 4)

    def test_repeat_after_c_or_better_is_not_allowed(self):
        result = plan(student([enr("CSC-151", "2025FA", grade="B"), enr("CSC-151", "2026SP", grade="A")]))
        flagged = [w for w in result["warnings"] if w["code"] == "repeat_not_allowed"]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["severity"], "error")
        self.assertEqual(flagged[0]["tablet"], "enr:CSC-151:2026SP")
        self.assertEqual(result["totals"]["counted"], 4)          # no double credit
        self.assertFalse(tablets(result)["enr:CSC-151:2026SP"]["required"])

    def test_ap_counts_for_degree_and_clears_prerequisites(self):
        ap = enr("MAT-131", None, grade="AP", mode="transfer")
        add = [{"op": "add", "term": "2027SP", "course": "MAT-133"}]
        with_ap = plan(student([ap], majors=[]), add)
        without = plan(student([], majors=[]), add)
        self.assertEqual(codes(with_ap, tablet="add:MAT-133:2027SP"), [])
        self.assertIn("prereq_missing", codes(without, tablet="add:MAT-133:2027SP"))
        self.assertEqual(with_ap["totals"]["counted"], 4)
        self.assertEqual(with_ap["prior"][0]["id"], "enr:MAT-131:prior")

    def test_ap_counts_for_a_major_only_when_the_catalog_says_so(self):
        ap = enr("MAT-131", None, grade="AP", mode="transfer")
        result = plan(student([ap], majors=["CS", "MATH"]))
        slots = {p["program"]: {s["id"]: s for s in p["slots"]} for p in result["progress"]}
        # The fixture lists MAT-131 as major credit for Mathematics only.
        self.assertEqual(slots["MATH"]["MATH:MAT-131"]["status"], "completed")
        self.assertNotEqual(slots["CS"]["CS:MAT-131"]["status"], "completed")
        self.assertIn("major_grade", codes(result, tablet="enr:MAT-131:prior"))

    def test_low_grade_and_sdf_do_not_count_for_the_major(self):
        result = plan(student([enr("CSC-151", "2025FA", grade="D"),
                               enr("MAT-131", "2025FA", grade="S", mode="sdf")]))
        tabs = tablets(result)
        for tid in ("enr:CSC-151:2025FA", "enr:MAT-131:2025FA"):
            self.assertFalse(tabs[tid]["required"])
            self.assertIn("major_grade", codes(result, tablet=tid))
        self.assertIn("slot:CS:CSC-151", tabs)                  # the R stays open
        self.assertEqual(result["totals"]["counted"], 8)        # still degree credit

    def test_cross_listed_course_counts_once(self):
        result = plan(student([enr("MAT-208", "2026SP")]),
                      [{"op": "add", "term": "2027SP", "course": "CSC-208"}])
        tabs = tablets(result)
        self.assertEqual(tabs["enr:MAT-208:2026SP"]["counts_for"], ["CS · Discrete math"])
        self.assertIn("duplicate", codes(result, tablet="add:CSC-208:2027SP"))
        self.assertEqual(result["totals"]["counted"], 4)
        # The duplicate adds no credit: planned credit is the requirement tablets alone.
        self.assertEqual(result["totals"]["planned"],
                         sum(t["credits"] for t in tabs.values() if t["id"].startswith("slot:")))

    def test_department_cap(self):
        csc = ["CSC-151", "CSC-161", "CSC-207", "CSC-208", "CSC-211", "CSC-213", "CSC-301", "CSC-312",
               "CSC-321", "CSC-322", "CSC-324", "CSC-341"]
        result = plan(student([enr(c, "2025FA") for c in csc] + [enr("CSC-364", "2026FA", "in_progress")],
                              majors=[]))
        cap = [w for w in result["warnings"] if w["code"] == "dept_cap"]
        self.assertEqual(len(cap), 1)
        self.assertEqual(cap[0]["tablet"], "enr:CSC-364:2026FA")
        self.assertEqual(result["totals"]["by_department"]["CSC"], 48)
        self.assertEqual(result["totals"]["counted"] + result["totals"]["in_progress"], 48)

    def test_division_cap(self):
        counted, events = apply_caps([(n, f"D{n % 3}", "Science", 4) for n in range(24)])
        self.assertEqual(sum(counted.values()), 92)
        self.assertEqual([e[1] for e in events], ["division_cap"])
        self.assertEqual(events[0][3], 4)

    def test_ap_credit_is_not_held_to_the_department_cap(self):
        counted, events = apply_caps([(n, "CSC", "Science", 4) for n in range(12)] + [("ap", None, "Science", 4)])
        self.assertEqual(counted["ap"], 4)
        self.assertEqual(events, [])


class MatchTests(unittest.TestCase):
    def test_augmenting_path_moves_a_course_to_free_a_slot(self):
        slots = [{"id": "wide", "options": ["A", "B", "C"]}, {"id": "narrow", "options": ["A", "B"]}]
        items = [{"course": "A", "status": "completed", "index": 0},
                 {"course": "B", "status": "completed", "index": 1}]
        got = match_program(slots, items, lambda c: c)
        self.assertEqual({k: v["course"] for k, v in got.items()}, {"narrow": "B", "wide": "A"})

    def test_better_tier_wins_the_only_slot(self):
        slots = [{"id": "s", "options": ["A", "B"]}]
        items = [{"course": "B", "status": "projected", "index": 5},
                 {"course": "A", "status": "in_progress", "index": 2}]
        self.assertEqual(match_program(slots, items, lambda c: c)["s"]["course"], "A")

    def test_matching_is_maximum(self):
        slots = [{"options": ["x", "y"]}, {"options": ["x"]}, {"options": ["y", "z"]}]
        owner = max_matching(["y", "x", "z"], slots, lambda item, slot: item in slot["options"])
        self.assertEqual(len(owner), 3)

    def test_one_course_fills_one_slot_per_program_but_may_count_for_two_majors(self):
        result = plan(student(ON_ROUTE, majors=["CS", "MATH"]))
        mat131 = tablets(result)["enr:MAT-131:2025FA"]
        self.assertEqual(sorted(mat131["counts_for"]), ["CS · MAT-131", "MATH · MAT-131"])
        for p in result["progress"]:
            used = [s["course"] for s in p["slots"] if s["status"] in ("completed", "in_progress")]
            self.assertEqual(len(used), len(set(used)))

    def test_shared_projected_course_is_one_tablet_for_both_majors(self):
        result = plan(student([], majors=["CS", "MATH"]))
        tabs = tablets(result)
        self.assertNotIn("slot:MATH:MAT-131", tabs)
        self.assertEqual(sorted(tabs["slot:CS:MAT-131"]["counts_for"]), ["CS · MAT-131", "MATH · MAT-131"])
        # MAT-218, projected for Mathematics, also fills the CS discrete slot.
        self.assertNotIn("slot:CS:csc-discrete", tabs)
        self.assertIn("CS · Discrete math", tabs["slot:MATH:MAT-218"]["counts_for"])

    def test_route_follows_what_the_student_took(self):
        routes = FIXTURE.programs["CS"]["routes"]
        via_208 = choose_route(routes, {"CSC-151": 0, "CSC-208": 1}, FIXTURE.identity)
        via_218 = choose_route(routes, {"CSC-151": 0, "MAT-133": 1, "MAT-215": 2}, FIXTURE.identity)
        self.assertEqual((via_208["id"], via_218["id"]), ("cs-208", "cs-218"))
        result = plan(student([enr("CSC-151", "2025FA"), enr("MAT-131", "2025FA"), enr("MAT-133", "2026SP")]))
        self.assertEqual(result["progress"][0]["route"]["id"], "cs-218")


if __name__ == "__main__":
    unittest.main()
