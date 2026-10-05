# Supporting files — what each one is, and how to regenerate it

Derived from the tracks already published here. Nothing in this list is hand-edited:
every row count was read off the file itself when this index was written, and each
file has a one-line command that rebuilds it after a new daily upload.

| file | rows | what it is | rebuild with |
|---|---|---|---|
| `tails.csv` | 701 flights | which aircraft flew which leg, from the per-tail app pages, with the app's own status flag and a track-verified marker | `PYTHONPATH=. python3 work/final.py` |
| `fleet_summary.csv` | 5 tails | per-aircraft totals from the tracks: flights, air hours, routes, cruise and top of climb, with MSN and cabin | `PYTHONPATH=. python3 work/final.py` |
| `fleet_meta.csv` | 5 tails | the hardware record behind those columns: MSN, ICAO type code, mode-S hex, build month, cabin split | `maintained by hand, then re-run work/final.py` |
| `triangle_assignments.csv` | 47 sectors | the fifth-freedom legs flown away from Entebbe (LUN-HRE, ZNZ-JRO), with flight numbers | `PYTHONPATH=. python3 work/final.py` |
| `triangle_routes.md` | — | the triangle-route write-up | `PYTHONPATH=. python3 work/triangle_report.py` |
| `runway_usage.csv` | 802 tracks | runway identification and runway-use measurement per track: which end, where the roll started, how much runway was used | `PYTHONPATH=. python3 work/runways.py` |
| `runway_usage.md` | — | the runway report, including the corrected Entebbe centreline | `python3 work/runway_report.py` |
| `flight_conditions.csv` | 610 flights | the published weather at each end of every flight: wind, gust, visibility, temperature, and the head/crosswind component on the runway actually used | `PYTHONPATH=. python3 work/weather.py` |
| `weather_analysis.md` | — | what the weather explains: runway-in-use, wind against the measured rolls, delayed sectors | `PYTHONPATH=. python3 work/weather.py` |
| `punctuality.csv` | 610 flights | the app's status flag for each leg (on time / late / very late) and the measured minutes against the usual departure time | `python3 work/punctuality.py` |
| `punctuality.md` | — | the punctuality write-up, by aircraft and by worst departure | `python3 work/punctuality.py` |
| `app_status.csv` | 705 rows | the flag table underneath: every status dot read off the per-tail screenshots, matched to its flight | `python3 work/app_status.py` |
| `date_coverage.md` | — | day-by-day coverage: which days of the month are complete, which are holed, which rotations never finished | `PYTHONPATH=. python3 work/date_coverage.py` |
| `data_gaps.md` | — | what is missing and why, counted against the other files in this folder | `PYTHONPATH=. python3 work/report_gaps.py` |
| `no_code_tracks.md` | — | tracks that arrived without a flight code, and every one the log does not cite — its own line says how wide the scan was | `PYTHONPATH=. python3 work/no_code_tracks.py` |
| `SUPPORTING.md` | — | one-line description and rebuild command for every derived file | `written by this same build: `python3 fr24_update.py --zip <export>`` |
| `metar/` | 41 airports | every published METAR for each airport in this operation, one CSV per station plus `index.csv`, raw report text kept | `python3 work/metar_split.py` |

## Deliberately absent

A month folder is not a smaller copy of the archive: some layers cannot be written for a month that has no input for them. They are listed so their absence is a fact and not an oversight.

* `FR data.zip` — the archive is cumulative and lives at the top level, one copy for every month
* `schedule_delays.csv` — not produced for this month; the command in `work/` will write it when the data arrives
* `schedule_delays.md` — not produced for this month; the command in `work/` will write it when the data arrives


## Two things worth knowing

**The screenshots arrive in batches.** `tails.csv` is built from the per-tail app
pages, transcribed into `work/screens_extra/batch_<date>.csv` and merged by
`work/final.py`. A row that already exists is dropped rather than counted twice, so
adding a batch never inflates the totals. To add a day, save its rows as a CSV with
columns `tail,date,flight,origin,dest` in that folder and re-run the command.

**Weather comes from the Iowa Environmental Mesonet ASOS archive** — the same
published reports that feed NOAA's Integrated Surface Database, free and with no
account. It is a live service: each airport is cached in `weather/raw/<ICAO>.csv`,
so delete that folder to re-fetch. Harare files under **FVRG** and Lusaka under
**FLKK** (both re-coded since the runway datasets were compiled); Juba (HSSJ) has no
observations in the archive at all.

Licences: the OurAirports tables are public domain; METAR observations are US
government public-domain data redistributed by IEM under their free-use terms; the
Entebbe centreline geometry derived from OpenStreetMap is ODbL — attribute it rather
than republishing the geometry.
