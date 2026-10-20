# Runway usage — 1–16 October 2026 (rebuilt 2026-10-20)

`runway_usage.csv` was regenerated from the month zip by
`work/rebuild_month.py` using a **simplified model**: the mean ground-roll
heading (fixes faster than 20 kt around liftoff/touchdown) is snapped to the
airport's runway headings. It fills the legacy columns for airport, runway,
confidence, heading, ground-roll distance and liftoff/touchdown speed. The
frozen build's threshold-crossing, along-track and performance-survey
columns are **blank** — they depended on reference data that is not in this
repository and cannot be reproduced honestly.

## Entebbe (HUEN) — 1–16 October

| | runway 17 | runway 35 | undetermined |
|---|---:|---:|---:|
| departures (161 from EBB) | 140 | 21 | 0 |
| arrivals (158 to EBB) | 126 | 32 | 0 |

Same pattern as September: runway 17 works ~87% of departures and ~80% of
arrivals, with 35 used in overnight northerly flow.

## Confidence

High (roll heading within 12° of a runway heading): 308 of 335 departures,
297 of 335 arrivals. Blank runway = no usable ground roll in the track
(takeoff/landing not observed, or no heading table for that airport).
Treat medium/low-confidence rows as indicative only.

Outstation runway labels use published runway headings; Johannesburg and
Mumbai labels give direction only (no L/R/C designator).
