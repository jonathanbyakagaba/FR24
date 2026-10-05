# Departure punctuality

The app status dot is available for **603 of 610** logged flights. It is the operator-facing judgement; the delay column is our own measurement.

No leg in this month can be scored against a timetable: the build holds no `reference/schedule_<month>.csv` for this month. Every delay below is therefore measured against the service’s own usual time, which cannot see a habit — a service that always leaves 40 minutes late scores zero here. Where a timetable exists for a date, `schedule_delays.csv` is the file that answers the scheduling question instead.

| app dot | flights | what it means | measured departure delay (median) |
|---|---|---|---|
| green | 502 | on time | +0 min |
| amber | 40 | late | +36 min |
| red | 53 | very late | +108 min |
| grey | 8 | no data | -122 min |

**The dot is not a cancellation flag.** Every red-flagged leg in this set still flew — it left late.

## Worst departures in the month

| date | flight | tail | sector | dep (local) | app dot | vs usual |
|---|---|---|---|---|---|---|
| 2026-09-23 | UGD111 |  | LGW-EBB | 0746 | — | +692 min |
| 2026-09-20 | UGD360 | 5X-KDP | EBB-BJM | 2012 | red | +214 min |
| 2026-09-20 | UGD361 | 5X-KDP | BJM-EBB | 2059 | red | +213 min |
| 2026-09-20 | UGD321 | 5X-KDP | DAR-EBB | 1724 | red | +179 min |
| 2026-09-20 | UGD320 | 5X-KDP | EBB-DAR | 1445 | red | +178 min |
| 2026-09-29 | UGD206 | 5X-KOB | EBB-NBO | 2028 | red | +163 min |
| 2026-09-16 | UGD361 | 5X-KOB | BJM-EBB | 2005 | red | +159 min |
| 2026-09-16 | UGD360 | 5X-KOB | EBB-BJM | 1911 | red | +153 min |
| 2026-09-20 | UGD720 | 5X-KOB | EBB-LUN | 2317 | red | +123 min |
| 2026-09-21 | UGD720 | 5X-KOB | HRE-EBB | 0316 | red | +108 min |
| 2026-09-08 | UGD111 | 5X-NIL | LGW-EBB | 2157 | red | +103 min |
| 2026-09-27 | UGD206 | 5X-EQU | EBB-NBO | 1919 | red | +94 min |

## By aircraft

| tail | flights | on time | late | very late | not captured |
|---|---|---|---|---|---|
|  | 7 | 0 | 0 | 0 | 7 |
| 5X-EQU | 118 | 110 | 4 | 4 | 0 |
| 5X-KDP | 147 | 131 | 1 | 8 | 0 |
| 5X-KOB | 176 | 155 | 6 | 14 | 0 |
| 5X-NIL | 41 | 30 | 10 | 1 | 0 |
| ET-APL | 121 | 76 | 19 | 26 | 0 |

