# Uganda Airlines — September 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-09/tracks/`, 594 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01SEP26 – 30SEP26 |
| flights | 589 |
| airborne | 1,219 h 51 min |
| distance flown | 974,373 km (complete tracks only) |
| track coverage | 581 of 589 flights end to end |
| city pairs | 29 directional / 16 undirected |
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
*eff 01SEP26* 6 weekly CRJ900  
UR361 BJM1736 – 1924EBB CRJ9 123457

**Dar es Salaam – Entebbe**  
*eff 01SEP26* 6 weekly CRJ900 / 737-800  
UR321 DAR1425 – 1553EBB CRJ9 127
UR323 DAR0033 – 0202EBB CRJ9 14567

**Entebbe – Bujumbura**  
*eff 01SEP26* 6 weekly CRJ900  
UR360 EBB1628 – 1611BJM CRJ9 123457

**Entebbe – Dar es Salaam**  
*eff 01SEP26* 1 daily CRJ900 / 737-800  
UR320 EBB1150 – 1314DAR CRJ9 127
UR322 EBB2201 – 2325DAR CRJ9 13456

**Entebbe – Harare**  
*eff 01SEP26* 4 weekly 737-800 / CRJ900  
UR722 EBB1343 – 1524HRE B738 2346

**Entebbe – Hoima**  
*eff 27SEP26* 3 weekly CRJ900  
UR523 EBB1237 – 1256 UG-0013 CRJ9 237

**Entebbe – Johannesburg**  
*eff 01SEP26* 1 daily 737-800 / CRJ900  
UR710 EBB0956 – 1245JNB B738 1356
UR712 EBB2243 – 0136(+1)JNB B738 1247

**Entebbe – Juba**  
*eff 02SEP26* 1 daily CRJ900  
UR120 EBB1218 – 1209JUB CRJ9 234567
UR122 EBB0721 – 0708JUB CRJ9 13

**Entebbe – Lagos**  
*eff 04SEP26* 5 weekly 737-800  
UR900 EBB1038 – 1236LOS B738 17
UR902 EBB0001 – 0204LOS B738 456

**Entebbe – London Gatwick**  
*eff 01SEP26* 3 weekly A330-800  
UR110 EBB1052 – 1641LGW A338 257

**Entebbe – Lusaka**  
*eff 04SEP26* 4 weekly CRJ900 / 737-800  
UR720 EBB2115 – 2236LUN CRJ9 1567

**Entebbe – Mogadishu**  
*eff 01SEP26* 4 weekly CRJ900  
UR520 EBB0506 – 0703MGQ CRJ9 2567

**Entebbe – Mombasa**  
*eff 02SEP26* 4 weekly CRJ900  
UR342 EBB2003 – 2116MBA CRJ9 1357

**Entebbe – Mumbai**  
*eff 02SEP26* 2 weekly A330-800  
UR430 EBB2137 – 0621(+1)BOM A338 36

**Entebbe – Nairobi**  
*eff 01SEP26* 1 daily CRJ900 / 737-800  
UR200 EBB0818 – 0910NBO CRJ9 1234567
UR206 EBB1819 – 1906NBO CRJ9 1257
UR208 EBB2212 – 2257NBO CRJ9 13467

**Entebbe – Zanzibar**  
*eff 02SEP26* 3 weekly CRJ900  
UR334 EBB1237 – 1358ZNZ CRJ9 357

**Harare – Entebbe**  
*eff 05SEP26* 4 weekly CRJ900 / 737-800  
UR720 HRE0137 – 0517EBB CRJ9 1267

**Harare – Nairobi**  
*eff 29SEP26* 1 weekly CRJ900  
UR720 HRE0228 – 0651NBO CRJ9 2

**Hoima – Entebbe**  
*eff 27SEP26* 1 weekly CRJ900  
UR523 UG-0013 1408 – 1429EBB CRJ9 7

**Johannesburg – Entebbe**  
*eff 01SEP26* 5 weekly 737-800 / CRJ900  
UR711 JNB1422 – 1920EBB B738 1356
UR713 JNB0257 – 0742EBB B738 1235

**Juba – Entebbe**  
*eff 02SEP26* 1 daily CRJ900  
UR121 JUB1505 – 1653EBB CRJ9 234567
UR123 JUB0832 – 1021EBB CRJ9 13

**Kilimanjaro – Entebbe**  
*eff 02SEP26* 3 weekly CRJ900  
UR334 JRO1649 – 1747EBB CRJ9 357

**Lagos – Entebbe**  
*eff 04SEP26* 4 weekly 737-800  
UR901 LOS1428 – 2046EBB B738 17
UR903 LOS0344 – 0954EBB B738 56

**London Gatwick – Entebbe**  
*eff 01SEP26* 4 weekly A330-800  
UR111 LGW2029 – 0630(+1)EBB A338 2357

