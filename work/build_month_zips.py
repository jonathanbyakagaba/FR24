#!/usr/bin/env python3
"""Rebuild the track archives after adding recovered tracks.

Pool = top-level FR data.zip (every unique track, all operators).
Month zips = the UR subset whose date_local (origin-local date of
takeoff/first fix, exactly as work/rebuild_month.py computes it) falls
in the month window:
  UR SEPTEMBER 2026/UR September flights.zip : 2026-09-01..2026-09-30
  UR OCTOBER 2026/FR data.zip                : 2026-10-01..2026-10-19

New tracks are read from work/tracks_in/*.csv (FR24 playback downloads),
added to the pool under the usual "FR data/FR data/<file>" entry names,
deduplicated by exact-content MD5 (canonical rule).

Safety: before writing, the computed membership of the OLD pool is
checked against the current month zips; any difference aborts the run.

Usage: python3 work/build_month_zips.py [--check]
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("rebuild_month", ROOT / "work" / "rebuild_month.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

TOP_ZIP = ROOT / "FR data.zip"
NEW_DIR = ROOT / "work" / "tracks_in"
PREFIX = "FR data/FR data/"
MONTHS = [
    (ROOT / "UR SEPTEMBER 2026" / "UR September flights.zip", "2026-09-01", "2026-09-30"),
    (ROOT / "UR OCTOBER 2026" / "FR data.zip", "2026-10-01", "2026-10-19"),
]


def track_info(name: str, text: str):
    """(is_ur, date_local) replicating rebuild_month.py's derivation."""
    base = Path(name).name
    rows = rb.parse_track(text)
    if not rows:
        return False, None
    import re
    m = re.match(r"(UR\d+|AF\d+)-([0-9a-f]+)\.csv", base)
    flight_no = m.group(1) if m else ""
    cs = next((r["cs"] for r in rows if r["cs"]), "")
    if not flight_no and cs.startswith("UGD"):
        mm = re.match(r"UGD(\d+)", cs)
        flight_no = "UR" + mm.group(1) if mm else ""
    is_ur = bool(flight_no) or cs.startswith("UGD")
    if not is_ur:
        return False, None
    a = rb.analyse(rows)
    can_o = rb.ROUTES.get(flight_no, ("", ""))[0]
    origin, od = rb.nearest_airport(rows[0]["lat"], rows[0]["lon"])
    if a["takeoff_not_obs"] and can_o and od > 80:
        origin = can_o
    dep_t = a["takeoff_t"] or rows[0]["t"]
    tz = ZoneInfo(rb.AIRPORTS.get(origin, rb.AIRPORTS["EBB"])[4])
    date_local = datetime.fromtimestamp(dep_t, timezone.utc).astimezone(tz).strftime("%Y-%m-%d")
    return True, date_local


def main() -> None:
    check_only = "--check" in sys.argv

    pool: dict[str, bytes] = {}  # entry name -> bytes
    with zipfile.ZipFile(TOP_ZIP) as z:
        for n in z.namelist():
            if n.endswith(".csv"):
                pool[n] = z.read(n)
    print(f"pool: {len(pool)} tracks")

    # verify membership rule reproduces current month zips from old pool
    info = {}
    for n, data in pool.items():
        info[n] = track_info(n, data.decode("utf-8", "replace"))
    ok = True
    for zip_path, lo, hi in MONTHS:
        computed = {Path(n).name for n, (ur, dl) in info.items() if ur and dl and lo <= dl <= hi}
        with zipfile.ZipFile(zip_path) as z:
            current = {Path(n).name for n in z.namelist() if n.endswith(".csv")}
        if computed != current:
            ok = False
            print(f"MISMATCH {zip_path.name}: computed {len(computed)} vs current {len(current)}")
            print("  only computed:", sorted(computed - current)[:10])
            print("  only current :", sorted(current - computed)[:10])
        else:
            print(f"membership rule OK for {zip_path.name}: {len(current)} tracks")
    if not ok:
        sys.exit("membership rule does not reproduce current zips; aborting")

    # add new tracks (content-MD5 dedupe, canonical)
    md5s = {hashlib.md5(d).hexdigest() for d in pool.values()}
    added = []
    for fp in sorted(NEW_DIR.glob("*.csv")):
        data = fp.read_bytes()
        if hashlib.md5(data).hexdigest() in md5s:
            print(f"  dupe skipped: {fp.name}")
            continue
        entry = PREFIX + fp.name
        if entry in pool:
            print(f"  name clash (different content): {fp.name}")
            continue
        pool[entry] = data
        info[entry] = track_info(entry, data.decode("utf-8", "replace"))
        added.append(fp.name)
    print(f"new tracks added to pool: {len(added)}")

    if check_only:
        print("--check only; nothing written")
        return

    def write_zip(path: Path, names: list[str]) -> None:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for n in names:
                z.writestr(n, pool[n])
        print(f"wrote {path.relative_to(ROOT)}: {len(names)} entries")

    write_zip(TOP_ZIP, sorted(pool))
    for zip_path, lo, hi in MONTHS:
        names = sorted(n for n, (ur, dl) in info.items() if ur and dl and lo <= dl <= hi)
        write_zip(zip_path, names)


if __name__ == "__main__":
    main()
