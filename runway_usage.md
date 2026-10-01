# Which runway was used — and how much of it

Everything here is read from the FR24 tracks in `FR data.zip`. The exports carry **no
runway field**, so each row is *inferred* from where the aircraft actually rolled, and
then measured along that runway: where the roll started, where the wheels left the
ground, where the wheels touched down, and where the aircraft left the pavement.

Source: `runway_usage.csv` — one row per track, 66 columns. Regenerate with
`PYTHONPATH=/home/user python3 work/runways.py` then `python3 work/runway_report.py`.

## Coverage

| | known | high | medium | low | from the roll | from climb/approach heading |
|---|---|---|---|---|---|---|
| Departure runway | **694/731** | 623 | 56 | 15 | 642 | 52 |
| Arrival runway | **700/731** | 551 | 146 | 3 | 565 | 135 |
| Take-off distance measured | **612/731** (27 fallback only) | | | | | |
| Landing distance measured | **565/731** | | | | | |

- both runway ends known: **664/731** (91%)
- the airline's own (UR/UGD) tracks: departures **648/682**, arrivals **658/682**, both ends **624/682**
- tail (5X-… / ET-APL) attached from your screenshots: **594** rows — every UR track whose (date, flight, route) key matches exactly one screenshot row
- `high` = roll captured, on the centreline (mean cross-track ≤ 70 m) and heading within 10°
- `medium` = roll captured but shorter/looser, or the heading fallback with a clear margin
- `low` = heading-only evidence at an airport with a parallel strip, or a weak fit — a hint
- **33 rows get their runway from alignment rather than a roll.** Where the export starts just after the rotation or stops on short final there is nothing on the ground to match, but the aircraft is low, close to the field and lined up with one runway: the call is made from its position against that runway's extended centreline plus the heading between two fixes ~2 km apart (`climb-alignment` / `approach-alignment`). No roll, touchdown or distance figures come out of those rows.

## Why it is trustworthy

| check | departure | arrival |
|---|---|---|
| heading error vs the runway's true heading (median / p95) | 1.0° / 1.1° | 1.1° / 2.0° |
| position fixes inside the roll (median) | 10 | 11 |

The paved surface is 45–60 m wide, so a heading error of 0–1° is unambiguously *that*
runway. Laterally the strongest evidence is the roll itself: thousands of ground-roll
fixes at one runway end fit a single straight line to within a few metres (table further
down), which is both proof that the aircraft rolled straight down the runway and a
measure of how good the position data is.

Independent checks that were run:

- **Day-direction coherence.** Wind holds one direction all day, so every flight at an airport that day should use the same runway direction. Of the flights that could be compared, departures **399/399** and arrivals **394/394** agree with their day's dominant direction — **0 exceptions**.
- **Airport geometry.** Threshold-to-threshold bearings of every runway in scope were
  checked against the published runway true headings; no swapped runway ends.
- **Gatwick** returns 26L for both arrivals and departures (LGW is a single-runway
  operation); **Johannesburg** returns arrivals on 03R/21L and departures on 03L/21R —
  the parallel-strip split the airport actually uses.
- **Worked example.** `UR110-416c0a6a.csv` (UGD110, 5X-NIL) leaves Entebbe (HUEN) 17: the roll starts 136 m past the threshold at 15 kt, the wheels leave the ground 2,537 m down a 3,681 m runway (69% used), leaving 1,143 m. Bracket around the lift-off: 239 m, i.e. that is the export's time resolution.

## How much runway was used

Two moments are measured per flight, both as a distance along the runway from the
threshold of the runway in use:

**Take-off**

| figure | column | meaning |
|---|---|---|
| roll start | `dep_roll_start_m` | line-up point — the first fix after the last one below 15 kt; the take-off run begins there |
| runway used | `dep_runway_used_m` | where the wheels left the ground, measured from the threshold |
| roll length | `dep_roll_len_m` | roll start → wheels-off (the actual take-off run) |
| runway left | `dep_rwy_remaining_m` | pavement remaining ahead at wheels-off |
| bracket | `dep_liftoff_bracket_m` | gap between the last on-ground fix and the first airborne one — the export's resolution |

