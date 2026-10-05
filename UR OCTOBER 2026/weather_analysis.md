# Airport conditions and what they explain

Published METAR observations joined to each flight: **77 of 82** take-offs and **76** landings have an observation within three hours.
Source: Iowa Environmental Mesonet ASOS archive (the same reports feed NOAA's Integrated
Surface Database) for the build month, one row per observation in `reference/weather_2026-10.csv`.

**Coverage: 41 of 46 airports** in this operation file reports. No observations exist for FZKA, FZNA, HJJJ, HSSK, OESB — Juba simply does not appear in the archive, so any Juba analysis has to come from the aircraft's own track.

## Runway in use vs the wind

| | flights with a wind observation | chose the into-wind runway | chose the other end | calm (<3 kt) |
|---|---|---|---|---|
| Take-off | 47 | **19** | 28 | 6 |
| Landing | 48 | **18** | 30 | 4 |

Most of the "other end" cases are airports with a single physical runway where the difference between the two ends is small; only **2 of 28** of them actually took off with more than 5 kt of tailwind. They cluster at EBB (15), DAR (2), LUN (2), LOS (2).

## Wind components on the runway actually used

- **Take-off**: median headwind component 3 kt, median crosswind 2 kt; **2 of 50** had more than 5 kt of tailwind.
- **Landing**: median headwind component 2 kt, median crosswind 3 kt; **4 of 49** had more than 5 kt of tailwind.

**11 flights** took off or landed with weather actually in the report — these are the ones where conditions, not just traffic, were a factor:

| condition | flights | examples |
|---|---|---|
| `dep -RA` | 2 | UGD200 03OCT EBB-NBO, UGD901 04OCT LOS-EBB |
| `dep HZ` | 1 | UGD431 01OCT BOM-EBB |
| `dep RA` | 1 | UGD722 01OCT HRE-LUN |
| `dep DZ` | 1 | UGD722 01OCT LUN-EBB |
| `arr TS` | 1 | UGD334 02OCT JRO-EBB |
| `dep TS` | 1 | UGD120 02OCT EBB-JUB |
| `arr -RA` | 1 | UGD903 03OCT LOS-EBB |
| `arr FU` | 1 | UGD430 03OCT EBB-BOM |

- **2** landings had visibility below 5 statute miles.
- UGD430 03OCT BOM 2 SM, UGD900 04OCT LOS 5 SM.
- Warmest departures — density altitude is the hidden variable on the long-roll days: UGD361 02OCT BJM 30°C, UGD430 03OCT EBB 29°C, UGD361 01OCT BJM 29°C, UGD722 01OCT EBB 29°C, UGD722 03OCT EBB 29°C.

## Does the wind show up in the measured distances?

## Where the schedule stretched


