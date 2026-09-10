# FR24 — Uganda Airlines flight log & telemetry analysis

Published flight log in AeroRoutes notation, plus the telemetry pipeline that produces it.

**Current coverage: 173 flights, 01SEP26 – 09SEP26.** (Earlier dates have been dropped.)

## Start here

| File | What it is |
|---|---|
| `all_flights_aeroroutes.md` | **The flight log.** One line per flight: `DDMMMYY  UGD### ORIGhhmm – hhmm[+1]DEST`, times **local at each end**, dates are **local departure dates**. `*` = landing unobserved, `≈` = estimated take-off. |
| `output/report.html` | Interactive dashboard — network map of every recorded track, per-leg altitude/speed profile, timeline, rotations, data-quality register. Self-contained; open it in a browser. |
| `output/report.md` | The same findings as plain markdown. |
| `output/flights.csv` | **Master table**: one row per leg with origin/destination, take-off/landing, block and air time, track and great-circle distance, cruise altitude and speed, climb/descent rates, feed continuity. |

## Repository layout

```
all_flights_aeroroutes.md    the published log
uploads/                     raw telemetry input, one CSV per flown leg
output/                      generated tables + dashboard
cache/                       offline basemap used by the dashboard
*.py                         the pipeline
airports.csv                 airport reference (IATA/ICAO/coords)
```

## Regenerating everything

Nothing is hand-edited — all outputs are rebuilt from the raw telemetry:

```bash
python3 ingest.py --run                  # pull in new CSVs (from uploads/ or a zip), rebuild
# or, if the new files are already in uploads/:
python3 analyze_flights.py && python3 build_report.py && python3 merge_aeroroutes.py
```

`merge_aeroroutes.py` folds newly analysed legs into the log, skipping duplicates and keeping each
day's lines in take-off order. It drops anything before the cutoff (default `01SEP26`); change it with
`--since 01AUG26` or the `SINCE` environment variable.

## Adding new flights

Put the new leg CSVs in `uploads/` (one file per leg, columns `Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction`),
then run the three commands above. `ingest.py` also accepts a folder or a zip archive — renamed to
`.txt` or anything else is fine, since it detects archives by content, not by extension.

## Method

* Positions are WGS-84; altitude in feet; speed is **ground** speed in knots; direction is true track.
* Endpoints are matched to the nearest airport in `airports.csv`, reporting the miss distance.
* Take-off/landing = first/last fix above 100 ft; block time = first fix to last fix.
* Ground-track distance excludes segments implying more than 700 kt.
* Cruise = median of fixes within 500 ft of the leg maximum; vertical rates use sample pairs ≤ 30 s apart.
* Log times are converted from UTC to local using fixed September offsets: EBB/NBO/DAR/ZNZ/MBA
  UTC+3, JUB/BJM/JNB/HRE/LUN UTC+2, LGW UTC+1 (BST), BOM UTC+5:30.

## Known data limitations

* **Sparse reporting on remote legs.** Sampling is 3–6 s in the terminal area and ~31 s in cruise, but
  drops to roughly one report every 25–45 minutes over remote airspace (LGW–EBB, EBB–BOM, EBB–JNB/
  JNB–EBB, EBB–HRE). Those hours are reconstructed by joining isolated fixes — fine for times and
  distances, not for en-route winds or fuel analysis.
* Two lines in the log read `UG342`/`UG343` rather than `UGD…` (as received).
