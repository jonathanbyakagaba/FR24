#!/usr/bin/env python3
r"""Fetch Uganda Airlines track history from Flightradar24 and write it in the shape this
repository already uses: one CSV per flight, `<FLIGHT>-<id>.csv`, seven columns.

    python3 tools/fetch_fr24.py --since 2026-10-26 --out work/ci_capture
    python3 tools/fetch_fr24.py --flights UR209,UR111 --dry-run
    python3 fr24_update.py --zip work/ci_capture/FR\ data.zip --month 2026-10   # then the usual chain

Two endpoints, both the ones flightradar24.com's own map page uses, and both answer from a
datacenter IP with no key:

  list   `api.flightradar24.com/common/v1/flight/list.json?query=<n>&fetchBy=flight&mode=original`
  trail  `data-live.flightradar24.com/clickhandler/?version=1.5&flight=<id>`

**The one fact that shapes this whole tool: `trail` is not history.** It is the live map's
buffer, and it survives about three to five days after landing. Measured on 30/31 Oct 2026:
`UR209` on 27 Oct returned its full 260-point trail, `UR209` on 24 Oct returned the flight
record with an empty trail. So a *frequent* run loses nothing, while a run after a fortnight
silently fetches nothing. That is why the nightly workflow exists, why `--since` defaults to
short, and why `empty` is reported as loudly as `captured`: an empty result here means "too
late", not "did not fly". Full history behind the account's own download is not reimplemented
here on purpose.

Politeness is not a nicety on these endpoints: one request per flight number, one per new
flight, `--sleep` between them, backoff on 429/5xx. A fleet of ~30 flight numbers costs about
40 requests, which is what a human clicking the page would spend.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API = 'https://api.flightradar24.com/common/v1'
LIVE = 'https://data-live.flightradar24.com'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/120.0.0.0 Safari/537.36')
HEADER = ['Timestamp', 'UTC', 'Callsign', 'Position', 'Altitude', 'Speed', 'Direction']


def get(url, tries=4, log=None):
    """GET with backoff. 429 and 5xx are retried; a 4xx that is not 429 is a real answer."""
    delay = 2.0
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA,
                                                        'Accept': 'application/json',
                                                        'Accept-Language': 'en-GB,en;q=0.9'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(delay)
                delay *= 2.5
                continue
            if log:
                log(f'    ! {e.code} {url[:110]}')
            return None
        except Exception as e:                                    # noqa: BLE001
            if i < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if log:
                log(f'    ! {type(e).__name__} {e} {url[:90]}')
            return None
    return None


def known_ids(archive):
    """The flight ids already in the archive, read out of the filenames.

    `UR110-420b1d5b.csv` carries its id in the suffix and `3e02c7e0.csv` is the id alone, so
    the last stem of every name is the id — which is what makes a resume cheap and exact.
    """
    out = set()
    if not archive or not os.path.exists(archive):
        return out
    with zipfile.ZipFile(archive) as z:
        for n in z.namelist():
            if not n.lower().endswith('.csv'):
                continue
            stem = os.path.splitext(os.path.basename(n))[0]
            out.add(stem.split('-')[-1].lower())
    return out


def flight_numbers(path):
    """Distinct IATA flight numbers out of a month log or manifest.

    The log's `flight` column holds the radio callsign (`UGD209`), not the flight number, so
    the number is taken from the `source_file` prefix (`UR209-41e99651.csv`) where there is
    one — that is the name the build gave the track, so it cannot disagree with the archive —
    and a bare UGD/UGA callsign is folded to `UR` as the fallback. Hash-only filenames and
    non-UR operators contribute nothing, which is correct: their number is not ours to guess.
    """
    nums = set()
    with open(path, newline='', encoding='utf-8', errors='replace') as fh:
        for r in csv.DictReader(fh):
            for key in ('source_file', 'file'):
                m = re.match(r'^([A-Z0-9]{2}\d{2,4})-[0-9a-f]{6,8}\.csv$',
                             (r.get(key) or '').strip())
                if m:
                    nums.add(m.group(1).upper())
                    break
            else:
                cs = (r.get('flight') or r.get('callsign') or '').strip().upper()
                if re.fullmatch(r'UG[DAZ]\d{2,4}', cs):
                    nums.add('UR' + cs[3:])
    return sorted(nums)


def listings(num, limit, log):
    """Recent flights of one number, newest first, as flat records."""
    q = urllib.parse.urlencode({'query': num, 'fetchBy': 'flight', 'mode': 'original',
                                'limit': limit})
    j = get(f'{API}/flight/list.json?{q}', log=log)
    rows = []
    for it in ((j or {}).get('result', {}).get('response', {}) or {}).get('data') or []:
        ident = it.get('identification') or {}
        t = it.get('time') or {}
        real, sch = t.get('real') or {}, t.get('scheduled') or {}
        ap = it.get('airport') or {}
        dep = real.get('departure') or sch.get('departure')
        rows.append({
            'id': ident.get('id'), 'row': ident.get('row'),
            'number': ((ident.get('number') or {}).get('default') or num).upper(),
            'callsign': ident.get('callsign') or '',
            'status': (it.get('status') or {}).get('text') or '',
            'dep': dep, 'arr': real.get('arrival') or t.get('estimated', {}).get('arrival'),
            'origin': ((ap.get('origin') or {}).get('code') or {}).get('iata') or '',
            'dest': ((ap.get('destination') or {}).get('code') or {}).get('iata') or '',
        })
    return rows


def fixes(flight_id, log):
    """The map's trail for one flight, ascending in time. Empty list means 'too old', not 'no flight'."""
    j = get(f'{LIVE}/clickhandler/?version=1.5&flight={urllib.parse.quote(str(flight_id))}', log=log)
    r = (j or {}).get('result') if isinstance((j or {}).get('result'), dict) else j
    src = r or {}
    tr = src.get('track') or src.get('trail') or []
    out = []
    for p in tr:
        try:
            ts = int(p['ts'])
        except Exception:                                        # noqa: BLE001
            continue
        out.append({'ts': ts, 'lat': float(p['lat']), 'lon': float(p['lng']),
                    'alt': int(float(p.get('alt') or 0)), 'spd': int(float(p.get('spd') or 0)),
                    'hd': int(float(p.get('hd') or 0))})
    out.sort(key=lambda p: p['ts'])
    return out


