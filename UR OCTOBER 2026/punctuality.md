# Departure punctuality — 1–22 October 2026 (rebuilt 2026-10-23)

`punctuality.csv` was regenerated on a new basis: the **FTA utilization
plan's** scheduled departure (STD) for the leg, joined to the track by
`work/build_october_fta.py` (458 of 480 planned legs matched; the 22
without a track are classified in `data_gaps.md` — 17 did not
operate, 2 operated outside the join window, 3 not yet exported). This replaces the frozen build's
"usual time" scoring for 1–5 Oct, which could not see a habitually late
service. September's `punctuality.csv` (September folder) keeps the
app/usual-time basis — the two months' files are not directly comparable.

**Read the delay column carefully:** the "actual" is the track's *takeoff*
(first airborne fix), while STD is off-block. Departure delay therefore
includes taxi-out — roughly 15–30 min at Entebbe. A flight showing +20 min
here is typically on time at the gate.

## Scoreboard (takeoff vs STD, 458 matched legs)

| early | on time (0–15m) | delayed (16–60m) | heavily delayed (>60m) |
|---:|---:|---:|---:|
| 158 | 153 | 121 | 26 |

Two-thirds of legs got airborne within 15 minutes of the (taxi-inclusive)
allowance — i.e. the operation ran close to plan. The heavily-delayed tail
concentrates in the A330/leased-A350 long-hauls and in the disrupted first
week (the plan itself carries DELAYED/RESCHEDULED statuses on 2, 4, 5, 6, 7
and 9 Oct). `schedule_delays.csv` has the per-leg detail, including the
plan's own status flags and arrival delays.

## What is not here

The FR24 app status dots (`app_status.csv`) end at 30 Sep — no October app
captures were available to this rebuild, so `app_status` is blank in
`punctuality.csv` and no app-based judgement is offered for October.
