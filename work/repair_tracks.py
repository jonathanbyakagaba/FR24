#!/usr/bin/env python3
"""Put the coordinates back into the tracks the archive fetched without them.

Between 6 and 24 November every track the nightly job wrote came out at
0.000000,0.000000: the playback's latitude and longitude were read from a nested
field the API does not use. The parser is fixed, so nothing new arrives like
that, but 513 tracks are already in the archive with altitude, speed and heading
and no position at all.

They are recoverable without guessing. Each one's manifest row carries the
flight id and the departure time, and a playback can be asked for by id — no
flight list, no seven-day window, no matching of routes. This walks the archive
for tracks with no positions, asks for each flight's playback again, and
rewrites the file in place when the answer this time has coordinates in it. The
manifest row keeps its flight, route and times; only the points change.

    python3 work/repair_tracks.py --plan           # what is empty, no network
    python3 work/repair_tracks.py --dry-run        # what it would ask for
    python3 work/repair_tracks.py --minutes 30     # the repair pass

It is bounded the way the sweep is bounded — by a clock, not a head-count — so
it can run inside the nightly job without eating it. Whatever is left waits for
the next run. A flight whose playback still comes back empty is remembered in
``state/repair.json`` and not asked about more than twice: if Flightradar24 has
nothing for it now, asking again tomorrow is just noise.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_fr24_tracks as fetch  # noqa: E402
import fr24_tracks as ft  # noqa: E402

STATE = ft.ROOT / "state" / "repair.json"
DEFAULT_MINUTES = 30.0
DEFAULT_TRIES = 2          # ask twice, then leave it alone
EMPTY = "0.000000,0.000000"


@dataclass
class Track:
    """One track file that holds no position, and the row that describes it."""

    month: str
    path: Path
    row: dict = field(default_factory=dict)

    @property
    def flight_id(self) -> str:
        return str(self.row.get("flight_id_hex") or "").strip()

    @property
    def departure(self) -> datetime | None:
        stamp = str(self.row.get("atd_utc") or "").strip()
        if stamp:
            try:
                return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return _first_stamp(self.path)

    def describe(self) -> str:
        row = self.row
        return (f"{self.month} {row.get('number') or row.get('callsign') or '?'} "
                f"{row.get('from') or '?'}-{row.get('to') or '?'} "
                f"{row.get('registration') or '?'} {row.get('atd_utc') or ''}").strip()


def _first_stamp(path: Path) -> datetime | None:
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                try:
                    return datetime.fromtimestamp(int(row["Timestamp"]), tz=timezone.utc)
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError:
        return None
    return None


def _ident(path: Path) -> tuple[str, str]:
    """The callsign and registration already written in the file's first row."""
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                return (row.get("Callsign") or "").strip(), (row.get("Registration") or "").strip()
    except OSError:
        pass
    return "", ""


def has_positions_in_file(path: Path) -> bool:
    """Whether a track file on disk holds a real coordinate anywhere."""
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if (row.get("Position") or "").strip() not in ("", EMPTY):
                    return True
    except OSError:
        return False
    return False


def empty_tracks(root: Path | None = None, months: list[str] | None = None) -> list[Track]:
    """Every track in the archive with no position, newest flight first."""
    base = (root or ft.ROOT) / "archive"
    if not base.is_dir():
        return []
    wanted = months or sorted(p.name for p in base.iterdir()
                              if p.is_dir() and len(p.name) == 7 and p.name[4] == "-")
    found: list[Track] = []
    for month in wanted:
        tracks = base / month / "tracks"
        if not tracks.is_dir():
            continue
        manifest = ft.load_manifest(tracks / "manifest.csv")
        for path in sorted(tracks.glob("*.csv")):
            if path.name == "manifest.csv":
                continue
            if has_positions_in_file(path):
                continue
            found.append(Track(month=month, path=path, row=manifest.get(path.name) or {}))
    found.sort(key=lambda track: track.row.get("atd_utc") or "", reverse=True)
    return found


