# 2026-09 — closed flight log and track archive

Frozen **2026-10-05** from the build of that name. This folder is a snapshot: nothing here is regenerated when a new export arrives, and the top level of the repository now describes the month being collected. The rule used throughout: **a flight belongs to the month its departure falls in, local time** — so a leg that departs 2026-09-30 and lands on the 1st of the next month is counted here, and a track that starts in this month is a track of this month even if it ends outside it.

* **610 logged flights**, every one dated in 2026-09.
* **802 tracks · 334,309 fixes** in the archive zip: **625 in 2026-09**, the rest 2026-02 ×5, 2026-03 ×80, 2026-04 ×2, 2026-07 ×2, 2026-08 ×20, 2026-10 ×56 and 4 more — the archive is cumulative, so earlier months stay in it and nothing here was pruned to fit the calendar.
* **1 track crosses this month's boundary**: `UR430-41e8fb3a.csv` (2026-09-30 → 2026-10-01). It is stored whole — one track is never split across two zips.
* `tails.csv` rows reach **2026-07 → 2026-09**: the per-tail app pages are rolling history rather than a calendar month, so a closed month keeps whatever the pages held on the day it was captured. Rows outside this month are the older tail-end of those pages, not contamination.

## What is in this folder

| file | size | rows |
|---|---|---|
| `SUPPORTING.md` | 5 KB | 54 lines |
| `UR September flights.zip` | 4696 KB | — |
| `all_flights_aeroroutes.md` | 23 KB | 766 lines |
| `app_status.csv` | 77 KB | 705 |
| `data_gaps.md` | 13 KB | 230 lines |
| `date_coverage.md` | 13 KB | 269 lines |
| `fleet_summary.csv` | 1 KB | 5 |
| `flight_conditions.csv` | 85 KB | 610 |
| `flights.csv` | 63 KB | 610 |
| `manifest.csv` | 71 KB | 802 |
| `no_code_tracks.md` | 6 KB | 81 lines |
| `punctuality.csv` | 85 KB | 610 |
| `punctuality.md` | 2 KB | 43 lines |
| `runway_usage.csv` | 233 KB | 802 |
| `runway_usage.md` | 25 KB | 354 lines |
| `tails.csv` | 40 KB | 701 |
| `triangle_assignments.csv` | 2 KB | 47 |
| `triangle_routes.md` | 9 KB | 132 lines |
| `weather_analysis.md` | 5 KB | 91 lines |

## Verifying the freeze

`FR data.zip` sha256 `8ccc910d92760d733fcc0aafc89833266e03658945da7cd3c3b935aa2d2b9d47`.
It differs from the top-level archive, which has moved on since this month closed: this copy is the one that matches the tables beside it.

`reference/` and `metar/` are not duplicated here: they are shared lookups described by the top-level README, and the weather this month was measured against is the month-stamped file named in `flight_conditions.csv`'s own rebuild line.

## How this folder was made

```
python3 work/close_month.py 2026-09
```

Re-running it with `--force` re-freezes from the current build, which is only correct if the build still holds this month's log.

