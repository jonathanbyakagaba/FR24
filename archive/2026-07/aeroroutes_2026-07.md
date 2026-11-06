# Uganda Airlines — July 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-07/tracks/`, 598 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01JUL26 – 31JUL26 |
| flights | 597 |
| airborne | 1,223 h 16 min |
| distance flown | 981,250 km (complete tracks only) |
| track coverage | 594 of 597 flights end to end |
| city pairs | 26 directional / 14 undirected |
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

**Bujumbura – Entebbe**  
*eff 01JUL26* 6 weekly CRJ900  
UR361 BJM1725 – 1914EBB CRJ9 123457

**Dar es Salaam – Entebbe**  
*eff 02JUL26* 1 daily CRJ900 / 737-800  
UR321 DAR1423 – 1555EBB CRJ9 127
UR323 DAR0033 – 0204EBB CRJ9 1234567

**Entebbe – Bujumbura**  
*eff 01JUL26* 6 weekly CRJ900  
UR360 EBB1642 – 1627BJM CRJ9 123457

**Entebbe – Dar es Salaam**  
*eff 01JUL26* 1 daily CRJ900 / 737-800  
UR320 EBB1159 – 1317DAR CRJ9 127
UR322 EBB2211 – 2330DAR CRJ9 13456

**Entebbe – Harare**  
*eff 08JUL26* 4 weekly CRJ900 / 737-800  
UR722 EBB1253 – 1429HRE CRJ9 2346

**Entebbe – Johannesburg**  
*eff 01JUL26* 1 daily 737-800 / CRJ900  
UR710 EBB0923 – 1211JNB B738 1356
UR712 EBB2253 – 0140(+1)JNB B738 12457

**Entebbe – Juba**  
*eff 01JUL26* 1 daily CRJ900  
UR120 EBB1402 – 1353JUB CRJ9 24567
UR122 EBB0929 – 0915JUB CRJ9 13

**Entebbe – Lagos**  
*eff 03JUL26* 4 weekly 737-800  
UR900 EBB0956 – 1203LOS B738 17
UR902 EBB2141 – 2348LOS B738 45

**Entebbe – London Gatwick**  
*eff 03JUL26* 3 weekly B788 / A330-800  
UR110 EBB1052 – 1641LGW B788 257

**Entebbe – Lusaka**  
*eff 01JUL26* 6 weekly CRJ900 / 737-800  
UR720 EBB2121 – 2241LUN CRJ9 1567
UR722 EBB1103 – 1228LUN CRJ9 23

**Entebbe – Mogadishu**  
*eff 03JUL26* 4 weekly CRJ900  
UR520 EBB0518 – 0714MGQ CRJ9 2567

**Entebbe – Mombasa**  
*eff 01JUL26* 3 weekly CRJ900  
UR342 EBB1957 – 2108MBA CRJ9 357

**Entebbe – Mumbai**  
*eff 02JUL26* 3 weekly 737-800 / A330-800  
UR430 EBB0856 – 1816BOM B738 346

**Entebbe – Nairobi**  
*eff 01JUL26* 1 daily CRJ900 / 737-800  
UR200 EBB0759 – 0843NBO CRJ9 1234567
UR206 EBB1748 – 1837NBO CRJ9 1257
UR208 EBB2209 – 2254NBO CRJ9 13467

**Entebbe – Zanzibar**  
*eff 01JUL26* 3 weekly CRJ900  
UR334 EBB1311 – 1429ZNZ CRJ9 357

**Harare – Entebbe**  
*eff 01JUL26* 5 weekly CRJ900 / 737-800  
UR720 HRE0134 – 0515EBB CRJ9 12367

**Johannesburg – Entebbe**  
*eff 01JUL26* 5 weekly 737-800 / CRJ900  
UR711 JNB1417 – 1859EBB B738 1356
UR713 JNB0355 – 0840EBB B738 1235

**Juba – Entebbe**  
*eff 01JUL26* 1 daily CRJ900  
UR121 JUB1512 – 1659EBB CRJ9 24567
UR123 JUB1016 – 1204EBB CRJ9 13

**Kilimanjaro – Entebbe**  
*eff 01JUL26* 3 weekly CRJ900  
UR334 JRO1708 – 1807EBB CRJ9 357

**Lagos – Entebbe**  
*eff 04JUL26* 4 weekly 737-800  
UR901 LOS1322 – 1930EBB B738 17
UR903 LOS0116 – 0725EBB B738 56

