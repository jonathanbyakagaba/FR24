# Uganda Airlines — November 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-11/tracks/`, 345 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01NOV26 – 06NOV26 (part month, 6 days) |
| flights | 97 |
| airborne | 227 h 43 min |
| distance flown | 85,173 km (complete tracks only) |
| track coverage | 69 of 97 flights end to end |
| city pairs | 27 directional / 14 undirected |
| rotations | 28 (5 with an untracked hop) |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL |
| types | A338, B738, CRJ9 |

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

**Bujumbura – Entebbe**  
*eff 01NOV26* 5 weekly CRJ900  
UR361 BJM1942 – 2131EBB CRJ9 12347

**Dar es Salaam – Entebbe**  
*eff 02NOV26* 4 weekly CRJ900  
UR321 DAR1519 – 1646EBB CRJ9 12
UR323 DAR0125 – 0254EBB CRJ9 134

**Entebbe – Bujumbura**  
*eff 01NOV26* 5 weekly CRJ900  
UR360 EBB1841 – 1826BJM CRJ9 12347

**Entebbe – Dar es Salaam**  
*eff 01NOV26* 5 weekly CRJ900  
UR320 EBB1200 – 1350DAR CRJ9 12
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
UR122 EBB0940 – 0931JUB CRJ9 13

**Entebbe – Kilimanjaro**  
*eff 01NOV26* 1 weekly CRJ900  
UR334 EBB1200 – 1350JRO CRJ9 7

**Entebbe – Lagos**  
*eff 01NOV26* 4 weekly 737-800  
UR900 EBB1000 – 1230LOS B738 2457

**Entebbe – London Gatwick**  
*eff 01NOV26* 3 weekly A330-800  
UR110 EBB1053 – 1611LGW A338 257

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
UR206 EBB1721 – 1810NBO CRJ9 27

**Entebbe – Zanzibar**  
*eff 04NOV26* 2 weekly CRJ900  
UR334 EBB1000 – 1150ZNZ CRJ9 35

**Harare – Entebbe**  
*eff 01NOV26* 1 weekly CRJ900  
UR720 HRE1338 – 1720EBB CRJ9 7

**Johannesburg – Entebbe**  
*eff 02NOV26* 3 weekly CRJ900 / 737-800  
UR711 JNB1417 – 1903EBB B738 13
UR713 JNB0307 – 0800EBB CRJ9 135

**Juba – Entebbe**  
*eff 01NOV26* 5 weekly CRJ900  
UR121 JUB1326 – 1511EBB CRJ9 247
UR123 JUB1038 – 1225EBB CRJ9 13

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
UR207 NBO2018 – 2105EBB CRJ9 27

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| EBB-NBO | 8 | 6 | CRJ900 | 521 | 46 |
| NBO-EBB | 8 | 6 | CRJ900 | 521 | 48 |
| EBB-JUB | 6 | 6 | CRJ900 | 545 | 50 |
| EBB-JNB | 6 | 6 | CRJ900 / 737-800 | 2946 | 255 |
| JUB-EBB | 5 | 5 | CRJ900 | 545 | 46 |
| EBB-BJM | 5 | 5 | CRJ900 | 511 | 45 |
| BJM-EBB | 5 | 5 | CRJ900 | 511 | 48 |
| EBB-DAR | 5 | 5 | CRJ900 | 1074 | 110 |
| DAR-EBB | 5 | 4 | CRJ900 | 1074 | 86 |
| JNB-EBB | 5 | 3 | CRJ900 / 737-800 | 2946 | 229 |
| EBB-LOS | 4 | 4 | 737-800 | 3312 | 270 |
| EBB-MGQ | 3 | 3 | CRJ900 | 1447 | 114 |
| MGQ-EBB | 3 | 3 | CRJ900 | 1447 | 117 |
| EBB-LGW | 3 | 3 | A330-800 | 6457 | 580 |
| EBB-MBA | 3 | 3 | CRJ900 | 915 | 74 |
| MBA-EBB | 3 | 3 | CRJ900 | 915 | 74 |
| LOS-EBB | 3 | 3 | 737-800 | 3312 | 270 |
| EBB-HRE | 3 | 3 | CRJ900 / 737-800 | 2004 | 180 |
| LUN-EBB | 3 | 3 | CRJ900 / 737-800 | 1765 | 143 |
| JRO-EBB | 2 | 2 | CRJ900 | 643 | 58 |
| LGW-EBB | 2 | 2 | A330-800 | 6457 | 520 |
| EBB-ZNZ | 2 | 2 | CRJ900 | 1025 | 110 |
| EBB-LUN | 1 | 1 | CRJ900 | 1765 | 140 |
| EBB-JRO | 1 | 1 | CRJ900 | 643 | 110 |
| HRE-EBB | 1 | 1 | CRJ900 | 2004 | 161 |
| EBB-BOM | 1 | 1 | A330-800 | 4890 | 430 |
| BOM-EBB | 1 | 1 | A330-800 | 4890 | 369 |

## Rotations

A rotation is one airframe's day of flying, its legs chained in order: 28 this
month, 23 with every sector of the chain in the record. In the 5 below, the
aircraft puts down at one airport and is next heard from at another, so it
must have flown a sector the movement board does not hold — 5 such hops. They
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
| 5X-EQU-20261103 | 5X-EQU CRJ9 | EBB–MGQ–EBB–HRE–[EBB?]–JNB–[LUN?]–EBB–[JNB]–EBB | 6 | 03NOV26 05:16 – 04NOV 07:38 |
| 5X-KOB-20261104 | 5X-KOB CRJ9 | EBB–NBO–[EBB?]–ZNZ–[NBO?]–EBB–[JRO]–EBB–MBA–EBB | 6 | 04NOV26 08:00 – 22:07 |
| ET-APL-20261104 | ET-APL B738 | EBB–HRE–[LUN]–EBB | 2 | 04NOV26 12:00 – 20:14 |
| 5X-EQU-20261105 | 5X-EQU CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 05NOV26 14:00 – 21:34 |

## Track coverage

28 of the 97 flights have a track that covers only part of
the flight: the export starts after take-off, stops in the cruise, or both.
They are still logged — the flight happened and its days are not in doubt.
The route comes from the flight record; the times come from the board's scheduled times (28 flights).

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
