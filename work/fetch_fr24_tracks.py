#!/usr/bin/env python3
"""Fetch the sectors missing from the archive, straight from Flightradar24.

Two kinds of hole are worth chasing, and both break a rotation in two:

* a **tag sector** — the aircraft lands at Lusaka and is next seen at Harare, so
  it must have flown Lusaka–Harare on the widebody's Harare run, or Zanzibar–
  Kilimanjaro on the Zanzibar run, and the movement enumeration never caught it;
* a **missing flight** — a numbered service the board scheduled and the
  enumeration skipped altogether (``UR120 EBB–JUB`` on a day the log has no such
  leg).

`work/fr24_tracks.py` already chains each airframe's legs and brackets the
airport that is only reachable through a hop, ``EBB–HRE–[LUN]–EBB``. This script
goes and fetches the missing sector with the
[`fr24`](https://github.com/abc8747/fr24) client and drops its track into the
month beside the others; rebuild the month and the rotation reads end to end.

List what is missing (no network, no credentials):

    python3 work/fetch_fr24_tracks.py --month 2026-09 --gaps-only

Say what would be asked of Flightradar24, without asking (no network):

    python3 work/fetch_fr24_tracks.py --month 2026-09 --dry-run

Fetch it (needs credentials, see below):

    python3 work/fetch_fr24_tracks.py --month 2026-09

Work a list of specific flights instead of the detected hops — the gap sheet a
reconciliation produces, with ``Flight``, ``Sector``, ``Tail``, ``Date`` and
``Planned_STD`` columns, is read as it stands:

    python3 work/fetch_fr24_tracks.py --month 2026-09 --worklist "FR24 gap legs.csv"

Credentials are the client's own: ``fr24_username`` / ``fr24_password``, or
``fr24_subscription_key`` / ``fr24_token``, in the environment or in
``~/.config/fr24/fr24.conf`` (``fr24 auth create``). Install the client with an
HTTP backend — the JSON endpoints need it:

    python3 -m pip install "fr24[curl]"

A fetched track is written in the same column layout as the rest of the folder
and its row goes into ``tracks/manifest.csv`` with ``source = fr24-api``, so a
sector recovered from the API is always distinguishable from one that came out
of the enumeration.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fr24_tracks as ft  # noqa: E402  (sibling module)

# the archive's track layout, with the registration kept on the file itself so a
# fetched track can be rebuilt into a leg without leaning on the manifest
TRACK_COLUMNS = ["Timestamp", "UTC", "Callsign", "Registration", "Position",
                 "Altitude", "Speed", "Direction"]
MANIFEST_COLUMNS = ["file", "flight_id_hex", "number", "callsign", "date", "from", "to",
                    "registration", "aircraft", "atd_utc", "ata_utc", "std_utc", "sta_utc",
                    "track_points", "sha256", "source"]
API_SOURCE = "fr24-api"
ENUMERATION_SOURCE = "ebbs-fr24"

GAP_COLUMNS = ["date", "sector", "registration", "aircraft_type", "flight_number",
               "after_utc", "before_utc", "hole_min", "rotation_id",
               "neighbour_flights", "status"]

# how far either side of a planned departure time a flight will be looked for
WORKLIST_SLACK = timedelta(hours=3)


# --------------------------------------------------------------------------- #
# the holes
# --------------------------------------------------------------------------- #

@dataclass
class Gap:
    """One sector worth fetching, and the window it has to fit in."""

    origin: str
    destination: str
    registration: str = ""
    flight_number: str = ""
    aircraft_type: str = ""
    after: datetime | None = None      # wheels down of the leg before the hop
    before: datetime | None = None     # wheels up of the leg after it
    planned: datetime | None = None    # planned departure, when the list gives one
    rotation_id: str = ""
    neighbours: str = ""
    plausible: bool = True
    reason: str = ""

    @property
    def sector(self) -> str:
        return f"{self.origin}-{self.destination}"

    @property
    def day(self) -> str:
        stamp = self.planned or self.after or self.before
        return f"{stamp.astimezone(ft.BASE_TZ) - ft.SERVICE_DAY_SHIFT:%Y-%m-%d}" if stamp else ""

    def windows(self) -> list[tuple[datetime, datetime]]:
        """Where to look: the hole itself first, then the whole day around it."""
        found: list[tuple[datetime, datetime]] = []
        if self.after and self.before:
            found.append((self.after - timedelta(minutes=20),
                          self.before + timedelta(minutes=10)))
        if self.planned:
            found.append((self.planned - WORKLIST_SLACK, self.planned + WORKLIST_SLACK))
        stamp = self.planned or self.after or self.before
        if stamp:
            start = datetime.combine(stamp.date(), datetime.min.time(), tzinfo=timezone.utc)
            day = (start, start + timedelta(days=1, hours=6))
            if all(day != window for window in found):
                found.append(day)
        return found

    def describe(self) -> str:
        when = self.planned or self.after
        clock = f"{when:%Y-%m-%d %H:%M}Z" if when else "?"
        parts = [clock, self.sector, self.registration or self.flight_number or "?"]
        return " ".join(part for part in parts if part)


def gaps_from_rotations(rotations: list[ft.Rotation]) -> list[Gap]:
    """The hops the rotation chain proves but the record does not hold."""
    gaps: list[Gap] = []
    for rotation in rotations:
        for hop in rotation.hops:
            gaps.append(Gap(
                origin=hop.origin,
                destination=hop.destination,
                registration=rotation.key,
                aircraft_type=rotation.type,
                after=hop.after,
                before=hop.before,
                rotation_id=rotation.id,
                neighbours=rotation.flight_numbers,
                plausible=hop.plausible,
                reason=("hole too small to hold the sector" if not hop.plausible else ""),
            ))
    gaps.sort(key=lambda gap: (gap.after or datetime.min.replace(tzinfo=timezone.utc)))
    return gaps


def write_gap_list(path: Path, gaps: list[Gap]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(GAP_COLUMNS)
        for gap in gaps:
            hole = int((gap.before - gap.after).total_seconds() // 60) if gap.after and gap.before else ""
            writer.writerow([
                gap.day, gap.sector, gap.registration, gap.aircraft_type,
                gap.flight_number,
                gap.after.strftime("%Y-%m-%dT%H:%M:%SZ") if gap.after else "",
                gap.before.strftime("%Y-%m-%dT%H:%M:%SZ") if gap.before else "",
                hole, gap.rotation_id, gap.neighbours,
                "fetchable" if gap.plausible else f"skipped ({gap.reason})",
            ])


def _field(row: dict, *names: str) -> str:
    lowered = {key.lower().strip(): (value or "").strip() for key, value in row.items()}
    for name in names:
        if lowered.get(name.lower()):
            return lowered[name.lower()]
    return ""


def _valid_sector(value: str) -> bool:
    value = (value or "").upper().replace(" ", "")
    return bool(re.fullmatch(r"[A-Z0-9]{3,4}-[A-Z0-9]{3,4}", value))


def _aligned(header: list[str], values: list[str]) -> dict:
    """Line a data row up with its header.

    Gap sheets are often hand-maintained, and a column can go missing from the
    rows while the header keeps it — every value after it then sits under the
    wrong name. Where that has happened, the alignment that makes ``Sector`` read
    as a city pair is the right one.
    """
    row = dict(zip(header, values))
    if _valid_sector(row.get("Sector", "")):
        return row
    for drop in range(len(header)):
        trimmed = header[:drop] + header[drop + 1:]
        candidate = dict(zip(trimmed, values))
        if _valid_sector(candidate.get("Sector", "")):
            return candidate
    return row


def read_gap_list(path: Path) -> list[Gap]:
    """Read a gap sheet: this tool's own, or a reconciliation worklist.

    Recognised per row: ``Sector`` (``EBB-JUB``), ``Tail``/``Registration``,
    ``Flight``, ``Date``, and either explicit ``after_utc``/``before_utc`` bounds
    or a ``Planned_STD`` to search around. Rows that only ask for a log line to be
    rebuilt from a track already on disk are left alone — there is nothing to
    fetch for those.
    """
    gaps: list[Gap] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        try:
            header = [name.strip() for name in next(reader)]
        except StopIteration:
            return gaps
        for values in reader:
            if not any(values):
                continue
            row = _aligned(header, values)
            sector = _field(row, "sector").upper().replace(" ", "")
            if not _valid_sector(sector):
                continue
            action = _field(row, "action", "leg_gap", "status").lower()
            if "track in the archive" in action or "rebuild the log row" in action:
                continue
            origin, destination = sector.split("-", 1)
            tail = _field(row, "tail", "registration", "aircraft")
            if tail.upper() in ("TBN", "UNKNOWN"):
                tail = ""
            planned = _parse(_field(row, "planned_std", "std", "std_utc"))
            after = _parse(_field(row, "after_utc"))
            before = _parse(_field(row, "before_utc"))
            if planned is None:
                planned = _parse(_field(row, "date"))
            gaps.append(Gap(
                origin=origin, destination=destination,
                registration=tail.upper(),
                flight_number=_field(row, "flight", "flight_number", "flight_no").upper(),
                aircraft_type=_field(row, "aircraft_type").upper(),
                after=after, before=before, planned=planned,
                rotation_id=_field(row, "rotation_id"),
                neighbours=_field(row, "neighbour_flights", "note"),
                plausible="skipped" not in action,
                reason=_field(row, "status"),
            ))
    return gaps


def _parse(value: str | None) -> datetime | None:
    """A timestamp in the several shapes these sheets are written in.

    A bare local time (``2026-09-01 11:00``) is read on the base's clock, since
    that is what a movement board prints.
    """
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M"):
        try:
            stamp = datetime.strptime(value, fmt)
        except ValueError:
            continue
        if fmt.endswith("Z"):
            return stamp.replace(tzinfo=timezone.utc)
        return stamp.replace(tzinfo=ft.BASE_TZ).astimezone(timezone.utc)
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# talking to Flightradar24
# --------------------------------------------------------------------------- #

def icao_for(code: str) -> str | None:
    """The ICAO ident for one of the archive's airports."""
    for airport in ft.load_airports():
        if airport.code == code:
            ident = airport.ident.upper()
            if len(ident) == 4 and ident.isalpha():
                return ident
    return None


