# June 2026

Uganda Airlines' June 2026 operation, rebuilt from the position tracks of every
flight the carrier filed that month: **430 flights**, **1,021 h 58 min** airborne,
**826,292 km** flown, across **14 city pairs**.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | 01JUN26 – 30JUN26, by local departure date |
| flights logged | 430 |
| airborne | 1,021 h 58 min |
| distance flown | 826,292 km (summed from the track positions, complete tracks only) |
| city pairs | 28 directional / 14 undirected |
| track coverage | 429 of 430 flights end to end |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL |
| types | A330-800 (38 flights), 737-800 (71), CRJ900 (321) |
| median flight | 1 h 27 min |
| busiest days | 07, 14 and 28 June, 20 flights each |
| quietest day | 13 June, 9 flights |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | 431 raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual and scheduled times, point count, SHA-256 |
| `flights_2026-06.csv` | one row per flight leg — 430 rows — with off/on times in UTC and local, airborne minutes, flown distance, max altitude, whether the track is complete, where its times came from, and the track file behind each row |
| `aeroroutes_2026-06.md` | the month's log in AeroRoutes notation, plus a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

`flights_2026-06.csv`, `aeroroutes_2026-06.md` and `sources.json` are generated:

```bash
python3 work/fr24_tracks.py --month 2026-06
```

## Where the data came from

The tracks are Flightradar24's, taken from the operator's own `EBBs-FR24`
project, which enumerates every movement at Entebbe and pulls the position track
for each one. This month was sliced out of that project at commit
`47e7201c5372` — the `track_targets.csv` rows for `Uganda Airlines` dated
`2026-06` — and copied here unchanged by `work/import_ebbs_month.py`.

Two things follow from that route into the archive:

- **Every flight is one the Entebbe enumeration saw**, so the sample is complete
  at the hub and thinner at the far ends. Where a return sector was not
  enumerated separately the month shows an imbalance between the two directions
  of a city pair — Zanzibar–Entebbe carries 4 flights against 6 the other way,
  because the other two were catalogued under their Kilimanjaro legs.
- **Nothing has been inferred.** Registrations and aircraft types come from the
  movement board's own record, not from the reference fleet list; the route on
  each line is read off the track itself.

## A check on the numbers

The off and on times in `flights_2026-06.csv` are read out of the tracks. They
can be checked against something the tracks did not produce: the movement board's
own actual times. Across the 427 flights where both exist they agree to a median
of **1.4 minutes** at departure and **2.9 minutes** at arrival, with a worst case
of 13 minutes. The difference is what you would expect between "airborne" and
"off blocks", which is why the log uses the former and says so.

## Coverage, and what to be careful with

- **429 of the 430 flights have a track that runs end to end**; the one that does
  not is timed from the movement board's actual times and listed under *Track
  coverage* in the log.
- **Two UR334 sectors are logged somewhere other than the flight record says.**
  On 12 and 19 June the flight was filed Entebbe–Zanzibar, but the track shows
  the aircraft landing at Kilimanjaro and stopping there. The log records what it
  flew (Entebbe–Kilimanjaro) and flags the difference under *Route
  discrepancies*.
- **One export belongs to May.** UR111 departed Gatwick on 31 May and landed at
  Entebbe on 1 June; logged by departure date it is a May flight, so it is not
  in this month's 430. 21 of the 430 flights land on the day after they depart.
- **The clock is local at both ends.** A westbound hop can therefore arrive
  earlier by the clock than it departed — Entebbe 06:52 to Juba 06:40 — because
  Juba is an hour behind Entebbe. `(+1)` marks next-day arrivals.
- **Times are airborne times**, from wheels-off to wheels-on as recorded in the
  track, not the airline's schedule and not block times. They differ from the
  timetable by a few minutes either way.
- **Positions are sampled, not continuous.** Flown distance is the sum of
  great-circle steps between successive positions, so it understates the true
  path slightly, and it is not comparable with `reference/route_distances.csv`,
  which is straight-line distance between airports.
- **An empty gap in service is real.** The fleet flew every day of the month;
  there is no day with a missing track bundle.

## Licence

The track data is Flightradar24's, kept here for the operator's own analytical
use within FR24's terms, the same basis on which it sits in `EBBs-FR24`. The
derived tables and the log are the operator's own.
