# FR24 — Uganda Airlines flight log & ADS-B track archive

Raw flight-tracking data downloaded from FlightRadar24, plus a flight log in AeroRoutes notation.
Two datasets side by side: **what was flown** (the log) and **the recorded position tracks** (the archive).

Rebuilt: **2026-10-01** from 731 tracks of data through **2026-10-01**.

---

## What is in here

| File | Size | What it is |
|---|---|---|
| `FR data.zip` | 5.8 MB | **731 CSV tracks** · 305,932 position fixes · flat, de-duplicated |
| `manifest.csv` | 65 KB | One row per track: flight, callsign, fixes, first/last fix, duration |
| `all_flights_aeroroutes.md` | 23 KB | **The flight log** — 597 flights in AeroRoutes notation, 01SEP26–30SEP26, generated from the tracks |
| `flights.csv` | 62 KB | The same 597 flights as a table: UTC times, air time, fixes, source track |
| `README.md` | this file | Inventory and format reference |
| analysis files | 14 files | **Derived from the tracks**: aircraft assignment, runway use, weather, punctuality, triangles |
| `reference/` | 5 tables | **Static lookups**: the 47 airports this data touches, their 86 runways, route distances and haul bands, the five airframes, and the published weather — see `reference/README.md` |

---

## 1. `FR data.zip` — the track archive

**731 tracks · 305,932 position fixes · 80 distinct callsigns**
**Coverage: 2025-05-04 → 2026-10-01**

Every file sits flat at the top level and is named `<FLIGHT>-<8 hex>.csv`, where the hex is the FR24
download identifier. One CSV per flight, one flight per CSV.

### What flies in here

| Operator | Track files | Fixes | Coverage |
|---|---:|---:|---|
| Uganda Airlines (UR) | 682 | 278,571 | 2025-05-04 → 2026-10-01 |
| Ethiopian Airlines (ET) | 14 | 6,909 | 2026-03-06 → 2026-09-18 |
| Qatar Airways (QR) | 6 | 4,318 | 2026-01-21 → 2026-03-22 |
| Garuda Indonesia (GA) | 4 | 3,022 | 2026-07-19 → 2026-09-25 |
| Brussels Airlines (SN) | 4 | 2,284 | 2026-03-16 → 2026-03-20 |
| Turkish Airlines (TK) | 4 | 3,387 | 2026-03-20 → 2026-03-22 |
| RwandAir (WB) | 4 | 1,143 | 2026-03-17 → 2026-03-19 |
| Flynas (XY) | 4 | 1,741 | 2026-03-17 → 2026-03-20 |
| KLM (KL) | 3 | 1,704 | 2026-03-16 → 2026-03-19 |
| EgyptAir (MS) | 2 | 943 | 2026-03-22 → 2026-03-22 |
| flydubai (FZ) | 1 | 1,013 | 2026-03-17 → 2026-03-17 |
| Kenya Airways (KQ) | 1 | 411 | 2026-03-19 → 2026-03-19 |
| *no callsign in file* | 2 | 486 | 2026-01-22 |

Endpoints are matched to the nearest airport in a **39-airport reference list**,
taking a match at 25 NM or closer. On that basis the tracks touch **30 airports**
and form **58 route pairs**. The busiest: NBO-EBB (71); EBB-NBO (70); EBB-JNB (34); DAR-EBB (33); JNB-EBB (33); EBB-JUB (32); EBB-DAR (32); JUB-EBB (29); BJM-EBB (28); EBB-BJM (28); LOS-EBB (20); EBB-MGQ (18).

These figures move if the reference list changes — adding an airport reclassifies endpoints that were
previously attributed to a neighbour. The list above is the one used throughout this README.

**11 tracks begin or end more than 25 NM from any airport**, meaning the record starts
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
2026-07:   2
2026-08:  20
2026-09: 610
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

Files run 8–94 KB. Sampling follows flight phase and
ground-station coverage: the median gap between fixes is about 9 s, but the
largest gap inside a track has a median of 3.3 minutes, and
296 of the 731 tracks contain at least one gap over 10 minutes. The worst
cases are 127, 114, 107 minutes. **202 tracks have a gap longer
than 25 minutes and 72 exceed 45 minutes**, so any en-route timing, wind or fuel analysis built
on this data will be working from very sparse stretches. Take-off, landing and total distance are reliable.