**Landing**

| figure | column | meaning |
|---|---|---|
| touchdown | `arr_td_along_m` | first sustained deceleration after the threshold |
| runway used | `arr_runway_used_m` | where the aircraft left the pavement (or came to a stop / turned around on it) |
| landing roll | `arr_roll_len_m` | touchdown → that point |
| runway left | `arr_rwy_remaining_m` | pavement remaining beyond that point (taxiway exits are not subtracted) |
| turn-off speed | `arr_turnoff_speed_kt` | groundspeed when the aircraft left the centreline corridor |
| bracket | `arr_td_bracket_m` | gap between the two fixes that bound the touchdown |

How the two moments are pinned down, and why they can be trusted:

- **Wheels-off** is found from the altitude trace. In these exports the altitude field
  reads exactly **0 while the aircraft is on the ground** — at every airport, including
  7,630 ft Addis — and reverts to MSL once airborne. So the lift-off is bracketed by the
  last zero-altitude fix and the first fix above it. The acceleration signature (the roll
  runs at 3–5 kt/s, then roughly halves when the aircraft pitches up) is computed
  alongside as a second opinion: `dep_accel_alt_ft` records the altitude at which it fired,
  a median of a few tens of feet above the field, i.e. it corroborates.
- **Touchdown** is found from the deceleration instead: the approach runs at a near-constant
  speed, then spoilers and brakes bring it down at 2–4 kt/s. The first fix with a sustained
  deceleration past the threshold is the touchdown (or a second after it). The altitude
  trend *cannot* be used here — it holds near field elevation for the first ~2 km after
  touchdown, so it only serves as a lagging cross-check (`arr_alt_flat_m`).
- **Turn-off** is the point where the aircraft's centre crosses the runway edge
  (half-width + 10 m), measured against the **fitted** centreline, not the published one —
  at Entebbe the published line sits ~35 m off the line the fleet rolls on, which is more
  than half the runway width and would fire the test at touchdown. Where an aircraft brakes
  and then taxis back down the runway (Kilimanjaro 09 does this), the landing run is taken
  to end at the stop/turn-around point, not at the taxiway it later exits through.

### Take-off, by aircraft type

| type | flights | roll starts at | take-off run | runway used | runway left | runway in use |
|---|---|---|---|---|---|---|
| A330-800neo | 38 | 205 m | **2,224 m** (p10–p90 1,778–2,752) | 2,440 m | 1,104 m | 3,681 m |
| 737-800 | 94 | 160 m | **2,440 m** (p10–p90 2,056–3,539) | 2,673 m | 1,046 m | 3,681 m |
| CRJ900 | 348 | 109 m | **2,709 m** (p10–p90 2,115–3,332) | 2,816 m | 866 m | 3,681 m |

| type | flights | touchdown past threshold | landing roll | runway used | runway left | over the threshold at |
|---|---|---|---|---|---|---|
| A330-800neo | 23 | 356 m | **2,624 m** (p10–p90 2,412–2,850) | 2,946 m | 735 m | 148 kt |
| 737-800 | 97 | 384 m | **2,534 m** (p10–p90 1,782–2,860) | 2,936 m | 745 m | 151 kt |
| CRJ900 | 343 | 331 m | **2,490 m** (p10–p90 1,503–2,800) | 2,931 m | 750 m | 142 kt |

### Take-off, by airport (≥5 flights measured)