def rewrite(track: Track, points: list[dict]) -> int:
    """Replace a track file's points with real coordinates, and update its row."""
    callsign, registration = _ident(track.path)
    with track.path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(fetch.TRACK_COLUMNS)
        for point in points:
            stamp = int(point.get("timestamp") or 0)
            latitude, longitude = fetch.point_coords(point)
            writer.writerow([
                stamp,
                datetime.fromtimestamp(stamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                callsign,
                registration,
                f"{latitude:.6f},{longitude:.6f}",
                int((point.get("altitude") or {}).get("feet") or 0),
                int((point.get("speed") or {}).get("kts") or 0),
                int(point.get("heading") or 0),
            ])
    track.row["track_points"] = len(points)
    track.row["sha256"] = hashlib.sha256(track.path.read_bytes()).hexdigest()
    return len(points)


def write_manifest(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fetch.MANIFEST_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fetch.MANIFEST_COLUMNS})


def load_state(path: Path | None = None) -> dict:
    path = path or STATE
    if not path.exists():
        return {"attempts": {}, "totals": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"attempts": {}, "totals": {}}
    state.setdefault("attempts", {})
    state.setdefault("totals", {})
    return state


def save_state(state: dict, path: Path | None = None, repaired: int = 0) -> None:
    path = path or STATE
    state["totals"] = {
        "repaired": int(state.get("totals", {}).get("repaired") or 0) + repaired,
        "empty": len(state["attempts"]),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def note(state: dict, track: Track, outcome: str) -> None:
    record = state["attempts"].setdefault(track.flight_id or track.path.name, {"tries": 0})
    record["tries"] = int(record.get("tries") or 0) + 1
    record["last"] = outcome
    record["file"] = track.path.name
    record["at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan(tracks: list[Track], state: dict, max_tries: int, limit: int = 0) -> list[Track]:
    """What to ask for: never tried first, then newest, skipping the written-off."""
    fresh = []
    for track in tracks:
        tries = int((state["attempts"].get(track.flight_id or track.path.name) or {})
                    .get("tries") or 0)
        if tries >= max_tries:
            continue
        fresh.append((tries, track))
    fresh.sort(key=lambda pair: pair[1].row.get("atd_utc") or "", reverse=True)  # newest first
    fresh.sort(key=lambda pair: pair[0])                                         # never tried first
    chosen = [track for _tries, track in fresh]
    return chosen[:limit] if limit else chosen


@dataclass
class Repaired:
    touched: set[str] = field(default_factory=set)
    done: list[Track] = field(default_factory=list)
    asked: int = 0
    repaired: int = 0
    left: int = 0
    still_empty: int = 0


async def repair(tracks: list[Track], args, state: dict, *,
                 client_factory=None, clock=None) -> Repaired:
    """Ask for each flight's playback again, and rewrite the ones that now have points."""
    clock = clock or time.monotonic
    if client_factory is None:
        from fr24 import FR24 as client_factory

    result = Repaired()
    deadline = (clock() + args.minutes * 60) if args.minutes else None
    async with client_factory() as client:
        await client.login("from_env")
        for index, track in enumerate(tracks):
            if deadline is not None and clock() >= deadline:
                result.left = len(tracks) - index
                print(f"out of time after {result.asked} flights — "
                      f"{result.left} left for the next run", file=sys.stderr)
                break
            departure = track.departure
            if departure is None or not track.flight_id:
                result.still_empty += 1
                note(state, track, "no flight id or departure in the manifest")
                continue
            try:
                payload = await client.playback.fetch(
                    track.flight_id, timestamp=int(departure.timestamp()))
                body = (payload.to_dict().get("result") or {}).get("response") or {}
                points = ((body.get("data") or {}).get("flight") or {}).get("track") or []
            except Exception as error:  # noqa: BLE001 - one flight is not the repair
                result.still_empty += 1
                note(state, track, f"{type(error).__name__}: {error}")
                continue
            result.asked += 1
            if not fetch.has_positions(points):
                result.still_empty += 1
                note(state, track, "the playback still has no positions")
                print(f"  {track.describe()}: still no positions", file=sys.stderr)
                continue
            count = rewrite(track, points)
            state["attempts"].pop(track.flight_id or track.path.name, None)
            result.repaired += 1
            result.done.append(track)
            result.touched.add(track.month)
            print(f"  {track.describe()}: {count} points restored")
            await asyncio.sleep(args.pause)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Put the coordinates back into tracks that were written without them.")
    parser.add_argument("--minutes", type=float, default=DEFAULT_MINUTES,
                        help=f"wall-clock limit for the asking (default {DEFAULT_MINUTES}; "
                             "0 = no limit)")
    parser.add_argument("--limit", type=int, default=0,
                        help="at most this many flights this run (default 0 = all)")
    parser.add_argument("--month", action="append", default=[],
                        help="restrict to a month (repeatable); default is all of them")
    parser.add_argument("--tries", type=int, default=DEFAULT_TRIES,
                        help=f"attempts before a flight is left alone (default {DEFAULT_TRIES})")
    parser.add_argument("--plan", action="store_true",
                        help="say what is empty and stop (no network, no credentials)")
    parser.add_argument("--dry-run", action="store_true",
                        help="say what would be asked for, fetch nothing")
    parser.add_argument("--no-rebuild", action="store_true",
                        help="rewrite the tracks but do not rebuild the months")
    parser.add_argument("--root", default=str(ft.ROOT), help="the archive to work on")
    parser.add_argument("--state", default=None, help="path to state/repair.json")
    parser.add_argument("--pause", type=float, default=1.0, help="seconds between flights")
    args = parser.parse_args(argv)

    root = Path(args.root)
    state_path = Path(args.state) if args.state else root / "state" / "repair.json"
    state = load_state(state_path)
    tracks = empty_tracks(root, args.month or None)
    chosen = plan(tracks, state, args.tries, args.limit)

    head = (f"tracks with no positions: {len(tracks)}\n"
            f"  {len(chosen)} to ask for, "
            f"{len(tracks) - len(chosen)} already written off")
    if args.plan:
        print(head)
        for track in chosen[:40]:
            print("  next: " + track.describe())
        if len(chosen) > 40:
            print(f"  … and {len(chosen) - 40} more")
        return 0

    if not chosen:
        print(head)
        print("nothing empty to repair")
        return 0

    if args.dry_run:
        print(head)
        print(f"dry run — would ask for {len(chosen)} flights")
        for track in chosen[:20]:
            print("  " + track.describe())
        return 0

    try:
        import fr24  # noqa: F401
    except ImportError:
        print('the Flightradar24 client is not installed: '
              'python3 -m pip install "fr24[curl]"', file=sys.stderr)
        return 1
    if not (os.environ.get("fr24_username") or os.environ.get("fr24_subscription_key")):
        print("no Flightradar24 credentials in the environment", file=sys.stderr)
        return 1

    result = asyncio.run(repair(chosen, args, state))

    for month in sorted(result.touched):
        # the manifest row keeps its flight, route and times; the points changed,
        # so the row's point count and hash are refreshed before the month is read
        manifest = root / "archive" / month / "tracks" / "manifest.csv"
        existing = ft.load_manifest(manifest)
        repaired_files = {track.path.name for track in result.done if track.month == month}
        for track in result.done:
            if track.month == month and track.row:
                existing[track.row.get("file") or track.path.name] = track.row
        if repaired_files:
            write_manifest(manifest, list(existing.values()))
        if args.no_rebuild:
            continue
        print(f"rebuilding {month}")
        ft.main(["--month", month, "--outdir", str(root / "archive" / month)])

    save_state(state, state_path, repaired=result.repaired)
    print(f"{result.repaired} repaired, {result.still_empty} still empty, "
          f"{result.left} left for the next run — {len(tracks) - result.repaired} to go")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
