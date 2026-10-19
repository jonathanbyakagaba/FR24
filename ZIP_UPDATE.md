# Zip update — 19 Oct 2026

## What was done

The two top-level archives were rebuilt from `FR data (1).zip`, the
newest download (coverage to 16 Oct 2026):

- **`FR data (1).zip`** and **`FR data.zip`** are now the *same* cleaned
  archive, so there is no longer an old and a new version at the top
  level.
  - sha256: `0e7cacc3ec4ea0dfeba2e42a7b443948ceb81ff00e632f6ae62be06e514563d3`
  - **1,065 track CSVs** (was 1,100 files / 1,037 files respectively)
  - Same internal layout: `FR data/FR data/*.csv`
- Cleaned = duplicate-free. **35 byte-identical duplicate files were
  removed** (the `_1`, `-1`, `-2`, ` (1)` re-downloads, e.g.
  `UR110-4180268d_1.csv`, `UR520-41f6251e-2.csv`). No unique track was
  removed: per-date coverage after cleaning is identical to the
  analysis in `missing_dates_fr_data_1.md` (e.g. 10 Oct still the
  single UR431, 16 Oct still 25 UR tracks).
- Every other zip in the repo was checked first for tracks the newest
  archive lacked. There were none: `FR data.zip` and
  `UR OCTOBER 2026/FR data.zip` are strict (content) subsets of
  `FR data (1).zip`.

## What was deliberately NOT changed

- **`UR OCTOBER 2026/FR data.zip`** and the September folder were left
  untouched. Those folders are frozen month snapshots — their READMEs
  state the sha256 the folder's tables were built against, so
  overwriting their zips would silently invalidate the freeze.
- Note: `UR SEPTEMBER 2026/UR September flights.zip` is a **2-byte
  empty placeholder** (`\r\n`), not a real zip. That predates this
  update; it was not touched. If the real September archive exists
  elsewhere, it should be restored there.

## The missing flights could NOT be added — they exist nowhere in the repo

"Adding the missing flights" was requested, but it can't be done from
anything currently in this repository, and the tracks can't be fetched
from here either (no Flightradar24 access). Specifically:

- No zip in the repo contains a single track for **Sat 10 Oct 2026**
  (beyond the UR431 inbound already in the archive), for
  **17–19 Oct 2026**, or for the missing triangle/UR343/UR111 legs
  listed in `missing_flights_october_2026.md`. The older zips are
  older, so they hold *less* October, not more.
- Those tracks only exist on Flightradar24. To add them:
  1. From a Flightradar24 account, download the flight histories for
     the flights/dates listed in `missing_flights_october_2026.md`
     (priority: all of 10 Oct; 17 Oct onwards; UR720 LUN–HRE /
     UR722 HRE–LUN / UR334 ZNZ–JRO sectors; UR343 MBA–EBB;
     UR111 LGW–EBB).
  2. Drop the downloaded CSVs anywhere in the repo (e.g. a folder
     named `new tracks/`) and commit/push, or open an issue on the PR.
  3. They will then be merged into both top-level zips,
     deduplicated the same way, and the coverage reports regenerated.

Until then the updated zips are exactly as complete as the newest
download — minus duplicates, plus nothing fabricated.
