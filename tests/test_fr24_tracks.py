#!/usr/bin/env python3
"""Tests for work/fr24_tracks.py.

    python3 -m unittest discover -s tests -v

They run against the synthetic export in tests/fixtures, never against archive
data, so they stay fast and independent of whether a month has been built.
"""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "work"))

import fr24_tracks as fr24  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "fr24_2026-06_sample.csv"


class ReadExportTests(unittest.TestCase):
    def test_reads_every_point(self):
        points = fr24.read_export(FIXTURE)
        self.assertEqual(len(points), 164)
        self.assertEqual({p.callsign for p in points}, {"UR713", "UR710", "UR201", "UR202"})

    def test_header_aliases(self):
        self.assertEqual(fr24.CANONICAL["flight_number"], "callsign")
        self.assertEqual(fr24.CANONICAL["tail_number"], "registration")
        self.assertEqual(fr24.CANONICAL["on_ground"], "onground")


class BuildLegsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.airports = fr24.load_airports()
        cls.fleet = fr24.load_fleet()
        cls.legs = fr24.build_legs(fr24.read_export(FIXTURE), cls.airports, cls.fleet)

    def test_leg_count(self):
        self.assertEqual(len(self.legs), 4)

    def test_routes_and_order(self):
        self.assertEqual([leg.route for leg in self.legs],
                         ["EBB-JNB", "JNB-EBB", "EBB-NBO", "NBO-EBB"])

    def test_type_resolved_from_fleet(self):
        self.assertEqual([leg.type for leg in self.legs], ["A338", "A338", "CRJ9", "CRJ9"])

    def test_local_times_use_airport_zone(self):
        outbound = self.legs[0]
        # 04:36 UTC off-blocks in Entebbe (UTC+3)
        self.assertEqual(outbound.takeoff.strftime("%H:%M"), "04:36")
        self.assertEqual(outbound.local_departure.strftime("%H:%M"), "07:36")
        self.assertEqual(outbound.local_arrival.strftime("%H:%M"), "10:29")

    def test_distance_matches_reference(self):
        gc = fr24.load_gc_distances()["EBB-JNB"]
        self.assertAlmostEqual(self.legs[0].distance_km, gc, delta=1)

    def test_gap_splits_a_track(self):
        """One callsign flying EBB-NBO twice in a day becomes two legs, not one."""
        base = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        start, end = (0.042386, 32.443501), (-1.318886, 36.928233)
        points = []
        for trip in range(2):
            offset = timedelta(hours=4 * trip)
            for i in range(11):
                fraction = i / 10
                points.append(fr24.Point(
                    ts=base + offset + timedelta(minutes=6 * i),
                    lat=start[0] + (end[0] - start[0]) * fraction,
                    lon=start[1] + (end[1] - start[1]) * fraction,
                    altitude=30000, onground=False, callsign="UR900"))
        legs = fr24.build_legs(points, self.airports, self.fleet)
        self.assertEqual(len(legs), 2)
        self.assertTrue(all(leg.route == "EBB-NBO" for leg in legs))


class ManifestTests(unittest.TestCase):
    """One file per flight, with the flight record alongside the track."""

    @classmethod
    def setUpClass(cls):
        cls.airports = fr24.load_airports()
        cls.fleet = fr24.load_fleet()

    def test_manifest_supplies_registration_and_type(self):
        points = fr24.read_export(FIXTURE)
        meta = {"file": "UR713-abc.csv", "flight_id_hex": "abc", "number": "UR713",
                "from": "EBB", "to": "JNB", "registration": "5X-NIL",
                "aircraft": "A338"}
        legs = fr24.build_legs(points, self.airports, self.fleet, meta=meta,
                               source="UR713-abc.csv")
        jnb = [leg for leg in legs if leg.destination.code == "JNB"][0]
        self.assertEqual((jnb.registration, jnb.type), ("5X-NIL", "A338"))
        self.assertEqual(jnb.flight_id, "abc")
        self.assertEqual(jnb.source, "UR713-abc.csv")

    def test_track_wins_when_the_record_disagrees(self):
        """A track filed Entebbe-Zanzibar that stops at Kilimanjaro is logged
        Entebbe-Kilimanjaro, with the difference noted."""
        points = fr24.read_export(FIXTURE)
        meta = {"file": "UR334-abc.csv", "number": "UR334", "from": "EBB", "to": "ZNZ"}
        legs = fr24.build_legs(points, self.airports, self.fleet, meta=meta)
        outbound = [leg for leg in legs if leg.origin.code == "EBB"][0]
        self.assertEqual(outbound.destination.code, "JNB")     # what the track shows
        self.assertEqual(outbound.note, "filed as EBB-ZNZ, track EBB-JNB")
        # every leg in the file is checked against the record it was filed under
        self.assertTrue(all(leg.note.startswith("filed as EBB-ZNZ, track ") for leg in legs))

    def test_short_track_is_flagged(self):
        points = fr24.read_export(FIXTURE)
        # keep the outbound leg but cut it off a third of the way along
        cut = [p for p in points if p.callsign == "UR713"][:12]
        legs = fr24.build_legs(cut, self.airports, self.fleet,
                               meta={"number": "UR713", "from": "EBB", "to": "JNB"})
        self.assertEqual(len(legs), 1)
        self.assertIn("track stops", legs[0].note)
        self.assertGreater(legs[0].gap_km, 0)


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        airports = fr24.load_airports()
        legs = fr24.build_legs(fr24.read_export(FIXTURE), airports, fr24.load_fleet())
        cls.log = fr24.render_log("2026-06", legs, fr24.load_gc_distances())

    def test_route_heading(self):
        self.assertIn("**Entebbe – Johannesburg**", self.log)

    def test_flight_line_notation(self):
        self.assertIn("UR713 EBB0736 – 1029JNB A338 1", self.log)

    def test_effective_line(self):
        self.assertIn("*eff 01JUN26* 1 weekly A330-800", self.log)

    def test_period(self):
        self.assertIn("| period | 01JUN26 – 30JUN26 |", self.log)

    def test_distance_falls_back_to_coordinates(self):
        """Routes missing from reference/route_distances.csv still get a distance."""
        airports = fr24.load_airports()
        legs = fr24.build_legs(fr24.read_export(FIXTURE), airports, fr24.load_fleet())
        log = fr24.render_log("2026-06", legs, {})
        self.assertIn("| EBB-JNB | 1 | 1 | A330-800 | 2946 |", log)

    def test_frequency_wording(self):
        self.assertEqual(fr24.frequency_text([1, 2, 3, 4, 5, 6, 7]), "1 daily")
        self.assertEqual(fr24.frequency_text([1, 3, 5]), "3 weekly")


if __name__ == "__main__":
    unittest.main()
