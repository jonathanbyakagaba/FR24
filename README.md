# FR24 — Uganda Airlines flight log & ADS-B track archive

Raw flight-tracking data downloaded from FlightRadar24, plus a flight log in AeroRoutes notation.
Two datasets side by side: **what was flown** (the log) and **the recorded position tracks** (the archive).

Last rebuilt: **2026-09-11** from 317 tracks.

---

## What is in here

| File | Size | What it is |
|---|---|---|
| `FR data.zip` | 2.6 MB | **317 CSV tracks** · 137,807 position fixes · flat, de-duplicated |
| `manifest.csv` | 28 KB | One row per track: flight, callsign, fixes, first/last fix, duration |
| `all_flights_aeroroutes.md` | 8 KB | **The flight log** — 198 flights in AeroRoutes notation, 01SEP26–10SEP26, generated from the tracks |
| `flights.csv` | 21 KB | The same 198 flights as a table: UTC times, air time, fixes, source track |
| `README.md` | this file | Inventory and format reference |

---

## 1. `FR data.zip` — the track archive

**317 tracks · 137,807 position fixes · 73 distinct callsigns**
**Coverage: 2025-05-04 → 2026-09-11**

Every file sits flat at the top level and is named `<FLIGHT>-<8 hex>.csv`, where the hex is the FR24
download identifier. One CSV per flight, one flight per CSV.

### What flies in here

| Operator | Track files | Fixes | Coverage |
|---|---:|---:|---|
| Uganda Airlines (UR) | 275 | 114,507 | 2025-05-04 → 2026-09-11 |
| Ethiopian Airlines (ET) | 12 | 6,155 | 2026-03-06 → 2026-04-30 |
| Qatar Airways (QR) | 6 | 4,318 | 2026-01-21 → 2026-03-22 |
| Brussels Airlines (SN) | 4 | 2,284 | 2026-03-16 → 2026-03-20 |
| Turkish Airlines (TK) | 4 | 3,387 | 2026-03-20 → 2026-03-22 |
| RwandAir (WB) | 4 | 1,143 | 2026-03-17 → 2026-03-19 |
| Flynas (XY) | 4 | 1,741 | 2026-03-17 → 2026-03-20 |
| KLM (KL) | 3 | 1,704 | 2026-03-16 → 2026-03-19 |
| EgyptAir (MS) | 2 | 943 | 2026-03-22 → 2026-03-22 |
| flydubai (FZ) | 1 | 1,013 | 2026-03-17 → 2026-03-17 |
| Kenya Airways (KQ) | 1 | 411 | 2026-03-19 → 2026-03-19 |
| *no callsign in file* | 1 | 201 | 2026-01-22 |

Endpoints are matched to the nearest airport in a **37-airport reference list**,
taking a match at 25 NM or closer. On that basis the tracks touch **28 airports**
and form **53 route pairs**. The busiest: NBO-EBB (25); EBB-NBO (25); DAR-EBB (15); EBB-JNB (14); EBB-DAR (14); JNB-EBB (13); BJM-EBB (12); EBB-JUB (12); JUB-EBB (11); EBB-BJM (11); LOS-EBB (9); EBB-HRE (9).

These figures move if the reference list changes — adding an airport reclassifies endpoints that were
previously attributed to a neighbour. The list above is the one used throughout this README.

**12 tracks begin or end more than 25 NM from any airport**, meaning the record starts
airborne or stops before landing. Treat their first or last fix as a partial flight, not a take-off or
landing.

### Coverage by month

```
2025-05:   1
2025-07:   5
2025-12:   1
2026-01:   5
2026-02:   5
2026-03:  80
2026-04:   2
2026-08:  20
2026-09: 198
```

This is an ad-hoc collection rather than a continuous feed: some months carry hundreds of tracks and
others none at all.

### CSV format

Every file shares the same seven-column header:

```csv
Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction
1788681009,2026-09-06T07:50:09Z,UGD110,"0.04533,32.441788",0,2,84
```

| Column | Meaning |
|---|---|
| `Timestamp` | Unix epoch seconds (UTC) |
| `UTC` | ISO-8601 timestamp, same instant, human-readable |
| `Callsign` | Callsign as transmitted — **not the same as the filename**: `UR110-….csv` carries `UGD110`, `ET332-….csv` carries `ETH332` |
| `Position` | `"latitude,longitude"` in WGS-84, quoted because of the comma |
| `Altitude` | Barometric altitude in **feet** |
| `Speed` | **Ground** speed in knots |
| `Direction` | True track in degrees (0–360) |

