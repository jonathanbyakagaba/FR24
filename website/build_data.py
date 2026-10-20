#!/usr/bin/env python3
"""Build website/data.json from the September/October 2026 datasets.

Inputs (repo tree, nothing downloaded):
  UR SEPTEMBER 2026/flights.csv + UR September flights.zip + punctuality.csv
  UR OCTOBER  2026/flights.csv + FR data.zip            + punctuality.csv
  both months' flight_conditions.csv and notams.csv
  airport coordinates from work/rebuild_month.py (AIRPORTS)

Output: website/data.json with airports, per-flight records (incl. a
downsampled flown path from the actual FR24 track), route aggregates,
daily counts and NOTAMs per airport. Rerun after any dataset update:
  python3 website/build_data.py
"""
import csv
import importlib.util
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "data.json"

spec = importlib.util.spec_from_file_location("rebuild_month", ROOT / "work" / "rebuild_month.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)
AIRPORTS = {
    code: {"iata": code, "icao": v[0], "name": v[1], "lat": v[2], "lon": v[3]}
    for code, v in rb.AIRPORTS.items()
}
AIRPORTS.pop("UGHO", None)
AIRPORTS["KBG"] = AIRPORTS.get("KBG") or {"iata": "KBG", "icao": "HKHO",
                                          "name": "Hoima (Kabaale)",
                                          "lat": 1.5639, "lon": 31.3197}

MONTHS = [
    ("September 2026", "2026-09", ROOT / "UR SEPTEMBER 2026", "UR September flights.zip"),
    ("October 2026", "2026-10", ROOT / "UR OCTOBER 2026", "FR data.zip"),
]

MAX_PATH_POINTS = 140


def downsample(points, cap=MAX_PATH_POINTS):
    if len(points) <= cap:
        return points
    step = len(points) / cap
    return [points[int(i * step)] for i in range(cap)] + [points[-1]]


def read_track(zf, by_base, source_file):
    name = by_base.get(source_file)
    if not name:
        return [], None
    pts = []
    callsign = None
    for r in csv.DictReader(zf.read(name).decode("utf-8", "ignore").splitlines()):
        try:
            lat, lon = (float(x) for x in r["Position"].split(","))
            pts.append([round(lat, 5), round(lon, 5),
                        int(float(r["Altitude"] or 0)),
                        int(float(r["Speed"] or 0))])
            callsign = callsign or (r["Callsign"] or "").strip()
        except Exception:
            continue
    return downsample(pts), callsign


def main():
    flights = []
    notams = defaultdict(list)
    used_airports = Counter()

    for label, prefix, folder, zipname in MONTHS:
        zf = zipfile.ZipFile(folder / zipname)
        by_base = {Path(n).name: n for n in zf.namelist() if n.endswith(".csv")}

        punct = {}
        pfile = folder / "punctuality.csv"
        if pfile.exists():
            for r in csv.DictReader(open(pfile)):
                if r.get("source_file"):
                    punct[r["source_file"]] = r

        cond = {}
        cfile = folder / "flight_conditions.csv"
        if cfile.exists():
            for r in csv.DictReader(open(cfile)):
                cond[r["file"]] = r

        nfile = folder / "notams.csv"
        if nfile.exists():
            for r in csv.DictReader(open(nfile)):
                key = "EBB" if r["iata"] == "ENTEBBE FIR" else r["iata"]
                entry_id = (r["icao"], r["notam_id"], r["valid_from_utc"])
                if any((n["icao"], n["id"], n["from"]) == entry_id for n in notams[key]):
                    continue  # overlaps both months - keep once
                notams[key].append({
                    "id": r["notam_id"], "icao": r["icao"],
                    "from": r["valid_from_utc"], "to": r["valid_to_utc"],
                    "schedule": r["schedule"], "category": r["category"],
                    "text": r["text"], "source": r["source"],
                })

        for r in csv.DictReader(open(folder / "flights.csv")):
            dep = datetime.strptime(r["departure_utc"], "%Y-%m-%d %H:%M:%SZ")
            path, callsign = read_track(zf, by_base, r["source_file"])
            p = punct.get(r["source_file"], {})
            c = cond.get(r["source_file"], {})
            f = {
                "id": r["source_file"].replace(".csv", ""),
                "month": label,
                "date": dep.strftime("%Y-%m-%d"),
                "flight": r["flight"].replace("UGD", "UR"),
                "callsign": callsign or r["flight"],
                "origin": r["origin"], "dest": r["dest"],
                "dep_utc": r["departure_utc"], "arr_utc": r["arrival_utc"],
                "air_min": int(r["air_minutes"] or 0),
                "fixes": int(r["fixes"] or 0),
                "tail": p.get("tail", ""),
                "dep_delay": (int(p["dep_delay_min"]) if p.get("dep_delay_min") not in ("", None) else None),
                "arr_delay": (int(p["arr_delay_min"]) if p.get("arr_delay_min") not in ("", None) else None),
                "punctuality": p.get("punctuality", ""),
                "dep_wx": c.get("dep_wx", ""), "arr_wx": c.get("arr_wx", ""),
                "dep_rwy": c.get("dep_rwy", ""), "arr_rwy": c.get("arr_rwy", ""),
                "path": path,
            }
            flights.append(f)
            used_airports[r["origin"]] += 1
            used_airports[r["dest"]] += 1

    flights.sort(key=lambda f: f["dep_utc"])

    airports = []
    for code, a in AIRPORTS.items():
        if used_airports.get(code):
            a = dict(a)
            a["movements"] = used_airports[code]
            a["out"] = sum(1 for f in flights if f["origin"] == code)
            a["in"] = sum(1 for f in flights if f["dest"] == code)
            airports.append(a)

    routes = Counter((f["origin"], f["dest"]) for f in flights)
    route_rows = [{"origin": o, "dest": d, "count": n}
                  for (o, d), n in routes.most_common()]

    daily = Counter(f["date"] for f in flights)
    delays = [f["dep_delay"] for f in flights if f["dep_delay"] is not None]
    punct = Counter(f["punctuality"] for f in flights if f["punctuality"])

    data = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ"),
        "airports": airports,
        "flights": flights,
        "routes": route_rows,
        "daily": [{"date": d, "flights": daily[d]} for d in sorted(daily)],
        "notams": notams,
        "stats": {
            "flights": len(flights),
            "airports": len(airports),
            "routes": len(route_rows),
            "tails": len({f["tail"] for f in flights if f["tail"]}),
            "median_dep_delay": sorted(delays)[len(delays) // 2] if delays else None,
            "punctuality": dict(punct),
            "period": [min(daily), max(daily)] if daily else [],
        },
    }
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size/1e6:.1f} MB): "
          f"{len(flights)} flights, {len(airports)} airports, "
          f"{len(route_rows)} routes, {sum(len(v) for v in notams.values())} NOTAM rows")


if __name__ == "__main__":
    main()