**London Gatwick – Entebbe**  
*eff 03JUL26* 3 weekly B788 / A330-800  
UR111 LGW2003 – 0600(+1)EBB B788 257

**Lusaka – Entebbe**  
*eff 08JUL26* 4 weekly CRJ900 / 737-800  
UR722 LUN1743 – 2105EBB CRJ9 2346

**Mogadishu – Entebbe**  
*eff 03JUL26* 4 weekly CRJ900  
UR521 MGQ0852 – 1051EBB CRJ9 2567

**Mombasa – Entebbe**  
*eff 01JUL26* 3 weekly CRJ900  
UR343 MBA2224 – 2342EBB CRJ9 357

**Mumbai – Entebbe**  
*eff 05JUL26* 2 weekly 737-800 / A330-800  
UR431 BOM0118 – 0431EBB B738 47

**Nairobi – Entebbe**  
*eff 01JUL26* 1 daily CRJ900 / 737-800  
UR200 NBO0957 – 1043EBB CRJ9 56
UR201 NBO1010 – 1056EBB CRJ9 1234567
UR207 NBO1956 – 2044EBB CRJ9 1257
UR209 NBO0014 – 0102EBB CRJ9 124567

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| EBB-NBO | 68 | 7 | CRJ900 / 737-800 | 521 | 45 |
| NBO-EBB | 68 | 7 | CRJ900 / 737-800 | 521 | 47 |
| EBB-DAR | 34 | 7 | CRJ900 / 737-800 | 1074 | 84 |
| EBB-JNB | 33 | 7 | 737-800 / CRJ900 | 2946 | 232 |
| JNB-EBB | 33 | 5 | 737-800 / CRJ900 | 2946 | 227 |
| DAR-EBB | 33 | 7 | CRJ900 / 737-800 | 1074 | 87 |
| EBB-JUB | 31 | 7 | CRJ900 | 545 | 50 |
| JUB-EBB | 31 | 7 | CRJ900 | 545 | 46 |
| EBB-BJM | 27 | 6 | CRJ900 | 511 | 45 |
| BJM-EBB | 27 | 6 | CRJ900 | 511 | 49 |
| EBB-LUN | 17 | 6 | CRJ900 / 737-800 | 1765 | 140 |
| EBB-MGQ | 17 | 4 | CRJ900 | 1447 | 115 |
| MGQ-EBB | 17 | 4 | CRJ900 | 1447 | 117 |
| HRE-EBB | 14 | 5 | CRJ900 / 737-800 | 2004 | 160 |
| EBB-ZNZ | 14 | 3 | CRJ900 | 1025 | 80 |
| JRO-EBB | 14 | 3 | CRJ900 | 643 | 57 |
| EBB-MBA | 14 | 3 | CRJ900 | 915 | 74 |
| MBA-EBB | 14 | 3 | CRJ900 | 915 | 76 |
| EBB-LOS | 14 | 4 | 737-800 | 3312 | 242 |
| EBB-LGW | 13 | 3 | B788 / A330-800 | 6457 | 469 |
| LOS-EBB | 13 | 4 | 737-800 | 3312 | 255 |
| LGW-EBB | 12 | 3 | B788 / A330-800 | 6457 | 476 |
| EBB-HRE | 11 | 4 | CRJ900 / 737-800 | 2004 | 156 |
| LUN-EBB | 11 | 4 | CRJ900 / 737-800 | 1765 | 142 |
| EBB-BOM | 9 | 3 | 737-800 / A330-800 | 4890 | 388 |
| BOM-EBB | 8 | 2 | 737-800 / A330-800 | 4890 | 347 |

## Track coverage

3 of the 597 flights have a track that covers only part of
the flight: the export starts after take-off, stops in the cruise, or both.
They are still logged — the flight happened and its days are not in doubt.
The route comes from the flight record; the times come from the movement board's actual times (3 flights).

| flight | date | logged as | times from | what the track covers |
|---|---|---|---|---|
| UR360 | 2026-07-05 | EBB-BJM | board, actual | track incomplete |
| UR360 | 2026-07-24 | EBB-BJM | board, actual | track stops 102 km short |
| UR520 | 2026-07-26 | EBB-MGQ | board, actual | track stops 32 km short |

## Route discrepancies

Sectors the aircraft flew under a through flight number, where the track
shows a landing the flight record does not name. The log follows the track.

| flight | date | logged as | flight record |
|---|---|---|---|
| UR722 | 2026-07-01 | EBB-LUN | EBB-HRE |
| UR722 | 2026-07-07 | EBB-LUN | EBB-HRE |
