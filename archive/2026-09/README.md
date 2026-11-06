# September 2026

Uganda Airlines' September 2026 operation: **589 flights**, **1,219 h 51 min**
airborne, **974,373 km** flown — and the month the airline first appears at
Hoima, flying six sectors into Kabalega International while it was still listed
as under construction.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | 01SEP26 – 30SEP26, by local departure date |
| flights logged | 589 |
| airborne | 1,219 h 51 min |
| distance flown | 974,373 km (summed from the track positions, complete tracks only) |
| city pairs | 29 directional / 16 undirected |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL |
| types | CRJ900 (431 flights), 737-800 (115), A330-800 (43) |
| median flight | 1 h 20 min |
| busiest days | 06, 13 and 27 September, 27 flights each |
| quietest day | 03 September, 13 flights |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | 594 raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual and scheduled times, point count, SHA-256 |
| `flights_2026-09.csv` | one row per flight leg — 589 rows — with off/on times in UTC and local, airborne minutes, flown distance, max altitude, whether the track is complete, and where its times came from |
| `aeroroutes_2026-09.md` | the month's log in AeroRoutes notation, with a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

Regenerate the last three with:

```bash
python3 work/fr24_tracks.py --month 2026-09
```

## Where the data came from

Flightradar24's tracks, sliced out of the operator's `EBBs-FR24` movement
enumeration at commit `47e7201c5372` and copied here unchanged by
`work/import_ebbs_month.py`. Registrations and types are the movement board's
own; the route on each line is read off the track.

## A check on the numbers

Across the 577 flights timed from a complete track, those times agree with the
movement board's own actual times to a median of **1.3 minutes** at departure and
**3.0 minutes** at arrival (worst case 14 and 19 minutes).

## What the month looks like

- **Hoima appears.** Six sectors on 27, 29 and 30 September — four with 5X-EQU,
  two with 5X-KDP — shuttling Entebbe–Kabalega–Entebbe in about 20 minutes each
  way. The airport carries no IATA code yet, so the log prints its OurAirports
  identifier, `UG-0013`. These look like proving or demonstration flights ahead
  of opening; the archive records them, it does not interpret them.
- **A Harare–Nairobi sector on 29 September** (UR720) is flown as a through
  flight rather than the filed Harare–Entebbe, and is flagged under *Route
  discrepancies*.
- **Nairobi stayed the backbone** at 66 sectors each way; Johannesburg and Dar es
  Salaam ran about daily at 30 each.

## Coverage, and what to be careful with

- **581 of 589 flights have a track that runs end to end.** Eight are logged with
  times from the movement board's actual times (seven) or from the part of the
  track that exists (one); they are listed under *Track coverage* in the log.
- **Four exports could not be turned into a leg** and are named in
  `sources.json`: three are fragments of the 30 September UR523 rotations whose
  origin the record does not give, and one is a ground-only recording at Entebbe
  on 27 September. They are not silently dropped — they are counted here.
- **One export belongs to August** (departure on 31 August, arrival on
  1 September) and is logged there, by departure date.
- **Times are airborne times**, local at both ends, not the schedule; `(+1)`
  marks next-day arrivals.
- **Flown distance** sums the great-circle steps between recorded positions; it
  understates the true path and is not the straight-line figure in
  `reference/route_distances.csv`.

## Licence

The track data is Flightradar24's, kept here for the operator's own analytical
use within FR24's terms, the same basis on which it sits in `EBBs-FR24`. The
derived tables and the log are the operator's own.
