#!/usr/bin/env python3
"""Close the archive's missing sectors, month after month, without being asked.

The nightly harvest keeps the *new* flying coming in. It cannot fix history: a
rotation that landed two months ago with a hole in the middle stays holed, and
nothing about tonight's flights makes it whole. This is the other half — a sweep
that walks every month in the archive, finds the sectors the rotation chains
prove but the record does not hold, and fetches them a few at a time.

    python3 work/sweep_gaps.py --plan              # the backlog, no network
    python3 work/sweep_gaps.py --minutes 25        # ask for 25 minutes' worth
    python3 work/sweep_gaps.py --month 2026-06 --minutes 5
    python3 work/sweep_gaps.py --dry-run           # say what it would fetch

It sweeps the whole archive, back to the first month, and stops only when the
backlog is empty. Four things make that safe to run every night:

* **A clock, not a head-count.** A sweep keeps asking until its minutes are up,
  so the job always finishes inside its timeout and the API is never hammered.
  Whatever is left waits for tomorrow, and the summary says how much that is.
* **A memory.** ``state/sweep.json`` counts the tries against each sector. Sectors
  inside the record's seven-day window get three attempts; anything older gets
  one honest ask and is then parked, with the reason written into the gap sheet
  rather than a lie about the sector still being "open".
* **A reach, measured rather than assumed.** Nothing is written off in advance
  because a plan *might* only keep seven days. The sweep asks, records the oldest
  sector the record did serve, and only writes a horizon down after the API has
  refused several sectors in a row for being too old — then stops asking about
  anything older until that measurement is a month old and worth testing again.
* **Recomputation, not bookkeeping.** The backlog is derived from the tracks on
  disk every night, so a filled sector disappears from the list on its own, and a
  sector that only became visible once a neighbouring track arrived appears
  without anybody adding it.

Exit status: 0 done — fetched, or nothing left to fetch; 1 it could not start.
A sweep that finds the archive whole is not a failure, it is the point.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fr24_tracks as ft  # noqa: E402
import fetch_fr24_tracks as fetch  # noqa: E402

STATE = ft.ROOT / "state" / "sweep.json"
# no count cap by default: the clock is the budget, so a sweep never stops with
# something askable still sitting in the backlog
DEFAULT_BUDGET = 0
DEFAULT_MINUTES = 25        # what the nightly job can spare before it commits
DEFAULT_TRIES = 3           # inside the record's window
DEFAULT_OLD_TRIES = 1       # older than the window: one honest ask, then park

OPEN = "open"
PARKED = "parked"          # asked for, never served — stop asking
NO_ICAO = "no-icao"        # the sector cannot be queried without an ICAO code
OUT_OF_RANGE = "out-of-range"  # older than the history the subscription keeps
TOO_SMALL = "too-small"    # the hole is shorter than any flight

# every state in which a sector is still *missing* — out of reach is not closed
MISSING = (OPEN, PARKED, NO_ICAO, TOO_SMALL, OUT_OF_RANGE)

PARKED_OLD = "parked-old"   # a reason, not a status: asked once, too old to serve

_REASONS = {
    PARKED: "not in the Flightradar24 record after {tries} tries",
    PARKED_OLD: "older than the {days}-day record (asked {tries}x, no answer)",
    "measured": "the record stops before {date} (measured, not assumed)",
    NO_ICAO: "no ICAO code for this airport pair",
    OUT_OF_RANGE: "the record no longer reaches back this far",
}

# Swept by default: 0 means "assume no horizon and ask", because assuming one is
# how 199 June-to-October sectors came to be written off without ever asking.
DEFAULT_HISTORY_DAYS = 0
# What the record reliably keeps. This no longer gates anything — it only decides
# how many tries a sector is worth.
API_WINDOW_DAYS = 7
# How long a measured horizon is trusted before it is tested again, in case the
# subscription was upgraded underneath it.
REACH_RECHECK = timedelta(days=30)


@dataclass
class Entry:
    """One untracked sector in one month, and where it stands."""

    month: str
    outdir: Path
    gap: "fetch.Gap"
    key: str
    tries: int = 0
    status: str = OPEN
    outcome: str = field(default="", compare=False)

    @property
    def when(self) -> datetime:
        stamp = self.gap.planned or self.gap.after or self.gap.before
        return stamp or datetime.max.replace(tzinfo=timezone.utc)

    def describe(self) -> str:
        return f"{self.month} {self.gap.describe()}"


# --------------------------------------------------------------------------- #
# what is missing


def archive_months(root: Path | None = None) -> list[str]:
    """Every month folder in the archive, oldest first."""
    base = (root or ft.ROOT) / "archive"
    if not base.is_dir():
        return []
    return sorted(path.name for path in base.iterdir()
                  if path.is_dir() and len(path.name) == 7 and path.name[4] == "-")


def gap_key(month: str, gap: "fetch.Gap") -> str:
    """A stable name for one sector, so attempts survive a rebuilt month."""
    stamp = gap.planned or gap.after or gap.before
    clock = f"{stamp:%Y-%m-%dT%H:%M}" if stamp else "?"
    return f"{month}|{gap.sector}|{clock}|{gap.registration or gap.flight_number or '?'}"


def survey(months: list[str], root: Path | None = None) -> list[Entry]:
    """Read every month and return the sectors it cannot account for."""
    base = (root or ft.ROOT) / "archive"
    entries: list[Entry] = []
    for month in months:
        outdir = base / month
        if not (outdir / "tracks").is_dir():
            continue
        try:
            _legs, rotations = fetch.load_month(month, outdir, [])
        except Exception as error:  # noqa: BLE001 - one bad month must not stop the sweep
            print(f"{month}: could not read the month — {type(error).__name__}: {error}",
                  file=sys.stderr)
            continue
        for gap in fetch.gaps_from_rotations(rotations):
            entries.append(Entry(month=month, outdir=outdir, gap=gap,
                                 key=gap_key(month, gap)))
    entries.sort(key=lambda entry: (entry.when, entry.month, entry.gap.sector))
    return entries


def measured_reach(state: dict, now: datetime | None = None) -> datetime | None:
    """The oldest the record has been *shown* to reach, if measured recently.

    Nothing about a subscription is taken on trust in either direction: this is
    written only after the API has refused several sectors in a row for being too
    old, and it is thrown away after a month so an upgraded plan is noticed.
    """
    reach = state.get("reach") or {}
    stop, checked = reach.get("stop_before"), reach.get("checked")
    if not stop or not checked:
        return None
    try:
        stamp = datetime.strptime(stop, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        tested = datetime.strptime(checked, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    if (now or datetime.now(timezone.utc)) - tested > REACH_RECHECK:
        return None
    return stamp


def classify(entries: list[Entry], attempts: dict, max_tries: int,
             history_days: int = 0, now: datetime | None = None,
             old_tries: int = DEFAULT_OLD_TRIES,
             horizon: datetime | None = None) -> list[Entry]:
    """Mark each sector open, parked, or impossible — and say how many tries.

    ``history_days`` is an opt-in cut-off for a plan that really does stop short
    of the archive's own start; left at 0 the sweep asks about every sector the
    archive can see, which is the point. Either way a sector older than the
    record's window is worth fewer tries: one ask answers it for good.
    """
    stamp = now or datetime.now(timezone.utc)
    cutoff = stamp - timedelta(days=history_days) if history_days else None
    stale = stamp - timedelta(days=API_WINDOW_DAYS)
    for entry in entries:
        entry.tries = int((attempts.get(entry.key) or {}).get("tries") or 0)
        gap = entry.gap
        if not gap.plausible:
            entry.status = TOO_SMALL
            gap.reason = gap.reason or "the hole is shorter than the sector"
        elif not (fetch.icao_for(gap.origin) and fetch.icao_for(gap.destination)):
            entry.status = NO_ICAO
            gap.reason = _REASONS[NO_ICAO]
        elif cutoff and entry.when < cutoff:
            entry.status = OUT_OF_RANGE
            gap.reason = _REASONS[OUT_OF_RANGE]
        elif horizon and entry.when < horizon:
            entry.status = OUT_OF_RANGE
            gap.reason = _REASONS["measured"].format(
                date=horizon.strftime("%Y-%m-%d"))
        elif entry.tries >= (max_tries if entry.when >= stale else old_tries):
            entry.status = PARKED
            gap.reason = (_REASONS[PARKED].format(tries=entry.tries)
                          if entry.when >= stale
                          else _REASONS[PARKED_OLD].format(tries=entry.tries,
                                                           days=API_WINDOW_DAYS))
        else:
            entry.status = OPEN
        if entry.status != OPEN:
            gap.plausible = False
    return entries


def plan(entries: list[Entry], budget: int) -> list[Entry]:
    """The sectors to ask for tonight: never tried first, then *newest* first.

    Newest, because the record only reaches back so far — the older a hole is,
    the likelier it is already beyond the plan's history and the less a request
    can possibly return. Working from the oldest end burns the budget on the
    sectors that cannot be answered.
    """
    open_entries = [entry for entry in entries if entry.status == OPEN]
    open_entries.sort(key=lambda entry: (entry.tries, -_stamp(entry), entry.month,
                                         entry.gap.sector))
    return open_entries[:budget] if budget else open_entries


def _stamp(entry: Entry) -> float:
    """A sortable clock that does not overflow on a sector with no timestamp."""
    when = entry.when
    return when.timestamp() if when.year < 9000 else 0.0


# --------------------------------------------------------------------------- #
# state


def load_state(path: Path | None = None) -> dict:
    path = path or STATE
    if not path.exists():
        return {"attempts": {}, "months": {}, "totals": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"attempts": {}, "months": {}, "totals": {}}
    state.setdefault("attempts", {})
    state.setdefault("months", {})
    state.setdefault("totals", {})
    return state


def closed_since(entries: list[Entry], state: dict) -> dict[str, int]:
    """How many sectors each month has gained since the last sweep.

    A sector that is no longer a gap was either fetched or made whole by a
    neighbouring track arriving — either way it is no longer missing.
    """
    previous = (state.get("months") or {})
    now: dict[str, set[str]] = {}
    for entry in entries:
        if entry.status in MISSING:
            now.setdefault(entry.month, set()).add(entry.key)
    closed: dict[str, int] = {}
    for month, record in previous.items():
        before = set(record.get("open_keys") or [])
        closed[month] = len(before - now.get(month, set()))
    return closed


def save_state(entries: list[Entry], state: dict, path: Path | None = None,
               months: list[str] | None = None) -> dict:
    path = path or STATE
    closed = closed_since(entries, state)
    records: dict[str, dict] = {}
    for entry in entries:
        record = records.setdefault(entry.month, {"open": 0, "parked": 0, "keys": []})
        if entry.status == OPEN:
            record["open"] += 1
            record["keys"].append(entry.key)
        elif entry.status == PARKED:
            record["parked"] += 1
    for month in (months if months is not None
                  else sorted({entry.month for entry in entries})):
        record = records.setdefault(month, {"open": 0, "parked": 0, "keys": []})
        record["closed_since"] = (state.get("months", {}).get(month, {})
                                  .get("closed_total") or 0) + closed.get(month, 0)
        record["open_keys"] = sorted(record.pop("keys"))
        record["swept"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    totals = {
        "open": sum(1 for entry in entries if entry.status == OPEN),
        "parked": sum(1 for entry in entries if entry.status == PARKED),
        "closed": sum(record["closed_since"] for record in records.values()),
        "no_icao": sum(1 for entry in entries if entry.status == NO_ICAO),
        "out_of_range": sum(1 for entry in entries if entry.status == OUT_OF_RANGE),
        "too_small": sum(1 for entry in entries if entry.status == TOO_SMALL),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    state["months"] = records
    state["totals"] = totals
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def note_stop(state: dict, when: datetime) -> None:
    """Write down where the record stopped, and when that was tested."""
    reach = state.setdefault("reach", {})
    reach["stop_before"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    reach["checked"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def note_reach(state: dict, when: datetime) -> None:
    """Remember the oldest sector the record did serve: a horizon, measured.

    Presumed in advance it was seven days, and 199 sectors were written off
    unasked on the strength of that presumption. Measured, it is whatever the
    subscription actually answers, and the archive can say which it is.
    """
    reach = state.setdefault("reach", {})
    stamp = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    oldest = reach.get("oldest_served")
    if not oldest or stamp < oldest:
        reach["oldest_served"] = stamp
    reach["at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record(state: dict, entry: Entry, outcome: str) -> None:
    """Note what one attempt at one sector came to."""
    if outcome == "filled" or "400" in outcome:
        state["attempts"].pop(entry.key, None)
        return
    record_ = state["attempts"].setdefault(entry.key, {"tries": 0})
    record_["tries"] = int(record_.get("tries") or 0) + 1
    record_["last"] = outcome
    record_["at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# reporting


def summarise(entries: list[Entry], state: dict, fetched: int = 0,
              attempted: int = 0, left: int = 0) -> str:
    months: dict[str, list[Entry]] = {}
    for entry in entries:
        months.setdefault(entry.month, []).append(entry)
    lines = []
    for month in sorted(months):
        rows = months[month]
        open_ = sum(1 for row in rows if row.status == OPEN)
        parked = sum(1 for row in rows if row.status == PARKED)
        beyond = sum(1 for row in rows if row.status == OUT_OF_RANGE)
        closed = (state.get("months", {}).get(month, {}).get("closed_since") or 0)
        lines.append(f"  {month}   {open_:>3} open   {parked:>3} parked   "
                     f"{beyond:>3} out of reach   {closed:>3} closed so far")
    def count(status: str) -> int:
        return sum(1 for entry in entries if entry.status == status)

    closed = sum((state.get("months", {}).get(month, {}).get("closed_since") or 0)
                 for month in months)
    stamp = (state.get("totals") or {}).get("updated") or ""
    head = (f"gap sweep{' — ' + stamp if stamp else ''}\n"
            f"  {count(OPEN)} open, {count(PARKED)} parked, "
            f"{count(OUT_OF_RANGE)} beyond the record's reach, {closed} closed so far")
    if attempted:
        head += f"\n  fetched {fetched} of {attempted} asked for tonight"
    if left:
        head += f", {left} left for tomorrow"
    reach = (state.get("reach") or {}).get("oldest_served")
    if reach:
        head += f"\n  the record has served a sector as old as {reach}"
    stop = (state.get("reach") or {}).get("stop_before")
    if stop:
        head += f"\n  the record stops before {stop[:10]} — measured, not assumed"
    return head + "\n" + "\n".join(lines)


def write_sheets(entries: list[Entry]) -> list[Path]:
    """Refresh every month's gap sheet, with the statuses the sweep knows."""
    written: list[Path] = []
    for month in sorted({entry.month for entry in entries}):
        rows = [entry for entry in entries if entry.month == month]
        if not rows:
            continue
        path = rows[0].outdir / f"gaps_{month}.csv"
        fetch.write_gap_list(path, [entry.gap for entry in rows])
        written.append(path)
    return written


