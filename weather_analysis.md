# Airport conditions and what they explain

Published METAR observations joined to each flight: **561 of 597** take-offs and **558** landings have an observation within three hours.
Source: Iowa Environmental Mesonet ASOS archive (the same reports feed NOAA's Integrated
Surface Database), August–September 2026, one row per observation in `reference/weather_2026-09.csv`.

**Coverage: 41 of 46 airports** in this operation file reports. No observations exist for FZKA, FZNA, HJJJ, HSSK, OESB — Juba simply does not appear in the archive, so any Juba analysis has to come from the aircraft's own track.

## Runway in use vs the wind

| | flights with a wind observation | chose the into-wind runway | chose the other end | calm (<3 kt) |
|---|---|---|---|---|
| Take-off | 468 | **250** | 218 | 58 |
| Landing | 469 | **215** | 254 | 63 |

Most of the "other end" cases are airports with a single physical runway where the difference between the two ends is small; only **9 of 218** of them actually took off with more than 5 kt of tailwind. They cluster at EBB (132), DAR (20), LOS (13), NBO (12).

## Wind components on the runway actually used

- **Take-off**: median headwind component 4 kt, median crosswind 2 kt; **9 of 512** had more than 5 kt of tailwind.
- **Landing**: median headwind component 3 kt, median crosswind 2 kt; **14 of 518** had more than 5 kt of tailwind.

Landings with the strongest crosswind component:

| flight | date | airport | runway | wind | crosswind | gust |
|---|---|---|---|---|---|---|
| UGD713 | 29SEP26 | EBB | 35 | 90° / 17 kt | +17 kt | — |
| UGD431 | 10SEP26 | EBB | 17 | 230° / 18 kt | +15 kt | — |

**64 flights** took off or landed with weather actually in the report — these are the ones where conditions, not just traffic, were a factor:

| condition | flights | examples |
|---|---|---|
| `arr HZ` | 7 | UGD722 05SEP EBB-HRE, UGD722 16SEP EBB-HRE, UGD430 16SEP EBB-BOM |
| `arr -RA` | 7 | UGD900 07SEP EBB-LOS, UGD110 13SEP EBB-LGW, UGD322D 17SEP EBB-DAR |
| `arr BR` | 5 | UGD430 02SEP EBB-BOM, UGD430 05SEP EBB-BOM, UGD712 07SEP EBB-JNB |
| `dep -RA` | 5 | UGD901 07SEP LOS-EBB, UGD710 11SEP EBB-JNB, UGD111 18SEP LGW-EBB |
| `dep TS` | 5 | UGD320 08SEP EBB-DAR, UGD120 13SEP EBB-JUB, UGD361 24SEP BJM-EBB |
| `dep HZ` | 4 | UGD720 06SEP HRE-EBB, UGD431 10SEP BOM-EBB, UGD720 19SEP HRE-EBB |
| `arr TSRA` | 4 | UGD903 11SEP LOS-EBB, UGD111 13SEP LGW-EBB, UGD201 16SEP NBO-EBB |
| `dep TSRA` | 4 | UGD722 12SEP EBB-HRE, UGD120 12SEP EBB-JUB, UGD200 17SEP EBB-NBO |

- **38** landings had visibility below 5 statute miles.
- UGD430 02SEP BOM 2 SM, UGD722 05SEP HRE 2 SM, UGD430 05SEP BOM 2 SM, UGD360 06SEP BJM 5 SM, UGD900 07SEP LOS 3 SM, UGD360 07SEP BJM 5 SM, UGD712 07SEP JNB 3 SM, UGD713 08SEP EBB 4 SM.
- Warmest departures — density altitude is the hidden variable on the long-roll days: UGD321 01SEP DAR 32°C, UGD321 13SEP DAR 32°C, UGD321 29SEP DAR 32°C, UGD722 16SEP LUN 32°C, UGD321 22SEP DAR 32°C.

## Does the wind show up in the measured distances?

**Take-off run, like for like** — each aircraft against its own median in winds below 5 kt (so the A330 cannot be mistaken for a wind effect):

| tail | type | median change at 5 kt+ headwind | n (>=5 kt / <5 kt) |
|---|---|---|---|
| 5X-NIL | A330-800neo | -477 m | 14 / 23 |
| 5X-KDP | CRJ900 | -291 m | 47 / 62 |
| ET-APL | 737-800 | -146 m | 38 / 56 |
| 5X-EQU | CRJ900 | -9 m | 41 / 46 |
| 5X-KOB | CRJ900 | +2 m | 55 / 65 |

Mean change across the fleet: **-184 m**.

**Landing roll, like for like** — each aircraft against its own median in winds below 5 kt (so the A330 cannot be mistaken for a wind effect):

| tail | type | median change at 5 kt+ headwind | n (>=5 kt / <5 kt) |
|---|---|---|---|
| ET-APL | 737-800 | -243 m | 36 / 55 |
| 5X-EQU | CRJ900 | -158 m | 34 / 46 |
| 5X-KDP | CRJ900 | -124 m | 44 / 63 |
| 5X-KOB | CRJ900 | -107 m | 46 / 68 |
| 5X-NIL | A330-800neo | +106 m | 6 / 17 |

Mean change across the fleet: **-105 m**.

## Where the schedule stretched

9 flights ran more than 10 % over the median for their own sector (`flight_conditions.csv` carries the wind and weather for each):

| flight | date | sector | air min | sector median | over | wind at departure | weather |
|---|---|---|---|---|---|---|---|
| UGD712 | 24SEP | EBB-JNB | 332 | 239 | +39 % | 240° / 5 kt | — |
| UGD520 | 11SEP | EBB-MGQ | 136 | 118 | +16 % | 360° / 3 kt | — |
| UGD123 | 30SEP | JUB-EBB | 67 | 51 | +31 % | — | — |
| UGD520 | 12SEP | EBB-MGQ | 132 | 118 | +12 % | 360° / 4 kt | — |
| UGD722 | 29SEP | HRE-LUN | 53 | 45 | +18 % | 60° / 12 kt | — |
| UGD200 | 02SEP | EBB-NBO | 57 | 50 | +14 % | 110° / 14 kt | — |
| UGD200 | 27SEP | EBB-NBO | 57 | 50 | +14 % | 360° / 12 kt | — |
| UGD206 | 15SEP | EBB-NBO | 56 | 50 | +12 % | 140° / 6 kt | — |
| UGD360 | 03SEP | EBB-BJM | 54 | 49 | +10 % | 180° / 11 kt | — |

Of those, **0 of 9** had weather in the report at one end — so most of the stretch is traffic, sequencing or routeing, not the sky.


