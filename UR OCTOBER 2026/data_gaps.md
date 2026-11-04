# October coverage — checked against `FR data.zip`

*This file tracks what is missing across the whole archive (aircraft, weather, runways, events not observed). For the day-by-day picture — which dates are unfinished and exactly which flights are short — see **`date_coverage.md`**.*

Verified against the export as published (**2026-10-18T15:19:28Z UTC** is its newest fix — pass `FR24_PUSH=` to name the commit) (`FR data.zip`, 9.24 MB, 1108 tracks).

**Archive: 1108 tracks · 461,856 fixes · log 360 flights, 01OCT26–18OCT26.**

---

## Which dates are covered

| date | day | tracks | log | METAR | |
|---|---|---|---|---|---|
| 01 Oct | Thu | 16 | 16 | 0 | ✓ |
| 02 Oct | Fri | 27 | 27 | 0 | ✓ |
| 03 Oct | Sat | 19 | 17 | 0 | ✓ |
| 04 Oct | Sun | 22 | 24 | 0 | ✓ |
| 05 Oct | Mon | 20 | 21 | 0 | ✓ |
| 06 Oct | Tue | 20 | 21 | 0 | ✓ |
| 07 Oct | Wed | 22 | 20 | 0 | ✓ |
| 08 Oct | Thu | 16 | 15 | 0 | ✓ |
| 09 Oct | Fri | 25 | 26 | 0 | ✓ |
| 10 Oct | Sat | 19 | 17 | 0 | ✓ |
| 11 Oct | Sun | 24 | 26 | 0 | ✓ |
| 12 Oct | Mon | 23 | 23 | 0 | ✓ |
| 13 Oct | Tue | 20 | 22 | 0 | ✓ |
| 14 Oct | Wed | 22 | 20 | 0 | ✓ |
| 15 Oct | Thu | 15 | 15 | 0 | ✓ |
| 16 Oct | Fri | 25 | 26 | 0 | ✓ |
| 17 Oct | Sat | 17 | 15 | 0 | ✓ |
| 18 Oct | Sun | 6 | 9 | 0 | ✓ |

**Covered: 01 Oct – 18 Oct, 18 of 31 days.** Tracks are counted by UTC start and log entries by local departure date, so the two differ on the days that straddle midnight. The next day (19 Oct) is not in any export yet.

---

## The gap the app exposes — legs flown but absent from the export

The per-tail app pages now cover 25 Jul – 18 Oct, so every leg they list can be checked against the export. **607 of 1100 app rows are matched by a track**; 493 are not. Of those, **134 have no track at all** for that flight number and sector on either the app date or the next local day:

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
| 03 Oct | 5X-KDP | UR722 | HRE–LUN |
| 03 Oct | ET-APL | UR720 | LUN–HRE |
| 07 Oct | 5X-NIL | UR111 | LGW–EBB |
| 09 Oct | 5X-KDP | UR334 | ZNZ–JRO |
| 09 Oct | 5X-KDP | UR720 | LUN–HRE |
| 10 Oct | 5X-KDP | UR722 | HRE–LUN |
| 10 Oct | 5X-NIL | UR111 | LGW–EBB |
| 10 Oct | ET-APL | UR720 | LUN–HRE |
| 11 Oct | 5X-EQU | UR323 | NBO–EBB |
| 11 Oct | 5X-EQU | UR343 | MBA–EBB |
| 11 Oct | 5X-KOB | UR334 | ZNZ–JRO |
| 11 Oct | 5X-NIL | UR111 | LGW–EBB |
| 13 Oct | 5X-KDP | UR121 | JUB–EBB |
| 13 Oct | 5X-KOB | UR323 | DAR–EBB |
| 14 Oct | 5X-NIL | UR111 | LGW–EBB |
| 15 Oct | ET-APL | UR722 | HRE–LUN |
| 16 Oct | 5X-KDP | UR720 | LUN–HRE |
| 17 Oct | 5X-KDP | UR722 | HRE–LUN |
| 17 Oct | 5X-NIL | UR111 | LGW–EBB |
| 17 Oct | ET-APL | UR720 | LUN–HRE |
| 18 Oct | 5X-EQU | UR206 | EBB–NBO |
| 18 Oct | 5X-EQU | UR207 | NBO–EBB |
| 18 Oct | 5X-EQU | UR208 | EBB–NBO |
| 18 Oct | 5X-EQU | UR321 | DAR–EBB |
| 18 Oct | 5X-EQU | UR521 | MGQ–EBB |
| 18 Oct | 5X-KDP | UR120 | EBB–JUB |
| 18 Oct | 5X-KDP | UR121 | JUB–EBB |
| 18 Oct | 5X-KDP | UR201 | NBO–EBB |
| 18 Oct | 5X-KDP | UR342 | EBB–MBA |
| 18 Oct | 5X-KDP | UR343 | MBA–EBB |
| 18 Oct | 5X-KOB | UR334 | JRO–EBB |
| 18 Oct | 5X-KOB | UR334 | ZNZ–JRO |
| 18 Oct | 5X-KOB | UR360 | EBB–BJM |
| 18 Oct | 5X-KOB | UR361 | BJM–EBB |
| 18 Oct | 5X-KOB | UR720 | EBB–LUN |
| 18 Oct | 5X-KOB | UR720 | LUN–HRE |
| 18 Oct | 5X-NIL | UR111 | LGW–EBB |
| 18 Oct | ET-APL | UR712 | EBB–JNB |
| 18 Oct | ET-APL | UR720 | HRE–EBB |
| 18 Oct | ET-APL | UR901 | LOS–EBB |

