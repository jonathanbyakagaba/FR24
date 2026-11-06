# FR24 — Uganda Airlines flight archive

A month-by-month archive of Uganda Airlines (UR / UGD) operations, rebuilt from
Flightradar24 track exports and written up in the [AeroRoutes](https://www.aeroroutes.com/)
notation used for airline route listings.

```
reference/           static lookups: airports, runways, time zones, fleet, route distances
archive/YYYY-MM/     one folder per month — the month's tracks, its leg table, its log
work/                the scripts that build the archive, and the one that repairs it
                     from the Flightradar24 API
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

Where the fetch cannot run — a sandbox with no route to `flightradar24.com`, for
instance — the rotations still show the hole honestly, and
[`.github/workflows/fetch-fr24-gaps.yml`](.github/workflows/fetch-fr24-gaps.yml)
runs the same four steps on demand from a runner that does have the route, given
the credentials as repository secrets.

## Adding a month

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

The tests cover the rotation chain as well as the leg building, and stand a fake
Flightradar24 client in for the fetch script, so the repair path is exercised
without a subscription.

## Reference data

Everything the log borrows — airport city names and coordinates, local time zones,
registration-to-type mapping, great-circle distances — lives in `reference/`, and
`reference/README.md` records where each table came from and under what licence.
