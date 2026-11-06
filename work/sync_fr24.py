#!/usr/bin/env python3
"""Harvest Uganda Airlines' flying from Flightradar24, day in and day out.

Run once a night, this keeps the archive current without anybody exporting a
file: it asks Flightradar24 what each airframe of the fleet has been doing since
the last run, downloads the playback of every flight it does not already hold,
files each track into the month it belongs to, rebuilds those months, and reports
whether anything looks wrong.

    python3 work/sync_fr24.py --days 3          # the nightly run
    python3 work/sync_fr24.py --days 3 --dry-run
    python3 work/sync_fr24.py --since 2026-06-01 --rebuild   # a backfill

Why by airframe rather than by airport: an enumeration built from Entebbe's
movements cannot see a sector that never touches Entebbe, which is exactly what
was missing — the Lusaka–Harare tag on the widebody's Harare run, the Zanzibar–
Kilimanjaro hop. Asking for the aircraft instead brings those sectors in as
first-class legs, so the rotations close on their own instead of needing a hop.

The ledger in ``state/ledger.csv`` remembers every flight id already looked at,
so a nightly run costs a handful of flight-list pages and only the playbacks that
are genuinely new. A flight with no track yet is retried for a day or two and then
left alone rather than asked for forever.

Exit status matters to whatever schedules it: 0 fine, 2 nothing to do, 3
suspicious (flights seen, none fetched), 4 too many failures. A silent job that
stops working is worse than one that fails loudly, so the sanity checks are the
point of the script as much as the fetching is.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fr24_tracks as ft  # noqa: E402
import fetch_fr24_tracks as fetch  # noqa: E402

UTC = timezone.utc
STATE_DIR = "state"
LEDGER_COLUMNS = ["flight_id_hex", "registration", "date", "month", "file", "status",
                  "checked_utc"]
# a flight whose playback is not there yet gets this many days of retries
RETRY_DAYS = 2
# playbacks are only worth asking for once the aircraft has had time to land
SETTLE = timedelta(minutes=20)
# a night's worth of fetching, to stay polite and inside a rate limit
MAX_FETCHES = 400

EXIT_OK, EXIT_SUSPICIOUS, EXIT_FLAKY = 0, 3, 4


# --------------------------------------------------------------------------- #
# state
# --------------------------------------------------------------------------- #

def state_paths(root: Path) -> tuple[Path, Path]:
    return root / STATE_DIR / "ledger.csv", root / STATE_DIR / "sync.json"


def load_ledger(root: Path) -> dict[str, dict]:
    path, _ = state_paths(root)
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {(row.get("flight_id_hex") or "").lower(): row for row in csv.DictReader(fh)}


def save_ledger(root: Path, ledger: dict[str, dict]) -> None:
    path, _ = state_paths(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for key in sorted(ledger):
            writer.writerow({column: ledger[key].get(column, "") for column in LEDGER_COLUMNS})


def read_state(root: Path) -> dict:
    _, path = state_paths(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_state(root: Path, state: dict) -> None:
    _, path = state_paths(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tracked_ids(root: Path) -> set[str]:
    """Flight ids already on disk, by the file name the tracks carry."""
    known: set[str] = set()
    for month_dir in sorted((root / "archive").glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]")):
        for path in (month_dir / "tracks").glob("*.csv"):
            stem = path.stem
            if "-" in stem:
                known.add(stem.rsplit("-", 1)[-1].lower())
    return known


# --------------------------------------------------------------------------- #
# what to ask for
# --------------------------------------------------------------------------- #

@dataclass
class Stats:
    window: tuple[datetime, datetime]
    airframes: list[str] = field(default_factory=list)
    seen: int = 0
    new: int = 0
    fetched: int = 0
    failed: int = 0
    months: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


def _airport_for_icao(icao: str):
    for airport in ft.load_airports():
        if airport.ident.upper() == (icao or "").upper():
            return airport
    return None


def leg_month(item: dict, departure: datetime) -> str:
    """The month a track belongs to: the month the leg departs in, local at origin.

    This is the builder's own rule — a flight logged under the date it left on,
    local time at the airport it left — so a track is never filed into a month the
    rebuild will then drop it from.
    """
    origin = _airport_for_icao(fetch._icao(item, "origin"))
    local = departure.astimezone(origin.tz if origin else ft.BASE_TZ)
    return f"{local:%Y-%m}"


def fleet_registrations(root: Path) -> list[str]:
    fleet = ft.load_fleet(root / "reference")
    return sorted({reg for reg in fleet if reg})


async def discover_airframes(client, start: datetime, end: datetime,
                             seed: list[str]) -> tuple[list[str], str]:
    """Registrations to ask about: the fleet on file, plus anything Entebbe saw.

    The airport list is the cheap way to notice a new airframe or a wet lease
    without anybody editing ``reference/fleet.csv``; when the endpoint is not
    available the seed list still covers the whole fleet.
    """
    found: set[str] = set(seed)
    note = ""
    try:
        result = await client.airport_list.fetch(
            airport="EBB", mode="departures", limit=100,
            timestamp=int(end.timestamp()))
        for item in fetch._data(result):
            registration = ((item.get("aircraft") or {}).get("registration") or "").strip()
            if registration:
                found.add(registration.upper())
        result = await client.airport_list.fetch(
            airport="EBB", mode="arrivals", limit=100,
            timestamp=int(end.timestamp()))
        for item in fetch._data(result):
            registration = ((item.get("aircraft") or {}).get("registration") or "").strip()
            if registration:
                found.add(registration.upper())
    except Exception as error:  # noqa: BLE001 - discovery is a convenience
        note = f"airport list unavailable ({type(error).__name__}), using the fleet file"
    newcomers = sorted(found - set(seed))
    if newcomers:
        note = f"{note}; new airframes seen at Entebbe: {', '.join(newcomers)}".lstrip("; ")
    return sorted(found), note


async def flights_since(client, registration: str, start: datetime, end: datetime,
                        pages: int, delay: int) -> list[dict]:
    """The airframe's flights with a departure inside the window."""
    found: list[dict] = []
    async for result in client.flight_list.fetch_all(
            reg=registration, timestamp=int(end.timestamp()), filter_by="historic",
            limit=100, max_pages=pages, delay=delay):
        page = fetch._data(result)
        if not page:
            break
        oldest = None
        for item in page:
            departure = fetch.departure_of(item)
            if departure is None:
                continue
            oldest = departure if oldest is None else min(oldest, departure)
            if start <= departure <= end:
                found.append(item)
        if oldest is not None and oldest < start - timedelta(hours=12):
            break
    return found


