# Supporting files — what each one is, and how to regenerate it

Rewritten 2026-10-20 for the rebuilt folder. The frozen build's pipeline
(`work/final.py`, `work/runways.py`, …) is not in this repository; the
rebuild uses the two scripts now in `work/`, and this index says honestly
which files they produce and which files are carried over frozen.

| file | rows | what it is | rebuild with |
|---|---|---|---|
| `manifest.csv` | 622 | one row per track file in the month zip | `python3 work/rebuild_month.py "UR SEPTEMBER 2026" "UR September flights.zip"` |
| `flights.csv` | 622 | flight log from the tracks (takeoff/landing, route, air time) | same |
| `fleet_summary.csv` | 5 tails | per-aircraft September totals; fleet meta carried from the frozen file | same (reads existing `fleet_summary.csv`/`tails.csv` first) |
| `triangle_assignments.csv` | 225 | triangle sectors (UR720/722, UR334, UR206–209, UR342/343) with tails | same |
| `runway_usage.csv` | 622 | runway in use, simplified heading model (legacy header; survey columns blank) | same |
| `date_coverage.md` | — | flights per origin-local date | same |
| `all_flights_aeroroutes.md` | — | every flight grouped by route | same |
| `no_code_tracks.md` | — | tracks without a clean UGD flight identity (AF523, UGD720X) | same |
| `flight_conditions.csv` | 622 | Entebbe-end weather per flight | `python3 work/build_conditions.py "UR SEPTEMBER 2026"` |
| `weather_analysis.md` | — | September weather write-up | written from `flight_conditions.csv` + `metar/` |
| `runway_usage.md` | — | runway write-up and model limits | written from `runway_usage.csv` |
| `triangle_routes.md` | — | triangle write-up | written from `triangle_assignments.csv` |
| `data_gaps.md` | — | the 52 FTA-planned legs with no track, plus track-side notes | `python3 work/build_september_fta.py` |
| `notams.csv` | 51 | NOTAM notices whose validity touches Sep 2026 - lower bound only: the 2026-10-20 snapshot cannot see September-expired notices (see `notams.md`) | `python3 work/build_notams.py` from `work/notams_snapshot_*.csv` |
| `procedures.csv` | 20 | SID/STAR inventory seeded from NOTAM-named procedures + AIP evidence; no coded (ARINC 424) data - see `sid_star.md` | seeded from `work/procedures_seed.csv` |
| `notams.md` / `sid_star.md` | — | NOTAM read-across and the SID/STAR publication findings | written from the snapshot / source check 2026-10-20 |
| `punctuality.md` | — | punctuality basis note | — |
| `schedule_delays.md` | — | why no schedule-basis file exists for September | — |
| `tails.csv` | 701 | tail per flight, FR24 app pages — **frozen, not regenerated** | n/a (no app captures in repo) |
| `app_status.csv` | 705 | app status dots — **frozen, not regenerated** | n/a |
| `punctuality.csv` | 610 | app status + usual-time delays — **frozen, not regenerated** | n/a |
| `metar/` | HUEN, Sep 2026 | IEM ASOS parsed extract (drct/sknt/gust/vsby/tmpc/alti/wxcodes), 5 part files | see below |

## METAR

Source: Iowa State IEM ASOS (mesonet.agron.iastate.edu), station HUEN,
routine reports (report_type=3), UTC, parsed fields only — raw METAR
strings were not archived in this pass; the same request with
`data=metar` returns them. On a machine with internet access:

```
curl "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=HUEN&data=drct&data=sknt&data=gust&data=vsby&data=tmpc&data=alti&data=wxcodes&year1=2026&month1=9&day1=1&year2=2026&month2=10&day2=1&tz=Etc%2FUTC&format=onlycomma&latlon=no&elev=no&missing=empty&trace=empty&direct=no&report_type=3" -o metar/HUEN_202609_part0.csv
```

The frozen build archived 41 stations (Harare as FVRG, Lusaka as FLKK;
Juba has no IEM observations). To extend coverage, drop IEM extracts for
the other stations into `metar/` and re-run `work/build_conditions.py` —
it uses every station file present. This rebuild covers Entebbe, which is
one end of all but a handful of triangle middle sectors.

## Deliberately absent

* `schedule_delays.csv` — no September timetable baseline transcribed;
  see `schedule_delays.md`.
* `fleet_meta.csv` — the frozen fleet meta lives inside
  `fleet_summary.csv`'s carried-over columns; no separate file was kept.
