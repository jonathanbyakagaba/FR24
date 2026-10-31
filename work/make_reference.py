#!/usr/bin/env python3
"""Build the reference/ folder that ships alongside the flight archive.

Everything in here is either (a) public domain, (b) our own derived measurement,
or (c) a handful of stated facts about the fleet.  Nothing is copied from a
source that forbids redistribution.

    reference/airports.csv        the airports these tracks touch (OurAirports, public domain)
    reference/runways.csv         their runway geometry (OurAirports, public domain)
    reference/route_distances.csv our own: great-circle distance per route pair + haul band
    reference/fleet.csv           the five airframes, type / role / ownership
reference/schedule_<month>.csv  the published timetable the delays are measured against, when the
                          month has one (from `work/schedule/`; without it `punctuality.py` scores
                          each service against its own median instead)
    reference/README.md           sources and licences for the above

Run:  PYTHONPATH=/home/user python3 work/make_reference.py
"""
import csv, os, sys

sys.path.insert(0, '/home/user')
import build_log as B

SRC = 'work/rwy'
OUT = 'fr24_publish/reference'
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------- airports ---
want = {}
# the raw OurAirports dump is the full answer for every airport on earth; when the workspace has
# thinned it, the published subset carries the same columns for exactly the airports this
# operation touches, which is all the table below ever needs
src_apts = f'{SRC}/airports.csv'
if not os.path.exists(src_apts):
    src_apts = f'{OUT}/airports.csv'
    if not os.path.exists(src_apts):
        raise SystemExit(f'no airport table: neither {SRC}/airports.csv nor {OUT}/airports.csv '
                         'exists - re-download the public-domain dump from '
                         'https://ourairports.com/data/ into work/rwy/airports.csv')
print(f'airport metadata read from: {src_apts}')
for a in csv.DictReader(open(src_apts)):
    want[a['ident']] = a
by_iata = {a['iata_code'].strip().upper(): a for a in want.values() if a['iata_code'].strip()}

used = set()
for r in csv.DictReader(open('runway_usage.csv')):
    for k in ('dep_apt', 'arr_apt'):
        if r[k]:
            used.add(r[k])
for code in B.AIRPORTS:                       # the log's network, kept whole
    # most entries are IATA codes; an airport with no code assigned yet (Kabalega,
    # Hoima) is keyed by its OurAirports ident, so look that up directly too
    a = by_iata.get(code) or want.get(code)
    if a:
        used.add(a['ident'])
used = sorted(used)

APT_COLS = ['ident', 'type', 'name', 'latitude_deg', 'longitude_deg', 'elevation_ft',
            'iso_country', 'municipality', 'iata_code', 'gps_code', 'scheduled_service']
