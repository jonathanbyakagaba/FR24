# September coverage — checked against `FR data.zip`

*This file tracks what is missing across the whole archive (aircraft, weather, runways, events not observed). For the day-by-day picture — which dates are unfinished and exactly which flights are short — see **`date_coverage.md`**.*

Verified against the export as published (**2026-10-03 20:31:52Z UTC** is its newest fix — pass `FR24_PUSH=` to name the commit) (`FR data.zip`, 6.66 MB, 802 tracks).

**Archive: 802 tracks · 334,309 fixes · log 610 flights, 01SEP26–30SEP26.**

---

## Which dates are covered

| date | day | tracks | log | METAR | |
|---|---|---|---|---|---|
| 01 Sep | Tue | 17 | 17 | 0 | ✓ |
| 02 Sep | Wed | 24 | 22 | 0 | ✓ |
| 03 Sep | Thu | 15 | 14 | 0 | ✓ |
| 04 Sep | Fri | 25 | 26 | 0 | ✓ |
| 05 Sep | Sat | 21 | 19 | 0 | ✓ |
| 06 Sep | Sun | 26 | 28 | 0 | ✓ |
| 07 Sep | Mon | 23 | 23 | 0 | ✓ |
| 08 Sep | Tue | 19 | 21 | 0 | ✓ |
| 09 Sep | Wed | 21 | 19 | 0 | ✓ |
| 10 Sep | Thu | 15 | 15 | 0 | ✓ |
| 11 Sep | Fri | 26 | 26 | 0 | ✓ |
| 12 Sep | Sat | 22 | 18 | 0 | ✓ |
| 13 Sep | Sun | 27 | 30 | 0 | ✓ |
| 14 Sep | Mon | 16 | 18 | 0 | ✓ |
| 15 Sep | Tue | 18 | 18 | 0 | ✓ |
| 16 Sep | Wed | 18 | 16 | 0 | ✓ |
| 17 Sep | Thu | 13 | 13 | 0 | ✓ |
| 18 Sep | Fri | 23 | 22 | 0 | ✓ |
| 19 Sep | Sat | 17 | 15 | 0 | ✓ |
| 20 Sep | Sun | 19 | 21 | 0 | ✓ |
| 21 Sep | Mon | 19 | 19 | 0 | ✓ |
| 22 Sep | Tue | 17 | 19 | 0 | ✓ |
| 23 Sep | Wed | 23 | 21 | 0 | ✓ |
| 24 Sep | Thu | 16 | 15 | 0 | ✓ |
| 25 Sep | Fri | 29 | 28 | 0 | ✓ |
| 26 Sep | Sat | 21 | 18 | 0 | ✓ |
| 27 Sep | Sun | 26 | 24 | 0 | ✓ |
| 28 Sep | Mon | 22 | 23 | 0 | ✓ |
| 29 Sep | Tue | 22 | 22 | 0 | ✓ |
| 30 Sep | Wed | 25 | 20 | 0 | ✓ |

**Covered: 1–30 September, every day.** Tracks are counted by UTC start and log entries by local departure date, so the two differ on the days that straddle midnight. The next day (01 Oct) is not in any export yet.

---

## The gap the app exposes — legs flown but absent from the export

The per-tail app pages now cover 25 Jul – 30 Sep, so every leg they list can be checked against the export. **607 of 701 app rows are matched by a track**; 94 are not. Of those, **76 have no track at all** for that flight number and sector on either the app date or the next local day:

