# October coverage — checked against `FR data.zip`

*This file tracks what is missing across the whole archive (aircraft, weather, runways, events not observed). For the day-by-day picture — which dates are unfinished and exactly which flights are short — see **`date_coverage.md`**.*

Verified against the export as published (**2026-10-05 02:23:07Z UTC** is its newest fix — pass `FR24_PUSH=` to name the commit) (`FR data.zip`, 6.84 MB, 826 tracks).

**Archive: 826 tracks · 343,491 fixes · log 82 flights, 01OCT26–05OCT26.**

---

## Which dates are covered

| date | day | tracks | log | METAR | |
|---|---|---|---|---|---|
| 01 Oct | Thu | 16 | 16 | 0 | ✓ |
| 02 Oct | Fri | 27 | 27 | 0 | ✓ |
| 03 Oct | Sat | 19 | 17 | 0 | ✓ |
| 04 Oct | Sun | 17 | 21 | 0 | ✓ |
| 05 Oct | Mon | 1 | 1 | 0 | ✓ |

**Covered: 01 Oct – 05 Oct, 5 of 31 days.** Tracks are counted by UTC start and log entries by local departure date, so the two differ on the days that straddle midnight. The next day (06 Oct) is not in any export yet.

---

## The gap the app exposes — legs flown but absent from the export

The per-tail app pages now cover 25 Jul – 30 Sep, so every leg they list can be checked against the export. **607 of 701 app rows are matched by a track**; 94 are not. Of those, **94 have no track at all** for that flight number and sector on either the app date or the next local day:

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
| 31 Aug | 5X-EQU | UR321 | DAR–EBB |
| 31 Aug | 5X-EQU | UR720 | LUN–HRE |
| 31 Aug | 5X-KDP | UR360 | EBB–BJM |
| 31 Aug | 5X-KDP | UR361 | BJM–EBB |
| 31 Aug | 5X-KDP | UR720 | HRE–EBB |
| 31 Aug | 5X-KOB | UR712 | – |
| 31 Aug | ET-APL | UR208 | EBB–NBO |
| 04 Sep | 5X-KOB | UR720 | LUN–HRE |
| 06 Sep | 5X-EQU | UR720 | LUN–HRE |
| 09 Sep | 5X-KOB | UR722 | HRE–LUN |
| 15 Sep | 5X-KOB | UR209 | NBO–EBB |
| 15 Sep | ET-APL | UR722 | EBB–HRE |
| 16 Sep | 5X-EQU | UR322 | EBB–DAR |
| 16 Sep | 5X-KDP | UR711 | JNB–EBB |
| 16 Sep | 5X-KOB | UR334 | ZNZ–JRO |
| 17 Sep | 5X-EQU | UR361 | BJM–EBB |
| 17 Sep | 5X-KOB | UR121 | JUB–EBB |
| 17 Sep | ET-APL | UR720 | LUN–HRE |
| 18 Sep | 5X-EQU | UR520 | EBB–MGQ |
| 18 Sep | 5X-KDP | UR334 | ZNZ–JRO |
| 18 Sep | 5X-KDP | UR720 | LUN–HRE |
| 20 Sep | 5X-KDP | UR121 | JUB–EBB |
| 20 Sep | 5X-KOB | UR334 | EBB–ZNZ |
| 20 Sep | 5X-KOB | UR334 | ZNZ–JRO |
| 20 Sep | ET-APL | UR720 | HRE–EBB |
| 20 Sep | ET-APL | UR900 | EBB–LOS |
| 21 Sep | 5X-KOB | UR720 | LUN–HRE |
| 22 Sep | 5X-NIL | UR111 | LGW–EBB |
| 22 Sep | ET-APL | UR722 | HRE–LUN |
| 27 Sep | 5X-EQU | UR523 | EBB–EBB |
| 27 Sep | 5X-EQU | UR523 | EBB–UG-0013 |
| 27 Sep | 5X-EQU | UR523 | UG-0013–EBB |
| 27 Sep | 5X-KDP | UR334 | ZNZ–JRO |
| 27 Sep | ET-APL | UR320 | EBB–DAR |
| 27 Sep | ET-APL | UR321 | DAR–EBB |
| 29 Sep | 5X-EQU | UR209 | NBO–EBB |
| 29 Sep | 5X-KDP | UR523 | EBB–UG-0013 |
| 29 Sep | 5X-KOB | UR720 | HRE–EBB |
| 29 Sep | 5X-KOB | UR720X | NBO–EBB |
| 30 Sep | 5X-KDP | UR523 | EBB–UG-0013 |
| 30 Sep | 5X-KDP | UR523 | UG-0013–EBB |

**12 of the 94 are the middle sector of a triangle rotation** — the HRE–LUN / LUN–HRE hop or ZNZ–JRO. The export carries the Entebbe legs of those rotations and, on many days, nothing for the sector between the two outstations, even though the app lists it as flown. That is the single largest systematic gap in the source export.

The other 0 unmatched rows **do** have a track for that flight number and sector — but on the next local day, with the app dating the row a day earlier:

| date (app) | tail | flight | sector | app status | track in export |
|---|---|---|---|---|---|

For 7 of these the timing settles it: the track left in the last hours of the app's UTC day, so the app was dating the leg by its UTC day and the log by the airport's local day — those rows are joined by the build (see `tails.csv`, `track_date`). For the rest the app row is mostly green (on time), which argues the leg flew on the app's own date and the export is missing that day's track — the same gap as the table above, with a same-sector track one day later. The two readings cannot be told apart from this data, so those rows are left unjoined rather than guessed.

---

## Same-weekday check (independent of the app)

For days where the app has no coverage, compare the services flown with the other days of the same weekday. An entry here is a **candidate** gap, not a confirmed one — the service may simply not have operated.


---

## Other data still flagged as missing

| | now | note |
|---|---|---|
| **Aircraft assignment** | 607 of 701 app rows · 0 of 82 logged flights | the per-tail pages run to 30 Sep; the remainder are rows the export has no track for (above) |
| **Weather** | 77 take-off / 76 landing of 82 | Juba has no METAR station; the rest are legs whose station report is absent at that hour |
| **Runway identification** | 785 departures / 792 arrivals of 826 tracks | the remainder start airborne or end before touchdown |
| **Events not observed** | 2 take-offs · 4 landings | times shown are the last real observation, never a guess |
| **Other operators** | — | October holds 80 Uganda-call-sign tracks; the archive also carries 57 earlier tracks from Ethiopian ×14, `AF523` (Hoima) ×9, Qatar ×6, Garuda ×4, Brussels ×4, Turkish ×4, Rwandair ×4, Kenya ×4, KLM ×3, EgyptAir ×2, (blank) ×1, flydubai ×1, Kenya Airways ×1, none after 30 Sep |

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

1. **Keep the daily export coming** — the archive is only as complete as the last upload, and this one runs to 05 Oct, past the last logged day (05 Oct), so no October day is missing from it.
2. **Re-export the triangle middle sectors** — the HRE–LUN / ZNZ–JRO hops are the bulk of what the app sees and the export does not.
3. **Keep sending the per-tail screenshots** — they are what ties an airframe to each leg; coverage now stands at **0 of 82** logged flights carrying an aircraft.
4. Juba's weather cannot be closed from this source.
