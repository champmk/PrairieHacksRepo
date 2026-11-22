"""COLSS snapshot importer, against a copy of the documented sample responses."""
import copy
import json
import os
import tempfile
import unittest

from coursegraph.colss import clock, main, sections_from_colss, term_id

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "fixtures", "colss_snapshot.json")


def snapshot():
    with open(SNAPSHOT, encoding="utf-8") as f:
        return json.load(f)


class ColssTests(unittest.TestCase):
    def test_sample_responses_map_to_the_contract_section_shape(self):
        snap = snapshot()
        (section,) = sections_from_colss(snap["search"], snap["sections"])
        self.assertEqual(section, {
            "id": "2027SP-CSC-151-01", "course": "CSC-151", "term": "2027SP", "number": "01",
            "instructor": "Samuel Rebelsky", "available": 10, "capacity": 24, "meetings": [],
            "colss_id": "99067"})

    def test_meetings_are_read_when_present(self):
        snap = snapshot()
        entry = snap["sections"]["5044"]["SectionsRetrieved"]["TermsAndSections"][0]["Sections"][0]
        entry["Section"]["Meetings"] = [{"Days": [1, 3, 5], "StartTime": "08:00:00", "EndTime": "09:20:00",
                                         "Building": "Noyce Science Ctr", "Room": "3813"}]
        (section,) = sections_from_colss(snap["search"], snap["sections"])
        self.assertEqual(section["meetings"], [{"days": ["M", "W", "F"], "start": "08:00", "end": "09:20",
                                                "room": "Noyce Science Ctr 3813"}])
        del entry["Section"]["Meetings"]
        entry["FormattedMeetingTimes"] = [{"DaysOfWeekDisplay": "T/Th", "StartTimeDisplay": "1:10 PM",
                                           "EndTimeDisplay": "2:30 PM"}]
        (section,) = sections_from_colss(snap["search"], snap["sections"])
        self.assertEqual(section["meetings"], [{"days": ["T", "R"], "start": "13:10", "end": "14:30", "room": None}])

    def test_only_matching_section_ids_are_kept(self):
        snap = snapshot()
        block = snap["sections"]["5044"]["SectionsRetrieved"]["TermsAndSections"][0]
        other = copy.deepcopy(block["Sections"][0])
        other["Section"].update(Id="11111", Number="09")
        block["Sections"].append(other)
        self.assertEqual([s["colss_id"] for s in sections_from_colss(snap["search"], snap["sections"])], ["99067"])

    def test_missing_data_gives_no_sections(self):
        self.assertEqual(sections_from_colss({}, {}), [])
        self.assertEqual(sections_from_colss(snapshot()["search"], {}), [])

    def test_small_parsers(self):
        self.assertEqual(term_id("2027/SP"), "2027SP")
        self.assertEqual([clock("8:00 AM"), clock("12:05 PM"), clock("12:00 AM"), clock("13:10"), clock("x")],
                         ["08:00", "12:05", "00:00", "13:10", None])

    def test_cli_writes_a_sections_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "sections.json")
            self.assertEqual(main(["import", SNAPSHOT, "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                written = json.load(f)
        self.assertEqual(written["origin"], "colss")
        self.assertEqual([s["id"] for s in written["sections"]], ["2027SP-CSC-151-01"])

    def test_module_has_no_network_code(self):
        import coursegraph.colss as module
        with open(module.__file__, encoding="utf-8") as f:
            source = f.read()
        for word in ("import requests", "urllib", "http.client", "socket", "Session("):
            self.assertNotIn(word, source)


if __name__ == "__main__":
    unittest.main()
