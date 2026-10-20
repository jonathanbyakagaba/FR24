# NOTAMs — October 2026 (added 2026-10-20)

`notams.csv` (92 rows) = every notice whose validity window touches
October 2026, taken from the snapshot in `work/notams_snapshot_20261020.csv`
(retrieved 2026-10-20; split by `python3 work/build_notams.py`).

**Sources.** Entebbe/FIR Uganda items are from the official **UCAA AIM
NOTAM list of 19 Oct 2026** (aim.caa.co.ug/pdf/notam.pdf). The other
stations come from **Speedbird Online's mirror of the FAA NOTAM feed**
(refreshed daily; unofficial, "not for operational use" — verified
identical to the UCAA list for HUEN: A0194/26 and A0192/26 appear in
both). `JUB` and `BJM` are **not covered** by that mirror; `MBA`, `MGQ`,
`HRE` and `LUN` show **no current notices** (Lusaka was queried under
its old code FLLS — Kenneth Kaunda Intl is FLKK today, so treat LUN as
unverified). A current-notices snapshot can never see notices that
expired before retrieval: expired items must be captured month by
month from now on, or bought back via the FAA NOTAM Search archive
(5-year history, one location+date at a time) / national AIS offices.

## What mattered operationally this month

* **EBB — the runway closed every night.** `A0194/26`: **RWY 17/35 CLSD
  14–21 Oct, daily 03:00–06:00Z (06:00–09:00 EAT).** Almost no UR
  movement touched the window — except the inbound **UR111 from LGW,
  which landed RWY 17 at 03:21Z on 14 Oct**, 21 minutes into the first
  closure morning. Worth a query to UCAA/ops: waived for the inbound,
  or the schedule started a night later than the B) time says.
  UR713's planned arrival (16 Oct, STA 05:15Z) is inside the window too,
  but the operated flight stayed clear of it.
* **DAR — ILS RWY 05 localizer shut down** from 13 Oct to 13 Jan 2027
  (system replacement). Arrivals on 05 in poor weather lose the ILS;
  relevant context for any slow DAR approaches in `flight_conditions`.
* **NBO — taxiway G pothole & partial closure** (23 Sep – 30 Oct,
  portions closed from 8 Oct) plus bay 7/18/19 towing procedures:
  ground-time friction at Nairobi all month. And from **20 Oct 22:40Z,
  RWY 06/24 closed nightly 22:40–01:40Z** for WIP — just after this
  dataset's track window ends.
* **JNB — arrival procedures in flux.** From 9 Oct, arrivals on several
  STARs must expect **radar vectors** (VEKOP/UVLOG/ETLIG/ETGAV) and the
  STARs' communication-failure procedures are suspended; from 29 Sep
  the charted STAR level restrictions are not to be flown (ATC levels
  only) and four RNAV SIDs (EGMEN/APDAK/GEROX) are suspended. Read
  JNB arrival track shapes with this in mind — see `sid_star.md`.
* **BOM — works on Taxiway M** all month ("ARR/DEP TRAFFIC TO EXP DLA
  DRG TAX", Code-F restrictions), bird concentration at dawn/dusk
  windows, and two RVR (DRISHTI) sensors U/S (18 Sep – 27 Oct).
* **LGW — nightly single-runway ops from 19 Oct:** RWY 08R/26L closed
  22:00–04:30Z (08L/26R in use). UR111's 19:15 local departure clears
  it, but any slippage past 22:10Z has no main-runway fallback.
* **ZNZ** — stand 06 (Terminal III) restricted to Code A/B until
  22 Oct (UR uses CRJ-900 = Code C on ZNZ sectors; stand planning
  context) and apron construction by TWY C.
* **JRO** — Kilimanjaro Approach primary frequency changed
  120.1 → 123.9 MHz (22 Sep – 22 Oct).

## Columns

`valid_from_utc`/`valid_to_utc` are the B)/C) validity times;
`schedule` is the D) line where one exists (daily windows). Several
BOM long-dated items show a `19 Jan 03:14Z` end in the source feed —
that is the mirror's rendering of a PERM/open-ended item, not a real
expiry; treat those as "still in force at snapshot date".