def already_known(item: dict, ledger: dict, tracked: set[str], now: datetime) -> bool:
    flight_id = str(fetch.flight_id_of(item) or "").lower()
    if not flight_id:
        return True
    if flight_id in tracked:
        return True
    entry = ledger.get(flight_id)
    if not entry:
        return False
    if entry.get("status") == "tracked":
        return True
    checked = fetch._parse(entry.get("checked_utc"))
    return bool(checked and (now - checked).days >= RETRY_DAYS)


# --------------------------------------------------------------------------- #
# one month's folder, kept in shape
# --------------------------------------------------------------------------- #

README_TEMPLATE = """# {month_label}

Uganda Airlines' {month_label} operation, as rebuilt from Flightradar24 tracks:
**{flights:,} flights**, **{hours} h {minutes:02d} min** airborne, **{km:,.0f} km**
flown.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | {window} |
| flights logged | {flights:,} |
| airborne | {hours} h {minutes:02d} min |
| distance flown | {km:,.0f} km (summed from the track positions, complete tracks only) |
| city pairs | {pairs} directional |
| rotations | {rotations} ({broken} with a sector still missing) |
| airframes | {airframes} |
| types | {types} |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | the raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, route, registration, aircraft, times, point count, checksum, and whether it came out of the enumeration or the API |
| `flights_{month}.csv` | one row per flight leg, with off/on times in UTC and local, airborne minutes, distance flown and the track behind it |
| `rotations_{month}.csv` | one row per airframe rotation: the airport chain, and any sector the record is missing |
| `aeroroutes_{month}.md` | the month's log in AeroRoutes notation, with a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

Regenerate the four derived files with:

```bash
python3 work/fr24_tracks.py --month {month}
```

## What the month looks like

*Drafted automatically when the month first appeared. Add the month's story here;
this section is not regenerated.*
"""

def month_numbers(root: Path, month: str) -> dict:
    """The figures the README and the index need, from the month's own files."""
    folder = root / "archive" / month
    flights = []
    with (folder / f"flights_{month}.csv").open(newline="", encoding="utf-8-sig") as fh:
        flights = list(csv.DictReader(fh))
    minutes = sum(int(row["airborne_min"] or 0) for row in flights)
    km = sum(float(row["distance_km"] or 0) for row in flights if row["track_complete"] == "yes")
    first = min(row["flight_date"] for row in flights)
    last = max(row["flight_date"] for row in flights)
    rotations = []
    path = folder / f"rotations_{month}.csv"
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as fh:
            rotations = list(csv.DictReader(fh))
    return {
        "month": month,
        "flights": len(flights),
        "minutes": minutes,
        "km": km,
        "first": first,
        "last": last,
        # city pairs are counted the way the log's summary counts them: a route
        # and its return leg are one pair
        "pairs": len({frozenset((row["origin"], row["destination"])) for row in flights}),
        "rotations": len(rotations),
        "broken": sum(1 for row in rotations if row["complete"] == "no"),
        "airframes": ", ".join(sorted({row["registration"] for row in flights if row["registration"]})),
        "types": ", ".join(sorted({row["aircraft_type"] for row in flights if row["aircraft_type"]})),
    }


