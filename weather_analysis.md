# Airport conditions and what they explain

Published METAR observations joined to each flight: **208 of 223** take-offs and **208** landings have an observation within three hours.
Source: Iowa Environmental Mesonet ASOS archive (the same reports feed NOAA's Integrated
Surface Database), August–September 2026, one row per observation in `reference/weather_2026-09.csv`.

**Coverage: 40 of 45 airports** in this operation file reports. No observations exist for FZKA, FZNA, HJJJ, HSSK, OESB — Juba simply does not appear in the archive, so any Juba analysis has to come from the aircraft's own track.

## Runway in use vs the wind

| | flights with a wind observation | chose the into-wind runway | chose the other end | calm (<3 kt) |
|---|---|---|---|---|
| Take-off | 171 | **109** | 62 | 25 |
| Landing | 169 | **82** | 87 | 27 |

Most of the "other end" cases are airports with a single physical runway where the difference between the two ends is small; only **0 of 62** of them actually took off with more than 5 kt of tailwind. They cluster at EBB (34), DAR (8), LGW (4), NBO (4).

## Wind components on the runway actually used

- **Take-off**: median headwind component 5 kt, median crosswind 2 kt; **0 of 188** had more than 5 kt of tailwind.
- **Landing**: median headwind component 4 kt, median crosswind 2 kt; **5 of 189** had more than 5 kt of tailwind.

Landings with the strongest crosswind component:

| flight | date | airport | runway | wind | crosswind | gust |
|---|---|---|---|---|---|---|
| UGD431 | 10SEP26 | EBB | 17 | 230° / 18 kt | +15 kt | — |

**20 flights** took off or landed with weather actually in the report — these are the ones where conditions, not just traffic, were a factor:

| condition | flights | examples |
|---|---|---|
| `arr BR` | 4 | UGD430 02SEP EBB-BOM, UGD430 05SEP EBB-BOM, UGD712 07SEP EBB-JNB |
| `dep HZ` | 2 | UGD720 06SEP HRE-EBB, UGD431 10SEP BOM-EBB |
| `dep -RA` | 2 | UGD901 07SEP LOS-EBB, UGD710 11SEP EBB-JNB |
| `arr -TSRA` | 2 | UGD521 08SEP MGQ-EBB, UGD201 08SEP NBO-EBB |
| `dep -SHRA` | 1 | UGD431 03SEP BOM-EBB |
| `arr VCTS` | 1 | UGD710 04SEP EBB-JNB |
| `arr HZ` | 1 | UGD722 05SEP EBB-HRE |
| `dep TS HZ` | 1 | UGD722 05SEP LUN-EBB |

- **12** landings had visibility below 5 statute miles.
- UGD430 02SEP BOM 2 SM, UGD722 05SEP HRE 2 SM, UGD430 05SEP BOM 2 SM, UGD360 06SEP BJM 5 SM, UGD900 07SEP LOS 3 SM, UGD360 07SEP BJM 5 SM, UGD712 07SEP JNB 3 SM, UGD713 08SEP EBB 4 SM.
- Warmest departures — density altitude is the hidden variable on the long-roll days: UGD321 06SEP DAR 32°C, UGD321 07SEP DAR 32°C, UGD321 01SEP DAR 32°C, UGD361 06SEP BJM 31°C, UGD361 07SEP BJM 31°C.

## Does the wind show up in the measured distances?

**Take-off run, like for like** — each aircraft against its own median in winds below 5 kt (so the A330 cannot be mistaken for a wind effect):

| tail | type | median change at 5 kt+ headwind | n (>=5 kt / <5 kt) |
|---|---|---|---|
| 5X-KDP | CRJ900 | -427 m | 25 / 21 |
| 5X-NIL | A330-800neo | -360 m | 6 / 6 |
| ET-APL | 737-800 | -236 m | 15 / 17 |
| 5X-KOB | CRJ900 | -170 m | 24 / 17 |
| 5X-EQU | CRJ900 | -62 m | 19 / 17 |

Mean change across the fleet: **-251 m**.

**Landing roll, like for like** — each aircraft against its own median in winds below 5 kt (so the A330 cannot be mistaken for a wind effect):

| tail | type | median change at 5 kt+ headwind | n (>=5 kt / <5 kt) |
|---|---|---|---|
| 5X-EQU | CRJ900 | -186 m | 14 / 17 |
| 5X-KDP | CRJ900 | -133 m | 21 / 24 |
| ET-APL | 737-800 | -90 m | 14 / 17 |
| 5X-KOB | CRJ900 | -67 m | 21 / 13 |
| 5X-NIL | A330-800neo | +94 m | 4 / 5 |

Mean change across the fleet: **-76 m**.

## Where the schedule stretched

5 flights ran more than 10 % over the median for their own sector (`flight_conditions.csv` carries the wind and weather for each):

| flight | date | sector | air min | sector median | over | wind at departure | weather |
|---|---|---|---|---|---|---|---|
| UGD520 | 11SEP | EBB-MGQ | 136 | 117 | +16 % | 360° / 3 kt | — |
| UGD521 | 08SEP | MGQ-EBB | 116 | 101 | +15 % | 210° / 14 kt | -TSRA |
| UGD521 | 11SEP | MGQ-EBB | 113 | 101 | +12 % | 220° / 14 kt | — |
| UGD200 | 02SEP | EBB-NBO | 57 | 51 | +12 % | 110° / 14 kt | — |
| UGD360 | 03SEP | EBB-BJM | 54 | 49 | +10 % | 180° / 11 kt | — |

Of those, **1 of 5** had weather in the report at one end — so most of the stretch is traffic, sequencing or routeing, not the sky.


