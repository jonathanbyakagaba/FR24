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

    @staticmethod
    def _trip(base, start, end, *, ground_altitude=None):
        """A straight 10-point run from start to end, optionally on the ground."""
        points = []
        for i in range(11):
            fraction = i / 10
            grounded = ground_altitude is not None and i in (0, 10)
            points.append(fr24.Point(
                ts=base + timedelta(minutes=6 * i),
                lat=start[0] + (end[0] - start[0]) * fraction,
                lon=start[1] + (end[1] - start[1]) * fraction,
                altitude=ground_altitude if grounded else 30000,
                speed=5 if grounded else 450,
                onground=grounded,
                callsign="UR900"))
        return points

    def test_a_ground_stop_splits_a_track(self):
        """EBB-NBO, sit on the ground, NBO-EBB: two legs."""
        base = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        ebb, nbo = (0.042386, 32.443501), (-1.318886, 36.928233)
        points = self._trip(base, ebb, nbo, ground_altitude=0) + \
            self._trip(base + timedelta(minutes=130), nbo, ebb, ground_altitude=0)
        legs = fr24.build_legs(points, self.airports, self.fleet)
        self.assertEqual(len(legs), 2)
        self.assertEqual([leg.route for leg in legs], ["EBB-NBO", "NBO-EBB"])
        self.assertTrue(all(leg.track_complete for leg in legs))

    def test_a_coverage_hole_does_not_split_a_track(self):
        """A gap in the middle of one flight is a hole, not a landing."""
        base = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        ebb, nbo = (0.042386, 32.443501), (-1.318886, 36.928233)
        # wheels up out of EBB, nothing recorded for two and a half hours, then
        # back on the air and down at NBO
        first = self._trip(base, ebb, nbo, ground_altitude=0)[:6]
        second = self._trip(base + timedelta(hours=3), ebb, nbo, ground_altitude=0)[5:]
        legs = fr24.build_legs(first + second, self.airports, self.fleet)
        self.assertEqual(len(legs), 1)
        self.assertFalse(legs[0].track_complete)
        self.assertIn("hole en route", legs[0].note)


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
        """The fixture covers two days, so the period says so rather than
        claiming the whole calendar month."""
        self.assertIn("| period | 01JUN26 – 02JUN26 (part month, 2 days) |", self.log)

    def test_track_coverage_line(self):
        self.assertIn("| track coverage | 4 of 4 flights end to end |", self.log)

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
