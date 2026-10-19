# 2026-10 — flight log and track archive

> **Zip updated 2026-10-19 (counts & checksums only).**
> `FR data.zip` in this folder now holds the month's UR flights from
> the current top-level archive: **317 UR tracks · 131,192 fixes**,
> all starting in 2026-10 (01 Oct – 16 Oct).
> sha256 `e7f92fe68a65bc567eb7d4ef32930b6d661fb05c87a97cb3c68d4c155877ce08`
> (2,567 KiB). It replaces the old 880-file cumulative snapshot zip
> that reached only ~05 Oct.

## What is — and is not — up to date

* **Up to date:** the zip above, and this README.
* **Stale (frozen, deliberately not regenerated):** every other file
  in this folder — `flights.csv`, `manifest.csv`, `tails.csv`,
  `app_status.csv`, `flight_conditions.csv`, `punctuality.csv`,
  `runway_usage.csv`, `schedule_delays.csv`, `fleet_summary.csv`,
  `triangle_assignments.csv` and the `.md` write-ups. They describe
  the earlier freeze (**82 logged flights, 01–05 Oct, against an
  826-track cumulative archive**), not the current zip. Regenerating
  them needs the `work/` pipeline (`work/close_month.py` etc.) plus
  its external inputs — FR24 per-tail app pages, METAR, timetable and
  runway datasets — none of which are in this repository. See
  `SUPPORTING.md` for what each file is and its rebuild command.

## Verifying

* This folder's `FR data.zip`:
  sha256 `e7f92fe68a65bc567eb7d4ef32930b6d661fb05c87a97cb3c68d4c155877ce08`
* The top-level `FR data.zip` it was split from (1,065 tracks,
  deduplicated):
  sha256 `0e7cacc3ec4ea0dfeba2e42a7b443948ceb81ff00e632f6ae62be06e514563d3`

The rule used throughout this repo: **a flight belongs to the month
its departure falls in, local time (EAT)** — a track that starts in
this month is stored whole in this month's zip, even if it lands in
the next.
