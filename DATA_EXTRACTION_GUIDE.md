# FR24 Data Extraction & Rebuild Guide

**Purpose:** bring the Uganda Airlines (UR) flight-track dataset in this
repository up to date — from a cold start, with nothing assumed. Follow the
phases in order. Last verified end-to-end on **2026-10-23**; if commands or
counts look different when you run them, trust what the scripts print and
update this guide in the same commit.

---

## 0. The 30-second picture

There are two ways track data gets in, and one pipeline that processes it:

```
SOURCE A (bulk export)                SOURCE B (API playback, Windows PC)
user exports FR24 tracks        ┌──►  fetch_fr24.py    enumerate flight lists
as FR data.zip, uploads it      │     fetch_tracks.py  download target tracks
                                │     pick_flights.py  hand-pick + download
                                └──────────┬──────────────────────────────┘
                                           ▼
        FR data.zip  (pool: every track, all operators, MD5-deduped)
            ├── UR September flights.zip   (UR subset, September)
            └── UR OCTOBER 2026/FR data.zip (UR subset, October)
                                           ▼
        rebuild_month.py → FTA join → rebuild_month.py → conditions →
        OD matrices → docs → website/build_data.py → website/data.json
```

**Canonical rules (never break these):**

1. **Dedupe by exact file content (MD5)** — never by filename.
2. **A flight belongs to the month of its origin-local departure date**
   (local time at the *origin* airport of takeoff/first fix), as computed by
   `work/rebuild_month.py`. An overnight LUN→HRE departure at 21:42Z is 23:42
   Lusaka time the same day — do not judge dates in EAT or UTC alone.
3. **Routes are inferred** from the nearest airport to the first/last fix.
4. **UR membership:** filename starts `UR`/`AF`, or callsign starts `UGD`.
5. In the FTA plans, **CANCELLED and NON_SCHEDULED legs are not missing**,
   and a leg listed in two day-plans counts once.
6. FR24 ICAO codes differ from old tables: **Harare = FVRG** (not FVHA),
   **Juba = HJJJ** (not HSSJ). EBB = HUEN, LUN = FLKK.

**Track file format** (all archives): CSV named `<FLIGHT>-<fr24hexid>.csv`
(e.g. `UR720-4172c560.csv`, the hex is the FR24 flight id in hex), header
`Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction`, `Position`
quoted as `"lat,lon"` at 6 decimal places. Inside every zip, entries live
under `FR data/FR data/<file>.csv`.

---

## 1. Repository map

| path | what it is |
|---|---|
| `FR data.zip` | the pool: every unique track ever ingested (all operators) |
| `UR SEPTEMBER 2026/` | September dataset: month zip + rebuilt tables + write-ups |
| `UR OCTOBER 2026/` | October dataset (same layout; month zip is also named `FR data.zip` — careful!) |
| `work/` | all pipeline scripts, source transcriptions, flight lists, targets |
| `website/` | interactive map; `build_data.py` generates `data.json` |
| `DATA_EXTRACTION_GUIDE.md` | this file |

Month-folder tables are **derived** — never hand-edit CSVs there; regenerate
them (Phase 8). Files that are *inputs* and are safe to update: the zips,
`work/fta_*.csv`, `work/notams_snapshot_*.csv`, `work/flightlists/`,
`work/tracks_in/`, and each folder's `metar/` and `tails.csv` (see Phase 8).

**Status at last verification (2026-10-23):** the 1,239-track pool is
fully cascaded — September 640 flights, October 473 flights
(1–22 Oct); website 1,113 flights, 1 Sep – 22 Oct. See §13.

---

## 2. Phase 1 — Windows workstation setup (once)

FR24's API is only reachable from the user’s Windows machine (see the
troubleshooting table in §12). Set up once:

1. Install Python 3.11+ from python.org (tick "Add to PATH").
2. Open Command Prompt in `C:\Users\User` and create the environment:
   ```bat
   python -m venv fr24env
   fr24env\Scripts\activate
   pip install "fr24[curl,polars]==0.4.0" tzdata
   ```
   The version pin matters: `fr24` 0.4.0 with the `curl` extra (curl-cffi
   client) is the only combination verified to work. `tzdata` is required
   because Windows Python has no timezone database.
