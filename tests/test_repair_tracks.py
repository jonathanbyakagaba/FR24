#!/usr/bin/env python3
"""Tests for work/repair_tracks.py — putting the coordinates back.

    python3 -m unittest discover -s tests -v

The archive is a handful of throwaway files: two tracks with no position, one
good track to be left alone, and a manifest that names the flight each one came
from. The client is stood in for, so the repair path runs end to end without a
subscription.
"""

import asyncio
import csv
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "work"))

import fetch_fr24_tracks as fetch  # noqa: E402
import fr24_tracks as fr24  # noqa: E402
import repair_tracks as repair_mod  # noqa: E402

WHEN = datetime(2026, 11, 10, 9, 30, tzinfo=timezone.utc)


def track_rows(points, callsign="UGD334", registration="5X-KOB", zero=False):
    rows = []
    for index in range(points):
        stamp = int(WHEN.timestamp()) + index * 60
        position = ("0.000000,0.000000" if zero
                    else f"{-0.05 + index * 0.01:.6f},{32.44 + index * 0.01:.6f}")
        rows.append([stamp, datetime.fromtimestamp(stamp, tz=timezone.utc)
                     .strftime("%Y-%m-%dT%H:%M:%SZ"), callsign, registration,
                     position, 30000, 420, 180])
    return rows


