# Data gaps — FTA-planned legs with no FR24 track (rebuilt 2026-10-20)

40 planned operating legs (1–18 Oct 2026) have no track in `FR data.zip`, plus
11 leg(s) scheduled at/after the export's last fix (2026-10-18 15:19Z)
that cannot be verified either way.
Source: FTA utilization plans (work/fta_oct2026.csv) joined to flights.csv by
work/build_october_fta.py. CANCELLED and NON_SCHEDULED plan rows are not gaps.

## Legs with no track

| date | flight | route | STD (local) | reg | plan status |
|---|---|---|---|---|---|
| 2026-10-02 | UR720 | HRE-EBB | 01:45 | 5X-KOB | SCHEDULED |
| 2026-10-03 | UR722 | HRE-LUN | 16:00 | 5X-KDP | SCHEDULED |
| 2026-10-03 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-10-03 | UR720 | LUN-HRE | 23:45 | ET-APL | SCHEDULED |
| 2026-10-04 | UR342 | EBB-MBA | 01:45 | 5X-EQU | RESCHEDULED |
| 2026-10-04 | UR343 | MBA-EBB | 04:20 | 5X-EQU | RESCHEDULED |
| 2026-10-04 | UR713 | JNB-EBB | 02:45 | ET-APL | SCHEDULED |
| 2026-10-05 | UR720 | LUN-HRE | 23:45 | 5X-KDP | SCHEDULED |
| 2026-10-05 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-10-07 | UR123 | JUB-EBB | 14:15 | 5X-KOB | SCHEDULED |
| 2026-10-07 | UR111 | LGW-EBB | 20:10 | 5X-NIL | SCHEDULED |
| 2026-10-08 | UR343 | MBA-EBB | 22:40 | 5X-KOB | SCHEDULED |
| 2026-10-09 | UR334 | ZNZ-JRO | 12:05 | 5X-KDP | SCHEDULED |
| 2026-10-09 | UR720 | LUN-HRE | 23:45 | 5X-KDP | SCHEDULED |
| 2026-10-10 | UR722 | HRE-LUN | 16:00 | 5X-KDP | SCHEDULED |
| 2026-10-10 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-10-10 | UR720 | LUN-HRE | 23:45 | ET-APL | SCHEDULED |
| 2026-10-11 | UR343 | MBA-EBB | 21:40 | 5X-EQU | SCHEDULED |
| 2026-10-11 | UR334 | ZNZ-JRO | 12:05 | 5X-KOB | SCHEDULED |
| 2026-10-11 | UR720 | LUN-HRE | 23:45 | 5X-KOB | SCHEDULED |
| 2026-10-11 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-10-12 | UR111 | LGW-EBB | 19:35 | 5X-NIL | SCHEDULED |
| 2026-10-13 | UR323 | DAR-EBB | 23:50 | 5X-KOB | SCHEDULED |
| 2026-10-14 | UR111 | LGW-EBB | 20:10 | 5X-NIL | SCHEDULED |
| 2026-10-15 | UR343 | MBA-EBB | 22:40 | 5X-KOB | SCHEDULED |
| 2026-10-15 | UR722 | HRE-LUN | 15:45 | ET-APL | SCHEDULED |
| 2026-10-16 | UR720 | LUN-HRE | 23:45 | 5X-KDP | SCHEDULED |
| 2026-10-17 | UR722 | HRE-LUN | 15:45 | 5X-KDP | SCHEDULED |
| 2026-10-17 | UR111 | LGW-EBB | 19:15 | 5X-NIL | SCHEDULED |
| 2026-10-17 | UR431 | BOM-EBB | 01:10 | 5X-NIL | SCHEDULED |
| 2026-10-17 | UR720 | LUN-HRE | 23:45 | ET-APL | SCHEDULED |
| 2026-10-18 | UR201 | NBO-EBB | 11:00 | 5X-KDP | SCHEDULED |
| 2026-10-18 | UR120 | EBB-JUB | 14:00 | 5X-KDP | SCHEDULED |
| 2026-10-18 | UR121 | JUB-EBB | 15:10 | 5X-KDP | SCHEDULED |
| 2026-10-18 | UR521 | MGQ-EBB | 08:30 | 5X-EQU | SCHEDULED |
| 2026-10-18 | UR321 | DAR-EBB | 14:35 | 5X-EQU | SCHEDULED |
| 2026-10-18 | UR334 | ZNZ-JRO | 12:05 | 5X-KOB | SCHEDULED |
| 2026-10-18 | UR334 | JRO-EBB | 14:05 | 5X-KOB | SCHEDULED |
| 2026-10-18 | UR720 | HRE-EBB | 01:45 | ET-APL | SCHEDULED |
| 2026-10-18 | UR901 | LOS-EBB | 13:30 | ET-APL | SCHEDULED |

## Legs at/after the export end (unverifiable)

| date | flight | route | STD (local) | reg | plan status |
|---|---|---|---|---|---|
| 2026-10-18 | UR342 | EBB-MBA | 18:50 | 5X-KDP | SCHEDULED |
| 2026-10-18 | UR343 | MBA-EBB | 21:40 | 5X-KDP | SCHEDULED |
| 2026-10-18 | UR206 | EBB-NBO | 17:40 | 5X-EQU | SCHEDULED |
| 2026-10-18 | UR207 | NBO-EBB | 19:55 | 5X-EQU | SCHEDULED |
| 2026-10-18 | UR208 | EBB-NBO | 22:10 | 5X-EQU | SCHEDULED |
| 2026-10-18 | UR360 | EBB-BJM | 16:30 | 5X-KOB | SCHEDULED |
| 2026-10-18 | UR361 | BJM-EBB | 17:45 | 5X-KOB | SCHEDULED |
| 2026-10-18 | UR720 | EBB-LUN | 21:00 | 5X-KOB | SCHEDULED |
| 2026-10-18 | UR720 | LUN-HRE | 23:45 | 5X-KOB | SCHEDULED |
| 2026-10-18 | UR111 | LGW-EBB | 19:15 | 5X-NIL | SCHEDULED |
| 2026-10-18 | UR712 | EBB-JNB | 23:30 | ET-APL | SCHEDULED |

Recurring gap patterns: triangle middle sectors (UR720 LUN-HRE, UR722 HRE-LUN,
UR334 ZNZ-JRO), late UR343 MBA-EBB and the overnight UR111 LGW-EBB.
Note: 10 Oct originally looked like a total recording blackout (1 track); the
main-repo export of 2026-10-19 added 18 tracks (17 on 10 Oct plus the UR111
inbound of 9 Oct) and that day now matches like any other.
