# Uganda Airlines — November 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-11/tracks/`, 686 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01NOV26 – 27NOV26 (part month, 10 days) |
| flights | 160 |
| airborne | 355 h 44 min |
| distance flown | 156,038 km (complete tracks only) |
| track coverage | 125 of 160 flights end to end |
| city pairs | 32 directional / 18 undirected |
| rotations | 48 (5 with an untracked hop) |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-AOU, ET-APL |
| types | A338, B738, B788, CRJ9 |

**How to read a line.** Route heading in bold, then the effective date, weekly
frequency and equipment, then one line per flight number:

```
UR713 EBB0900 – 1125JNB A338 135
  |    |         |      |   |   +-- days of week flown (1 = Monday ... 7 = Sunday)
  |    |         |      |   +------ ICAO type designator
  |    |         |      +---------- arrival airport (IATA)
  |    |         +----------------- arrival time, local, HHMM
  |    +--------------------------- departure time, local, HHMM
  +-------------------------------- flight number
```

Times are the actual off/on times recorded in the track data, converted to
local time at each end; `(+1)` marks an arrival on the following day. A flight
is logged under the date it departed, local time.

## Log

**Addis Ababa – Cape Town**  
*eff 27NOV26* 1 weekly B788  
ET845 ADD0730 – 1300CPT B788 5

**Bujumbura – Entebbe**  
*eff 01NOV26* 5 weekly CRJ900  
UR361 BJM1942 – 2131EBB CRJ9 12347

**Dar es Salaam – Entebbe**  
*eff 02NOV26* 4 weekly CRJ900  
UR320 DAR0912 – 1045EBB CRJ9 3
UR321 DAR1519 – 1646EBB CRJ9 12
UR323 DAR0125 – 0254EBB CRJ9 134

**Entebbe – Bujumbura**  
*eff 01NOV26* 5 weekly CRJ900  
UR360 EBB1841 – 1826BJM CRJ9 12347

**Entebbe – Dar es Salaam**  
*eff 01NOV26* 5 weekly CRJ900  
UR320 EBB1200 – 1350DAR CRJ9 123
UR322 EBB2200 – 2350DAR CRJ9 347

**Entebbe – Harare**  
*eff 03NOV26* 3 weekly CRJ900 / 737-800  
UR722 EBB1200 – 1400HRE CRJ9 234

**Entebbe – Johannesburg**  
*eff 01NOV26* 6 weekly CRJ900 / 737-800  
UR710 EBB0830 – 1145JNB CRJ9 135
UR712 EBB1625 – 1940JNB CRJ9 247

**Entebbe – Juba**  
*eff 01NOV26* 6 weekly CRJ900  
UR120 EBB1213 – 1203JUB CRJ9 2457
UR122 EBB0940 – 0931JUB CRJ9 1234

**Entebbe – Kigali**  
*eff 25NOV26* 3 weekly CRJ900  
UR380 EBB1215 – 1145KGL CRJ9 35
UR382 EBB0803 – 0735KGL CRJ9 4

**Entebbe – Kilimanjaro**  
*eff 01NOV26* 1 weekly CRJ900  
UR334 EBB1200 – 1350JRO CRJ9 7

**Entebbe – Lagos**  
*eff 01NOV26* 4 weekly 737-800  
UR900 EBB1000 – 1230LOS B738 2457

**Entebbe – London Gatwick**  
*eff 01NOV26* 3 weekly A330-800  
UR110 EBB1100 – 1740LGW A338 257

**Entebbe – Lusaka**  
*eff 01NOV26* 1 weekly CRJ900  
UR720 EBB0918 – 1038LUN CRJ9 7

**Entebbe – Mogadishu**  
*eff 01NOV26* 3 weekly CRJ900  
UR520 EBB0521 – 0716MGQ CRJ9 247

**Entebbe – Mombasa**  
*eff 01NOV26* 3 weekly CRJ900  
UR342 EBB1921 – 2035MBA CRJ9 357

