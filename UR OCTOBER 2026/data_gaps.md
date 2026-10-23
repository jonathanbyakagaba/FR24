# Data gaps — FTA-planned legs with no FR24 track (updated 2026-10-23)

17 planned operating legs (1–19 Oct 2026) have no track in
`FR data.zip`. **None of them is an open gap.** On 2026-10-23 every
no-track leg was checked against FR24's own per-aircraft flight lists
(all active Uganda Airlines tails, history from 2026-08-30, via the
`fr24` library with subscription-key auth): **every leg below did not
operate** — no aircraft flew the sector within ±36 h of the planned
departure (matcher: `work/match_missing.py`, verdicts in
`work/match_report.csv`). The FTA utilization plans systematically
overstate operations — UR111 LGW–EBB is planned near-daily but flown
every 2–3 days — so a plan leg without a track is a paper leg, not a
recording failure.

## Recovered on 2026-10-23 (no longer gaps)

28 of this month's originally-missing legs were real flights whose
tracks were simply absent from the user's FR24 export. Their playback
tracks were downloaded from FR24 and merged into the archives
(`work/fetch_tracks.py` → `work/tracks_in/`, merged by
`work/build_month_zips.py`; target list `work/targets.csv`):

| date | flight | route | track file |
|---|---|---|---|
| 2026-10-03 | UR720 | LUN-HRE | UR720-41f58e5d.csv |
| 2026-10-03 | UR722 | HRE-LUN | UR722-41f436a2.csv |
| 2026-10-05 | UR720 | LUN-HRE | UR720-41fd0aa4.csv |
| 2026-10-09 | UR334 | ZNZ-JRO | UR334-420b27ee.csv |
| 2026-10-09 | UR720 | LUN-HRE | UR720-420da881.csv |
| 2026-10-10 | UR720 | LUN-HRE | UR720-42112f5b.csv |
| 2026-10-10 | UR722 | HRE-LUN | UR722-420ff2aa.csv |
| 2026-10-11 | UR111 | LGW-EBB | UR111-421411be.csv |
| 2026-10-11 | UR334 | ZNZ-JRO | UR334-421297f7.csv |
| 2026-10-11 | UR343 | MBA-EBB | UR343-421407a6.csv |
| 2026-10-11 | UR720 | LUN-HRE | UR720-42147ca9.csv |
| 2026-10-15 | UR722 | HRE-LUN | UR722-42228338.csv |
| 2026-10-16 | UR720 | LUN-HRE | UR720-4227f4f5.csv |
| 2026-10-17 | UR720 | LUN-HRE | UR720-422b82df.csv |
| 2026-10-17 | UR722 | HRE-LUN | UR722-422a1bdf.csv |
| 2026-10-18 | UR720 | HRE-EBB | UR720-422bc19f.csv |
| 2026-10-18 | UR720 | LUN-HRE | UR720-422f0d1d.csv |
| 2026-10-19 | UR123 | JUB-EBB | UR123-42306683.csv |
| 2026-10-19 | UR208 | EBB-NBO | UR208-423277bd.csv |
| 2026-10-19 | UR320 | EBB-DAR | UR320-42309a98.csv |
| 2026-10-19 | UR321 | DAR-EBB | UR321-42310ee0.csv |
| 2026-10-19 | UR360 | EBB-BJM | UR360-42314eaf.csv |
| 2026-10-19 | UR361 | BJM-EBB | UR361-4231bb20.csv |
| 2026-10-19 | UR711 | JNB-EBB | UR711-4230fb0f.csv |
| 2026-10-19 | UR712 | EBB-JNB | UR712-4232b3c6.csv |
| 2026-10-19 | UR720 | EBB-LUN | UR720-42325619.csv |
| 2026-10-19 | UR720 | LUN-HRE | UR720-42330293.csv |
| 2026-10-19 | UR901 | LOS-EBB | UR901-42312319.csv |

## Legs that did not operate (verified 2026-10-23)

| date | flight | route | STD (local) | plan reg | FR24 evidence |
|---|---|---|---|---|---|
| 2026-10-02 | UR720 | HRE-EBB | 01:45 | 5X-KOB | no UR720 HRE→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-03 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-04 | UR342 | EBB-MBA | 01:45 | 5X-EQU | no UR342 EBB→MBA in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-04 | UR713 | JNB-EBB | 02:45 | ET-APL | no UR713 JNB→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-04 | UR343 | MBA-EBB | 04:20 | 5X-EQU | no UR343 MBA→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-05 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-07 | UR123 | JUB-EBB | 14:15 | 5X-KOB | no UR123 JUB→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-07 | UR111 | LGW-EBB | 20:10 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-08 | UR343 | MBA-EBB | 22:40 | 5X-KOB | no UR343 MBA→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-10 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-12 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-13 | UR323 | DAR-EBB | 23:50 | 5X-KOB | no UR323 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-14 | UR111 | LGW-EBB | 20:10 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-15 | UR343 | MBA-EBB | 22:40 | 5X-KOB | no UR343 MBA→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-17 | UR431 | BOM-EBB | 01:10 | 5X-NIL | no UR431 BOM→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-17 | UR111 | LGW-EBB | 19:15 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-10-19 | UR111 | LGW-EBB | 19:15 | 5X-NIL | 5X-NIL A338 EGKK->HUEN (flightlist_5X-NIL.csv) |

Source: FTA utilization plans (`work/fta_oct2026.csv`) joined to `flights.csv` by
`work/build_october_fta.py`; verification by `work/match_missing.py` against
`work/flightlists/`. To refresh the leg list re-run the FTA builder,
then re-check any new no-track legs against fresh flight lists before
quoting counts — do not carry the verified classification over blindly.
