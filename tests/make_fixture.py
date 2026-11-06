#!/usr/bin/env python3
"""Write a tiny synthetic Flightradar24-style export used by the tests.

This is *not* archive data — it exists only so the pipeline in
``work/fr24_tracks.py`` can be exercised without a real export checked in.
It reproduces the column layout of FR24's playback export:

    Timestamp,UTC,Callsign,Registration,Position,Altitude,Speed,Direction,
    Latitude,Longitude,VerticalRate,Squawk,OnGround,Airport

Run ``python3 tests/make_fixture.py`` to regenerate the CSV.
"""

import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fixtures" / "fr24_2026-06_sample.csv"

EBB = (0.042386, 32.443501)
JNB = (-26.140081, 28.246801)
NBO = (-1.318886, 36.928233)

FLIGHTS = [
    # callsign, registration, origin, destination, departure UTC, block hours
    ("UR713", "5X-NIL", EBB, JNB, datetime(2026, 6, 1, 4, 30, tzinfo=timezone.utc), 4.1),
    ("UR710", "5X-NIL", JNB, EBB, datetime(2026, 6, 1, 10, 10, tzinfo=timezone.utc), 4.0),
    ("UR201", "5X-KOB", EBB, NBO, datetime(2026, 6, 2, 3, 30, tzinfo=timezone.utc), 1.1),
    ("UR202", "5X-KOB", NBO, EBB, datetime(2026, 6, 2, 6, 15, tzinfo=timezone.utc), 1.1),
]


def interpolate(a, b, fraction):
    return (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for callsign, registration, origin, destination, departure, block in FLIGHTS:
        steps = 40
        for i in range(steps + 1):
            fraction = i / steps
            when = departure + timedelta(hours=block * fraction)
            lat, lon = interpolate(origin, destination, fraction)
            if i == 0 or i == steps:
                altitude, on_ground = 0, True
            else:
                climb = math.sin(math.pi * fraction)
                altitude = round(3000 + 32000 * climb)
                on_ground = False
            rows.append([
                int(when.timestamp()), when.strftime("%Y-%m-%d %H:%M:%S"),
                callsign, registration, f"{lat:.5f},{lon:.5f}", altitude, 470, 210,
                f"{lat:.5f}", f"{lon:.5f}", 0, "2000", str(on_ground).lower(),
                "",
            ])
    rows.sort(key=lambda r: r[0])
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Timestamp", "UTC", "Callsign", "Registration", "Position",
                         "Altitude", "Speed", "Direction", "Latitude", "Longitude",
                         "VerticalRate", "Squawk", "OnGround", "Airport"])
        writer.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
