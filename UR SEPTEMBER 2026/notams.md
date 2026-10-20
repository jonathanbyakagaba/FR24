# NOTAMs — September 2026 (added 2026-10-20)

`notams.csv` (51 rows) = every notice in the 2026-10-20 snapshot
(`work/notams_snapshot_20261020.csv`, split by `work/build_notams.py`)
whose validity window touches September 2026.

**Read this caveat first.** The snapshot holds notices *still active or
upcoming on 20 Oct 2026* (Entebbe: UCAA AIM official list of 19 Oct
2026; other stations: Speedbird Online's mirror of the FAA feed).
Notices that were issued for September and **expired before 20 Oct are
invisible to it** — so this file is a *lower bound* on September's
NOTAM load, biased toward long-running items (works, procedures,
obstacles). Short September items (a weekend runway closure, a navaid
outage since fixed) can only be recovered from the FAA NOTAM Search
archive search (5-year history, location+date) or the national AIS
offices, one query at a time. From October 2026 onward the fix is
procedural: archive a snapshot on the 1st of each month (see
`work/build_notams.py`) and the gap stops growing.

## September items with operational read-across

* **NBO — apron/taxiway pavement problems from 23–24 Sep:** pothole on
  TWY G, loose surface behind Bay 18 (Code D+ towing procedure),
  pavement failure on Bay 07 — congestion context for the late-September
  Nairobi delays in `schedule_delays.csv`; TWY G was then part-closed
  from 8 Oct (October file).
* **JNB — procedures changed mid-month:** charted STAR level
  restrictions withdrawn (ATC levels only) and RNAV SIDs
  EGMEN/APDAK/GEROX suspended, both from **29 Sep**; three RNAV/GNSS
  approach procedures suspended the same day. UR710/711
  arrival/departure profiles at JNB before/after 29 Sep are
  not directly comparable.
* **BOM — bird concentration** in the vicinity from 9 Sep
  (05:01–07:59 and 14:30–21:00 daily windows), RVR/pressure sensors
  (METPARK-09) U/S from 18/23 Sep — our EBB-only METAR join can't see
  BOM weather anyway, but a U/S RVR sensor also degrades what BOM
  reports to the world.
* **LOS — ATIS unserviceable from 30 Sep** (to 30 Dec); TWY H and
  Link C1 closed since 24 Aug.
* **ZNZ — new apron construction** by TWY C/Taxilane D from 17 Sep;
  stand 06 restricted to Code A/B from 23 Sep.
* **JRO — Kilimanjaro Approach frequency changed** 120.1 → 123.9 MHz
  from 22 Sep (the old frequency NOTAM'd U/S alongside).
* **LGW — lasers/fireworks notices** around Turners Hill from 21 Sep
  (evenings) — the only LGW items touching UR111's late-evening
  departures this month.
* **EBB — none.** No Uganda A-series notice in the snapshot has a
  September validity window; that means nothing from September was
  still running on 19 Oct — not that September was NOTAM-free.
  September Entebbe items are exactly what the archive search (above)
  would be needed for.

## Columns

`valid_from_utc`/`valid_to_utc` are the B)/C) validity times;
`schedule` is the D) line where one exists. Several BOM long-dated
items show `19 Jan 03:14Z` as the end — the mirror's rendering of a
PERM item, i.e. "still in force at snapshot", not a true expiry.
