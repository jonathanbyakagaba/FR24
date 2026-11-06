# Uganda Airlines — June 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-06/tracks/`, 431 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01JUN26 – 30JUN26 |
| flights | 430 |
| airborne | 1,021 h 53 min |
| city pairs | 28 directional / 14 undirected |
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
*eff 01JUN26* 6 weekly CRJ900  
UR361 BJM1601 – 1751EBB CRJ9 123457

**Dar es Salaam – Entebbe**  
*eff 01JUN26* 6 weekly CRJ900 / 737-800  
UR321 DAR1716 – 1848EBB CRJ9 23567
UR323 DAR1013 – 1157EBB CRJ9 1

**Entebbe – Bujumbura**  
*eff 01JUN26* 6 weekly CRJ900  
UR360 EBB1623 – 1608BJM CRJ9 123457

**Entebbe – Dar es Salaam**  
*eff 01JUN26* 6 weekly CRJ900 / 737-800  
UR320 EBB1452 – 1613DAR CRJ9 23567
UR322 EBB0726 – 0852DAR CRJ9 1

**Entebbe – Harare**  
*eff 04JUN26* 2 weekly CRJ900 / 737-800  
UR722 EBB1442 – 1620HRE CRJ9 46

**Entebbe – Johannesburg**  
*eff 01JUN26* 1 daily 737-800 / CRJ900  
UR710 EBB1326 – 1607JNB CRJ9 1356
UR712 EBB1632 – 1919JNB B738 247

**Entebbe – Juba**  
*eff 01JUN26* 1 daily CRJ900  
UR120 EBB1539 – 1533JUB CRJ9 567
UR122 EBB0652 – 0640JUB CRJ9 1234

**Entebbe – Kilimanjaro**  
*eff 07JUN26* 2 weekly CRJ900  
UR334 EBB1335 – 1429JRO CRJ9 57

**Entebbe – Lagos**  
*eff 01JUN26* 3 weekly 737-800  
UR900 EBB0833 – 1042LOS B738 147

**Entebbe – London Gatwick**  
*eff 02JUN26* 3 weekly A330-800  
UR110 EBB0123 – 0728LGW A338 257

**Entebbe – Lusaka**  
*eff 01JUN26* 2 weekly CRJ900  
UR720 EBB1053 – 1213LUN CRJ9 12

**Entebbe – Mogadishu**  
*eff 02JUN26* 4 weekly CRJ900  
UR520 EBB0526 – 0732MGQ CRJ9 2467

**Entebbe – Mombasa**  
*eff 03JUN26* 3 weekly CRJ900  
UR342 EBB0742 – 0854MBA CRJ9 357

**Entebbe – Mumbai**  
*eff 03JUN26* 2 weekly A330-800 / 737-800  
UR430 EBB2043 – 0510(+1)BOM A338 36

**Entebbe – Nairobi**  
*eff 01JUN26* 4 weekly CRJ900  
UR208 EBB1058 – 1143NBO CRJ9 1457

**Entebbe – Zanzibar**  
*eff 03JUN26* 2 weekly CRJ900  
UR334 EBB2022 – 2140ZNZ CRJ9 35

**Harare – Entebbe**  
*eff 01JUN26* 2 weekly CRJ900  
UR720 HRE1437 – 1819EBB CRJ9 13

**Johannesburg – Entebbe**  
*eff 01JUN26* 6 weekly 737-800 / CRJ900  
UR711 JNB1720 – 2216EBB CRJ9 1356
UR713 JNB0057 – 0544EBB B738 124

**Juba – Entebbe**  
*eff 01JUN26* 1 daily CRJ900  
UR121 JUB1628 – 1815EBB CRJ9 567
UR123 JUB0731 – 0918EBB CRJ9 1234

**Kilimanjaro – Entebbe**  
*eff 04JUN26* 4 weekly CRJ900  
UR334 JRO0001 – 0102EBB CRJ9 3456

**Lagos – Entebbe**  
*eff 01JUN26* 3 weekly 737-800  
UR901 LOS1218 – 1829EBB B738 147

**London Gatwick – Entebbe**  
*eff 02JUN26* 3 weekly A330-800  
UR111 LGW1040 – 2027EBB A338 257

