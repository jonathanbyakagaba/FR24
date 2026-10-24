#!/usr/bin/env python3
"""Build the download list to bring the flight archive up to date.

Reads the enumerated FR24 flight lists (work/flightlists/*.csv, produced
on the user's machine by fetch_fr24.py) and writes a targets CSV for
fetch_tracks.py containing every Uganda Airlines flight that

  * has arrived (ATOA set),
  * departed (origin-local date, as work/rebuild_month.py attributes it)
    between 2026-09-01 and the end date below,
  * is not already in the track archive (top-level FR data.zip) and was
    not already downloaded in the gap-recovery round (work/targets.csv).

Everything is included: no route/flight-number cherry-picking, and
fetch_tracks.py downloads the complete playback track as FR24 serves it.

Usage: python3 work/build_targets_uptodate.py [end-date YYYY-MM-DD]
       (default end date: 2026-10-22)
       python3 work/build_targets_uptodate.py <end-date> <only-date>
       writes work/targets_<only-date>.csv with just that day's flights.
"""

from __future__ import annotations

import csv
import glob
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from rebuild_month import AIRPORTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
START = "2026-09-01"
END = sys.argv[1] if len(sys.argv) > 1 else "2026-10-22"
ONLY = sys.argv[2] if len(sys.argv) > 2 else None  # single origin-local date
LO, HI = (ONLY, ONLY) if ONLY else (START, END)

ICAO2IATA = {
    "HUEN": "EBB", "HKJK": "NBO", "HTDA": "DAR", "FAOR": "JNB",
    "EGKK": "LGW", "DNMM": "LOS", "VABB": "BOM", "HKMO": "MBA",
    "HCMM": "MGQ", "HJJJ": "JUB", "HSSJ": "JUB", "FVRG": "HRE",
    "FVHA": "HRE", "HTZA": "ZNZ", "HTKJ": "JRO", "HBBA": "BJM",
    "FLKK": "LUN",
}


def parse_ts(s: str):
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def archived_ids() -> set[str]:
    ids: set[str] = set()
    with zipfile.ZipFile(ROOT / "FR data.zip") as z:
        for name in z.namelist():
            base = Path(name).name
            m = re.search(r"-([0-9a-f]{8})\.csv$", base) or re.match(r"([0-9a-f]{8})\.csv$", base)
            if m:
                ids.add(m.group(1).lower())
    prev = ROOT / "work" / "targets.csv"
    if prev.exists():
        for r in csv.DictReader(open(prev)):
            ids.add(r["flight_id_hex"].strip().lower())
    return ids


def main() -> None:
    have = archived_ids()
    print(f"archived flight ids: {len(have)}; window {LO} .. {HI} (origin-local)")
    targets: dict[str, dict] = {}
    seen = 0
    for fp in sorted(glob.glob(str(ROOT / "work" / "flightlists" / "*.csv"))):
        for r in csv.DictReader(open(fp)):
            seen += 1
            number = (r.get("number") or "").strip()
            callsign = (r.get("callsign") or "").strip()
            if not (number.startswith(("UR", "AF")) or callsign.startswith("UGD")):
                continue
            if not r.get("flight_id"):
                continue
            hex_id = f"{int(r['flight_id']):08x}"
            if hex_id in have or hex_id in targets:
                continue
            atod, atoa = parse_ts(r.get("ATOD", "")), parse_ts(r.get("ATOA", ""))
            status = (r.get("status") or "").strip()
            # Arrived means: ATOA recorded, OR the list itself says the
            # flight landed / diverted (FR24 sometimes leaves ATOA empty
            # for diverted flights and some landed ones).
            arrived = atoa is not None or status.startswith(("Landed", "Diverted"))
            if atod is None or not arrived:
                continue  # not departed, or still airborne: arrived only
            o_iata = ICAO2IATA.get(r["origin"], r["origin"])
            d_iata = ICAO2IATA.get(r["destination"], r["destination"])
            tz = ZoneInfo(AIRPORTS[o_iata][4]) if o_iata in AIRPORTS else timezone.utc
            date_local = atod.astimezone(tz).strftime("%Y-%m-%d")
            if not (LO <= date_local <= HI):
                continue
            targets[hex_id] = dict(
                flight_id_hex=hex_id, number=number, callsign=callsign,
                date=date_local, **{"from": o_iata, "to": d_iata},
                registration=r.get("registration", ""),
                atod_utc=atod.strftime("%Y-%m-%dT%H:%M:%SZ"),
                atoa_utc=atoa.strftime("%Y-%m-%dT%H:%M:%SZ") if atoa else "",
                status=status,
            )
    rows = sorted(targets.values(), key=lambda t: t["atod_utc"])
    out = ROOT / "work" / (f"targets_{ONLY}.csv" if ONLY else "targets_uptodate.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["flight_id_hex", "number", "callsign", "date",
                                          "from", "to", "registration", "atod_utc", "atoa_utc", "status"])
        w.writeheader()
        w.writerows(rows)
    print(f"scanned {seen} flight-list rows; wrote {len(rows)} targets -> {out.relative_to(ROOT)}")
    print("by origin-local date:", dict(sorted(Counter(t["date"] for t in rows).items())))


if __name__ == "__main__":
    main()
