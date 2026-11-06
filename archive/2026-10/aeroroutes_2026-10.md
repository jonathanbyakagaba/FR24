# Uganda Airlines — October 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-10/tracks/`, 618 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01OCT26 – 31OCT26 |
| flights | 616 |
| airborne | 1,324 h 23 min |
| distance flown | 958,990 km (complete tracks only) |
| track coverage | 588 of 616 flights end to end |
| city pairs | 29 directional / 17 undirected |
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
*eff 01OCT26* 6 weekly CRJ900  
UR361 BJM1729 – 1917EBB CRJ9 123457

**Dar es Salaam – Entebbe**  
*eff 01OCT26* 6 weekly CRJ900  
UR321 DAR1946 – 2115EBB CRJ9 127
UR323 DAR0050 – 0217EBB CRJ9 124567

**Dar es Salaam – Nairobi**  
*eff 11OCT26* 1 weekly CRJ900  
UR323 DAR0036 – 0302NBO CRJ9 7

**Entebbe – Bujumbura**  
*eff 01OCT26* 6 weekly CRJ900  
UR360 EBB1626 – 1610BJM CRJ9 123457

**Entebbe – Dar es Salaam**  
*eff 01OCT26* 1 daily CRJ900  
UR320 EBB1658 – 1822DAR CRJ9 127
UR322 EBB2150 – 2309DAR CRJ9 13456

**Entebbe – Harare**  
*eff 01OCT26* 4 weekly CRJ900 / 737-800  
UR722 EBB1336 – 1516HRE CRJ9 2346

**Entebbe – Johannesburg**  
*eff 01OCT26* 1 daily 737-800 / CRJ900  
UR710 EBB0830 – 1145JNB B738 1356
UR712 EBB2245 – 0200(+1)JNB B738 1247

**Entebbe – Juba**  
*eff 01OCT26* 1 daily CRJ900  
UR120 EBB1225 – 1214JUB CRJ9 24567
UR122 EBB0713 – 0659JUB CRJ9 13
UR201 EBB1321 – 1311JUB CRJ9 7

**Entebbe – Lagos**  
*eff 01OCT26* 6 weekly 737-800  
UR900 EBB1008 – 1212LOS B738 12457
UR902 EBB2309 – 0109(+1)LOS B738 456

**Entebbe – London Gatwick**  
*eff 02OCT26* 3 weekly A330-800  
UR110 EBB1113 – 1731LGW A338 257

**Entebbe – Lusaka**  
*eff 02OCT26* 4 weekly CRJ900 / 737-800  
UR720 EBB2106 – 2226LUN CRJ9 1567
UR722 EBB1559 – 1722LUN CRJ9 7

**Entebbe – Mogadishu**  
*eff 02OCT26* 5 weekly CRJ900  
UR520 EBB0522 – 0715MGQ CRJ9 24567

**Entebbe – Mombasa**  
*eff 02OCT26* 4 weekly CRJ900  
UR342 EBB1857 – 2010MBA CRJ9 1357

**Entebbe – Mumbai**  
*eff 03OCT26* 2 weekly A330-800  
UR430 EBB1404 – 2244BOM A338 36

**Entebbe – Nairobi**  
*eff 01OCT26* 1 daily CRJ900 / 737-800  
UR200 EBB0808 – 0855NBO CRJ9 1234567
UR206 EBB1748 – 1835NBO CRJ9 12567
UR208 EBB2211 – 2257NBO CRJ9 1234567

**Entebbe – Zanzibar**  
*eff 02OCT26* 3 weekly CRJ900  
UR334 EBB1214 – 1333ZNZ CRJ9 357

**Harare – Entebbe**  
*eff 03OCT26* 5 weekly CRJ900 / 737-800  
UR711 HRE2111 – 0053(+1)EBB B738 4
UR720 HRE0106 – 0440EBB CRJ9 1267
UR722 HRE2022 – 2359EBB CRJ9 7

**Johannesburg – Entebbe**  
*eff 02OCT26* 5 weekly 737-800 / CRJ900  
UR711 JNB1509 – 2003EBB B738 1356
UR713 JNB0256 – 0735EBB B738 1235

