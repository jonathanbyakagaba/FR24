# Runway usage — September 2026 (rebuilt 2026-10-20)

`runway_usage.csv` was regenerated from the month zip by
`work/rebuild_month.py` using a **simplified model**: the mean ground-roll
heading (fixes faster than 20 kt around liftoff/touchdown) is snapped to the
airport's runway headings. It fills the legacy columns for airport, runway,
confidence, heading, ground-roll distance and liftoff/touchdown speed. The
frozen build's threshold-crossing, along-track and performance-survey
columns are **blank** — they depended on reference data that is not in this
repository and cannot be reproduced honestly.

## Entebbe (HUEN) — September

| | runway 17 | runway 35 | undetermined |
|---|---:|---:|---:|
| departures (298 from EBB) | 275 | 23 | 0 |
| arrivals (298 to EBB) | 264 | 34 | 0 |

Runway 17 dominates in both directions (92% of departures, 89% of arrivals),
matching the daytime southerly lake breeze: most of the day Entebbe works
into a 160–190° wind. Runway 35 use clusters overnight and in northerly
spells.

## Confidence

High (roll heading within 12° of a runway heading): 588 of 640 departures,
549 of 640 arrivals. Blank runway = no usable ground roll in the track
(takeoff/landing not observed, or the airport has no heading table here —
e.g. Hoima). Treat medium/low-confidence rows as indicative only.

## Reading the other airports

Outstation runway labels use published runway headings for NBO, DAR, ZNZ,
JRO, JUB, MGQ, BJM, MBA, LUN, HRE, JNB, BOM, LGW, LOS and KGL. Johannesburg
and Mumbai have parallel/multiple runways; the label gives the direction
(03/21, 09/27…) without the L/R/C designator.
