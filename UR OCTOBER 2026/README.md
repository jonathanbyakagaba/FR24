# 2026-10 — Uganda Airlines flight log and track archive (rebuilt 2026-10-20)

**Rebuilt 2026-10-20; refreshed the same day from the main-repo update**
(`FR data.zip` upload of 2026-10-19, merged into this branch). Every
derived file in this folder was regenerated against the current month
zip. Reproducible from the repository:

```
python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"
python3 work/build_october_fta.py
python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"
python3 work/build_conditions.py "UR OCTOBER 2026"
python3 work/build_od_matrix_october.py
```

The rule used throughout: **a flight belongs to the month its departure
falls in, local time at the origin**; a track is stored whole.

* **335 logged flights** from **335 tracks · 139,526 fixes**, 1–16 Oct
  (last fix 17 Oct 00:17 UTC — an inbound still airborne at export).
  `FR data.zip` sha256
  `a6add0e29b677720b997f762c7d1677c2aade0d2b3676f3eac5ed5c54803fd29`.
  The main-repo update added 18 tracks (17 dated 10 Oct plus the UR111
  inbound of 9 Oct) over the previous export — 10 Oct is no longer a
  recording blackout (see *The 10 Oct story* below).
* **Schedule cross-check (new basis):** the FTA utilization plans for
  1–16 Oct were transcribed (`work/fta_oct2026.csv`) — 354 operating legs.
  324 matched a track; **30 planned legs have no track** and are listed in
  `data_gaps.md`. `schedule_delays.csv` and `punctuality.csv` are scored
  against the plan's STD/STA, *not* the frozen build's "usual time"
  baseline. Departure delay here includes taxi-out (actual = takeoff).
* **Tails:** 330 of 335 flights carry the plan-assigned aircraft
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
| `FR data.zip` | 335 tracks | the month's UR track files |
| `manifest.csv` | 335 | one row per track file |
| `flights.csv` | 335 | flight log from the tracks |
| `tails.csv` | 1052 (701 Sep history + 351 Oct) | tail per flight: app-based ≤30 Sep, FTA-plan-based from 1 Oct |
| `app_status.csv` | 705 | app status dots — **September copy, through 30 Sep** |
| `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for 1–16 Oct |
| `triangle_assignments.csv` | 113 sectors | triangle sectors with plan/confirmed tails |
| `schedule_delays.csv` | 354 legs | FTA plan vs operated, delays, `no_track` flags |
| `punctuality.csv` | 324 | matched flights scored vs plan STD |
| `runway_usage.csv` | 335 | runway in use (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 335 | Entebbe-end weather per flight |
| `metar/` | 3 part files | IEM ASOS parsed extract, HUEN, 1–17 Oct |
| `od_matrix_october2026.pdf` | 16 matrices | OD matrix per day (1–16 Oct) + diversion findings — the readable version |
| `od_matrix_october2026.xlsx` | 20 sheets | same matrices per day + TOTAL + tidy + DIVERSION_CHECK, for analysis |
| `od_matrix_october2026.csv` | 282 rows | tidy OD counts (date, origin, dest, flights) |

Write-ups: `all_flights_aeroroutes.md`, `date_coverage.md`,
`data_gaps.md` (the 30 unmatched legs, day by day), `no_code_tracks.md`,
`triangle_routes.md`, `runway_usage.md`, `weather_analysis.md`,
`punctuality.md`, `schedule_delays.md`.

## Verifying

* This folder's `FR data.zip`: sha256 `a6add0e29b677720b997f762c7d1677c2aade0d2b3676f3eac5ed5c54803fd29`
* The top-level `FR data.zip` it was split from (1,083 tracks, deduplicated): sha256 `a60990fd14e24976b1d84e0b461d3e6def77fe2b9cfbeffeb92f5278e827ffff`

## The 10 Oct story

In the previous export, 10 Oct looked like a total recording blackout:
a full 20-leg programme and one surviving track. The main-repo export
merged into this branch on 2026-10-20 contained 17 tracks dated 10 Oct
(plus the UR111 inbound that departed London on 9 Oct), and the day now
matches the plan like any other (17 sectors in the OD matrix). The
remaining 30 unmatched legs are listed in `data_gaps.md`; the recurring
patterns are triangle middle sectors and the UR111 London return.
