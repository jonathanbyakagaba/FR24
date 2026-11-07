#!/usr/bin/env python3
"""Tests for work/sweep_gaps.py — closing the sectors missing from every month.

    python3 -m unittest discover -s tests -v

The sweep's jobs are planning, remembering and reporting; the fetching is a thin
loop over the same function the month builder already trusts. So these tests
build gaps by hand, hand them a made-up memory, and check what comes back. No
network, no Flightradar24 client, no archive.
"""

import argparse
import asyncio
import json
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "work"))

import fetch_fr24_tracks as fetch  # noqa: E402
import sweep_gaps as sweep  # noqa: E402

WHEN = datetime(2026, 6, 1, 10, 13, tzinfo=timezone.utc)


def gap(sector="LUN-HRE", when=WHEN, registration="5X-EQU", plausible=True,
        flight_number=""):
    origin, destination = sector.rsplit("-", 1)
    return fetch.Gap(origin=origin, destination=destination,
                     registration=registration, flight_number=flight_number,
                     after=when - timedelta(hours=1), before=when + timedelta(hours=2),
                     rotation_id=f"{registration}-{when:%Y%m%d}",
                     plausible=plausible,
                     reason="" if plausible else "hole too small to hold the sector")


def entry(month="2026-06", **kwargs):
    built = gap(**kwargs)
    return sweep.Entry(month=month, outdir=Path(tempfile.gettempdir()) / month,
                       gap=built, key=sweep.gap_key(month, built))


class SurveyTests(unittest.TestCase):
    def test_archive_months_are_read_oldest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("2026-09", "2026-06", "2026-11"):
                (root / "archive" / name).mkdir(parents=True)
            (root / "archive" / "README.md").write_text("index", encoding="utf-8")
            self.assertEqual(sweep.archive_months(root),
                             ["2026-06", "2026-09", "2026-11"])

    def test_an_empty_archive_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sweep.archive_months(Path(tmp)), [])

    def test_a_gap_key_names_one_sector_and_its_time(self):
        key = sweep.gap_key("2026-06", gap())
        self.assertEqual(key, "2026-06|LUN-HRE|2026-06-01T09:13|5X-EQU")

    def test_a_rebuilt_month_keeps_the_same_key(self):
        """The memory is only useful if the name survives a rebuild."""
        self.assertEqual(sweep.gap_key("2026-06", gap()),
                         sweep.gap_key("2026-06", gap()))


class ClassificationTests(unittest.TestCase):
    def test_a_never_tried_sector_is_open(self):
        entries = sweep.classify([entry()], {}, max_tries=3)
        self.assertEqual(entries[0].status, sweep.OPEN)
        self.assertEqual(entries[0].tries, 0)

    def test_a_sector_that_keeps_failing_is_parked(self):
        rows = [entry()]
        attempts = {rows[0].key: {"tries": 3}}
        entries = sweep.classify(rows, attempts, max_tries=3,
                                 now=WHEN + timedelta(days=1))
        self.assertEqual(entries[0].status, sweep.PARKED)
        self.assertIn("not in the Flightradar24 record after 3 tries", entries[0].gap.reason)
        self.assertFalse(entries[0].gap.plausible)

    def test_two_failures_are_not_yet_a_parking(self):
        rows = [entry()]
        entries = sweep.classify(rows, {rows[0].key: {"tries": 2}}, max_tries=3,
                                 now=WHEN + timedelta(days=1))
        self.assertEqual(entries[0].status, sweep.OPEN)

    def test_a_sector_whose_airport_has_no_icao_code_is_unqueryable(self):
        entries = sweep.classify([entry(sector="UG-0013-EBB")], {}, max_tries=3)
        self.assertEqual(entries[0].status, sweep.NO_ICAO)
        self.assertFalse(entries[0].gap.plausible)
        self.assertIn("no ICAO code", entries[0].gap.reason)

    def test_a_hole_too_short_to_hold_a_flight_stays_skipped(self):
        entries = sweep.classify([entry(plausible=False)], {}, max_tries=3)
        self.assertEqual(entries[0].status, sweep.TOO_SMALL)


