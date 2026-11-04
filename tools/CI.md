# CI: how the build runs by itself

One workflow, `.github/workflows/fr24-nightly.yml`, and two programs: `tools/fetch_fr24.py` (asks
Flightradar24 for tracks) and `tools/ci_run.py` (runs the build in the order the README recipe
gives, and nothing else). No pip install: the chain is standard library only.

## What runs, and when

| trigger | what happens |
|---|---|
| schedule 04:10Z and 16:10Z, daily | fetch the flights whose trails still exist, ingest, rebuild every derived table, commit what moved |
| push touching `FR data.zip`, `work/**`, `tools/**` | rebuild from the archive as pushed — the hand-uploaded export still works and needs no re-run |
| **Run workflow** → `since`/`until` | fetch a chosen window (a backfill while the days are still young) |
| **Run workflow** → `skip_fetch` | rebuild only, asking Flightradar24 for nothing |
| **Run workflow** → `close_month=YYYY-MM` | `work/close_month.py --force` for that month, then commit |

Two runs a day rather than one, because the fleet's banks are ~10 hours apart and a trail is only
worth fetching while Flightradar24 still holds it.

## The fact the whole design rests on

**A trail is not history.** `data-live.flightradar24.com/clickhandler/?flight=<id>` returns the
positions the map is still buffering. Measured on 31 Oct 2026, `UR209`: 30 Oct 260 fixes ✓, 29 Oct ✓,
28 Oct ✓, 27 Oct ✓, **26 Oct empty, 25 Oct empty, 24 Oct empty**. About four days.

Consequences, all of them deliberate:

- A scheduled job loses nothing. A job that stops for a fortnight loses that fortnight permanently.
- `fetch_fr24.py` prints `empty trail — too old to fetch` rather than reporting nothing, because "we
  were too late" and "the flight did not happen" look identical otherwise. The 16–25 Oct hole in this
  archive is exactly that: unrecoverable from the free endpoints, and only the account's own export
  can fill it.
- `already-held` ids are skipped by reading the filenames in `FR data.zip` (`UR110-420b1d5b.csv` *is*
  the flight id), so a re-run is cheap and a resumed backfill is exact.
- Requests are one per flight number plus one per new flight, 2.5 s apart, with backoff on 429/5xx —
  a 429 was seen at 1.2 s, so do not lower `--sleep`. These are the endpoints the public web page
  uses; a few hundred polite requests a day is what a human clicking would spend. If the operator
  ever gets Flightradar24's own API key or CSV feed, `fixes()` and `listings()` in
  `tools/fetch_fr24.py` are the only two functions that have to change.

## What CI never touches

- **The human layers.** `app_status.csv`, `punctuality.*` and `schedule_delays.*` come from
  screenshots and timetable OCR that only a person can take. They are copied forward, and the run
  ends with a warning when the newest capture lags the newest fix by more than `--stale-days` (5):
  `::warning:: human captures are N days behind the data — app flags and timetable delays are copied
  forward`. A green run with that warning means the flags are not to be trusted for the new days; it
  never means "on time".
- **Nothing is deleted.** `publish_layers` still refuses a layer smaller than the published one, so a
  run that lost input cannot shrink the repository; `--allow-shrink` stays a human decision.
- **A month is not frozen by a schedule.** `close_month.py` moves a month's tables into a folder that
  later builds stop rewriting; that is a button press with the month typed in, after checking
  `date_coverage.md`.

## What CI cannot refresh, and how it says so

The checkout is the repository, so anything not committed here is absent in CI. The run prints the
reason and carries on — a skip is never a blank, and never a failure:

| needs | committed? | CI behaviour |
|---|---|---|
| `weather/raw*`, `weather/metar*` (7–22 MB of IEM dumps) | no, regenerable | `weather.py` still runs (it fetches); `metar_split.py` reports `SKIPPED, needs weather`, and `metar/` + `reference/weather_*.csv` stay as published |
| `work/screens_*`, `work/records*`, `work/status_dots.csv` | yes, they are small | `final.py`, `app_status.py`, `schedule_delays.py` run on them; without them the same three lines say `SKIPPED, needs …` |
| `work/fta/` (the plan crawl) | no | `missing_flights.py` and the FTA-side readers are outside the nightly chain entirely — that crawl stays a manual `work/fta/fta_pull.py` |
| `work/rwy/runways.csv` | yes (3.8 MB) | the runway measurement needs it; without it `runway_usage.csv` is refused by `publish_layers`, not silently shrunk |

