# FR24 — Uganda Airlines flight log & ADS-B track archive

Raw flight-tracking data downloaded from FlightRadar24, plus a flight log in AeroRoutes notation.
Two datasets side by side: **what was flown** (the log) and **the recorded position tracks** (the archive).

---

## What is in here

| File | Size | What it is |
|---|---|---|
| `FR data.zip` | 2.4 MB | **292 CSV tracks** · 129,165 position fixes · flat, de-duplicated |
| `manifest.csv` | 40 KB | One row per track: flight, callsign, fixes, first/last fix, duration |
| `all_flights_aeroroutes.md` | 6.7 KB | **The flight log** — 167 flights in AeroRoutes notation, 29AUG26–08SEP26 |
| `README.md` | this file | Inventory and format reference |

Nothing else is stored here: no scripts, no generated reports, no intermediate files.

---

## 1. `FR data.zip` — the track archive

**292 tracks · 129,165 position fixes · 73 distinct callsigns**
**Coverage: 2025-05-04 → 2026-09-10 · 49 route pairs · 26 airports**

Every file sits flat at the top level and is named `<FLIGHT>-<8 hex>.csv` (e.g. `UR110-4187ba0c.csv`);
the 8-digit hex is the FR24 download identifier. One CSV per flight, one flight per CSV, no folders.

