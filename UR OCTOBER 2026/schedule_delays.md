# Schedule delays — 1–19 October 2026 (rebuilt 2026-10-20)

`schedule_delays.csv` was regenerated on the **FTA utilization plan** basis
by `work/build_october_fta.py`, replacing the frozen build's timetable-based
file (1–5 Oct, Aeroroutes times). The plan transcribed from
fta.ugandairlines.com (422 operating legs, 1–19 Oct, after de-duplicating
double-listed overnight legs) is kept at `work/fta_oct2026.csv`.

For each leg: scheduled STD/STA (local, converted to UTC by airport
timezone), the plan's aircraft and status, and — for the 405 legs with a
track — actual takeoff/landing and delays. 17 legs have no track; all
were verified against FR24's per-aircraft flight lists on 2026-10-23
and **did not operate** (the FTA plans overstate the schedule). They
are listed in `data_gaps.md` and marked `no_track` here. CANCELLED plan
rows (UR520/UR521 on 17 Oct) and NON_SCHEDULED plan rows (the 15 Oct
EBB–EBB test entry) are excluded.

Caveats:

- **Departure delay includes taxi-out**: actual = first airborne fix, STD =
  off-block. Subtract ~15–30 min for a gate-departure reading.
- STA in the plans is occasionally internally inconsistent (e.g. UR209 on
  13 Oct: STA before STD); arrival delays for such legs are indicative only.
- One UR323 DAR–EBB leg on 1 Oct is listed under two aircraft in the plan;
  it is counted once here.
- `op_median_*` columns summarise the same flight's operated departures in
  this 19-day window (≥3 legs) — a thin baseline, not a timetable.
