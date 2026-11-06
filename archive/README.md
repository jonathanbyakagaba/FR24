# The archive

One folder per month of Uganda Airlines operations, newest last. Each folder is
self-contained: the raw Flightradar24 exports, the normalised leg table, the log
in AeroRoutes notation, and a README saying what the month contains and what it
does not. Nothing is shared between months except `reference/`.

| month | flights | airborne | km flown | city pairs | rotations | untracked hops | types | folder |
|---|---|---|---|---|---|---|---|---|
| June 2026 | 430 | 1,021 h 58 min | 826,292 | 14 | 143 | 24 | A338, B738, CRJ9 | [`2026-06/`](2026-06/) |
| July 2026 | 597 | 1,223 h 16 min | 981,250 | 14 | 139 | 39 | A338, B738, B788, CRJ9 | [`2026-07/`](2026-07/) |
| August 2026 | 619 | 1,323 h 17 min | 1,049,216 | 14 | 152 | 47 | A338, B738, CRJ9 | [`2026-08/`](2026-08/) |
| September 2026 | 589 | 1,219 h 51 min | 974,373 | 16 | 137 | 45 | A338, B738, CRJ9 | [`2026-09/`](2026-09/) |
| October 2026 | 616 | 1,324 h 23 min | 958,990 | 17 | 148 | 47 | A338, B738, CRJ9 | [`2026-10/`](2026-10/) |
| November 2026 (to the 6th) | 97 | 227 h 43 min | 85,173 | 14 | 28 | 9 | A338, B738, CRJ9 | [`2026-11/`](2026-11/) |
| **total** | **2,948** | **6,340 h 28 min** | **4,875,293** | — | **747** | **211** | — | |

Kilometres are the flown distance summed from the track positions, complete
tracks only, so they run a little under the true path. The totals row is computed
from the underlying data rather than by adding the rounded rows, so it can differ
from the column by a kilometre. November is a part month: the archive stops at
the last movement enumerated on 6 November 2026.

## Naming

`YYYY-MM`, zero-padded, so the folders sort chronologically. Inside:

```
YYYY-MM/
  README.md                    what the month is, and its caveats
  tracks/*.csv                 raw exports, one per flight, untouched
  tracks/manifest.csv          what each of those files is, and where it came from
  flights_YYYY-MM.csv          one row per leg — the month as a table
  rotations_YYYY-MM.csv        one row per airframe rotation, holes included
  aeroroutes_YYYY-MM.md        the month as a log
  sources.json                 checksums of everything read
```

The four derived files are written by `work/fr24_tracks.py`; see the repository
[README](../README.md) for how a month is added and
[`reference/`](../reference/README.md) for the lookups the build depends on.

## Rotations

Each airframe's legs are chained into the day of flying they belong to, and the
chain is what the month's *Rotations* table prints. Where the record has the
aircraft on the ground at one airport and then in the air from another, the
rotation keeps the sector it must have flown and brackets the airport reachable
only through it:

```
EBB–HRE  UR720  →  HRE–[LUN]  →  LUN–EBB  UR721      one rotation
```

That is the widebody's Harare run, and the same shape recurs on the Zanzibar run
as `EBB–ZNZ–[JRO]–ZNZ–EBB`. 184 of the archive's 747 rotations carry at least one
such hop, 211 in all, six of them marked `?` where the record contradicts itself
rather than merely missing a sector; `work/fetch_fr24_tracks.py` fills the rest
from the Flightradar24 API when credentials allow, after which the brackets come
off on a rebuild.

## Rules of the road

- **Raw exports are read-only.** Never edit a file under `tracks/`; if a flight
  is wrong, fix the pipeline or note it in the month's README.
- **Derived files are regenerated, never patched.** If a number is wrong, the
  input or the script is wrong.
- **A month is logged by local departure date.** A flight that leaves on 31 May
  and lands on 1 June belongs to May.
- **Follow the track, not the flight record.** Where the two disagree the log
  shows what the aircraft did and flags the difference.
- **A hop is evidence, not a guess.** A sector is only inserted where the aircraft
  changes airport and the hole is big enough to hold the flight; a gap that opens
  and closes at the same airport is left alone, and stays that way.
- **Keep the folder small enough to clone.** Under ~50 MB per month of raw
  tracks; beyond that, park the exports in external storage and keep
  `sources.json` (checksums) in the repository instead.
