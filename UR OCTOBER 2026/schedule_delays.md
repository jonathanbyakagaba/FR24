# Delays against the published schedule — 02–09 October 2026

201 legs · 41 flight numbers · 8 days. Per-leg numbers: `schedule_delays.csv`.

This is the first timetable the repository has held, so for the first time a delay is **observed minus published** — and for the first time there is an arrival delay at all, since the app screenshots and the ADS-B log only ever fix a departure. The two measures disagree in a useful direction: `punctuality.csv` scores a service against its own habit, so a flight that always leaves 40 minutes late scores zero. Where this table and that one part company, it is the schedule being reported on, not the aircraft.

## Three properties of the file that change the answer

1. **Status times are UTC; schedule times are local.** `UR209 NBO→EBB` is due at 01:30 Entebbe time and reads `Landed 22:10` — 22:10Z the previous evening, i.e. 01:10 local, **twenty minutes early**, not 23 h 40 min late. Every status is snapped to the day nearest the scheduled instant it belongs to.
2. **The file runs East Africa on a single clock.** Offsets are not assumed: each row carries a `block`, which fixes the difference between its two airports, so the table below is voted across the week with Entebbe pinned at +0300:

   `BJM` +0200 · `BOM` +0530 · `DAR` +0300 · `DXB` +0400 · `EBB` +0300 · `FIH` +0100 · `HRE` +0200 · `JNB` +0200 · `JRO` +0300 · `JUB` +0200 · `LGW` +0100 · `LOS` +0100 · `LUN` +0200 · `MBA` +0300 · `MGQ` +0300 · `NBO` +0300 · `ZNZ` +0300

   **DAR**, **JRO**, **ZNZ** come out at +0300 while those airports’ own wall clocks run +0200. That is a display convention rather than an error — but reading the column at the wall clock invents an hour, which is exactly how two Kilimanjaro arrivals came to look 80 minutes early on a first pass.

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

Every leg is joined to the service it repeats — flight number and sector, matched through the callsign form the log uses (`UGD209` for `UR209`) — and against what this build has measured for that service: 0 services have three or more logged legs to compare with. Two columns come out of that, and neither is a delay:

* **`sched_vs_op_min`** — scheduled departure against the median time the service actually left. Negative means the timetable is earlier than the operation: that leg is written to be missed, every day.
* **`block_slack_min`** — scheduled block against the median block actually flown, measured ground-to-ground out of the archive's own tracks (first fix to last, which is on the ground at both ends in 248 and 233 of the first 250 legs). Negative means the schedule asks for less time than the aircraft needs: the sector is late by construction, and the delay arrives on the next one.

One caveat on the block baseline. A track window is only a block where the track starts and ends on the ground, which it does for 248 and 233 of the first 250 legs sampled; the rest lose some taxi, so a shortfall of a minute or two on those is inside the measurement. The `air_minutes` counterpart is in the CSV as `op_median_air_min` — the airborne part only, which is what `air_minutes` in the archive log means — and it sits a median 5.8 min below the window over the 182 comparable legs.

0 legs sit 20 minutes or more away from the time their service actually leaves. That is the honest definition of a structurally late flight, and it is a number the median-based `punctuality.csv` cannot produce at all: measured against itself, a habit is invisible.

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
