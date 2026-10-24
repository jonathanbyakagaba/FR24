# UR OCTOBER 2026 — dated Uganda Airlines (UR) tracks

**State (checked 2026-10-23):**

* Top-level `FR data.zip` now holds **1,239 unique UR+non-UR dated
  tracks** (sha256 `b4e9df0f…`). The fresh export the user uploaded on
  2026-10-23 (commit `4947071`) was again a superset — **62 new
  tracks, none lost** — extending October coverage through **22 Oct**
  and closing 6 straggler flights from 3–18 Oct. Together with the 44
  FR24-playback recoveries of the same day (FTA legs no export had
  contained), everything was merged with
  `work/build_month_zips.py --force` (verified additions-only).
* This folder's `FR data.zip` was rebuilt from that archive: **473 UR
  tracks, 1–22 Oct** (sha256 `11153302…`), and every file derived from
  the tracks was regenerated (`2026-10-23`): flights, tails from the
  FTA plans, runway usage, flight conditions (Entebbe METAR to 22 Oct),
  fleet summary, triangle assignments, punctuality and data gaps.
* **473 logged flights** from **473 tracks · 194,656 fixes**, 1–22 Oct
  2026, across **5 aircraft** (5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL).
  Tails are **plan-assigned** aircraft from the FTA utilization plans,
  not FR24 app pages (no October app captures were available).
* **Schedule/punctuality basis changed to the FTA plans.** The airline's
  utilization plans (fta.ugandairlines.com, 14:00Z snapshots) for
  1–22 Oct were transcribed (`work/fta_oct2026.csv`) — 480 operating
  legs. 458 matched a track; of the **22 planned legs without a track,
  17 did not operate**, 2 operated with tracks the join's window
  missed, and 3 operated but are missing from every export so far
  (verified against FR24's flight lists on 2026-10-23 — see
  `data_gaps.md`). 28 of the month's missing tracks were recovered
  from FR24 playback the same day. Route
  inference and tails use the plans — but the plan's assigned aircraft
  can differ from the aircraft the app would have shown.
* **Tails:** 468 of 473 flights carry the plan-assigned aircraft
  (matched on flight number + route; unmatched mainly triangle middle
  sectors and off-pattern legs).
* Remaining known gaps: 3 operated flights whose tracks no export
  contains yet (downloadable, see `data_gaps.md`); every other
  no-track plan leg is verified not-operated or accounted for. NO app/status data for
  October at all. **No
  tables or figures from the retired frozen build of this folder were
  reused**; everything below was regenerated in the rebuild run.

## Files

| file | rows | what it is |
|---|---:|---|
| `FR data.zip` | 473 tracks | the month's UR track files |
| `manifest.csv` | 473 | one row per track file |
| `flights.csv` | 473 | flight log from the tracks |
| `coverage.csv` | 473 | track duration / completeness per flight |
| `aircraft_config_check.csv`, `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for 1–22 Oct |
| `tails.csv` | 1,178 | includes the September app history (689) + FTA plan rows for Oct |
| `schedule_delays.csv` | 480 legs | FTA plan vs operated, delays, `no_track` flags |
| `punctuality.csv` | 458 | matched flights scored vs plan STD |
| `runway_usage.csv` | 473 | runway in use (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 473 | Entebbe-end weather per flight |
| `od_matrix_october2026.pdf` | 22 matrices | OD matrix per day (1–22 Oct) + diversion findings — the readable version |
| `od_matrix_october2026.xlsx` | 26 sheets | READ_ME, tidy, TOTAL, one sheet per day, DIVERSION_CHECK |
| `od_matrix_october2026.csv` | 397 tidy rows | long-format origin/destination/day counts |

`data_gaps.md` (the 22 no-track legs classified, day by day), `no_code_tracks.md`,
`all_flights_aeroroutes.md`, `date_coverage.md`,
`triangle_routes.md` and `triangle_assignments.csv` (UR720/722, UR334,
UR206–209, UR342/343 sectors), `runway_usage.md`, `weather_analysis.md`.
See `SUPPORTING.md` for provenance per file.

## Known data problems

* **Track coverage now ends 2026-10-22, 22:04Z.** Every 1–22 Oct
  plan leg without a track was classified against FR24's flight
  lists on 2026-10-23 (`work/classify_gaps.py`): 17 **did not
  operate** (mostly UR111 LGW–EBB paper legs — the service flies
  every 2–3 days, not near-daily as planned), 2 operated with
  tracks outside the join's time window, and 3 operated but are
  missing from every export so far (UR711/UR322 of 21 Oct, UR902 of
  22 Oct → `work/targets_uptodate.csv`). The UR520/UR521 Mogadishu
  return was **CANCELLED** in the 17 Oct plan, so it is not counted
  as a gap either. The plan can also understate: the 22 Oct UR722X
  rotation was filed NON_SCHEDULED and operated anyway, and 21
  Oct's UR711 diverted JNB→HRE mid-plan (see `data_gaps.md`).
* **Plan times are published as-is** — including a couple of internally
  inconsistent STA values; arrival delays inherit that (see
  `schedule_delays.md`).
* Codeshare/"operating" flight numbers never flown under that number
  are excluded (non-scheduled entries in the source plan are dropped).

Provenance and field-level notes are in `SUPPORTING.md`.
