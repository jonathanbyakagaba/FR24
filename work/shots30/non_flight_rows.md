# 30 September captures — rows that are not flights

From `work/screens_20260930_rows.csv`, written by `work/make_batch_30.py`.

## No flight number in the app

| capture | slot | tail | date | origin | dest | dot | what the page shows |
|---|---|---|---|---|---|---|---|
| 4740_Flightradar24 | 94 | 5X-KDP | 2026-09-15 | EBB | EBB | grey | `Sep 15 KDP  |  S Entebbe (EBB) 4  |  M. Entebbe (EBB)` |
| 5121_Flightradar24 | 20 | 5X-NIL | 2026-09-17 | EBB | N/A | grey | `Sep 17 TEST  |  Ss Entebbe (EBB) VY  |  Wo N/A` |

## Row left incomplete by the capture

- 4706_Flightradar24 slot 56 (5X-EQU): 2026-09-14 UR200 — the row is cut off at the foot of the capture, so it carries no route; the archive has the leg.

## Header and photograph block

The slots above the first flight row hold the aircraft photograph and its
specification block; they are not flights and are excluded by
`work/page_meta_30.py`. The block itself is kept in
`work/shots30/airframes.csv`.
