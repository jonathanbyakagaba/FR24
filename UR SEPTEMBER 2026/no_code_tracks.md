# Tracks that arrived without a flight code

Every track in the archive carries its flight code in the file name, `<FLIGHT>-<8 hex>.csv`. A few do not, and this is what each of them is — start and end resolved from the first and last position in the track.

Archive checked: **802 tracks** (`fr24_publish/FR data.zip`).

---

## 1. Tracks whose name carries no code — 2

| file | callsign | date | started | ended | air time | fixes | in the log? |
|---|---|---|---|---|---|---|---|
| `3e02c7e0.csv` | *(none)* | 22 Jan 2026 | **EBB** | **KGL** | 43 min | 201 | not in the log |
| `41e29857.csv` | UGD720X | 29 Sep 2026 | **NBO** | **EBB** | 53 min | 285 | UGD720X |

### `3e02c7e0.csv` — EBB → KGL

* **Callsign in the file**: **empty on every row** — no flight number, no operator
* **Started**: **EBB** — Entebbe International Airport (HUEN, large airport, UG, Entebbe), 1 NM from the fix — 22 Jan 11:15 local, 2026-01-22T08:15:26Z UTC, on the ground, 0 ft, 11 kt
* **Ended**: **KGL** — Kigali International Airport (HRYR, large airport, RW, Kigali), 1 NM from the fix — 22 Jan 10:59 local, 2026-01-22T08:59:20Z UTC, 0 ft
* **Profile**: 201 fixes, 42 of them on the ground, highest 24,025 ft
* **File**: `3e02c7e0.csv` — 13,511 bytes

### `41e29857.csv` — NBO → EBB

* **Callsign in the file**: `UGD720X`
* **Started**: **NBO** — Jomo Kenyatta International Airport (HKJK, large airport, KE, Nairobi), 1 NM from the fix — 29 Sep 08:12 local, 2026-09-29T05:12:25Z UTC, on the ground, 0 ft, 8 kt
* **Ended**: **EBB** — Entebbe International Airport (HUEN, large airport, UG, Entebbe), 1 NM from the fix — 29 Sep 09:05 local, 2026-09-29T06:05:34Z UTC, 0 ft
* **Profile**: 285 fixes, 58 of them on the ground, highest 34,025 ft
* **File**: `41e29857.csv` — 21,143 bytes
* **The same day's log on this pair** (29SEP26): `UGD200` EBB→NBO 0807–0859 local; `UGD201` NBO→EBB 1015–1106 local; `UGD206` EBB→NBO 2028–2116 local; `UGD207` NBO→EBB 2213–2304 local — this pair carries 140 further legs on other days.
* **Two aircraft crossed the pair inside 90 minutes** — `UGD200` EBB→NBO 0807–0859 local, against this track's NBO→EBB 08:12–09:05 local. That is what an extra/positioning leg looks like in the data.

---

## 2. Tracks with no callsign at all — 1

* `3e02c7e0.csv` — 22 Jan 2026, EBB → KGL, 201 fixes. Every `Callsign` field is empty, so nothing in the file says who flew it or under what number.

---

## 3. Coded tracks the log excludes: callsign outside the operator series — 9

| file | callsign | date | started | ended | max alt |
|---|---|---|---|---|---|
| `UR523-41db0d31.csv` | AF523 | 27 Sep 2026 | **EBB** | **EBB** | 19,025 ft |
| `UR523-41db7233.csv` | AF523 | 27 Sep 2026 | **EBB** | **UG-0013** | 18,025 ft |
| `UR523-41dba960.csv` | AF523 | 27 Sep 2026 | **UG-0013** | **EBB** | 19,000 ft |
| `UR523-41dbf274.csv` | AF523 | 27 Sep 2026 | **EBB** | **UG-0013** | 18,025 ft |
| `UR523-41dc48f7.csv` | AF523 | 27 Sep 2026 | **UG-0013** | **EBB** | 19,000 ft |
| `UR523-41e42128.csv` | AF523 | 29 Sep 2026 | **EBB** | **UG-0013** | 18,025 ft |
| `UR523-41e6a60c.csv` | AF523 | 30 Sep 2026 | **UG-0013** | **EBB** | 17,000 ft |
| `UR523-41e6cb8f.csv` | AF523 | 30 Sep 2026 | **EBB** | **UG-0013** | 18,000 ft |
| `UR523-41e6f162.csv` | AF523 | 30 Sep 2026 | **UG-0013** | **EBB** | 19,000 ft |

These are the Entebbe↔Hoima shuttles of 27 and 29 Sep 2026 — Kabalega International (`UG-0013`), which has no IATA or ICAO code yet. They are in the archive but not in the flight log, exactly as README §5 states.

The 29 Sep leg is the only one that ends away from Entebbe with the aircraft still airborne — the track stops 10 NM short of Hoima at 10,225 ft, so its landing was not captured. The five on 27 Sep all show ground contact at both ends, and the first of them (06:39–07:44 UTC) is a local sortie: it takes off and lands at Entebbe without Hoima appearing at either end.

---

## 4. Operator flights whose callsign came out off-pattern — 3

These **did** arrive with a code in the file name, so they are logged normally; the transmitted callsign just does not follow the usual `UGD###` form. Each carries a letter suffix (`X`, `D`) after the number rather than the bare callsign. What that suffix signals is not recorded in this dataset — it is left as it was transmitted.

The same pattern appears on the code-less track in section 1 (`UGD720X`), so the suffix is not the reason a track has no file code; the two things are independent.

| file | callsign | date | started | ended |
|---|---|---|---|---|
| `UR203-3b751c2a.csv` | UGD111X | 28 Jul 2025 | NBO | EBB |
| `UR207-4173413d.csv` | UGD207D | 01 Sep 2026 | NBO | EBB |
| `UR322-41b390ba.csv` | UGD322D | 17 Sep 2026 | EBB | DAR |

---

## What would close these out

1. `41e29857.csv` can be renamed in the published archive to carry its code: `UR720X-41e29857.csv`, following the `<FLIGHT>-<8 hex>.csv` convention (the operator's own prefix with the callsign's number). The manifest would then show `UR720X` in its `flight` column instead of an empty cell.
2. `3e02c7e0.csv` cannot be named from the data — no callsign means no flight number. An FR24 flight record or an app page for Entebbe→Kigali on 22 Jan 2026 would name it.
3. **Settled, 2 Oct 2026: these are the operator's `UR523` Hoima legs**, flown under the airline's `AF523` callsign — which is what the file names already say (`UR523-*.csv`) and what the app pages show (5X-EQU and 5X-KDP, grey status). They stay out of the log while the gate keys on the *transmitted* callsign; accepting `<FLIGHT>-` file names as well would add these 9 tracks to it, which is a build decision rather than a data gap.

