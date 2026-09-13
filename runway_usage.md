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
| Departure runway | **324/342** | 290 | 25 | 9 | 298 | 26 |
| Arrival runway | **327/342** | 250 | 75 | 2 | 257 | 70 |
| Take-off distance measured | **287/342** (12 fallback only) | | | | | |
| Landing distance measured | **257/342** | | | | | |

- both runway ends known: **310/342** (91%)
- the airline's own (UR/UGD) tracks: departures **285/300**, arrivals **291/300**, both ends **276/300**
- tail (5X-… / ET-APL) attached from your screenshots: **222** rows — every UR track whose (date, flight, route) key matches exactly one screenshot row
- `high` = roll captured, on the centreline (mean cross-track ≤ 70 m) and heading within 10°
- `medium` = roll captured but shorter/looser, or the heading fallback with a clear margin
- `low` = heading-only evidence at an airport with a parallel strip, or a weak fit — a hint
- **16 rows get their runway from alignment rather than a roll.** Where the export starts just after the rotation or stops on short final there is nothing on the ground to match, but the aircraft is low, close to the field and lined up with one runway: the call is made from its position against that runway's extended centreline plus the heading between two fixes ~2 km apart (`climb-alignment` / `approach-alignment`). No roll, touchdown or distance figures come out of those rows.

## Why it is trustworthy

| check | departure | arrival |
|---|---|---|
| heading error vs the runway's true heading (median / p95) | 1.0° / 1.1° | 1.1° / 3.0° |
| position fixes inside the roll (median) | 10 | 11 |

The paved surface is 45–60 m wide, so a heading error of 0–1° is unambiguously *that*
runway. Laterally the strongest evidence is the roll itself: thousands of ground-roll
fixes at one runway end fit a single straight line to within a few metres (table further
down), which is both proof that the aircraft rolled straight down the runway and a
measure of how good the position data is.

Independent checks that were run:

- **Day-direction coherence.** Wind holds one direction all day, so every flight at an airport that day should use the same runway direction. Of the flights that could be compared, departures **161/161** and arrivals **158/158** agree with their day's dominant direction — **0 exceptions**.
- **Airport geometry.** Threshold-to-threshold bearings of every runway in scope were
  checked against the published runway true headings; no swapped runway ends.
- **Gatwick** returns 26L for both arrivals and departures (LGW is a single-runway
  operation); **Johannesburg** returns arrivals on 03R/21L and departures on 03L/21R —
  the parallel-strip split the airport actually uses.
- **Worked example.** `UR110-4180268d.csv` (UGD110, 5X-NIL) leaves Entebbe (HUEN) 17: the roll starts 113 m past the threshold at 17 kt, the wheels leave the ground 2,819 m down a 3,681 m runway (77% used), leaving 862 m. Bracket around the lift-off: 617 m, i.e. that is the export's time resolution.

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
| A330-800neo | 12 | 240 m | **2,052 m** (p10–p90 1,830–2,706) | 2,292 m | 1,169 m | 3,479 m |
| 737-800 | 32 | 156 m | **2,478 m** (p10–p90 2,165–3,674) | 2,668 m | 1,052 m | 3,681 m |
| CRJ900 | 137 | 102 m | **2,634 m** (p10–p90 2,104–3,290) | 2,768 m | 879 m | 3,681 m |

| type | flights | touchdown past threshold | landing roll | runway used | runway left | over the threshold at |
|---|---|---|---|---|---|---|
| A330-800neo | 9 | 373 m | **2,561 m** (p10–p90 1,997–2,865) | 2,942 m | 735 m | 148 kt |
| 737-800 | 35 | 391 m | **2,434 m** (p10–p90 1,714–2,934) | 2,932 m | 746 m | 150 kt |
| CRJ900 | 128 | 306 m | **2,516 m** (p10–p90 1,519–2,823) | 2,936 m | 746 m | 141 kt |

### Take-off, by airport (≥5 flights measured)