If you want CI to be able to rebuild the weather tables from scratch, commit `weather/metar_2026-*.csv`
(~7 MB) and the `metar` step stops skipping.

## Reading a run

`ci_run.py` prints one line per step — `ok`, `FAILED`, or `SKIPPED, needs work/…` — and writes the
step summary with counts, the number of published files touched, and the list of them. Exit code is
non-zero only if a step failed, never because something was skipped, so a checkout without the
screenshot inputs still goes green and says which layers it left alone.

## Turning it on, once

1. Upload this folder and `.github/workflows/` to `main` (the code has to be in the repository for
   the runner to have it). Also commit the month folders' tables at the same time, or the first run
   will report a diff of everything.
2. **Actions → fr24-nightly → Set up schedule** if the workflow arrives by folder upload — GitHub only
   enables a schedule for a workflow that exists on the default branch as a committed file. Schedules
   also switch themselves off after 60 days without a push, which a twice-daily job prevents.
3. Run **Run workflow → skip_fetch** once as a smoke test: it rebuilds from the archive as pushed and
   should commit either nothing at all or only the README's sizes.
4. Watch the next 04:10Z run: its summary should say `fetch` ok, and the commit message carries the
   UTC minute of the build.

## Running it by hand, in this workspace

```
python3 tools/fetch_fr24.py --since 2026-10-27 --until 2026-10-31 --dry-run   # what is still in time
python3 tools/fetch_fr24.py --since 2026-10-27 --until 2026-10-31             # writes work/ci_capture/
python3 fr24_update.py --zip "work/ci_capture/FR data.zip" --month auto        # the usual chain from here
```

`work/ci_capture/` survives between runs on purpose — that is where a part-finished backfill sits —
which is also why CI always starts with an empty one and why the folder is gitignored. A capture left
lying around locally becomes the ingest source of the next `ci_run.py`, and `git log` will not tell
you that: `capture_manifest.json` inside it does.


## Where the night's flight list comes from

`tools/fetch_fr24.py --source board` (the default, and what the schedule uses) asks the operator's own
utilization board at `fta.ugandairlines.com` for the day: the index page names the board
("Tuesday, 3rd Nov, 2026"), its `/<uuid>/excel` sheet gives the flight numbers actually on the day —
21 of them on 3 November — and each number is then looked up on Flightradar24 by `flight/list.json`
and, while its trail is still young enough, captured.

If the board does not answer, the next source is the flight numbers FR24 itself reported on a previous
run (`capture_manifest.csv` in the out dir). A person's upload is only ever read on an explicit
`--source log`, and `work/ci_run.py` refuses to rebuild the archive at all when there is no capture
unless `--allow-archive-fallback` is passed. A fetch where nothing answered exits 4 and the workflow
fails the run rather than committing a no-op: a red run with a reason beats a green run that quietly
rebuilt stale data.

Steps that only write prose reports (`missing`, `gaps`, `gap_report`, `no_code`, `triangles`,
`runway_report`) are soft: a report that cannot parse another pipeline's markdown warns in the step
summary instead of stopping the commit of everything else.

## Closing a month, and telling you about it

`close_month.py` used to need a person typing `2026-10` into the Run-workflow box. Now the freeze
step asks `tools/month_to_close.py`, which prints the oldest month folder that is (a) older than this
month and (b) missing its `.closed` marker, and does nothing if there is no such folder. The live
month is exempt, so a run that captured nothing does not freeze October out of impatience — the run
that lands November data closes October by itself, in the same run. `close_month` as a manual input
still wins when someone wants a month shut the evening it ends.

The `notify` job posts one comment on the open issue titled **FR24-status** (created on first use)
with the captured/seen/too-old counts, the window, how many tables were written and whether they were
committed — but only when something happened. A green run that fetched nothing and committed nothing
stays silent, which is the normal look of a push-triggered run. Its `if: always()` also means a red
build reports itself, with the fetch exit code. Subscribe to that issue once and each comment arrives
by email; GitHub's own Actions mail is only for failures unless you untick "Only notify for failed
workflows" in Settings → Notifications → System → Actions.

