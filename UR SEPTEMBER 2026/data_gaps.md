# Data gaps — FTA-planned legs with no FR24 track (added 2026-10-20)

52 planned operating legs (1–30 Sep 2026) have no track in
`UR September flights.zip`. Source: FTA utilization plans
(work/fta_sep2026.csv) joined to flights.csv by work/build_september_fta.py.
CANCELLED (14) and NON_SCHEDULED (5) plan rows are not gaps;
6 duplicate plan listings of a leg (listed twice across
adjacent day-plans) were counted once, against the closest operated departure.
The plan's KBG/KGB code is Hoima (Kabaale), `UGHO` in flights.csv; the
Hoima shuttle tracks fly as AF523, not the plan's UR130–UR133 numbers.

## Legs with no track

| date | flight | route | STD (local) | reg | plan status |
|---|---|---|---|---|---|
| 2026-09-01 | UR120 | EBB-JUB | 14:00 | 5X-EQU | SCHEDULED |
| 2026-09-01 | UR121 | JUB-EBB | 15:25 | 5X-EQU | SCHEDULED |
| 2026-09-01 | UR323 | DAR-EBB | 23:50 | 5X-KDP | SCHEDULED |
| 2026-09-02 | UR209 | NBO-EBB | 00:25 | 5X-KDP | SCHEDULED |
| 2026-09-02 | UR323 | DAR-EBB | 00:50 | 5X-EQU | SCHEDULED |
| 2026-09-02 | UR431 | BOM-EBB | 08:00 | 5X-NIL | SCHEDULED |
| 2026-09-02 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-04 | UR720 | HRE-EBB | 01:45 | 5X-KOB | SCHEDULED |
| 2026-09-04 | UR720 | LUN-HRE | 23:45 | 5X-KOB | SCHEDULED |
| 2026-09-05 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-06 | UR720 | LUN-HRE | 23:45 | 5X-EQU | SCHEDULED |
| 2026-09-07 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-08 | UR323 | DAR-EBB | 23:50 | 5X-KDP | SCHEDULED |
| 2026-09-09 | UR209 | NBO-EBB | 00:25 | 5X-KDP | SCHEDULED |
| 2026-09-09 | UR323 | DAR-EBB | 00:50 | 5X-KOB | SCHEDULED |
| 2026-09-09 | UR431 | BOM-EBB | 08:00 | 5X-NIL | SCHEDULED |
| 2026-09-09 | UR722 | HRE-LUN | 14:45 | 5X-KOB | SCHEDULED |
| 2026-09-09 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-11 | UR720 | HRE-EBB | 01:45 | 5X-KDP | SCHEDULED |
| 2026-09-12 | UR431 | BOM-EBB | 01:10 | 5X-NIL | SCHEDULED |
| 2026-09-14 | UR720 | EBB-LUN | 21:00 | 5X-EQU | SCHEDULED |
| 2026-09-14 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-14 | UR720 | LUN-HRE | 23:45 | 5X-EQU | SCHEDULED |
| 2026-09-15 | UR722 | EBB-HRE | 13:00 | ET-APL | SCHEDULED |
| 2026-09-16 | UR343 | MBA-EBB | 01:55 | 5X-KOB | SCHEDULED |
| 2026-09-16 | UR431 | BOM-EBB | 08:00 | 5X-NIL | SCHEDULED |
| 2026-09-16 | UR111 | LGW-EBB | 20:10 | 5X-NIL | SCHEDULED |
| 2026-09-17 | UR121 | JUB-EBB | 14:10 | 5X-KOB | SCHEDULED |
| 2026-09-17 | UR361 | BJM-EBB | 17:45 | 5X-EQU | SCHEDULED |
| 2026-09-17 | UR322 | EBB-DAR | 22:00 | 5X-KOB | SCHEDULED |
| 2026-09-18 | UR343 | MBA-EBB | 01:10 | 5X-KOB | SCHEDULED |
| 2026-09-18 | UR720 | HRE-EBB | 01:45 | 5X-KDP | SCHEDULED |
| 2026-09-18 | UR334 | ZNZ-JRO | 12:05 | 5X-KDP | SCHEDULED |
| 2026-09-18 | UR720 | LUN-HRE | 23:45 | 5X-KDP | SCHEDULED |
| 2026-09-19 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-20 | UR343 | MBA-EBB | 02:20 | 5X-KDP | DELAYED |
| 2026-09-20 | UR720 | HRE-EBB | 02:35 | 5X-KOB | SCHEDULED |
| 2026-09-20 | UR900 | EBB-LOS | 10:00 | TBN | SCHEDULED |
| 2026-09-20 | UR121 | JUB-EBB | 11:10 | 5X-KDP | SCHEDULED |
| 2026-09-21 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-21 | UR720 | LUN-HRE | 23:45 | 5X-KOB | SCHEDULED |
| 2026-09-22 | UR722 | HRE-LUN | 16:00 | ET-APL | SCHEDULED |
| 2026-09-24 | UR713 | JNB-EBB | 03:00 | 5X-KOB | SCHEDULED |
| 2026-09-25 | UR720 | HRE-EBB | 01:45 | 5X-KOB | SCHEDULED |
| 2026-09-26 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-27 | UR334 | ZNZ-JRO | 12:05 | 5X-KDP | SCHEDULED |
| 2026-09-27 | UR320 | EBB-DAR | 12:15 | ET-APL | SCHEDULED |
| 2026-09-27 | UR321 | DAR-EBB | 14:50 | ET-APL | SCHEDULED |
| 2026-09-27 | UR720 | LUN-HRE | 23:45 | 5X-KDP | SCHEDULED |
| 2026-09-28 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-09-29 | UR323 | DAR-EBB | 23:50 | 5X-KDP | SCHEDULED |
| 2026-09-30 | UR111 | LGW-EBB | 18:10 | 5X-NIL | SCHEDULED |

Track-side notes (from the rebuilt log): 10 tracks start airborne and 40 end
airborne, so some ends are routed/timed by first/last fix; the AF523 Hoima
and UGD720X test tracks are in flights.csv but carry no scheduled identity.
5X-KNP and 5X-CRN were grounded (AOG) in every September plan; 5X-EQU was
also out of service for part of 7–23 Sep ('UNDER MX AT EBB').
