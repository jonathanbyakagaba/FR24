#!/usr/bin/env python3
"""Close the archive's missing sectors, month after month, without being asked.

The nightly harvest keeps the *new* flying coming in. It cannot fix history: a
rotation that landed two months ago with a hole in the middle stays holed, and
nothing about tonight's flights makes it whole. This is the other half — a sweep
that walks every month in the archive, finds the sectors the rotation chains
prove but the record does not hold, and fetches them a few at a time.

    python3 work/sweep_gaps.py --plan              # the backlog, no network
    python3 work/sweep_gaps.py --budget 150        # fetch up to 150 sectors
    python3 work/sweep_gaps.py --month 2026-06 --budget 20
    python3 work/sweep_gaps.py --dry-run           # say what it would fetch

Three things make it safe to run every night:

* **A budget.** A sweep asks for a bounded number of sectors, so the job always
  finishes and the API is never hammered. Whatever is left waits for tomorrow.
* **A memory.** ``state/sweep.json`` counts the tries against each sector. One
  that Flightradar24 will not serve is parked after three attempts instead of
  being asked for forever, and the gap sheet says so rather than lying about it.
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
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fr24_tracks as ft  # noqa: E402
import fetch_fr24_tracks as fetch  # noqa: E402

STATE = ft.ROOT / "state" / "sweep.json"
DEFAULT_BUDGET = 100
DEFAULT_TRIES = 3

OPEN = "open"
PARKED = "parked"          # asked for, never served — stop asking
NO_ICAO = "no-icao"        # the sector cannot be queried without an ICAO code
OUT_OF_RANGE = "out-of-range"  # older than the history the subscription keeps
TOO_SMALL = "too-small"    # the hole is shorter than any flight

# every state in which a sector is still *missing* — out of reach is not closed
MISSING = (OPEN, PARKED, NO_ICAO, TOO_SMALL, OUT_OF_RANGE)

_REASONS = {
    PARKED: "not in the Flightradar24 record after {tries} tries",
    NO_ICAO: "no ICAO code for this airport pair",
    OUT_OF_RANGE: "older than the {days}-day history this plan keeps",
}

DEFAULT_HISTORY_DAYS = 7


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


def classify(entries: list[Entry], attempts: dict, max_tries: int,
             history_days: int = 0, now: datetime | None = None) -> list[Entry]:
    """Mark each sector open, parked, or impossible — and say how many tries."""
    cutoff = None
    if history_days:
        cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=history_days)
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
            gap.reason = _REASONS[OUT_OF_RANGE].format(days=history_days)
        elif entry.tries >= max_tries:
            entry.status = PARKED
            gap.reason = _REASONS[PARKED].format(tries=entry.tries)
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
              attempted: int = 0) -> str:
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
            f"{count(OUT_OF_RANGE)} beyond the plan's history, {closed} closed so far")
    if attempted:
        head += f"\n  fetched {fetched} of {attempted} asked for tonight"
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


async def fetch_plan(entries: list[Entry], args, state: dict) -> list[str]:
    """Ask Flightradar24 for each planned sector, and note what came back."""
    from fr24 import FR24

    touched: list[str] = []
    beyond: int = 0
    async with FR24() as client:
        await client.login("from_env")
        for entry in entries:
            if beyond >= 3:
                # the API has said "too old" three times running; everything
                # after this is older still, so stop asking and say so instead
                entry.status = OUT_OF_RANGE
                entry.gap.plausible = False
                entry.gap.reason = _REASONS[OUT_OF_RANGE].format(days="plan's")
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
            if "400" in outcome:
                beyond += 1
                entry.status = OUT_OF_RANGE
            else:
                beyond = 0
            record(state, entry, outcome)
            if row:
                touched.append(entry.month)
            await asyncio.sleep(args.pause)
    return touched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Close the sectors missing from every month of the archive.")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                        help=f"how many sectors to ask for tonight (default {DEFAULT_BUDGET})")
    parser.add_argument("--month", action="append", default=[],
                        help="restrict to a month (repeatable); default is all of them")
    parser.add_argument("--history-days", type=int,
                        default=int(os.environ.get("FR24_HISTORY_DAYS")
                                    or DEFAULT_HISTORY_DAYS),
                        help="how far back the subscription's record reaches "
                             "(Basic 7, Silver 90, Gold 365, Business 1095); "
                             "older sectors are marked, not asked for")
    parser.add_argument("--tries", type=int, default=DEFAULT_TRIES,
                        help=f"attempts before a sector is parked (default {DEFAULT_TRIES})")
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

    entries = classify(survey(months), state["attempts"], args.tries,
                   history_days=args.history_days)
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

    fetched = asyncio.run(fetch_plan(chosen, args, state))

    for month in sorted(set(fetched)):
        if args.no_rebuild:
            continue
        print(f"rebuilding {month}")
        ft.main(["--month", month, "--outdir", str(ft.ROOT / "archive" / month)])

    # the months that changed are re-read, so the sheets and the counts are true
    if fetched:
        touched = set(fetched)
        entries = [entry for entry in entries if entry.month not in touched]
        entries += classify(survey(sorted(touched)), state["attempts"], args.tries,
                             history_days=args.history_days)
        entries.sort(key=lambda entry: (entry.when, entry.month, entry.gap.sector))
        write_sheets(entries)

    save_state(entries, state, state_path, months)
    print(summarise(entries, state, fetched=len(fetched), attempted=len(chosen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