`tools/capture_summary.py` exists because a here-doc cannot sit at column zero inside a `run: |`
block: it turns the fetcher's `capture_manifest.json` into step outputs, and prints zeros with the
"no fetch this run" window when there is no manifest to read.


## Weather, from aviationweather.gov (`tools/fetch_awx.py`)

Runs on the same two scheduled/dispatch events as the FR24 fetch, and is soft: weather never blocks
the data build. Measured facts the code depends on, all from 3 Nov 2026:

* History is capped at ~400 records per station (`hours=240` and `hours=336` return the same 400),
  about **8 days** at two observations an hour. Deeper than the FR24 trail horizon, so a leg's
  departure and arrival METARs are always retrievable on the night they matter — and, as with the
  trails, October 18-29 is beyond both services.
* Asking for 14 stations in one request returned 44 rows in total; one station alone returned 48.
  The cap is per **request**, so each station is queried separately.
* Coverage of the network: Entebbe is **HUEN** (not EBBU, which is not in their station list),
  Harare **FVHA**, Mogadishu **HCMM**, Juba **HJJJ**. Lusaka (FLLS), Harare (FVHA) and Juba (HJJJ)
  returned no observations at all in a 96-hour window — an empty answer from the service, not a
  failure; the IEM feed behind `metar/` is what covers those three. 12-13 stations did report, and
  13 of 16 had a live TAF.
* `airsigmet` and `gairmet` are the only products here that cannot be fetched later: they show what
  is live at this moment, worldwide, with polygons and valid-from/valid-to. Hence the nightly
  snapshot into `reference/weather/awx_hazards_<date>.json`, merged across the day's two runs and
  deduplicated on `(icaoId, receiptTime, alphaChar)`. Their `icaoId` is a **FIR**, not an aerodrome,
  so matching a hazard to a leg is a point-in-polygon or FIR-membership job for the analysis step,
  not a station-name join; the run only reports how many happened to name one of our codes.
* The map layers behind `aviationweather.gov/gfa/#obs` (icing, turbulence, jet streams, freezing
  levels) are served from `api.aviationweather.gov`, which did not resolve from the sandbox this was
  written in. They are plausible additions and deliberately not relied on here.

What lands in the repo is two files a day: `awx_metars_<date>.csv` (station, obs time, temp, dew
point, wind, gust, visibility, QNH, derived ceiling, ICAO flight category, and the raw METAR) and
`awx_hazards_<date>.json`. Everything else the fetcher writes is scratch under `work/awx/`, which
`.gitignore` now covers.

## When it runs

09:10Z and 21:10Z, which is **12:10 and 00:10 in Entebbe time** (Uganda is UTC+3, no DST). Two runs
a day is what keeps us inside the four-day trail horizon; GitHub delivers scheduled runs hours late,
which costs nothing as long as it is the same day.


## The paths themselves, outside the zip (`tools/publish_paths.py`)

The nightly build now publishes `flight_paths/` at the top of the branch: every trail as a plain CSV,
named exactly as it is inside `FR data.zip`, plus an `INDEX.csv` with file, flight, FR24 track id,
callsign, fix count, first and last observation, bytes and sha8. A folder of a thousand files is only
navigable with a table of contents, and a CSV is only reviewable on github.com if it is not inside an
archive. Measured on the branch as it stands: 1,001 archive tracks and 439,244 fixes, observation
dates 2025-05-04 to 2026-11-03, about 32 MB of text where the zip holds 9.2 MB compressed.

The zip stays. Ten scripts read the archive through `repo_layout.archive()` and `fr24_update.py`
rebuilds it as the de-duplicated, byte-reproducible index, and `fetch_fr24.py` uses its id list to
skip trails already held. What changes is which artefact is *for people*: `flight_paths/` is written
after the ingest, so it mirrors the cleaned archive, and files are only touched when their bytes
differ — a night that captures nothing leaves the folder and the branch alone. `--prune` exists for
the case where a source stops naming a file; it is off by default, so nothing here ever deletes
published history on a bad afternoon.

`paths` is a hard step, deliberately: a run that published tables without their paths is the kind of
half-state this build has spent its life avoiding. Flip it into `SOFT` in `tools/ci_run.py` if that
trade is wrong for you.