---

## 2. `all_flights_aeroroutes.md` — the flight log

**597 flights · 01SEP26–30SEP26**

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
  it left and marked `+1`. 52 flights in this log are marked `+1`.
* **`≈` = take-off not observed** (15 flights).
  The aircraft was first reported already airborne, so the logged time is that first report, not lift-off.
* **`*` = landing not observed** (38 flights, mostly into DAR).
  The track ends with the aircraft still airborne, so the logged time is the last report, not touchdown.

| Day | 01SEP26 | 02SEP26 | 03SEP26 | 04SEP26 | 05SEP26 | 06SEP26 | 07SEP26 | 08SEP26 | 09SEP26 | 10SEP26 | 11SEP26 | 12SEP26 | 13SEP26 | 14SEP26 | 15SEP26 | 16SEP26 | 17SEP26 | 18SEP26 | 19SEP26 | 20SEP26 | 21SEP26 | 22SEP26 | 23SEP26 | 24SEP26 | 25SEP26 | 26SEP26 | 27SEP26 | 28SEP26 | 29SEP26 | 30SEP26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tracks | 16 | 22 | 14 | 24 | 20 | 26 | 23 | 19 | 21 | 15 | 26 | 22 | 27 | 16 | 18 | 17 | 11 | 23 | 16 | 19 | 19 | 17 | 23 | 16 | 29 | 21 | 26 | 22 | 21 | 21 |
| flights logged | 16 | 20 | 13 | 25 | 18 | 28 | 23 | 21 | 19 | 15 | 26 | 18 | 30 | 18 | 18 | 15 | 11 | 22 | 15 | 20 | 19 | 19 | 21 | 15 | 28 | 18 | 24 | 23 | 21 | 18 |

Track counts are by UTC start; log entries are by local departure date, so the two differ on the days
that straddle midnight.

**Every line comes from a track**, so the two datasets cover the same window. To pair a line with its
source file, match the flight number to the callsign (`UGD713` → `UR713-….csv`) and convert between
local and UTC — the log's times are local, the CSV timestamps are UTC. `flights.csv` does that
pairing for you, with the source filename on each row.

---

## 3. Analysis files

Anything derived from the tracks sits beside them, at the top level, so the raw archive and the
analysis of it never have to be untangled. Every row count below is read off the file itself when
this README is rebuilt.

| File | Rows | What it is | Rebuild |
|---|---|---|---|
| `tails.csv` | 701 flights | which aircraft flew which leg, from the per-tail app pages, with the app's own status flag and a track-verified marker | `PYTHONPATH=. python3 work/final.py` |
| `fleet_summary.csv` | 5 tails | per-aircraft totals from the tracks: flights, air hours, routes, cruise and top of climb, with MSN and cabin | `PYTHONPATH=. python3 work/final.py` |
| `fleet_meta.csv` | 5 tails | the hardware record behind those columns: MSN, ICAO type code, mode-S hex, build month, cabin split | `maintained by hand, then re-run work/final.py` |
| `triangle_assignments.csv` | 47 sectors | the fifth-freedom legs flown away from Entebbe (LUN-HRE, ZNZ-JRO), with flight numbers | `PYTHONPATH=. python3 work/final.py` |
| `triangle_routes.md` | — | the triangle-route write-up | `PYTHONPATH=. python3 work/triangle_report.py` |
| `runway_usage.csv` | 731 tracks | runway identification and runway-use measurement per track: which end, where the roll started, how much runway was used | `PYTHONPATH=. python3 work/runways.py` |
| `runway_usage.md` | — | the runway report, including the corrected Entebbe centreline | `python3 work/runway_report.py` |
| `flight_conditions.csv` | 597 flights | the published weather at each end of every flight: wind, gust, visibility, temperature, and the head/crosswind component on the runway actually used | `PYTHONPATH=. python3 work/weather.py` |
| `weather_analysis.md` | — | what the weather explains: runway-in-use, wind against the measured rolls, delayed sectors | `PYTHONPATH=. python3 work/weather.py` |
| `punctuality.csv` | 597 flights | the app's status flag for each leg (on time / late / very late) and the measured minutes against the usual departure time | `python3 work/punctuality.py` |
| `punctuality.md` | — | the punctuality write-up, by aircraft and by worst departure | `python3 work/punctuality.py` |
| `app_status.csv` | 705 rows | the flag table underneath: every status dot read off the per-tail screenshots, matched to its flight | `python3 work/app_status.py` |
| `SUPPORTING.md` | — | one-line description and rebuild command for every derived file | `written by hand` |
| `metar/` | 41 airports | every published METAR for each airport in this operation, one CSV per station plus `index.csv`, raw report text kept | `python3 work/metar_split.py` |

