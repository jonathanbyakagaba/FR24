# Schedule delays — September 2026 (added 2026-10-20)

`schedule_delays.csv` now exists for September, on exactly the same basis
as October's: the **FTA utilization plan** for each day (transcribed to
`work/fta_sep2026.csv` from fta.ugandairlines.com, all 30 day-plans)
joined to the track log by `work/build_september_fta.py`.

The numbers: **660 operating legs** after excluding 14 CANCELLED and 5
NON_SCHEDULED plan rows and counting 6 duplicate listings of one leg
once. **624 matched a track; 36 did not** (listed in `data_gaps.md`).
Those 36 are **not** recording gaps: checked against FR24's per-aircraft
flight lists on 2026-10-23, no aircraft operated them within ±36 h of
the plan — the FTA plans overstate operations (UR111 LGW–EBB is planned
near-daily but flown every 2–3 days). A further 16 legs that had no
track on 2026-10-20 were real flights; their tracks were recovered
from FR24 playback on 2026-10-23, and the fresh `FR data.zip`
export of the same day closed two more September tracks (one a
twice-listed leg, hence 660 legs).

## Scoreboard (takeoff vs scheduled departure, 624 matched legs)

| early | on time (0–15m) | delayed (16–60m) | heavily delayed (>60m) |
|---:|---:|---:|---:|
| 223 | 213 | 156 | 32 |

Median departure delay is **+6 min** — but remember the "actual" is
*takeoff* and STD is off-block, so every figure includes taxi-out
(~15–30 min at Entebbe). On that reading the CRJ fleet (median +1 min
over 452 legs) effectively left the gate on time all month. The widebody
flying is where the lateness lives: A330 (UR110/111/430/431) median
+31 min over 42 legs, the leased A350 (ET-APL) median +19 min over
125 legs with 16 heavily-delayed legs. Worst individual services by
median: UR902 EBB–LOS (+44), UR111 LGW–EBB (+38), UR711 JNB–EBB (+37).

The single worst departure delay: **10 Sep**, when the daytime Dar es
Salaam rotation operated ~11 hours late (UR322 EBB–DAR +669 min — the
track exists, just half a day behind the plan; the matcher allows
+12 h for this reason).

## Caveats

- `punctuality.csv` in this folder is **not** this file's companion: it
  keeps the frozen app-based/usual-time scoring (see `punctuality.md`).
  The FTA-basis punctuality label for each leg is the `punctuality`
  column here.
- Hoima (Kabaale) shuttle legs: the plan calls the field KBG/KGB and the
  flights UR130–UR133; the tracks fly as AF523 to `UGHO` and some sectors
  are recorded as EBB–EBB round trips. Those legs are matched by route
  and time proximity (flagged in `compare_note`) and are the softest
  matches in the file.
- Plan STA is occasionally inconsistent; arrival delays inherit that.
- `op_median_*` columns summarise the same flight's operated departures
  within September only (≥3 legs) — a one-month baseline, not a timetable.