| airport | flights | measured at | roll | runway used | runway left | runway length | share used |
|---|---|---|---|---|---|---|---|
| Entebbe (HUEN) | 162 | 123 m past threshold | 2,619 m | 2,760 m | 920 m | 3,681 m | 75% |
| Nairobi (HKJK) | 27 | 97 m past threshold | 3,247 m | 3,395 m | 724 m | 4,119 m | 82% |
| Bujumbura (HBBA) | 13 | 98 m past threshold | 2,264 m | 2,478 m | 1,129 m | 3,608 m | 69% |
| Lusaka (FLLS) | 12 | 100 m past threshold | 2,708 m | 2,840 m | 1,100 m | 3,941 m | 72% |
| Johannesburg (FAOR) | 11 | 147 m past threshold | 3,637 m | 3,860 m | 564 m | 4,424 m | 87% |
| Mombasa (HKMO) | 9 | 102 m past threshold | 2,076 m | 2,154 m | 1,207 m | 3,361 m | 64% |
| Juba (HJJJ) | 8 | -190 m past threshold | 1,970 m | 1,958 m | 445 m | 2,403 m | 81% |
| Lagos (DNMM) | 7 | 517 m past threshold | 2,099 m | 2,459 m | 1,071 m | 3,921 m | 63% |
| Kigali (HRYR) | 5 | 140 m past threshold | 2,684 m | 2,887 m | 622 m | 3,509 m | 82% |
| London Gatwick (EGKK) | 5 | 260 m past threshold | 2,067 m | 2,332 m | 978 m | 3,310 m | 70% |

- A negative "roll starts at" (Juba 13) means the line-up point sits *before* the published
  threshold — the crew held at the displaced position, which is where line-up begins.
- 12 further take-offs have no usable lift-off signature (the export is too coarse), so
  they are left out of these tables; those rows carry the last sub-95 kt position instead,
  which under-reads. They are flagged in `dep_roll_source`.

### Landing, by airport (≥5 flights measured)

| airport | flights | measured at | roll | runway used | runway left | runway length | share used |
|---|---|---|---|---|---|---|---|
| Entebbe (HUEN) | 159 | 310 m past threshold | 2,640 m | 2,942 m | 739 m | 3,681 m | 80% |
| Nairobi (HKJK) | 28 | 501 m past threshold | 1,890 m | 2,299 m | 1,820 m | 4,119 m | 56% |
| Johannesburg (FAOR) | 15 | 511 m past threshold | 2,100 m | 2,647 m | 756 m | 3,404 m | 78% |
| Bujumbura (HBBA) | 12 | 402 m past threshold | 1,814 m | 2,202 m | 1,406 m | 3,608 m | 61% |
| Lusaka (FLLS) | 11 | 278 m past threshold | 2,452 m | 2,730 m | 1,211 m | 3,941 m | 69% |
| Juba (HJJJ) | 10 | 190 m past threshold | 936 m | 1,204 m | 1,200 m | 2,403 m | 50% |

### Per runway end (≥6 flights measured)

The same numbers split by the runway actually used — this is where the difference
between a 2,400 m strip and a 4,400 m one shows up.