**Entebbe – Mumbai**  
*eff 04NOV26* 1 weekly A330-800  
UR430 EBB2025 – 0605(+1)BOM A338 3

**Entebbe – Nairobi**  
*eff 01NOV26* 6 weekly CRJ900  
UR200 EBB0750 – 0836NBO CRJ9 123457
UR204 EBB2225 – 2331NBO CRJ9 234
UR206 EBB1721 – 1810NBO CRJ9 27

**Entebbe – Zanzibar**  
*eff 04NOV26* 2 weekly CRJ900  
UR334 EBB1000 – 1150ZNZ CRJ9 35

**Harare – Entebbe**  
*eff 01NOV26* 1 weekly CRJ900  
UR720 HRE1338 – 1720EBB CRJ9 7

**Harare – Lusaka**  
*eff 24NOV26* 1 weekly CRJ900  
UR722 HRE1519 – 1557LUN CRJ9 2

**Johannesburg – Entebbe**  
*eff 02NOV26* 3 weekly CRJ900 / 737-800  
UR711 JNB1417 – 1903EBB B738 13
UR713 JNB0307 – 0800EBB CRJ9 135

**Juba – Entebbe**  
*eff 01NOV26* 5 weekly CRJ900  
UR121 JUB1326 – 1511EBB CRJ9 247
UR123 JUB1038 – 1225EBB CRJ9 1234

**Kigali – Entebbe**  
*eff 25NOV26* 3 weekly CRJ900  
UR381 KGL1246 – 1416EBB CRJ9 35
UR383 KGL0902 – 1034EBB CRJ9 4

**Kilimanjaro – Entebbe**  
*eff 01NOV26* 2 weekly CRJ900  
UR334 JRO1700 – 1759EBB CRJ9 37

**Lagos – Entebbe**  
*eff 01NOV26* 3 weekly 737-800  
UR901 LOS2225 – 0455(+1)EBB B738 247

**London Gatwick – Entebbe**  
*eff 01NOV26* 2 weekly A330-800  
UR111 LGW1810 – 0550(+1)EBB A338 27

**Lusaka – Entebbe**  
*eff 03NOV26* 3 weekly CRJ900 / 737-800  
UR722 LUN1732 – 2055EBB CRJ9 234

**Mogadishu – Entebbe**  
*eff 01NOV26* 3 weekly CRJ900  
UR521 MGQ0842 – 1036EBB CRJ9 247

**Mombasa – Entebbe**  
*eff 01NOV26* 3 weekly CRJ900  
UR343 MBA2157 – 2311EBB CRJ9 357

**Mumbai – Entebbe**  
*eff 05NOV26* 1 weekly A330-800  
UR431 BOM0850 – 1229EBB A338 4

**Nairobi – Entebbe**  
*eff 01NOV26* 6 weekly CRJ900  
UR201 NBO1007 – 1051EBB CRJ9 123457
UR205 NBO0042 – 0128EBB CRJ9 34
UR207 NBO2018 – 2105EBB CRJ9 27