def _icao(item: dict, side: str) -> str:
    airport = (item.get("airport") or {}).get(side) or {}
    code = airport.get("code") or {}
    return str(code.get("icao") or code.get("iata") or "").upper()


def _epoch(value) -> datetime | None:
    if value in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _time(item: dict, kind: str, side: str) -> datetime | None:
    node = ((item.get("time") or {}).get(kind) or {})
    return _epoch(node.get(side))


def departure_of(item: dict) -> datetime | None:
    return _time(item, "real", "departure") or _time(item, "scheduled", "departure")


def number_of(item: dict) -> str:
    identification = item.get("identification") or {}
    number = identification.get("number") or {}
    return str(number.get("default") or identification.get("callsign") or "").upper().replace(" ", "")


def flight_id_of(item: dict):
    identification = item.get("identification") or {}
    return identification.get("id") or identification.get("row")


def _data(result) -> list[dict]:
    payload = (result.to_dict().get("result") or {}).get("response") or {}
    return payload.get("data") or []


async def flights_in(client, gap: Gap, window: tuple[datetime, datetime],
                     max_pages: int, delay: int) -> list[dict]:
    """Every flight the client will show inside ``window``, matched or not."""
    start, end = window
    query = {}
    if gap.flight_number:
        query = {"flight": gap.flight_number}
    elif gap.registration:
        query = {"reg": gap.registration}
    if not query:
        return []

    found: list[dict] = []
    async for result in client.flight_list.fetch_all(
            timestamp=int(end.timestamp()), filter_by="historic", limit=100,
            max_pages=max_pages, delay=delay, **query):
        page = _data(result)
        if not page:
            break
        oldest = None
        for item in page:
            departure = departure_of(item)
            if departure is None:
                continue
            oldest = departure if oldest is None else min(oldest, departure)
            if start <= departure <= end:
                found.append(item)
        # the list runs backwards in time: past the window, stop reading
        if oldest is not None and oldest < start - timedelta(hours=18):
            break
    return found


