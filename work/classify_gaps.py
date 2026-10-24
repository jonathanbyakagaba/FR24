#!/usr/bin/env python3
"""Classify every no-track FTA leg in both months' schedule_delays.csv.

For each leg with state == no_track, search the enumerated FR24 flight
lists (work/flightlists/*.csv) for the same flight number + route within
±36 h of the plan STD (UTC), excluding nothing up front, then verdict:

  operated_recoverable  a candidate whose flight id is NOT in the track
                        archive and ATOD is within -240..+480 min of STD
                        (or shifted by <=12 h): the flight operated; its
                        track can still be downloaded (Phase 5).
  operated_in_archive   a candidate inside the FTA window whose id IS
                        archived, yet the join missed it (e.g. departed
                        >8 h late, outside the join's +480 min window).
  did_not_operate       no candidate, or the only candidates are archived
                        rotations ~24 h away (adjacent rotations) or
                        shifted candidates that are already archived.

Writes work/gap_verdicts.csv. Read-only otherwise: it never touches
work/targets.csv / work/match_report.csv (the gap-recovery evidence).

Run: python3 work/classify_gaps.py
"""

from __future__ import annotations

import csv
import glob
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IATA2ICAO = {
    "EBB": {"HUEN"}, "NBO": {"HKJK"}, "DAR": {"HTDA"}, "JNB": {"FAOR"},
    "LGW": {"EGKK"}, "LOS": {"DNMM"}, "BOM": {"VABB"}, "MBA": {"HKMO"},
    "MGQ": {"HCMM"}, "JUB": {"HJJJ", "HSSJ"}, "HRE": {"FVRG", "FVHA"},
    "ZNZ": {"HTZA"}, "JRO": {"HTKJ"}, "BJM": {"HBBA"}, "LUN": {"FLKK"},
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
    return ids


def main() -> None:
    have = archived_ids()
    lists = []
    for fp in sorted(glob.glob(str(ROOT / "work" / "flightlists" / "*.csv"))):
        for r in csv.DictReader(open(fp)):
            atod = parse_ts(r.get("ATOD", ""))
            if atod is None or not r.get("flight_id"):
                continue
            lists.append(dict(number=(r.get("number") or "").strip(),
                              callsign=(r.get("callsign") or "").strip(),
                              origin=r.get("origin", ""), dest=r.get("destination", ""),
                              reg=r.get("registration", ""), atod=atod,
                              hex_id=f"{int(r['flight_id']):08x}"))

    out_rows = []
    for folder in ("UR SEPTEMBER 2026", "UR OCTOBER 2026"):
        sd = list(csv.DictReader(open(ROOT / folder / "schedule_delays.csv")))
        for leg in sd:
            if leg["state"] != "no_track":
                continue
            std = datetime.strptime(leg["sched_dep_utc"], "%Y-%m-%d %H:%MZ").replace(tzinfo=timezone.utc)
            num = leg["flight"]
            cands = []
            for r in lists:
                if r["number"] != num and r["callsign"] != "UGD" + num[2:]:
                    continue
                if r["origin"] not in IATA2ICAO.get(leg["from_"], set()) or r["dest"] not in IATA2ICAO.get(leg["to"], set()):
                    continue
                delta = (r["atod"] - std).total_seconds() / 60.0
                if abs(delta) <= 36 * 60:
                    cands.append((delta, r))
            cands.sort(key=lambda c: abs(c[0]))
            verdict, evidence = "did_not_operate", "no candidate within ±36 h in any tail's FR24 flight list"
            for delta, r in cands:
                archived = r["hex_id"] in have
                if not archived and -240 <= delta <= 480:
                    verdict = "operated_recoverable"
                    evidence = (f"{r['reg']} ATOD {r['atod'].strftime('%Y-%m-%d %H:%MZ')} "
                                f"({delta:+.0f} min vs STD), flight id {r['hex_id']} not in archive")
                    break
                if not archived and abs(delta) <= 12 * 60:
                    verdict = "operated_recoverable"
                    evidence = (f"shifted: {r['reg']} ATOD {r['atod'].strftime('%Y-%m-%d %H:%MZ')} "
                                f"({delta:+.0f} min vs STD), flight id {r['hex_id']} not in archive")
                    break
                if archived and -240 <= delta <= 480:
                    verdict = "operated_in_archive"
                    evidence = (f"{r['reg']} ATOD {r['atod'].strftime('%Y-%m-%d %H:%MZ')} "
                                f"({delta:+.0f} min vs STD); id {r['hex_id']} is archived but the FTA join missed it")
                    break
                if archived and abs(delta) <= 12 * 60:
                    verdict = "operated_in_archive"
                    evidence = (f"shifted: {r['reg']} ATOD {r['atod'].strftime('%Y-%m-%d %H:%MZ')} "
                                f"({delta:+.0f} min vs STD); id {r['hex_id']} is archived but the FTA join missed it")
                    break
            else:
                if cands:
                    delta, r = cands[0]
                    evidence = (f"nearest candidate is the adjacent rotation: {r['reg']} ATOD "
                                f"{r['atod'].strftime('%Y-%m-%d %H:%MZ')} ({delta:+.0f} min vs STD), "
                                f"archived={r['hex_id'] in have}")
            out_rows.append(dict(month=folder, date=leg["date"], flight=num,
                                 **{"from": leg["from_"], "to": leg["to"]},
                                 std_utc=leg["sched_dep_utc"], verdict=verdict, evidence=evidence))
    out = ROOT / "work" / "gap_verdicts.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["month", "date", "flight", "from", "to", "std_utc", "verdict", "evidence"])
        w.writeheader()
        w.writerows(out_rows)
    from collections import Counter
    print(f"{len(out_rows)} no_track legs classified -> {out.relative_to(ROOT)}")
    print(Counter(r["verdict"] for r in out_rows))
    for r in out_rows:
        if r["verdict"] != "did_not_operate":
            print(" ", r["month"][:12], r["date"], r["flight"], r["from"], "->", r["to"], "|", r["verdict"], "|", r["evidence"])


if __name__ == "__main__":
    main()