with open(f'{OUT}/airports.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=APT_COLS, extrasaction='ignore')
    w.writeheader()
    for ident in used:
        a = want.get(ident)
        if a:
            w.writerow({k: a[k] for k in APT_COLS})

# ---------------------------------------------------------------- runways ---
RWY_COLS = ['airport_ident', 'length_ft', 'width_ft', 'surface', 'lighted', 'closed',
            'le_ident', 'le_latitude_deg', 'le_longitude_deg', 'le_elevation_ft',
            'le_heading_degT', 'le_displaced_threshold_ft',
            'he_ident', 'he_latitude_deg', 'he_longitude_deg', 'he_elevation_ft',
            'he_heading_degT', 'he_displaced_threshold_ft']
n_rwy = 0
with open(f'{OUT}/runways.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=RWY_COLS, extrasaction='ignore')
    w.writeheader()
    for r in csv.DictReader(open(f'{SRC}/runways.csv')):
        if r['airport_ident'] in used and r['closed'] != '1' and r['le_latitude_deg']:
            w.writerow({k: r[k] for k in RWY_COLS})
            n_rwy += 1

# ------------------------------------------------------- route distances ----
n_rt = 0
if os.path.exists('route_distances.csv'):
    with open('route_distances.csv') as fh_in, open(f'{OUT}/route_distances.csv', 'w', newline='') as fh_out:
        rd = csv.DictReader(fh_in)
        w = csv.DictWriter(fh_out, fieldnames=rd.fieldnames)
        w.writeheader()
        for r in rd:
            w.writerow(r)
            n_rt += 1

# ------------------------------------------------------------------ fleet ---
FLEET_COLS = ['registration', 'type', 'ownership', 'role', 'haul_band', 'source']
fleet = []
for r in csv.DictReader(open('fleet_summary.csv')):
    fleet.append(dict(registration=r['tail'], type=r['type'], ownership=r['ownership'],
                      role=r['role'],
                      haul_band={'short': 'short (<1,500 km)', 'medium': 'medium (1,500-4,000 km)',
                                 'long': 'long (>4,000 km)'}.get(r['role'], r['role']),
                      source='operator (screenshots) + Eurocontrol distance bands'))
with open(f'{OUT}/fleet.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=FLEET_COLS)
    w.writeheader()
    for r in sorted(fleet, key=lambda r: r['registration']):
        w.writerow(r)

# keep the published weather table in step with the source one
import glob as _g
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import month_ctx as MC          # noqa: E402
# the weather CSV under weather/ is `work/weather.py`'s scratch copy for this month and may
# have been cleared; the *published* table is named for the build month either way, so fall
# back to the month instead of writing a `weather_None.csv` row into the shipped README
_wxs = sorted(_g.glob('weather/metar_*.csv'))
src_wx = _wxs[-1] if _wxs else None
wx_m = os.path.basename(src_wx)[len('metar_'):-len('.csv')] if src_wx else MC.ctx()['ym']
if src_wx:
    import shutil
    dst_wx = f'{OUT}/weather_{wx_m}.csv'

    def _rows(q):
        return (sum(1 for _ in csv.reader(open(q))) - 1) if os.path.exists(q) else -1

    # weather/ holds work/weather.py's scratch copy for whatever window it fetched; a stale or
    # partial fetch must not publish itself over the table the repo ships
    n_src, n_dst = _rows(src_wx), _rows(dst_wx)
    if n_src >= n_dst:
        shutil.copyfile(src_wx, dst_wx)
    else:
        print(f'  ! keeping the published weather table ({n_dst:,} rows) over '
              f'{os.path.basename(src_wx)} ({n_src:,} rows) — re-run work/weather.py, then '
              f'work/metar_split.py, to widen it')

n_wx = 0
if os.path.exists(f'{OUT}/weather_{wx_m}.csv'):
    n_wx = sum(1 for _ in csv.reader(open(f'{OUT}/weather_{wx_m}.csv'))) - 1
    n_wx = f'{n_wx:,}'

# ------------------------------------------------------------- reference/ ---
open(f'{OUT}/README.md', 'w').write(f"""# Reference data

The static lookups the archive and the flight log are built against. One row per
airport, one per runway, one per airframe.

| file | rows | what it is | source and licence |
|---|---|---|---|
| `airports.csv` | {len(used)} | every airport the tracks touch, plus the log's network | [OurAirports](https://ourairports.com/data/) — **public domain** (Unlicense) |
| `runways.csv` | {n_rwy} | runway geometry and orientation for those airports | OurAirports — **public domain** |
| `route_distances.csv` | {n_rt} | great-circle distance per route pair, in km and nm, with the haul band | our own calculation from the airport coordinates |
| `fleet.csv` | {len(fleet)} | the five airframes: type, ownership, role | supplied by the operator |
| `weather_{wx_m}.csv` | {n_wx} | published surface observations (METAR) for 40 airports, matching the log's window | Iowa Environmental Mesonet ASOS archive — US government public-domain data, free to redistribute |

**Why these are in the repository.** Every number in the log and in the runway
analysis depends on them: the haul bands come from `route_distances.csv`, the
airport identification and runway lengths come from the OurAirports pair, and the
per-airframe work needs `fleet.csv`. Shipping the subset means the analyses can be
recomputed from the repository alone, without a 12 MB download of the whole world.

**Licences.** OurAirports is public domain — no attribution required, but credit is
polite and given here. `route_distances.csv`, `fleet.csv` and everything derived in
this repository are the operator's own data.

**Adding the weather table.** `weather_{wx_m}.csv` is written by
`work/weather.py`, not by this script. It is counted here so the table stays
honest when it is present; delete it from this folder and the row disappears.

**Scale.** Great-circle distances are computed from the *threshold* coordinates in
`airports.csv`; the airline's own flown distances are longer (routes are not
straight lines) and live in the track data instead.

Regenerate with `PYTHONPATH=/home/user python3 work/make_reference.py`.
""")

# ------------------------------------------------------- the month's timetable ---
# A schedule is an input, not an output, but it belongs in reference/ for the same reason the
# runway geometry does: every delay figure in the month folder is computed against it, and without
# it the numbers cannot be reproduced.  One file per month, named for the month it covers.
import glob as _g
import shutil as _sh
import month_ctx as _MC
_ym = _MC.ctx()['ym']
_canon = f'work/schedule/schedule_{_ym}.csv'
if os.path.exists(_canon):
    _sh.copyfile(_canon, f'{OUT}/schedule_{_ym}.csv')
    n_leg = sum(1 for _ in open(f'{OUT}/schedule_{_ym}.csv')) - 1
    print(f'schedule  reference/schedule_{_ym}.csv  ({n_leg} legs)')
else:
    print(f'schedule  none on file for {_ym} — the month falls back to a median "usual" slot')

print(f'wrote {OUT}/:')
for f in sorted(os.listdir(OUT)):
    print(f'  {f:26} {os.path.getsize(f"{OUT}/{f}"):>8,} B')
print(f'\nairports {len(used)}, runways {n_rwy}, routes {n_rt}, fleet {len(fleet)}')
