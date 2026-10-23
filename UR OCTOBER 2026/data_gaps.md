# FR24 track gaps — October 2026 (updated 2026-10-23)

The FTA schedule join covers 480 operating legs (1–22 Oct); 458 matched
a track and 22 did not. Every remaining no-track leg was classified
against FR24's per-aircraft flight lists on 2026-10-23
(`work/classify_gaps.py`, full evidence in `work/gap_verdicts.csv`):

- **17 legs did not operate** (the FTA plans overstate the schedule);
- **2 legs operated** and their tracks are in the archive, but the
  join's match window (departure −240…+480 min vs STD) missed them —
  they therefore still show as `no_track` in `schedule_delays.csv`;
- **3 legs operated** but their tracks are in no export; they are
  FR24-downloadable and listed in `work/targets_uptodate.csv`.

> **Correction to the 2026-10-23 morning edition of this file:** the
> UR123 JUB–EBB leg of 7 Oct was listed as "did not operate". It in fact
> operated (5X-EQU, departed 05:50Z, 384 min *before* STD — outside the
> join's window) and its track (`UR123-42025f92.csv`) is in the archive.
> See the second table below.

## Verified: 17 legs that did not operate

| Date | Flight | Sector | STD (UTC) | Evidence |
|---|---|---|---|---|
| 2026-10-02 | UR720 | HRE–EBB | 2026-10-01 23:45Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-10-02 23:06Z (+1401 min vs STD), archived=True |
| 2026-10-03 | UR111 | LGW–EBB | 2026-10-03 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-02 19:05Z (-1409 min vs STD), archived=True |
| 2026-10-04 | UR342 | EBB–MBA | 2026-10-03 22:45Z | nearest candidate is the adjacent rotation: 5X-EQU ATOD 2026-10-04 22:34Z (+1429 min vs STD), archived=True |
| 2026-10-04 | UR343 | MBA–EBB | 2026-10-04 01:20Z | nearest candidate is the adjacent rotation: 5X-EQU ATOD 2026-10-05 01:28Z (+1449 min vs STD), archived=True |
| 2026-10-04 | UR713 | JNB–EBB | 2026-10-04 00:45Z | nearest candidate is the adjacent rotation: ET-APL ATOD 2026-10-05 01:15Z (+1470 min vs STD), archived=True |
| 2026-10-05 | UR111 | LGW–EBB | 2026-10-05 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-04 18:51Z (-1423 min vs STD), archived=True |
| 2026-10-07 | UR111 | LGW–EBB | 2026-10-07 19:10Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-06 19:27Z (-1423 min vs STD), archived=True |
| 2026-10-08 | UR343 | MBA–EBB | 2026-10-08 19:40Z | nearest candidate is the adjacent rotation: 5X-EQU ATOD 2026-10-09 19:22Z (+1422 min vs STD), archived=True |
| 2026-10-10 | UR111 | LGW–EBB | 2026-10-10 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-09 19:25Z (-1390 min vs STD), archived=True |
| 2026-10-12 | UR111 | LGW–EBB | 2026-10-12 18:35Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-11 19:14Z (-1400 min vs STD), archived=True |
| 2026-10-13 | UR323 | DAR–EBB | 2026-10-13 20:50Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-10-12 20:58Z (-1432 min vs STD), archived=True |
| 2026-10-14 | UR111 | LGW–EBB | 2026-10-14 19:10Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-13 19:17Z (-1432 min vs STD), archived=True |
| 2026-10-15 | UR343 | MBA–EBB | 2026-10-15 19:40Z | nearest candidate is the adjacent rotation: 5X-KOB ATOD 2026-10-16 18:29Z (+1370 min vs STD), archived=True |
| 2026-10-17 | UR111 | LGW–EBB | 2026-10-17 18:15Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-16 18:56Z (-1399 min vs STD), archived=True |
| 2026-10-17 | UR431 | BOM–EBB | 2026-10-16 19:40Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-17 19:54Z (+1455 min vs STD), archived=True |
| 2026-10-19 | UR111 | LGW–EBB | 2026-10-19 18:15Z | nearest candidate is the adjacent rotation: 5X-NIL ATOD 2026-10-18 18:56Z (-1398 min vs STD), archived=True |
| 2026-10-22 | UR712 | EBB–JNB | 2026-10-22 20:30Z | no candidate within ±36 h in any tail's FR24 flight list |

## Operated — track in the archive, outside the join's time window (2)

| Date | Flight | Sector | STD (UTC) | Evidence |
|---|---|---|---|---|
| 2026-10-07 | UR123 | JUB–EBB | 2026-10-07 12:15Z | shifted: 5X-EQU ATOD 2026-10-07 05:50Z (-384 min vs STD); id 42025f92 is archived but the FTA join missed it |
| 2026-10-22 | UR711 | HRE–EBB | 2026-10-22 09:00Z | shifted: ET-APL ATOD 2026-10-22 19:10Z (+610 min vs STD); id 423eb282 is archived but the FTA join missed it |

Notes: the 7 Oct UR123 departed 6 h 24 min ahead of the plan's times
(previous-day rotation carried into the morning). The 22 Oct **UR711**
HRE–EBB is the delayed recovery of 21 Oct's UR711 JNB–EBB, which
**diverted to Harare** (FR24 flight-list status) — ET-APL only left HRE
at 19:10Z on 22 Oct, 610 min after the recovery leg's STD, labelled
UR711D in the plan. Widening the join window to swallow either case
would create false matches elsewhere, so both legs stay `no_track`
with this explanation.

## Operated — track not in any export yet, downloadable (3)

| Date | Flight | Sector | STD (UTC) | Evidence |
|---|---|---|---|---|
| 2026-10-21 | UR322 | EBB–DAR | 2026-10-21 20:00Z | 5X-EQU ATOD 2026-10-21 22:11Z (+131 min vs STD), flight id 423b316c not in archive |
| 2026-10-21 | UR711 | JNB–EBB | 2026-10-21 12:15Z | ET-APL ATOD 2026-10-21 13:57Z (+102 min vs STD), flight id 423968ef not in archive |
| 2026-10-22 | UR902 | EBB–LOS | 2026-10-22 19:30Z | ET-APL ATOD 2026-10-22 23:48Z (+258 min vs STD), flight id 423f95c8 not in archive |

These three are in `work/targets_uptodate.csv` (15 flights: these,
UR207 of 2026-09-01, and 11 flights that arrived on 23 Oct) for the
next Windows download round (`work/fetch_tracks.py`, see
`DATA_EXTRACTION_GUIDE.md`). UR322 of 21 Oct was flown by 5X-EQU
although the plan assigned ET-APL; UR711 of 21 Oct is the diversion
above; UR902 departed Entebbe at 02:48 EAT on 23 Oct, so once
downloaded it will be dated (origin-local) 2026-10-23 and join the
archive when the October window extends.

## What the recovery found

28 October legs originally listed as missing *did* operate; their
tracks were absent from the exports and were recovered from FR24
playback on 2026-10-23 (`work/targets.csv`):

| Recovered via playback (28) | File |
|---|---|
| UR720 LUN→HRE 2026-10-03 | UR720-41f58e5d.csv |
| UR722 HRE→LUN 2026-10-03 | UR722-41f436a2.csv |
| UR720 LUN→HRE 2026-10-05 | UR720-41fd0aa4.csv |
| UR334 ZNZ→JRO 2026-10-09 | UR334-420b27ee.csv |
| UR720 LUN→HRE 2026-10-09 | UR720-420da881.csv |
| UR720 LUN→HRE 2026-10-10 | UR720-42112f5b.csv |
| UR722 HRE→LUN 2026-10-10 | UR722-420ff2aa.csv |
| UR111 LGW→EBB 2026-10-11 | UR111-421411be.csv |
| UR334 ZNZ→JRO 2026-10-11 | UR334-421297f7.csv |
| UR343 MBA→EBB 2026-10-11 | UR343-421407a6.csv |
| UR720 LUN→HRE 2026-10-11 | UR720-42147ca9.csv |
| UR722 HRE→LUN 2026-10-15 | UR722-42228338.csv |
| UR720 LUN→HRE 2026-10-16 | UR720-4227f4f5.csv |
| UR720 LUN→HRE 2026-10-17 | UR720-422b82df.csv |
| UR722 HRE→LUN 2026-10-17 | UR722-422a1bdf.csv |
| UR720 HRE→EBB 2026-10-18 | UR720-422bc19f.csv |
| UR720 LUN→HRE 2026-10-18 | UR720-422f0d1d.csv |
| UR123 JUB→EBB 2026-10-19 | UR123-42306683.csv |
| UR208 EBB→NBO 2026-10-19 | UR208-423277bd.csv |
| UR320 EBB→DAR 2026-10-19 | UR320-42309a98.csv |
| UR321 DAR→EBB 2026-10-19 | UR321-42310ee0.csv |
| UR360 EBB→BJM 2026-10-19 | UR360-42314eaf.csv |
| UR361 BJM→EBB 2026-10-19 | UR361-4231bb20.csv |
| UR711 JNB→EBB 2026-10-19 | UR711-4230fb0f.csv |
| UR712 EBB→JNB 2026-10-19 | UR712-4232b3c6.csv |
| UR720 EBB→LUN 2026-10-19 | UR720-42325619.csv |
| UR720 LUN→HRE 2026-10-19 | UR720-42330293.csv |
| UR901 LOS→EBB 2026-10-19 | UR901-42312319.csv |

The fresh `FR data.zip` export of 2026-10-23 closed 4 more October
stragglers (UR120, UR208, UR334, UR520 of 3–18 Oct) and extended
coverage through 22 Oct. Note the plan can also *understate*: the
22 Oct **UR722X** EBB–HRE–EBB rotation was filed NON_SCHEDULED but
operated anyway (tracks `UNKNOWN-423bc735.csv` /
`UNKNOWN-423c636e.csv`, in `flights.csv`).
