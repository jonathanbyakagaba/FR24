# November 2026

The first six days of November 2026: **97 flights**, **227 h 43 min** airborne,
**85,173 km** flown. This is a **part month** — the archive was cut at the last
enumerated movement, 6 November — and it is the patchier of the months, because
the most recent flights have neither complete tracks nor recorded arrival times
yet.

| | |
|---|---|
| operator | Uganda Airlines (UR / UGD) |
| window | 01NOV26 – 06NOV26 (part month, 6 days), by local departure date |
| flights logged | 97 |
| airborne | 227 h 43 min |
| distance flown | 85,173 km (summed from the track positions, complete tracks only) |
| city pairs | 27 directional / 14 undirected |
| airframes | 5X-EQU, 5X-KDP, 5X-KOB, 5X-NIL, ET-APL |
| types | CRJ900 (79 flights), 737-800 (11), A330-800 (7) |
| median flight | 1 h 26 min |
| busiest day | 01 November, 22 flights |
| last day | 06 November, 10 flights — the day the cut-off falls in, so it is short |

## What is in this folder

| file | what it is |
|---|---|
| `tracks/` | 98 raw Flightradar24 exports, one CSV per flight, unedited |
| `tracks/manifest.csv` | one row per track file: flight id, number, callsign, route, registration, aircraft, actual and scheduled times, point count, SHA-256 |
| `flights_2026-11.csv` | one row per flight leg — 97 rows — with off/on times in UTC and local, airborne minutes, flown distance, max altitude, whether the track is complete, and where its times came from |
| `rotations_2026-11.csv` | one row per airframe rotation — 28 rows — with the airport chain it flew, the sectors it has a track for, and any sector the record is missing |
| `aeroroutes_2026-11.md` | the month's log in AeroRoutes notation, with a route summary and the track-coverage notes |
| `sources.json` | the exact files that were read, their sizes and checksums |

Regenerate the last four with:

```bash
python3 work/fr24_tracks.py --month 2026-11
```

## Where the data came from

Flightradar24's tracks, sliced out of the operator's `EBBs-FR24` movement
enumeration at commit `47e7201c5372` and copied here unchanged by
`work/import_ebbs_month.py`. Registrations and types are the movement board's
own; the route on each line is read off the track.

## A check on the numbers

Across the 67 flights timed from a complete track, those times agree with the
movement board's own actual times to a median of **1.3 minutes** at departure and
**2.7 minutes** at arrival (worst case 11 and 8 minutes).

## Rotations

The airframe-by-airframe view: **28 rotations**, 23 with every sector of the
chain present in the record. The other **5** hold **9 hops** between them — a
sector the movement board never listed, because the aircraft puts down at one
airport and is next heard from at another:

| hop | times |
|---|---|
| HRE–LUN | 2 |
| LUN–HRE | 1 |
| HRE–EBB? | 1 |
| JNB–LUN? | 1 |
| EBB–JNB | 1 |
| NBO–EBB? | 1 |
| ZNZ–NBO? | 1 |
| EBB–JRO | 1 |

4 of those hops carry a question mark: the record has the next leg
under way while the aircraft should still be on the ground, so the airport is
shown and the sector is not claimed — most likely two tracks for one airframe
overlapping rather than a flight nobody caught.

Those hops are the tag sectors behind the fifth-freedom question: the widebody's
Harare run is flown Entebbe–Harare–Lusaka–Harare–Lusaka–Entebbe, and only the
transit Lusaka–Harare–Lusaka was being enumerated; the Zanzibar run carries the
same shape at Kilimanjaro. The month's log keeps each hop in place and brackets the
airport only reachable through it, `EBB–HRE–[LUN]–EBB`, so a rotation reads from
first departure to last arrival rather than as two orphan legs. Every rotation,
hop and all, is in `rotations_2026-11.csv`; `work/fetch_fr24_tracks.py` is what turns a
hop into a tracked sector.

## What the month looks like

- **Nairobi stayed the busiest pair**: 8 sectors each way in six days.
- **Long-haul continued**: 5X-NIL flew 7 sectors on the London and Mumbai routes,
  and ET-APL's 737-800 flew 11.
- **Zanzibar came back as a non-stop pair** (Entebbe–Zanzibar and Zanzibar–
  Entebbe), after the through-Kilimanjaro pattern of earlier months.

## Coverage, and what to be careful with

- **69 of 97 flights have a track that runs end to end.** The other 28 are timed
  from the board's **scheduled** times — this is the newest month in the archive,
  so the enumeration has not yet filled in actual arrival times for them.
  `flights_2026-11.csv` marks them `time_source=schedule`.
- **A part month reads as one.** Frequencies in the log are "N weekly" on the
  days that were flown; they say nothing about the last three weeks of November,
  which are not in the archive yet.
- **One export belongs to October** (departure on 31 October) and is logged there.
- **Times are airborne times**, local at both ends; `(+1)` marks next-day
  arrivals.
- **Flown distance** sums the great-circle steps between recorded positions and
  covers complete tracks only.

## Licence

The track data is Flightradar24's, kept here for the operator's own analytical
use within FR24's terms, the same basis on which it sits in `EBBs-FR24`. The
derived tables and the log are the operator's own.
