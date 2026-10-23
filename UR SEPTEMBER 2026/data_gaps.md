# Data gaps — FTA-planned legs with no FR24 track (updated 2026-10-23)

36 planned operating legs (1–30 Sep 2026) have no track in
`UR September flights.zip`. **None of them is an open gap.** On 2026-10-23 every
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

16 of this month's originally-missing legs were real flights whose
tracks were simply absent from the user's FR24 export. Their playback
tracks were downloaded from FR24 and merged into the archives
(`work/fetch_tracks.py` → `work/tracks_in/`, merged by
`work/build_month_zips.py`; target list `work/targets.csv`):

| date | flight | route | track file |
|---|---|---|---|
| 2026-09-04 | UR720 | LUN-HRE | UR720-4182c33a.csv |
| 2026-09-06 | UR720 | LUN-HRE | UR720-418a246d.csv |
| 2026-09-09 | UR722 | HRE-LUN | UR722-4194360c.csv |
| 2026-09-15 | UR722 | EBB-HRE | UR722-41ab839e.csv |
| 2026-09-17 | UR121 | JUB-EBB | UR121-41b43d30.csv |
| 2026-09-17 | UR322 | EBB-DAR | UR322-41b5b8d6.csv |
| 2026-09-17 | UR361 | BJM-EBB | UR361-41b501ce.csv |
| 2026-09-18 | UR334 | ZNZ-JRO | UR334-41b7d5c5.csv |
| 2026-09-18 | UR720 | LUN-HRE | UR720-41ba7f70.csv |
| 2026-09-20 | UR121 | JUB-EBB | UR121-41bfa6d2.csv |
| 2026-09-20 | UR720 | HRE-EBB | UR720-41be890a.csv |
| 2026-09-20 | UR900 | EBB-LOS | UR900-41bf5e86.csv |
| 2026-09-21 | UR720 | LUN-HRE | UR720-41c59871.csv |
| 2026-09-22 | UR722 | HRE-LUN | UR722-41c80fb7.csv |
| 2026-09-27 | UR334 | ZNZ-JRO | UR334-41db58b7.csv |
| 2026-09-27 | UR720 | LUN-HRE | UR720-41dda0c2.csv |

## Legs that did not operate (verified 2026-10-23)

| date | flight | route | STD (local) | plan reg | FR24 evidence |
|---|---|---|---|---|---|
| 2026-09-01 | UR120 | EBB-JUB | 14:00 | 5X-EQU | no UR120 EBB→JUB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-01 | UR121 | JUB-EBB | 15:25 | 5X-EQU | no UR121 JUB→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-01 | UR323 | DAR-EBB | 23:50 | 5X-KDP | no UR323 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-02 | UR209 | NBO-EBB | 00:25 | 5X-KDP | no UR209 NBO→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-02 | UR323 | DAR-EBB | 00:50 | 5X-EQU | no UR323 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-02 | UR431 | BOM-EBB | 08:00 | 5X-NIL | no UR431 BOM→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-02 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-04 | UR720 | HRE-EBB | 01:45 | 5X-KOB | no UR720 HRE→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-05 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-07 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-08 | UR323 | DAR-EBB | 23:50 | 5X-KDP | no UR323 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-09 | UR209 | NBO-EBB | 00:25 | 5X-KDP | no UR209 NBO→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-09 | UR323 | DAR-EBB | 00:50 | 5X-KOB | no UR323 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-09 | UR431 | BOM-EBB | 08:00 | 5X-NIL | no UR431 BOM→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-09 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-11 | UR720 | HRE-EBB | 01:45 | 5X-KDP | no UR720 HRE→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-12 | UR431 | BOM-EBB | 01:10 | 5X-NIL | no UR431 BOM→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-14 | UR720 | EBB-LUN | 21:00 | 5X-EQU | no UR720 EBB→LUN in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-14 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-14 | UR720 | LUN-HRE | 23:45 | 5X-EQU | no UR720 LUN→HRE in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-16 | UR343 | MBA-EBB | 01:55 | 5X-KOB | no UR343 MBA→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-16 | UR431 | BOM-EBB | 08:00 | 5X-NIL | no UR431 BOM→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-16 | UR111 | LGW-EBB | 20:10 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-18 | UR343 | MBA-EBB | 01:10 | 5X-KOB | no UR343 MBA→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-18 | UR720 | HRE-EBB | 01:45 | 5X-KDP | no UR720 HRE→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-19 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-20 | UR343 | MBA-EBB | 02:20 | 5X-KDP | no UR343 MBA→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-21 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-24 | UR713 | JNB-EBB | 03:00 | 5X-KOB | no UR713 JNB→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-25 | UR720 | HRE-EBB | 01:45 | 5X-KOB | no UR720 HRE→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-26 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-27 | UR320 | EBB-DAR | 12:15 | ET-APL | no UR320 EBB→DAR in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-27 | UR321 | DAR-EBB | 14:50 | ET-APL | no UR321 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-28 | UR111 | LGW-EBB | 19:35 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-29 | UR323 | DAR-EBB | 23:50 | 5X-KDP | no UR323 DAR→EBB in any tail's FR24 flight list within ±36 h of STD |
| 2026-09-30 | UR111 | LGW-EBB | 18:10 | 5X-NIL | no UR111 LGW→EBB in any tail's FR24 flight list within ±36 h of STD |

Source: FTA utilization plans (`work/fta_sep2026.csv`) joined to `flights.csv` by
`work/build_september_fta.py`; verification by `work/match_missing.py` against
`work/flightlists/`. To refresh the leg list re-run the FTA builder,
then re-check any new no-track legs against fresh flight lists before
quoting counts — do not carry the verified classification over blindly.
