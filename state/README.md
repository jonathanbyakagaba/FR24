# State

What the nightly harvest remembers between runs. Both files are written by
`work/sync_fr24.py` and committed back, which is what lets each night pick up
where the last one stopped.

| file | what it is |
|---|---|
| `ledger.csv` | one row per Flightradar24 flight id the sync has looked at: the airframe, the date, the month it was filed into, the track file if there was one, and `tracked` / `no-track` / `error` |
| `sync.json` | the last run: its window, the airframes asked about, how many flights were seen and fetched, the months touched, and any notes worth reading |
| `sweep.json` | the gap sweep's memory, written by `work/sweep_gaps.py`: how many tries each missing sector has had, which are parked, and per month what is open and how much has been closed |

`sweep.json` is the reason the sweep can keep walking June's backlog without
asking Flightradar24 the same question forever: three failed attempts at a sector
and it is parked, with the gap sheet saying so.

`ledger.csv` is the reason a nightly run is cheap — a flight already on disk is
skipped without another request — and the reason a missing one is not chased
forever: a `no-track` entry is retried for two nights and then left alone.

Deleting either file is safe. The next run treats the window as a first run
(`--days`, or `--since` if you give one) and rebuilds the ledger as it goes; the
only cost is a wider look-back and a few hundred redundant checks.