**Zanzibar – Kilimanjaro**  
*eff 25NOV26* 1 weekly CRJ900  
UR334 ZNZ1434 – 1512JRO CRJ9 3

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| EBB-NBO | 14 | 6 | CRJ900 | 521 | 46 |
| NBO-EBB | 14 | 6 | CRJ900 | 521 | 48 |
| EBB-JNB | 11 | 6 | CRJ900 / 737-800 | 2946 | 255 |
| EBB-JUB | 9 | 6 | CRJ900 | 545 | 51 |
| JUB-EBB | 8 | 5 | CRJ900 | 545 | 46 |
| EBB-BJM | 8 | 5 | CRJ900 | 511 | 46 |
| BJM-EBB | 8 | 5 | CRJ900 | 511 | 48 |
| EBB-DAR | 8 | 5 | CRJ900 | 1074 | 86 |
| DAR-EBB | 8 | 4 | CRJ900 | 1074 | 87 |
| JNB-EBB | 8 | 3 | CRJ900 / 737-800 | 2946 | 224 |
| EBB-LOS | 5 | 4 | 737-800 | 3312 | 270 |
| EBB-MBA | 5 | 3 | CRJ900 | 915 | 74 |
| MBA-EBB | 5 | 3 | CRJ900 | 915 | 75 |
| LOS-EBB | 5 | 3 | 737-800 | 3312 | 265 |
| EBB-MGQ | 4 | 3 | CRJ900 | 1447 | 114 |
| MGQ-EBB | 4 | 3 | CRJ900 | 1447 | 116 |
| EBB-LGW | 4 | 3 | A330-800 | 6457 | 580 |
| LUN-EBB | 4 | 3 | CRJ900 / 737-800 | 1765 | 143 |
| JRO-EBB | 3 | 2 | CRJ900 | 643 | 58 |
| LGW-EBB | 3 | 2 | A330-800 | 6457 | 520 |
| EBB-HRE | 3 | 3 | CRJ900 / 737-800 | 2004 | 180 |
| EBB-ZNZ | 3 | 2 | CRJ900 | 1025 | 110 |
| EBB-KGL | 3 | 3 | CRJ900 | 340 | 32 |
| KGL-EBB | 3 | 3 | CRJ900 | 340 | 32 |
| EBB-BOM | 2 | 1 | A330-800 | 4890 | 390 |
| BOM-EBB | 2 | 1 | A330-800 | 4890 | 400 |
| EBB-LUN | 1 | 1 | CRJ900 | 1765 | 140 |
| EBB-JRO | 1 | 1 | CRJ900 | 643 | 110 |
| HRE-EBB | 1 | 1 | CRJ900 | 2004 | 161 |
| HRE-LUN | 1 | 1 | CRJ900 | 403 | 38 |
| ZNZ-JRO | 1 | 1 | CRJ900 | 391 | 38 |
| ADD-CPT | 1 | 1 | B788 | 5230 | 390 |

## Rotations

A rotation is one airframe's day of flying, its legs chained in order: 48 this
month, 43 with every sector of the chain in the record. In the 5 below, the
aircraft puts down at one airport and is next heard from at another, so it
must have flown a sector the movement board does not hold — 4 such hops. They
are kept in place rather than dropped, so a rotation reads from its first
departure to its last arrival instead of breaking into orphan sectors. The
airport that is only reachable through a hop is bracketed in the chain, and
work/fetch_fr24_tracks.py goes and fetches the sector itself where
Flightradar24 credentials allow, after which the brackets come off on the next
rebuild.

```
EBB–HRE  UR720  →  HRE–[LUN]  →  LUN–EBB  UR721      one rotation
```

A hop carrying a question mark is where the record contradicts itself — the
next leg is already under way while this aircraft should still be on the
ground — so the airport is shown and the sector is not claimed.

| rotation | aircraft | chain | legs | first off – last on (EBB) |
|---|---|---|---|---|
| 5X-KDP-20261101 | 5X-KDP CRJ9 | EBB–LUN–[HRE]–EBB–BJM–EBB–DAR–EBB | 6 | 01NOV26 09:18 – 02NOV 02:54 |
| 5X-EQU-20261103 | 5X-EQU CRJ9 | EBB–MGQ–EBB–HRE–[EBB?]–JNB–[LUN?]–EBB–JNB–EBB | 7 | 03NOV26 05:16 – 04NOV 07:38 |
| 5X-KOB-20261104 | 5X-KOB CRJ9 | EBB–NBO–[EBB?]–ZNZ–[NBO?]–EBB–[JRO]–EBB–MBA–EBB | 6 | 04NOV26 08:00 – 22:07 |
| ET-APL-20261104 | ET-APL B738 | EBB–HRE–[LUN]–EBB | 2 | 04NOV26 12:00 – 20:14 |
| 5X-EQU-20261105 | 5X-EQU CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 05NOV26 14:00 – 21:34 |

