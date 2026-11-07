# FR24 — Uganda Airlines flight archive

A month-by-month archive of Uganda Airlines (UR / UGD) operations, rebuilt from
Flightradar24 track exports and written up in the [AeroRoutes](https://www.aeroroutes.com/)
notation used for airline route listings. It maintains itself: a nightly job
harvests the fleet's flying from the Flightradar24 API, files each track into its
month and rebuilds the month, so the archive stays current without anyone
exporting a file.

```
reference/           static lookups: airports, runways, time zones, fleet, route distances
archive/YYYY-MM/     one folder per month — the month's tracks, its leg table, its log
work/                the scripts that build the archive, and the one that repairs it
                     from the Flightradar24 API
state/               the sync's memory: which flight ids it has already looked at
tests/               tests and a synthetic export fixture (no real flight data)
```

## What is in the archive

Six months so far — June to November 2026, 2,948 flights and 6,340 airborne
hours. The month-by-month table, with each month's caveats in one line, is in
[`archive/README.md`](archive/README.md).

## The monthly folder

Every month lives in its own folder, `archive/YYYY-MM/`, and always holds:

| file | what it is |
|---|---|
| `tracks/*.csv` | the raw Flightradar24 exports, one file per flight, exactly as downloaded — never edited by hand |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual times, point count, SHA-256 |
| `flights_YYYY-MM.csv` | one row per flight leg: date, flight no, registration, type, origin, destination, off/on times in UTC and local, airborne minutes, distance flown, max altitude, track points, and the file it came from |
| `aeroroutes_YYYY-MM.md` | the month's log in AeroRoutes notation, with a route summary, a rotation table and a note on every anomalous track |
| `rotations_YYYY-MM.csv` | one row per airframe rotation: the airport chain it flew, the sectors with a track, and any sector the record is missing |
| `sources.json` | checksums and counts for everything the build read |
| `README.md` | what the month contains, what it does not, and anything odd about it |

The last five are derived and never hand-edited; regenerate them at any time:

```bash
python3 work/fr24_tracks.py --month 2026-06
```

## Rotations, and the sectors behind them

A flight log built from point-to-point sectors loses the thing a rotation is: one
airframe, one day, one chain of airports. Uganda Airlines' widebody flies
Entebbe–Harare, tags Harare–Lusaka–Harare, then Lusaka–Entebbe. If the movement
enumeration catches the first and last sector and not the tag, the day reads as
two unrelated legs that happen to share an aircraft.

So the build chains each airframe's legs, and where the aircraft lands at one
airport and is next seen at another, it keeps the sector in between — because the
aircraft demonstrably flew it — and marks the airport it could only have reached
that way:

```
EBB–HRE  UR720  →  HRE–[LUN]  →  LUN–EBB  UR721      one rotation
```

Every month carries that as `rotations_YYYY-MM.csv` and as the *Rotations* table
in its log; the bracketed airport is the missing hop. A rotation is the airframe's
flying day — grouped on Entebbe's clock, turning over at 04:00 local so a night
rotation that lands after midnight still belongs to the day it left on. Across the
archive that is 747 rotations, 184 of which carry at least one such hop, 211 hops
in all: almost entirely the Harare–Lusaka tag and the Zanzibar–Kilimanjaro hop,
with a handful of one-offs. Six of them carry a question mark, which is the model
saying the record contradicts itself — the next leg is under way while the
aircraft should still be on the ground — and declining to claim the sector.

Hops are a claim about the record, so they are made narrowly: only where the two
airports differ, the distance is a plausible sector, and the time on the ground is
long enough to fly it. Nothing is claimed where the aircraft lands and later leaves
the *same* airport — a hole like that is a rest, or a flight nobody can prove, and
`gaps_YYYY-MM.csv` leaves it alone.

### Filling the holes

`work/fetch_fr24_tracks.py` closes them from the [Flightradar24 API](https://github.com/abc8747/fr24)
rather than from the enumeration, using the airframe's flight list over the hole to
find the flight, then its playback to write the track:

```bash
python3 work/fetch_fr24_tracks.py --month 2026-09 --gaps-only    # what is missing
python3 work/fetch_fr24_tracks.py --month 2026-09 --dry-run      # what it would ask for
python3 work/fetch_fr24_tracks.py --month 2026-09                # fetch it
python3 work/fr24_tracks.py --month 2026-09                      # rebuild: the hop closes
```

It also takes a reconciliation sheet — a list of `Flight`, `Sector`, `Tail`, `Date`
and `Planned_STD` rows — with `--worklist`, so holes that the chain cannot see
(a service skipped for a whole day, with no airport change to betray it) can be
chased the same way.

Fetching needs credentials — `fr24_username`/`fr24_password`, or
`fr24_subscription_key`/`fr24_token`, in the environment or in
`~/.config/fr24/fr24.conf` — and the client with an HTTP backend,
`python3 -m pip install "fr24[curl]"` (also in `requirements.txt`). Nothing else
in the archive needs it: the builder and the tests run on the standard library.
Fetched tracks are added to `tracks/manifest.csv` with `source = fr24-api`, so a
recovered sector never passes for one that came out of the enumeration.

### Closing the backlog, night after night, until it is empty

Harvesting keeps the *new* flying coming in; it does nothing for history. A
rotation that landed in July with a hole in the middle stays holed forever, and
no amount of tonight's flying makes it whole. So the same nightly job also runs
`work/sweep_gaps.py`, which walks **every month in the archive** — June onward,
not just this one and last — and fetches the sectors the rotation chains prove but
the record does not hold. Nothing is written off for being old: it asks, and the
backlog shrinks until there is nothing left to ask about.

```bash
python3 work/sweep_gaps.py --plan              # the backlog, month by month
python3 work/sweep_gaps.py --dry-run           # what it would ask for tonight
python3 work/sweep_gaps.py --minutes 25        # what the nightly job runs
```

Three things make it safe to leave running:

- **A clock, not a head-count.** It keeps asking until its minutes are up — 25 by
  default, `SWEEP_MINUTES` to change it — so the job always finishes inside its
  timeout and the API is never hammered. Whatever is left is reported as *left for
  tomorrow* rather than quietly dropped. `--budget` remains as a hard cap on the
  count, and `SWEEP_BUDGET` sets it; left unset, the clock is the only limit.
- **A reach that is measured, not assumed.** Flightradar24 keeps a record whose
  depth depends on the subscription — 7 days on Basic, 90 on Silver, 365 on Gold,
  three years on Business — and the archive no longer guesses at it. The sweep
  asks about every sector the chains prove missing, and `state/sweep.json` records
  the oldest sector the record actually served. Buy a deeper plan and the backlog
  begins filling overnight with nothing to configure. `--history-days` /
  `FR24_HISTORY_DAYS` still exist for anyone who wants a cut-off; the default, 0,
  means none.
- **A memory.** `state/sweep.json` counts the tries against each sector. Inside
  the record's seven-day window a sector gets three attempts; older than that it
  gets one honest ask — one answer is all the record will ever give — and is then
  parked, with the gap sheet saying why instead of listing it as fetchable.
- **Recomputation, not bookkeeping.** The backlog is derived from the tracks on
  disk every night, so filled sectors leave the list by themselves and a sector
  that only became visible once a neighbouring track arrived appears without
  anybody adding it.

Each month keeps a `gaps_YYYY-MM.csv` listing what is still missing, with a status
column: `fetchable`, `skipped (hole too short …)`, `skipped (no ICAO code …)`,
`skipped (asked once — older than the 7-day record the plan keeps)`, or
`skipped (not in the Flightradar24 record after N tries)`. The night's email and
the issue comment carry the running total — *"1 sector still missing, 4 given up
on"* — so the number in your inbox is the archive as it actually stands.

**What that means for June–October.** The 199 sectors behind the seven-day
window — the LUN–HRE and ZNZ–JRO tag legs of the summer — had been written off as
*out of reach* without a single request being made for them, on the strength of an
assumption about the subscription. That assumption is gone. The next sweep asks
about all of them, in one night if the clock allows and over several if it does
not: whatever the record still holds returns as a real track and closes the hole,
and whatever it does not is parked after one attempt, with the reason in the gap
sheet and the count in the email. Either way the answer is the archive's own
measurement rather than a guess — and if a deeper Flightradar24 plan is bought
(Gold reaches all of them), the same sweep starts filling them in with nothing to
change.

### Keeping it current, all year round

`work/sync_fr24.py` turns that into a loop, and
[`.github/workflows/sync.yml`](.github/workflows/sync.yml) runs it nightly at
01:30 UTC — half an hour after the flying day turns over at 04:00 in Kampala:

```yaml
on:  schedule: [{cron: "30 1 * * *"}]
```

A night's work, in order:

1. **Ask what flew.** For each airframe in `reference/fleet.csv`, list its flights
   since the end of the last run. Entebbe's arrival and departure boards are read
   as well, which is how a new tail or a wet lease announces itself instead of
   someone editing the fleet file.
2. **Skip what is already here.** `state/ledger.csv` remembers every flight id
   looked at, and the track files carry their flight id in their name, so a night
   normally downloads twenty or thirty playbacks, not thousands.
3. **File each track by month.** The playback is written in the archive's own
   layout and dropped into `archive/YYYY-MM/tracks/` by its departure month, with
   a manifest row carrying `source = fr24-api`.
4. **Rebuild those months**, drafting a `README.md` if the month is new and
   regenerating the index table in [`archive/README.md`](archive/README.md) — both
   only ever touch what is theirs, so hand-written prose survives.
5. **Commit straight to `main`** — no pull request, no review gate — only if
   something changed, with the months named in the message. If a hand-made push
   lands mid-run the job rebases onto it and retries rather than fail the night.
6. **Fail loudly.** Exit `3` if flights were new and none produced a track, `4` if
   more than a fifth of the fetches failed. The workflow then opens (or comments
   on) a labelled issue: the failure mode that matters is not an error, it is a
   job that quietly stops finding anything while still reporting success.

Why by airframe rather than by airport: an enumeration built from Entebbe's
movements cannot see a sector that never touches Entebbe, which is exactly what
went missing. Asking for the aircraft instead brings the Lusaka–Harare tag and
the Zanzibar–Kilimanjaro hop in as legs in their own right, so most nights there
is no hop left to fill. The gap filler still runs afterwards, for the current and
previous month, as a safety net.

The job checks out `main`, runs the code that is on `main`, and pushes back to
`main` — a manual dispatch from a feature branch runs main's code too, so nothing
unreviewed can sneak into a nightly commit.

**Turning it on** takes two things, once:

1. Repository → Settings → Secrets and variables → Actions: add
   `FR24_SUBSCRIPTION_KEY` and `FR24_TOKEN` (the licensed API), or
   `FR24_USERNAME` and `FR24_PASSWORD`.
2. Merge the workflow to `main` — GitHub only schedules workflows that exist on
   the default branch. Nothing else: after that the archive grows by itself.

One thing to check on the way: if `main` is protected against direct pushes, allow
the GitHub Actions bot to bypass it (Settings → Branches → *Allow specified actors
to bypass*), otherwise the nightly commit is rejected — the job says so in its log
and opens an issue rather than failing silently.

### Hearing from it

A job that runs unseen is a job you stop trusting, so every run reports itself.
There are two routes, and the first needs no password at all.

**The issue log — nothing to set up.** Each night's summary is posted as a comment
on an issue — the existing *FR24-status* thread if there is one, otherwise a new
*Nightly sync log* issue the first run creates. GitHub sends the
notification, so it reaches you however your notification settings say — email,
phone, or the bell — and the issue itself becomes a running history of the archive.
It is on by default whenever no mailbox is configured. To stop it, set the
repository variable `SYNC_LOG` to `off`.

**Real email — a mailbox of its own.** Add two repository secrets (*Settings →
Secrets and variables → Actions*):

| secret | what it is |
|---|---|
| `SYNC_MAIL_USER` | the mailbox it sends from, e.g. `you@gmail.com` |
| `SYNC_MAIL_PASS` | an app password for it |

The mail goes to that address unless `SYNC_MAIL_TO` says otherwise. The issue log
keeps running alongside it, so there is always a record in the repository; set the
variable `SYNC_LOG=off` if you would rather have only the mail.

**Running it by hand is one click, with nothing to fill in.** Actions → *sync* →
**Run workflow** → the green **Run workflow** button, leaving every field alone:
the defaults *are* the nightly run. The form has three fields and only two of them
are ever useful — **dry_run** looks without fetching, **mail_test** sends one test
email and stops, and the single text field is a backfill start date.

A missed night costs nothing either way: every run looks **seven days back**
rather than resuming where the last one stopped, so whatever a dropped schedule
skipped is picked up by the next one. Re-listing a week costs the same one page
per airframe as re-listing a night — the flight list is paged backwards from now —
and the ledger skips the days already on disk in milliseconds.

**Checking the mailbox takes ten seconds.** Same button, tick **mail_test**. That
job does nothing but send a test message with the same credentials and transport as
the real thing, and it fails rather than passing quietly if no credentials are
configured — so a green tick means an email really left. Two things it forgives:
the spaces Gmail puts between the four groups of an app password, and quotes
pasted around it.

**If Gmail will not give you an app password**, the usual reasons are:

- **2-Step Verification is off** — app passwords do not exist until it is on.
  They live at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords),
  or Security → How you sign in to Google → 2-Step Verification → App passwords.
- **A Workspace (work or school) account**, where the administrator has disabled
  app passwords, or **Advanced Protection** is enrolled — both remove the option
  entirely, and no setting on your side will bring it back.

Either way you are not stuck: use the issue log, or give the workflow credentials
from a mail service instead of Gmail. The script speaks SMTP, or an HTTP API:

| route | what to add | catches |
|---|---|---|
| issue log | nothing | always |
| Gmail / any SMTP | `SYNC_MAIL_USER` + `SYNC_MAIL_PASS` | needs an app password |
| Brevo, Mailjet (SMTP relay) | same two secrets, plus `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` | free tier, sender verified by email, no domain |
| Resend | `RESEND_API_KEY` | sends from `onboarding@resend.dev` to your own address without a domain |
| SendGrid | `SENDGRID_API_KEY` | single-sender verification, no domain |
| Mailgun | `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` | needs a domain |

The transport is chosen from whichever credentials are present, so there is
nothing to select. How chatty it is comes from the repository **variable**
`SYNC_MAIL_MODE` (*Variables* tab, not secrets):

| `SYNC_MAIL_MODE` | when it writes |
|---|---|
| `always` (default) | every run, including a quiet night with nothing new |
| `work` | only nights that fetched tracks, and any failure |
| `never` | not at all |

Failures also arrive as an issue of their own, so nothing depends on one channel.
The summary is built from `state/sync.json` — what ran, how much flew, which
months changed, the commit it landed, and a link to the run:

```
FR24 sync — ran clean · 31 tracks fetched · 2026-11

| | |
|---|---|
| window | 2026-10-30 13:00Z → 2026-11-06 13:00Z |
| flights | 74 seen, 31 new |
| tracks | 31 fetched, 0 failed |
| months | 2026-11 |
| on main | `a1b2c3d sync: archive/2026-11` |

[Run log](https://github.com/…/actions/runs/123)
```

`work/notify.py` is standard library only. With no credentials it prints the
message rather than sending it, a mailbox that refuses delivery never fails the
night's work, and a dry run reports in the log instead of either channel. To see
what it would say:

```bash
python3 work/notify.py --status success --format issue
python3 work/notify.py --status success --dry-run
```

**Backfilling** is the same script with a start date, either from a laptop or from
the workflow's *Run workflow* button:

```bash
python3 work/sync_fr24.py --since 2026-06-01 --ignore-state --max-pages 40 --pause 0
python3 work/sweep_gaps.py --minutes 0         # and every sector the chain proves missing
```

Run once over June–November that also repairs the holes the reconciliation sheet
listed — the numbered services the enumeration dropped, `UR120 EBB–JUB` and its
like — because a flight already on disk is skipped in milliseconds and a missing
one is simply fetched.

**What it costs.** A normal night is three to eight flight-list pages per airframe
and twenty to forty playbacks — a few minutes. A six-month backfill is about 3,000
playbacks and roughly an hour at the default pacing (`--pause 1.5`, `--delay 2`),
which is deliberately polite to the API. Playbacks the API will not serve are
retried for two nights and then left in the ledger as `no-track`, so a cancelled
flight cannot haunt the job forever.

**What it needs from you.** A Flightradar24 API subscription, and honesty about
its terms — the client is pointed at the licensed API, and the pacing is there to
stay inside its limits. Raw tracks run to about 16 MB a month (95 MB for the six
months here, ~190 MB a year), so plan on moving the oldest raw exports to release
assets or object storage once the repository passes a few hundred megabytes; the
derived tables, the logs and `sources.json` (with checksums) are small enough to
keep forever, and they are what the archive is actually for.

## Adding a month

A month now arrives by itself, one night at a time — there is nothing to do. The
manual route is still here for a month that predates the sync, or for tracks
gathered by hand.

1. Export the tracks. This repository takes the per-flight CSVs that the sibling
   `EBBs-FR24` project already pulls from Flightradar24; exports straight from
   **Playback → Export data** work the same way, one file per flight.
2. Lay them out with `python3 work/import_ebbs_month.py --source ../EBBs-FR24 --month YYYY-MM`,
   or drop the files into `archive/YYYY-MM/tracks/` yourself along with a
   `manifest.csv` describing them.
3. Run `python3 work/fr24_tracks.py --month YYYY-MM`.
4. Read the *Rotations* table in the log. If it reports hops, `python3 work/fetch_fr24_tracks.py --month YYYY-MM`
   fetches them where the credentials allow it; rebuild afterwards.
5. Write the month's `README.md` from the previous month's, updating the counts.
6. Add the month to the table in [`archive/README.md`](archive/README.md).

Raw exports are the bulky part: a track point every few seconds for 400-odd legs
is a few tens of megabytes. Under ~50 MB keep them in the repository so a month
stays self-contained; above that, park them in external storage and keep
`sources.json`, whose checksums let a copy be verified before a rebuild.

## AeroRoutes notation

The log follows the layout of an aeroroutes.com route listing:

```
**Entebbe – Johannesburg**
*eff 01JUN26* 5 weekly A330-800
UR713 EBB0900 – 1125JNB A338 135
```

A bold city pair gives the direction of travel, `eff` the first date the pair was
flown that month, then the weekly frequency and the equipment in words. Each flight
line then carries, in order: flight number, departure time and airport, arrival time
and airport, the ICAO type designator, and the days of the week flown
(1 = Monday … 7 = Sunday, `x` before a digit meaning "except"). Times are local at
each end and `(+1)` marks an arrival on the next day.

Because the times come from the tracks rather than a timetable, they are the times
the aircraft actually got airborne and touched down, not the airline's schedule.
That difference is deliberate: this is an archive of what flew.

## Reproducing the log

```bash
python3 -m unittest discover -s tests -v   # pipeline tests, no real data needed
python3 work/fr24_tracks.py --month 2026-06
```

The suite is standard library only, so the interpreter barely matters — which is
the point: `.python-version` records **3.12** as the intended version, and the
nightly job runs the tests on **both 3.11 and 3.12** so a machine that cannot get
3.12 is still testing the same code CI does. Nothing here needs anything newer
than 3.10.

The tests cover the rotation chain as well as the leg building, and stand a fake
Flightradar24 client in for the fetch script, so the repair path is exercised
without a subscription.

## Reference data

Everything the log borrows — airport city names and coordinates, local time zones,
registration-to-type mapping, great-circle distances — lives in `reference/`, and
`reference/README.md` records where each table came from and under what licence.