| airport | flights | measured at | roll | runway used | runway left | runway length | share used |
|---|---|---|---|---|---|---|---|
| Entebbe (HUEN) | 346 | 129 m past threshold | 2,619 m | 2,774 m | 906 m | 3,681 m | 75% |
| Nairobi (HKJK) | 70 | 106 m past threshold | 3,240 m | 3,351 m | 768 m | 4,119 m | 81% |
| Bujumbura (HBBA) | 28 | 95 m past threshold | 2,270 m | 2,418 m | 1,190 m | 3,608 m | 67% |
| Lusaka (FLLS) | 26 | 110 m past threshold | 2,574 m | 2,670 m | 1,272 m | 3,941 m | 68% |
| Johannesburg (FAOR) | 24 | 144 m past threshold | 3,530 m | 3,693 m | 702 m | 4,424 m | 83% |
| Juba (HJJJ) | 20 | -112 m past threshold | 1,952 m | 1,986 m | 418 m | 2,403 m | 83% |
| Mombasa (HKMO) | 16 | 98 m past threshold | 2,199 m | 2,285 m | 1,076 m | 3,361 m | 68% |
| Lagos (DNMM) | 16 | 688 m past threshold | 2,152 m | 2,840 m | 970 m | 3,921 m | 72% |
| London Gatwick (EGKK) | 14 | 255 m past threshold | 2,000 m | 2,174 m | 1,136 m | 3,310 m | 66% |
| Mumbai (VABB) | 6 | 214 m past threshold | 1,976 m | 2,201 m | 1,278 m | 3,479 m | 63% |
| Kigali (HRYR) | 5 | 140 m past threshold | 2,684 m | 2,887 m | 622 m | 3,509 m | 82% |

- A negative "roll starts at" (Juba 13) means the line-up point sits *before* the published
  threshold — the crew held at the displaced position, which is where line-up begins.
- 27 further take-offs have no usable lift-off signature (the export is too coarse), so
  they are left out of these tables; those rows carry the last sub-95 kt position instead,
  which under-reads. They are flagged in `dep_roll_source`.

### Landing, by airport (≥5 flights measured)

| airport | flights | measured at | roll | runway used | runway left | runway length | share used |
|---|---|---|---|---|---|---|---|
| Entebbe (HUEN) | 344 | 320 m past threshold | 2,633 m | 2,942 m | 738 m | 3,681 m | 80% |
| Nairobi (HKJK) | 71 | 536 m past threshold | 1,871 m | 2,296 m | 1,824 m | 4,119 m | 56% |
| Johannesburg (FAOR) | 34 | 552 m past threshold | 2,038 m | 2,649 m | 755 m | 3,404 m | 78% |
| Juba (HJJJ) | 28 | 236 m past threshold | 1,076 m | 1,476 m | 927 m | 2,403 m | 61% |
| Bujumbura (HBBA) | 28 | 370 m past threshold | 1,876 m | 2,204 m | 1,404 m | 3,608 m | 61% |
| Lusaka (FLLS) | 28 | 366 m past threshold | 2,364 m | 2,730 m | 1,210 m | 3,941 m | 69% |

### Per runway end (≥6 flights measured)

The same numbers split by the runway actually used — this is where the difference
between a 2,400 m strip and a 4,400 m one shows up.

