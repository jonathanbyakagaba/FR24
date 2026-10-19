# Data gaps — September 2026 (rebuilt 2026-10-20)

Rebuilt against `UR September flights.zip` (622 UR tracks, 245,957 fixes).
The frozen version of this file described the old cumulative 802-track
archive; this one is scoped to the September month zip.

## What the tracks themselves show

- **Events not observed:** 10 tracks start airborne (takeoff not observed —
  the export picked the flight up en route) and 40 end airborne (landing
  not observed). Their unobserved ends are routed by flight-number pattern
  in `flights.csv`; times at those ends are first/last-fix proxies.
- **Non-scheduled flying in the zip:** 9 AF523 Hoima-shuttle/local tracks
  (27–30 Sep) and the UGD720X test flight `41e29857.csv` (29 Sep) are in
  the month zip and in `flights.csv`; they carry no scheduled-flight
  identity (see `no_code_tracks.md`). The frozen log excluded them; the
  rebuilt log includes them and says so.
- **One frozen-log flight is not in this zip:** `UR722-41b034d5.csv`
  (31 Aug triangle sector) predates the month window and belongs to the
  August record in the combined `FR data.zip`.
- **Duplicate content:** none — the month zip is exact-content deduplicated
  (see repository README-level notes in SUPPORTING.md).

## What is not checked here

Unlike October, **September was not cross-checked against the FTA
utilization plans in this rebuild** (transcribing 30 day-plans was out of
scope; October's FTA join is the worked example, in
`work/build_october_fta.py` and the October folder's `data_gaps.md`).
September legs that operated but left no track therefore do not appear
above — the frozen build's app-based gap notes (22 app-confirmed missing
flights to 5 Oct) were tied to the old cumulative archive and are not
reproduced. Treat September coverage as "622 tracks verified present",
not "all operated flights verified".
