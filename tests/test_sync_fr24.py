#!/usr/bin/env python3
"""Tests for work/sync_fr24.py — the nightly harvest.

    python3 -m unittest discover -s tests -v

The Flightradar24 client is stood in for, so a whole night's run is exercised
against a throwaway copy of the repository: flight lists, a playback, the track
on disk, the manifest row, the ledger, the rebuilt month and the index.
"""

import argparse
import asyncio
import csv
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "work"))

import fr24_tracks as fr24  # noqa: E402
import fetch_fr24_tracks as fetch  # noqa: E402
import sync_fr24 as sync  # noqa: E402
from test_fetch_fr24 import (  # noqa: E402
    FakeClient, _Playback, _Result, _flight, _track, at)

UTC = timezone.utc
LUN = next(ap for ap in fr24.load_airports() if ap.code == "LUN")
HRE = next(ap for ap in fr24.load_airports() if ap.code == "HRE")


class _AirportList:
    def __init__(self, registrations):
        self.registrations = registrations

    async def fetch(self, airport=None, mode=None, page=1, limit=100, timestamp=None):
        items = [{"aircraft": {"registration": reg}} for reg in self.registrations]
        return _Result({"result": {"response": {"data": items}}})


def build_root(tmp: Path) -> Path:
    """A throwaway repository: reference data, an empty month, an index to fill."""
    root = tmp / "repo"
    (root / "archive" / "2026-09" / "tracks").mkdir(parents=True)
    shutil.copytree(ROOT / "reference", root / "reference")
    (root / "archive" / "README.md").write_text(
        "# The archive\n\nProse above the table is left alone.\n\n"
        f"{sync.INDEX_HEADER}\n{sync.INDEX_RULE}\n"
        "| **total** | **0** | **0 h 00 min** | **0** | — | — | — | — | |\n\n"
        "Prose below the table is left alone too.\n", encoding="utf-8")
    return root


def args(**overrides):
    base = dict(days=3, since=None, ignore_state=True, dry_run=False,
                no_rebuild=False, root=None, limit=400, max_pages=5, delay=0,
                pause=0)
    base.update(overrides)
    return argparse.Namespace(**base)


def client_with(flights, tracks, registrations=("5X-KOB",)):
    client = FakeClient(flights, tracks)
    client.airport_list = _AirportList(registrations)
    return client


async def _empty_playback(flight_id, timestamp=None):
    return _Playback({"result": {"response": {"data": {"flight": {"track": []}}}}}, {})