**Johannesburg – Harare**  
*eff 21OCT26* 1 weekly 737-800  
UR711 JNB1558 – 1713HRE B738 3

**Juba – Entebbe**  
*eff 01OCT26* 1 daily CRJ900  
UR121 JUB1509 – 1655EBB CRJ9 24567
UR123 JUB0806 – 0955EBB CRJ9 13

**Juba – Nairobi**  
*eff 13OCT26* 1 weekly CRJ900  
UR121 JUB1517 – 1803NBO CRJ9 2

**Kilimanjaro – Entebbe**  
*eff 02OCT26* 3 weekly CRJ900  
UR334 JRO1344 – 1439EBB CRJ9 357

**Lagos – Entebbe**  
*eff 02OCT26* 5 weekly 737-800  
UR901 LOS1401 – 2017EBB B738 1457
UR903 LOS0227 – 0843EBB B738 56

**London Gatwick – Entebbe**  
*eff 02OCT26* 3 weekly A330-800  
UR111 LGW2008 – 0600(+1)EBB A338 257

**Lusaka – Entebbe**  
*eff 01OCT26* 4 weekly CRJ900 / 737-800  
UR722 LUN1759 – 2118EBB CRJ9 2346

**Mogadishu – Entebbe**  
*eff 02OCT26* 5 weekly CRJ900  
UR521 MGQ0843 – 1042EBB CRJ9 24567

**Mombasa – Entebbe**  
*eff 02OCT26* 4 weekly CRJ900  
UR343 MBA2134 – 2252EBB CRJ9 1357

**Mumbai – Entebbe**  
*eff 01OCT26* 2 weekly A330-800  
UR431 BOM0822 – 1157EBB A338 47

**Nairobi – Entebbe**  
*eff 01OCT26* 1 daily CRJ900 / 737-800  
UR121 NBO2031 – 2118EBB CRJ9 2
UR201 NBO1011 – 1056EBB CRJ9 1234567
UR207 NBO2004 – 2050EBB CRJ9 12567
UR209 NBO0024 – 0111EBB CRJ9 12457
UR323 NBO0519 – 0606EBB CRJ9 7

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| NBO-EBB | 69 | 7 | CRJ900 / 737-800 | 521 | 47 |
| EBB-NBO | 67 | 7 | CRJ900 / 737-800 | 521 | 47 |
| EBB-JNB | 34 | 7 | 737-800 / CRJ900 | 2946 | 235 |
| JNB-EBB | 33 | 5 | 737-800 / CRJ900 | 2946 | 226 |
| DAR-EBB | 32 | 6 | CRJ900 | 1074 | 88 |
| EBB-DAR | 32 | 7 | CRJ900 | 1074 | 84 |
| EBB-JUB | 31 | 7 | CRJ900 | 545 | 50 |
| JUB-EBB | 30 | 7 | CRJ900 | 545 | 46 |
| EBB-BJM | 26 | 6 | CRJ900 | 511 | 45 |
| BJM-EBB | 26 | 6 | CRJ900 | 511 | 49 |
| EBB-HRE | 18 | 4 | CRJ900 / 737-800 | 2004 | 160 |
| EBB-LOS | 18 | 6 | 737-800 | 3312 | 248 |
| LUN-EBB | 17 | 4 | CRJ900 / 737-800 | 1765 | 141 |
| LOS-EBB | 17 | 5 | 737-800 | 3312 | 256 |
| EBB-MGQ | 17 | 5 | CRJ900 | 1447 | 114 |
| MGQ-EBB | 17 | 5 | CRJ900 | 1447 | 117 |
| HRE-EBB | 17 | 5 | CRJ900 / 737-800 | 2004 | 157 |
| EBB-LUN | 16 | 4 | CRJ900 / 737-800 | 1765 | 142 |
| EBB-ZNZ | 13 | 3 | CRJ900 | 1025 | 79 |
| EBB-LGW | 13 | 3 | A330-800 | 6457 | 492 |
| JRO-EBB | 13 | 3 | CRJ900 | 643 | 57 |
| EBB-MBA | 13 | 4 | CRJ900 | 915 | 73 |
| MBA-EBB | 13 | 4 | CRJ900 | 915 | 77 |
| LGW-EBB | 13 | 3 | A330-800 | 6457 | 473 |
| BOM-EBB | 9 | 2 | A330-800 | 4890 | 366 |
| EBB-BOM | 9 | 2 | A330-800 | 4890 | 368 |
| DAR-NBO | 1 | 1 | CRJ900 | 667 | 146 |
| JUB-NBO | 1 | 1 | CRJ900 | 908 | 107 |
| JNB-HRE | 1 | 1 | 737-800 | 959 | 75 |

