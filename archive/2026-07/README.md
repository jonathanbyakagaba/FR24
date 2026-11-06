# July 2026

Uganda Airlines' July 2026 operation: **597 flights**, **1,223 h 16 min** airborne,
**981,250 km** flown, across **14 city pairs** — the month the 787-8 joined the
London run.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | 01JUL26 – 31JUL26, by local departure date |
| flights logged | 597 |
| airborne | 1,223 h 16 min |
| distance flown | 981,250 km (summed from the track positions, complete tracks only) |
| city pairs | 26 directional / 14 undirected |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL, ET-AOU |
| types | CRJ900 (468 flights), 737-800 (96), A330-800 (19), 787-8 (14) |
| median flight | 1 h 19 min |
| busiest day | 26 July, 27 flights |
| quietest day | 02 and 16 July, 13 flights |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | 598 raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual and scheduled times, point count, SHA-256 |
| `flights_2026-07.csv` | one row per flight leg — 597 rows — with off/on times in UTC and local, airborne minutes, flown distance, max altitude, whether the track is complete, and where its times came from |
| `aeroroutes_2026-07.md` | the month's log in AeroRoutes notation, with a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

`flights_2026-07.csv`, `aeroroutes_2026-07.md` and `sources.json` are generated:

```bash
python3 work/fr24_tracks.py --month 2026-07
```

## Where the data came from

The tracks are Flightradar24's, taken from the operator's own `EBBs-FR24`
project — the enumeration of every movement at Entebbe — at commit
`47e7201c5372`, and copied here unchanged by `work/import_ebbs_month.py`.
Registrations and types are the movement board's own; the route on each line is
read off the track.

## A check on the numbers

Across the 591 flights whose times come from a complete track, those times agree
with the movement board's own actual times to a median of **1.2 minutes** at
departure and **3.1 minutes** at arrival (worst case 14 and 23 minutes) — what
you would expect between "airborne" and "off blocks".

## What the month looks like

- **Nairobi became the backbone**: 68 sectors each way, up from 16 in June — two
  to three rotations a day on the CRJ900.
- **The 787-8 arrived.** ET-AOU, on wet-lease from Ethiopian Airlines, flew 14
  sectors on Entebbe–London Gatwick — seven each way — alongside the A330-800,
  which itself dropped to 19 flights from June's 38.
- **Dar es Salaam and Johannesburg held at about one rotation a day**, 34 and 33
  sectors respectively; Harare, Lusaka, Mombasa, Mogadishu, Bujumbura and Juba
  made up the short-haul spine on the CRJ900.
- **Zanzibar was served through Kilimanjaro**, so the month shows Entebbe–Zanzibar
  and Kilimanjaro–Entebbe rather than a non-stop return.

## Coverage, and what to be careful with

- **594 of 597 flights have a track that runs end to end.** The other three are
  logged with their times taken from the movement board's actual times, and are
  listed under *Track coverage* in the log.
- **One export belongs to June.** A flight that departed on 30 June and landed on
  1 July is logged in June, by departure date.
- **Times are airborne times**, local at both ends, not the schedule; `(+1)`
  marks next-day arrivals. Westbound hops can arrive earlier by the clock than
  they departed (Juba is an hour behind Entebbe, Bujumbura two).
- **Flown distance** sums the great-circle steps between recorded positions and
  is understated slightly; it is not the same as the straight-line distances in
  `reference/route_distances.csv`.

## Licence

The track data is Flightradar24's, kept here for the operator's own analytical
use within FR24's terms, the same basis on which it sits in `EBBs-FR24`. The
derived tables and the log are the operator's own.