| runway end | ops | take-off: run / used / left (% of runway) | landing: touchdown / roll / used / left |
|---|---|---|---|
| Entebbe (HUEN) 17 | 624 | 318 × 2,619 / 2,774 / 906 m (75%) | 306 × 324 / 2,621 / 2,942 / 739 m |
| Nairobi (HKJK) 06 | 141 | 70 × 3,240 / 3,351 / 768 m (81%) | 71 × 536 / 1,871 / 2,296 / 1,824 m |
| Entebbe (HUEN) 35 | 66 | 28 × 2,610 / 2,751 / 930 m (75%) | 38 × 288 / 2,793 / 3,074 / 607 m |
| Bujumbura (HBBA) 17 | 55 | 27 × 2,264 / 2,441 / 1,167 m (68%) | 28 × 370 / 1,876 / 2,204 / 1,404 m |
| Lusaka (FLLS) 10 | 54 | 26 × 2,574 / 2,670 / 1,272 m (68%) | 28 × 366 / 2,364 / 2,730 / 1,210 m |
| Juba (HJJJ) 13 | 39 | 18 × 1,952 / 1,922 / 482 m (80%) | 21 × 221 / 1,059 / 1,307 / 1,096 m |
| Johannesburg (FAOR) 03R | 25 | — | 25 × 511 / 2,093 / 2,649 / 755 m |
| Johannesburg (FAOR) 03L | 21 | 20 × 3,579 / 3,722 / 702 m (84%) | 1 × 662 / 1,548 / 2,210 / 2,214 m |
| Lagos (DNMM) 18R | 18 | 14 × 2,172 / 2,884 / 1,036 m (74%) | 4 × 1,211 / 1,286 / 2,496 / 1,426 m |
| Mombasa (HKMO) 21 | 16 | 16 × 2,199 / 2,285 / 1,076 m (68%) | — |
| London Gatwick (EGKK) 26L | 14 | 12 × 1,918 / 2,172 / 1,138 m (66%) | 2 × 600 / 2,000 / 2,600 / 710 m |
| Juba (HJJJ) 31 | 9 | 2 × 1,986 / 2,110 / 292 m (88%) | 7 × 270 / 1,931 / 2,201 / 202 m |
| Kilimanjaro (HTKJ) 09 | 6 | 4 × 2,508 / 2,607 / 992 m (72%) | 2 × 542 / 1,633 / 2,176 / 1,424 m |
| Johannesburg (FAOR) 21L | 6 | 1 × 2,623 / 2,762 / 641 m (81%) | 5 × 633 / 1,781 / 2,625 / 778 m |
| Mumbai (VABB) 27 | 6 | 6 × 1,976 / 2,201 / 1,278 m (63%) | — |
| Johannesburg (FAOR) 21R | 6 | 3 × 3,522 / 3,678 / 746 m (83%) | 3 × 402 / 2,370 / 3,497 / 927 m |

Across the whole dataset:

- take-off uses a median **75%** of the runway in use (p10–p90 62–87%); **35 of 585** take-offs used more than 90% of the pavement, and **21** had less than 300 m left in front of them
- landing uses a median **80%** (p10–p90 56–83%), and **23** landings ran to within 300 m of the far end (a taxiway exit, not
  necessarily a short runway)
- the median take-off run is **2,576 m** and the median landing roll **2,514 m**

| longest take-off runs | runway | run | used / length |
|---|---|---|---|
| UGD713 (ET-APL) 2026-09-07 | Johannesburg (FAOR) 03L | 4,017 m | 4,123 / 4,424 m |
| UGD713 (ET-APL) 2026-09-08 | Johannesburg (FAOR) 03L | 3,938 m | 4,086 / 4,424 m |
| UGD713 (ET-APL) 2026-09-09 | Johannesburg (FAOR) 03L | 3,915 m | 4,018 / 4,424 m |
| UGD713 (ET-APL) 2026-09-15 | Johannesburg (FAOR) 03L | 3,875 m | 3,963 / 4,424 m |
| UGD711 (—) 2026-03-21 | Johannesburg (FAOR) 03L | 3,789 m | 4,110 / 4,424 m |

| longest landing rolls | runway | roll | used / length |
|---|---|---|---|
| UR523 (—) — | Entebbe (HUEN) 35 | 6,160 m | 6,391 / 3,681 m |
| UGD521 (5X-EQU) 2026-09-04 | Entebbe (HUEN) 17 | 3,435 m | 3,653 / 3,681 m |
| UGD209 (5X-KDP) 2026-09-10 | Entebbe (HUEN) 17 | 3,386 m | 3,645 / 3,681 m |
| UGD722 (ET-APL) 2026-09-10 | Harare (FVHA) 05 | 3,369 m | 3,574 / 4,723 m |
| UGD201 (5X-EQU) 2026-09-25 | Entebbe (HUEN) 17 | 3,347 m | 3,645 / 3,681 m |

### How tightly is each moment pinned?

