#!/usr/bin/env python3
"""What aviationweather.gov holds for the airports Uganda Airlines actually flies to.

Written after measuring the service rather than trusting its docs (2026-11-03, from this repo):

* `api/data/metar` and `api/data/taf` answer for 14 of our 16 stations; Entebbe is **HUEN**, not the
  `EBBU` I had guessed, and Harare is **FVHA**. Lagos (DNMM) and Johannesburg (FAJS) hold no
  observations in a 3-hour window, so an empty answer is a fact about the service, not an error.
* History is capped: `hours=240` and `hours=336` both return exactly **400** records per station,
  which at two observations an hour is about **8 days**. That is comfortably deeper than the four-day
  FR24 trail horizon we work to, and it is why the backfill stops where it stops: the weather for
  18-29 Oct cannot be retrieved from here either.
* Asking for many `ids` in one request does **not** multiply the 400-record cap — 14 stations in one
  call returned 44 rows, while one station alone returned 48. So each station is asked separately.
  16 stations x 2 products is ~30 requests; at twice a day that is nothing.
* `api/data/airsigmet` and `api/data/gairmet` are the interesting ones, and they are the fragile
  ones: they return only what is *current*, polygons included, with no way to ask for last Tuesday.
  A SIGMET over the Entebbe FIR during a UR rotation is gone for ever unless somebody keeps it. That
  is the same shape of problem as the FR24 trails, so it is captured on the same schedule.

Output, in `--out` (default `work/awx`), is deliberately boring: one JSON per station per product, a
`hazards.json` holding the SIGMET/AIRMET snapshot of this moment, a flat `observations.csv` the other
scripts can read without knowing this API, and `manifest.json` saying what was asked and what came.
Nothing here is filtered to a month; `fr24_state`/the weather layer decide what to use.

Exit status: 0 something was written, 3 the service answered but had nothing for these stations,
4 nothing answered at all (blocked or offline) — 4 is the one a schedule should be angry about.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36 '
                    '(data collection for a published airline operations record)'}
BASE = 'https://aviationweather.gov/api/data'
LOW = ('LKG', 'FEW', 'SCT', 'BKN', 'OVC')          # anything with a base, for the ceiling rule
CEILING_COVER = ('BKN', 'OVC')                    # the actual ICAU/FAA definition


def get(path, tries=3, log=None):
    """GET BASE+path as JSON. None if it never answered; [] is a real empty answer."""
    url = BASE + path
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as r:
                body = r.read().decode('utf-8', 'replace')
            return json.loads(body) if body.strip() else []
        except urllib.error.HTTPError as e:
            if e.code == 204:                                   # no data for that query, by design
                return []
            if e.code in (429, 500, 502, 503, 504) and n < tries - 1:
                time.sleep(4 * (n + 1))
                continue
            if log:
                log(f'    ! {e.code} {path[:90]}')
            return None
        except Exception as e:                                  # noqa: BLE001
            if n < tries - 1:
                time.sleep(3 * (n + 1))
                continue
            if log:
                log(f'    ! {type(e).__name__} {path[:70]}')
            return None
    return None


def station_list(airports_csv, iata_codes, log):
    """Our own master, our own IATA codes: ICAO ids for the airports the log names.

    `reference/airports.csv` is an OurAirports extract, so `ident` is the ICAO where one exists. A
    code missing from it is reported, not dropped quietly, because a missing station is how a month
    ends up with weather for 12 airports and nobody notices.
    """
    by_iata, by_icao = {}, {}
    try:
        with open(airports_csv, newline='', encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                icao = (r.get('ident') or '').strip().upper()
                iata = (r.get('iata_code') or '').strip().upper()
                if len(icao) == 4:
                    by_icao[icao] = r
                if iata:
                    by_iata[iata] = r
    except OSError as e:
        log(f'  no airport master at {airports_csv} ({e}): pass --ids yourself')
        return [], []
    ids, unknown = [], []
    for c in iata_codes:
        row = by_iata.get(c.upper())
        icao = (row or {}).get('ident', '').strip().upper()
        if row and len(icao) == 4:
            if icao not in ids:
                ids.append(icao)
        elif c.upper() in by_icao:
            if c.upper() not in ids:
                ids.append(c.upper())
        else:
            unknown.append(c.upper())
    if unknown:
        log(f'  not in the master, so not queried: {", ".join(sorted(set(unknown)))}')
    return ids, sorted(set(by_iata) | set(by_icao))


def ceiling_ft(rec):
    """Lowest BKN/OVC layer, the ICAO ceiling. None when the sky is open."""
    bases = [c.get('base') for c in (rec.get('clouds') or [])
             if isinstance(c, dict) and c.get('cover') in CEILING_COVER and c.get('base')]
    return min(bases) if bases else None


def iso(ts):
    if not ts:
        return ''
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime('%Y-%m-%d %H:%M')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--ids', default='', help='ICAO stations, comma separated (default: derive from '
                                              'the month log through reference/airports.csv)')
    ap.add_argument('--flights', default='', help='month flights.csv to take the network from '
                        '(default: the newest "UR <MONTH> <YEAR>/flights.csv" in the publish dir)')
    ap.add_argument('--commit-dir', default='reference/weather', help='where the small, dated, '
                        'worth-keeping files go: one observations CSV per day and one merged hazard '
                        'snapshot per day. The per-station JSON in --out is scratch and is ignored.')
    ap.add_argument('--master', default='fr24_publish/reference/airports.csv')
    ap.add_argument('--hours', type=int, default=168, help='METAR depth to ask for (service caps a '
                        'station at ~400 records, about 8 days at two observations an hour)')
    ap.add_argument('--out', default='work/awx')
    ap.add_argument('--sleep', type=float, default=0.4)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    log = lambda m: (print(m), sys.stdout.flush())

    codes = [c.strip().upper() for c in a.ids.split(',') if c.strip()]
    if not a.flights:
        base = os.environ.get('FR24_PUBLISH') or 'fr24_publish'
        found = sorted(__import__('glob').glob(os.path.join(base, 'UR *', 'flights.csv')))
        a.flights = found[-1] if found else ''
        if a.flights:
            log(f'network from {os.path.relpath(a.flights, base)}')
    if not codes and a.flights:
        iata = set()
        try:
            with open(a.flights, newline='', encoding='utf-8') as fh:
                for r in csv.DictReader(fh):
                    for k in ('origin', 'dest', 'origin_icao', 'dest_icao', 'orig', 'dst'):
                        v = (r.get(k) or '').strip().upper()
                        if len(v) == 3:
                            iata.add(v)
                        elif len(v) == 4:
                            codes.append(v)
        except OSError as e:
            log(f'  cannot read {a.flights} ({e})')
        ids, _ = station_list(a.master, sorted(iata), log)
        codes = sorted(set(codes) | set(ids))
    if not codes:
        codes = ['HUEN']                                  # the one station we always want
        log(f'  no network given, using {", ".join(codes)}')
    log(f'stations: {" ".join(codes)} ({len(codes)}) · asking for the last {a.hours} h')

    os.makedirs(a.out, exist_ok=True)
    rows, answered, wrote = [], 0, 0
    per = {}
    for stn in codes:
        m = get(f'/metar?format=json&ids={stn}&hours={a.hours}', log=log)
        t = get(f'/taf?format=json&ids={stn}', log=log)
        answered += (m is not None) + (t is not None)
        if m is None and t is None:
            log(f'  {stn}: no answer')
            continue
        m, t = m or [], t or []
        per[stn] = {'metar': len(m), 'taf': len(t)}
        if not a.dry_run:
            for name, blob in ((f'metar_{stn}.json', m), (f'taf_{stn}.json', t)):
                with open(os.path.join(a.out, name), 'w') as fh:
                    json.dump(blob, fh)
                wrote += 1
        for r in m:
            rows.append({'station': stn, 'obs': iso(r.get('obsTime')), 'epoch': r.get('obsTime') or 0,
                         'temp_c': r.get('temp'), 'dewp_c': r.get('dewp'),
                         'wind_dir': r.get('wdir'), 'wind_kt': r.get('wspd'),
                         'gust_kt': r.get('wgst'), 'vis_m': r.get('visib'),
                         'altim_hpa': r.get('altim'), 'ceiling_ft': ceiling_ft(r),
                         'fltcat': r.get('fltCat'), 'raw': (r.get('rawOb') or '').strip()})
        time.sleep(a.sleep)

    haz = {}
    for prod in ('airsigmet', 'gairmet'):
        d = get(f'/{prod}?format=json', log=log)
        if d:
            mine = [x for x in d if (x.get('icaoId') or '').upper() in {c[:4] for c in codes}
                    or x.get('icaoId') in codes]
            haz[prod] = {'all': len(d), 'for_our_stations': len(mine), 'items': d}
            log(f'  {prod}: {len(d)} live worldwide, {len(mine)} naming one of our stations')
            if not a.dry_run:
                with open(os.path.join(a.out, f'hazard_{prod}.json'), 'w') as fh:
                    json.dump({'fetched_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                               'items': d}, fh)
                wrote += 1
    if not haz and not a.dry_run:
        with open(os.path.join(a.out, 'hazards_none.json'), 'w') as fh:
            json.dump({'fetched_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                       'note': 'the service answered and there was no SIGMET or AIRMET live at that '
                               'moment. Kept so that an empty night is on the record and not lost.'}, fh)
        wrote += 1

    rows.sort(key=lambda r: (r['obs'], r['station']))
    cols = ['station', 'obs', 'epoch', 'temp_c', 'dewp_c', 'wind_dir', 'wind_kt', 'gust_kt',
            'vis_m', 'altim_hpa', 'ceiling_ft', 'fltcat', 'raw']
    if rows and not a.dry_run:
        with open(os.path.join(a.out, 'observations.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        wrote += 1
    if not a.dry_run:
        with open(os.path.join(a.out, 'manifest.json'), 'w') as fh:
            json.dump({'fetched_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                       'hours': a.hours, 'stations': codes, 'per_station': per,
                       'observations': len(rows),
                       'oldest': rows[0]['obs'] if rows else None,
                       'newest': rows[-1]['obs'] if rows else None,
                       'hazards': {k: {kk: vv for kk, vv in v.items() if kk != 'items'}
                                   for k, v in haz.items()}}, fh, indent=1)
    # The two files worth committing are the day's observations and the day's hazard snapshot. The
    # SIGMET/AIRMET feed only shows what is live right now, so a day's file is merged rather than
    # replaced: both nightly runs add to it, and deduplication is by the product's own keys.
    if a.commit_dir and not a.dry_run:
        os.makedirs(a.commit_dir, exist_ok=True)
        day = dt.date.today().isoformat()
        if rows:
            with open(os.path.join(a.commit_dir, f'awx_metars_{day}.csv'), 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
            wrote += 1
        live = {}
        hp = os.path.join(a.commit_dir, f'awx_hazards_{day}.json')
        if os.path.exists(hp):
            try:
                live = json.load(open(hp))
            except Exception:                                   # noqa: BLE001
                live = {}
        for prod in ('airsigmet', 'gairmet'):
            if prod not in haz:
                continue
            seen = {(x.get('icaoId'), x.get('receiptTime'), x.get('alphaChar'))
                    for x in live.get(prod, [])}
            for x in haz[prod]['items']:
                if (x.get('icaoId'), x.get('receiptTime'), x.get('alphaChar')) not in seen:
                    live.setdefault(prod, []).append(x)
            live.setdefault('_fetched', []).append(
                {'at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'prod': prod,
                 'worldwide': haz[prod]['all']})
        if live:
            with open(hp, 'w') as fh:
                json.dump(live, fh, indent=1)
            wrote += 1
        for f in os.listdir(a.out):                             # keep only the scratch dir lean
            if f.endswith('.json') and f.startswith('metar_'):
                os.remove(os.path.join(a.out, f))

    if a.dry_run:
        log(f'\ndry run: {len(codes)} stations, {len(rows)} observations, {len(haz)} hazard products')
        return 0
    kept = a.commit_dir or "nothing"
    log(f'\nwrote {wrote} file(s) (scratch in {a.out}, kept in {kept}): '
        f'{len(rows)} observations from '
        f'{sum(1 for v in per.values() if v["metar"])} stations, '
        f'{sum(1 for v in per.values() if v["taf"])} with a live TAF')
    if not answered:
        return 4
    return 0 if rows or haz else 3


if __name__ == '__main__':
    sys.exit(main())