## Track coverage

35 of the 160 flights have a track that covers only part of
the flight: the export starts after take-off, stops in the cruise, or both.
They are still logged — the flight happened and its days are not in doubt.
The route comes from the flight record; the times come from the board's scheduled times (35 flights).

| flight | date | logged as | times from | what the track covers |
|---|---|---|---|---|
| UR900 | 2026-11-01 | EBB-LOS | board, scheduled | track stops 3182 km short |
| UR334 | 2026-11-01 | EBB-JRO | board, scheduled | track stops 108 km short |
| UR120 | 2026-11-01 | EBB-JUB | board, scheduled | track stops 42 km short |
| UR712 | 2026-11-01 | EBB-JNB | board, scheduled | track stops 1985 km short |
| UR111 | 2026-11-01 | LGW-EBB | board, scheduled | track stops 4853 km short |
| UR322 | 2026-11-01 | EBB-DAR | board, scheduled | track stops 50 km short |
| UR710 | 2026-11-02 | EBB-JNB | board, scheduled | track stops 278 km short |
| UR320 | 2026-11-02 | EBB-DAR | board, scheduled | track stops 589 km short |
| UR900 | 2026-11-03 | EBB-LOS | board, scheduled | track stops 2767 km short |
| UR110 | 2026-11-03 | EBB-LGW | board, scheduled | track stops 4658 km short |
| UR320 | 2026-11-03 | EBB-DAR | board, scheduled | track stops 257 km short |
| UR722 | 2026-11-03 | EBB-HRE | board, scheduled | track stops 1600 km short |
| UR712 | 2026-11-03 | EBB-JNB | board, scheduled | track stops 486 km short |
| UR111 | 2026-11-03 | LGW-EBB | board, scheduled | track stops 4545 km short |
| UR901 | 2026-11-03 | LOS-EBB | board, scheduled | track stops 2154 km short |
| UR710 | 2026-11-04 | EBB-JNB | board, scheduled | track incomplete |
| UR334 | 2026-11-04 | EBB-ZNZ | board, scheduled | track stops 169 km short |
| UR722 | 2026-11-04 | EBB-HRE | board, scheduled | track stops 1114 km short |
| UR430 | 2026-11-04 | EBB-BOM | board, scheduled | track stops 1801 km short |
| UR900 | 2026-11-05 | EBB-LOS | board, scheduled | track stops 2938 km short |
| UR722 | 2026-11-05 | EBB-HRE | board, scheduled | track stops 41 km short |
| UR712 | 2026-11-05 | EBB-JNB | board, scheduled | track incomplete |
| UR901 | 2026-11-05 | LOS-EBB | board, scheduled | track stops 2134 km short |
| UR710 | 2026-11-06 | EBB-JNB | board, scheduled | track stops 26 km short |
| UR900 | 2026-11-06 | EBB-LOS | board, scheduled | track stops 2779 km short |
| UR110 | 2026-11-06 | EBB-LGW | board, scheduled | track stops 5512 km short |
| UR334 | 2026-11-06 | EBB-ZNZ | board, scheduled | track stops 511 km short |
| UR120 | 2026-11-06 | EBB-JUB | board, scheduled | track stops 134 km short |
| UR710 | 2026-11-25 | EBB-JNB | board, scheduled | track stops 222 km short |
| UR334 | 2026-11-25 | EBB-ZNZ | board, scheduled | track stops 79 km short |
| UR431 | 2026-11-26 | BOM-EBB | board, scheduled | track stops 400 km short |
| UR900 | 2026-11-26 | EBB-LOS | board, scheduled | track stops 2931 km short |
| ET845 | 2026-11-27 | ADD-CPT | board, scheduled | track picks the flight up 258 km out; track stops 1004 km short |
| UR710 | 2026-11-27 | EBB-JNB | board, scheduled | track stops 735 km short |
| UR110 | 2026-11-27 | EBB-LGW | board, scheduled | track stops 5764 km short |
