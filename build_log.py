#!/usr/bin/env python3
"""
build_log.py — regenerate the AeroRoutes flight log from track data.

Reads the CSV tracks (from a zip or a folder), works out each flight's endpoints,
take-off and landing, converts to local time at each end, and writes the log in
AeroRoutes notation:

    DDMMMYY  UGD### ORIGhhmm – hhmm[+1]DEST[marker]

  * dates are local departure dates
  * times are local at each end (take-off origin-local, landing destination-local)
  * +1 before the destination means arrival on the following local day
  * ≈ = take-off not observed (no ground contact, or a silent gap at lift-off)
  * * = landing not observed (track ends airborne)

Every printed time comes from an actual position report. Where the moment itself
was not witnessed the marker says so, and --csv carries the uncertainty bracket.

Usage
  python3 build_log.py "FR data.zip" --month 2026-09 -o all_flights_aeroroutes.md
  python3 build_log.py "FR data.zip" --month 2026-09 --csv tracking.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import os
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# code: (latitude, longitude, UTC offset in hours) — none of these stations observe
# daylight saving, so one offset per code holds all year
AIRPORTS = {
    "EBB": (0.0424, 32.4435, 3),      "NBO": (-1.3192, 36.9278, 3),
    "DAR": (-6.8781, 39.2026, 3),     "ZNZ": (-6.2220, 39.2249, 3),
    "MBA": (-4.0348, 39.5944, 3),     "JRO": (-3.4294, 37.0745, 3),
    "MGQ": (2.0144, 45.3047, 3),      "ADD": (8.9779, 38.7993, 3),
    "DOH": (25.2731, 51.6081, 3),     "CAI": (30.1219, 31.4056, 3),
    "IST": (41.2753, 28.7519, 3),     "TNR": (-18.7969, 47.4788, 3),
    "JUB": (4.8720, 31.6011, 2),      "BJM": (-3.3240, 29.3185, 2),
    "JNB": (-26.1392, 28.2460, 2),    "HRE": (-17.9318, 31.0928, 2),
    "LUN": (-15.3308, 28.4526, 2),    "KGL": (-1.9686, 30.1395, 2),
    "GOM": (-1.6708, 29.2385, 2),     "FBM": (-11.5913, 27.5309, 2),
    "KRT": (15.5895, 32.5532, 2),     "CPT": (-33.9715, 18.6021, 2),
    "BRU": (50.9014, 4.4844, 2),      "AMS": (52.3105, 4.7683, 2),
    "LOS": (6.5774, 3.3212, 1),       "FIH": (-4.3858, 15.4446, 1),
    "LGW": (51.1481, -0.1903, 1),     "DXB": (25.2528, 55.3644, 4),
    "MRU": (-20.4302, 57.6836, 4),    "SEZ": (-4.6743, 55.5218, 4),
    "DSS": (14.6708, -17.0734, 0),
    # long-haul destinations that appear in the tracks; note India is UTC+5:30
    "BOM": (19.0887, 72.8679, 5.5),   "DEL": (28.5562, 77.1000, 5.5),
    "WDH": (-22.4799, 17.4709, 2),    "MED": (24.5534, 39.7051, 3),
    "GRU": (-23.4356, -46.4731, -3),  "ABJ": (5.2614, -3.9263, 0),
    # added after the original list, both because tracks touch them:
    #   JED  King Abdulaziz, Jeddah — the Garuda and Flynas tracks land here, and the
    #        nearest airport on the old list was Medina, 175 NM away
    #   UG-0013  Kabalega International, Hoima — opened to passenger flights on
    #        27 Sep 2026; carries no IATA or ICAO code yet, so it is keyed by its
    #        OurAirports ident
    "JED": (21.6796, 39.1565, 3),     "UG-0013": (1.4433, 31.0740, 3),
}
MAX_MISS_NM = 25        # endpoint must be this close to count as that airport
AIRBORNE_FT = 100       # airborne above this; on the ground at or below
OBSERVED_GAP_S = 600    # a longer silent gap means the transition was not observed


def haversine_nm(lat1, lon1, lat2, lon2) -> float:
    r = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_airport(lat: float, lon: float):
    best = (None, 1e9)
    for code, (alat, alon, _) in AIRPORTS.items():
        d = haversine_nm(lat, lon, alat, alon)
        if d < best[1]:
            best = (code, d)
    return best


def local(ts: float, offset_h: float) -> datetime:
    return datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None) + timedelta(hours=offset_h)


def read_tracks(src: str) -> list[tuple[str, bytes]]:
    out = []
    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                name = info.filename.split("/")[-1]
                if name.lower().endswith(".csv"):
                    out.append((name, z.read(info.filename)))
    elif os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.lower().endswith(".csv"):
                out.append((f, open(os.path.join(src, f), "rb").read()))
    else:
        raise SystemExit(f"error: {src} is neither a zip nor a folder")
    return out


def parse_track(raw: bytes) -> list[tuple]:
    text = raw.decode("utf-8-sig", errors="replace")
    rdr = csv.reader(io.StringIO(text))
    header = next(rdr, None)
    if not header:
        return []
    idx = {c.strip().lower(): i for i, c in enumerate(header)}
    if not {"timestamp", "position"} <= set(idx):
        return []
    rows = []
    for r in rdr:
        try:
            ts = float(r[idx["timestamp"]])
            lat, lon = (float(x) for x in r[idx["position"]].split(","))
        except (ValueError, IndexError, KeyError):
            continue
        try:
            alt = float(r[idx["altitude"]]) if "altitude" in idx else 0.0
        except (ValueError, IndexError):
            alt = 0.0
        cs = r[idx["callsign"]].strip() if "callsign" in idx and len(r) > idx["callsign"] else ""
        rows.append((ts, lat, lon, alt, cs))
    rows.sort(key=lambda x: x[0])
    return rows


def flight_number(name: str, callsign: str) -> str:
    """The callsign is authoritative: it keeps suffixes the filename drops
    (UR207-4173413d.csv is transmitted as UGD207D).  Filename is the fallback."""
    cs = callsign.upper().strip()
    m = re.match(r"^(UGD|UR|UG)(\d+[A-Z]?)$", cs)
    if m:
        return "UGD" + m.group(2)
    if re.match(r"^[A-Z]{2,3}\d+[A-Z]?$", cs):
        return cs
    m = re.match(r"^([A-Z]{2})(\d+[A-Z]?)-\w+\.csv$", name.upper())
    if m:
        return "UGD" + m.group(2)
    return cs


def build(src: str, month: str):
    tracks = read_tracks(src)
    flights, skipped = [], []
    for name, raw in tracks:
        rows = parse_track(raw)
        if len(rows) < 2:
            skipped.append((name, "no usable rows"))
            continue
        cs = next((r[4] for r in rows if r[4]), "")
        fn = flight_number(name, cs)
        if not fn.startswith("UGD"):
            continue

        air_idx = [i for i, r in enumerate(rows) if r[3] > AIRBORNE_FT]
        if not air_idx:
            skipped.append((name, "never airborne"))
            continue
        first_air, last_air = air_idx[0], air_idx[-1]

        # Convention taken from the published log: take-off is the first report with
        # the aircraft airborne (rotation), landing is the first report back on the
        # ground (touchdown). Each is the first fix in its new state.
        t_off, o_pos = rows[first_air][0], rows[first_air]
        ground_after = [i for i in range(last_air + 1, len(rows)) if rows[i][3] <= AIRBORNE_FT]
        if ground_after:
            t_land, d_pos = rows[ground_after[0]][0], rows[ground_after[0]]
        else:
            t_land, d_pos = rows[last_air][0], rows[last_air]

        # the moment counts as observed only if ground contact brackets it: otherwise
        # the aircraft was first seen already airborne (the Mogadishu pattern)
        ground_before = [i for i in range(first_air) if rows[i][3] <= AIRBORNE_FT]
        if ground_before:
            gi = ground_before[-1]
            est = (t_off - rows[gi][0]) > OBSERVED_GAP_S
            brk_off = (t_off, rows[gi][0]) if est else (None, None)
        else:
            est, brk_off = True, (t_off, None)
        unobs = not ground_after
        brk_land = (t_land, None) if unobs else (None, None)

        o_code, o_miss = nearest_airport(o_pos[1], o_pos[2])
        d_code, d_miss = nearest_airport(d_pos[1], d_pos[2])
        if o_miss > MAX_MISS_NM:
            est = True
        if d_miss > MAX_MISS_NM:
            unobs = True

        dep = local(t_off, AIRPORTS[o_code][2])
        arr = local(t_land, AIRPORTS[d_code][2])
        if month not in (None, "auto", "all") and dep.strftime("%Y-%m") != month:
            continue

        flights.append(dict(fn=fn, origin=o_code, dest=d_code, dep=dep, arr=arr,
                            est=est, unobs=unobs, name=name, o_miss=o_miss, d_miss=d_miss,
                            n=len(rows), dur=(t_land - t_off) / 60.0,
                            t_off_utc=t_off, t_land_utc=t_land,
                            brk_off=brk_off, brk_land=brk_land))
    flights.sort(key=lambda f: f["t_off_utc"])
    return flights, skipped


def render(flights, month: str) -> str:
    by_day = defaultdict(list)
    for f in flights:
        by_day[f["dep"].strftime("%d%b%y").upper()].append(f)
    first = flights[0]["dep"].strftime("%d%b%y").upper()
    last = flights[-1]["dep"].strftime("%d%b%y").upper()

    lines = ["# All Flights — AeroRoutes Notation with Departure Dates", ""]
    lines.append(f"**{len(flights)} flights**, {first}–{last}. Times are **local airport** "
                 "(take-off origin-local, landing destination-local). Dates are **local departure "
                 "dates**. `≈` = take-off not observed · `*` = landing not observed (time shown is "
                 "the last observation, not the touchdown).")
    lines.append("")
    for day in sorted(by_day, key=lambda d: datetime.strptime(d, "%d%b%y")):
        fs = by_day[day]
        lines.append(f"## {day} — {len(fs)} flights")
        lines.append("")
        lines.append("```")
        for f in fs:
            arr = f["arr"]
            plus = "+1" if arr.date() > f["dep"].date() else ""
            mark = "*" if f["unobs"] else ("≈" if f["est"] else "")
            lines.append(f"{day}  {f['fn']} {f['origin']}{f['dep']:%H%M} – "
                         f"{arr:%H%M}{plus}{f['dest']}{mark}")
        lines.append("```")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="zip archive or folder of CSVs")
    ap.add_argument("--month", default="auto",
                    help="local departure month, YYYY-MM, or auto (the latest month in the data)")
    ap.add_argument("-o", "--out", help="write the log here")
    ap.add_argument("--csv", dest="csv_out", help="also write a per-flight table")
    a = ap.parse_args()

    flights, skipped = build(a.src, a.month)
    if a.month == "auto" and flights:
        seen = sorted({f["dep"].strftime("%Y-%m") for f in flights})
        a.month = seen[-1]
        flights = [f for f in flights if f["dep"].strftime("%Y-%m") == a.month]
        print(f"  auto: {len(seen)} departure month(s) in the data — {', '.join(seen)} — "
              f"building {a.month} ({len(flights)} flights)")
    if not flights:
        print(f"error: no flights found for {a.month}", file=sys.stderr)
        return 1
    text = render(flights, a.month)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)

    days = defaultdict(int)
    for f in flights:
        days[f["dep"].strftime("%d%b%y").upper()] += 1
    print(f"\n{len(flights)} flights over {len(days)} day(s); "
          f"{sum(f['est'] for f in flights)} with an unobserved take-off, "
          f"{sum(f['unobs'] for f in flights)} with an unobserved landing", file=sys.stderr)
    print("  " + ", ".join(f"{d}:{n}" for d, n in sorted(days.items(),
          key=lambda x: datetime.strptime(x[0], '%d%b%y'))), file=sys.stderr)
    if skipped:
        print(f"  {len(skipped)} track(s) skipped: {', '.join(n for n, _ in skipped[:5])}",
              file=sys.stderr)

    if a.csv_out:
        with open(a.csv_out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["flight", "date", "origin", "takeoff_local", "arrival_local", "dest",
                        "next_day", "takeoff_estimated", "landing_unobserved",
                        "takeoff_utc", "landing_utc", "air_minutes", "fixes", "source_file",
                        "origin_miss_nm", "dest_miss_nm"])
            for f in flights:
                w.writerow([f["fn"], f["dep"].strftime("%d%b%y").upper(), f["origin"],
                            f["dep"].strftime("%H%M"), f["arr"].strftime("%H%M"), f["dest"],
                            "Y" if f["arr"].date() > f["dep"].date() else "",
                            "Y" if f["est"] else "", "Y" if f["unobs"] else "",
                            datetime.fromtimestamp(f["t_off_utc"], timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
                            datetime.fromtimestamp(f["t_land_utc"], timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
                            round(f["dur"]), f["n"], f["name"],
                            round(f["o_miss"], 1), round(f["d_miss"], 1)])
        print(f"wrote {a.csv_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
