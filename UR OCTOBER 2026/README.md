# UR OCTOBER 2026 — dated Uganda Airlines (UR) tracks

**State (checked 2026-10-20):**

* Top-level `FR data.zip` now holds **1,108 unique UR+non-UR dated
  tracks** (sha256 `ebdff074…`), after removing **35 content-identical
  duplicates** from the 2026-10-20 export (1,143 files). Every earlier
  track survived; the export added **25 tracks**, all Uganda Airlines,
  extending October coverage to **18 Oct** (plus one missing 16 Oct
  UR111 track, which closed the last October gap before the 17th).
* This folder's `FR data.zip` was rebuilt from that archive: **360 UR
  tracks, 1–18 Oct** (sha256 `01781f80…`), and every file derived from
  the tracks was regenerated (`2026-10-20`): flights, tails from the
  FTA plans, runway usage, flight conditions (Entebbe METAR to 19 Oct),
  fleet summary, triangle assignments, punctuality and data gaps.
* **360 logged flights** from **360 tracks · 151,068 fixes**, 1–18 Oct
  2026, across **5 aircraft** (5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL).
  Tails are **plan-assigned** aircraft from the FTA utilization plans,
  not FR24 app pages (no October app captures were available).
* **Schedule/punctuality basis changed to the FTA plans.** The airline's
  utilization plans (fta.ugandairlines.com, 14:00Z snapshots) for
  1–18 Oct were transcribed (`work/fta_oct2026.csv`) — 402 operating
  legs. 351 matched a track; **40 planned legs have no track** and are
  listed in `data_gaps.md`, plus 11 legs scheduled at/after the export's
  last fix (18 Oct 15:19Z) that cannot be verified either way. Route
  inference and tails use the plans — but the plan's assigned aircraft
  can differ from the aircraft the app would have shown.
* **Tails:** 356 of 360 flights carry the plan-assigned aircraft
  (matched on flight number + route; unmatched mainly triangle middle
  sectors and off-pattern legs).
* Remaining known gaps: 40 + 11 legs without tracks (see
  `data_gaps.md`), and NO app/status data for October at all. **No
  tables or figures from the retired frozen build of this folder were
  reused**; everything below was regenerated in the rebuild run.

## Files

| file | rows | what it is |
|---|---:|---|
| `FR data.zip` | 360 tracks | the month's UR track files |
| `manifest.csv` | 360 | one row per track file |
| `flights.csv` | 360 | flight log from the tracks |
| `coverage.csv` | 360 | track duration / completeness per flight |
| `aircraft_config_check.csv`, `fleet_summary.csv` | 5 tails | per-aircraft totals recomputed for 1–18 Oct |
| `tails.csv` | 1,100 | includes the September app history (689) + FTA plan rows for Oct |
| `schedule_delays.csv` | 402 legs | FTA plan vs operated, delays, `no_track` flags |
| `punctuality.csv` | 351 | matched flights scored vs plan STD |
| `runway_usage.csv` | 360 | runway in use (simplified model — see `runway_usage.md`) |
| `flight_conditions.csv` | 360 | Entebbe-end weather per flight |
| `flight_log.md` | — | day-by-day narrative log, built from `flights.csv` |
| `od_matrix_october2026.pdf` | 18 matrices | OD matrix per day (1–18 Oct) + diversion findings — the readable version |
| `od_matrix_october2026.xlsx` | 18 + TOTAL + audit | same matrices, Excel (TOTAL sheet + DIVERSION_CHECK) |
| `od_matrix_october2026.csv` | 306 tidy rows | long-format origin/destination/day counts |

`data_gaps.md` (the 40 unmatched legs, day by day), `no_code_tracks.md`,
`aeroroutes_routes.csv` (distinct IATA pairs flown; no segment page data),
`triangle_routes.md` and `triangle_assignments.csv` (UR720/722, UR334,
UR206–209, UR342/343 sectors), `runway_usage.md`, `weather_analysis.md`,
`summaries.txt`. See `SUPPORTING.md` for provenance per file.

## Known data problems

* **No tracks after 18 Oct, 15:19Z (~18:19 EAT).** 11 legs scheduled
  later on the 18th are unverifiable; 40 earlier legs are plain missing
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
