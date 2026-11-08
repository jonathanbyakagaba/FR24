# Uganda Airlines — September 2026

Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the
month's Flightradar24 track exports (`archive/2026-09/tracks/`, 607 files).

| field | value |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| period | 01SEP26 – 30SEP26 |
| flights | 589 |
| airborne | 1,219 h 51 min |
| distance flown | 974,373 km (complete tracks only) |
| track coverage | 581 of 589 flights end to end |
| city pairs | 29 directional / 16 undirected |
| rotations | 137 (38 with an untracked hop) |
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

## Rotations

A rotation is one airframe's day of flying, its legs chained in order: 137
this month, 99 with every sector of the chain in the record. In the 38 below,
the aircraft puts down at one airport and is next heard from at another, so it
must have flown a sector the movement board does not hold — 45 such hops. They
are kept in place rather than dropped, so a rotation reads from its first
departure to its last arrival instead of breaking into orphan sectors. The
airport that is only reachable through a hop is bracketed in the chain, and
work/fetch_fr24_tracks.py goes and fetches the sector itself where
Flightradar24 credentials allow, after which the brackets come off on the next
rebuild.

```
EBB–HRE  UR720  →  HRE–[LUN]  →  LUN–EBB  UR721      one rotation
```

| rotation | aircraft | chain | legs | first off – last on (EBB) |
|---|---|---|---|---|
| 5X-KDP-20260901 | 5X-KDP CRJ9 | EBB–MGQ–EBB–HRE–[LUN]–EBB | 4 | 01SEP26 05:06 – 22:36 |
| 5X-KOB-20260902 | 5X-KOB CRJ9 | EBB–JUB–EBB–ZNZ–[JRO]–EBB–MBA–EBB | 6 | 02SEP26 07:21 – 03SEP 00:03 |
| 5X-EQU-20260902 | 5X-EQU CRJ9 | EBB–HRE–[LUN]–EBB–DAR–EBB | 4 | 02SEP26 12:16 – 03SEP 02:05 |
| ET-APL-20260903 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 03SEP26 13:40 – 04SEP 04:04 |
| 5X-KOB-20260904 | 5X-KOB CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 04SEP26 09:13 – 05SEP 05:17 |
| ET-APL-20260905 | ET-APL B738 | LOS–EBB–JNB–EBB–LUN–[HRE]–EBB | 5 | 05SEP26 05:43 – 06SEP 05:00 |
| 5X-EQU-20260905 | 5X-EQU CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 05SEP26 13:17 – 21:01 |
| 5X-EQU-20260906 | 5X-EQU CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 06SEP26 09:20 – 07SEP 05:09 |
| 5X-EQU-20260907 | 5X-EQU CRJ9 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 07SEP26 09:44 – 08SEP 05:15 |
| ET-APL-20260908 | ET-APL B738 | JNB–EBB–HRE–[LUN]–EBB–JNB | 4 | 08SEP26 04:01 – 09SEP 03:03 |
| 5X-EQU-20260909 | 5X-EQU CRJ9 | EBB–JUB–EBB–ZNZ–[JRO]–EBB–MBA–EBB | 6 | 09SEP26 07:00 – 23:25 |
| 5X-KOB-20260909 | 5X-KOB CRJ9 | EBB–HRE–[LUN]–EBB–DAR–EBB | 4 | 09SEP26 12:02 – 10SEP 02:26 |
| ET-APL-20260910 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 10SEP26 13:21 – 11SEP 02:47 |
| 5X-KOB-20260911 | 5X-KOB CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 11SEP26 09:17 – 12SEP 04:44 |
| 5X-EQU-20260912 | 5X-EQU CRJ9 | EBB–MGQ–EBB–HRE–[LUN]–EBB–NBO–EBB | 6 | 12SEP26 05:10 – 13SEP 01:10 |
| ET-APL-20260912 | ET-APL B738 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 12SEP26 09:45 – 13SEP 05:33 |
| 5X-EQU-20260913 | 5X-EQU CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 13SEP26 09:29 – 14SEP 04:30 |
| ET-APL-20260915 | ET-APL B738 | EBB–HRE–[LUN]–EBB–JNB | 3 | 15SEP26 13:10 – 16SEP 02:36 |
| ET-APL-20260916 | ET-APL B738 | JNB–EBB–HRE–[LUN]–EBB–NBO–EBB | 5 | 16SEP26 04:14 – 17SEP 01:42 |
| 5X-KOB-20260916 | 5X-KOB CRJ9 | EBB–JUB–EBB–ZNZ–[JRO]–EBB–BJM–EBB–MBA–EBB | 8 | 16SEP26 06:58 – 17SEP 02:59 |
| ET-APL-20260917 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 17SEP26 13:29 – 18SEP 03:03 |
| 5X-KDP-20260918 | 5X-KDP CRJ9 | JNB–EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 7 | 18SEP26 04:09 – 19SEP 05:04 |
| ET-APL-20260919 | ET-APL B738 | LOS–EBB–JNB–EBB–LUN–[HRE]–EBB | 5 | 19SEP26 04:43 – 20SEP 05:26 |
| 5X-KOB-20260920 | 5X-KOB CRJ9 | EBB–MGQ–EBB–ZNZ–[JRO]–EBB–NBO–EBB–LUN | 7 | 20SEP26 05:06 – 21SEP 01:42 |
| 5X-KOB-20260921 | 5X-KOB CRJ9 | HRE–EBB–NBO–EBB–BJM–EBB–LUN–[HRE]–EBB | 7 | 21SEP26 04:17 – 22SEP 05:15 |
| ET-APL-20260922 | ET-APL B738 | JNB–EBB–HRE–[LUN]–EBB–JNB | 4 | 22SEP26 04:04 – 23SEP 02:52 |
| 5X-KDP-20260923 | 5X-KDP CRJ9 | EBB–NBO–EBB–ZNZ–[JRO]–EBB–BJM–EBB–MBA–EBB | 8 | 23SEP26 06:05 – 24SEP 00:07 |
| 5X-KOB-20260923 | 5X-KOB CRJ9 | EBB–JUB–EBB–HRE–[LUN]–EBB–NBO–EBB | 6 | 23SEP26 06:48 – 24SEP 01:02 |
| ET-APL-20260924 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 24SEP26 13:20 – 25SEP 05:29 |
| 5X-KOB-20260925 | 5X-KOB CRJ9 | JNB–EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 7 | 25SEP26 04:05 – 26SEP 05:06 |
| ET-APL-20260926 | ET-APL B738 | LOS–EBB–JNB–EBB–LUN–[HRE]–EBB | 5 | 26SEP26 04:59 – 27SEP 05:20 |
| 5X-KDP-20260926 | 5X-KDP CRJ9 | EBB–HRE–[LUN]–EBB–NBO–EBB | 4 | 26SEP26 12:47 – 27SEP 01:00 |
| 5X-KDP-20260927 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 27SEP26 09:30 – 28SEP 04:53 |
| 5X-KOB-20260928 | 5X-KOB CRJ9 | EBB–JUB–EBB–DAR–EBB–NBO–EBB–LUN–[HRE]–NBO | 8 | 28SEP26 07:04 – 29SEP 06:51 |
| ET-APL-20260929 | ET-APL B738 | JNB–EBB–HRE–[LUN]–EBB–JNB | 4 | 29SEP26 04:03 – 30SEP 03:00 |
| 5X-KOB-20260930 | 5X-KOB CRJ9 | EBB–JUB–EBB–HRE–[LUN]–EBB–DAR | 5 | 30SEP26 06:58 – 23:30 |
| 5X-EQU-20260930 | 5X-EQU CRJ9 | EBB–NBO–EBB–ZNZ–[JRO]–EBB–MBA | 5 | 30SEP26 08:14 – 21:05 |
| 5X-KDP-20260930 | 5X-KDP CRJ9 | EBB–UG-0013–[EBB]–BJM–EBB–NBO | 4 | 30SEP26 09:06 – 22:48 |

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