## Track coverage

28 of the 616 flights have a track that covers only part of
the flight: the export starts after take-off, stops in the cruise, or both.
They are still logged — the flight happened and its days are not in doubt.
The route comes from the flight record; the times come from the movement board's actual times (3 flights) and the board's scheduled times (23 flights) and the partial track itself (2 flights).

| flight | date | logged as | times from | what the track covers |
|---|---|---|---|---|
| UR111 | 2026-10-02 | LGW-EBB | the track | track has a 157 minute hole en route |
| UR711 | 2026-10-05 | JNB-EBB | board, actual | track picks the flight up 2504 km out |
| UR110 | 2026-10-06 | EBB-LGW | the track | track has a 75 minute hole en route |
| UR361 | 2026-10-15 | BJM-EBB | board, actual | track picks the flight up 74 km out |
| UR520 | 2026-10-18 | EBB-MGQ | board, scheduled | track incomplete |
| UR111 | 2026-10-25 | LGW-EBB | board, scheduled | track stops 3722 km short |
| UR712 | 2026-10-25 | EBB-JNB | board, scheduled | track stops 598 km short |
| UR343 | 2026-10-26 | MBA-EBB | board, actual | track stops 67 km short |
| UR208 | 2026-10-26 | EBB-NBO | board, scheduled | track stops 181 km short |
| UR900 | 2026-10-27 | EBB-LOS | board, scheduled | track stops 2669 km short |
| UR110 | 2026-10-27 | EBB-LGW | board, scheduled | track stops 5750 km short |
| UR712 | 2026-10-27 | EBB-JNB | board, scheduled | track stops 1595 km short |
| UR111 | 2026-10-27 | LGW-EBB | board, scheduled | track stops 5061 km short |
| UR209 | 2026-10-27 | NBO-EBB | board, scheduled | track stops 258 km short |
| UR710 | 2026-10-28 | EBB-JNB | board, scheduled | track stops 1016 km short |
| UR722 | 2026-10-28 | EBB-HRE | board, scheduled | track stops 1961 km short |
| UR430 | 2026-10-28 | EBB-BOM | board, scheduled | track stops 2739 km short |
| UR209 | 2026-10-29 | NBO-EBB | board, scheduled | track stops 402 km short |
| UR431 | 2026-10-29 | BOM-EBB | board, scheduled | track stops 247 km short |
| UR712 | 2026-10-29 | EBB-JNB | board, scheduled | track stops 2007 km short |
| UR323 | 2026-10-29 | DAR-EBB | board, scheduled | track stops 164 km short |
| UR710 | 2026-10-30 | EBB-JNB | board, scheduled | track stops 1144 km short |
| UR110 | 2026-10-30 | EBB-LGW | board, scheduled | track stops 6105 km short |
| UR111 | 2026-10-30 | LGW-EBB | board, scheduled | track stops 5675 km short |
| UR323 | 2026-10-30 | DAR-EBB | board, scheduled | track stops 389 km short |
| UR901 | 2026-10-30 | LOS-EBB | board, scheduled | track stops 3267 km short |
| UR710 | 2026-10-31 | EBB-JNB | board, scheduled | track stops 1079 km short |
| UR323 | 2026-10-31 | DAR-EBB | board, scheduled | track stops 994 km short |

## Route discrepancies

Sectors the aircraft flew under a through flight number, where the track
shows a landing the flight record does not name. The log follows the track.

| flight | date | logged as | flight record |
|---|---|---|---|
| UR323 | 2026-10-11 | DAR-NBO | DAR-EBB |
| UR121 | 2026-10-13 | JUB-NBO | JUB-EBB |
| UR711 | 2026-10-21 | JNB-HRE | JNB-EBB |