3. Copy these three repo files into `C:\Users\User\`, side by side (they
   import each other): `work/fetch_fr24.py`, `work/fetch_tracks.py`,
   `work/pick_flights.py`.
4. Every session starts with:
   ```bat
   cd C:\Users\User
   fr24env\Scripts\activate
   ```
   Check for the `(fr24env)` prompt prefix before running anything.

## 3. Phase 2 — FR24 credentials (the fiddly part, once)

The scripts authenticate with a **subscription key** harvested from your
own logged-in browser session. Do this carefully:

1. In Chrome, log in at flightradar24.com.
2. Press F12 → **Network** tab → trigger a login (or reload and find the
   `login` request) → open its **Response**: the JSON contains
   `userData.subscriptionKey` (a short string) and `userData.accessToken`.
3. Create the folder `%LOCALAPPDATA%\fr24\fr24\` and save `fr24.conf` there:
   ```ini
   [global]
   subscription_key=<paste the subscriptionKey value>
   ```
   Our scripts read only this key and log in with it directly — no other
   lines are needed.
4. **Traps (all learned the hard way):**
   - Do **not** also fill in `username=`/`password=` — when both credential
     pairs are present, the library prefers username/password, and that
     route is bot-blocked (HTTP 403).
   - The browser's `grpc.device-id`, the `cuid`, Firebase keys and XSRF
     cookies are **not** credentials. Only `subscriptionKey` works.
   - **Never** share `fr24 auth show` output or your config — it prints
     secrets in plaintext.
   - The access token (JWT) expires after ~a month. If downloads start
     failing with auth errors: log out of FR24 in the browser, log back in,
     and refresh `subscription_key` from the fresh login response.

## 4. Phase 3 — Enumerate flight lists

This discovers *which flights exist* (per aircraft tail) before downloading
anything. In `(fr24env)` on Windows, for each active tail:

```bat
python fetch_fr24.py --reg 5X-KOB --since 2026-09-30
```

- It pages backwards from now until actual departures pass `--since`,
  dedupes page overlaps by `flight_id`, and writes `flightlist_<REG>.csv`
  (columns: `flight_id,number,callsign,icao24,registration,typecode,
  origin,destination` (ICAO), `status,STOD,ETOD,ATOD,STOA,ETOA,ATOA`).
- Active tails in Oct 2026: `5X-EQU 5X-KDP 5X-KOB 5X-NIL ET-APL ET-AOU`
  (5X-CRN was inactive in the window; 5X-KNP was AOG with no list). Adjust
  to the fleet of the day.
- Zip the CSVs as `FlightLists.zip`, upload/commit to the repo, and extract
  into `work/flightlists/`. Only pick **arrived** flights downstream: a
  flight still in the air has an empty `ATOA` and incomplete playback —
  the target builders already enforce this.

## 5. Phase 4 — Build a download target list (pick one recipe)

Targets CSV columns: `flight_id_hex,number,callsign,date,from,to`
(only `flight_id_hex` and `number` are strictly used by the downloader).

**Recipe A — bring the archive up to date (routine):**
```bash
python3 work/build_targets_uptodate.py 2026-10-22   # end date = yesterday
```
Reads `work/flightlists/`, writes `work/targets_uptodate.csv`: every
arrived UR flight with origin-local departure date in
`2026-09-01`..end-date (edit `START` in the script for a later era) whose
flight id is not already in the pool or in `work/targets.csv`.

**Recipe B — recover FTA-planned legs that have no track:**
1. From both months' `schedule_delays.csv`, collect rows with
   `state == no_track` into `work/missing_legs.csv`
   (cols: `month,date,flight,from,to,aircraft,sched_dep_utc,sched_arr_utc`).
2. `python3 work/match_missing.py` → writes `work/targets.csv`
   (recoverable flights: same number+route, ATOD within −240…+480 min of
   plan STD, archive ids excluded) and `work/match_report.csv` with the
   per-leg verdict (`matched` / `shifted` / `adjacent_rotation` /
   `not_found`). Legs with no FR24 flight within ±36 h on any tail **did
   not operate** — the FTA plans overstate the schedule (UR111 is planned
   near-daily, flown every 2–3 days). Do not widen the match window
   without re-auditing: ≈24 h "matches" are adjacent rotations.

**Recipe C — hand-picked flights:** write `picks.csv` with
`flight,date[,from,to]` (date = departure day in East Africa Time), copy
it next to the Windows scripts, and run `python pick_flights.py picks.csv`
— it resolves and downloads in one step (Recipe A/B need Phase 5 instead).

## 6. Phase 5 — Download the tracks (Windows)

```bat
python fetch_tracks.py targets_uptodate.csv --out tracks_out
```

- Downloads FR24 playback per flight id and writes repo-format
  `<NUMBER>-<hexid>.csv`. Existing non-empty files are skipped, so a run is
  resumable; 1.5 s between requests keeps it gentle. Expect
  `ok <file>: N points, <first> .. <last>` per line.
- A report of 0 points or a failure for one id is not fatal — re-run later;
  don't hand-edit the outputs.
- Zip the output folder and upload/commit it to the repo (root name doesn't
  matter, e.g. `tracks_new.zip`); extract the CSVs into `work/tracks_in/`.

## 7. Phase 6 — Merge into the archives

Run from the repo root in the sandbox environment:

```bash
python3 work/build_month_zips.py --check   # ALWAYS first; writes nothing
```

- **Downloads route (Recipe A/B):** expect `membership rule OK` for both
  months plus `new tracks added to pool: N`. Then run without flags:
  `python3 work/build_month_zips.py`. It MD5-dedupes the new tracks into
  the pool and rebuilds both month zips by the origin-local-date rule.
- **Fresh export route (Source A):** if a new `FR data.zip` was uploaded
  over the pool, `--check` will report `MISMATCH … only computed: […]`
  (the new flights) — that is expected. **Verify `only current` is empty
  for both months** (nothing would be lost), then run
  `python3 work/build_month_zips.py --force`. If `only current` is ever
  non-empty, STOP: the new pool is missing tracks the archive relies on;
  investigate before proceeding. `--force` refuses in that case anyway.
- **Extending coverage to new dates:** first edit the October window end
  in `MONTHS` inside `work/build_month_zips.py` (currently `2026-10-22`)
  and the matching day list `days = [...]` in
  `work/build_od_matrix_october.py`, and make sure Phase 7 inputs cover
  the new dates *before* the Phase 8 FTA join.

## 8. Phase 7 — Extend the reference inputs for new dates

Only needed when coverage grows beyond the dates already covered.

- **FTA plans:** transcribe day plans from
  fta.ugandairlines.com/utilization-plans (one plan per flight date;
  `?page=N`) into `work/fta_oct2026.csv`
  (cols `date,reg,flight,origin,dest,std,sta,status`; STD/STA are local
  times at origin/destination). Current files: `fta_oct2026.csv` = 1–19 Oct,
  `fta_sep2026.csv` = 1–30 Sep. Hoima is `KBG`/`KGB` in plans, `UGHO` in the
  flight log; D-suffixed flight numbers are normalised at join time.
- **METAR (for conditions):** drop Iowa State IEM ASOS extracts for HUEN
  into the month folder's `metar/` as `HUEN_YYYYMM_partN.csv`
  (fields `station,valid,drct,sknt,gust,vsby,tmpc,alti,wxcodes`).
  `work/build_conditions.py` uses whatever station files are present;
  only Entebbe is covered so far.
- **NOTAMs (optional refresh):** build a new
  `work/notams_snapshot_YYYYMMDD.csv` (UCAA AIM PDF at
  aim.caa.co.ug/pdf/notam.pdf for HUEN; speedbird.online/notam?<IATA> for
  the BA-served outstations), then `python3 work/build_notams.py` — it
  auto-picks the newest snapshot and splits by validity overlap. Snapshots
  only see current/upcoming notices; expired ones are unrecoverable, which
  the month `notams.md` files state.
- **Waypoints (static):** `work/East African FIR.csv` →
  `python3 work/build_waypoints.py` → `waypoints.csv` in both folders.
  Rarely changes.

## 9. Phase 8 — The rebuild cascade (exact order)

Run from the repo root. Steps 1–2 then 3–4 then **1–2 again** — the FTA
join appends tail rows that only the second rebuild attaches.

```bash
python3 work/rebuild_month.py "UR SEPTEMBER 2026" "UR September flights.zip"
python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"
python3 work/build_september_fta.py
python3 work/build_october_fta.py
python3 work/rebuild_month.py "UR SEPTEMBER 2026" "UR September flights.zip"
python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"
python3 work/build_conditions.py "UR SEPTEMBER 2026"
python3 work/build_conditions.py "UR OCTOBER 2026"
python3 work/build_od_matrix_october.py    # October only; needs reportlab+openpyxl
```

- `rebuild_month.py` rewrites manifest/flights/fleet/triangle/runway/
  coverage artefacts from the month zip; it reads but never overwrites
  `tails.csv`. September tails are frozen FR24-app rows; October's are app
  history + FTA plan-assigned rows appended by `build_october_fta.py`
  (a plan-assigned tail can differ from the tail that flew — accepted
  convention, stated in the docs).
- FTA delay basis: actual = takeoff/landing, so dep delay includes
  taxi-out (~15–30 min at EBB). Labels: early <0, on-time 0–15,
  delayed 16–60, heavily >60 min.
- `build_od_matrix_october.py` needs `reportlab` and `openpyxl`
  (`pip install reportlab openpyxl`; in the Arena sandbox use
  `pip install --break-system-packages …` and reinstall each session).
- **Docs pass (manual, every cascade):** the FTA builders write a bare
  `data_gaps.md`. Before calling any remaining no-track leg "did not
  operate", re-verify it against fresh flight lists (Recipe B evidence).
  Then refresh the counts in both folders' `README.md`, `SUPPORTING.md`,
  `punctuality.md`, `schedule_delays.md`, `runway_usage.md`,
  `weather_analysis.md`, `triangle_routes.md` — grep the old totals
  (flight counts, matched counts, zip sha256s, date ranges) and replace.
  Sanity: `flights.csv` rows == month zip entries; FTA
  observed + no_track == operating legs.

## 10. Phase 9 — Website

```bash
python3 website/build_data.py     # regenerates website/data.json
```

Update the header line in `website/index.html` (flight count + date span)
to match the new totals, then preview:

```bash
cd website && python3 -m http.server 8000   # → http://localhost:8000
```

Rerun after **every** dataset update; the site reads the month folders,
nothing is fetched live.

## 11. Phase 10 — Commit, push, PR

- Work happens on the session branch (`arena/…-fr24`); push only there:
  `git push origin <branch>`. Commit data and code in focused commits;
  never run git operations in parallel.
- Arena sandbox quirk: the local branch can be silently reset between
  sessions — after `git fetch`, compare `git log --oneline -1 HEAD` with
  the origin branch tip before committing, and fast-forward/reset to it.
- Update PR descriptions with
  `gh api -X PATCH repos/jonathanbyakagaba/FR24/pulls/<N> -F body=@file`
  (`gh pr edit` is broken in this environment).

## 12. Troubleshooting (every trap we hit)

| symptom | cause / fix |
|---|---|
| FR24 returns 403 for every request | plain HTTP-client fingerprint is bot-blocked. Use `fr24==0.4.0` + `CurlAsyncClient` (the pinned setup in §2). Credentials are not the problem. |
| Login works in browser, 403 in script | same fingerprint issue; also check both credential pairs aren't filled in `fr24.conf` (username/password wins and fails). |
| "Is the cuid / device-id the key?" | No. Only `userData.subscriptionKey` from the login response. |
| Windows: `ZoneInfoNotFoundError` | `pip install tzdata` in the venv. |
| `flight_list` dies with `KeyError: 'data'` while paging | paging must re-anchor `timestamp` to the earliest STD of the previous batch — already implemented in `fetch_fr24.py`; don't simplify it. |
| Playback empty for a target | flight still airborne when listed, or wrong id. Re-enumerate lists and rebuild targets. |
| A track's date looks off by a day | overnight sectors: month/date attribution is origin-local (§0 rule 2), e.g. 21:42Z LUN departure = same local date. Not an error. |
| `--check` aborts after a fresh zip upload | expected: additions-only mismatch → verify `only current` empty → `--force` (§7). Non-empty `only current` = genuine data loss risk; stop. |
| Sandbox `curl` can't reach FR24 / FTA / IEM (SSL errors) | FR24 only from the Windows machine; FTA/IEM pages via the browsing tool. This is environmental, not a data problem. |
| `reportlab`/`openpyxl` import fails | (re)install; sandbox wipes pip packages between sessions. |
| Tempted to dedupe by filename or widen match windows | don't (§0 rule 1; §5 Recipe B). Filename dedupe loses distinct tracks; >12 h matches are adjacent rotations. |

## 13. Where things stand (2026-10-23) & pending

- Archives as committed: pool 1,239 tracks cascaded (Sep 640 flights,
  Oct 473 flights, 1–22 Oct); website 1,113 flights, 1 Sep – 22 Oct.
- The 2026-10-23 fresh export (1,239 tracks, commit `4947071`) has
  been absorbed: `--check` verified a pure superset (+62 tracks incl.
  Oct 20–22 coverage, nothing lost), the October window was extended
  to 2026-10-22, FTA plans and HUEN METARs extended, and the full
  cascade + website rerun. All 58 remaining no-track legs are
  classified in `work/gap_verdicts.csv` (53 did not operate, 2
  operated with tracks outside the join window, 3 operated and
  downloadable).
- `work/targets_uptodate.csv` regenerated after the cascade: 15
  flights (UR207 of 2026-09-01, the 3 recoverable October legs, 11
  flights that arrived 23 Oct) — the current residual download list.
  `work/pick_flights.py` remains the hand-pick route.
- Security debt: rotate the browser FR24 login (logout/login) and refresh
  `subscription_key` in `fr24.conf` (§3) — a JWT was exposed in plaintext
  during the original auth debugging.
