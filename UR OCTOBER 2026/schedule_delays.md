# Delays against the published schedule — 02–09 October 2026

201 legs · 41 flight numbers · 8 days. Per-leg numbers: `schedule_delays.csv`.

This is the first timetable the repository has held, so for the first time a delay is **observed minus published** — and for the first time there is an arrival delay at all, since the app screenshots and the ADS-B log only ever fix a departure. The two measures disagree in a useful direction: `punctuality.csv` scores a service against its own habit, so a flight that always leaves 40 minutes late scores zero. Where this table and that one part company, it is the schedule being reported on, not the aircraft.

## Three properties of the file that change the answer

1. **Status times are UTC; schedule times are local.** `UR209 NBO→EBB` is due at 01:30 Entebbe time and reads `Landed 22:10` — 22:10Z the previous evening, i.e. 01:10 local, **twenty minutes early**, not 23 h 40 min late. Every status is snapped to the day nearest the scheduled instant it belongs to.
2. **The file runs East Africa on a single clock.** Offsets are not assumed: each row carries a `block`, which fixes the difference between its two airports, so the table below is voted across the week with Entebbe pinned at +0300:

   `BJM` +0200 · `BOM` +0530 · `DAR` +0300 · `DXB` +0400 · `EBB` +0300 · `FIH` +0100 · `HRE` +0200 · `JNB` +0200 · `JRO` +0300 · `JUB` +0200 · `LGW` +0100 · `LOS` +0100 · `LUN` +0200 · `MBA` +0300 · `MGQ` +0300 · `NBO` +0300 · `ZNZ` +0300

   **DAR**, **JRO**, **ZNZ** come out at +0300 while those airports’ own wall clocks run +0200. That is a display convention rather than an error — but reading the column at the wall clock invents an hour, which is exactly how two Kilimanjaro arrivals came to look 80 minutes early on a first pass.

   A `block` is a difference, so it cannot settle which clock is meant; the archive can. Across **17 legs** into DAR, JRO, ZNZ that the log also holds, the scheduled arrival sits a median of **+14 min** from a real landing on the file’s clock, and -46 min on the airport’s own. So the **file** reading is the exporter’s, and it is what this table uses.

3. **15 legs carry a status, 8 more had departed without one.** The snapshot was cut at 18:35Z on 02 Oct: everything later reads `not yet flown` — no data is expected for those, so they are not gaps — while 8 were already airborne with nothing from the feed.

## What actually happened

| date | flight | sector | scheduled arrival | landed | delay | reads as |
|---|---|---|---|---|---|---|
| 2026-10-02 | UR209 | NBO→EBB | 2026-10-01 22:30Z | 2026-10-01 22:10Z | -20 min | early |
| 2026-10-02 | UR323 | DAR→EBB | 2026-10-01 23:40Z | 2026-10-01 22:54Z | -46 min | early |
| 2026-10-02 | UR903 | LOS→EBB | 2026-10-02 05:30Z | 2026-10-02 05:45Z | +15 min | late |
| 2026-10-02 | UR713 | JNB→EBB | 2026-10-02 05:15Z | 2026-10-02 04:39Z | -36 min | early |
| 2026-10-02 | UR520 | EBB→MGQ | 2026-10-02 04:30Z | 2026-10-02 04:24Z | -6 min | on time |
| 2026-10-02 | UR200 | EBB→NBO | 2026-10-02 06:15Z | 2026-10-02 05:41Z | -34 min | early |
| 2026-10-02 | UR521 | MGQ→EBB | 2026-10-02 08:00Z | 2026-10-02 07:44Z | -16 min | early |
| 2026-10-02 | UR334 | EBB→ZNZ | 2026-10-02 08:05Z | 2026-10-02 07:51Z | -14 min | on time · *clock* |
| 2026-10-02 | UR710 | EBB→JNB | 2026-10-02 10:45Z | 2026-10-02 11:10Z | +25 min | late |
| 2026-10-02 | UR201 | NBO→EBB | 2026-10-02 08:30Z | 2026-10-02 08:00Z | -30 min | early |
| 2026-10-02 | UR334 | ZNZ→JRO | 2026-10-02 10:05Z | 2026-10-02 09:30Z | -35 min | early · *clock* |
| 2026-10-02 | UR120 | EBB→JUB | 2026-10-02 12:25Z | 2026-10-02 12:12Z | -13 min | on time |
| 2026-10-02 | UR334 | JRO→EBB | 2026-10-02 12:20Z | 2026-10-02 11:41Z | -39 min | early |

**3 of 13 inside the ±15 min on-time window**, 2 late, 8 early. Median -20 min, range -46 to +25 min.

