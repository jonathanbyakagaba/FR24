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
| rotations | 152 (41 with an untracked hop) |
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

## Rotations

A rotation is one airframe's day of flying, its legs chained in order: 152
this month, 111 with every sector of the chain in the record. In the 41 below,
the aircraft puts down at one airport and is next heard from at another, so it
must have flown a sector the movement board does not hold — 47 such hops. They
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
| ET-APL-20260801 | ET-APL B738 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 01AUG26 09:46 – 02AUG 05:23 |
| 5X-KOB-20260801 | 5X-KOB CRJ9 | EBB–HRE–[LUN]–EBB–DAR | 3 | 01AUG26 13:42 – 02AUG 03:04 |
| 5X-EQU-20260802 | 5X-EQU CRJ9 | EBB–MGQ–EBB–DAR–EBB–NBO–EBB–LUN–[HRE]–EBB | 8 | 02AUG26 05:10 – 03AUG 04:54 |
| 5X-KDP-20260802 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–NBO–EBB | 6 | 02AUG26 09:25 – 03AUG 02:12 |
| 5X-KOB-20260803 | 5X-KOB CRJ9 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 03AUG26 09:32 – 04AUG 05:21 |
| ET-APL-20260804 | ET-APL B738 | EBB–HRE–[LUN]–EBB–JNB | 3 | 04AUG26 13:08 – 05AUG 03:52 |
| 5X-KOB-20260805 | 5X-KOB CRJ9 | EBB–JUB–EBB–ZNZ–[JRO]–EBB–MBA–EBB | 6 | 05AUG26 07:14 – 23:44 |
| 5X-KDP-20260805 | 5X-KDP CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 05AUG26 12:31 – 20:11 |
| ET-APL-20260806 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 06AUG26 14:13 – 07AUG 03:43 |
| 5X-KOB-20260807 | 5X-KOB CRJ9 | JNB–EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 7 | 07AUG26 04:09 – 08AUG 05:11 |
| ET-APL-20260808 | ET-APL B738 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 08AUG26 09:43 – 09AUG 05:23 |
| 5X-KOB-20260808 | 5X-KOB CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 08AUG26 13:13 – 21:17 |
| 5X-KOB-20260809 | 5X-KOB CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 09AUG26 09:15 – 10AUG 04:57 |
| 5X-KOB-20260810 | 5X-KOB CRJ9 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 10AUG26 09:43 – 11AUG 05:42 |
| ET-APL-20260811 | ET-APL B738 | EBB–HRE–[LUN]–EBB–JNB | 3 | 11AUG26 13:12 – 12AUG 02:39 |
| 5X-KOB-20260812 | 5X-KOB CRJ9 | EBB–JUB–EBB–ZNZ–[JRO]–EBB–MBA–EBB | 6 | 12AUG26 07:01 – 23:50 |
| 5X-KDP-20260812 | 5X-KDP CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 12AUG26 12:31 – 20:27 |
| ET-APL-20260813 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 13AUG26 13:39 – 14AUG 04:09 |
| 5X-KDP-20260814 | 5X-KDP CRJ9 | JNB–EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 7 | 14AUG26 05:50 – 15AUG 05:05 |
| 5X-KDP-20260815 | 5X-KDP CRJ9 | EBB–LUN–[HRE]–EBB | 2 | 15AUG26 21:42 – 16AUG 05:23 |
| 5X-KDP-20260816 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN | 5 | 16AUG26 09:31 – 23:38 |
| 5X-KOB-20260817 | 5X-KOB CRJ9 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 17AUG26 10:00 – 18AUG 05:30 |
| ET-APL-20260818 | ET-APL B738 | JNB–EBB–HRE–[LUN]–EBB–JNB | 4 | 18AUG26 05:34 – 19AUG 04:42 |
| 5X-KDP-20260819 | 5X-KDP CRJ9 | EBB–NBO–EBB–ZNZ–[JRO]–EBB–MBA–EBB | 6 | 19AUG26 09:50 – 23:30 |
| 5X-KOB-20260819 | 5X-KOB CRJ9 | EBB–HRE–[LUN]–EBB–DAR–EBB | 4 | 19AUG26 12:20 – 20AUG 02:19 |
| ET-APL-20260820 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 20AUG26 13:50 – 21AUG 03:42 |
| 5X-KDP-20260821 | 5X-KDP CRJ9 | JNB–EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 7 | 21AUG26 05:36 – 22AUG 04:58 |
| ET-APL-20260822 | ET-APL B738 | LOS–EBB–JNB–EBB–LUN–[HRE]–EBB | 5 | 22AUG26 05:10 – 23AUG 05:30 |
| 5X-KDP-20260822 | 5X-KDP CRJ9 | EBB–HRE–[LUN]–EBB–DAR–EBB | 4 | 22AUG26 13:22 – 23AUG 03:50 |
| 5X-KDP-20260823 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 23AUG26 09:54 – 24AUG 05:16 |
| 5X-KOB-20260824 | 5X-KOB CRJ9 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 24AUG26 09:49 – 25AUG 05:32 |
| ET-APL-20260825 | ET-APL B738 | JNB–EBB–HRE–[LUN]–EBB–JNB | 4 | 25AUG26 05:43 – 26AUG 02:32 |
| 5X-EQU-20260825 | 5X-EQU CRJ9 | EBB–NBO–EBB–[JUB]–EBB | 3 | 25AUG26 08:25 – 16:50 |
| 5X-EQU-20260826 | 5X-EQU CRJ9 | EBB–NBO–EBB–HRE–[LUN]–EBB–DAR–EBB | 6 | 26AUG26 07:55 – 27AUG 02:20 |
| 5X-KDP-20260826 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB | 4 | 26AUG26 09:16 – 18:44 |
| ET-APL-20260827 | ET-APL B738 | EBB–HRE–[LUN]–EBB–LOS | 3 | 27AUG26 14:01 – 28AUG 03:06 |
| 5X-EQU-20260828 | 5X-EQU CRJ9 | EBB–NBO–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 28AUG26 08:06 – 29AUG 05:06 |
| 5X-KDP-20260828 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–NBO–EBB–DAR–EBB | 6 | 28AUG26 09:51 – 29AUG 02:10 |
| ET-APL-20260829 | ET-APL B738 | EBB–JNB–EBB–LUN–[HRE]–EBB | 4 | 29AUG26 09:38 – 30AUG 05:22 |
| 5X-EQU-20260829 | 5X-EQU CRJ9 | EBB–HRE–[LUN]–EBB | 2 | 29AUG26 13:00 – 21:08 |
| 5X-KDP-20260830 | 5X-KDP CRJ9 | EBB–ZNZ–[JRO]–EBB–BJM–EBB–LUN–[HRE]–EBB | 6 | 30AUG26 09:21 – 31AUG 05:21 |

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
