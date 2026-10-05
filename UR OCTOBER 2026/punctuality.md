# Departure punctuality

The app status dot is available for **0 of 82** logged flights. It is the operator-facing judgement; the delay column is our own measurement.

**66 of 82** legs are measured against the published timetable (`schedule_2026-10.csv`) — the only basis that can call a habit late. The rest fall back to each service’s usual time, because the build holds no timetable for their date. The `slot_basis` column says which of the two every row used; a table that mixed them without saying so would be comparing two different questions.

No leg in this month carries a status dot: the per-tail app screenshots for these dates have not arrived, so the operator’s own judgement is simply not in the build yet. Everything below is measured here, from the tracks.

## Worst departures in the month

| date | flight | tail | sector | dep (local) | app dot | vs usual |
|---|---|---|---|---|---|---|
| 2026-10-04 | UGD360 |  | EBB-BJM | 2221 | — | +351 min |
| 2026-10-04 | UGD321 |  | DAR-EBB | 1944 | — | +324 min |
| 2026-10-04 | UGD320 |  | EBB-DAR | 1657 | — | +313 min |
| 2026-10-04 | UGD334 |  | ZNZ-JRO | 1639 | — | +275 min |
| 2026-10-04 | UGD334 |  | JRO-EBB | 1823 | — | +258 min |
| 2026-10-04 | UGD206 |  | EBB-NBO | 2041 | — | +181 min |
| 2026-10-04 | UGD334 |  | EBB-ZNZ | 1213 | — | +179 min |
| 2026-10-02 | UGD711 |  | JNB-EBB | 1508 | — | +84 min |
| 2026-10-02 | UGD710 |  | EBB-JNB | 1014 | — | +44 min |
| 2026-10-02 | UGD111 |  | LGW-EBB | 2005 | — | +31 min |
| 2026-10-04 | UGD901 |  | LOS-EBB | 1359 | — | +29 min |
| 2026-10-02 | UGD903 |  | LOS-EBB | 0224 | — | +25 min |

## By aircraft

| tail | flights | on time | late | very late | not captured |
|---|---|---|---|---|---|
|  | 82 | 0 | 0 | 0 | 82 |

