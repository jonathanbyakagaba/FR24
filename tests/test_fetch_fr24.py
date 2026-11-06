#!/usr/bin/env python3
"""Tests for the rotation chain and work/fetch_fr24_tracks.py.

    python3 -m unittest discover -s tests -v

No network, no credentials: the Flightradar24 client is replaced by a stand-in
that answers with the two shapes the fetch script consumes, so the whole path —
gap list, matching, playback, track file, manifest row, rebuilt leg — is
exercised offline.
"""

import csv
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "work"))

import fr24_tracks as fr24  # noqa: E402
import fetch_fr24_tracks as fetch  # noqa: E402

UTC = timezone.utc
EBB = next(ap for ap in fr24.load_airports() if ap.code == "EBB")
HRE = next(ap for ap in fr24.load_airports() if ap.code == "HRE")
LUN = next(ap for ap in fr24.load_airports() if ap.code == "LUN")
JUB = next(ap for ap in fr24.load_airports() if ap.code == "JUB")


def leg(origin, destination, takeoff, landing, callsign="UR720",
        registration="5X-KOB", type_code="CRJ9") -> fr24.Leg:
    return fr24.Leg(
        callsign=callsign, registration=registration, type=type_code,
        origin=origin, destination=destination,
        takeoff=takeoff, landing=landing,
        points=100, distance_km=1000.0, max_altitude_ft=36000,
    )


def at(day: int, hour: int, minute: int = 0, month: int = 9) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=UTC)