**Lusaka – Entebbe**  
*eff 01SEP26* 4 weekly 737-800 / CRJ900  
UR722 LUN1912 – 2236EBB B738 2346

**Mogadishu – Entebbe**  
*eff 01SEP26* 4 weekly CRJ900  
UR521 MGQ0908 – 1056EBB CRJ9 2567

**Mombasa – Entebbe**  
*eff 02SEP26* 6 weekly CRJ900  
UR343 MBA2248 – 0003(+1)EBB CRJ9 134567

**Mumbai – Entebbe**  
*eff 03SEP26* 2 weekly A330-800  
UR431 BOM0841 – 1202EBB A338 47

**Nairobi – Entebbe**  
*eff 01SEP26* 1 daily CRJ900 / 737-800  
UR201 NBO1007 – 1054EBB CRJ9 1234567
UR207 NBO0705 – 0748EBB CRJ9 1257
UR209 NBO0013 – 0100EBB CRJ9 12457

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| NBO-EBB | 66 | 7 | CRJ900 / 737-800 | 521 | 47 |
| EBB-NBO | 66 | 7 | CRJ900 / 737-800 | 521 | 45 |
| JNB-EBB | 30 | 5 | 737-800 / CRJ900 | 2946 | 224 |
| EBB-DAR | 30 | 7 | CRJ900 / 737-800 | 1074 | 84 |
| EBB-JUB | 30 | 7 | CRJ900 | 545 | 50 |
| JUB-EBB | 30 | 7 | CRJ900 | 545 | 47 |
| DAR-EBB | 29 | 6 | CRJ900 / 737-800 | 1074 | 87 |
| EBB-JNB | 29 | 7 | 737-800 / CRJ900 | 2946 | 235 |
| EBB-BJM | 26 | 6 | CRJ900 | 511 | 45 |
| BJM-EBB | 26 | 6 | CRJ900 | 511 | 49 |
| EBB-MGQ | 17 | 4 | CRJ900 | 1447 | 115 |
| EBB-HRE | 17 | 4 | 737-800 / CRJ900 | 2004 | 157 |
| LUN-EBB | 17 | 4 | 737-800 / CRJ900 | 1765 | 141 |
| MGQ-EBB | 16 | 4 | CRJ900 | 1447 | 117 |
| EBB-LOS | 15 | 5 | 737-800 | 3312 | 244 |
| LOS-EBB | 15 | 4 | 737-800 | 3312 | 256 |
| EBB-LUN | 15 | 4 | CRJ900 / 737-800 | 1765 | 141 |
| HRE-EBB | 14 | 4 | CRJ900 / 737-800 | 2004 | 154 |
| EBB-LGW | 13 | 3 | A330-800 | 6457 | 486 |
| LGW-EBB | 13 | 4 | A330-800 | 6457 | 481 |
| EBB-ZNZ | 13 | 3 | CRJ900 | 1025 | 80 |
| JRO-EBB | 13 | 3 | CRJ900 | 643 | 58 |
| EBB-MBA | 13 | 4 | CRJ900 | 915 | 73 |
| MBA-EBB | 12 | 6 | CRJ900 | 915 | 74 |
| EBB-BOM | 9 | 2 | A330-800 | 4890 | 366 |
| BOM-EBB | 8 | 2 | A330-800 | 4890 | 348 |
| EBB-UG-0013 | 4 | 3 | CRJ900 | 218 | 21 |
| UG-0013-EBB | 2 | 1 | CRJ900 | 218 | 22 |
| HRE-NBO | 1 | 1 | CRJ900 | 1954 | 203 |

## Track coverage

8 of the 589 flights have a track that covers only part of
the flight: the export starts after take-off, stops in the cruise, or both.
They are still logged — the flight happened and its days are not in doubt.
The route comes from the flight record; the times come from the movement board's actual times (7 flights) and the partial track itself (1 flights).

| flight | date | logged as | times from | what the track covers |
|---|---|---|---|---|
| UR520 | 2026-09-01 | EBB-MGQ | board, actual | track stops 91 km short |
| UR520 | 2026-09-04 | EBB-MGQ | board, actual | track stops 128 km short |
| UR520 | 2026-09-05 | EBB-MGQ | board, actual | track incomplete |
| UR520 | 2026-09-06 | EBB-MGQ | board, actual | track stops 48 km short |
| UR521 | 2026-09-11 | MGQ-EBB | board, actual | track picks the flight up 72 km out |
| UR520 | 2026-09-19 | EBB-MGQ | board, actual | track incomplete |
| UR520 | 2026-09-22 | EBB-MGQ | board, actual | track incomplete |
| UR523 | 2026-09-29 | EBB-UG-0013 | the track | track incomplete |

## Route discrepancies

Sectors the aircraft flew under a through flight number, where the track
shows a landing the flight record does not name. The log follows the track.

| flight | date | logged as | flight record |
|---|---|---|---|
| UR720 | 2026-09-29 | HRE-NBO | HRE-EBB |
