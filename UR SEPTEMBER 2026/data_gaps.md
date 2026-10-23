# FR24 track gaps — September 2026 (updated 2026-10-23)

The FTA schedule join covers 660 operating legs; 624 matched a track and
36 did not. Every one of the 36 was checked against FR24's per-aircraft
flight lists (see `work/match_missing.py`, re-run after the archive
merge, and `work/classify_gaps.py`, which re-classified every remaining
no-track leg after the 2026-10-23 export merge): **all 36 legs did not
operate** — the FTA plans systematically overstate the schedule (they
carry paper rotations, e.g. near-daily UR111 LGW–EBB, that do not fly).

## Verified: 36 legs that did not operate

| Date | Flight | Sector | STD (UTC) | Evidence |
|---|---|---|---|---|
| 2026-09-01 | UR120 | EBB–JUB | 2026-09-01 11:00Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-02 09:17Z (+1338 min vs STD), archived=True |
| 2026-09-01 | UR121 | JUB–EBB | 2026-09-01 13:25Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-02 11:11Z (+1307 min vs STD), archived=True |
| 2026-09-01 | UR323 | DAR–EBB | 2026-09-01 20:50Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-08-31 20:35Z (-1454 min vs STD), archived=True |
| 2026-09-02 | UR111 | LGW–EBB | 2026-09-02 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-01 19:26Z (-1388 min vs STD), archived=True |
| 2026-09-02 | UR209 | NBO–EBB | 2026-09-01 21:25Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-02 21:35Z (+1451 min vs STD), archived=True |
| 2026-09-02 | UR323 | DAR–EBB | 2026-09-01 21:50Z | nearest candidate is the adjacent rotation: 5X-EQU ATOD 2026-09-02 21:38Z (+1428 min vs STD), archived=True |
| 2026-09-02 | UR431 | BOM–EBB | 2026-09-02 02:30Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-03 03:08Z (+1478 min vs STD), archived=True |
| 2026-09-04 | UR720 | HRE–EBB | 2026-09-03 23:45Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-04 23:36Z (+1432 min vs STD), archived=True |
| 2026-09-05 | UR111 | LGW–EBB | 2026-09-05 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-04 19:24Z (-1390 min vs STD), archived=True |
| 2026-09-07 | UR111 | LGW–EBB | 2026-09-07 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-06 19:05Z (-1410 min vs STD), archived=True |
| 2026-09-08 | UR323 | DAR–EBB | 2026-09-08 20:50Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-07 20:48Z (-1442 min vs STD), archived=True |
| 2026-09-09 | UR111 | LGW–EBB | 2026-09-09 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-08 20:57Z (-1297 min vs STD), archived=True |
| 2026-09-09 | UR209 | NBO–EBB | 2026-09-08 21:25Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-07 21:22Z (-1442 min vs STD), archived=True |
| 2026-09-09 | UR323 | DAR–EBB | 2026-09-08 21:50Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-09 21:54Z (+1444 min vs STD), archived=True |
| 2026-09-09 | UR431 | BOM–EBB | 2026-09-09 02:30Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-10 03:01Z (+1472 min vs STD), archived=True |
| 2026-09-11 | UR720 | HRE–EBB | 2026-09-10 23:45Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-11 23:12Z (+1407 min vs STD), archived=True |
| 2026-09-12 | UR431 | BOM–EBB | 2026-09-11 19:40Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-12 19:51Z (+1452 min vs STD), archived=True |
| 2026-09-14 | UR111 | LGW–EBB | 2026-09-14 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-13 18:51Z (-1424 min vs STD), archived=True |
| 2026-09-14 | UR720 | EBB–LUN | 2026-09-14 18:00Z | nearest candidate is the adjacent rotation: 5X-EQU ATOD 2026-09-13 18:06Z (-1433 min vs STD), archived=True |
| 2026-09-14 | UR720 | LUN–HRE | 2026-09-14 21:45Z | nearest candidate is the adjacent rotation: 5X-EQU ATOD 2026-09-13 21:25Z (-1460 min vs STD), archived=True |
| 2026-09-16 | UR111 | LGW–EBB | 2026-09-16 19:10Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-15 19:15Z (-1435 min vs STD), archived=True |
| 2026-09-16 | UR343 | MBA–EBB | 2026-09-15 22:55Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-16 22:36Z (+1422 min vs STD), archived=True |
| 2026-09-16 | UR431 | BOM–EBB | 2026-09-16 02:30Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-17 03:08Z (+1479 min vs STD), archived=True |
| 2026-09-18 | UR343 | MBA–EBB | 2026-09-17 22:10Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-16 22:36Z (-1413 min vs STD), archived=True |
| 2026-09-18 | UR720 | HRE–EBB | 2026-09-17 23:45Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-18 23:30Z (+1426 min vs STD), archived=True |
| 2026-09-19 | UR111 | LGW–EBB | 2026-09-19 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-18 18:50Z (-1425 min vs STD), archived=True |
| 2026-09-20 | UR343 | MBA–EBB | 2026-09-19 23:20Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-20 23:22Z (+1442 min vs STD), archived=True |
| 2026-09-21 | UR111 | LGW–EBB | 2026-09-21 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-20 18:57Z (-1418 min vs STD), archived=True |
| 2026-09-24 | UR713 | JNB–EBB | 2026-09-24 01:00Z | nearest candidate is the adjacent rotation: ET-APL ATOD 2026-09-23 01:06Z (-1433 min vs STD), archived=True |
| 2026-09-25 | UR720 | HRE–EBB | 2026-09-24 23:45Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-25 23:30Z (+1426 min vs STD), archived=True |
| 2026-09-26 | UR111 | LGW–EBB | 2026-09-26 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-25 19:13Z (-1401 min vs STD), archived=True |
| 2026-09-27 | UR320 | EBB–DAR | 2026-09-27 09:15Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-28 08:24Z (+1390 min vs STD), archived=True |
| 2026-09-27 | UR321 | DAR–EBB | 2026-09-27 11:50Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-09-28 11:13Z (+1403 min vs STD), archived=True |
| 2026-09-28 | UR111 | LGW–EBB | 2026-09-28 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-27 18:54Z (-1421 min vs STD), archived=True |
| 2026-09-29 | UR323 | DAR–EBB | 2026-09-29 20:50Z | nearest candidate is the adjacent rotation: 5X-KDP ATOD 2026-09-28 20:44Z (-1445 min vs STD), archived=True |
| 2026-09-30 | UR111 | LGW–EBB | 2026-09-30 17:10Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-09-29 20:12Z (-1257 min vs STD), archived=True |