def pick(items: list[dict], gap: Gap, from_icao: str | None,
         to_icao: str | None) -> dict | None:
    """The one flight in the list that is this sector, or nothing.

    The airframe can pass the same pair four times a day (Entebbe–Nairobi), so
    the time decides when there is more than one; the route and the flight
    number decide which of the day's flights it is when the sheet names them.
    """
    target = gap.planned or gap.after
    best, best_skew = None, None
    for item in items:
        if from_icao and _icao(item, "origin") not in ("", from_icao):
            continue
        if to_icao and _icao(item, "destination") not in ("", to_icao):
            continue
        if gap.flight_number and number_of(item) not in ("", gap.flight_number):
            continue
        departure = departure_of(item)
        if departure is None:
            continue
        skew = abs((departure - target).total_seconds()) if target else 0.0
        if best_skew is None or skew < best_skew:
            best, best_skew = item, skew
    return best


async def fetch_gap(client, gap: Gap, outdir: Path, args) -> dict | None:
    """Resolve one gap to a track file. Returns its manifest row, or None."""
    from_icao, to_icao = icao_for(gap.origin), icao_for(gap.destination)
    if not from_icao or not to_icao:
        print(f"  {gap.describe()}: {gap.origin} or {gap.destination} has no ICAO code "
              f"in reference/airports.csv — skipped", file=sys.stderr)
        return None

    item = None
    seen = 0
    for window in gap.windows():
        items = await flights_in(client, gap, window, args.max_pages, args.delay)
        seen += len(items)
        item = pick(items, gap, from_icao, to_icao)
        if item is not None:
            break
    if item is None:
        print(f"  {gap.describe()}: no {from_icao}-{to_icao} flight for "
              f"{gap.registration or gap.flight_number} in the record "
              f"({seen} flights read) — left open", file=sys.stderr)
        return None

    departure = departure_of(item)
    flight_id = flight_id_of(item)
    result = await client.playback.fetch(flight_id, timestamp=int(departure.timestamp()))
    payload = (result.to_dict().get("result") or {}).get("response") or {}
    track = ((payload.get("data") or {}).get("flight") or {}).get("track") or []
    if not track:
        print(f"  {gap.describe()}: flight {flight_id} has no playback track — left open",
              file=sys.stderr)
        return None

    row = write_track(outdir, gap, item, result, track)
    print(f"  {gap.describe()}: fetched {row['file']} "
          f"({row['track_points']} points, {row['atd_utc']} – {row['ata_utc']})")
    return row