class HistoryTests(unittest.TestCase):
    """A sector older than the plan's record is marked, never asked for."""

    def test_a_sector_beyond_the_history_window_is_out_of_range(self):
        now = WHEN + timedelta(days=30)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                 history_days=7, now=now)
        self.assertEqual(entries[0].status, sweep.OUT_OF_RANGE)
        self.assertIn("no longer reaches back this far", entries[0].gap.reason)
        self.assertFalse(entries[0].gap.plausible)

    def test_a_sector_inside_the_window_stays_open(self):
        now = WHEN + timedelta(days=3)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                 history_days=7, now=now)
        self.assertEqual(entries[0].status, sweep.OPEN)

    def test_no_window_configured_means_no_cutoff(self):
        now = WHEN + timedelta(days=365)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                 history_days=0, now=now)
        self.assertEqual(entries[0].status, sweep.OPEN)

    def test_an_unreachable_sector_is_never_planned(self):
        now = WHEN + timedelta(days=30)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                 history_days=7, now=now)
        self.assertEqual(sweep.plan(entries, 10), [])

    def test_out_of_reach_is_not_counted_as_closed(self):
        """It is still missing; the archive has not been made whole."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sweep.json"
            first = sweep.classify([entry(when=WHEN)], {}, max_tries=3)
            sweep.save_state(first, {"attempts": {}, "months": {}, "totals": {}},
                             path, months=["2026-06"])
            state = sweep.load_state(path)
            later = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                   history_days=7, now=WHEN + timedelta(days=30))
            sweep.save_state(later, state, path, months=["2026-06"])
            state = sweep.load_state(path)
        self.assertEqual(state["totals"]["out_of_range"], 1)
        self.assertEqual(state["totals"]["closed"], 0)

    def test_a_refusal_does_not_count_against_the_sector(self):
        """A 400 means 'too old for this plan', not 'this sector is bad'."""
        state = {"attempts": {}, "months": {}, "totals": {}}
        row = entry()
        sweep.record(state, row, "UnwrapError: HTTPStatusError('... status 400')")
        self.assertNotIn(row.key, state["attempts"])


class BacklogTests(unittest.TestCase):
    """Nothing is written off for being old: the sweep asks, then parks."""

    def test_the_default_assumes_no_horizon(self):
        self.assertEqual(sweep.DEFAULT_HISTORY_DAYS, 0)

    def test_a_june_sector_is_asked_for_months_later(self):
        """It may only be answerable inside seven days — but that is the record's
        answer to give, not ours to presume."""
        now = WHEN + timedelta(days=150)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3, now=now)
        self.assertEqual(entries[0].status, sweep.OPEN)
        self.assertEqual(len(sweep.plan(entries, 0)), 1)

    def test_a_sector_older_than_the_record_is_still_asked_once(self):
        now = WHEN + timedelta(days=150)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3, now=now,
                                 old_tries=1)
        self.assertEqual(entries[0].status, sweep.OPEN)
        self.assertEqual(entries[0].tries, 0)

    def test_an_old_sector_is_parked_after_that_one_ask(self):
        row = entry(when=WHEN)
        now = WHEN + timedelta(days=150)
        entries = sweep.classify([row], {row.key: {"tries": 1}}, max_tries=3, now=now)
        self.assertEqual(entries[0].status, sweep.PARKED)
        self.assertIn("older than the 7-day record", entries[0].gap.reason)
        self.assertFalse(entries[0].gap.plausible)

    def test_a_recent_sector_still_gets_three_tries(self):
        row = entry(when=WHEN)
        now = WHEN + timedelta(days=1)
        entries = sweep.classify([row], {row.key: {"tries": 1}}, max_tries=3, now=now)
        self.assertEqual(entries[0].status, sweep.OPEN)

    def test_a_cutoff_still_works_when_somebody_asks_for_one(self):
        now = WHEN + timedelta(days=150)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                 history_days=7, now=now)
        self.assertEqual(entries[0].status, sweep.OUT_OF_RANGE)
        self.assertEqual(sweep.plan(entries, 0), [])


class HorizonTests(unittest.TestCase):
    """A refusal is worth remembering — but only for as long as it is true."""

    def test_a_measured_horizon_takes_the_older_backlog_out_of_the_queue(self):
        horizon = WHEN + timedelta(days=30)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3,
                                 horizon=horizon, now=WHEN + timedelta(days=60))
        self.assertEqual(entries[0].status, sweep.OUT_OF_RANGE)
        self.assertIn("measured, not assumed", entries[0].gap.reason)
        self.assertEqual(sweep.plan(entries, 0), [])

    def test_a_sector_after_the_horizon_is_still_asked_for(self):
        horizon = WHEN - timedelta(days=30)
        entries = sweep.classify([entry(when=WHEN)], {}, max_tries=3, horizon=horizon)
        self.assertEqual(entries[0].status, sweep.OPEN)

    def test_a_fresh_horizon_is_trusted(self):
        state = {"reach": {"stop_before": "2026-06-15T00:00:00Z",
                           "checked": "2026-11-07T00:00:00Z"}}
        now = datetime(2026, 11, 10, tzinfo=timezone.utc)
        self.assertEqual(sweep.measured_reach(state, now=now),
                         datetime(2026, 6, 15, tzinfo=timezone.utc))

    def test_a_month_old_horizon_is_tested_again(self):
        """A plan can be bought. Nothing should have to be edited for that."""
        state = {"reach": {"stop_before": "2026-06-15T00:00:00Z",
                           "checked": "2026-09-01T00:00:00Z"}}
        now = datetime(2026, 11, 7, tzinfo=timezone.utc)
        self.assertIsNone(sweep.measured_reach(state, now=now))

    def test_no_horizon_measured_yet_means_ask(self):
        self.assertIsNone(sweep.measured_reach({"reach": {}}))
        self.assertIsNone(sweep.measured_reach({}))

    def test_the_summary_reports_what_was_measured(self):
        entries = sweep.classify([entry()], {}, max_tries=3)
        state = {"attempts": {}, "months": {}, "totals": {},
                 "reach": {"stop_before": "2026-06-15T00:00:00Z",
                           "oldest_served": "2026-07-02T09:00:00Z"}}
        text = sweep.summarise(entries, state)
        self.assertIn("served a sector as old as 2026-07-02", text)
        self.assertIn("stops before 2026-06-15", text)


class ClockTests(unittest.TestCase):
    """The night ends when the minutes are up, and says what it left behind."""

    def args(self, **kwargs):
        base = dict(minutes=1, beyond_stop=3, max_pages=1, delay=0, pause=0)
        base.update(kwargs)
        return argparse.Namespace(**base)

    def fake_client(self):
        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return False

            async def login(self, *_args, **_kwargs):
                return True
        return lambda: Client()

    def test_it_stops_at_the_deadline_and_counts_what_is_left(self):
        rows = sweep.classify([entry(when=WHEN + timedelta(hours=n)) for n in range(10)],
                              {}, max_tries=3, now=WHEN + timedelta(days=1))
        ticks = iter(range(0, 10_000, 30))       # 30 s a look: two fit in a minute

        async def never(*_args, **_kwargs):
            return None

        with mock.patch.object(sweep.fetch, "fetch_gap", never):
            swept = asyncio.run(sweep.fetch_plan(rows, self.args(), {"attempts": {}},
                                                 client_factory=self.fake_client(),
                                                 clock=lambda: next(ticks)))
        self.assertLess(swept.asked, len(rows))
        self.assertEqual(swept.asked + swept.left, len(rows))

    def test_three_too_old_answers_write_the_horizon_down(self):
        # newest first, as the sweep runs it: the refusal is what everything
        # older than it inherits
        rows = sweep.plan(sweep.classify(
            [entry(when=WHEN + timedelta(days=n)) for n in range(5)],
            {}, max_tries=3, now=WHEN + timedelta(days=1)), 0)

        async def too_old(*_args, **_kwargs):
            raise RuntimeError("HTTPStatusError('too old', status 400)")

        with mock.patch.object(sweep.fetch, "fetch_gap", too_old):
            swept = asyncio.run(sweep.fetch_plan(rows, self.args(minutes=0),
                                                 {"attempts": {}},
                                                 client_factory=self.fake_client(),
                                                 clock=lambda: 0))
        self.assertEqual(swept.asked, 3)
        self.assertEqual(swept.stop_before, rows[3].when)
        self.assertTrue(all(row.status == sweep.OUT_OF_RANGE for row in rows))

    def test_a_beyond_stop_of_zero_never_stops(self):
        rows = sweep.plan(sweep.classify(
            [entry(when=WHEN + timedelta(days=n)) for n in range(3)], {},
            max_tries=3, now=WHEN + timedelta(days=1)), 0)

        async def too_old(*_args, **_kwargs):
            raise RuntimeError("HTTPStatusError('too old', status 400)")

        with mock.patch.object(sweep.fetch, "fetch_gap", too_old):
            swept = asyncio.run(sweep.fetch_plan(rows, self.args(minutes=0, beyond_stop=0),
                                                 {"attempts": {}},
                                                 client_factory=self.fake_client(),
                                                 clock=lambda: 0))
        self.assertIsNone(swept.stop_before)
        self.assertEqual(swept.asked, 3)

    def test_no_minutes_means_no_deadline(self):
        rows = sweep.classify([entry(when=WHEN + timedelta(hours=n)) for n in range(4)],
                              {}, max_tries=3, now=WHEN + timedelta(days=1))

        async def never(*_args, **_kwargs):
            return None

        with mock.patch.object(sweep.fetch, "fetch_gap", never):
            swept = asyncio.run(sweep.fetch_plan(rows, self.args(minutes=0),
                                                 {"attempts": {}},
                                                 client_factory=self.fake_client(),
                                                 clock=lambda: 0))
        self.assertEqual(swept.asked, len(rows))


class PlanTests(unittest.TestCase):
    def test_the_budget_is_respected(self):
        entries = sweep.classify([entry(when=WHEN + timedelta(days=n)) for n in range(10)],
                                 {}, max_tries=3)
        self.assertEqual(len(sweep.plan(entries, 4)), 4)

    def test_a_budget_of_zero_means_all_of_them(self):
        entries = sweep.classify([entry(when=WHEN + timedelta(days=n)) for n in range(5)],
                                 {}, max_tries=3)
        self.assertEqual(len(sweep.plan(entries, 0)), 5)

    def test_the_newest_untried_sector_goes_first(self):
        """The record only reaches back so far: ask where an answer is possible."""
        early, late = entry(when=WHEN), entry(when=WHEN + timedelta(days=30))
        entries = sweep.classify([late, early], {}, max_tries=3)
        self.assertIs(sweep.plan(entries, 10)[0], late)

    def test_a_retried_sector_waits_behind_one_never_asked(self):
        tried, fresh = entry(when=WHEN), entry(when=WHEN + timedelta(days=5))
        attempts = {tried.key: {"tries": 1}}
        entries = sweep.classify([tried, fresh], attempts, max_tries=3)
        self.assertIs(sweep.plan(entries, 1)[0], fresh)

    def test_parked_and_impossible_sectors_are_never_asked_for(self):
        rows = [entry(plausible=False), entry(sector="UG-0013-EBB"),
                entry(when=WHEN + timedelta(days=1))]
        entries = sweep.classify(rows, {}, max_tries=3)
        self.assertEqual([row.status for row in sweep.plan(entries, 10)], [sweep.OPEN])


class MemoryTests(unittest.TestCase):
    def test_a_missing_state_file_is_an_empty_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = sweep.load_state(Path(tmp) / "absent.json")
        self.assertEqual(state["attempts"], {})

    def test_a_corrupt_state_file_does_not_stop_the_sweep(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sweep.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(sweep.load_state(path)["attempts"], {})

    def test_a_failure_counts_against_the_sector(self):
        state = {"attempts": {}, "months": {}, "totals": {}}
        row = entry()
        sweep.record(state, row, "left open — the record has no such flight")
        sweep.record(state, row, "left open — the record has no such flight")
        self.assertEqual(state["attempts"][row.key]["tries"], 2)
        self.assertIn("no such flight", state["attempts"][row.key]["last"])

    def test_a_fetch_forgets_the_sector(self):
        state = {"attempts": {}, "months": {}, "totals": {}}
        row = entry()
        sweep.record(state, row, "left open")
        sweep.record(state, row, "filled")
        self.assertNotIn(row.key, state["attempts"])

    def test_state_round_trips_and_remembers_the_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sweep.json"
            entries = sweep.classify([entry()], {}, max_tries=3)
            sweep.save_state(entries, {"attempts": {}, "months": {}, "totals": {}},
                             path, months=["2026-06"])
            state = sweep.load_state(path)
        self.assertEqual(state["months"]["2026-06"]["open"], 1)
        self.assertEqual(state["totals"]["open"], 1)
        self.assertEqual(state["months"]["2026-06"]["open_keys"],
                         ["2026-06|LUN-HRE|2026-06-01T09:13|5X-EQU"])

    def test_a_sector_that_stopped_being_missing_counts_as_closed(self):
        """Filled by the sweep, or made whole by a neighbouring track — either way."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sweep.json"
            filler, survivor = entry(), entry(when=WHEN + timedelta(days=7))
            first = sweep.classify([filler, survivor], {}, max_tries=3)
            sweep.save_state(first, {"attempts": {}, "months": {}, "totals": {}},
                             path, months=["2026-06"])
            state = sweep.load_state(path)
            second = sweep.classify([survivor], {}, max_tries=3)
            sweep.save_state(second, state, path, months=["2026-06"])
            state = sweep.load_state(path)
        self.assertEqual(state["months"]["2026-06"]["closed_since"], 1)
        self.assertEqual(state["totals"]["closed"], 1)