- **Wheels-off**: resolution = the export's fix interval. Median bracket **648 m** (p90 1,167 m), i.e. typically ±300 m on the along-runway figure. Sources: altitude × 580; speed fallback (below the altitude-valid speed) × 27; acceleration × 5.
- **Take-off capture**: full × 578; full / no wheel-off signature × 24; no stop captured (rolling take-off) × 7; no stop captured (rolling take-off) / no wheel-off signature × 3.
- **Touchdown**: median bracket **0 m** (p90 525 m) — the sharper of the two signals, since the deceleration onset is sampled directly.
- **Landing capture**: full × 484; full / track ends on the runway (roll is a lower bound) × 70; no deceleration captured (coarse export) × 7; no deceleration captured (coarse export) / track ends on the runway (roll is a lower bound) × 4.
- **74 landings are lower bounds**: the export ends while the aircraft is still on
  the runway, so the roll-out continues past the last fix. They are marked in
  `arr_roll_capture`.

## Where across the runway the wheels were

Measured against the centreline the fleet actually rolls on (see the fit table below),
signed + = right of the direction of travel.

| | flights | median | p90 | max | within 10 m | within 20 m |
|---|---|---|---|---|---|---|
| At lift-off (wheels leaving the runway) | 612 | 2 m | 8 m | 38 m | 95% | 99% |
| At touchdown | 565 | 2 m | 5 m | 275 m | 96% | 99% |

Touchdown is the tighter of the two: the aircraft has just flown an instrument approach,
so 96% of landings are within 10 m of the centreline.
At lift-off the aircraft has already been rolling for two to three kilometres and is
beginning to climb away, so the spread is wider (4 of
612 fixes sit more than 20 m off — the tail end of a long, fast roll).

| runway end | flights | roll fixes | fit residual | offset at threshold | offset at far end | rotation |
|---|---|---|---|---|---|---|
| Entebbe (HUEN) 17 | 626 | 6759 | 2.0 m | 0 m | 0 m | -0.0° |
| Nairobi (HKJK) 06 | 141 | 1678 | 1.8 m | -3 m | -1 m | 0.03° |
| Entebbe (HUEN) 35 | 66 | 1090 | 1.5 m | -1 m | -1 m | -0.0° |
| Bujumbura (HBBA) 17 | 55 | 608 | 1.6 m | 0 m | -4 m | -0.06° |
| Lusaka (FLLS) 10 | 54 | 560 | 2.2 m | 0 m | 1 m | 0.02° |
| Juba (HJJJ) 13 | 43 | 202 | 2.1 m | 4 m | 3 m | -0.04° |
| Johannesburg (FAOR) 03R | 26 | 398 | 19.9 m | 15 m | -38 m | -0.88° |
| Johannesburg (FAOR) 03L | 26 | 166 | 2.1 m | 9 m | -8 m | -0.21° |
| Harare (FVHA) 05 | 23 | 57 | 7.7 m | 2 m | -5 m | -0.08° |
| Lagos (DNMM) 18R | 20 | 136 | 7.6 m | 54 m | -15 m | -1.0° |
| Mombasa (HKMO) 21 | 16 | 186 | 2.0 m | -5 m | 5 m | 0.18° |
| London Gatwick (EGKK) 26L | 14 | 253 | 1.8 m | -1 m | 4 m | 0.08° |

23 runway ends have enough ground-roll fixes for a fit. Where there is none the
published line is used — that applies to the residual-deviation figures of
166 rows.

### Entebbe 17/35 — a corrected centreline, and why it matters

The runway coordinates published by OurAirports for Entebbe 17/35 run at **170.96°**;
the physical 46 m-wide strip runs at **172.10°**. Measured against the published line,
every flight appears to slide diagonally across the runway — starting **35 m** left of it
and finishing **38 m** right of it, i.e. off both edges of a runway that is only 46 m
wide. Nothing is wrong with the flying: the fleet's 3,006 ground-roll fixes fit a
straight line to within 2.1 m, and that line is corroborated independently by the runway
axis mapped from satellite imagery in OpenStreetMap, which agrees with it to **1.8 m**.

**This is now corrected in the data, not just in the arithmetic.** The reviewed line is
stored in `work/rwy/centreline_fixes.csv` and loaded as the reference by the pipeline, so
every measurement in this document — and in any future run, before any fitting happens —
is taken against the corrected line. Three sources agree on it:

