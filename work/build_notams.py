#!/usr/bin/env python3
"""Split the NOTAM snapshot master (work/notams_snapshot_*.csv) into the
per-month dataset files `UR <MONTH> 2026/notams.csv`.

A NOTAM lands in a month's file if its validity window touches that month.
The master is a SNAPSHOT of currently-active/upcoming notices retrieved on
the date in its filename - expired notices are unrecoverable from it, which
is why each month's notams.md states the snapshot date and the gap.

Rerun after adding a newer snapshot master (update SNAPSHOT below).
"""
import csv
import glob

SNAPSHOT = sorted(glob.glob("work/notams_snapshot_*.csv"))[-1]

MONTHS = {
    "UR SEPTEMBER 2026": ("2026-09-01 00:00", "2026-09-30 23:59"),
    "UR OCTOBER 2026": ("2026-10-01 00:00", "2026-10-31 23:59"),
}

rows = list(csv.DictReader(open(SNAPSHOT)))
for folder, (m0, m1) in MONTHS.items():
    sel = [r for r in rows if r["valid_from_utc"] <= m1 and r["valid_to_utc"] >= m0]
    sel.sort(key=lambda r: (r["icao"], r["valid_from_utc"]))
    with open(f"{folder}/notams.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sel)
    print(folder, "notams.csv:", len(sel), "notices overlap the month")
