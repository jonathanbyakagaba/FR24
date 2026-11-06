# Uganda Airlines — August 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-08/tracks/`, 620 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01AUG26 – 31AUG26 |
| flights | 619 |
| airborne | 1,323 h 17 min |
| distance flown | 1,049,216 km (complete tracks only) |
| track coverage | 613 of 619 flights end to end |
| city pairs | 26 directional / 14 undirected |
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
*eff 02AUG26* 6 weekly CRJ900  
UR361 BJM1729 – 1919EBB CRJ9 123457

**Dar es Salaam – Entebbe**  
*eff 01AUG26* 6 weekly CRJ900 / 737-800  
UR321 DAR1447 – 1617EBB CRJ9 127
UR323 DAR0101 – 0227EBB CRJ9 14567

**Entebbe – Bujumbura**  
*eff 02AUG26* 6 weekly CRJ900  
UR360 EBB1633 – 1617BJM CRJ9 123457

**Entebbe – Dar es Salaam**  
*eff 02AUG26* 1 daily CRJ900 / 737-800  
UR320 EBB1143 – 1308DAR CRJ9 127
UR322 EBB2201 – 2327DAR CRJ9 134567

**Entebbe – Harare**  
*eff 01AUG26* 4 weekly CRJ900 / 737-800  
UR722 EBB1231 – 1412HRE CRJ9 2346

**Entebbe – Johannesburg**  
*eff 01AUG26* 1 daily 737-800 / CRJ900  
UR710 EBB0946 – 1243JNB B738 1356
UR712 EBB2254 – 0141(+1)JNB B738 123457

**Entebbe – Juba**  
*eff 01AUG26* 1 daily CRJ900  
UR120 EBB1355 – 1346JUB CRJ9 24567
UR122 EBB0704 – 0652JUB CRJ9 13

**Entebbe – Lagos**  
*eff 02AUG26* 5 weekly 737-800  
UR900 EBB1013 – 1213LOS B738 17
UR902 EBB2349 – 0143(+1)LOS B738 456

**Entebbe – London Gatwick**  
*eff 02AUG26* 3 weekly A330-800  
UR110 EBB1058 – 1651LGW A338 257

**Entebbe – Lusaka**  
*eff 01AUG26* 4 weekly CRJ900 / 737-800  
UR720 EBB2105 – 2225LUN CRJ9 1567

**Entebbe – Mogadishu**  
*eff 01AUG26* 4 weekly CRJ900  
UR520 EBB0500 – 0651MGQ CRJ9 2567

**Entebbe – Mombasa**  
*eff 02AUG26* 3 weekly CRJ900  
UR342 EBB1854 – 2005MBA CRJ9 357

**Entebbe – Mumbai**  
*eff 01AUG26* 2 weekly A330-800  
UR430 EBB1454 – 2347BOM A338 36

**Entebbe – Nairobi**  
*eff 01AUG26* 1 daily CRJ900 / 737-800  
UR200 EBB0809 – 0853NBO CRJ9 1234567
UR206 EBB1736 – 1821NBO CRJ9 1257
UR208 EBB2212 – 2257NBO CRJ9 123467

**Entebbe – Zanzibar**  
*eff 02AUG26* 3 weekly CRJ900  
UR334 EBB0925 – 1045ZNZ CRJ9 357

**Harare – Entebbe**  
*eff 01AUG26* 4 weekly CRJ900 / 737-800  
UR720 HRE0155 – 0528EBB CRJ9 1267

**Johannesburg – Entebbe**  
*eff 01AUG26* 5 weekly 737-800 / CRJ900  
UR711 JNB1409 – 1909EBB B738 1356
UR713 JNB0305 – 0755EBB B738 1235

**Juba – Entebbe**  
*eff 01AUG26* 1 daily CRJ900  
UR121 JUB1506 – 1653EBB CRJ9 24567
UR123 JUB0808 – 0954EBB CRJ9 13

**Kilimanjaro – Entebbe**  
*eff 02AUG26* 3 weekly CRJ900  
UR334 JRO1340 – 1438EBB CRJ9 357

**Lagos – Entebbe**  
*eff 01AUG26* 4 weekly 737-800  
UR901 LOS1343 – 2003EBB B738 17
UR903 LOS0159 – 0827EBB B738 56

**London Gatwick – Entebbe**  
*eff 02AUG26* 3 weekly A330-800  
UR111 LGW2004 – 0612(+1)EBB A338 257

