# Flight Data Explorer — interactive map for this dataset

A static website (no build step, no framework) to explore the
September–October 2026 Uganda Airlines data in this repository on a map.

## Run it

```bash
python3 website/build_data.py          # regenerate website/data.json
cd website && python3 -m http.server 8000
# open http://localhost:8000
```

Any static file server works; opening `index.html` via `file://` will
**not** work because the app fetches `data.json`.

## What you can do

* **Map** — 15 airports (markers sized by movements, permanent code
  labels, red badges = NOTAM count) and curved route arcs coloured by
  direction (blue out of Entebbe, amber into Entebbe, violet between
  outstations), line width ∝ flights. Click an arc to filter that route.
* **Filters** — month (All / September / October), flight-number search,
  origin, destination, aircraft tail, punctuality class, date range.
  Everything on the page (stats, arcs, airport sizes, daily chart,
  flight list) responds to the same filter set.
* **Flight replay** — click any flight: its *actual flown FR24 track*
  is drawn on the map with an animated aircraft you can play/pause and
  scrub (1×–40×), with live lat/lon, altitude, ground speed and an
  altitude-profile chart in the detail panel.
* **Detail panels** — per flight: tail, takeoff/landing UTC, air time,
  departure/arrival delay vs the FTA plan (takeoff-based, includes
  taxi-out), runways used at the Entebbe end, weather codes, the
  NOTAMs in force at both ends, and **fixes passed** — listed East
  African waypoints within 3 nm of the flown path, in order. Per
  airport (click a marker): in/out counts, busiest routes, NOTAM list.
* **Waypoint overlay** (toggle) — the 536-point East African waypoint
  list (`waypoints.csv` in the month folders): fixes, navaid idents,
  ICAO locations and coordinate fixes.
* **Daily traffic chart** — flights per day for the filtered set
  (blue = September, gold = October).

## Files

| file | what |
|---|---|
| `index.html`, `styles.css`, `app.js` | the site (Leaflet app) |
| `build_data.py` | builds `data.json` from `../UR SEPTEMBER 2026/`, `../UR OCTOBER 2026/` and `../work/rebuild_month.py` (airport coordinates) |
| `data.json` | generated (~4 MB): 1,007 flights with downsampled flown paths, airports, routes, daily counts, NOTAMs |
| `vendor/leaflet/` | Leaflet 1.9.4 vendored locally (BSD-2-Clause, see LICENSE.txt) so the app shell works offline — map tiles still come from CARTO/OpenStreetMap |

Data provenance is the repository's: FR24 tracks, FTA utilization
plans, Iowa State IEM METAR (via `flight_conditions.csv`) and the
2026-10-20 NOTAM snapshot (`notams.csv`). Delays are therefore
plan-vs-actual exactly as documented in the month folders.