def write_month_readme(root: Path, month: str) -> bool:
    """Draft a README for a month that has never had one. Never overwrites."""
    path = root / "archive" / month / "README.md"
    if path.exists():
        return False
    numbers = month_numbers(root, month)
    year, month_no = (int(part) for part in month.split("-"))
    first = datetime.strptime(numbers["first"], "%Y-%m-%d")
    last = datetime.strptime(numbers["last"], "%Y-%m-%d")
    names = ft.MONTH_NAMES
    window = (f"{first:%d}{names[first.month - 1]}{first:%y} – "
              f"{last:%d}{names[last.month - 1]}{last:%y}")
    if (last + timedelta(days=1)).month == last.month:
        window += f" (part month, to the {last.day}{_ordinal(last.day)})"
    path.write_text(README_TEMPLATE.format(
        month=month, month_label=f"{first:%B %Y}", window=window,
        flights=numbers["flights"], hours=numbers["minutes"] // 60,
        minutes=numbers["minutes"] % 60, km=numbers["km"], pairs=numbers["pairs"],
        rotations=numbers["rotations"], broken=numbers["broken"],
        airframes=numbers["airframes"] or "—", types=numbers["types"] or "—",
    ), encoding="utf-8")
    return True


INDEX_HEADER = ("| month | flights | airborne | km flown | city pairs | rotations | "
                "untracked hops | types | folder |")
INDEX_RULE = "|---|---|---|---|---|---|---|---|---|"


def update_index(root: Path) -> bool:
    """Regenerate the index table in archive/README.md from the months on disk.

    Only the table is touched: the prose above and below it is left exactly as it
    was, so the index stays current as months appear without anyone editing it.
    """
    path = root / "archive" / "README.md"
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        head_at = lines.index(INDEX_HEADER)
    except ValueError:
        return False
    # the table runs from the header to the first line that is not a table row
    end_at = head_at + 1
    while end_at < len(lines) and lines[end_at].startswith("|"):
        end_at += 1

    months = sorted(p.name for p in (root / "archive").glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]")
                    if (p / f"flights_{p.name}.csv").exists())
    rows = []
    totals = {"flights": 0, "minutes": 0, "km": 0.0, "rotations": 0, "hops": 0}
    for month in months:
        numbers = month_numbers(root, month)
        hops = _hop_count(root, month)
        totals["flights"] += numbers["flights"]
        totals["minutes"] += numbers["minutes"]
        totals["km"] += numbers["km"]
        totals["rotations"] += numbers["rotations"]
        totals["hops"] += hops
        rows.append("| " + " | ".join([
            _month_label(numbers),
            f"{numbers['flights']:,}",
            f"{numbers['minutes'] // 60:,} h {numbers['minutes'] % 60:02d} min",
            f"{numbers['km']:,.0f}",
            str(numbers["pairs"]),
            str(numbers["rotations"]),
            str(hops),
            numbers["types"],
            f"[`{month}/`]({month}/)",
        ]) + " |")
    total_row = ("| **total** | " + " | ".join([
        f"**{totals['flights']:,}**",
        f"**{totals['minutes'] // 60:,} h {totals['minutes'] % 60:02d} min**",
        f"**{totals['km']:,.0f}**", "—",
        f"**{totals['rotations']}**", f"**{totals['hops']}**", "—", "",
    ]) + "|")
    table = [INDEX_HEADER, INDEX_RULE] + rows + [total_row]
    path.write_text("\n".join(lines[:head_at] + table + lines[end_at:]) + "\n",
                    encoding="utf-8")
    return True


def _month_label(numbers: dict) -> str:
    first = datetime.strptime(numbers["first"], "%Y-%m-%d")
    last = datetime.strptime(numbers["last"], "%Y-%m-%d")
    label = f"{first:%B %Y}"
    if (last + timedelta(days=1)).month == last.month:
        label += f" (to the {last.day}{_ordinal(last.day)})"
    return label


