#!/usr/bin/env python3
"""Cross-check the 30 September app rows against the track archive.

Every row in the screenshots claims a flight number, a route and a date.  The
archive holds the legs that actually flew, and it is independent of the app, so a
row that matches a logged leg is on firm ground, and a row that does not is either

  * a leg the export is missing (which is exactly what the app pages are for), or
  * an OCR error in this pass.

Both are flagged, and the classes are kept apart: a "no track" row is fine if the
same flight number flies that route on other days, and suspicious if the number is
not a flight number this operator uses at all.

Writes work/shots30/crosscheck_30.csv and prints the rows that need a read-back.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout as RL
import csv
import collections
import re

P = RL.live_dir()          # this month's folder inside fr24_publish/
ROWS = 'work/screens_20260930_rows.csv'
OUT = 'work/shots30/crosscheck_30.csv'
MONN = {m: i for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                                    'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}


def iso(s):
    return f"20{s[5:7]}-{MONN[s[2:5]]:02d}-{s[:2]}"


def digits(s):
    return re.sub(r'\D', '', s or '')


def main():
    log = list(csv.DictReader(open(f'{P}/flights.csv')))
    by_key = {(digits(r['flight']), r['origin'], r['dest']): [] for r in log}
    for r in log:
        by_key[(digits(r['flight']), r['origin'], r['dest'])].append(iso(r['date_local']))
    route_dates = collections.defaultdict(set)          # (orig,dest) -> dates flown
    for r in log:
        route_dates[(r['origin'], r['dest'])].add(iso(r['date_local']))
    flights_seen = collections.Counter(digits(r['flight']) for r in log)
    routes_seen = {(r['origin'], r['dest']) for r in log}

    rows = list(csv.DictReader(open(ROWS)))
    out, need = [], []
    for r in rows:
        d = r['date']
        fl = digits(r['flight'])
        o, de = r['origin'], r['dest']
        v = dict(r)
        if not all([d, fl, o, de]):
            v['verdict'] = 'incomplete'
            need.append(v)
            out.append(v)
            continue
        dates = by_key.get((fl, o, de))
        same_day = dates is not None and d in dates
        other_day = bool(dates)
        alt = [k for k, vv in by_key.items() if k[0] == fl and vv and
               (k[1], k[2]) != (o, de)]
        if same_day:
            v['verdict'] = 'log-match'                  # the archive holds this exact leg
        elif other_day:
            v['verdict'] = 'log-other-day'              # same flight+route flew other days
            v['note'] = f"flies this pair on {len(dates)} day(s)"
        elif not flights_seen.get(fl):
            v['verdict'] = 'unknown-flight'             # number is not one we log at all
            need.append(v)
        elif (o, de) not in routes_seen:
            v['verdict'] = 'unknown-route'
            need.append(v)
        elif alt:
            v['verdict'] = 'route-mismatch'             # number flies, but elsewhere
            v['note'] = '; '.join(f"{a}->{b}" for a, b, _ in alt[:3])
            need.append(v)
        else:
            v['verdict'] = 'no-track'                   # plausibly a leg the export lacks
        out.append(v)

    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['image', 'slot', 'idx', 'tail', 'date', 'flight',
                                           'callsign', 'origin', 'dest', 'dot', 'conf',
                                           'verdict', 'note', 'raw'],
                           extrasaction='ignore')
        w.writeheader()
        w.writerows(out)

    c = collections.Counter(r['verdict'] for r in out)
    print('verdicts:')
    for k, n in c.most_common():
        print(f'  {k:16s} {n}')

    # per-tail coverage of the days the archive is missing aircraft for
    tails = list(csv.DictReader(open(f'{P}/tails.csv')))
    have = {(r['track_date'] or r['date'], digits(r['flight']), r['origin'], r['dest'])
            for r in tails if r['verified_track'] == 'Y'}
    log_legs = {(iso(r['date_local']), digits(r['flight']), r['origin'], r['dest'])
                for r in log}
    app = {(r['date'], digits(r['flight']), r['origin'], r['dest']) for r in out
           if r['date'] and r['flight'] and r['origin'] and r['dest']}
    missing = log_legs - have
    closeable = missing & app
    print(f'\nlog legs with no aircraft  : {len(missing)}')
    print(f'  ...named by this capture : {len(closeable)}')
    print(f'  ...still unnamed         : {len(missing - closeable)}')
    by_day = collections.Counter(d for d, *_ in missing - closeable)
    print('still unnamed, by date:')
    for d, n in sorted(by_day.items()):
        print(f'   {d}  {n}')

    print(f'\nrows needing a read-back: {len(need)}')
    for v in need[:60]:
        print(f"  {v['image'][-22:]} slot{v['slot']:>3} {v['date'] or '—':10s} "
              f"{v['flight'] or '—':7s} {v['origin'] or '—'}->{v['dest'] or '—'} "
              f"{v['dot']:5s} {v['verdict']:15s} | {(v['raw'] or '')[:66]}")


if __name__ == '__main__':
    main()
