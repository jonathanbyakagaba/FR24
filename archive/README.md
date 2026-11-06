# The archive

One folder per month of Uganda Airlines operations, newest last. Each folder is
self-contained: the raw Flightradar24 exports, the normalised leg table, the log
in AeroRoutes notation, and a README saying what the month contains and what it
does not. Nothing is shared between months except `reference/`.

| month | flights | airborne | city pairs | types | folder |
|---|---|---|---|---|---|
| June 2026 | 430 | 1,021 h 53 min | 14 undirected | A338, B738, CRJ9 | [`2026-06/`](2026-06/) |

## Naming

`YYYY-MM`, zero-padded, so the folders sort chronologically. Inside:

```
YYYY-MM/
  README.md                    what the month is, and its caveats
  tracks/*.csv                 raw exports, one per flight, untouched
  tracks/manifest.csv          what each of those files is
  flights_YYYY-MM.csv          one row per leg — the month as a table
  aeroroutes_YYYY-MM.md        the month as a log
  sources.json                 checksums of everything read
```

The three derived files are written by `work/fr24_tracks.py`; see the repository
[README](../README.md) for how a month is added and
[`reference/`](../reference/README.md) for the lookups the build depends on.

## Rules of the road

- **Raw exports are read-only.** Never edit a file under `tracks/`; if a flight
  is wrong, fix the pipeline or note it in the month's README.
- **Derived files are regenerated, never patched.** If a number is wrong, the
  input or the script is wrong.
- **A month is logged by local departure date.** A flight that leaves on 31 May
  and lands on 1 June belongs to May.
- **Follow the track, not the flight record.** Where the two disagree the log
  shows what the aircraft did and flags the difference.
- **Keep the folder small enough to clone.** Under ~50 MB per month of raw
  tracks; beyond that, park the exports in external storage and keep
  `sources.json` (checksums) in the repository instead.