def write_track(outdir: Path, gap: Gap, item: dict, result, track: list[dict]) -> dict:
    """Write one playback as an archive track, and return its manifest row."""
    try:
        metadata = result.metadata()
    except Exception:  # noqa: BLE001 - metadata is a nicety, the track is the point
        metadata = {}
    hex_id = str(metadata.get("flight_id") or flight_id_of(item) or "").lower()
    number = str(metadata.get("flight_number") or number_of(item) or "").upper().replace(" ", "")
    callsign = str(metadata.get("callsign") or number or gap.registration or "UNKNOWN")
    registration = str(metadata.get("registration") or gap.registration or "")
    name = f"{(number or callsign).replace(' ', '')}-{hex_id[-8:] or 'fetched'}.csv"
    path = outdir / name

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(TRACK_COLUMNS)
        for point in track:
            stamp = int(point.get("timestamp") or 0)
            position = point.get("position") or {}
            writer.writerow([
                stamp,
                datetime.fromtimestamp(stamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                callsign,
                registration,
                f"{float(position.get('latitude', 0)):.6f},{float(position.get('longitude', 0)):.6f}",
                int((point.get("altitude") or {}).get("feet") or 0),
                int((point.get("speed") or {}).get("kts") or 0),
                int(point.get("heading") or 0),
            ])

    def stamp_of(value: datetime | None) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else ""

    atd = _time(item, "real", "departure")
    ata = _time(item, "real", "arrival")
    return {
        "file": name,
        "flight_id_hex": hex_id,
        "number": number,
        "callsign": callsign,
        "date": f"{atd or gap.planned or gap.after:%Y-%m-%d}" if (atd or gap.planned or gap.after) else gap.day,
        "from": metadata.get("origin") or gap.origin,
        "to": metadata.get("destination") or gap.destination,
        "registration": metadata.get("registration") or gap.registration,
        "aircraft": metadata.get("model_code") or gap.aircraft_type,
        "atd_utc": stamp_of(atd),
        "ata_utc": stamp_of(ata),
        "std_utc": stamp_of(_time(item, "scheduled", "departure")),
        "sta_utc": stamp_of(_time(item, "scheduled", "arrival")),
        "track_points": len(track),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source": API_SOURCE,
    }


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #

def append_manifest(path: Path, rows: list[dict]) -> None:
    """Add fetched tracks to the month's manifest, one row per file.

    The manifest gains a ``source`` column the first time a track is fetched from
    the API: every row already there came out of the movement enumeration, and
    the difference should stay visible.
    """
    if not rows:
        return
    existing: list[dict] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as fh:
            existing = list(csv.DictReader(fh))
    for row in existing:
        row["source"] = (row.get("source") or "").strip() or ENUMERATION_SOURCE
    known = {row.get("file") for row in existing}
    existing.extend(row for row in rows if row["file"] not in known)
    existing.sort(key=lambda row: (row.get("date") or "", row.get("file") or ""))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in existing:
            writer.writerow({key: row.get(key, "") for key in MANIFEST_COLUMNS})


def load_month(month: str, outdir: Path, explicit: list[str]):
    """The month's legs and rotations, exactly as the builder sees them."""
    files = [path for path in ft.collect_tracks(outdir, month, explicit) if path.exists()]
    airports = ft.load_airports()
    fleet = ft.load_fleet()
    manifest = ft.load_manifest(outdir / "tracks" / "manifest.csv")
    legs: list[ft.Leg] = []
    for path in files:
        points = ft.read_export(path)
        if not points:
            continue
        built = ft.build_legs(points, airports, fleet,
                              meta=manifest.get(path.name, {}), source=path.name)
        legs.extend(leg for leg in built
                    if leg.local_departure and f"{leg.local_departure:%Y-%m}" == month)
    legs.sort(key=lambda leg: leg.takeoff)
    return legs, ft.build_rotations(legs)


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

async def run(client, gaps: list[Gap], outdir: Path, args) -> list[dict]:
    fetched: list[dict] = []
    for gap in gaps:
        if not gap.plausible:
            print(f"  {gap.describe()}: skipped — {gap.reason or 'not fetchable'}",
                  file=sys.stderr)
            continue
        try:
            row = await fetch_gap(client, gap, outdir, args)
        except Exception as error:  # noqa: BLE001 - one bad gap must not stop the run
            print(f"  {gap.describe()}: {type(error).__name__}: {error}", file=sys.stderr)
            continue
        if row:
            fetched.append(row)
        await asyncio.sleep(args.pause)
    return fetched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch the sectors missing from the archive, from Flightradar24.")
    parser.add_argument("--month", required=True, help="YYYY-MM, e.g. 2026-09")
    parser.add_argument("--gaps-only", action="store_true",
                        help="write the month's gap list and stop (no network)")
    parser.add_argument("--dry-run", action="store_true",
                        help="say what would be asked of Flightradar24, fetch nothing")
    parser.add_argument("--worklist", default=None,
                        help="fetch from a gap sheet instead of the detected hops")
    parser.add_argument("--track", action="append", default=[],
                        help="track file, folder or glob, as the month builder takes them")
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after this many gaps (0 = all)")
    parser.add_argument("--max-pages", type=int, default=3,
                        help="flight-list pages to read per window (100 flights a page)")
    parser.add_argument("--delay", type=int, default=2,
                        help="seconds between flight-list pages")
    parser.add_argument("--pause", type=float, default=1.5,
                        help="seconds between gaps, to stay inside the rate limit")
    args = parser.parse_args(argv)

    month = args.month
    datetime.strptime(month, "%Y-%m")  # validate
    outdir = ft.ROOT / "archive" / month
    if not (outdir / "tracks").is_dir():
        print(f"{outdir}/tracks does not exist — build the month first", file=sys.stderr)
        return 1

    if args.worklist:
        gaps = read_gap_list(Path(args.worklist))
        print(f"worklist {Path(args.worklist).name}: {len(gaps)} sectors to fetch")
    else:
        legs, rotations = load_month(month, outdir, args.track)
        gaps = gaps_from_rotations(rotations)
        print(f"{month}: {len(legs):,} legs in {len(rotations)} rotations, "
              f"{len(gaps)} untracked hops "
              f"({sum(1 for gap in gaps if gap.plausible)} fetchable)")
        if args.gaps_only:
            path = outdir / f"gaps_{month}.csv"
            write_gap_list(path, gaps)
            for gap in gaps:
                print("  " + gap.describe() + ("" if gap.plausible else "  [skipped]"))
            print(f"wrote {path.relative_to(ft.ROOT)}")
            return 0

    if args.limit:
        gaps = gaps[:args.limit]

    if args.dry_run:
        print("dry run — nothing will be fetched")
        def window_text(a: datetime, b: datetime) -> str:
            tail = f"{b:%H:%M}Z" if b.date() == a.date() else f"{b:%d%b %H:%M}Z"
            return f"{a:%d%b %H:%M}Z-{tail}"

        for gap in gaps:
            windows = ", ".join(window_text(a, b) for a, b in gap.windows())
            query = (f"flight {gap.flight_number}" if gap.flight_number
                     else f"airframe {gap.registration}")
            print(f"  {gap.describe()}: list {query} over {windows}; fetch the playback "
                  f"of the {gap.origin}-{gap.destination} flight found")
        return 0

    try:
        import fr24  # noqa: F401
    except ImportError:
        print('the Flightradar24 client is not installed: '
              'python3 -m pip install "fr24[curl]"', file=sys.stderr)
        return 1

    if not (os.environ.get("fr24_username") or os.environ.get("fr24_subscription_key")):
        print("no Flightradar24 credentials in the environment: set fr24_username and "
              "fr24_password (or fr24_subscription_key and fr24_token), or run "
              "`fr24 auth create`", file=sys.stderr)
        return 1

    from fr24 import FR24

    async def go() -> list[dict]:
        async with FR24() as client:
            await client.login("from_env")
            return await run(client, gaps, outdir / "tracks", args)

    fetched = asyncio.run(go())
    append_manifest(outdir / "tracks" / "manifest.csv", fetched)
    if not fetched:
        print("nothing fetched — every gap was left open", file=sys.stderr)
        return 2
    print(f"{len(fetched)} sector(s) fetched into {outdir.relative_to(ft.ROOT)}/tracks/")
    print(f"rebuild the month with: python3 work/fr24_tracks.py --month {month}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