def write_csv(path, rec, pts):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(HEADER)
    cs = rec['callsign'] or ''
    for p in pts:
        w.writerow([p['ts'], dt.datetime.fromtimestamp(p['ts'], dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    cs, f"{p['lat']:.6f},{p['lon']:.6f}", p['alt'], p['spd'], p['hd']])
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(buf.getvalue())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--flights', default='', help='comma list of flight numbers (default: read --from-log)')
    ap.add_argument('--from-log', default='fr24_publish/UR OCTOBER 2026/flights.csv',
                    help='flights.csv to take the fleet of numbers from')
    ap.add_argument('--since', default='', help='first departure date, YYYY-MM-DD (default: 4 days ago)')
    ap.add_argument('--until', default='', help='last departure date, inclusive')
    ap.add_argument('--out', default='work/ci_capture', help='where to write the CSVs and the zip')
    ap.add_argument('--archive', default='fr24_publish/FR data.zip',
                    help='archive to skip already-held ids against ("" to disable)')
    ap.add_argument('--limit', type=int, default=30, help='listings fetched per flight number')
    ap.add_argument('--min-fixes', type=int, default=8, help='ignore trails thinner than this')
    ap.add_argument('--sleep', type=float, default=2.5, help='seconds between requests (a 429 '
                        'arrives below about two); 429 and 5xx are retried with backoff')
    ap.add_argument('--cap', type=int, default=400, help='stop after this many captures')
    ap.add_argument('--zip-name', default='FR data.zip')
    ap.add_argument('--dry-run', action='store_true', help='list what would be fetched, write nothing')
    a = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    since = (dt.date.fromisoformat(a.since) if a.since else (now - dt.timedelta(days=4)).date())
    until = dt.date.fromisoformat(a.until) if a.until else now.date()
    nums = ([n.strip().upper() for n in a.flights.split(',') if n.strip()] if a.flights
            else (flight_numbers(a.from_log) if os.path.exists(a.from_log) else []))
    if not nums:
        raise SystemExit(f'no flight numbers: pass --flights or point --from-log at a flights.csv '
                         f'(looked at {a.from_log})')
    have = known_ids(a.archive)
    log = lambda s: (print(s), sys.stdout.flush())
    log(f'fetch: {len(nums)} flight numbers · departures {since} to {until} · '
        f'{len(have):,} ids already in {a.archive or "(no archive)"}')

    os.makedirs(a.out, exist_ok=True)
    files, rec_rows = [], []
    seen = new = empty = skipped = out_of_window = 0
    for num in nums:
        recs = [r for r in listings(num, a.limit, log) if r['id']]
        for r in recs:
            seen += 1
            if not r['dep']:
                skipped += 1                                    # scheduled, not flown yet
                continue
            d = dt.datetime.fromtimestamp(r['dep'], dt.timezone.utc).date()
            if not (since <= d <= until):
                out_of_window += 1
                continue
            if r['id'].lower() in have:
                skipped += 1
                continue
            time.sleep(a.sleep)
            pts = fixes(r['id'], log)
            if len(pts) < a.min_fixes:
                empty += 1
                log(f'  {num} {d} {r["origin"]}->{r["dest"]:4} id={r["id"]}  '
                    f'{"empty trail — too old to fetch" if not pts else "only %d fixes" % len(pts)}')
                continue
            name = f"{r['number']}-{r['id']}.csv"
            p = os.path.join(a.out, name)
            if a.dry_run:
                log(f'  would write {name}: {len(pts)} fixes '
                    f'{time.strftime("%m-%d %H:%M", time.gmtime(pts[0]["ts"]))} -> '
                    f'{time.strftime("%m-%d %H:%M", time.gmtime(pts[-1]["ts"]))}')
            else:
                write_csv(p, r, pts)
                files.append(p)
                log(f'  wrote {name}: {len(pts)} fixes, {r["status"]}')
            new += 1
            rec_rows.append({**r, 'dep_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(r['dep'])),
                             'fixes': len(pts),
                             'first_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(pts[0]['ts'])),
                             'last_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(pts[-1]['ts']))})
            if new >= a.cap:
                log(f'  --cap {a.cap} reached, stopping')
                break
        time.sleep(a.sleep)
    if a.dry_run:
        log(f'\ndry run: {new} flight(s) would be fetched, {empty} too old, '
            f'{skipped} already held, {out_of_window} outside the window')
        return 0

    zpath = os.path.join(a.out, a.zip_name)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(files):
            z.write(p, os.path.basename(p))
    with open(os.path.join(a.out, 'capture_manifest.json'), 'w') as fh:
        json.dump({'fetched_utc': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'since': str(since),
                   'until': str(until), 'listings_seen': seen, 'captured': new,
                   'too_old_or_thin': empty, 'already_held_or_scheduled': skipped,
                   'files': [os.path.basename(p) for p in sorted(files)], 'flights': rec_rows},
                  fh, indent=1)
    log(f'\ncaptured {new} of {seen} listing(s): {empty} too old or thin, '
        f'{skipped} already held or not flown')
    if new:
        log(f'zip: {zpath} ({os.path.getsize(zpath):,} B, {len(files)} files)')
        log('next: python3 fr24_update.py --zip "%s" --month auto' % zpath)
    else:
        log('nothing new to write — the zip was not rebuilt')
    return 0 if new else 3 if empty == 0 else 0


if __name__ == '__main__':
    sys.exit(main())