Files run 12–94 KB. Sampling follows flight phase and
ground-station coverage: the median gap between fixes is about 9 s, but the
largest gap inside a track has a median of 5.8 minutes, and
152 of the 317 tracks contain at least one gap over 10 minutes. The worst
cases are 127, 114, 107 minutes. **107 tracks have a gap longer
than 25 minutes and 34 exceed 45 minutes**, so any en-route timing, wind or fuel analysis built
on this data will be working from very sparse stretches. Take-off, landing and total distance are reliable.

---

## 2. `all_flights_aeroroutes.md` — the flight log

**198 flights · 01SEP26–10SEP26**

```text
01SEP26  UGD720 HRE0205 – 0545EBB
01SEP26  UGD111 LGW2026 – 0632+1EBB
01SEP26  UGD520 EBB0506 – 0650MGQ*
```

`DDMMMYY  FLIGHT ORIGhhmm – hhmm[+1]DEST[marker]`

* **Times are local at each end** — take-off in the origin's local time, landing in the destination's.
  This is why a short regional flight can appear to arrive "before" it departs (e.g. `EBB1621 – 1609BJM`:
  Entebbe is UTC+3, Bujumbura UTC+2).
* **Dates are local departure dates**, so a flight landing after local midnight is listed under the day
  it left and marked `+1`. 16 flights in this log are marked `+1`.
* **`≈` = take-off not observed** (4 flights, all leaving MGQ).
  The aircraft was first reported already airborne, so the logged time is that first report, not lift-off.
* **`*` = landing not observed** (14 flights, mostly into DAR).
  The track ends with the aircraft still airborne, so the logged time is the last report, not touchdown.

| Day | 01SEP26 | 02SEP26 | 03SEP26 | 04SEP26 | 05SEP26 | 06SEP26 | 07SEP26 | 08SEP26 | 09SEP26 | 10SEP26 |
|---|---|---|---|---|---|---|---|---|---|---|
| tracks | 16 | 22 | 14 | 24 | 20 | 26 | 23 | 19 | 21 | 13 |
| flights logged | 16 | 20 | 13 | 25 | 18 | 28 | 23 | 21 | 19 | 15 |

Track counts are by UTC start; log entries are by local departure date, so the two differ on the days
that straddle midnight.

**Every line comes from a track**, so the two datasets cover the same window. To pair a line with its
source file, match the flight number to the callsign (`UGD713` → `UR713-….csv`) and convert between
local and UTC — the log's times are local, the CSV timestamps are UTC. `flights.csv` does that
pairing for you, with the source filename on each row.

---

## 3. Remaining data notes

* **A track with no callsign cannot be attributed.** Any file whose `Callsign` field is empty on every
  row has no airline and no flight number; it is kept because the positions are valid, and renamed by
  hand once identified.
* **12 tracks begin or end more than 25 NM from any airport** (see §1).
* **Markers mark what was not seen** — they are not estimates. Where an event was not witnessed the
  logged time is the nearest real observation and the marker says so.

---

## 4. Daily update

The archive grows by **appending**: existing tracks are never rewritten. One command does the whole
rebuild after you replace the zip in the repository:

```bash
python3 fr24_update.py            # fetch the repo zip, clean, rebuild every output
python3 fr24_update.py --check    # report what would change, write nothing
```

It removes duplicate and row-identical copies, drops partial downloads, restores any fuller version an
earlier build already had, flattens folders, renames to `<FLIGHT>-<8 hex>.csv`, normalises line endings
to LF, then regenerates `manifest.csv`, the log, `flights.csv` and this README with every count
recomputed.

Keep new files in the same seven-column format, one file per flight, named `<FLIGHT>-<8 hex>.csv`.
Avoid `-1`/`_1`/`(1)` suffixes: those are repeat-save artefacts, not versions, and they are what makes
duplicates accumulate.

---

## 5. Cleaning log

This run received **342 entries** and published **317 tracks**
(9.62 MB uncompressed). Cumulative across 4 run(s): **161 files removed**.

| Removed | Count |
|---|---:|
| duplicate content | 24 |
| row-identical copy | 1 |

**Restored this run.** These were present in the previous build but missing or truncated in the incoming archive, so the fuller version was put back:

* `UR110-3ed2932d.csv` — the incoming archive carried only `UR110-3ed2932d.csv` (234 rows), against 1065 rows in the previous build

Also normalised: all line endings to LF, and all names to canonical form.

---

## Provenance

Tracks downloaded from FlightRadar24 — hence the repo name and the hex identifiers in the filenames.
The log is generated from those tracks and is written in the notation used by aeroroutes.com. The
archive is raw data as downloaded: values are as reported by the source, with no cleaning,
interpolation or gap filling. Times in the log are observations, never extrapolations — where an event
was not witnessed, a marker says so.
