# 2026-10 — Uganda Airlines flight log and track archive (rebuilt 2026-10-20)

**Rebuilt 2026-10-20.** Every derived file in this folder was regenerated
against the current month zip (`FR data.zip` here, replaced 2026-10-19
with the month's UR flights). Reproducible from the repository:

```
python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"
python3 work/build_october_fta.py
python3 work/build_conditions.py "UR OCTOBER 2026"
```

The rule used throughout: **a flight belongs to the month its departure
falls in, local time at the origin**; a track is stored whole.

* **317 logged flights** from **317 tracks · 131,192 fixes**, 1–16 Oct
  (last fix 17 Oct 00:17 UTC — an inbound still airborne at export).
  `FR data.zip` sha256
  `e7f92fe68a65bc567eb7d4ef32930b6d661fb05c87a97cb3c68d4c155877ce08`.
* **Schedule cross-check (new basis):** the FTA utilization plans for
  1–16 Oct were transcribed (`work/fta_oct2026.csv`) — 354 operating legs.
  306 matched a track; **48 planned legs have no track** and are listed in
  `data_gaps.md`. `schedule_delays.csv` and `punctuality.csv` are scored
  against the plan's STD/STA, *not* the frozen build's "usual time"
  baseline. Departure delay here includes taxi-out (actual = takeoff).
* **Tails:** 312 of 317 flights carry the plan-assigned aircraft
  (`tails.csv` rows from 2026-10-01 are FTA-based; its September history
  rows are app-based). Two aircraft (5X-KNP, 5X-CRN) were grounded all
  period.
* **Weather:** `metar/` holds the IEM ASOS extract for Entebbe (HUEN),
  1–17 Oct; `flight_conditions.csv` rebuilt from it (Entebbe end only).
* **One file is deliberately stale:** `app_status.csv` is the September
  copy (through 30 Sep) — no October FR24-app captures were available, so
  October app statuses are blank throughout rather than invented.

## What is in this folder

| file | rows | what it is |
|---|---|---|
| `FR data.zip` | 317 tracks | the month's UR track files |
| `manifest.csv` | 317 | one row per track file |
| `flights.csv` | 317 | flight log from the tracks |
| `tails.csv` | 1052 (701 Sep history + 351 Oct) | tail per flight: app-based ≤30 Sep, FTA-plan-based from 1 Oct |
| `app_status.csv` | 705 | app status dots — **September copy, through 30 Sep** |
| `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for 1–16 Oct |
| `triangle_assignments.csv` | 108 sectors | triangle sectors with plan/confirmed tails |
| `schedule_delays.csv` | 354 legs | FTA plan vs operated, delays, `no_track` flags |
| `punctuality.csv` | 306 | matched flights scored vs plan STD |
| `runway_usage.csv` | 317 | runway in use (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 317 | Entebbe-end weather per flight |
| `metar/` | 3 part files | IEM ASOS parsed extract, HUEN, 1–17 Oct |

Write-ups: `all_flights_aeroroutes.md`, `date_coverage.md`,
`data_gaps.md` (the 48 unmatched legs, day by day), `no_code_tracks.md`,
`triangle_routes.md`, `runway_usage.md`, `weather_analysis.md`,
`punctuality.md`, `schedule_delays.md`.

## Verifying

* This folder's `FR data.zip`: sha256 `e7f92fe68a65bc567eb7d4ef32930b6d661fb05c87a97cb3c68d4c155877ce08`
* The top-level `FR data.zip` it was split from (1,065 tracks, deduplicated): sha256 `0e7cacc3ec4ea0dfeba2e42a7b443948ceb81ff00e632f6ae62be06e514563d3`

## The one soft spot

10 Oct: the plan published a full 20-leg programme and exactly one track
survived (an inbound that operated to the next morning's plan). Whether
that day's export failed or the programme was cut after publication,
these tables show what was recorded — not what flew. See `data_gaps.md`.