class RotationTests(unittest.TestCase):
    def test_a_tag_stop_chains_the_whole_rotation(self):
        """EBB-HRE then LUN-EBB is one rotation, not two orphan legs."""
        legs = [
            leg(EBB, HRE, at(5, 13, 17), at(5, 15, 0)),
            leg(LUN, EBB, at(5, 17, 30), at(5, 19, 45), callsign="UR721"),
        ]
        rotations = fr24.build_rotations(legs)
        self.assertEqual(len(rotations), 1)
        rotation = rotations[0]
        self.assertEqual(rotation.chain, "EBB–HRE–LUN–EBB")
        self.assertEqual(rotation.marked_chain, "EBB–HRE–[LUN]–EBB")
        self.assertEqual([hop.route for hop in rotation.hops], ["HRE-LUN"])
        self.assertFalse(rotation.complete)
        self.assertEqual(rotation.id, "5X-KOB-20260905")

    def test_a_fully_tracked_rotation_has_no_hop(self):
        legs = [
            leg(EBB, HRE, at(5, 13, 17), at(5, 15, 0)),
            leg(HRE, LUN, at(5, 15, 45), at(5, 17, 0)),
            leg(LUN, EBB, at(5, 17, 45), at(5, 20, 0), callsign="UR721"),
        ]
        rotation = fr24.build_rotations(legs)[0]
        self.assertEqual(rotation.chain, "EBB–HRE–LUN–EBB")
        self.assertEqual(rotation.marked_chain, "EBB–HRE–LUN–EBB")
        self.assertTrue(rotation.complete)

    def test_a_night_rotation_crossing_midnight_stays_whole(self):
        """Wheels up at 01:37 local is still the previous flying day."""
        legs = [
            leg(EBB, LUN, at(4, 18, 15), at(4, 20, 36)),
            leg(HRE, EBB, at(4, 23, 37), at(5, 2, 17), callsign="UR721"),
        ]
        rotations = fr24.build_rotations(legs)
        self.assertEqual(len(rotations), 1)
        self.assertEqual(rotations[0].day, datetime(2026, 9, 4).date())

    def test_different_days_are_different_rotations(self):
        legs = [
            leg(EBB, JUB, at(5, 7, 0), at(5, 8, 0)),
            leg(EBB, JUB, at(6, 7, 0), at(6, 8, 0)),
        ]
        self.assertEqual(len(fr24.build_rotations(legs)), 2)

    def test_a_hole_at_the_same_airport_claims_nothing(self):
        """Landing and leaving the same airport again proves no lost sector."""
        legs = [
            leg(EBB, JUB, at(5, 3, 0), at(5, 4, 0)),
            leg(JUB, EBB, at(5, 5, 0), at(5, 6, 0), callsign="UR721"),
            leg(EBB, HRE, at(5, 12, 0), at(5, 14, 0), callsign="UR722"),
        ]
        rotation = fr24.build_rotations(legs)[0]
        self.assertEqual(rotation.hops, [])
        self.assertEqual(rotation.chain, "EBB–JUB–EBB–HRE")

    def test_an_implausible_hole_is_marked_unconfirmed(self):
        """Five minutes on the ground cannot hide Harare-Lusaka."""
        legs = [
            leg(EBB, HRE, at(5, 13, 0), at(5, 14, 0)),
            leg(LUN, EBB, at(5, 14, 5), at(5, 16, 0), callsign="UR721"),
        ]
        rotation = fr24.build_rotations(legs)[0]
        self.assertEqual(len(rotation.hops), 1)
        self.assertFalse(rotation.hops[0].plausible)
        self.assertEqual(rotation.marked_chain, "EBB–HRE–[LUN?]–EBB")

    def test_rotations_are_written_with_the_hop(self):
        legs = [
            leg(EBB, HRE, at(5, 13, 17), at(5, 15, 0)),
            leg(LUN, EBB, at(5, 17, 30), at(5, 19, 45), callsign="UR721"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rotations.csv"
            fr24.write_rotations(path, fr24.build_rotations(legs))
            with path.open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["chain"], "EBB–HRE–LUN–EBB")
        self.assertEqual(rows[0]["untracked_hops"], "HRE-LUN")
        self.assertEqual(rows[0]["sectors"], "3")
        self.assertEqual(rows[0]["complete"], "no")

    def test_the_log_section_names_the_missing_hop(self):
        legs = [
            leg(EBB, HRE, at(5, 13, 17), at(5, 15, 0)),
            leg(LUN, EBB, at(5, 17, 30), at(5, 19, 45), callsign="UR721"),
        ]
        lines = "\n".join(fr24.render_rotations(fr24.build_rotations(legs)))
        self.assertIn("## Rotations", lines)
        self.assertIn("EBB–HRE–[LUN]–EBB", lines)


class GapTests(unittest.TestCase):
    def test_gaps_come_from_the_chain(self):
        legs = [
            leg(EBB, HRE, at(5, 13, 17), at(5, 15, 0)),
            leg(LUN, EBB, at(5, 17, 30), at(5, 19, 45), callsign="UR721"),
        ]
        gaps = fetch.gaps_from_rotations(fr24.build_rotations(legs))
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].sector, "HRE-LUN")
        self.assertEqual(gaps[0].registration, "5X-KOB")
        self.assertEqual(gaps[0].day, "2026-09-05")
        self.assertTrue(gaps[0].plausible)

    def test_the_gap_list_round_trips(self):
        legs = [
            leg(EBB, HRE, at(5, 13, 17), at(5, 15, 0)),
            leg(LUN, EBB, at(5, 17, 30), at(5, 19, 45), callsign="UR721"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gaps.csv"
            fetch.write_gap_list(path, fetch.gaps_from_rotations(fr24.build_rotations(legs)))
            gaps = fetch.read_gap_list(path)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].sector, "HRE-LUN")
        self.assertEqual(gaps[0].registration, "5X-KOB")

    def test_a_hand_maintained_sheet_is_read_despite_its_shifted_columns(self):
        """The reconciliation sheet keeps a Month column its rows do not have."""
        rows = [
            ["Name", "Date", "Month", "Flight", "Sector", "Tail", "Board_Status",
             "Planned_STD", "Leg_gap", "Action", "Track_to_check", "Note"],
            # note: no Month value, so every later column is one to the left
            ["UR720 LUN to HRE 2026-09-04", "2026-09-04", "UR720", "LUN-HRE", "5X-KOB",
             "SCHEDULED", "2026-09-04 20:45", "no leg in the log",
             "check the nearby track first, then re-fetch", "UR720-418217cc.csv",
             "belongs to the leg before or after it"],
            ["UR902 EBB to LOS 2026-09-24", "2026-09-24", "UR902", "EBB-LOS", "ET-APL",
             "SCHEDULED", "2026-09-24 19:00", "track in the archive",
             "rebuild the log row from the track already on disk", "",
             "track overlaps, no log row"],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "worklist.csv"
            with path.open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(rows)
            gaps = fetch.read_gap_list(path)
        self.assertEqual(len(gaps), 1, "the rebuild-only row needs no fetch")
        gap = gaps[0]
        self.assertEqual(gap.sector, "LUN-HRE")
        self.assertEqual(gap.flight_number, "UR720")
        self.assertEqual(gap.registration, "5X-KOB")
        # 20:45 printed on the board is Entebbe time
        self.assertEqual(gap.planned, datetime(2026, 9, 4, 17, 45, tzinfo=UTC))


# --------------------------------------------------------------------------- #
# the client, stood in for
# --------------------------------------------------------------------------- #

class _Result:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


class _Playback(_Result):
    def __init__(self, payload, metadata):
        super().__init__(payload)
        self._metadata = metadata

    def metadata(self):
        return self._metadata


def _flight(flight_id, number, origin_icao, destination_icao, departure, arrival):
    return {
        "identification": {"id": flight_id, "number": {"default": number},
                           "callsign": number},
        "airport": {"origin": {"code": {"icao": origin_icao}},
                    "destination": {"code": {"icao": destination_icao}}},
        "time": {"real": {"departure": int(departure.timestamp()),
                          "arrival": int(arrival.timestamp())},
                 "scheduled": {"departure": int(departure.timestamp()),
                               "arrival": int(arrival.timestamp())}},
    }


class _FlightList:
    def __init__(self, flights, page_size=100):
        self.flights = flights
        self.page_size = page_size

    async def fetch_all(self, reg=None, flight=None, timestamp=None,
                        filter_by=None, limit=100, max_pages=None, delay=0, **kwargs):
        wanted = (flight or reg or "").upper()
        items = [item for item in self.flights
                 if wanted in (item["identification"]["number"]["default"].upper(),
                               item["_registration"].upper())]
        for start in range(0, len(items), self.page_size):
            yield _Result({"result": {"response": {
                "data": items[start:start + self.page_size]}}})


class _PlaybackService:
    def __init__(self, tracks):
        self.tracks = tracks

    async def fetch(self, flight_id, timestamp=None):
        track, metadata = self.tracks[str(flight_id)]
        return _Playback({"result": {"response": {"data": {"flight": {
            "track": track}}}}}, metadata)


class FakeClient:
    """Just enough of `fr24.FR24` for the fetch path."""

    def __init__(self, flights, tracks):
        self.flight_list = _FlightList(flights)
        self.playback = _PlaybackService(tracks)


def _track(start: datetime, minutes=75, points=10, origin=None, destination=None):
    """A playback track from one airport to the other, down at both ends."""
    origin = origin or LUN
    destination = destination or HRE
    rows = []
    for index in range(points):
        fraction = index / (points - 1)
        rows.append({
            "timestamp": int((start + timedelta(minutes=minutes * fraction)).timestamp()),
            "position": {"latitude": origin.lat + (destination.lat - origin.lat) * fraction,
                         "longitude": origin.lon + (destination.lon - origin.lon) * fraction},
            "altitude": {"feet": 0 if index in (0, points - 1) else 30000},
            "speed": {"kts": 0 if index in (0, points - 1) else 420},
            "heading": 180,
        })
    return rows


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.departure = at(4, 17, 45)
        self.arrival = self.departure + timedelta(hours=1, minutes=15)
        self.flights = [{
            **_flight("4194953e", "UR720", "FLLS", "FVHA", self.departure, self.arrival),
            "_registration": "5X-KOB",
        }]
        self.tracks = {"4194953e": (_track(self.departure), {
            "flight_id": "4194953e", "flight_number": "UR720", "callsign": "UGD720",
            "origin": "FLLS", "destination": "FVHA", "registration": "5X-KOB",
            "model_code": "CRJ9",
        })}
        self.client = FakeClient(self.flights, self.tracks)

    def _args(self, **overrides):
        import argparse
        base = dict(max_pages=3, delay=0, pause=0, limit=0)
        base.update(overrides)
        return argparse.Namespace(**base)

    def test_a_hop_is_turned_into_a_track_file(self):
        gap = fetch.Gap(origin="LUN", destination="HRE", registration="5X-KOB",
                        after=at(4, 16, 30), before=at(4, 19, 30))
        import asyncio
        with tempfile.TemporaryDirectory() as tmp:
            row = asyncio.run(fetch.fetch_gap(self.client, gap, Path(tmp), self._args()))
            self.assertIsNotNone(row)
            written = Path(tmp) / row["file"]
            self.assertTrue(written.exists())
            header = written.open(encoding="utf-8").readline().strip().split(",")
            self.assertEqual(header, fetch.TRACK_COLUMNS)
            self.assertEqual(row["source"], fetch.API_SOURCE)
            # the export reads back as the leg the rotation was missing
            legs = fr24.build_legs(fr24.read_export(written), fr24.load_airports(),
                                   fr24.load_fleet())
            self.assertEqual(len(legs), 1)
            self.assertEqual((legs[0].origin.code, legs[0].destination.code), ("LUN", "HRE"))

    def test_the_rebuilt_rotation_now_reads_end_to_end(self):
        import asyncio
        gap = fetch.Gap(origin="LUN", destination="HRE", registration="5X-KOB",
                        after=at(4, 16, 30), before=at(4, 19, 30))
        with tempfile.TemporaryDirectory() as tmp:
            row = asyncio.run(fetch.fetch_gap(self.client, gap, Path(tmp), self._args()))
            fetched_leg = fr24.build_legs(
                fr24.read_export(Path(tmp) / row["file"]),
                fr24.load_airports(), fr24.load_fleet())[0]
        rotation = fr24.build_rotations([
            leg(EBB, LUN, at(4, 13, 0), at(4, 15, 30)),
            fetched_leg,
            leg(HRE, EBB, at(4, 20, 15), at(4, 22, 0), callsign="UR721"),
        ])[0]
        self.assertEqual(rotation.chain, "EBB–LUN–HRE–EBB")
        self.assertEqual(rotation.marked_chain, "EBB–LUN–HRE–EBB")
        self.assertTrue(rotation.complete)

    def test_a_route_that_does_not_match_is_not_taken(self):
        """A flight of the right number on the wrong pair is not the hop."""
        self.flights[0]["airport"]["destination"]["code"]["icao"] = "FAOR"
        gap = fetch.Gap(origin="LUN", destination="HRE", registration="5X-KOB",
                        after=at(4, 16, 30), before=at(4, 19, 30))
        import asyncio
        with tempfile.TemporaryDirectory() as tmp:
            row = asyncio.run(fetch.fetch_gap(self.client, gap, Path(tmp), self._args()))
            self.assertIsNone(row)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_manifest_gains_a_source_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.csv"
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["file", "flight_id_hex", "number"])
                writer.writerow(["UR110-4173c002.csv", "4173c002", "UR110"])
            fetch.append_manifest(path, [{
                "file": "UR720-4194953e.csv", "flight_id_hex": "4194953e",
                "number": "UR720", "source": fetch.API_SOURCE}])
            with path.open(encoding="utf-8") as fh:
                rows = {row["file"]: row for row in csv.DictReader(fh)}
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows["UR110-4173c002.csv"]["source"], fetch.ENUMERATION_SOURCE)
        self.assertEqual(rows["UR720-4194953e.csv"]["source"], fetch.API_SOURCE)


if __name__ == "__main__":
    unittest.main()