Best and worst: **UR323 DAR→EBB** at -46 min, **UR710 EBB→JNB** at +25 min. The pattern is the one the app dots could only hint at, and the blocks now explain: short East African sectors arrive early — they are blocked generously — and the lateness lives on the long sectors, where the hours are in the air and not on the ground.

In the air when the file was cut, so these are forecasts and not delays:

* 2026-10-02 **UR110** EBB→LGW: scheduled 2026-10-02 16:40Z, FR24 estimates 2026-10-02 16:33Z → -7 min at arrival.
* 2026-10-02 **UR111** LGW→EBB: scheduled 2026-10-02 18:35Z, FR24 estimates 2026-10-02 18:35Z → +0 min at take-off.

## Gone before the cut-off with no status (8)

These had departed — the file carries observations from later in the same day — and the weekly view had nothing for them. They are unmeasurable from this file, which says something about the export and nothing about the operation; the daily export and the app screenshots are what fill them in:

* 2026-10-02 UR711 JNB→EBB, scheduled departure 2026-10-02 11:45Z
* 2026-10-02 UR121 JUB→EBB, scheduled departure 2026-10-02 13:25Z
* 2026-10-02 UR360 EBB→BJM, scheduled departure 2026-10-02 13:30Z
* 2026-10-02 UR206 EBB→NBO, scheduled departure 2026-10-02 14:40Z
* 2026-10-02 UR361 BJM→EBB, scheduled departure 2026-10-02 15:45Z
* 2026-10-02 UR342 EBB→MBA, scheduled departure 2026-10-02 15:50Z
* 2026-10-02 UR207 NBO→EBB, scheduled departure 2026-10-02 16:55Z
* 2026-10-02 UR720 EBB→LUN, scheduled departure 2026-10-02 18:00Z

## What the schedule says about the rest of the week

Every leg is joined to the service it repeats — flight number and sector, matched through the callsign form the log uses (`UGD209` for `UR209`) — and against what this build has measured for that service: 41 services have three or more logged legs to compare with. Two columns come out of that, and neither is a delay:

* **`sched_vs_op_min`** — scheduled departure against the median time the service actually left. Negative means the timetable is earlier than the operation: that leg is written to be missed, every day.
* **`block_slack_min`** — scheduled block against the median block actually flown, measured ground-to-ground out of the archive's own tracks (first fix to last, which is on the ground at both ends in 248 and 233 of the first 250 legs). Negative means the schedule asks for less time than the aircraft needs: the sector is late by construction, and the delay arrives on the next one.

The services scheduled tighter than they fly, worst first:

| service | legs this week | worst shortfall | median flown | baseline legs |
|---|---|---|---|---|
| UR901 LOS→EBB | 2 | -22 min | 292.5 min | 8 |
| UR903 LOS→EBB | 3 | -11 min | 281.4 min | 10 |
| UR902 EBB→LOS | 3 | -11 min | 281.0 min | 10 |
| UR430 EBB→BOM | 2 | -10 min | 399.8 min | 10 |
| UR710 EBB→JNB | 5 | -3 min | 258.3 min | 17 |
| UR110 EBB→LGW | 4 | -3 min | 522.9 min | 15 |
| UR900 EBB→LOS | 2 | -2 min | 272.3 min | 7 |
| UR712 EBB→JNB | 4 | -2 min | 255.7 min | 16 |
| UR722 HRE→LUN | 4 | -1 min | 60.8 min | 16 |


### Where the week’s time is hiding

Across the 182 legs with a flown baseline, the scheduled block sits a median **+16.0 min** above the block the fleet actually spends (range -22.5 to +30.2 min). Read one way that is a padded timetable; read the other way, 29 legs in 9 services are blocked at or below the hours they take, and those are the ones that will run late:

| service | legs this week | worst shortfall | median flown | baseline legs |
|---|---|---|---|---|
| UR901 LOS→EBB | 2 | -22.5 min | 292.5 min | 8 |
| UR903 LOS→EBB | 3 | -11.4 min | 281.4 min | 10 |
| UR902 EBB→LOS | 3 | -11.0 min | 281.0 min | 10 |
| UR430 EBB→BOM | 2 | -9.8 min | 399.8 min | 10 |
| UR710 EBB→JNB | 5 | -3.3 min | 258.3 min | 17 |
| UR110 EBB→LGW | 4 | -2.9 min | 522.9 min | 15 |
| UR900 EBB→LOS | 2 | -2.3 min | 272.3 min | 7 |
| UR712 EBB→JNB | 4 | -1.7 min | 255.7 min | 16 |
| UR722 HRE→LUN | 4 | -0.8 min | 60.8 min | 16 |