# --------------------------------------------------------------------------- #
# fetching


def _args(budget_args):
    return argparse.Namespace(max_pages=budget_args.max_pages,
                              delay=budget_args.delay,
                              pause=budget_args.pause)


@dataclass
class Swept:
    """What one night's asking came to."""

    touched: list[str] = field(default_factory=list)
    asked: int = 0
    left: int = 0
    oldest_served: datetime | None = None
    stop_before: datetime | None = None
    filled: int = 0


async def fetch_plan(entries: list[Entry], args, state: dict, *,
                     client_factory=None, clock=None) -> Swept:
    """Ask Flightradar24 for each planned sector, and note what came back.

    The clock, not a head-count, decides when to stop: whatever is left stays
    open for tomorrow instead of being quietly dropped.
    """
    clock = clock or time.monotonic
    if client_factory is None:
        from fr24 import FR24 as client_factory

    swept = Swept()
    deadline = (clock() + args.minutes * 60) if args.minutes else None
    beyond: int = 0
    async with client_factory() as client:
        await client.login("from_env")
        for index, entry in enumerate(entries):
            if deadline is not None and clock() >= deadline:
                swept.left = len(entries) - index
                print(f"out of time after {swept.asked} sectors — "
                      f"{swept.left} left for tomorrow", file=sys.stderr)
                break
            if args.beyond_stop and beyond >= args.beyond_stop:
                # the API has said "too old" this many times running; everything
                # after this is older still, so stop asking and write the horizon
                # down — measured, so tomorrow does not repeat the experiment
                if swept.stop_before is None:
                    swept.stop_before = entry.when
                    print(f"the record stops before {entry.when:%Y-%m-%d} — "
                          f"not asking about anything older", file=sys.stderr)
                entry.status = OUT_OF_RANGE
                entry.gap.plausible = False
                entry.gap.reason = _REASONS[OUT_OF_RANGE]
                continue
            try:
                row = await fetch.fetch_gap(client, entry.gap, entry.outdir / "tracks",
                                            _args(args))
            except Exception as error:  # noqa: BLE001 - one bad sector is not the sweep
                outcome = f"{type(error).__name__}: {error}"
                row = None
            else:
                outcome = "filled" if row else "left open — the record has no such flight"
            entry.outcome = outcome
            swept.asked += 1
            if "400" in outcome:
                beyond += 1
                entry.status = OUT_OF_RANGE
            else:
                beyond = 0
            record(state, entry, outcome)
            if row:
                swept.filled += 1
                swept.touched.append(entry.month)
                when = entry.when
                if when != datetime.max.replace(tzinfo=timezone.utc):
                    if swept.oldest_served is None or when < swept.oldest_served:
                        swept.oldest_served = when
            await asyncio.sleep(args.pause)
    return swept


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Close the sectors missing from every month of the archive.")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                        help="hard cap on sectors asked for tonight "
                             f"(default {DEFAULT_BUDGET} = no cap)")
    parser.add_argument("--minutes", type=float, default=DEFAULT_MINUTES,
                        help="wall-clock limit for the asking, in minutes "
                             f"(default {DEFAULT_MINUTES}; 0 = no limit)")
    parser.add_argument("--month", action="append", default=[],
                        help="restrict to a month (repeatable); default is all of them")
    parser.add_argument("--history-days", type=int,
                        default=int(os.environ.get("FR24_HISTORY_DAYS")
                                    or DEFAULT_HISTORY_DAYS),
                        help="opt-in cut-off: treat sectors older than this as "
                             "beyond the plan's history instead of asking for "
                             f"them (default {DEFAULT_HISTORY_DAYS} = ask about "
                             "everything back to the first month)")
    parser.add_argument("--tries", type=int, default=DEFAULT_TRIES,
                        help="attempts before a recent sector is parked "
                             f"(default {DEFAULT_TRIES})")
    parser.add_argument("--old-tries", type=int, default=DEFAULT_OLD_TRIES,
                        help="attempts before a sector older than the "
                             f"{API_WINDOW_DAYS}-day record is parked "
                             f"(default {DEFAULT_OLD_TRIES})")
    parser.add_argument("--beyond-stop", type=int, default=3,
                        help="stop asking after this many consecutive "
                             "'too old' answers (default 3; 0 = never stop)")
    parser.add_argument("--plan", action="store_true",
                        help="print the backlog and stop (no network, no credentials)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be asked for, fetch nothing")
    parser.add_argument("--no-rebuild", action="store_true",
                        help="write the tracks but do not rebuild the months")
    parser.add_argument("--state", default=str(STATE), help="path to state/sweep.json")
    parser.add_argument("--max-pages", type=int, default=3,
                        help="flight-list pages to read per window")
    parser.add_argument("--delay", type=int, default=2,
                        help="seconds between flight-list pages")
    parser.add_argument("--pause", type=float, default=1.5,
                        help="seconds between sectors")
    args = parser.parse_args(argv)

    months = args.month or archive_months()
    if not months:
        print("no months in the archive yet — nothing to sweep")
        return 0

    state_path = Path(args.state)
    state = load_state(state_path)

    horizon = measured_reach(state)
    entries = classify(survey(months), state["attempts"], args.tries,
                       history_days=args.history_days, old_tries=args.old_tries,
                       horizon=horizon)
    chosen = plan(entries, args.budget)

    if args.plan:
        print(summarise(entries, state))
        for entry in chosen[:40]:
            print("  next: " + entry.describe() + (f"  (tried {entry.tries})"
                                                   if entry.tries else ""))
        if len(chosen) > 40:
            print(f"  … and {len(chosen) - 40} more")
        return 0

    for path in write_sheets(entries):
        print(f"wrote {path.relative_to(ft.ROOT)}")
    save_state(entries, state, state_path, months)

    if not chosen:
        print(summarise(entries, state))
        print("nothing open — the archive is whole")
        return 0

    if args.dry_run:
        print(summarise(entries, state))
        print(f"dry run — would ask for {len(chosen)} sectors")
        for entry in chosen[:20]:
            print("  " + entry.describe())
        return 0

    try:
        import fr24  # noqa: F401
    except ImportError:
        print('the Flightradar24 client is not installed: '
              'python3 -m pip install "fr24[curl]"', file=sys.stderr)
        return 1
    if not (__import__("os").environ.get("fr24_username")
            or __import__("os").environ.get("fr24_subscription_key")):
        print("no Flightradar24 credentials in the environment", file=sys.stderr)
        return 1

    swept = asyncio.run(fetch_plan(chosen, args, state))
    fetched = swept.touched
    if swept.oldest_served is not None:
        note_reach(state, swept.oldest_served)
    if swept.stop_before is not None:
        note_stop(state, swept.stop_before)

    for month in sorted(set(fetched)):
        if args.no_rebuild:
            continue
        print(f"rebuilding {month}")
        ft.main(["--month", month, "--outdir", str(ft.ROOT / "archive" / month)])

    # the months that changed are re-read, so the sheets and the counts are true
    if fetched:
        touched = set(fetched)
        entries = [entry for entry in entries if entry.month not in touched]
        entries += survey(sorted(touched))
    # and everything is re-classified against what tonight's answers were, so a
    # sector asked for and refused is parked now rather than a night late
    entries.sort(key=lambda entry: (entry.when, entry.month, entry.gap.sector))
    entries = classify(entries, state["attempts"], args.tries,
                       history_days=args.history_days, old_tries=args.old_tries,
                       horizon=measured_reach(state))
    write_sheets(entries)

    save_state(entries, state, state_path, months)
    print(summarise(entries, state, fetched=len(fetched), attempted=swept.asked,
                    left=swept.left))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