class LedgerTests(unittest.TestCase):
    def test_a_tracked_flight_is_not_asked_for_again(self):
        tracked = {"4194953e"}
        self.assertTrue(sync.already_known({"identification": {"id": "4194953e"}},
                                           {}, tracked, datetime.now(tz=UTC)))

    def test_a_missing_track_is_retried_for_a_couple_of_days_and_then_dropped(self):
        now = datetime.now(tz=UTC)
        item = {"identification": {"id": "aaaa1111"}}
        entry = {"status": "no-track",
                 "checked_utc": (now - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.assertFalse(sync.already_known(item, {"aaaa1111": entry}, set(), now),
                         "a playback that was not there last night is worth asking "
                         "for again")
        entry["checked_utc"] = (now - timedelta(days=sync.RETRY_DAYS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        self.assertTrue(sync.already_known(item, {"aaaa1111": entry}, set(), now),
                        "after a couple of nights it is left alone")


class MonthRoutingTests(unittest.TestCase):
    def test_a_track_is_filed_in_the_month_the_leg_departs_in_local_time(self):
        """The builder logs by local departure at origin, so the sync files by it too.

        Bombay is two and a half hours ahead of Kampala: a 18:45Z departure on
        30 September is already 1 October in India, and belongs to October.
        """
        item = {"airport": {"origin": {"code": {"icao": "VABB"}}}}
        departure = datetime(2026, 9, 30, 18, 45, tzinfo=UTC)
        self.assertEqual(sync.leg_month(item, departure), "2026-10")
        same = {"airport": {"origin": {"code": {"icao": "HUEN"}}}}
        self.assertEqual(sync.leg_month(same, departure), "2026-09")


class HarvestTests(unittest.TestCase):
    def setUp(self):
        self.departure = at(4, 17, 45)
        self.arrival = self.departure + timedelta(hours=1, minutes=15)
        self.flight = {
            **_flight("4194953e", "UR720", "FLLS", "FVHA", self.departure, self.arrival),
            "_registration": "5X-KOB",
        }
        self.tracks = {"4194953e": (_track(self.departure), {
            "flight_id": "4194953e", "flight_number": "UR720", "callsign": "UGD720",
            "origin": "FLLS", "destination": "FVHA", "registration": "5X-KOB",
            "model_code": "CRJ9",
        })}

    def test_discovery_adds_an_airframe_the_fleet_file_does_not_list(self):
        client = client_with([self.flight], self.tracks, registrations=("5X-ABC",))
        airframes, note = asyncio.run(sync.discover_airframes(
            client, self.departure, self.arrival, ["5X-KOB"]))
        self.assertIn("5X-KOB", airframes)
        self.assertIn("5X-ABC", airframes)
        self.assertIn("new airframes", note)

    def test_the_harvest_skips_what_is_already_on_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(Path(tmp))
            (root / "archive" / "2026-09" / "tracks" / "UR720-4194953e.csv").write_text(
                "Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction\n",
                encoding="utf-8")
            client = client_with([self.flight], self.tracks)
            stats = sync.Stats(window=(self.departure - timedelta(days=1),
                                       self.arrival + timedelta(days=1)))
            todo = asyncio.run(sync.gather(client, args(), root, stats))
        self.assertEqual(todo, [])

    def test_a_new_flight_is_written_into_its_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(Path(tmp))
            client = client_with([self.flight], self.tracks)
            stats = sync.Stats(window=(self.departure - timedelta(days=1),
                                       self.arrival + timedelta(days=1)))
            row = asyncio.run(sync.fetch_one(client, "5X-KOB", self.flight, root, stats))
            written = root / "archive" / "2026-09" / "tracks" / row["file"]
            self.assertTrue(written.exists())
            self.assertEqual(row["source"], fetch.API_SOURCE)
            self.assertEqual(stats.months, {"2026-09"})


class NightlyRunTests(unittest.TestCase):
    """One night, end to end: tracks in, month rebuilt, index and state written."""

    def setUp(self):
        self.departure = at(4, 17, 45)
        self.arrival = self.departure + timedelta(hours=1, minutes=15)
        self.flight = {
            **_flight("4194953e", "UR720", "FLLS", "FVHA", self.departure, self.arrival),
            "_registration": "5X-KOB",
        }
        self.tracks = {"4194953e": (_track(self.departure), {
            "flight_id": "4194953e", "flight_number": "UR720", "callsign": "UGD720",
            "origin": "FLLS", "destination": "FVHA", "registration": "5X-KOB",
            "model_code": "CRJ9",
        })}

    def test_a_night_produces_a_month_a_readme_an_index_and_a_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(Path(tmp))
            client = client_with([self.flight], self.tracks)
            run_args = args(since="2026-09-04", days=3)
            # the window is fixed; the run itself decides what is new
            code = asyncio.run(sync.run(client, run_args, root))
            month = root / "archive" / "2026-09"
            self.assertEqual(code, sync.EXIT_OK)
            self.assertTrue((month / "flights_2026-09.csv").exists())
            self.assertTrue((month / "rotations_2026-09.csv").exists())
            self.assertTrue((month / "aeroroutes_2026-09.md").exists())
            readme = (month / "README.md").read_text(encoding="utf-8")
            self.assertIn("Uganda Airlines' September 2026 operation", readme)
            index = (root / "archive" / "README.md").read_text(encoding="utf-8")
            self.assertIn("[`2026-09/`](2026-09/)", index)
            self.assertIn("Prose above the table is left alone.", index)
            self.assertIn("| **total** | **1** |", index)
            ledger = sync.load_ledger(root)
            self.assertEqual(ledger["4194953e"]["status"], "tracked")
            self.assertEqual(ledger["4194953e"]["month"], "2026-09")
            state = sync.read_state(root)
            self.assertEqual(state["fetched"], 1)
            self.assertEqual(state["months"], ["2026-09"])

    def test_a_second_night_fetches_nothing_and_is_happy_about_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(Path(tmp))
            client = client_with([self.flight], self.tracks)
            asyncio.run(sync.run(client, args(since="2026-09-04"), root))
            code = asyncio.run(sync.run(client, args(since="2026-09-04"), root))
            self.assertEqual(code, sync.EXIT_OK)

    def test_a_night_where_every_new_flight_fails_is_flagged(self):
        """Silence is the failure mode worth catching: ask, get nothing, say so."""
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(Path(tmp))
            client = client_with([self.flight], {})  # playback service returns nothing
            client.playback.fetch = _empty_playback
            code = asyncio.run(sync.run(client, args(since="2026-09-04"), root))
            self.assertEqual(code, sync.EXIT_SUSPICIOUS)

    def test_a_readme_is_drafted_only_when_a_month_has_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(Path(tmp))
            month = root / "archive" / "2026-09"
            (month / "README.md").write_text("# Hand written\n", encoding="utf-8")
            created = sync.write_month_readme(root, "2026-09")
            self.assertFalse(created)
            self.assertEqual((month / "README.md").read_text(encoding="utf-8"),
                             "# Hand written\n")


if __name__ == "__main__":
    unittest.main()
