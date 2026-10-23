# UR OCTOBER 2026 — dated Uganda Airlines (UR) tracks

**State (checked 2026-10-23):**

* Top-level `FR data.zip` now holds **1,177 unique UR+non-UR dated
  tracks** (sha256 `0e001736…`). The export the user placed on `main`
  (`work/FR data.zip`, 2026-10-22) was again a strict superset: **25
  new tracks, none lost** — 17 filling the afternoon/evening of
  **18 Oct** and 8 on the morning of **19 Oct**. On 2026-10-23 a
  further **44 tracks were recovered from FR24 playback** (16 for
  September, 28 for October — FTA legs that no export had contained)
  and merged with `work/build_month_zips.py`.
* This folder's `FR data.zip` was rebuilt from that archive: **413 UR
  tracks, 1–19 Oct** (sha256 `297f803c…`), and every file derived from
  the tracks was regenerated (`2026-10-21`): flights, tails from the
  FTA plans, runway usage, flight conditions (Entebbe METAR to 19 Oct),
  fleet summary, triangle assignments, punctuality and data gaps.
* **413 logged flights** from **413 tracks · 170,790 fixes**, 1–19 Oct
  2026, across **5 aircraft** (5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL).
  Tails are **plan-assigned** aircraft from the FTA utilization plans,
  not FR24 app pages (no October app captures were available).
* **Schedule/punctuality basis changed to the FTA plans.** The airline's
  utilization plans (fta.ugandairlines.com, 14:00Z snapshots) for
  1–19 Oct were transcribed (`work/fta_oct2026.csv`) — 422 operating
  legs. 405 matched a track; **the 17 planned legs without a track did
  not operate** — verified against FR24's per-aircraft flight lists on
  2026-10-23 (see `data_gaps.md`). 28 of the month's missing tracks
  were recovered from FR24 playback the same day. Route
  inference and tails use the plans — but the plan's assigned aircraft
  can differ from the aircraft the app would have shown.
* **Tails:** 409 of 413 flights carry the plan-assigned aircraft
  (matched on flight number + route; unmatched mainly triangle middle
  sectors and off-pattern legs).
* Remaining known gaps: none unexplained — every no-track plan leg is
  verified not-operated (see `data_gaps.md`). NO app/status data for
  October at all. **No
  tables or figures from the retired frozen build of this folder were
  reused**; everything below was regenerated in the rebuild run.

## Files

| file | rows | what it is |
|---|---:|---|
| `FR data.zip` | 413 tracks | the month's UR track files |
| `manifest.csv` | 413 | one row per track file |
| `flights.csv` | 413 | flight log from the tracks |
| `coverage.csv` | 413 | track duration / completeness per flight |
| `aircraft_config_check.csv`, `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for 1–19 Oct |
| `tails.csv` | 1,120 | includes the September app history (689) + FTA plan rows for Oct |
| `schedule_delays.csv` | 422 legs | FTA plan vs operated, delays, `no_track` flags |
| `punctuality.csv` | 405 | matched flights scored vs plan STD |
| `runway_usage.csv` | 413 | runway in use (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 413 | Entebbe-end weather per flight |
| `od_matrix_october2026.pdf` | 19 matrices | OD matrix per day (1–19 Oct) + diversion findings — the readable version |
| `od_matrix_october2026.xlsx` | 23 sheets | READ_ME, tidy, TOTAL, one sheet per day, DIVERSION_CHECK |
| `od_matrix_october2026.csv` | 348 tidy rows | long-format origin/destination/day counts |

`data_gaps.md` (the 17 legs verified not operated, day by day), `no_code_tracks.md`,
`all_flights_aeroroutes.md`, `date_coverage.md`,
`triangle_routes.md` and `triangle_assignments.csv` (UR720/722, UR334,
UR206–209, UR342/343 sectors), `runway_usage.md`, `weather_analysis.md`.
See `SUPPORTING.md` for provenance per file.

## Known data problems

* **Track coverage now ends 2026-10-20, 00:33Z** (the last recovered
  arrival). Every 1–19 Oct plan leg without a track was verified
  against FR24's flight lists on 2026-10-23: all 17 **did not
  operate** — mostly UR111 LGW–EBB paper legs (the service flies
  every 2–3 days, not near-daily as planned). The UR520/UR521
  Mogadishu return was **CANCELLED** in the 17 Oct plan, so it is
  not counted as a gap either.
* **Plan times are published as-is** — including a couple of internally
  inconsistent STA values; arrival delays inherit that (see
  `schedule_delays.md`).
* Codeshare/"operating" flight numbers never flown under that number
  are excluded (non-scheduled entries in the source plan are dropped).

Provenance and field-level notes are in `SUPPORTING.md`.