| source | 17/35 heading | offset vs the published line (17 end → 35 end) |
|---|---|---|
| OurAirports (original reference) | 170.96° | 0 m by definition |
| fleet: 3,006 ground-roll fixes | 172.10° | −35.0 m → +38.0 m |
| OpenStreetMap, mapped from imagery | 172.10° | −33.5 m → +39.7 m |

Against the corrected line the same fixes read: mean offset **−0.6 m**, standard
deviation **1.2 m** (rolling fixes ≥ 55 kt). Against one that is a half-width out it is
not a cosmetic difference — the arrival roll-out is cut where the aircraft crosses the
runway edge (half-width + 10 m), so the old line fired that test at touchdown and
reported a zero-length landing roll for 15 Entebbe arrivals. With the corrected line,
none of the 159 Entebbe landings measured this run comes out shorter than 400 m.

The before/after picture is `entebbe_centreline.png`; the derivation and the
corroboration for each corrected line is recorded in the `evidence` column of the fixes
file. The other 18 fitted runway ends sit within a few metres of their published lines
and are left on the published coordinates — the fit is still used for their lateral
figures, but no correction is applied to the reference data.

**Three independent checks agree with each other and differ from the published line:**

1. every flight would have to have made the same 1.1° steering error, for 13 days, in
   the same direction, on both the 17 and the 35 rolls — implausible on its face;
2. the ground-track direction computed from the fixes with plain plane geometry
   (no shared code, no per-runway constants) gives 172.1° for the fleet against the
   published 171.0°;
3. the runway axis mapped in OpenStreetMap from satellite imagery runs at 172.10°,
   i.e. within a few tens of centimetres of the fleet line — see
   `entebbe_centreline.png`.

A related trap, for the record: the OurAirports **heading** field is rounded to whole
degrees — Entebbe 17 is filed as `171`, against a coordinate axis of 170.96° and a
physical axis of 172.10°. A degree is ~64 m of lateral drift over a 3,680 m runway, so
all geometry here is computed from the coordinate pairs, never from that heading field.

## Reading the CSV

| column | meaning |
|---|---|
| `file` | track file in the zip — the flight number is the prefix |
| `flight / tail / when` | flight number, airframe from your screenshots (blank when not pinned), scheduled departure (local) |
| `log_origin / log_dest` | airports as labelled by the log builder — metadata; can disagree with the geometry outside September |
| `dep_apt / arr_apt (+ `_dist_km`, `_ground`)` | nearest airport with a 4,000 ft+ runway to the first/last ground-ish fix; `_ground` = yes when a real ground fix was found there |
| `dep_rwy / arr_rwy` | runway end used, e.g. `17` or `03R` |
| `dep_conf / arr_conf` | high / medium / low — see Coverage |
| `dep_method / arr_method` | `roll` (measured from the ground roll) or climb-/approach-heading (inferred) |
| `dep_xt / arr_xt (+ `_rival_xt`, `_margin`)` | mean distance from the centreline over the matched roll, the same for the nearest *other* runway end, and the score gap to it |
| `dep_day_dir / arr_day_dir` | match when the flight agrees with the day's dominant direction at that airport |
| `dep_rwy_len_m / dep_rwy_width_m` | runway length and width in use (OurAirports) |
| `dep_roll_start_m / dep_roll_start_speed_kt` | line-up point and the speed there — the take-off run starts here |
| `dep_runway_used_m` | **distance down the runway at wheels-off** — the headline take-off figure |
| `dep_roll_len_m` | take-off run actually used (wheels-off minus roll start) |
| `dep_rwy_remaining_m` | pavement left ahead at wheels-off |
| `dep_liftoff_along_lo / _hi / _bracket_m` | the two fixes that bracket the lift-off, and the gap between them (the resolution) |
| `dep_liftoff_speed_kt` | groundspeed at the first airborne fix |
| `dep_roll_source` | which signature found the lift-off: altitude (direct) / acceleration / speed fallback |
| `dep_accel_alt_ft` | height at which the acceleration second-opinion fired |
| `dep_roll_capture` | full = a standstill (or sub-15 kt taxi) was captured before the roll; otherwise the roll started before the export |
| `dep_liftoff_xt_m / dep_liftoff_xt_cal_m` | lateral offset from the published / fitted centreline at wheels-off (+ = right) |
| `arr_thr_speed_kt / arr_thr_height_ft` | interpolated speed and height over the threshold |
| `arr_td_along_m (+ `_lo`, `_hi`, `_bracket_m`)` | **touchdown distance past the threshold** and the bracket around it |
| `arr_td_speed_kt` | groundspeed at touchdown |
| `arr_alt_flat_m` | where the altitude trace flattens — a lagging cross-check on the touchdown |
| `arr_roll_len_m` | landing roll: touchdown → leaving the pavement (or stopping on it) |
| `arr_runway_used_m` | **how far down the runway the landing run ended** — the headline landing figure |
| `arr_rwy_remaining_m` | pavement left beyond that point |
| `arr_turnoff_speed_kt` | groundspeed when the aircraft left the centreline corridor |
| `arr_stop_along_m` | where it came to a stop, when it stopped rather than rolling off |
| `arr_roll_capture` | full, or track-ends-on-the-runway (roll is a lower bound) |
| `arr_td_xt_m / arr_td_xt_cal_m` | lateral offset from the published / fitted centreline at touchdown |

