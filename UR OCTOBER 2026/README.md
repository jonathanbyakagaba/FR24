# UR OCTOBER 2026 — dated Uganda Airlines (UR) tracks

**State (checked 2026-10-20):**

* Top-level `FR data.zip` now holds **1,133 unique UR+non-UR dated
  tracks** (sha256 `9590df76…`). The export the user placed on `main`
  (`work/FR data.zip`, 2026-10-22) was again a strict superset: **25
  new tracks, none lost** — 17 filling the afternoon/evening of
  **18 Oct** and 8 on the morning of **19 Oct**.
* This folder's `FR data.zip` was rebuilt from that archive: **385 UR
  tracks, 1–19 Oct** (sha256 `35457367…`), and every file derived from
  the tracks was regenerated (`2026-10-21`): flights, tails from the
  FTA plans, runway usage, flight conditions (Entebbe METAR to 19 Oct),
  fleet summary, triangle assignments, punctuality and data gaps.
* **385 logged flights** from **385 tracks · 161,295 fixes**, 1–19 Oct
  2026, across **5 aircraft** (5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL).
  Tails are **plan-assigned** aircraft from the FTA utilization plans,
  not FR24 app pages (no October app captures were available).
* **Schedule/punctuality basis changed to the FTA plans.** The airline's
  utilization plans (fta.ugandairlines.com, 14:00Z snapshots) for
  1–19 Oct were transcribed (`work/fta_oct2026.csv`) — 422 operating
  legs. 377 matched a track; **35 planned legs have no track** and are
  listed in `data_gaps.md`, plus 10 legs scheduled at/after the export's
  last fix (19 Oct 12:02Z) that cannot be verified either way. Route
  inference and tails use the plans — but the plan's assigned aircraft
  can differ from the aircraft the app would have shown.
* **Tails:** 381 of 385 flights carry the plan-assigned aircraft
  (matched on flight number + route; unmatched mainly triangle middle
  sectors and off-pattern legs).
* Remaining known gaps: 40 + 11 legs without tracks (see
  `data_gaps.md`), and NO app/status data for October at all. **No
  tables or figures from the retired frozen build of this folder were
  reused**; everything below was regenerated in the rebuild run.

## Files

| file | rows | what it is |
|---|---:|---|
| `FR data.zip` | 385 tracks | the month's UR track files |
| `manifest.csv` | 385 | one row per track file |
| `flights.csv` | 385 | flight log from the tracks |
| `coverage.csv` | 385 | track duration / completeness per flight |
| `aircraft_config_check.csv`, `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for 1–19 Oct |
| `tails.csv` | 1,120 | includes the September app history (689) + FTA plan rows for Oct |
| `schedule_delays.csv` | 422 legs | FTA plan vs operated, delays, `no_track` flags |
| `punctuality.csv` | 377 | matched flights scored vs plan STD |
| `runway_usage.csv` | 385 | runway in use (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 385 | Entebbe-end weather per flight |
| `flight_log.md` | — | day-by-day narrative log, built from `flights.csv` |
| `od_matrix_october2026.pdf` | 19 matrices | OD matrix per day (1–19 Oct) + diversion findings — the readable version |
| `od_matrix_october2026.xlsx` | 18 + TOTAL + audit | same matrices, Excel (TOTAL sheet + DIVERSION_CHECK) |
| `od_matrix_october2026.csv` | 325 tidy rows | long-format origin/destination/day counts |

`data_gaps.md` (the 35 unmatched legs, day by day), `no_code_tracks.md`,
`aeroroutes_routes.csv` (distinct IATA pairs flown; no segment page data),
`triangle_routes.md` and `triangle_assignments.csv` (UR720/722, UR334,
UR206–209, UR342/343 sectors), `runway_usage.md`, `weather_analysis.md`,
`summaries.txt`. See `SUPPORTING.md` for provenance per file.

## Known data problems

* **No tracks after 19 Oct, 12:02Z (~15:02 EAT).** 10 legs scheduled
  later on the 19th are unverifiable; 35 earlier legs are plain missing
  (see `data_gaps.md`). The recurring holes: the LGW–EBB UR111
  return legs, UR720/UR722/UR334 triangle middle sectors and UR343
  MBA–EBB. The UR520/UR521 Mogadishu return was **CANCELLED** in the
  17 Oct plan, so it is not counted as a recording gap.
* **Plan times are published as-is** — including a couple of internally
  inconsistent STA values; arrival delays inherit that (see
  `schedule_delays.md`).
* Codeshare/"operating" flight numbers never flown under that number
  are excluded (non-scheduled entries in the source plan are dropped).

Provenance and field-level notes are in `SUPPORTING.md`.