**Lusaka – Entebbe**  
*eff 01AUG26* 4 weekly CRJ900 / 737-800  
UR722 LUN1809 – 2130EBB CRJ9 2346

**Mogadishu – Entebbe**  
*eff 01AUG26* 4 weekly CRJ900  
UR520 MGQ0829 – 1026EBB CRJ9 57
UR521 MGQ0851 – 1046EBB CRJ9 2567

**Mombasa – Entebbe**  
*eff 02AUG26* 4 weekly CRJ900  
UR343 MBA2121 – 2237EBB CRJ9 1357

**Mumbai – Entebbe**  
*eff 02AUG26* 2 weekly A330-800  
UR431 BOM0202 – 0512EBB A338 47

**Nairobi – Entebbe**  
*eff 01AUG26* 1 daily CRJ900 / 737-800  
UR200 NBO1009 – 1059EBB CRJ9 7
UR201 NBO1008 – 1056EBB CRJ9 1234567
UR207 NBO1935 – 2021EBB CRJ9 1257
UR209 NBO2357 – 0042(+1)EBB CRJ9 124567

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| EBB-NBO | 66 | 7 | CRJ900 / 737-800 | 521 | 45 |
| NBO-EBB | 65 | 7 | CRJ900 / 737-800 | 521 | 47 |
| EBB-JNB | 35 | 7 | 737-800 / CRJ900 | 2946 | 233 |
| EBB-DAR | 35 | 7 | CRJ900 / 737-800 | 1074 | 83 |
| DAR-EBB | 34 | 6 | CRJ900 / 737-800 | 1074 | 88 |
| JNB-EBB | 34 | 5 | 737-800 / CRJ900 | 2946 | 228 |
| EBB-JUB | 30 | 7 | CRJ900 | 545 | 50 |
| JUB-EBB | 30 | 7 | CRJ900 | 545 | 46 |
| EBB-BJM | 26 | 6 | CRJ900 | 511 | 44 |
| BJM-EBB | 26 | 6 | CRJ900 | 511 | 49 |
| HRE-EBB | 19 | 4 | CRJ900 / 737-800 | 2004 | 154 |
| LOS-EBB | 19 | 4 | 737-800 | 3312 | 256 |
| EBB-LUN | 19 | 4 | CRJ900 / 737-800 | 1765 | 143 |
| MGQ-EBB | 18 | 4 | CRJ900 | 1447 | 116 |
| EBB-LOS | 18 | 5 | 737-800 | 3312 | 239 |
| EBB-MGQ | 17 | 4 | CRJ900 | 1447 | 112 |
| EBB-HRE | 16 | 4 | CRJ900 / 737-800 | 2004 | 162 |
| LUN-EBB | 16 | 4 | CRJ900 / 737-800 | 1765 | 140 |
| EBB-ZNZ | 13 | 3 | CRJ900 | 1025 | 80 |
| EBB-LGW | 13 | 3 | A330-800 | 6457 | 475 |
| JRO-EBB | 13 | 3 | CRJ900 | 643 | 58 |
| EBB-MBA | 13 | 3 | CRJ900 | 915 | 72 |
| MBA-EBB | 13 | 4 | CRJ900 | 915 | 75 |
| LGW-EBB | 13 | 3 | A330-800 | 6457 | 487 |
| EBB-BOM | 9 | 2 | A330-800 | 4890 | 377 |
| BOM-EBB | 9 | 2 | A330-800 | 4890 | 343 |

## Track coverage

6 of the 619 flights have a track that covers only part of
the flight: the export starts after take-off, stops in the cruise, or both.
They are still logged — the flight happened and its days are not in doubt.
The route comes from the flight record; the times come from the movement board's actual times (3 flights) and the partial track itself (3 flights).

| flight | date | logged as | times from | what the track covers |
|---|---|---|---|---|
| UR430 | 2026-08-01 | EBB-BOM | the track | track has a 62 minute hole en route |
| UR520 | 2026-08-08 | EBB-MGQ | board, actual | track incomplete |
| UR430 | 2026-08-08 | EBB-BOM | the track | track has a 106 minute hole en route |
| UR521 | 2026-08-21 | MGQ-EBB | board, actual | track picks the flight up 72 km out |
| UR722 | 2026-08-22 | EBB-HRE | board, actual | track incomplete |
| UR430 | 2026-08-22 | EBB-BOM | the track | track has a 80 minute hole en route |