## What the recovery found

16 September legs originally listed as missing *did* operate; their
tracks were absent from every `FR data.zip` export but recoverable from
FR24 playback. They were downloaded on 2026-10-23 (`work/targets.csv`,
44 flights across both months) and merged into the archives, so these
legs now carry full delay entries in `schedule_delays.csv`. The fresh
`FR data.zip` export of the same day also closed two more September
tracks (UR722 `41b034d5`, UR323 `41b3f78f`), one of them a twice-listed
leg — hence 660 legs and 624 matched. One September flight is still
absent from FR24's exports entirely: **UR207 NBO–EBB of 2026-09-01**
(FR24 flight id `41734071`, ET-APL) — it is listed in
`work/targets_uptodate.csv` for download.

| Recovered via playback (16) | File |
|---|---|
| UR720 LUN→HRE 2026-09-04 | UR720-4182c33a.csv |
| UR720 LUN→HRE 2026-09-06 | UR720-418a246d.csv |
| UR722 HRE→LUN 2026-09-09 | UR722-4194360c.csv |
| UR722 EBB→HRE 2026-09-15 | UR722-41ab839e.csv |
| UR121 JUB→EBB 2026-09-17 | UR121-41b43d30.csv |
| UR322 EBB→DAR 2026-09-17 | UR322-41b5b8d6.csv |
| UR361 BJM→EBB 2026-09-17 | UR361-41b501ce.csv |
| UR334 ZNZ→JRO 2026-09-18 | UR334-41b7d5c5.csv |
| UR720 LUN→HRE 2026-09-18 | UR720-41ba7f70.csv |
| UR121 JUB→EBB 2026-09-20 | UR121-41bfa6d2.csv |
| UR720 HRE→EBB 2026-09-20 | UR720-41be890a.csv |
| UR900 EBB→LOS 2026-09-20 | UR900-41bf5e86.csv |
| UR720 LUN→HRE 2026-09-21 | UR720-41c59871.csv |
| UR722 HRE→LUN 2026-09-22 | UR722-41c80fb7.csv |
| UR334 ZNZ→JRO 2026-09-27 | UR334-41db58b7.csv |
| UR720 LUN→HRE 2026-09-27 | UR720-41dda0c2.csv |
