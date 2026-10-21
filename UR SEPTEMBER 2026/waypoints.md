# East African waypoints — reference list (added 2026-10-21)

`waypoints.csv` (536 rows) is the waypoint list supplied on 2026-10-21
as `East African FIR.csv` (kept verbatim at `work/East African FIR.csv`,
split into both month folders by `python3 work/build_waypoints.py`,
which only adds a `kind` column and tidier headers — names and
coordinates are untouched).

## What is in it

Named navigation points across the region the airline flies in —
latitude −12.4°…+5.3°, longitude 28.3°…46.5° (Uganda, Kenya, Tanzania,
Rwanda, Burundi, South Sudan, eastern DRC and the Somali coast):

| kind | rows | meaning |
|---|---:|---|
| `fix` | 364 | ICAO five-letter name-codes (PASAN, GABKU, UNKOS…) |
| `location` | 119 | four-letter ICAO aerodrome/location codes (HBBA Bujumbura, HKJK Nairobi…) |
| `navaid` | 27 | short NDB/VOR idents (NN, EM, PB — the Entebbe beacons among them) |
| `coord_fix` | 26 | latitude/longitude-named points (S0032, E0133…) |

## Does it match what actually flew? Yes.

Spot-checked against the October tracks: **27% of sampled track fixes
pass within 3 nm of a listed waypoint**, and the most-overflown point
in a 40-track sample is `NN` (Entebbe) — exactly what you'd expect.
The website uses it two ways: an optional **waypoint overlay** on the
map, and a **"fixes passed"** readout per flight (listed waypoints
within 3 nm of the flown path, in order) — a first step from "a line
on a map" to "the route structure the flight actually followed".

## Caveats — read before using it for anything serious

* **Provenance is thin.** The file arrived without an AIRAC cycle,
  effective date or publisher (the format resembles a flight-planning /
  GPS database export). Waypoints get renamed and moved between AIRAC
  cycles; **verify against the current AIP** before operational use.
  This is a reference and analysis aid, not a navigation database.
* **`altitude_m` is not terrain data.** Many rows carry `1131.0`
  (looks like a default), others are blank or `0`. Do not use it for
  obstacle or MSA reasoning.
* One ident (`TV`) names two different points, and three coordinates
  are shared by two names — kept as supplied, flagged here.
* `desc_` was empty and `overfly` was FALSE for every row in the
  source; both columns were dropped rather than carried as noise.

## Columns

`name, kind, latitude, longitude, altitude_m, source` — the last
column repeats the provenance string on every row so a filtered
extract can never lose it.