| date (app) | tail | flight | sector |
|---|---|---|---|
| 25 Jul | 5X-NIL | UR430 | EBB–BOM |
| 26 Jul | 5X-NIL | UR110 | EBB–LGW |
| 26 Jul | 5X-NIL | UR111 | LGW–EBB |
| 26 Jul | 5X-NIL | UR431 | BOM–EBB |
| 28 Jul | 5X-NIL | UR110 | EBB–LGW |
| 28 Jul | 5X-NIL | UR111 | LGW–EBB |
| 29 Jul | 5X-NIL | UR430 | EBB–BOM |
| 30 Jul | 5X-NIL | UR431 | BOM–EBB |
| 31 Jul | 5X-NIL | UR110 | EBB–LGW |
| 31 Jul | 5X-NIL | UR111 | LGW–EBB |
| 01 Aug | 5X-NIL | UR430 | EBB–BOM |
| 02 Aug | 5X-NIL | UR110 | EBB–LGW |
| 02 Aug | 5X-NIL | UR111 | LGW–EBB |
| 02 Aug | 5X-NIL | UR431 | BOM–EBB |
| 04 Aug | 5X-NIL | UR110 | EBB–LGW |
| 04 Aug | 5X-NIL | UR111 | LGW–EBB |
| 05 Aug | 5X-NIL | UR430 | EBB–BOM |
| 06 Aug | 5X-NIL | UR431 | BOM–EBB |
| 07 Aug | 5X-NIL | UR110 | EBB–LGW |
| 07 Aug | 5X-NIL | UR111 | LGW–EBB |
| 08 Aug | 5X-NIL | UR430 | EBB–BOM |
| 09 Aug | 5X-NIL | UR110 | EBB–LGW |
| 09 Aug | 5X-NIL | UR111 | LGW–EBB |
| 09 Aug | 5X-NIL | UR431 | BOM–EBB |
| 11 Aug | 5X-NIL | UR110 | EBB–LGW |
| 11 Aug | 5X-NIL | UR111 | LGW–EBB |
| 12 Aug | 5X-NIL | UR430 | EBB–BOM |
| 13 Aug | 5X-NIL | UR431 | BOM–EBB |
| 14 Aug | 5X-NIL | UR110 | EBB–LGW |
| 14 Aug | 5X-NIL | UR111 | LGW–EBB |
| 15 Aug | 5X-NIL | UR430 | EBB–BOM |
| 16 Aug | 5X-NIL | UR110 | EBB–LGW |
| 16 Aug | 5X-NIL | UR111 | LGW–EBB |
| 16 Aug | 5X-NIL | UR431 | BOM–EBB |
| 18 Aug | 5X-NIL | UR110 | EBB–LGW |
| 18 Aug | 5X-NIL | UR111 | LGW–EBB |
| 19 Aug | 5X-NIL | UR430 | EBB–BOM |
| 20 Aug | 5X-NIL | UR431 | BOM–EBB |
| 21 Aug | 5X-NIL | UR110 | EBB–LGW |
| 21 Aug | 5X-NIL | UR111 | LGW–EBB |
| 22 Aug | 5X-NIL | UR430 | EBB–BOM |
| 23 Aug | 5X-NIL | UR110 | EBB–LGW |
| 23 Aug | 5X-NIL | UR111 | LGW–EBB |
| 23 Aug | 5X-NIL | UR431 | BOM–EBB |
| 25 Aug | 5X-NIL | UR110 | EBB–LGW |
| 25 Aug | 5X-NIL | UR111 | LGW–EBB |
| 26 Aug | 5X-NIL | UR430 | EBB–BOM |
| 27 Aug | 5X-NIL | UR431 | BOM–EBB |
| 28 Aug | 5X-NIL | UR110 | EBB–LGW |
| 28 Aug | 5X-NIL | UR111 | LGW–EBB |
| 29 Aug | 5X-NIL | UR430 | EBB–BOM |
| 30 Aug | 5X-NIL | UR111 | LGW–EBB |
| 31 Aug | 5X-EQU | UR320 | – |
| 31 Aug | 5X-EQU | UR720 | LUN–HRE |
| 31 Aug | 5X-KOB | UR712 | – |
| 31 Aug | ET-APL | UR208 | EBB–NBO |
| 15 Sep | 5X-KOB | UR209 | NBO–EBB |
| 16 Sep | 5X-EQU | UR322 | EBB–DAR |
| 16 Sep | 5X-KDP | UR711 | JNB–EBB |
| 16 Sep | 5X-KOB | UR334 | ZNZ–JRO |
| 17 Sep | ET-APL | UR720 | LUN–HRE |
| 18 Sep | 5X-KDP | UR334 | ZNZ–JRO |
| 18 Sep | 5X-KDP | UR720 | LUN–HRE |
| 20 Sep | 5X-KDP | UR121 | JUB–EBB |
| 20 Sep | 5X-KOB | UR334 | EBB–ZNZ |
| 20 Sep | 5X-KOB | UR334 | ZNZ–JRO |
| 21 Sep | 5X-KOB | UR720 | LUN–HRE |
| 27 Sep | 5X-EQU | UR523 | EBB–EBB |
| 27 Sep | 5X-EQU | UR523 | EBB–UG-0013 |
| 27 Sep | 5X-EQU | UR523 | UG-0013–EBB |
| 27 Sep | 5X-KDP | UR334 | ZNZ–JRO |
| 29 Sep | 5X-EQU | UR209 | NBO–EBB |
| 29 Sep | 5X-KDP | UR523 | EBB–UG-0013 |
| 29 Sep | 5X-KOB | UR720 | HRE–EBB |
| 30 Sep | 5X-KDP | UR523 | EBB–UG-0013 |
| 30 Sep | 5X-KDP | UR523 | UG-0013–EBB |

**8 of the 76 are the middle sector of a triangle rotation** — the HRE–LUN / LUN–HRE hop or ZNZ–JRO. The export carries the Entebbe legs of those rotations and, on many days, nothing for the sector between the two outstations, even though the app lists it as flown. That is the single largest systematic gap in the source export.