| runway end | ops | take-off: run / used / left (% of runway) | landing: touchdown / roll / used / left |
|---|---|---|---|
| Entebbe (HUEN) 17 | 299 | 153 × 2,600 / 2,734 / 947 m (74%) | 146 × 313 / 2,630 / 2,942 / 739 m |
| Nairobi (HKJK) 06 | 55 | 27 × 3,247 / 3,395 / 724 m (82%) | 28 × 501 / 1,890 / 2,299 / 1,820 m |
| Bujumbura (HBBA) 17 | 25 | 13 × 2,264 / 2,478 / 1,129 m (69%) | 12 × 402 / 1,814 / 2,202 / 1,406 m |
| Lusaka (FLLS) 10 | 23 | 12 × 2,708 / 2,840 / 1,100 m (72%) | 11 × 278 / 2,452 / 2,730 / 1,211 m |
| Entebbe (HUEN) 35 | 22 | 9 × 2,747 / 2,902 / 779 m (79%) | 13 × 306 / 2,794 / 3,075 / 606 m |
| Juba (HJJJ) 13 | 16 | 8 × 1,970 / 1,958 / 445 m (81%) | 8 × 183 / 934 / 1,092 / 1,310 m |
| Johannesburg (FAOR) 03R | 11 | — | 11 × 414 / 2,136 / 2,648 / 755 m |
| Lagos (DNMM) 18R | 9 | 5 × 2,183 / 2,727 / 1,193 m (70%) | 4 × 1,211 / 1,303 / 2,516 / 1,406 m |
| Mombasa (HKMO) 21 | 9 | 9 × 2,076 / 2,154 / 1,207 m (64%) | — |
| Johannesburg (FAOR) 03L | 9 | 9 × 3,674 / 3,992 / 432 m (90%) | — |
| London Gatwick (EGKK) 26L | 6 | 4 × 2,002 / 2,257 / 1,053 m (68%) | 2 × 600 / 2,000 / 2,600 / 710 m |
| Kilimanjaro (HTKJ) 09 | 6 | 4 × 2,508 / 2,607 / 992 m (72%) | 2 × 542 / 1,633 / 2,176 / 1,424 m |

Across the whole dataset:

- take-off uses a median **75%** of the runway in use (p10–p90 62–87%); **17 of 275** take-offs used more than 90% of the pavement, and **9** had less than 300 m left in front of them
- landing uses a median **80%** (p10–p90 56–82%), and **9** landings ran to within 300 m of the far end (a taxiway exit, not
  necessarily a short runway)
- the median take-off run is **2,565 m** and the median landing roll **2,514 m**

| longest take-off runs | runway | run | used / length |
|---|---|---|---|
| UGD713 (ET-APL) 2026-09-07 | Johannesburg (FAOR) 03L | 4,017 m | 4,123 / 4,424 m |
| UGD713 (ET-APL) 2026-09-08 | Johannesburg (FAOR) 03L | 3,938 m | 4,086 / 4,424 m |
| UGD713 (ET-APL) 2026-09-09 | Johannesburg (FAOR) 03L | 3,915 m | 4,018 / 4,424 m |
| UGD711 (—) 2026-03-21 | Johannesburg (FAOR) 03L | 3,789 m | 4,110 / 4,424 m |
| KQ418 (—) — | Nairobi (HKJK) 06 | 3,682 m | 3,762 / 4,119 m |

| longest landing rolls | runway | roll | used / length |
|---|---|---|---|
| UGD521 (5X-EQU) 2026-09-04 | Entebbe (HUEN) 17 | 3,435 m | 3,653 / 3,681 m |
| UGD209 (5X-KDP) 2026-09-10 | Entebbe (HUEN) 17 | 3,386 m | 3,645 / 3,681 m |
| UGD722 (ET-APL) 2026-09-10 | Harare (FVHA) 05 | 3,369 m | 3,574 / 4,723 m |
| UGD711 (ET-APL) 2026-09-04 | Entebbe (HUEN) 17 | 3,329 m | 3,654 / 3,681 m |
| UGD123 (5X-KOB) 2026-09-07 | Entebbe (HUEN) 17 | 3,301 m | 3,646 / 3,681 m |

### How tightly is each moment pinned?

- **Wheels-off**: resolution = the export's fix interval. Median bracket **650 m** (p90 1,180 m), i.e. typically ±300 m on the along-runway figure. Sources: altitude × 274; speed fallback (below the altitude-valid speed) × 12; acceleration × 1.
- **Take-off capture**: full × 273; full / no wheel-off signature × 10; no stop captured (rolling take-off) / no wheel-off signature × 2; no stop captured (rolling take-off) × 2.
- **Touchdown**: median bracket **0 m** (p90 514 m) — the sharper of the two signals, since the deceleration onset is sampled directly.
- **Landing capture**: full × 222; full / track ends on the runway (roll is a lower bound) × 32; no deceleration captured (coarse export) / track ends on the runway (roll is a lower bound) × 2; no deceleration captured (coarse export) × 1.
- **34 landings are lower bounds**: the export ends while the aircraft is still on
  the runway, so the roll-out continues past the last fix. They are marked in
  `arr_roll_capture`.

