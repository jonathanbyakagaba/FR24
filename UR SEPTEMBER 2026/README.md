# 2026-09 — Uganda Airlines flight log and track archive (rebuilt 2026-10-20; tracks extended 2026-10-23)

**Rebuilt 2026-10-20.** Every derived file in this folder was regenerated
against the current month zip (the counts-and-checksums pass of 2026-10-19
only replaced the zip; this pass rebuilt the tables). **Extended
2026-10-23:** 16 tracks recovered from FR24 playback and 2 more from the
same day's fresh `FR data.zip` export were merged into
the archives and every table regenerated again (see `data_gaps.md`).
The rebuild is
reproducible from the repository: `python3 work/rebuild_month.py
"UR SEPTEMBER 2026" "UR September flights.zip"` plus
`python3 work/build_conditions.py "UR SEPTEMBER 2026"`.

The rule used throughout: **a flight belongs to the month its departure
falls in, local time at the origin** — a track that starts in September is
a September track even if it ends in October (`UR430-41e8fb3a.csv`,
`UR343-41e94875.csv` land 1 Oct and stay here, whole).

* **640 logged flights** from **640 tracks · 251,752 fixes**, all starting
  in 2026-09. `UR September flights.zip` sha256
  `3cfaf9c75e83429a7e2dc94dea228d72ea9ac4c99f3842403c60083adabce105`.
* The frozen 2026-10-05 log carried 610 of these flights; 609 are
  reproduced here from the same tracks (routes identical, departure times
  to the second for 565 and within ~25 s for the rest). The rebuilt log
  adds the AF523 Hoima/test tracks the frozen log excluded (see
  `no_code_tracks.md`) and drops one 31 Aug sector that predates the
  month.
* `tails.csv` (701 rows, app-based, through 30 Sep) is **unchanged** — it
  was already September-valid. 625 of 640 rebuilt flights match a tail in
  it. `app_status.csv` and `punctuality.csv` likewise keep their frozen,
  app-based content; see `punctuality.md`.
* **Schedule cross-check (added 2026-10-20):** the FTA utilization plans
  for 1–30 Sep were transcribed (`work/fta_sep2026.csv`) — 660 operating
  legs. 624 matched a track; **the 36 legs without a track did not
  operate** (verified against FR24's flight lists on 2026-10-23; see
  `data_gaps.md`). 16 of the month's originally-missing legs were real
  flights whose tracks were recovered from FR24 playback.
  `schedule_delays.csv` scores every leg against the
  plan's STD/STA; departure delay includes taxi-out (actual = takeoff).
* Weather: **new** — `metar/` holds the Iowa State IEM ASOS extract for
  Entebbe (HUEN), 1–30 Sep, and `flight_conditions.csv` /
  `weather_analysis.md` were rebuilt from it. Outstation METARs were not
  retrieved in this pass (the frozen build's 41-station archive is not in
  this repository); the Entebbe end of every flight is covered.

## What is in this folder

| file | rows | what it is |
|---|---|---|
| `UR September flights.zip` | 640 tracks | the month's UR track files |
| `manifest.csv` | 640 | one row per track file in the zip |
| `flights.csv` | 640 | the flight log (takeoff/landing from the tracks) |
| `tails.csv` | 701 | tail per flight from the FR24 app pages (frozen, app-based) |
| `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for September |
| `triangle_assignments.csv` | 237 sectors | triangle/milk-run sectors with tails |
| `runway_usage.csv` | 640 | runway in use per flight (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 640 | Entebbe-end weather per flight from `metar/` |
| `punctuality.csv` | 610 | app status + usual-time delay (frozen basis) |
| `schedule_delays.csv` | 660 legs | FTA plan vs operated, delays, `no_track` flags (added 2026-10-20) |
| `app_status.csv` | 705 | the app status dots underneath `tails.csv`/`punctuality.csv` |
| `metar/` | 5 part files | IEM ASOS parsed extract, HUEN, Sep 2026 |

Write-ups: `all_flights_aeroroutes.md`, `date_coverage.md`,
`data_gaps.md` (the 36 FTA legs verified not operated), `no_code_tracks.md`,
`triangle_routes.md`, `runway_usage.md`, `weather_analysis.md`,
`punctuality.md`, `schedule_delays.md`.

## Provenance and limits

Tracks are the only flight source. Takeoff = first airborne fix, landing =
last airborne fix before touchdown (verified against the frozen log).
`schedule_delays.csv` is FTA-plan-based (added 2026-10-20, one day after
the rest of the rebuild); the plan transcription is
`work/fta_sep2026.csv` and the join is `work/build_september_fta.py`.