The other 18 unmatched rows **do** have a track for that flight number and sector — but on the next local day, with the app dating the row a day earlier:

| date (app) | tail | flight | sector | app status | track in export |
|---|---|---|---|---|---|
| 31 Aug | 5X-EQU | UR321 | DAR–EBB | green | 2026-09-01 11:23Z |
| 31 Aug | 5X-KDP | UR361 | BJM–EBB | green | 2026-09-01 15:35Z |
| 31 Aug | 5X-KDP | UR360 | EBB–BJM | green | 2026-09-01 14:04Z |
| 31 Aug | 5X-KDP | UR720 | HRE–EBB | green | 2026-09-01 00:05Z |
| 04 Sep | 5X-KOB | UR720 | LUN–HRE | green | 2026-09-05 21:50Z |
| 06 Sep | 5X-EQU | UR720 | LUN–HRE | green | 2026-09-07 21:49Z |
| 09 Sep | 5X-KOB | UR722 | HRE–LUN | green | 2026-09-10 14:16Z |
| 15 Sep | ET-APL | UR722 | EBB–HRE | green | 2026-09-16 09:13Z |
| 17 Sep | 5X-EQU | UR361 | BJM–EBB | green | 2026-09-18 15:17Z |
| 17 Sep | 5X-KOB | UR121 | JUB–EBB | green | 2026-09-18 13:19Z |
| 18 Sep | 5X-EQU | UR520 | EBB–MGQ | red | 2026-09-19 02:13Z |
| 20 Sep | ET-APL | UR900 | EBB–LOS | green | 2026-09-21 07:11Z |
| 20 Sep | ET-APL | UR720 | HRE–EBB | green | 2026-09-21 01:16Z |
| 22 Sep | 5X-NIL | UR111 | LGW–EBB | red | 2026-09-23 06:46Z |
| 22 Sep | ET-APL | UR722 | HRE–LUN | green | 2026-09-23 13:16Z |
| 27 Sep | ET-APL | UR321 | DAR–EBB | red | 2026-09-28 11:14Z |
| 27 Sep | ET-APL | UR320 | EBB–DAR | grey | 2026-09-28 08:24Z |
| 29 Sep | 5X-KOB | UR720X | NBO–EBB | grey | next day |

For 7 of these the timing settles it: the track left in the last hours of the app's UTC day, so the app was dating the leg by its UTC day and the log by the airport's local day — those rows are joined by the build (see `tails.csv`, `track_date`). For the rest the app row is mostly green (on time), which argues the leg flew on the app's own date and the export is missing that day's track — the same gap as the table above, with a same-sector track one day later. The two readings cannot be told apart from this data, so those rows are left unjoined rather than guessed.

---

## Same-weekday check (independent of the app)

For days where the app has no coverage, compare the services flown with the other days of the same weekday. An entry here is a **candidate** gap, not a confirmed one — the service may simply not have operated.