def write_track_file(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(fetch.TRACK_COLUMNS)
        writer.writerows(rows)


def manifest_row(name, flight_id, atd="2026-11-10T09:30:00Z"):
    return {
        "file": name, "flight_id_hex": flight_id, "number": "UR334", "callsign": "UGD334",
        "date": "2026-11-10", "from": "ZNZ", "to": "JRO", "registration": "5X-KOB",
        "aircraft": "CRJ9", "atd_utc": atd, "ata_utc": "", "std_utc": "", "sta_utc": "",
        "track_points": "5", "sha256": "", "source": fetch.API_SOURCE,
    }


class Archive:
    """A month with one empty track, one good track and a manifest."""

    def __init__(self, root: Path):
        self.root = root
        tracks = root / "archive" / "2026-11" / "tracks"
        tracks.mkdir(parents=True)
        write_track_file(tracks / "UR334-empty.csv", track_rows(5, zero=True))
        write_track_file(tracks / "UR720-good.csv", track_rows(4, callsign="UGD720"))
        rows = [manifest_row("UR334-empty.csv", "11112222"),
                manifest_row("UR720-good.csv", "33334444")]
        with (tracks / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fetch.MANIFEST_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        self.tracks = tracks


def playback_points(points=6, zero=False):
    return [{"timestamp": int(WHEN.timestamp()) + index * 120,
             "latitude": 0.0 if zero else -0.04 + index * 0.01,
             "longitude": 0.0 if zero else 32.45 + index * 0.01,
             "altitude": {"feet": 30000}, "speed": {"kts": 420}, "heading": 180}
            for index in range(points)]


class _Result:
    def __init__(self, track):
        self._track = track

    def to_dict(self):
        return {"result": {"response": {"data": {"flight": {"track": self._track}}}}}


class _Playback:
    def __init__(self, tracks):
        self.tracks = tracks

    async def fetch(self, flight_id, timestamp=None):
        return _Result(self.tracks.get(str(flight_id), []))


class FakeClient:
    """Only the playback service: a repair asks for nothing else."""

    def __init__(self, tracks):
        self.playback = _Playback(tracks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def login(self, *_args, **_kwargs):
        return True


class FindingTests(unittest.TestCase):
    def test_only_the_tracks_without_positions_are_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            found = repair_mod.empty_tracks(Path(tmp))
        self.assertEqual([track.path.name for track in found], ["UR334-empty.csv"])

    def test_the_manifest_row_travels_with_the_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            Archive(Path(tmp))
            found = repair_mod.empty_tracks(Path(tmp))
        self.assertEqual(found[0].flight_id, "11112222")
        self.assertEqual(found[0].departure, WHEN)
        self.assertIn("UR334", found[0].describe())

    def test_an_archive_with_nothing_in_it_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(repair_mod.empty_tracks(Path(tmp)), [])

    def test_a_month_can_be_chosen(self):
        with tempfile.TemporaryDirectory() as tmp:
            Archive(Path(tmp))
            self.assertEqual(repair_mod.empty_tracks(Path(tmp), ["2026-10"]), [])


class RewriteTests(unittest.TestCase):
    def test_the_points_are_replaced_and_the_flight_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            track = repair_mod.empty_tracks(Path(tmp))[0]
            count = repair_mod.rewrite(track, playback_points(6))
            written = list(csv.DictReader((archive.tracks / "UR334-empty.csv").open(
                newline="", encoding="utf-8-sig")))
        self.assertEqual(count, 6)
        self.assertEqual(len(written), 6)
        self.assertEqual(written[0]["Callsign"], "UGD334")
        self.assertEqual(written[0]["Registration"], "5X-KOB")
        self.assertNotEqual(written[0]["Position"], "0.000000,0.000000")
        self.assertEqual(track.row["track_points"], 6)
        self.assertEqual(len(track.row["sha256"]), 64)

    def test_the_manifest_can_be_written_back_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            rows = list(fr24.load_manifest(archive.tracks / "manifest.csv").values())
            repair_mod.write_manifest(archive.tracks / "manifest.csv", rows)
            again = fr24.load_manifest(archive.tracks / "manifest.csv")
        self.assertEqual(len(again), 2)
        self.assertIn("UR720-good.csv", again)


class PlanTests(unittest.TestCase):
    def test_newest_first_and_written_off_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            Archive(Path(tmp))
            found = repair_mod.empty_tracks(Path(tmp))
            state = {"attempts": {"11112222": {"tries": 2}}}
            self.assertEqual(repair_mod.plan(found, state, max_tries=2), [])
            self.assertEqual(len(repair_mod.plan(found, {"attempts": {}}, max_tries=2)), 1)

    def test_a_limit_is_respected(self):
        tracks = [repair_mod.Track("2026-11", Path(f"{n}.csv"), {"atd_utc": f"2026-11-1{n}T00:00:00Z"})
                  for n in range(5)]
        self.assertEqual(len(repair_mod.plan(tracks, {"attempts": {}}, 2, limit=3)), 3)


class RepairTests(unittest.TestCase):
    def args(self, **kwargs):
        import argparse
        base = dict(minutes=1, pause=0)
        base.update(kwargs)
        return argparse.Namespace(**base)

    def test_a_playback_with_coordinates_is_written_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            tracks = repair_mod.empty_tracks(Path(tmp))
            state = {"attempts": {}}
            client = FakeClient({"11112222": playback_points(6)})
            result = asyncio.run(repair_mod.repair(tracks, self.args(), state,
                                                   client_factory=lambda: client,
                                                   clock=lambda: 0))
            rows = list(csv.DictReader((archive.tracks / "UR334-empty.csv").open(
                newline="", encoding="utf-8-sig")))
        self.assertEqual(result.repaired, 1)
        self.assertEqual(result.still_empty, 0)
        self.assertIn("2026-11", result.touched)
        self.assertNotEqual(rows[0]["Position"], "0.000000,0.000000")

    def test_a_playback_that_is_still_empty_is_remembered_not_rewritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            tracks = repair_mod.empty_tracks(Path(tmp))
            state = {"attempts": {}}
            client = FakeClient({"11112222": playback_points(4, zero=True)})
            result = asyncio.run(repair_mod.repair(tracks, self.args(), state,
                                                   client_factory=lambda: client,
                                                   clock=lambda: 0))
            positions = {row["Position"] for row in
                         csv.DictReader((archive.tracks / "UR334-empty.csv").open(
                             newline="", encoding="utf-8-sig"))}
        self.assertEqual(result.repaired, 0)
        self.assertEqual(result.still_empty, 1)
        self.assertEqual(state["attempts"]["11112222"]["tries"], 1)
        self.assertIn("no positions", state["attempts"]["11112222"]["last"])
        self.assertEqual(positions, {"0.000000,0.000000"})

    def test_the_clock_ends_the_run_and_says_what_is_left(self):
        with tempfile.TemporaryDirectory() as tmp:
            Archive(Path(tmp))
            tracks = repair_mod.empty_tracks(Path(tmp))
            client = FakeClient({})
            ticks = iter([0, 100, 100])     # deadline is 0.06 s; the first look is past it
            result = asyncio.run(repair_mod.repair(tracks, self.args(minutes=0.001),
                                                   {"attempts": {}},
                                                   client_factory=lambda: client,
                                                   clock=lambda: next(ticks)))
        self.assertEqual(result.left, len(tracks))

    def test_a_flight_with_no_id_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            Archive(Path(tmp))
            tracks = repair_mod.empty_tracks(Path(tmp))
            tracks[0].row = {}
            state = {"attempts": {}}
            result = asyncio.run(repair_mod.repair(tracks, self.args(), state,
                                                   client_factory=lambda: FakeClient({}),
                                                   clock=lambda: 0))
        self.assertEqual(result.repaired, 0)
        self.assertEqual(result.still_empty, 1)


class CommandTests(unittest.TestCase):
    def run_main(self, tmp, argv):
        with tempfile.TemporaryDirectory() as state_dir:
            return repair_mod.main(["--root", str(tmp),
                                    "--state", str(Path(state_dir) / "repair.json")] + argv)

    def test_a_plan_touches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            before = (archive.tracks / "UR334-empty.csv").read_bytes()
            self.assertEqual(self.run_main(tmp, ["--plan"]), 0)
            self.assertEqual(before, (archive.tracks / "UR334-empty.csv").read_bytes())

    def test_a_dry_run_touches_nothing_and_writes_no_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp))
            before = (archive.tracks / "UR334-empty.csv").read_bytes()
            with tempfile.TemporaryDirectory() as state_dir:
                path = Path(state_dir) / "repair.json"
                code = repair_mod.main(["--root", str(tmp), "--state", str(path), "--dry-run"])
                self.assertFalse(path.exists())
            self.assertEqual(code, 0)
            self.assertEqual(before, (archive.tracks / "UR334-empty.csv").read_bytes())

    def test_an_archive_that_is_whole_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tracks = root / "archive" / "2026-11" / "tracks"
            tracks.mkdir(parents=True)
            write_track_file(tracks / "UR720-good.csv", track_rows(4))
            self.assertEqual(self.run_main(tmp, []), 0)


if __name__ == "__main__":
    unittest.main()
