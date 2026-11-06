# October 2026

Uganda Airlines' October 2026 operation: **616 flights**, **1,324 h 23 min**
airborne, **958,990 km** flown. It is also the first month in the archive where
a noticeable share of the exports stop short — read the coverage notes before
quoting a number from it.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | 01OCT26 – 31OCT26, by local departure date |
| flights logged | 616 |
| airborne | 1,324 h 23 min |
| distance flown | 958,990 km (summed from the track positions, complete tracks only) |
| city pairs | 29 directional / 17 undirected |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL |
| types | CRJ900 (466 flights), 737-800 (106), A330-800 (44) |
| median flight | 1 h 23 min |
| busiest day | 11 October, 28 flights |
| quietest day | 08 October, 14 flights |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | 618 raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual and scheduled times, point count, SHA-256 |
| `flights_2026-10.csv` | one row per flight leg — 616 rows — with off/on times in UTC and local, airborne minutes, flown distance, max altitude, whether the track is complete, and where its times came from |
| `rotations_2026-10.csv` | one row per airframe rotation — 148 rows — with the airport chain it flew, the sectors it has a track for, and any sector the record is missing |
| `aeroroutes_2026-10.md` | the month's log in AeroRoutes notation, with a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

Regenerate the last four with:

```bash
python3 work/fr24_tracks.py --month 2026-10
```

## Where the data came from

Flightradar24's tracks, sliced out of the operator's `EBBs-FR24` movement
enumeration at commit `47e7201c5372` and copied here unchanged by
`work/import_ebbs_month.py`. Registrations and types are the movement board's
own; the route on each line is read off the track.

## A check on the numbers

Across the 581 flights timed from a complete track, those times agree with the
movement board's own actual times to a median of **1.3 minutes** at departure and
**3.2 minutes** at arrival. The worst arrival gap is 93 minutes, on a single
flight whose track ends on the landing roll well before the aircraft reached the
block.

## Rotations

The airframe-by-airframe view: **148 rotations**, 107 with every sector of the
chain present in the record. The other **41** hold **47 hops** between them — a
sector the movement board never listed, because the aircraft puts down at one
airport and is next heard from at another:

| hop | times |
|---|---|
| HRE–LUN | 16 |
| LUN–HRE | 15 |
| ZNZ–JRO | 13 |
| HRE–EBB | 1 |
| HRE–EBB? | 1 |
| JNB–LUN? | 1 |

2 of those hops carry a question mark: the record has the next leg
under way while the aircraft should still be on the ground, so the airport is
shown and the sector is not claimed — most likely two tracks for one airframe
overlapping rather than a flight nobody caught.

Those hops are the tag sectors behind the fifth-freedom question: the widebody's
Harare run is flown Entebbe–Harare–Lusaka–Harare–Lusaka–Entebbe, and only the
transit Lusaka–Harare–Lusaka was being enumerated; the Zanzibar run carries the
same shape at Kilimanjaro. The month's log keeps each hop in place and brackets the
airport only reachable through it, `EBB–HRE–[LUN]–EBB`, so a rotation reads from
first departure to last arrival rather than as two orphan legs. Every rotation,
hop and all, is in `rotations_2026-10.csv`; `work/fetch_fr24_tracks.py` is what turns a
hop into a tracked sector.

## What the month looks like

- **Nairobi led again**, 69 sectors in and 67 out — two rotations a day.
- **Three city pairs appear that are not end-to-end routes**: Dar es Salaam–
  Nairobi (11 October), Juba–Nairobi (13 October) and Johannesburg–Harare
  (21 October). In each case the aircraft set down en route and carried on under
  the same flight number; the log splits them into sectors and flags the
  difference from the flight record.
- **Johannesburg and Dar es Salaam ran daily** (33 and 30 sectors), with the
  usual short-haul spine on the CRJ900s.
- **The A330-800 flew 44 sectors** across London Gatwick and Mumbai, close to
  September's 43.

## Coverage, and what to be careful with

- **588 of 616 flights have a track that runs end to end.** The remaining 28 are
  listed under *Track coverage* in the log, and they are why this month needs a
  caveat:
  - **23** are timed from the board's **scheduled** times, because neither a
    complete track nor an actual arrival time exists for them. Those lines are
    timetable, not record; `flights_2026-10.csv` marks them
    `time_source=schedule` so they can be filtered out;
  - **3** are timed from the board's **actual** times — good to a few minutes,
    the same as the rest of the log;
  - **2** have a hole in the middle of the track (UR111 on 2 October, 157 minutes;
    UR110 on 6 October, 75 minutes), so their distance is understated.
- **Two exports belong either side of the month boundary** — one departed 30
  September, one on 31 October — and are logged by departure date, so each sits
  in the month it left.
- **Times are airborne times**, local at both ends, not the schedule; `(+1)`
  marks next-day arrivals.
- **Flown distance** sums the great-circle steps between recorded positions and
  covers complete tracks only; it understates the true path.

## Licence

The track data is Flightradar24's, kept here for the operator's own analytical
use within FR24's terms, the same basis on which it sits in `EBBs-FR24`. The
derived tables and the log are the operator's own.
