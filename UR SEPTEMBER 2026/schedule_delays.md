# Schedule delays — September 2026 (added 2026-10-20)

`schedule_delays.csv` now exists for September, on exactly the same basis
as October's: the **FTA utilization plan** for each day (transcribed to
`work/fta_sep2026.csv` from fta.ugandairlines.com, all 30 day-plans)
joined to the track log by `work/build_september_fta.py`.

The numbers: **660 operating legs** after excluding 14 CANCELLED and 5
NON_SCHEDULED plan rows and counting 6 duplicate listings of one leg
once. **608 matched a track; 52 did not** (listed in `data_gaps.md` —
UR720 triangle sectors ×12 and the overnight UR111 London return ×11
dominate; they are recording gaps, not cancellations).

## Scoreboard (takeoff vs scheduled departure, 608 matched legs)

| early | on time (0–15m) | delayed (16–60m) | heavily delayed (>60m) |
|---:|---:|---:|---:|
| 217 | 203 | 156 | 32 |

Median departure delay is **+6 min** — but remember the "actual" is
*takeoff* and STD is off-block, so every figure includes taxi-out
(~15–30 min at Entebbe). On that reading the CRJ fleet (median +1 min
over 438 legs) effectively left the gate on time all month. The widebody
flying is where the lateness lives: A330 (UR110/111/430/431) median
+31 min, the leased A350 (ET-APL) median +19 min with 16 heavily-delayed
legs. Worst individual services by median: the Lagos pair UR902/UR903
(+44/+42), UR111 LGW–EBB (+38) and UR711 JNB–EBB (+37).

The single worst day: **10 Sep**, when the daytime Dar es Salaam rotation
(UR322/UR323) operated ~11 hours late (departure delays +669/+666 min —
the tracks exist, just half a day behind the plan; the matcher allows
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