def _hop_count(root: Path, month: str) -> int:
    path = root / "archive" / month / f"rotations_{month}.csv"
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return sum(len(row["untracked_hops"].split()) for row in csv.DictReader(fh))


def _ordinal(day: int) -> str:
    if 11 <= day % 100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #

async def gather(client, args, root: Path, stats: Stats) -> list[tuple[str, dict]]:
    ledger = load_ledger(root)
    known = tracked_ids(root)
    seed = fleet_registrations(root)
    stats.months = set()

    airframes, note = await discover_airframes(client, stats.window[0], stats.window[1], seed)
    stats.airframes = airframes
    if note:
        stats.notes.append(note)

    todo: list[tuple[str, dict]] = []
    for registration in airframes:
        items = await flights_since(client, registration, stats.window[0],
                                    stats.window[1], args.max_pages, args.delay)
        stats.seen += len(items)
        for item in items:
            if already_known(item, ledger, known, datetime.now(tz=UTC)):
                continue
            todo.append((registration, item))
        if args.pause:
            await asyncio.sleep(args.pause)

    # one playback each, oldest first so a cut-off run keeps the record in order
    todo.sort(key=lambda pair: fetch.departure_of(pair[1]) or datetime.max.replace(tzinfo=UTC))
    stats.new = len(todo)
    if args.limit:
        todo = todo[:args.limit]
    return todo


async def fetch_one(client, registration: str, item: dict, root: Path,
                    stats: Stats) -> dict | None:
    departure = fetch.departure_of(item)
    if departure is None:
        return None
    if departure > datetime.now(tz=UTC) - SETTLE:
        return None  # not flown, or not published yet
    flight_id = fetch.flight_id_of(item)
    result = await client.playback.fetch(flight_id, timestamp=int(departure.timestamp()))
    payload = (result.to_dict().get("result") or {}).get("response") or {}
    track = ((payload.get("data") or {}).get("flight") or {}).get("track") or []
    if not track:
        return None

    month = leg_month(item, departure)
    outdir = root / "archive" / month / "tracks"
    outdir.mkdir(parents=True, exist_ok=True)
    gap = fetch.Gap(origin=_icao_to_code(fetch._icao(item, "origin")),
                    destination=_icao_to_code(fetch._icao(item, "destination")),
                    registration=registration,
                    flight_number=fetch.number_of(item),
                    after=departure, before=departure)
    row = fetch.write_track(outdir, gap, item, result, track)
    stats.months.add(month)
    return row


def _icao_to_code(icao: str) -> str:
    for airport in ft.load_airports():
        if airport.ident.upper() == (icao or "").upper():
            return airport.code
    return icao or "ZZZZ"


