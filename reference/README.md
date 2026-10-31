# Reference data

The static lookups the archive and the flight log are built against. One row per
airport, one per runway, one per airframe.

| file | rows | what it is | source and licence |
|---|---|---|---|
| `airports.csv` | 47 | every airport the tracks touch, plus the log's network | [OurAirports](https://ourairports.com/data/) — **public domain** (Unlicense) |
| `runways.csv` | 86 | runway geometry and orientation for those airports | OurAirports — **public domain** |
| `route_distances.csv` | 29 | great-circle distance per route pair, in km and nm, with the haul band | our own calculation from the airport coordinates |
| `fleet.csv` | 5 | the five airframes: type, ownership, role | supplied by the operator |
| `weather_2026-10.csv` | 20,945 | published surface observations (METAR) for 40 airports, matching the log's window | Iowa Environmental Mesonet ASOS archive — US government public-domain data, free to redistribute |

**Why these are in the repository.** Every number in the log and in the runway
analysis depends on them: the haul bands come from `route_distances.csv`, the
airport identification and runway lengths come from the OurAirports pair, and the
per-airframe work needs `fleet.csv`. Shipping the subset means the analyses can be
recomputed from the repository alone, without a 12 MB download of the whole world.

**Licences.** OurAirports is public domain — no attribution required, but credit is
polite and given here. `route_distances.csv`, `fleet.csv` and everything derived in
this repository are the operator's own data.

**Adding the weather table.** `weather_2026-10.csv` is written by
`work/weather.py`, not by this script. It is counted here so the table stays
honest when it is present; delete it from this folder and the row disappears.

**Scale.** Great-circle distances are computed from the *threshold* coordinates in
`airports.csv`; the airline's own flown distances are longer (routes are not
straight lines) and live in the track data instead.

Regenerate with `PYTHONPATH=/home/user python3 work/make_reference.py`.