**Lusaka – Entebbe**  
*eff 04JUN26* 2 weekly CRJ900 / 737-800  
UR722 LUN1914 – 2244EBB CRJ9 46

**Mogadishu – Entebbe**  
*eff 02JUN26* 4 weekly CRJ900  
UR521 MGQ0900 – 1057EBB CRJ9 2467

**Mombasa – Entebbe**  
*eff 03JUN26* 3 weekly CRJ900  
UR342 MBA1004 – 1122EBB CRJ9 3
UR343 MBA1022 – 1144EBB CRJ9 357

**Mumbai – Entebbe**  
*eff 04JUN26* 2 weekly A330-800 / 737-800  
UR431 BOM0844 – 1213EBB A338 47

**Nairobi – Entebbe**  
*eff 01JUN26* 4 weekly CRJ900  
UR209 NBO1305 – 1354EBB CRJ9 1457

**Zanzibar – Entebbe**  
*eff 07JUN26* 1 weekly CRJ900  
UR334 ZNZ1718 – 1843EBB CRJ9 7

## Route summary

| route | flights | weekly | equipment | great-circle km | median air min |
|---|---|---|---|---|---|
| JNB-EBB | 30 | 6 | 737-800 / CRJ900 | 2946 | 224 |
| EBB-JNB | 30 | 7 | 737-800 / CRJ900 | 2946 | 225 |
| EBB-JUB | 29 | 7 | CRJ900 | 545 | 50 |
| JUB-EBB | 29 | 7 | CRJ900 | 545 | 46 |
| EBB-DAR | 25 | 6 | CRJ900 / 737-800 | 1074 | 84 |
| DAR-EBB | 25 | 6 | CRJ900 / 737-800 | 1074 | 88 |
| BJM-EBB | 25 | 6 | CRJ900 | 511 | 48 |
| EBB-BJM | 24 | 6 | CRJ900 | 511 | 44 |
| EBB-MGQ | 17 | 4 | CRJ900 | 1447 | 116 |
| MGQ-EBB | 17 | 4 | CRJ900 | 1447 | 117 |
| EBB-NBO | 16 | 4 | CRJ900 | 521 | 46 |
| NBO-EBB | 16 | 4 | CRJ900 | 521 | 47 |
| EBB-LOS | 13 | 3 | 737-800 | 3312 | 244 |
| EBB-LGW | 13 | 3 | A330-800 | 6457 | 484 |
| LGW-EBB | 13 | 3 | A330-800 | 6457 | 484 |
| LOS-EBB | 12 | 3 | 737-800 | 3312 | 256 |
| EBB-MBA | 11 | 3 | CRJ900 | 915 | 74 |
| MBA-EBB | 11 | 3 | CRJ900 | 915 | 76 |
| EBB-LUN | 10 | 2 | CRJ900 | 1765 | 140 |
| HRE-EBB | 8 | 2 | CRJ900 | 2004 | 160 |
| EBB-BOM | 8 | 2 | A330-800 / 737-800 | 4890 | 380 |
| JRO-EBB | 8 | 4 | CRJ900 | 643 | 58 |
| BOM-EBB | 8 | 2 | A330-800 / 737-800 | 4890 | 346 |
| EBB-HRE | 8 | 2 | CRJ900 / 737-800 | 2004 | 158 |
| LUN-EBB | 8 | 2 | CRJ900 / 737-800 | 1765 | 144 |
| EBB-ZNZ | 6 | 2 | CRJ900 | 1025 | 78 |
| EBB-JRO | 6 | 2 | CRJ900 | 643 | 55 |
| ZNZ-EBB | 4 | 1 | CRJ900 | 1025 | 82 |

## Track anomalies

The log follows the track, not the flight record. Where the two disagree —
a track that stops short of its destination, or a sector flown under a
through flight number — the line above shows what the aircraft did, and the
note here says how that differs from the record the track was filed under.

| flight | date | logged as | note |
|---|---|---|---|
| UR334 | 2026-06-12 | EBB-JRO | filed as EBB-ZNZ, track EBB-JRO |
| UR334 | 2026-06-19 | EBB-JRO | filed as EBB-ZNZ, track EBB-JRO |