The rebuild commands refer to the small toolkit kept beside this data (the `work/` scripts); the
files themselves are the deliverable, and every count above can be checked directly against them.

Two notes on the derived files:

* **`tails.csv` is the only place an aircraft is tied to a flight.** The FR24 exports carry no
  registration, so the assignment comes from the per-tail app pages and the track archive; a row
  marked verified is one whose flight number and sector were found in `FR data.zip`.
* **Nothing here is an estimate of a schedule.** `punctuality.csv` measures each departure against
  the usual departure time for that service as flown, because the published timetable is not part
  of this dataset.

---

## 4. Reference data (`reference/`)

The static lookups every analysis here leans on, so the whole thing can be recomputed from
the repository alone:

| File | Rows | What it is | Source |
|---|---:|---|---|
| `reference/airports.csv` | 47 | every airport these tracks touch, plus the log's network | OurAirports — public domain |
| `reference/runways.csv` | 86 | runway geometry and orientation for those airports | OurAirports — public domain |
| `reference/route_distances.csv` | 29 | great-circle distance per route pair (km, nm) and the haul band | our own calculation |
| `reference/fleet.csv` | 5 | the airframes: type, ownership, haul band | the operator |
| `reference/weather_2026-09.csv` | 40,926 | published surface observations (METAR) for the airports this operation uses, one row per report | Iowa Environmental Mesonet ASOS archive — free to redistribute |

Haul bands follow the Eurocontrol distance convention: short < 1,500 km, medium
1,500–4,000 km, long > 4,000 km. Notes and licences: `reference/README.md`.

---

## 5. Remaining data notes

* **A track with no callsign cannot be attributed.** Any file whose `Callsign` field is empty on every
  row has no airline and no flight number; it is kept because the positions are valid, and renamed by
  hand once identified.
* **11 tracks begin or end more than 25 NM from any airport** (see §1).
* **The download ends at 03:30 local on 01 Oct** (2026-10-01 00:30:40Z UTC) — the last position in the archive. Nothing after it is in this export yet, which is past the end of the last logged day, so that day runs to its normal end.
* **9 tracks in the archive carry a callsign outside the operator's series** — `UR523` ×9 transmits `AF523`. The log is built from the operator's own callsigns (`UGD…`, `UR…`, `UG…`), so these tracks stay in the archive and out of the log. The per-tail app pages do list them, under `UR523`, so they appear in `tails.csv` as rows with no track match.
* **`UG-0013` is a new airport in the data** — 8 tracks touch it, and it carries no IATA or ICAO code yet, so the tables key it by its OurAirports ident. OurAirports still records it as under construction.
* **1 logged flight takes off and lands at the same airport** — a local sortie (air test, crew training or a return to base), not a service. It still carries the day's flight number: `UGD520` on 18 Sep left and returned to EBB in 46 min. Tracks of this shape that fail the callsign gate are counted in the bullet above, not here.
* **Markers mark what was not seen** — they are not estimates. Where an event was not witnessed the
  logged time is the nearest real observation and the marker says so.

---

## 6. Daily update

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

## 7. Cleaning log

This run received **759 entries** (0 of them not track files,
skipped) and published **731 tracks**
(21.36 MB uncompressed). Cumulative across 44 run(s): **1223 files removed**.

| Removed | Count |
|---|---:|
| duplicate content | 27 |
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