Two things about that list are worth more than the numbers. It is made of long sectors — Lagos, Johannesburg, Mumbai, London — where an hour is a rounding error and the padding cannot be recovered; and the padding that does exist is all on the short East African sectors, where 15 free minutes in a 75-minute block is how a 78-seat CRJ-900 keeps a timetable it could not otherwise keep.

The 13 measured arrivals say the same thing from the other side:

* **UR710 EBB→JNB** arrived +25 min on a sector with -3.3 min of slack.
* **UR903 LOS→EBB** arrived +15 min on a sector with -11.4 min of slack.
* **UR520 EBB→MGQ** arrived -6 min on a sector with 20.0 min of slack.
* **UR120 EBB→JUB** arrived -13 min on a sector with 25.2 min of slack.
* **UR334 EBB→ZNZ** arrived -14 min on a sector with 18.4 min of slack.
* **UR521 MGQ→EBB** arrived -16 min on a sector with 19.1 min of slack.
* **UR209 NBO→EBB** arrived -20 min on a sector with 10.2 min of slack.
* **UR201 NBO→EBB** arrived -30 min on a sector with 19.7 min of slack.
* **UR200 EBB→NBO** arrived -34 min on a sector with 20.9 min of slack.
* **UR334 ZNZ→JRO** arrived -35 min on a sector with 12.8 min of slack.
* **UR713 JNB→EBB** arrived -36 min on a sector with 5.6 min of slack.
* **UR334 JRO→EBB** arrived -39 min on a sector with 10.3 min of slack.
* **UR323 DAR→EBB** arrived -46 min on a sector with 15.8 min of slack.

Every late arrival in the file sits on a sector with **negative** slack, and the eleven that came early or on time sit on sectors with +4 to +26 min of it. With thirteen data points that is not proof of anything, but it is the first time this project has had a reason for a late flight rather than a measurement of one.

On the departure clock the schedule is closer to the habit than the blocks are: median -4 min over 175 legs. 56 legs are scheduled after the time their service usually leaves (median +8 min of slack to bank) and 110 before it (median -9 min) — and the second group is where the operation is quietly chronic.

The largest of them: **UR722 HRE→LUN** is scheduled to leave 14:45 local (2026-10-07 12:45Z), and across 16 logged legs that service has left at a median of **14:04Z** — 80 min later than the plan, with a scatter of 22 min around it. The airline is not late at that station by accident; it is late by timetable, which is a different problem and looks like none in a table that scores each flight against its own habit.

Not the whole service, either: the 4 legs of it in this week run from -80 to -4 min against that median, so what is mis-timed is a day of the week, not a route. That distinction is only visible with a timetable; against a month of habit, all of these legs are equally normal.

7 legs were left out of that comparison altogether: their service sits more than three hours away from the time it kept in the archive month, which is a re-timed season, not a late flight. A number of that size is not a measurement, and the honest move is to withhold it rather than explain it.

One caveat on the block baseline. A track window is only a block where the track starts and ends on the ground, which it does for 248 and 233 of the first 250 legs sampled; the rest lose some taxi, so a shortfall of a minute or two on those is inside the measurement. The `air_minutes` counterpart is in the CSV as `op_median_air_min` — the airborne part only, which is what `air_minutes` in the archive log means — and it sits a median 5.8 min below the window over the 182 comparable legs.

48 legs sit 20 minutes or more away from the time their service actually leaves. That is the honest definition of a structurally late flight, and it is a number the median-based `punctuality.csv` cannot produce at all: measured against itself, a habit is invisible.

## What this file cannot answer

* **Which aircraft flew what.** There is no registration column, so a flight number cannot be chained into a rotation — and without rotations there is no propagation: this table can say UR710 arrived 25 minutes late, not what that cost the UR711 that was to follow it. The daily export has the tail, and `tails.csv` already carries the claims, so the question is answerable as soon as the tail column is added to this export.
* **The other 178 legs.** Only 2 October has statuses; 03–09 October in this file is the forward plan, not a record. They fill in one day at a time.
* **September.** The timetable in this file starts on 2 October, so the 605 logged September legs cannot be re-scored against a published time. `punctuality.csv` stays on its median baseline for that month, correctly labelled; one September export of the same view would let the whole closed month be restated the way this week has been.
* **Sectors the schedule does not show.** Where the operation flew a sector the timetable has no row for, there is no scheduled time to be late against — the archive and this file disagree by omission, and the count is in `schedule_delays.csv` only from the schedule side.

---

Re-run it against the next export and the week fills itself in:

```
python3 work/schedule_delays.py uploads/<newest weekly export>.csv
```

When the week closes, this is the file `punctuality.csv` should be computed from — a timetable in place of the median that had to stand in for one.
