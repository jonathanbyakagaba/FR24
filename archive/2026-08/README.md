# August 2026

Uganda Airlines' August 2026 operation: **619 flights**, **1,323 h 17 min**
airborne and **1,049,216 km** flown — the busiest month in the archive so far,
and the first past a million kilometres.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | 01AUG26 – 31AUG26, by local departure date |
| flights logged | 619 |
| airborne | 1,323 h 17 min |
| distance flown | 1,049,216 km (summed from the track positions, complete tracks only) |
| city pairs | 26 directional / 14 undirected |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL |
| types | CRJ900 (455 flights), 737-800 (120), A330-800 (44) |
| median flight | 1 h 23 min |
| busiest days | 02, 09 and 16 August, 27 flights each |
| quietest day | 13 August, 13 flights |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | 620 raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual and scheduled times, point count, SHA-256 |
| `flights_2026-08.csv` | one row per flight leg — 619 rows — with off/on times in UTC and local, airborne minutes, flown distance, max altitude, whether the track is complete, and where its times came from |
| `aeroroutes_2026-08.md` | the month's log in AeroRoutes notation, with a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

Regenerate the last three with:

```bash
python3 work/fr24_tracks.py --month 2026-08
```

## Where the data came from

Flightradar24's tracks, sliced out of the operator's `EBBs-FR24` movement
enumeration at commit `47e7201c5372` and copied here unchanged by
`work/import_ebbs_month.py`. Registrations and types are the movement board's
own; the route on each line is read off the track.

## A check on the numbers

Across the 612 flights timed from a complete track, those times agree with the
movement board's own actual times to a median of **1.3 minutes** at departure and
**2.9 minutes** at arrival (worst case 14 and 20 minutes).

## What the month looks like

- **Nairobi carried the month**: 66 sectors each way, roughly two rotations a day.
- **The A330-800 came back** to 47 flights — up from 19 in July — after the 787-8
  covered part of the London run the month before; no 787 appears in August.
- **Johannesburg and Dar es Salaam ran daily**, 35 sectors each, with Harare,
  Lusaka, Mombasa, Mogadishu, Bujumbura and Juba sharing the CRJ900s.
- **Three Mumbai legs have a hole in the middle of the track** — UR430 on 1, 8
  and 22 August, 62, 106 and 80 minutes long. They are logged as the single
  flights they were, with the gap noted under *Track coverage*.

## Coverage, and what to be careful with

- **613 of 619 flights have a track that runs end to end.** The other six are
  listed under *Track coverage*: three have a hole en route, so their distance is
  understated, and three are logged with times from the movement board's actual
  times.
- **One export belongs to July** (departure on 31 July, arrival on 1 August) and
  is logged there, by departure date.
- **Times are airborne times**, local at both ends, not the schedule; `(+1)`
  marks next-day arrivals.
- **Flown distance** sums the great-circle steps between recorded positions; it
  understates the true path and is not the straight-line figure in
  `reference/route_distances.csv`.

## Licence

The track data is Flightradar24's, kept here for the operator's own analytical
use within FR24's terms, the same basis on which it sits in `EBBs-FR24`. The
derived tables and the log are the operator's own.