**25 of the 134 are the middle sector of a triangle rotation** — the HRE–LUN / LUN–HRE hop or ZNZ–JRO. The export carries the Entebbe legs of those rotations and, on many days, nothing for the sector between the two outstations, even though the app lists it as flown. That is the single largest systematic gap in the source export.

The other 359 unmatched rows **do** have a track for that flight number and sector — but on the next local day, with the app dating the row a day earlier:

| date (app) | tail | flight | sector | app status | track in export |
|---|---|---|---|---|---|
| 01 Oct | 5X-EQU | UR209 | NBO–EBB | — | 2026-10-01 21:18Z |
| 01 Oct | 5X-EQU | UR360 | EBB–BJM | — | 2026-10-02 13:34Z |
| 01 Oct | 5X-EQU | UR361 | BJM–EBB | — | 2026-10-02 15:13Z |
| 01 Oct | 5X-EQU | UR208 | EBB–NBO | — | next day |
| 01 Oct | 5X-KDP | UR323 | DAR–EBB | — | 2026-10-01 21:24Z |
| 01 Oct | 5X-KDP | UR200 | EBB–NBO | — | 2026-10-02 04:52Z |
| 01 Oct | 5X-KDP | UR201 | NBO–EBB | — | 2026-10-02 07:07Z |
| 01 Oct | 5X-KDP | UR322 | EBB–DAR | — | 2026-10-02 19:03Z |
| 01 Oct | 5X-KOB | UR120 | EBB–JUB | — | 2026-10-02 11:14Z |
| 01 Oct | 5X-KOB | UR121 | JUB–EBB | — | 2026-10-02 13:27Z |
| 01 Oct | 5X-KOB | UR712 | EBB–JNB | — | next day |
| 01 Oct | 5X-NIL | UR431 | BOM–EBB | — | next day |
| 01 Oct | ET-APL | UR722 | EBB–HRE | — | next day |
| 01 Oct | ET-APL | UR722 | HRE–LUN | — | next day |
| 01 Oct | ET-APL | UR722 | LUN–EBB | — | next day |
| 01 Oct | ET-APL | UR902 | EBB–LOS | — | 2026-10-02 19:07Z |
| 02 Oct | 5X-EQU | UR209 | NBO–EBB | — | next day |
| 02 Oct | 5X-EQU | UR200 | EBB–NBO | — | 2026-10-03 05:06Z |
| 02 Oct | 5X-EQU | UR201 | NBO–EBB | — | 2026-10-03 07:30Z |
| 02 Oct | 5X-EQU | UR206 | EBB–NBO | — | next day |
| 02 Oct | 5X-EQU | UR207 | NBO–EBB | — | next day |
| 02 Oct | 5X-EQU | UR322 | EBB–DAR | — | 2026-10-03 18:34Z |
| 02 Oct | 5X-KDP | UR323 | DAR–EBB | — | 2026-10-02 21:41Z |
| 02 Oct | 5X-KDP | UR520 | EBB–MGQ | — | 2026-10-03 01:50Z |
| 02 Oct | 5X-KDP | UR521 | MGQ–EBB | — | 2026-10-03 05:13Z |
| 02 Oct | 5X-KDP | UR120 | EBB–JUB | — | 2026-10-03 10:06Z |
| 02 Oct | 5X-KDP | UR121 | JUB–EBB | — | 2026-10-03 12:03Z |
| 02 Oct | 5X-KDP | UR342 | EBB–MBA | — | next day |
| 02 Oct | 5X-KDP | UR343 | MBA–EBB | — | next day |
| 02 Oct | 5X-KOB | UR720 | HRE–EBB | — | 2026-10-02 23:06Z |
| 02 Oct | 5X-KOB | UR713 | JNB–EBB | — | next day |
| 02 Oct | 5X-KOB | UR334 | EBB–ZNZ | — | next day |
| 02 Oct | 5X-KOB | UR334 | ZNZ–JRO | — | next day |
| 02 Oct | 5X-KOB | UR334 | JRO–EBB | — | next day |
| 02 Oct | 5X-KOB | UR360 | EBB–BJM | — | next day |
| 02 Oct | 5X-KOB | UR361 | BJM–EBB | — | next day |
| 02 Oct | 5X-KOB | UR720 | EBB–LUN | — | 2026-10-03 18:03Z |
| 02 Oct | 5X-KOB | UR720 | LUN–HRE | — | next day |
| 02 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 02 Oct | 5X-NIL | UR111 | LGW–EBB | — | next day |
| 02 Oct | ET-APL | UR903 | LOS–EBB | — | 2026-10-03 00:41Z |
| 02 Oct | ET-APL | UR710 | EBB–JNB | — | 2026-10-03 06:38Z |
| 02 Oct | ET-APL | UR711 | JNB–EBB | — | 2026-10-03 11:47Z |
| 02 Oct | ET-APL | UR902 | EBB–LOS | — | next day |
| 03 Oct | 5X-EQU | UR323 | DAR–EBB | — | 2026-10-03 21:19Z |
| 03 Oct | 5X-EQU | UR520 | EBB–MGQ | — | 2026-10-04 02:03Z |
| 03 Oct | 5X-EQU | UR521 | MGQ–EBB | — | 2026-10-04 05:38Z |
| 03 Oct | 5X-EQU | UR322 | EBB–DAR | — | next day |
| 03 Oct | 5X-KDP | UR722 | EBB–HRE | — | next day |
| 03 Oct | 5X-KDP | UR722 | LUN–EBB | — | next day |
| 03 Oct | 5X-KOB | UR720 | HRE–EBB | — | 2026-10-03 23:33Z |
| 03 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-04 05:13Z |
| 03 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-04 07:25Z |
| 03 Oct | 5X-KOB | UR120 | EBB–JUB | — | 2026-10-04 09:45Z |
| 03 Oct | 5X-KOB | UR121 | JUB–EBB | — | 2026-10-04 11:56Z |
| 03 Oct | 5X-KOB | UR208 | EBB–NBO | — | next day |
| 03 Oct | 5X-NIL | UR430 | EBB–BOM | — | next day |
| 03 Oct | 5X-NIL | UR111 | LGW–EBB | — | 2026-10-04 18:51Z |
| 03 Oct | ET-APL | UR903 | LOS–EBB | — | next day |
| 03 Oct | ET-APL | UR710 | EBB–JNB | — | next day |
| 03 Oct | ET-APL | UR711 | JNB–EBB | — | next day |
| 03 Oct | ET-APL | UR720 | EBB–LUN | — | next day |
| 04 Oct | 5X-EQU | UR342 | EBB–MBA | — | 2026-10-04 22:34Z |
| 04 Oct | 5X-EQU | UR343 | MBA–EBB | — | 2026-10-05 01:28Z |
| 04 Oct | 5X-EQU | UR200 | EBB–NBO | — | 2026-10-05 07:27Z |
| 04 Oct | 5X-EQU | UR201 | NBO–EBB | — | 2026-10-05 10:36Z |
| 04 Oct | 5X-EQU | UR120 | EBB–JUB | — | next day |
| 04 Oct | 5X-EQU | UR121 | JUB–EBB | — | next day |
| 04 Oct | 5X-EQU | UR320 | EBB–DAR | — | 2026-10-05 08:39Z |
| 04 Oct | 5X-EQU | UR321 | DAR–EBB | — | 2026-10-05 11:24Z |
| 04 Oct | 5X-EQU | UR360 | EBB–BJM | — | 2026-10-05 14:08Z |
| 04 Oct | 5X-EQU | UR361 | BJM–EBB | — | 2026-10-05 16:00Z |
| 04 Oct | 5X-KDP | UR720 | EBB–LUN | — | 2026-10-04 22:24Z |
| 04 Oct | 5X-KDP | UR720 | LUN–HRE | — | 2026-10-05 01:43Z |
| 04 Oct | 5X-KDP | UR520 | EBB–MGQ | — | next day |
| 04 Oct | 5X-KDP | UR720 | HRE–EBB | — | 2026-10-05 03:25Z |
| 04 Oct | 5X-KDP | UR521 | MGQ–EBB | — | next day |
| 04 Oct | 5X-KDP | UR334 | EBB–ZNZ | — | next day |
| 04 Oct | 5X-KDP | UR334 | ZNZ–JRO | — | next day |
| 04 Oct | 5X-KDP | UR334 | JRO–EBB | — | next day |
| 04 Oct | 5X-KDP | UR206 | EBB–NBO | — | 2026-10-05 18:11Z |
| 04 Oct | 5X-KDP | UR207 | NBO–EBB | — | next day |
| 04 Oct | 5X-NIL | UR431 | BOM–EBB | — | next day |
| 04 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 04 Oct | 5X-NIL | UR111 | LGW–EBB | — | next day |
| 04 Oct | ET-APL | UR713 | JNB–EBB | — | 2026-10-05 01:15Z |
| 04 Oct | ET-APL | UR900 | EBB–LOS | — | 2026-10-05 13:04Z |
| 04 Oct | ET-APL | UR901 | LOS–EBB | — | 2026-10-05 19:12Z |
| 04 Oct | ET-APL | UR712 | EBB–JNB | — | next day |
| 05 Oct | 5X-EQU | UR343 | MBA–EBB | — | next day |
| 05 Oct | 5X-EQU | UR122 | EBB–JUB | — | next day |
| 05 Oct | 5X-EQU | UR123 | JUB–EBB | — | next day |
| 05 Oct | 5X-EQU | UR320 | EBB–DAR | — | 2026-10-06 08:57Z |
| 05 Oct | 5X-EQU | UR321 | DAR–EBB | — | 2026-10-06 11:45Z |
| 05 Oct | 5X-EQU | UR360 | EBB–BJM | — | 2026-10-06 15:47Z |
| 05 Oct | 5X-EQU | UR361 | BJM–EBB | — | 2026-10-06 17:53Z |
| 05 Oct | 5X-EQU | UR206 | EBB–NBO | — | 2026-10-06 14:30Z |
| 05 Oct | 5X-EQU | UR207 | NBO–EBB | — | 2026-10-06 16:44Z |
| 05 Oct | 5X-KDP | UR720 | HRE–EBB | — | 2026-10-05 23:48Z |
| 05 Oct | 5X-KDP | UR710 | EBB–JNB | — | next day |
| 05 Oct | 5X-KDP | UR711 | JNB–EBB | — | next day |
| 05 Oct | 5X-KDP | UR720 | EBB–LUN | — | next day |
| 05 Oct | 5X-KDP | UR720 | LUN–HRE | — | next day |
| 05 Oct | 5X-NIL | UR111 | LGW–EBB | — | 2026-10-06 19:27Z |
| 05 Oct | ET-APL | UR200 | EBB–NBO | — | 2026-10-06 04:59Z |
| 05 Oct | ET-APL | UR201 | NBO–EBB | — | 2026-10-06 07:06Z |
| 05 Oct | ET-APL | UR900 | EBB–LOS | — | next day |
| 05 Oct | ET-APL | UR901 | LOS–EBB | — | next day |
| 06 Oct | 5X-EQU | UR520 | EBB–MGQ | — | next day |
| 06 Oct | 5X-EQU | UR521 | MGQ–EBB | — | next day |
| 06 Oct | 5X-EQU | UR320 | EBB–DAR | — | next day |
| 06 Oct | 5X-EQU | UR321 | DAR–EBB | — | next day |
| 06 Oct | 5X-EQU | UR206 | EBB–NBO | — | next day |
| 06 Oct | 5X-EQU | UR207 | NBO–EBB | — | next day |
| 06 Oct | 5X-KDP | UR720 | HRE–EBB | — | next day |
| 06 Oct | 5X-KDP | UR200 | EBB–NBO | — | 2026-10-07 04:52Z |
| 06 Oct | 5X-KDP | UR201 | NBO–EBB | — | 2026-10-07 07:14Z |
| 06 Oct | 5X-KDP | UR120 | EBB–JUB | — | next day |
| 06 Oct | 5X-KDP | UR121 | JUB–EBB | — | next day |
| 06 Oct | 5X-KDP | UR360 | EBB–BJM | — | 2026-10-07 13:23Z |
| 06 Oct | 5X-KDP | UR361 | BJM–EBB | — | 2026-10-07 15:13Z |
| 06 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 06 Oct | ET-APL | UR712 | EBB–JNB | — | next day |
| 06 Oct | ET-APL | UR713 | JNB–EBB | — | 2026-10-07 02:11Z |
| 06 Oct | ET-APL | UR722 | EBB–HRE | — | 2026-10-07 09:31Z |
| 06 Oct | ET-APL | UR722 | HRE–LUN | — | 2026-10-07 13:26Z |
| 06 Oct | ET-APL | UR722 | LUN–EBB | — | 2026-10-07 15:16Z |
| 07 Oct | 5X-EQU | UR200 | EBB–NBO | — | 2026-10-08 05:02Z |
| 07 Oct | 5X-EQU | UR201 | NBO–EBB | — | 2026-10-08 07:09Z |
| 07 Oct | 5X-EQU | UR334 | EBB–ZNZ | — | next day |
| 07 Oct | 5X-EQU | UR334 | ZNZ–JRO | — | next day |
| 07 Oct | 5X-EQU | UR334 | JRO–EBB | — | next day |
| 07 Oct | 5X-EQU | UR342 | EBB–MBA | — | next day |
| 07 Oct | 5X-EQU | UR343 | MBA–EBB | — | next day |
| 07 Oct | 5X-KDP | UR722 | EBB–HRE | — | 2026-10-08 10:58Z |
| 07 Oct | 5X-KDP | UR722 | HRE–LUN | — | 2026-10-08 14:49Z |
| 07 Oct | 5X-KDP | UR722 | LUN–EBB | — | 2026-10-08 16:32Z |
| 07 Oct | 5X-KDP | UR322 | EBB–DAR | — | 2026-10-08 19:52Z |
| 07 Oct | 5X-KOB | UR122 | EBB–JUB | — | next day |
| 07 Oct | 5X-KOB | UR123 | JUB–EBB | — | next day |
| 07 Oct | 5X-KOB | UR360 | EBB–BJM | — | 2026-10-08 13:21Z |
| 07 Oct | 5X-KOB | UR361 | BJM–EBB | — | 2026-10-08 15:06Z |
| 07 Oct | 5X-KOB | UR208 | EBB–NBO | — | 2026-10-08 19:39Z |
| 07 Oct | 5X-NIL | UR430 | EBB–BOM | — | next day |
| 07 Oct | ET-APL | UR713 | JNB–EBB | — | next day |
| 07 Oct | ET-APL | UR710 | EBB–JNB | — | next day |
| 07 Oct | ET-APL | UR711 | JNB–EBB | — | next day |
| 08 Oct | 5X-EQU | UR323 | DAR–EBB | — | 2026-10-08 22:55Z |
| 08 Oct | 5X-EQU | UR360 | EBB–BJM | — | 2026-10-09 13:31Z |
| 08 Oct | 5X-EQU | UR361 | BJM–EBB | — | 2026-10-09 15:23Z |
| 08 Oct | 5X-EQU | UR208 | EBB–NBO | — | next day |
| 08 Oct | 5X-KDP | UR209 | NBO–EBB | — | 2026-10-08 21:49Z |
| 08 Oct | 5X-KDP | UR120 | EBB–JUB | — | 2026-10-09 11:04Z |
| 08 Oct | 5X-KDP | UR121 | JUB–EBB | — | 2026-10-09 13:38Z |
| 08 Oct | 5X-KDP | UR712 | EBB–JNB | — | next day |
| 08 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-09 04:45Z |
| 08 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-09 06:58Z |
| 08 Oct | 5X-KOB | UR322 | EBB–DAR | — | 2026-10-09 19:24Z |
| 08 Oct | 5X-KOB | UR343 | MBA–EBB | — | 2026-10-09 19:22Z |
| 08 Oct | 5X-NIL | UR431 | BOM–EBB | — | next day |
| 08 Oct | ET-APL | UR722 | EBB–HRE | — | next day |
| 08 Oct | ET-APL | UR722 | HRE–LUN | — | next day |
| 08 Oct | ET-APL | UR722 | LUN–EBB | — | next day |
| 08 Oct | ET-APL | UR902 | EBB–LOS | — | 2026-10-08 21:05Z |
| 09 Oct | 5X-EQU | UR209 | NBO–EBB | — | next day |
| 09 Oct | 5X-EQU | UR520 | EBB–MGQ | — | 2026-10-10 02:07Z |
| 09 Oct | 5X-EQU | UR521 | MGQ–EBB | — | 2026-10-10 05:35Z |
| 09 Oct | 5X-EQU | UR120 | EBB–JUB | — | 2026-10-10 11:18Z |
| 09 Oct | 5X-EQU | UR121 | JUB–EBB | — | 2026-10-10 13:38Z |
| 09 Oct | 5X-EQU | UR342 | EBB–MBA | — | next day |
| 09 Oct | 5X-EQU | UR343 | MBA–EBB | — | next day |
| 09 Oct | 5X-KDP | UR713 | JNB–EBB | — | next day |
| 09 Oct | 5X-KDP | UR334 | EBB–ZNZ | — | next day |
| 09 Oct | 5X-KDP | UR334 | JRO–EBB | — | next day |
| 09 Oct | 5X-KDP | UR360 | EBB–BJM | — | next day |
| 09 Oct | 5X-KDP | UR361 | BJM–EBB | — | next day |
| 09 Oct | 5X-KDP | UR720 | EBB–LUN | — | 2026-10-10 17:56Z |
| 09 Oct | 5X-KOB | UR323 | DAR–EBB | — | 2026-10-09 22:03Z |
| 09 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-10 04:49Z |
| 09 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-10 06:52Z |
| 09 Oct | 5X-KOB | UR206 | EBB–NBO | — | next day |
| 09 Oct | 5X-KOB | UR207 | NBO–EBB | — | next day |
| 09 Oct | 5X-KOB | UR322 | EBB–DAR | — | 2026-10-10 18:54Z |
| 09 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 09 Oct | 5X-NIL | UR111 | LGW–EBB | — | next day |
| 09 Oct | ET-APL | UR903 | LOS–EBB | — | 2026-10-10 01:06Z |
| 09 Oct | ET-APL | UR710 | EBB–JNB | — | 2026-10-10 06:54Z |
| 09 Oct | ET-APL | UR711 | JNB–EBB | — | 2026-10-10 12:27Z |
| 09 Oct | ET-APL | UR902 | EBB–LOS | — | next day |
| 10 Oct | 5X-EQU | UR520 | EBB–MGQ | — | 2026-10-11 01:59Z |
| 10 Oct | 5X-EQU | UR521 | MGQ–EBB | — | 2026-10-11 05:12Z |
| 10 Oct | 5X-EQU | UR120 | EBB–JUB | — | 2026-10-11 10:58Z |
| 10 Oct | 5X-EQU | UR121 | JUB–EBB | — | 2026-10-11 12:58Z |
| 10 Oct | 5X-EQU | UR322 | EBB–DAR | — | next day |
| 10 Oct | 5X-KDP | UR720 | HRE–EBB | — | 2026-10-10 23:22Z |
| 10 Oct | 5X-KDP | UR722 | EBB–HRE | — | next day |
| 10 Oct | 5X-KDP | UR722 | LUN–EBB | — | next day |
| 10 Oct | 5X-KOB | UR323 | DAR–EBB | — | next day |
| 10 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-11 05:01Z |
| 10 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-11 07:43Z |
| 10 Oct | 5X-KOB | UR208 | EBB–NBO | — | 2026-10-11 19:09Z |
| 10 Oct | 5X-NIL | UR430 | EBB–BOM | — | next day |
| 10 Oct | ET-APL | UR903 | LOS–EBB | — | next day |
| 10 Oct | ET-APL | UR710 | EBB–JNB | — | next day |
| 10 Oct | ET-APL | UR711 | JNB–EBB | — | next day |
| 10 Oct | ET-APL | UR720 | EBB–LUN | — | 2026-10-11 18:22Z |
| 11 Oct | 5X-EQU | UR200 | EBB–NBO | — | 2026-10-12 04:56Z |
| 11 Oct | 5X-EQU | UR201 | NBO–EBB | — | 2026-10-12 07:00Z |
| 11 Oct | 5X-EQU | UR120 | EBB–JUB | — | next day |
| 11 Oct | 5X-EQU | UR121 | JUB–EBB | — | next day |
| 11 Oct | 5X-EQU | UR342 | EBB–MBA | — | next day |
| 11 Oct | 5X-KDP | UR520 | EBB–MGQ | — | next day |
| 11 Oct | 5X-KDP | UR521 | MGQ–EBB | — | next day |
| 11 Oct | 5X-KDP | UR320 | EBB–DAR | — | 2026-10-12 08:37Z |
| 11 Oct | 5X-KDP | UR321 | DAR–EBB | — | 2026-10-12 11:10Z |
| 11 Oct | 5X-KDP | UR206 | EBB–NBO | — | 2026-10-12 14:47Z |
| 11 Oct | 5X-KDP | UR207 | NBO–EBB | — | 2026-10-12 17:03Z |
| 11 Oct | 5X-KDP | UR208 | EBB–NBO | — | 2026-10-12 19:00Z |
| 11 Oct | 5X-KOB | UR209 | NBO–EBB | — | 2026-10-11 21:30Z |
| 11 Oct | 5X-KOB | UR334 | EBB–ZNZ | — | next day |
| 11 Oct | 5X-KOB | UR334 | JRO–EBB | — | next day |
| 11 Oct | 5X-KOB | UR360 | EBB–BJM | — | 2026-10-12 13:21Z |
| 11 Oct | 5X-KOB | UR361 | BJM–EBB | — | 2026-10-12 15:30Z |
| 11 Oct | 5X-KOB | UR720 | EBB–LUN | — | 2026-10-12 18:13Z |
| 11 Oct | 5X-KOB | UR720 | LUN–HRE | — | 2026-10-12 21:38Z |
| 11 Oct | 5X-NIL | UR431 | BOM–EBB | — | next day |
| 11 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 11 Oct | ET-APL | UR900 | EBB–LOS | — | 2026-10-12 07:12Z |
| 11 Oct | ET-APL | UR901 | LOS–EBB | — | 2026-10-12 12:47Z |
| 11 Oct | ET-APL | UR712 | EBB–JNB | — | 2026-10-12 19:35Z |
| 11 Oct | ET-APL | UR720 | HRE–EBB | — | 2026-10-11 23:32Z |
| 12 Oct | 5X-EQU | UR710 | EBB–JNB | — | next day |
| 12 Oct | 5X-EQU | UR711 | JNB–EBB | — | next day |
| 12 Oct | 5X-EQU | UR720 | EBB–LUN | — | next day |
| 12 Oct | 5X-EQU | UR720 | LUN–HRE | — | next day |
| 12 Oct | 5X-KDP | UR122 | EBB–JUB | — | next day |
| 12 Oct | 5X-KDP | UR123 | JUB–EBB | — | next day |
| 12 Oct | 5X-KDP | UR320 | EBB–DAR | — | 2026-10-13 08:46Z |
| 12 Oct | 5X-KDP | UR321 | DAR–EBB | — | 2026-10-13 11:31Z |
| 12 Oct | 5X-KDP | UR206 | EBB–NBO | — | 2026-10-13 17:57Z |
| 12 Oct | 5X-KDP | UR207 | NBO–EBB | — | 2026-10-13 20:01Z |
| 12 Oct | 5X-KDP | UR208 | EBB–NBO | — | next day |
| 12 Oct | 5X-KOB | UR720 | HRE–EBB | — | 2026-10-12 23:36Z |
| 12 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-13 05:21Z |
| 12 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-13 07:33Z |
| 12 Oct | 5X-KOB | UR360 | EBB–BJM | — | 2026-10-13 13:41Z |
| 12 Oct | 5X-KOB | UR361 | BJM–EBB | — | 2026-10-13 16:48Z |
| 12 Oct | 5X-KOB | UR322 | EBB–DAR | — | next day |
| 12 Oct | 5X-KOB | UR323 | DAR–EBB | — | next day |
| 12 Oct | 5X-NIL | UR111 | LGW–EBB | — | 2026-10-13 19:17Z |
| 12 Oct | ET-APL | UR713 | JNB–EBB | — | 2026-10-13 01:17Z |
| 12 Oct | ET-APL | UR900 | EBB–LOS | — | next day |
| 12 Oct | ET-APL | UR901 | LOS–EBB | — | next day |
| 12 Oct | ET-APL | UR712 | EBB–JNB | — | 2026-10-13 20:34Z |
| 13 Oct | 5X-EQU | UR720 | HRE–EBB | — | next day |
| 13 Oct | 5X-EQU | UR320 | EBB–DAR | — | next day |
| 13 Oct | 5X-EQU | UR321 | DAR–EBB | — | next day |
| 13 Oct | 5X-EQU | UR206 | EBB–NBO | — | next day |
| 13 Oct | 5X-EQU | UR207 | NBO–EBB | — | next day |
| 13 Oct | 5X-KDP | UR209 | NBO–EBB | — | next day |
| 13 Oct | 5X-KDP | UR520 | EBB–MGQ | — | next day |
| 13 Oct | 5X-KDP | UR521 | MGQ–EBB | — | next day |
| 13 Oct | 5X-KDP | UR120 | EBB–JUB | — | next day |
| 13 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-14 06:13Z |
| 13 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-14 08:15Z |
| 13 Oct | 5X-KOB | UR360 | EBB–BJM | — | 2026-10-14 13:29Z |
| 13 Oct | 5X-KOB | UR361 | BJM–EBB | — | 2026-10-14 15:12Z |
| 13 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 13 Oct | ET-APL | UR713 | JNB–EBB | — | 2026-10-14 02:15Z |
| 13 Oct | ET-APL | UR722 | EBB–HRE | — | 2026-10-14 09:07Z |
| 13 Oct | ET-APL | UR722 | HRE–LUN | — | 2026-10-14 12:56Z |
| 13 Oct | ET-APL | UR722 | LUN–EBB | — | 2026-10-14 14:45Z |
| 13 Oct | ET-APL | UR712 | EBB–JNB | — | next day |
| 14 Oct | 5X-EQU | UR200 | EBB–NBO | — | 2026-10-15 06:53Z |
| 14 Oct | 5X-EQU | UR201 | NBO–EBB | — | 2026-10-15 08:49Z |
| 14 Oct | 5X-EQU | UR334 | EBB–ZNZ | — | next day |
| 14 Oct | 5X-EQU | UR334 | ZNZ–JRO | — | next day |
| 14 Oct | 5X-EQU | UR334 | JRO–EBB | — | next day |
| 14 Oct | 5X-EQU | UR342 | EBB–MBA | — | next day |
| 14 Oct | 5X-EQU | UR343 | MBA–EBB | — | next day |
| 14 Oct | 5X-KDP | UR722 | EBB–HRE | — | 2026-10-15 10:32Z |
| 14 Oct | 5X-KDP | UR722 | HRE–LUN | — | next day |
| 14 Oct | 5X-KDP | UR722 | LUN–EBB | — | 2026-10-15 16:16Z |
| 14 Oct | 5X-KDP | UR322 | EBB–DAR | — | 2026-10-15 18:52Z |
| 14 Oct | 5X-KOB | UR122 | EBB–JUB | — | next day |
| 14 Oct | 5X-KOB | UR123 | JUB–EBB | — | next day |
| 14 Oct | 5X-KOB | UR360 | EBB–BJM | — | 2026-10-15 13:05Z |
| 14 Oct | 5X-KOB | UR361 | BJM–EBB | — | 2026-10-15 15:19Z |
| 14 Oct | 5X-KOB | UR208 | EBB–NBO | — | 2026-10-15 19:21Z |
| 14 Oct | 5X-NIL | UR430 | EBB–BOM | — | next day |
| 14 Oct | ET-APL | UR713 | JNB–EBB | — | next day |
| 14 Oct | ET-APL | UR710 | EBB–JNB | — | next day |
| 14 Oct | ET-APL | UR711 | JNB–EBB | — | next day |
| 15 Oct | 5X-EQU | UR360 | EBB–BJM | — | 2026-10-16 13:23Z |
| 15 Oct | 5X-EQU | UR361 | BJM–EBB | — | 2026-10-16 15:19Z |
| 15 Oct | 5X-EQU | UR208 | EBB–NBO | — | next day |
| 15 Oct | 5X-KDP | UR209 | NBO–EBB | — | 2026-10-15 21:23Z |
| 15 Oct | 5X-KDP | UR712 | EBB–JNB | — | next day |
| 15 Oct | 5X-KOB | UR323 | DAR–EBB | — | 2026-10-15 21:37Z |
| 15 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-16 07:27Z |
| 15 Oct | 5X-KOB | UR201 | NBO–EBB | — | 2026-10-16 09:37Z |
| 15 Oct | 5X-KOB | UR120 | EBB–JUB | — | 2026-10-16 10:50Z |
| 15 Oct | 5X-KOB | UR121 | JUB–EBB | — | 2026-10-16 13:09Z |
| 15 Oct | 5X-KOB | UR322 | EBB–DAR | — | 2026-10-16 19:06Z |
| 15 Oct | 5X-KOB | UR343 | MBA–EBB | — | 2026-10-16 18:29Z |
| 15 Oct | 5X-NIL | UR431 | BOM–EBB | — | next day |
| 15 Oct | ET-APL | UR722 | EBB–HRE | — | next day |
| 15 Oct | ET-APL | UR722 | LUN–EBB | — | next day |
| 15 Oct | ET-APL | UR902 | EBB–LOS | — | 2026-10-16 19:51Z |
| 16 Oct | 5X-EQU | UR209 | NBO–EBB | — | next day |
| 16 Oct | 5X-EQU | UR334 | EBB–ZNZ | — | next day |
| 16 Oct | 5X-EQU | UR334 | ZNZ–JRO | — | next day |
| 16 Oct | 5X-EQU | UR334 | JRO–EBB | — | next day |
| 16 Oct | 5X-EQU | UR206 | EBB–NBO | — | next day |
| 16 Oct | 5X-EQU | UR207 | NBO–EBB | — | next day |
| 16 Oct | 5X-EQU | UR322 | EBB–DAR | — | 2026-10-17 19:02Z |
| 16 Oct | 5X-KDP | UR713 | JNB–EBB | — | next day |
| 16 Oct | 5X-KDP | UR200 | EBB–NBO | — | 2026-10-17 06:13Z |
| 16 Oct | 5X-KDP | UR201 | NBO–EBB | — | 2026-10-17 08:15Z |
| 16 Oct | 5X-KDP | UR360 | EBB–BJM | — | next day |
| 16 Oct | 5X-KDP | UR361 | BJM–EBB | — | next day |
| 16 Oct | 5X-KDP | UR720 | EBB–LUN | — | 2026-10-17 18:47Z |
| 16 Oct | 5X-KOB | UR323 | DAR–EBB | — | 2026-10-16 21:43Z |
| 16 Oct | 5X-KOB | UR520 | EBB–MGQ | — | next day |
| 16 Oct | 5X-KOB | UR521 | MGQ–EBB | — | next day |
| 16 Oct | 5X-KOB | UR120 | EBB–JUB | — | 2026-10-17 10:49Z |
| 16 Oct | 5X-KOB | UR121 | JUB–EBB | — | 2026-10-17 12:53Z |
| 16 Oct | 5X-KOB | UR342 | EBB–MBA | — | next day |
| 16 Oct | 5X-KOB | UR343 | MBA–EBB | — | next day |
| 16 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 16 Oct | 5X-NIL | UR111 | LGW–EBB | — | next day |
| 16 Oct | ET-APL | UR710 | EBB–JNB | — | 2026-10-17 07:59Z |
| 16 Oct | ET-APL | UR711 | JNB–EBB | — | 2026-10-17 13:36Z |
| 16 Oct | ET-APL | UR902 | EBB–LOS | — | next day |
| 17 Oct | 5X-EQU | UR323 | DAR–EBB | — | 2026-10-17 21:39Z |
| 17 Oct | 5X-EQU | UR208 | EBB–NBO | — | next day |
| 17 Oct | 5X-KDP | UR720 | HRE–EBB | — | next day |
| 17 Oct | 5X-KDP | UR722 | EBB–HRE | — | next day |
| 17 Oct | 5X-KDP | UR722 | LUN–EBB | — | next day |
| 17 Oct | 5X-KOB | UR200 | EBB–NBO | — | 2026-10-18 06:11Z |
| 17 Oct | 5X-KOB | UR201 | NBO–EBB | — | next day |
| 17 Oct | 5X-KOB | UR120 | EBB–JUB | — | next day |
| 17 Oct | 5X-KOB | UR121 | JUB–EBB | — | next day |
| 17 Oct | 5X-KOB | UR322 | EBB–DAR | — | next day |
| 17 Oct | 5X-NIL | UR431 | BOM–EBB | — | 2026-10-17 19:55Z |
| 17 Oct | 5X-NIL | UR430 | EBB–BOM | — | next day |
| 17 Oct | ET-APL | UR903 | LOS–EBB | — | next day |
| 17 Oct | ET-APL | UR710 | EBB–JNB | — | next day |
| 17 Oct | ET-APL | UR711 | JNB–EBB | — | next day |
| 17 Oct | ET-APL | UR720 | EBB–LUN | — | next day |
| 18 Oct | 5X-EQU | UR209 | NBO–EBB | — | next day |
| 18 Oct | 5X-EQU | UR520 | EBB–MGQ | — | next day |
| 18 Oct | 5X-EQU | UR320 | EBB–DAR | — | next day |
| 18 Oct | 5X-KDP | UR200 | EBB–NBO | — | next day |
| 18 Oct | 5X-KOB | UR323 | DAR–EBB | — | next day |
| 18 Oct | 5X-KOB | UR334 | EBB–ZNZ | — | next day |
| 18 Oct | 5X-NIL | UR431 | BOM–EBB | — | next day |
| 18 Oct | 5X-NIL | UR110 | EBB–LGW | — | next day |
| 18 Oct | ET-APL | UR900 | EBB–LOS | — | next day |