class ReportingTests(unittest.TestCase):
    def test_the_summary_counts_every_month(self):
        entries = sweep.classify(
            [entry(month="2026-06"), entry(month="2026-07", when=WHEN + timedelta(days=40))],
            {}, max_tries=3)
        text = sweep.summarise(entries, {"attempts": {}, "months": {}, "totals": {}})
        self.assertIn("2 open", text)
        self.assertIn("2026-06", text)
        self.assertIn("2026-07", text)

    def test_the_summary_says_what_tonight_managed(self):
        entries = sweep.classify([entry()], {}, max_tries=3)
        text = sweep.summarise(entries, {"attempts": {}, "months": {}, "totals": {}},
                               fetched=1, attempted=4)
        self.assertIn("fetched 1 of 4", text)

    def test_the_gap_sheet_states_why_a_sector_is_not_being_asked_for(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "2026-06"
            outdir.mkdir()
            rows = [entry(), entry(sector="UG-0013-EBB")]
            for row in rows:
                row.outdir = outdir
            entries = sweep.classify(rows, {}, max_tries=3)
            sweep.write_sheets(entries)
            text = (outdir / "gaps_2026-06.csv").read_text(encoding="utf-8")
        self.assertIn("fetchable", text)
        self.assertIn("no ICAO code", text)


if __name__ == "__main__":
    unittest.main()