async def run(client, args, root: Path) -> int:
    stats = Stats(window=window(args, root))
    print(f"window {stats.window[0]:%Y-%m-%d %H:%M}Z – {stats.window[1]:%Y-%m-%d %H:%M}Z")
    todo = await gather(client, args, root, stats)
    print(f"{len(stats.airframes)} airframes, {stats.seen} flights seen, "
          f"{stats.new} new to fetch")

    if args.dry_run:
        for registration, item in todo[:20]:
            print(f"  {fetch.departure_of(item):%Y-%m-%d %H:%M}Z {registration} "
                  f"{fetch.number_of(item)} {fetch._icao(item, 'origin')}-"
                  f"{fetch._icao(item, 'destination')}")
        if len(todo) > 20:
            print(f"  ... and {len(todo) - 20} more")
        return EXIT_OK

    ledger = load_ledger(root)
    rows_by_month: dict[str, list[dict]] = {}
    now = datetime.now(tz=UTC)
    for registration, item in todo:
        flight_id = str(fetch.flight_id_of(item) or "").lower()
        departure = fetch.departure_of(item)
        try:
            row = await fetch_one(client, registration, item, root, stats)
        except Exception as error:  # noqa: BLE001 - one flight must not stop the night
            stats.failed += 1
            stats.notes.append(f"{flight_id}: {type(error).__name__}: {error}")
            ledger[flight_id] = {
                "flight_id_hex": flight_id, "registration": registration,
                "date": f"{departure:%Y-%m-%d}" if departure else "",
                "month": leg_month(item, departure) if departure else "",
                "file": "", "status": "error",
                "checked_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            continue
        status = "tracked" if row else "no-track"
        ledger[flight_id] = {
            "flight_id_hex": flight_id, "registration": registration,
            "date": f"{departure:%Y-%m-%d}" if departure else "",
            "month": leg_month(item, departure) if departure else "",
            "file": (row or {}).get("file", ""), "status": status,
            "checked_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if row:
            stats.fetched += 1
            month = leg_month(item, departure)
            rows_by_month.setdefault(month, []).append(row)
            print(f"  {departure:%Y-%m-%d %H:%M}Z {registration} {row['number']} "
                  f"{row['from']}-{row['to']} -> archive/{month}/tracks/{row['file']}")
        if args.pause:
            await asyncio.sleep(args.pause)

    for month, rows in rows_by_month.items():
        fetch.append_manifest(root / "archive" / month / "tracks" / "manifest.csv", rows)
    save_ledger(root, ledger)
    return finish(args, root, stats)


def finish(args, root: Path, stats: Stats) -> int:
    for month in sorted(stats.months):
        if not args.no_rebuild:
            ft.main(["--month", month, "--outdir", str(root / "archive" / month)])
        if write_month_readme(root, month):
            print(f'drafted archive/{month}/README.md')
    if stats.months:
        update_index(root)
    write_state(root, {
        "last_run": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": [stamp.strftime("%Y-%m-%dT%H:%M:%SZ") for stamp in stats.window],
        "airframes": stats.airframes,
        "seen": stats.seen,
        "new": stats.new,
        "fetched": stats.fetched,
        "failed": stats.failed,
        "months": sorted(stats.months),
        "notes": stats.notes[-20:],
    })
    print(f"{stats.fetched} tracks fetched, {stats.failed} failures, "
          f"months touched: {', '.join(sorted(stats.months)) or 'none'}")
    for note in stats.notes[-5:]:
        print(f"  note: {note}", file=sys.stderr)

    if stats.failed and stats.failed > max(3, (stats.fetched + stats.failed) // 5):
        print(f"{stats.failed} of {stats.fetched + stats.failed} fetches failed",
              file=sys.stderr)
        return EXIT_FLAKY
    if stats.new and not stats.fetched and not stats.failed:
        print(f"suspicious: {stats.new} flights were new to the archive and none of "
              f"them produced a track — the API is answering, but with nothing usable",
              file=sys.stderr)
        return EXIT_SUSPICIOUS
    return EXIT_OK


def window(args, root: Path) -> tuple[datetime, datetime]:
    now = datetime.now(tz=UTC) - SETTLE
    if args.since:
        start = fetch._parse(args.since)
    else:
        start = None
        if not args.ignore_state:
            previous = read_state(root).get("window")
            if previous:
                try:
                    start = datetime.strptime(previous[1], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
                except (ValueError, IndexError):
                    start = None
        if start is None:
            start = now - timedelta(days=args.days)
    if start is None:
        raise SystemExit(f"could not read --since {args.since!r}; use YYYY-MM-DD")
    return start, now


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Harvest the fleet's flying from Flightradar24 into the archive.")
    parser.add_argument("--days", type=int, default=3,
                        help="how far back to look on a first run (default 3)")
    parser.add_argument("--since", default=None,
                        help="start of the window, YYYY-MM-DD or YYYY-MM-DD HH:MM")
    parser.add_argument("--ignore-state", action="store_true",
                        help="ignore the last run's end and use --days/--since")
    parser.add_argument("--dry-run", action="store_true", help="fetch nothing, list what is new")
    parser.add_argument("--no-rebuild", action="store_true",
                        help="write the tracks but do not rebuild the months")
    parser.add_argument("--root", default=None,
                        help="repository root (defaults to the one containing work/)")
    parser.add_argument("--limit", type=int, default=MAX_FETCHES,
                        help=f"most playbacks to fetch in one run (default {MAX_FETCHES})")
    parser.add_argument("--max-pages", type=int, default=5,
                        help="flight-list pages per airframe (100 flights a page)")
    parser.add_argument("--delay", type=int, default=2, help="seconds between flight-list pages")
    parser.add_argument("--pause", type=float, default=1.5,
                        help="seconds between requests, to stay inside the rate limit")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else ft.ROOT
    try:
        import fr24  # noqa: F401
    except ImportError:
        print('the Flightradar24 client is not installed: '
              'python3 -m pip install "fr24[curl]"', file=sys.stderr)
        return 1
    import os
    if not (os.environ.get("fr24_username") or os.environ.get("fr24_subscription_key")):
        print("no Flightradar24 credentials in the environment: set fr24_username and "
              "fr24_password (or fr24_subscription_key and fr24_token)", file=sys.stderr)
        return 1

    from fr24 import FR24

    async def go() -> int:
        async with FR24() as client:
            await client.login("from_env")
            return await run(client, args, root)

    return asyncio.run(go())


if __name__ == "__main__":
    raise SystemExit(main())
