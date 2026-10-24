#!/usr/bin/env python3
"""Match the 97 no-track FTA legs (work/missing_legs.csv) against the
FR24 flight lists enumerated on the user's machine (work/flightlists/).

v3 (final) rules, learned from the data:
- FR24 ICAO codes: Harare = FVRG (not FVHA), Juba = HJJJ (not HSSJ).
- Candidates exclude every flight id already in the archive (observed
  legs' track filenames + every -<hex>.csv in the FR data zips).
- Pass 1: same flight number + exact route, ATOD within -240..+480 min
  of FTA STD (the FTA-join window); rank by typecode match, |delta|.
- Pass 2: nearest remaining candidate within +/-12 h -> shifted_match.
  Candidates 12-36 h away are reported as adjacent_rotation: the leg
  did not operate; that flight is the neighbouring rotation (usually
  already archived). Everything else is not_found = not operated.

Writes work/targets.csv (pass1 + pass2) and work/match_report.csv.
Run: python3 work/match_missing.py
"""

from __future__ import annotations

import csv
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / "work" / "flightlists"

IATA_TO_ICAO = {
    "EBB": "HUEN", "NBO": "HKJK", "DAR": "HTDA", "JNB": "FAOR",
    "LGW": "EGKK", "LOS": "DNMM", "BOM": "VABB", "MBA": "HKMO",
    "MGQ": "HCMM", "JUB": "HJJJ", "HRE": "FVRG", "ZNZ": "HTZA",
    "JRO": "HTKJ", "BJM": "HBBA", "LUN": "FLKK",
}
WIN_LO, WIN_HI = timedelta(hours=-4), timedelta(hours=8)
SHIFT_ACCEPT = timedelta(hours=12)
SHIFT_SCAN = timedelta(hours=36)
HEX_RE = re.compile(r"-([0-9a-f]{8})\.csv$")


def parse_ts(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_flights() -> list[dict]:
    flights = []
    for fp in sorted(LISTS.glob("flightlist_*.csv")):
        for r in csv.DictReader(fp.open()):
            if not r["flight_id"] or not r["ATOD"]:
                continue
            r["_atod"] = parse_ts(r["ATOD"])
            r["_file"] = fp.name
            flights.append(r)
    return flights


def claimed_ids() -> set[int]:
    """Every flight id whose track is already in the archive."""
    ids: set[int] = set()
    for folder in ("UR SEPTEMBER 2026", "UR OCTOBER 2026"):
        for r in csv.DictReader((ROOT / folder / "schedule_delays.csv").open()):
            st = r["fr24_status"]
            if "track " in st:
                try:
                    ids.add(int(st.split("track ")[1].split(".csv")[0].rsplit("-", 1)[1], 16))
                except (ValueError, IndexError):
                    pass
    for zname in ("FR data.zip",):
        with zipfile.ZipFile(ROOT / zname) as z:
            for n in z.namelist():
                if (m := HEX_RE.search(n)):
                    ids.add(int(m.group(1), 16))
    return ids


def main() -> None:
    flights = load_flights()
    claimed = claimed_ids()
    print(f"flight rows: {len(flights)}; ids already in archive: {len(claimed)}")

    legs = list(csv.DictReader((ROOT / "work" / "missing_legs.csv").open()))
    used: set[int] = set()
    results: dict[int, dict] = {}

    def candidates(leg, std):
        o, d = IATA_TO_ICAO[leg["from"]], IATA_TO_ICAO[leg["to"]]
        return [
            r for r in flights
            if r["number"] == leg["flight"] and r["origin"] == o and r["destination"] == d
            and int(r["flight_id"]) not in claimed and int(r["flight_id"]) not in used
        ]

    def rank(leg, std):
        return lambda r: (r["typecode"] != leg["aircraft"],
                          abs((r["_atod"] - std).total_seconds()))

    # Pass 1: in-window matches for all legs first (no leg may steal
    # another leg's in-window flight via the shifted rule).
    pending = []
    for i, leg in enumerate(legs):
        std = parse_ts(leg["sched_dep_utc"])
        pool = [r for r in candidates(leg, std)
                if std + WIN_LO <= r["_atod"] <= std + WIN_HI]
        if pool:
            pool.sort(key=rank(leg, std))
            status = "matched"
            if len(pool) > 1:
                gap = abs((pool[1]["_atod"] - pool[0]["_atod"]).total_seconds())
                if gap < 1800 and pool[1]["typecode"] == pool[0]["typecode"]:
                    status = "ambiguous"
            results[i] = (status, pool[0], std)
            used.add(int(pool[0]["flight_id"]))
        else:
            pending.append(i)

    # Pass 2: shifted / adjacent / not found.
    for i in pending:
        leg = legs[i]
        std = parse_ts(leg["sched_dep_utc"])
        pool = candidates(leg, std)
        near = [r for r in pool if abs(r["_atod"] - std) <= SHIFT_SCAN]
        near.sort(key=rank(leg, std))
        if near and abs(near[0]["_atod"] - std) <= SHIFT_ACCEPT:
            results[i] = ("shifted_match", near[0], std)
            used.add(int(near[0]["flight_id"]))
        elif near:
            results[i] = ("adjacent_rotation", near[0], std)
        else:
            results[i] = ("not_found", None, std)

    targets, report = [], []
    counts: dict[str, int] = {}
    for i, leg in enumerate(legs):
        status, chosen, std = results[i]
        counts[status] = counts.get(status, 0) + 1
        row = {**leg, "status": status, "flight_id_hex": "", "callsign": "",
               "matched_atod": "", "delta_min": "", "note": ""}
        if chosen is not None:
            fid = int(chosen["flight_id"])
            row.update(
                flight_id_hex=f"{fid:08x}", callsign=chosen["callsign"],
                matched_atod=chosen["ATOD"],
                delta_min=round((chosen["_atod"] - std).total_seconds() / 60),
                note=f"{chosen['registration']} {chosen['typecode']} "
                     f"{chosen['origin']}->{chosen['destination']} ({chosen['_file']})",
            )
            if status in ("matched", "shifted_match", "ambiguous"):
                targets.append({
                    "flight_id_hex": row["flight_id_hex"], "number": leg["flight"],
                    "callsign": chosen["callsign"], "date": leg["date"],
                    "from": leg["from"], "to": leg["to"],
                })
        report.append(row)

    with (ROOT / "work" / "targets.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["flight_id_hex", "number", "callsign", "date", "from", "to"])
        w.writeheader(); w.writerows(targets)
    with (ROOT / "work" / "match_report.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(report[0].keys()))
        w.writeheader(); w.writerows(report)

    print(f"legs: {len(legs)}  targets: {len(targets)}  status: {counts}")
    for r in report:
        if r["status"] not in ("matched", "not_found"):
            print(f"  {r['status']:>17}  {r['date']} {r['flight']} {r['from']}->{r['to']} "
                  f"delta_min={r['delta_min']} {r['note']}")


if __name__ == "__main__":
    main()