- **01 Sep (Tue)** — 17 services vs 4 peer days; not seen: UGD120, UGD121, UGD200, UGD201, UGD209, UGD720, UGD720X.
- **02 Sep (Wed)** — 22 services vs 4 peer days; not seen: UGD111.
- **03 Sep (Thu)** — 14 services vs 3 peer days; not seen: UGD322D, UGD343, UGD712, UGD902.
- **04 Sep (Fri)** — 25 services vs 3 peer days; not seen: UGD520, UGD713, UGD720.
- **05 Sep (Sat)** — 19 services vs 3 peer days; not seen: UGD343.
- **06 Sep (Sun)** — 28 services vs 3 peer days; not seen: UGD720.
- **07 Sep (Mon)** — 23 services vs 3 peer days; not seen: UGD342, UGD343.
- **08 Sep (Tue)** — 21 services vs 4 peer days; not seen: UGD207D, UGD720, UGD720X.
- **09 Sep (Wed)** — 19 services vs 4 peer days; not seen: UGD111, UGD120, UGD121, UGD722.
- **10 Sep (Thu)** — 15 services vs 3 peer days; not seen: UGD322D, UGD343, UGD712.
- **11 Sep (Fri)** — 26 services vs 3 peer days; not seen: UGD520, UGD713.
- **12 Sep (Sat)** — 18 services vs 3 peer days; not seen: UGD343, UGD720.
- **14 Sep (Mon)** — 17 services vs 3 peer days; not seen: UGD322, UGD323, UGD342, UGD343, UGD710, UGD711, UGD720.
- **15 Sep (Tue)** — 18 services vs 4 peer days; not seen: UGD207D, UGD209, UGD720, UGD720X, UGD722.
- **16 Sep (Wed)** — 16 services vs 4 peer days; not seen: UGD111, UGD120, UGD121, UGD322, UGD334, UGD343, UGD711.
- **17 Sep (Thu)** — 13 services vs 3 peer days; not seen: UGD121, UGD322, UGD323, UGD361, UGD712.
- **18 Sep (Fri)** — 22 services vs 3 peer days; not seen: UGD322, UGD334, UGD343, UGD520, UGD521, UGD720.
- **19 Sep (Sat)** — 15 services vs 3 peer days; not seen: UGD323, UGD720, UGD722.
- **20 Sep (Sun)** — 21 services vs 3 peer days; not seen: UGD121, UGD208, UGD334, UGD342, UGD343, UGD720, UGD900.
- **21 Sep (Mon)** — 19 services vs 3 peer days; not seen: UGD209, UGD322, UGD323, UGD710, UGD711, UGD720.
- **22 Sep (Tue)** — 19 services vs 4 peer days; not seen: UGD111, UGD207D, UGD720, UGD720X, UGD722.
- **23 Sep (Wed)** — 21 services vs 4 peer days; not seen: UGD120, UGD121.
- **24 Sep (Thu)** — 15 services vs 3 peer days; not seen: UGD322D, UGD343, UGD902.
- **25 Sep (Fri)** — 27 services vs 3 peer days; not seen: UGD520.
- **26 Sep (Sat)** — 18 services vs 3 peer days; not seen: UGD343, UGD720.
- **27 Sep (Sun)** — 24 services vs 3 peer days; not seen: UGD320, UGD321, UGD334, UGD900, UGD901.
- **28 Sep (Mon)** — 22 services vs 3 peer days; not seen: UGD342, UGD343, UGD720.
- **29 Sep (Tue)** — 22 services vs 4 peer days; not seen: UGD207D, UGD209, UGD720.
- **30 Sep (Wed)** — 20 services vs 4 peer days; not seen: UGD111, UGD120, UGD121.

---

## Other data still flagged as missing

| | now | note |
|---|---|---|
| **Aircraft assignment** | 607 of 701 app rows · 603 of 610 logged flights | the per-tail pages run to 30 Sep; the remainder are rows the export has no track for (above) |
| **Weather** | 574 take-off / 569 landing of 610 | Juba has no METAR station; the rest are legs whose station report is absent at that hour |
| **Runway identification** | 762 departures / 769 arrivals of 802 tracks | the remainder start airborne or end before touchdown |
| **Events not observed** | 15 take-offs · 38 landings | times shown are the last real observation, never a guess |
| **Local sortie** | 1 track(s) | `UGD520` on 18SEP26 took off and landed at EBB — an air test or training sortie, not a service |
| **Other operators** | — | September holds 612 Uganda-call-sign tracks plus `AF523` (Hoima) ×9, Ethiopian ×2, Garuda ×2; the archive also carries 44 earlier tracks from Ethiopian ×12, Qatar ×6, Brussels ×4, Turkish ×4, Rwandair ×4, Kenya ×4, KLM ×3, Garuda ×2, EgyptAir ×2, (blank) ×1, flydubai ×1, Kenya Airways ×1, none after 20 Jul |

---

## What the screenshots cover

| tail | app rows | window | 11 Sep | 12 Sep | 22 Sep | 30 Sep |
|---|---|---|---|---|---|---|
| 5X-EQU | 128 | 31 Aug – 30 Sep | 31 | 0 | 0 | 97 |
| 5X-KDP | 160 | 31 Aug – 30 Sep | 54 | 4 | 6 | 96 |
| 5X-KOB | 186 | 31 Aug – 30 Sep | 53 | 6 | 28 | 99 |
| 5X-NIL | 96 | 25 Jul – 29 Sep | 0 | 0 | 0 | 96 |
| ET-APL | 131 | 31 Aug – 30 Sep | 36 | 0 | 1 | 94 |

The pages are per-tail snapshots, each holding roughly the last hundred flights, so a tail's window opens whenever its page ran out of history: **the 11 Sep + 12 Sep + 22 Sep + 30 Sep batches** supply 705 status rows. 485 of those rows come from the newest capture (2026-09-30 20:4x-20:5x), which is why the days nearest the capture are the best covered and the older ones thin out at the far end of each page, not the near one.

---

## Shortest path to complete

1. **Keep the daily export coming** — the archive is only as complete as the last upload, and this one runs to 03 Oct, past the last logged day (30 Sep), so no September day is missing from it.
2. **Re-export the triangle middle sectors** — the HRE–LUN / ZNZ–JRO hops are the bulk of what the app sees and the export does not.
3. **Keep sending the per-tail screenshots** — they are what ties an airframe to each leg; coverage now stands at **603 of 610** logged flights carrying an aircraft.
4. Juba's weather cannot be closed from this source.