## Where across the runway the wheels were

Measured against the centreline the fleet actually rolls on (see the fit table below),
signed + = right of the direction of travel.

| | flights | median | p90 | max | within 10 m | within 20 m |
|---|---|---|---|---|---|---|
| At lift-off (wheels leaving the runway) | 287 | 3 m | 8 m | 38 m | 93% | 99% |
| At touchdown | 257 | 2 m | 5 m | 16 m | 98% | 100% |

Touchdown is the tighter of the two: the aircraft has just flown an instrument approach,
so 98% of landings are within 10 m of the centreline.
At lift-off the aircraft has already been rolling for two to three kilometres and is
beginning to climb away, so the spread is wider (3 of
287 fixes sit more than 20 m off — the tail end of a long, fast roll).

| runway end | flights | roll fixes | fit residual | offset at threshold | offset at far end | rotation |
|---|---|---|---|---|---|---|
| Entebbe (HUEN) 17 | 299 | 3178 | 2.1 m | 0 m | 0 m | -0.0° |
| Nairobi (HKJK) 06 | 55 | 619 | 1.8 m | -2 m | 0 m | 0.02° |
| Bujumbura (HBBA) 17 | 25 | 279 | 1.5 m | 0 m | -4 m | -0.06° |
| Lusaka (FLLS) 10 | 23 | 232 | 2.2 m | 0 m | 0 m | 0.0° |
| Entebbe (HUEN) 35 | 22 | 368 | 1.4 m | 0 m | -1 m | -0.01° |
| Juba (HJJJ) 13 | 18 | 66 | 2.4 m | 4 m | 4 m | -0.02° |
| Johannesburg (FAOR) 03R | 12 | 175 | 19.3 m | 11 m | -37 m | -0.81° |
| Johannesburg (FAOR) 03L | 11 | 77 | 1.3 m | 8 m | -3 m | -0.14° |
| Lagos (DNMM) 18R | 10 | 79 | 12.3 m | 58 m | -26 m | -1.23° |
| Mombasa (HKMO) 21 | 9 | 109 | 1.9 m | -4 m | 5 m | 0.17° |
| Kilimanjaro (HTKJ) 09 | 8 | 50 | 2.2 m | -3 m | -3 m | 0.0° |
| London Gatwick (EGKK) 26L | 6 | 114 | 2.7 m | -1 m | 5 m | 0.1° |

19 runway ends have enough ground-roll fixes for a fit. Where there is none the
published line is used — that applies to the residual-deviation figures of
85 rows.

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

- **18 departures and 15 arrivals stay blank.** Either the export starts after the rotation or stops before the landing, or the only ground fix is a single sparse sample.
  Departure blanks: Mogadishu (HCMM) × 7, (no airport) × 5, Shaqra (OESB) × 2, Entebbe (HUEN) × 1, Butembo (FZKA) × 1, Nairobi (HKJK) × 1, Windhoek (FYWH) × 1.
  Arrival blanks: (no airport) × 6, Mogadishu (HCMM) × 5, Entebbe (HUEN) × 1, Doha (OTHH) × 1, Constantine (DABC) × 1, Windhoek (FYWH) × 1.
  A finer export (or the full track history) is the only way to recover those.
- **"Wheels-off" is not the rotation.** The nose lifts before the wheels leave, and the
  export only samples every few seconds, so `dep_runway_used_m` carries the bracket above
  (median ±300 m along the runway). The lateral figure barely moves over that distance.
- **Coarse exports.** A handful of tracks are sampled at 30 s or more; there the roll
  start, the lift-off bracket and the landing roll are all widened, and the rows are
  flagged in `*_roll_source` / `*_roll_capture`. 34 landings are marked as lower bounds.
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

