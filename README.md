# FR24 — Uganda Airlines flight archive

A month-by-month archive of Uganda Airlines (UR / UGD) operations, rebuilt from
Flightradar24 track exports and written up in the [AeroRoutes](https://www.aeroroutes.com/)
notation used for airline route listings.

```
reference/           static lookups: airports, runways, time zones, fleet, route distances
archive/YYYY-MM/     one folder per month — the month's tracks, its leg table, its log
work/                the scripts that build the archive
tests/               tests and a synthetic export fixture (no real flight data)
```

## The monthly folder

Every month lives in its own folder, `archive/YYYY-MM/`, and always holds:

| file | what it is |
|---|---|
| `tracks/*.csv` | the raw Flightradar24 exports, one file per flight, exactly as downloaded — never edited by hand |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual times, point count, SHA-256 |
| `flights_YYYY-MM.csv` | one row per flight leg: date, flight no, registration, type, origin, destination, off/on times in UTC and local, airborne minutes, distance flown, max altitude, track points, and the file it came from |
| `aeroroutes_YYYY-MM.md` | the month's log in AeroRoutes notation, with a route summary and a note on every anomalous track |
| `sources.json` | checksums and counts for everything the build read |
| `README.md` | what the month contains, what it does not, and anything odd about it |

The last four are derived and never hand-edited; regenerate them at any time:

```bash
python3 work/fr24_tracks.py --month 2026-06
```

## Adding a month

1. Export the tracks. This repository takes the per-flight CSVs that the sibling
   `EBBs-FR24` project already pulls from Flightradar24; exports straight from
   **Playback → Export data** work the same way, one file per flight.
2. Lay them out with `python3 work/import_ebbs_month.py --source ../EBBs-FR24 --month YYYY-MM`,
   or drop the files into `archive/YYYY-MM/tracks/` yourself along with a
   `manifest.csv` describing them.
3. Run `python3 work/fr24_tracks.py --month YYYY-MM`.
4. Write the month's `README.md` from the previous month's, updating the counts.
5. Add the month to the table in [`archive/README.md`](archive/README.md).

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

## Reference data

Everything the log borrows — airport city names and coordinates, local time zones,
registration-to-type mapping, great-circle distances — lives in `reference/`, and
`reference/README.md` records where each table came from and under what licence.
