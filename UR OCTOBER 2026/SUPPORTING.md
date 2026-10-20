# Supporting files — what each one is, and how to regenerate it

Rewritten 2026-10-20 for the rebuilt folder. The frozen build's pipeline
is not in this repository; the rebuild uses the three scripts now in
`work/`, and this index says honestly which files they produce and which
are carried over.

| file | rows | what it is | rebuild with |
|---|---|---|---|
| `manifest.csv` | 335 | one row per track file in the month zip | `python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"` |
| `flights.csv` | 335 | flight log from the tracks | same — run **before** the FTA join so tails can attach |
| `fleet_summary.csv` | 5 tails | per-aircraft 1–16 Oct totals; meta carried from frozen file | same |
| `triangle_assignments.csv` | 113 | triangle sectors with tails | same (re-run after the FTA join for final tails) |
| `runway_usage.csv` | 335 | runway in use, simplified heading model (legacy header; survey columns blank) | same |
| `date_coverage.md` | — | flights per origin-local date | same |
| `all_flights_aeroroutes.md` | — | every flight grouped by route | same |
| `no_code_tracks.md` | — | tracks without a clean UGD identity | same |
| `tails.csv` | 1052 | tail per flight. Rows ≤2026-09-30: FR24 app pages (frozen). Rows from 2026-10-01: **FTA utilization plan assignments**, appended idempotently; their `app_status` is blank because no October app captures exist | app rows n/a; FTA rows: `python3 work/build_october_fta.py` |
| `schedule_delays.csv` | 354 legs | FTA plan STD/STA vs operated times; basis column reads `FTA utilization plan` — this **replaces** the frozen file's timetable/"usual time" basis for 1–5 Oct | `python3 work/build_october_fta.py` |
| `punctuality.csv` | 326 | matched flights vs plan STD (takeoff-based; includes taxi-out) | same |
| `data_gaps.md` | — | the 28 planned legs with no track, day by day (10 Oct resolved by the 2026-10-19 export) | same |
| `flight_conditions.csv` | 335 | Entebbe-end weather per flight | `python3 work/build_conditions.py "UR OCTOBER 2026"` |
| `weather_analysis.md` | — | weather write-up | written from `flight_conditions.csv` + `metar/` |
| `runway_usage.md` | — | runway write-up and model limits | written from `runway_usage.csv` |
| `triangle_routes.md` | — | triangle write-up | written from `triangle_assignments.csv` |
| `punctuality.md` | — | punctuality basis and scoreboard | written from `punctuality.csv` |
| `schedule_delays.md` | — | schedule-delay basis and caveats | written from `schedule_delays.csv` |
| `app_status.csv` | 705 | app status dots — **the September copy, through 30 Sep; not an October source** | n/a |
| `od_matrix_october2026.pdf` | 16 matrices | OD matrix per day (1–16 Oct) + the diversion audit | `python3 work/build_od_matrix_october.py` (needs reportlab + openpyxl) |
| `od_matrix_october2026.xlsx` | 20 sheets | READ_ME, tidy, TOTAL, one sheet per day, DIVERSION_CHECK | same |
| `od_matrix_october2026.csv` | 282 | tidy OD counts: date, origin, dest, flights | same |
| `metar/` | HUEN, 1–17 Oct | IEM ASOS parsed extract (drct/sknt/gust/vsby/tmpc/alti/wxcodes), 3 part files | see September folder's SUPPORTING.md, same request with October dates |

## Sources

* **FTA utilization plans** — fta.ugandairlines.com, one published/amended
  plan per flight date, transcribed 1–16 Oct to `work/fta_oct2026.csv`
  (local STD/STA at origin/destination; block times). CANCELLED legs are
  excluded from gap counts; overnight legs listed twice in a plan are
  counted once. Plan-assigned aircraft can differ from what flew.
* **Tracks** — the month zip; takeoff/landing from the airborne segments.
* **METAR** — Iowa State IEM ASOS, HUEN only in this pass (parsed fields;
  raw strings re-fetchable from the same request with `data=metar`).
* The **FR24 app** contributed nothing for October: `app_status.csv` here
  ends 30 Sep, and October `tails.csv` rows do not pretend otherwise.
