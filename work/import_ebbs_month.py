#!/usr/bin/env python3
"""Copy one month of track exports out of an EBBs-FR24 checkout into the archive.

The sibling project `EBBs-FR24` enumerates every movement at Entebbe, pulls the
position track for each one and keeps a movement board plus a track manifest.
This script takes the slice belonging to one airline and one month and lays it
down in this repository as

    archive/YYYY-MM/tracks/<number>-<flight_id_hex>.csv   raw exports, unedited
    archive/YYYY-MM/tracks/manifest.csv                   one row per file

and nothing else — `work/fr24_tracks.py` builds the log from there.

    python3 work/import_ebbs_month.py --source ../EBBs-FR24 --month 2026-06
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MANIFEST_COLUMNS = [
    "file", "flight_id_hex", "number", "callsign", "date", "from", "to",
    "registration", "aircraft", "atd_utc", "ata_utc", "std_utc", "sta_utc",
    "track_points", "sha256",
]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def git_commit(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def count_points(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, type=Path, help="EBBs-FR24 checkout")
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument("--airline", default="Uganda Airlines")
    parser.add_argument("--outdir", type=Path, default=None,
                        help="defaults to archive/<month>")
    parser.add_argument("--force", action="store_true", help="overwrite an existing archive")
    args = parser.parse_args(argv)

    outdir = args.outdir or ROOT / "archive" / args.month
    tracks_out = outdir / "tracks"
    if tracks_out.exists() and any(tracks_out.glob("*.csv")) and not args.force:
        print(f"{tracks_out} already holds tracks — pass --force to replace them",
              file=sys.stderr)
        return 1
    tracks_out.mkdir(parents=True, exist_ok=True)

    targets = [row for row in read_csv(args.source / "data" / "track_targets.csv")
               if row.get("airline") == args.airline
               and row.get("date", "").startswith(args.month)]
    board = {row["flight_id_hex"]: row
             for row in read_csv(args.source / "data" / "movements.csv")}
    manifest = {row["flight_id_hex"]: row
                for row in read_csv(args.source / "data" / "track_manifest.csv")}

    if not targets:
        print(f"no {args.airline} flights for {args.month} in {args.source}", file=sys.stderr)
        return 1

    rows, missing, total_bytes = [], [], 0
    for target in sorted(targets, key=lambda r: (r["date"], r["number"])):
        entry = manifest.get(target["flight_id_hex"])
        if not entry or not entry.get("file"):
            missing.append(target["number"])
            continue
        source_file = args.source / "tracks" / entry["file"]
        if not source_file.exists():
            missing.append(entry["file"])
            continue
        shutil.copy2(source_file, tracks_out / entry["file"])
        total_bytes += source_file.stat().st_size
        board_row = board.get(target["flight_id_hex"], {})
        rows.append({
            "file": entry["file"],
            "flight_id_hex": target["flight_id_hex"],
            "number": target["number"],
            "callsign": target.get("callsign", ""),
            "date": target.get("date", ""),
            "from": target.get("from", ""),
            "to": target.get("to", ""),
            "registration": board_row.get("registration", ""),
            "aircraft": target.get("aircraft", ""),
            "atd_utc": board_row.get("atod_utc", ""),
            "ata_utc": board_row.get("atoa_utc", ""),
            "std_utc": board_row.get("stod_utc", ""),
            "sta_utc": board_row.get("stoa_utc", ""),
            "track_points": count_points(source_file),
            "sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
        })

    with (tracks_out / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} tracks, {total_bytes / 1e6:.1f} MB, from {args.source} "
          f"@ {git_commit(args.source)[:12] or 'unknown commit'}")
    if missing:
        print(f"{len(missing)} flights had no track file and were skipped: "
              f"{', '.join(missing[:10])}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