## Caveats

- **37 departures and 31 arrivals stay blank.** Either the export starts after the rotation or stops before the landing, or the only ground fix is a single sparse sample.
  Departure blanks: Mogadishu (HCMM) × 17, (no airport) × 11, Shaqra (OESB) × 2, Harare (FVHA) × 2, Entebbe (HUEN) × 1, Butembo (FZKA) × 1, Nairobi (HKJK) × 1, Kilimanjaro (HTKJ) × 1, Windhoek (FYWH) × 1.
  Arrival blanks: Mogadishu (HCMM) × 15, (no airport) × 10, Entebbe (HUEN) × 2, Doha (OTHH) × 1, Constantine (DABC) × 1, Windhoek (FYWH) × 1, Harare (FVHA) × 1.
  A finer export (or the full track history) is the only way to recover those.
- **"Wheels-off" is not the rotation.** The nose lifts before the wheels leave, and the
  export only samples every few seconds, so `dep_runway_used_m` carries the bracket above
  (median ±300 m along the runway). The lateral figure barely moves over that distance.
- **Coarse exports.** A handful of tracks are sampled at 30 s or more; there the roll
  start, the lift-off bracket and the landing roll are all widened, and the rows are
  flagged in `*_roll_source` / `*_roll_capture`. 74 landings are marked as lower bounds.
- **Displaced thresholds.** Touchdown is measured past the *published* threshold, which
  for a displaced threshold includes the displaced part — Los Angeles-style, the runway
  available for landing is shorter than the length quoted here. Lagos 18R (touchdowns
  ~1.2 km) and Sao Paulo / Nairobi (0.5 km) reflect displaced-threshold layouts as much as
  crew technique.
- **Back-tracking arrivals** (Kilimanjaro 09, some Juba 13) brake, then taxi back along
  the runway; those rows are cut at the stop/turn-around point rather than at the later
  taxiway exit, which is the best that can be done from position data alone.
- **Runway exits are not subtracted** from `*_rwy_remaining_m`: they report pavement left
  in front of the aircraft, not pavement available for a further landing.
- **The fitted centreline assumes the fleet, on average, rolls down the centre.** If every
  crew habitually sat, say, 5 m left, that would be baked in as "zero". The fit residual
  (2–3 m at the busiest airports) bounds how precisely it is pinned, not whether the
  absolute offset from the painted centreline is zero.
- **No wind, weight or derate information exists in these exports**, so nothing here says
  *why* a roll was long or short — only how long it was. Nothing here says *why* a runway
  was chosen either (wind, noise abatement, availability): only which one was used.
- Verdicts come from position data alone: the exports have no runway, weight, or
  registration field.