For 7 of these the timing settles it: the track left in the last hours of the app's UTC day, so the app was dating the leg by its UTC day and the log by the airport's local day — those rows are joined by the build (see `tails.csv`, `track_date`). For the rest the app row is mostly green (on time), which argues the leg flew on the app's own date and the export is missing that day's track — the same gap as the table above, with a same-sector track one day later. The two readings cannot be told apart from this data, so those rows are left unjoined rather than guessed.

---

## Same-weekday check (independent of the app)

For days where the app has no coverage, compare the services flown with the other days of the same weekday. An entry here is a **candidate** gap, not a confirmed one — the service may simply not have operated.

- **04 Oct (Sun)** — 24 services vs 2 peer days; not seen: UGD208, UGD323, UGD323D, UGD342, UGD720.
- **05 Oct (Mon)** — 20 services vs 1 peer days; not seen: UGD207, UGD208, UGD209, UGD322, UGD323, UGD712.
- **06 Oct (Tue)** — 20 services vs 1 peer days; not seen: UGD121, UGD121D, UGD209.
- **08 Oct (Thu)** — 15 services vs 2 peer days; not seen: UGD902.
- **09 Oct (Fri)** — 25 services vs 2 peer days; not seen: UGD334, UGD720.
- **11 Oct (Sun)** — 26 services vs 2 peer days; not seen: UGD111, UGD323, UGD334.
- **12 Oct (Mon)** — 23 services vs 1 peer days; not seen: UGD207D, UGD342, UGD343.
- **13 Oct (Tue)** — 22 services vs 1 peer days; not seen: UGD121.
- **15 Oct (Thu)** — 15 services vs 2 peer days; not seen: UGD722.
- **16 Oct (Fri)** — 26 services vs 2 peer days; not seen: UGD720.
- **17 Oct (Sat)** — 15 services vs 2 peer days; not seen: UGD520, UGD521.
- **18 Oct (Sun)** — 9 services vs 2 peer days; not seen: UGD111, UGD120, UGD121, UGD201, UGD206, UGD207, UGD208, UGD321, UGD323, UGD323D, UGD334, UGD342, UGD360, UGD361, UGD521, UGD712, UGD720, UGD901.

