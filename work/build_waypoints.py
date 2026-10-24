#!/usr/bin/env python3
"""Classify the user-supplied East African waypoint list and write
`waypoints.csv` into both month folders.

Source: work/East African FIR.csv - verbatim copy of the file supplied
2026-10-21 (536 rows: type,latitude,longitude,altitude__m_,name,desc_,
overfly). This script only adds a `kind` classification and tidy column
names; coordinates and names are passed through untouched.

Kind rules (by name shape, documented in waypoints.md):
  5 letters                -> fix       (ICAO five-letter name-code)
  N/S/E/W + 4 digits etc.  -> coord_fix (latitude/longitude-named point)
  1-3 characters           -> navaid    (NDB/VOR ident: NN, EM, PB, ...)
  anything else (4 chars)  -> location  (ICAO aerodrome/location code)
"""
import csv
import re
import pathlib

SRC = pathlib.Path("work/East African FIR.csv")
FOLDERS = ["UR SEPTEMBER 2026", "UR OCTOBER 2026"]


def kind(name):
    if re.fullmatch(r"[A-Z]{5}", name):
        return "fix"
    if re.fullmatch(r"([NSEW]\d{4}|\d{4}[NSEW])", name):
        return "coord_fix"
    if len(name) <= 3:
        return "navaid"
    return "location"


rows = []
for r in csv.DictReader(open(SRC, encoding="utf-8-sig")):
    rows.append({
        "name": r["name"],
        "kind": kind(r["name"]),
        "latitude": r["latitude"],
        "longitude": r["longitude"],
        "altitude_m": r["altitude__m_"],
        "source": "user-supplied 'East African FIR.csv' 2026-10-21 (work/East African FIR.csv)",
    })

for folder in FOLDERS:
    out = pathlib.Path(folder) / "waypoints.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(out, len(rows), "waypoints")

from collections import Counter
print(Counter(r["kind"] for r in rows))
