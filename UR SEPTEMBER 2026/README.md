# 2026-09 — Uganda Airlines flight log and track archive (rebuilt 2026-10-20)

**Rebuilt 2026-10-20.** Every derived file in this folder was regenerated
against the current month zip (the counts-and-checksums pass of 2026-10-19
only replaced the zip; this pass rebuilt the tables). The rebuild is
reproducible from the repository: `python3 work/rebuild_month.py
"UR SEPTEMBER 2026" "UR September flights.zip"` plus
`python3 work/build_conditions.py "UR SEPTEMBER 2026"`.

The rule used throughout: **a flight belongs to the month its departure
falls in, local time at the origin** — a track that starts in September is
a September track even if it ends in October (`UR430-41e8fb3a.csv`,
`UR343-41e94875.csv` land 1 Oct and stay here, whole).

* **622 logged flights** from **622 tracks · 245,957 fixes**, all starting
  in 2026-09. `UR September flights.zip` sha256
  `e47228acad61a838b156257a273f219f3547518f24bd89352291c31abfd595e2`.
* The frozen 2026-10-05 log carried 610 of these flights; 609 are
  reproduced here from the same tracks (routes identical, departure times
  to the second for 565 and within ~25 s for the rest). The rebuilt log
  adds the AF523 Hoima/test tracks the frozen log excluded (see
  `no_code_tracks.md`) and drops one 31 Aug sector that predates the
  month.
* `tails.csv` (701 rows, app-based, through 30 Sep) is **unchanged** — it
  was already September-valid. 607 of 622 rebuilt flights match a tail in
  it. `app_status.csv` and `punctuality.csv` likewise keep their frozen,
  app-based content; see `punctuality.md`.
* Weather: **new** — `metar/` holds the Iowa State IEM ASOS extract for
  Entebbe (HUEN), 1–30 Sep, and `flight_conditions.csv` /
  `weather_analysis.md` were rebuilt from it. Outstation METARs were not
  retrieved in this pass (the frozen build's 41-station archive is not in
  this repository); the Entebbe end of every flight is covered.

## What is in this folder

| file | rows | what it is |
|---|---|---|
| `UR September flights.zip` | 622 tracks | the month's UR track files |
| `manifest.csv` | 622 | one row per track file in the zip |
| `flights.csv` | 622 | the flight log (takeoff/landing from the tracks) |
| `tails.csv` | 701 | tail per flight from the FR24 app pages (frozen, app-based) |
| `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for September |
| `triangle_assignments.csv` | 225 sectors | triangle/milk-run sectors with tails |
| `runway_usage.csv` | 622 | runway in use per flight (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 622 | Entebbe-end weather per flight from `metar/` |
| `punctuality.csv` | 610 | app status + usual-time delay (frozen basis) |
| `app_status.csv` | 705 | the app status dots underneath `tails.csv`/`punctuality.csv` |
| `metar/` | 5 part files | IEM ASOS parsed extract, HUEN, Sep 2026 |

Write-ups: `all_flights_aeroroutes.md`, `date_coverage.md`,
`data_gaps.md`, `no_code_tracks.md`, `triangle_routes.md`,
`runway_usage.md`, `weather_analysis.md`, `punctuality.md`,
`schedule_delays.md` (why September has no schedule-basis file).

## Provenance and limits

Tracks are the only flight source. Takeoff = first airborne fix, landing =
last airborne fix before touchdown (verified against the frozen log).
`schedule_delays.csv` is **absent** for September: no timetable baseline
was transcribed (October's folder shows the FTA-based version). September
was not cross-checked against the FTA plans in this rebuild — see
`data_gaps.md` for exactly what that does and doesn't claim.
