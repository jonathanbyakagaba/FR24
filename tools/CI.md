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