---

## Other data still flagged as missing

| | now | note |
|---|---|---|
| **Aircraft assignment** | 607 of 1100 app rows · 349 of 360 logged flights | the per-tail pages run to 18 Oct; the remainder are rows the export has no track for (above) |
| **Weather** | 175 take-off / 168 landing of 360 | Juba has no METAR station; the rest are legs whose station report is absent at that hour |
| **Runway identification** | 353 departures / 339 arrivals of 360 tracks | the remainder start airborne or end before touchdown |
| **Events not observed** | 7 take-offs · 21 landings | times shown are the last real observation, never a guess |
| **Other operators** | — | October holds 358 Uganda-call-sign tracks |

---

## What the screenshots cover

| tail | app rows | window | 11 Sep | 12 Sep | 22 Sep | 30 Sep |
|---|---|---|---|---|---|---|
| 5X-EQU | 233 | 31 Aug – 18 Oct | 31 | 0 | 0 | 97 |
| 5X-KDP | 258 | 31 Aug – 18 Oct | 54 | 4 | 6 | 96 |
| 5X-KOB | 275 | 31 Aug – 18 Oct | 53 | 6 | 28 | 99 |
| 5X-NIL | 129 | 25 Jul – 18 Oct | 0 | 0 | 0 | 96 |
| ET-APL | 205 | 31 Aug – 18 Oct | 36 | 0 | 1 | 94 |

The pages are per-tail snapshots, each holding roughly the last hundred flights, so a tail's window opens whenever its page ran out of history: **the 11 Sep + 12 Sep + 22 Sep + 30 Sep batches** supply 705 status rows. 485 of those rows come from the newest capture (2026-09-30 20:4x-20:5x), which is why the days nearest the capture are the best covered and the older ones thin out at the far end of each page, not the near one.

---

## Shortest path to complete

1. **Keep the daily export coming** — the archive is only as complete as the last upload, and this one runs to 18 Oct, past the last logged day (18 Oct), so no October day is missing from it.
2. **Re-export the triangle middle sectors** — the HRE–LUN / ZNZ–JRO hops are the bulk of what the app sees and the export does not.
3. **Keep sending the per-tail screenshots** — they are what ties an airframe to each leg; coverage now stands at **349 of 360** logged flights carrying an aircraft.
4. Juba's weather cannot be closed from this source.