The archive was rebuilt from 378 stored files down to these 292 tracks — see
[Cleaning log](#5-cleaning-log) for exactly what was removed and why.

### What flies in here

Mostly Uganda Airlines, plus the other carriers sharing its network:

| Operator | Track files | Fixes | Coverage |
|---|---:|---:|---|
| **Uganda Airlines** (UR) | 250 | 105,865 | 2025-05-04 → 2026-09-10 |
| Ethiopian Airlines (ET) | 12 | 6,155 | 2026-03-06 → 2026-04-30 |
| Qatar Airways (QR) | 6 | 4,318 | 2026-01-21 → 2026-03-22 |
| Brussels Airlines (SN) | 4 | 2,284 | 2026-03-16 → 2026-03-20 |
| Turkish Airlines (TK) | 4 | 3,387 | 2026-03-20 → 2026-03-22 |
| RwandAir (WB) | 4 | 1,143 | 2026-03-17 → 2026-03-19 |
| Flynas (XY) | 4 | 1,741 | 2026-03-17 → 2026-03-20 |
| KLM (KL) | 3 | 1,704 | 2026-03-16 → 2026-03-19 |
| EgyptAir (MS) | 2 | 943 | 2026-03-22 |
| flydubai (FZ) | 1 | 1,013 | 2026-03-17 |
| Kenya Airways (KQ) | 1 | 411 | 2026-03-19 |
| *no callsign in file* | 1 | 201 | 2026-01-22 |

Counts are for **tracks**. 49 distinct route pairs appear, with endpoints resolving to within
25 NM of Entebbe and: NBO, DAR, ZNZ, MBA, JRO, JUB, BJM, KGL, JNB, HRE, LUN, LOS, ADD, MGQ, DOH,
DXB, BRU, AMS, IST, CAI, LGW, BOM and others. Busiest: **NBO–EBB (23); EBB–NBO (23); EBB–JNB (15);
DAR–EBB (14); EBB–DAR (13); JNB–EBB (13); EBB–JUB (11); JUB–EBB (10)**.

17 tracks begin or end more than 25 NM from any airport — those records start airborne or stop before
landing, so treat their first/last fix as a partial flight, not a take-off or landing.

### Coverage by month

```
2025-05:   1      2026-02:   5
2025-07:   5      2026-03:  80      ← a quarter of the archive
2025-12:   1      2026-04:   2
2026-01:   5      2026-08:  20
                  2026-09: 173      ← 59% of all tracks
```

This is an ad-hoc collection rather than a continuous feed: March 2026 and September 2026 together
account for 253 of the 292 files, while several months are absent.

**September 2026 is now essentially complete,** covering 1–9 September with 173 tracks and 68,016 fixes:

| Day | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tracks | 16 | 22 | 14 | 24 | 19 | 25 | 22 | 18 | 13 |

### CSV format

All 292 files share the same seven-column header, with no variation:

```csv
Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction
1788681009,2026-09-06T07:50:09Z,UGD110,"0.04533,32.441788",0,2,84
```

| Column | Meaning |
|---|---|
| `Timestamp` | Unix epoch seconds (UTC) |
| `UTC` | ISO-8601 timestamp, same instant, human-readable |
| `Callsign` | Callsign as transmitted — **not the same as the filename**: `UR110-….csv` carries `UGD110`, `ET332-….csv` carries `ETH332`, `XY1233-….csv` carries `KNE1233` |
| `Position` | `"latitude,longitude"` in WGS-84, quoted because of the comma |
| `Altitude` | Barometric altitude in **feet** |
| `Speed` | **Ground** speed in knots |
| `Direction` | True track in degrees (0–360) |

Files run 13–94 KB. Sampling follows flight phase and ground-station coverage: the median gap between
fixes is about 11 s, widening to 30–60 s in cruise and, on some remote-airspace legs, to a single
report every 25–45 minutes. Take-off, landing and total distance are reliable; en-route timing, winds
and fuel are not.

---

## 2. `all_flights_aeroroutes.md` — the flight log

**167 flights · 29AUG26–08SEP26 · 38 flight numbers · 15 airports**
Written in AeroRoutes notation, grouped by day:

```text
01SEP26  UGD713 JNB0255 – 0746EBB
04SEP26  UGD111 LGW2024 – 0637+1EBB
08SEP26  UGD521 MGQ0848 – 1039EBB≈
```

`DDMMMYY  FLIGHT ORIGhhmm – hhmm[+1]DEST[marker]`

* **Times are local at each end** — take-off in the origin's local time, landing in the destination's.
  This is why a short regional flight can appear to arrive "before" it departs (e.g. `EBB1621 – 1609BJM`:
  Entebbe is UTC+3, Bujumbura UTC+2).
* **Dates are local departure dates**, so a flight landing after local midnight is listed under the day
  it left and marked `+1`.
* `*` = landing unobserved (the track ends airborne) · `≈` = estimated take-off (Mogadishu coverage gap).
  22 of the 167 lines carry one of these markers.

**The log and the archive do not cover the same window.** The log runs 29 Aug – 8 Sep as timetable
lines with no coordinates; the archive's September tracks run 1–9 Sep. To pair a log line with a
track, match the flight number to the callsign (`UGD713` → `UR713-….csv`) *and* convert between local
and UTC — the log's times are local, the CSV timestamps are UTC.

---

## 3. Remaining data notes

The archive is clean: no duplicate content, no partial copies, no nested folders, no stray file
extensions. Three things still need care when analysing it:

* **`3e02c7e0.csv` has no flight number** and its `Callsign` field is empty on all 201 rows, so it
  cannot be attributed to an airline or a flight number. Its positions place it at Entebbe on
  **2026-01-22 08:15Z**. It is kept rather than deleted because the track itself is valid; rename it
  by hand once the flight is identified.
* **17 tracks begin or end more than 25 NM from any airport** — those records start airborne or stop
  before landing, so their first/last fix is a partial flight, not a take-off or landing.
* **The log and the archive cover different windows.** The log runs 29 Aug – 8 Sep as timetable lines
  with no coordinates; the archive's September tracks run 1–9 Sep. Pair a line with a track by
  matching the flight number to the callsign (`UGD713` → `UR713-….csv`) *and* converting between local
  and UTC — the log's times are local, the CSV timestamps are UTC.

---

## 4. Updating the archive

Keep it growing by **appending**: nothing is ever rewritten, so the original tracks remain
byte-for-byte unchanged. Before adding anything:

1. **De-duplicate first**, checking three separate things — content hash, row-level equality, and
   callsign-plus-time-window overlap. Two files can have different bytes, different sizes, or
   different line endings and still be the same flight. All three cases were present in this archive.
2. **Drop partial downloads.** A short file whose rows are a strict subset of a longer one is a
   truncated copy, not a second flight.
3. **Keep it flat.** No folders — put every CSV at the top level.
4. **Use one naming scheme:** `<FLIGHT>-<8 hex>.csv`. Strip `(1)`-style suffixes and avoid `-1`/`_1`
   endings, which are repeat-save artefacts rather than versions.
5. **Save as UTF-8 with LF line endings** so a single track does not stand out by encoding alone.
6. Then update this README's counts, operator table and month breakdown, and regenerate `manifest.csv`.

---

## 5. Cleaning log

The archive was rebuilt from **378 stored files → 292 tracks** (11.52 MB → 9.02 MB uncompressed).
86 files were removed. All 293 original distinct row-sets survive: the one row-set that is absent is
the 234-row partial whose rows are all present in the retained 1065-row file. Nothing was modified,
and no track was shortened.

| Removed | Count | Reason |
|---|---:|---|
| Files in `FR data/CSVs for upload/uploads/` | 38 | each duplicated a top-level track |
| Repeat saves duplicated elsewhere | 46 | identical content stored under a second name |
| `UR445-3dba7a13 (1).csv` | 1 | row-identical to `UR445-3dba7a13.csv`, CRLF endings only |
| `UR110-3ed2932d.csv` | 1 | partial download — its 234 rows are all inside the retained 1065-row file |
| **total removed** | **86** | from 378 stored files down to 292 tracks |

Of the 86 removed, 56 carried a `-1`/`_1` suffix. Also normalised: line endings to LF (one file was
CRLF) and all names to canonical form — `UR110-3ed2932d-1.csv` became `UR110-3ed2932d.csv` once its
partial twin was dropped.

The earlier state is recoverable from git history if needed.

---

## Provenance

Tracks downloaded from FlightRadar24 — hence the repo name and the hex identifiers in the filenames.
The log is transcribed in the notation used by aeroroutes.com. The archive is raw data as downloaded:
values are as reported by the source, with no cleaning, interpolation or gap filling.
