#!/usr/bin/env python3
"""Split the METAR table into one CSV per airport.

Reads weather/metar_2026-09.csv (written by work/weather.py) and writes
weather/metar/<ICAO>.csv for every airport, plus an index.  Pass --daily to
also write one file per airport per day under weather/metar/daily/.

Run:  python3 work/metar_split.py [--daily]
"""
import csv, os, sys, collections
import apt_source   # the airport table: raw dump if present, published subset otherwise

import collections
import glob as _g
# `metar/` is a shared lookup, not a per-month one (close_month says so), so the split covers every
# month the build has fetched: shipping only the newest month would silently drop September's
# observations from the repo while the README still called the directory complete.  Pass
# --month 2026-09 to split one month alone.
import sys as _sys
_only = None
if '--month' in _sys.argv:
    _only = _sys.argv[_sys.argv.index('--month') + 1]
def _month_of(f):
    b = os.path.basename(f)
    return b[len('metar_'):-len('.csv')] if b.startswith('metar_') else b[len('weather_'):-len('.csv')]

_cands = collections.defaultdict(list)
for pat, tag in (('weather/metar_*.csv', 'scratch'), ('fr24_publish/reference/weather_*.csv', 'published')):
    for f in _g.glob(pat):
        _cands[_month_of(f)].append(f)
# one file per month, the bigger one wins: a scratch window fetch that was overwritten by a later
# partial run must not beat the table the repository actually ships
_sources = []
for mo, files in sorted(_cands.items()):
    if _only is not None and mo != _only:
        continue
    _sources.append(max(files, key=lambda f: sum(1 for _ in open(f, errors='replace'))))
_sources.sort()
if not _sources:
    raise SystemExit(f'metar_split.py: no weather/metar_*.csv for {_only or "any month"} — '
                     f'run work/weather.py first (a split built from nothing would publish an '
                     f'empty shared lookup over a full one)')
SRC = _sources[0] if len(_sources) == 1 else None      # merged below when several months
OUT = 'weather/metar'
COLS = ['icao', 'station', 'valid', 'wind_from', 'wind_kt', 'gust_kt', 'vis_sm',
        'temp_f', 'dew_f', 'qnh_inhg', 'wx', 'metar']


def main():
    daily = '--daily' in sys.argv
    rows = []
    seen = set()
    for q in _sources:
        for r in csv.DictReader(open(q)):
            k = (r['icao'], r['valid'])
            if k in seen:
                continue                      # a month file and a window file can overlap
            seen.add(k)
            rows.append(r)
    if len(_sources) > 1:
        print(f'merging {len(_sources)} month files ({", ".join(os.path.basename(x) for x in _sources)}) '
              f'-> {len(rows):,} observations')
    by = collections.defaultdict(list)
    for r in rows:
        by[r['icao']].append(r)
    os.makedirs(OUT, exist_ok=True)
    if daily:
        os.makedirs(os.path.join(OUT, 'daily'), exist_ok=True)

    index = []
    for icao in sorted(by):
        rs = sorted(by[icao], key=lambda r: r['valid'])
        path = os.path.join(OUT, f'{icao}.csv')
        with open(path, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, extrasaction='ignore')
            w.writeheader(); w.writerows(rs)
        if daily:
            for day, group in collections.groupby(rs, key=lambda r: r['valid'][:10]):
                with open(os.path.join(OUT, 'daily', f'{icao}_{day}.csv'), 'w', newline='') as fh:
                    w = csv.DictWriter(fh, fieldnames=COLS, extrasaction='ignore')
                    w.writeheader(); w.writerows(group)
        index.append(dict(icao=icao, station=rs[0]['station'], rows=len(rs),
                          first=rs[0]['valid'], last=rs[-1]['valid'],
                          days=len({r['valid'][:10] for r in rs}), file=f'{icao}.csv'))

    with open(os.path.join(OUT, 'index.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(index[0]))
        w.writeheader(); w.writerows(index)

    L = ['# METAR by airport', '',
         'One file per airport: every published surface observation for that station, '
         'newest last. Times are UTC and the raw METAR text is kept as the audit trail.',
         '', '| file | station | observations | days | first | last |', '|---|---|---|---|---|---|']
    for r in index:
        L.append(f"| `{r['file']}` | {r['icao']} | {r['rows']:,} | {r['days']} | "
                 f"{r['first']} | {r['last']} |")
    # airports in the operation that filed nothing at all
    want = set()
    try:
        iata2icao = {}
        for r in apt_source.rows():
            if r['iata_code'].strip():
                iata2icao[r['iata_code'].strip().upper()] = r['ident']
        import sys as _s
        _s.path.insert(0, '/home/user')
        import build_log as B
        want = {iata2icao[i] for i in B.AIRPORTS if i in iata2icao}
    except Exception:
        pass
    missing = sorted(want - set(by))

    L += ['', f'{len(index)} airports, {sum(r["rows"] for r in index):,} observations.', '']
    L += ['**Two airport codes have changed.** Lusaka now files under **FLKK** and Harare under '
          '**FVRG**; both files are named after the airport so they line up with the rest of the '
          'repository, and the `station` column shows the code the report was filed under.', '']
    if missing:
        L += ['**No observations exist for ' + ', '.join(missing) + '.** Juba in particular '
              'does not appear in the archive at all, so any Juba analysis has to come from the '
              "aircraft's own track.", '']
    L += ['Regenerate: `python3 work/metar_split.py` (add `--daily` for one file per '
          'airport per day under `daily/`).']
    open(os.path.join(OUT, 'README.md'), 'w').write('\n'.join(L) + '\n')
    print(f'wrote {len(index)} airport files + index.csv + README.md into {OUT}/ '
          f'({sum(r["rows"] for r in index):,} observations)')
    if daily:
        print(f'  and {sum(r["days"] for r in index)} daily files under {OUT}/daily/')


if __name__ == '__main__':
    main()
