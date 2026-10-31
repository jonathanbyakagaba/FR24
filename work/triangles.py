#!/usr/bin/env python3
"""Build the triangle-route assignment table from the screenshot records and
verify each against the published archive."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user')
import json, collections, csv, build_log as B
import repo_layout as RL
from month_ctx import iso_date as iso        # 01SEP26 -> 2026-09-01

MONTHS = [f'{y}-{m:02d}' for y in (2025, 2026) for m in range(1, 13)]


def archive():
    """(callsign, YYYY-MM-DD) -> [(origin,dest,file,dep)]  and  non-EBB sectors"""
    idx, tri = collections.defaultdict(list), []
    for mo in MONTHS:
        fl, _ = B.build('fr24_publish/FR data.zip', mo)
        for f in fl:
            d = f['dep'].strftime('%Y-%m-%d')
            idx[(f['fn'], d)].append((f['origin'], f['dest'], f['name'], f['dep']))
            if 'EBB' not in (f['origin'], f['dest']):
                tri.append(f)
    return idx, tri


def main():
    recs = json.load(open('work/records.json'))
    idx, tri = archive()
    for r in recs:
        r['date'] = f"2026-{r['month']:02d}-{r['day']:02d}" if r['month'] and r['day'] else None
        cands = idx.get((r['callsign'], r['date']), []) if r['callsign'] else []
        r['verified'] = any(c[0] == r['origin'] and c[1] == r['dest'] for c in cands)

    # --- per-date chains: group records by (date, flight) ---
    chains = collections.defaultdict(list)
    for r in recs:
        if r['date'] and r['callsign'] and r['origin']:
            chains[(r['date'], r['callsign'])].append(r)

    tri_days = []
    for (date, cs), legs in sorted(chains.items()):
        if not any('EBB' not in (l['origin'], l['dest']) for l in legs):
            continue
        tails = {l['tail'] for l in legs}
        tri_days.append((date, cs, legs, tails))

    print('=' * 100)
    print('TRIANGLE ROUTES — days where a UR flight flew a sector that does not touch Entebbe')
    print('=' * 100)
    for date, cs, legs, tails in tri_days:
        order = sorted(legs, key=lambda l: (l['idx'] < 0, l['origin']))
        chain = ' -> '.join([legs[0]['origin']] + [l['dest'] for l in order])
        fr = [l for l in legs if l['origin'] != 'EBB'][0]
        print(f"\n{date}  {fr['flight']} ({cs})   tail={ ' / '.join(sorted(tails)) }   "
              f"{'VERIFIED in archive' if any(l['verified'] for l in legs) else 'screenshot only'}")
        for l in order:
            mark = '  <-- fifth-freedom sector' if 'EBB' not in (l['origin'], l['dest']) else ''
            v = ' [archive]' if l['verified'] else ''
            print(f"    {l['origin']}->{l['dest']}{v}{mark}")

    # --- write the deliverable table ---
    rows = []
    for r in sorted(recs, key=lambda x: (x['tail'], x['date'] or '', x['idx'])):
        rows.append({'tail': r['tail'], 'date': r['date'], 'flight': r['flight'],
                     'callsign': r['callsign'], 'origin': r['origin'], 'dest': r['dest'],
                     'triangle_sector': 'Y' if r['origin'] and r['dest'] and 'EBB' not in (r['origin'], r['dest']) else '',
                     'verified_track': 'Y' if r['verified'] else ''})
    # never write tails.csv from here: the published tails table is work/final.py's product
    # and covers every record the app pages hold, while this script only knows the 233 rows of
    # work/records.json.  Running it used to cut tails.csv to a third of its size, and publish
    # duly shipped the smaller table as the archive-wide one.
    TAILS_OUT = 'work/tails_from_records.csv'
    with open(TAILS_OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['tail', 'date', 'flight', 'callsign', 'origin', 'dest',
                                           'triangle_sector', 'verified_track'])
        w.writeheader()
        w.writerows(rows)
    print(f'\nwrote {TAILS_OUT}: {len(rows)} records')
    print('   (`tails.csv` itself belongs to work/final.py, which reads every record the app '
          'pages hold; this script only knows work/records.json, so it must not overwrite it)')

    tri_rows = [r for r in rows if r['triangle_sector'] == 'Y']
    # same reason as tails.csv above: the published triangle table is work/final.py's output
    TRI_OUT = 'work/triangle_assignments_from_records.csv'
    with open(TRI_OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['date', 'flight', 'callsign', 'origin', 'dest', 'tail', 'verified_track'])
        w.writeheader()
        for r in tri_rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f'wrote {TRI_OUT}: {len(tri_rows)} rows')

    # --- coverage of the published September log ---
    import csv as _csv
    log = []
    for _p in (os.path.join(RL.live_dir(), 'flights.csv'), 'fr24_publish/flights.csv'):
        if os.path.exists(_p):
            log = list(_csv.DictReader(open(_p)))
            break
    bykey = {(r['callsign'], r['date'], r['origin'], r['dest']): r['tail'] for r in rows if r['callsign']}
    hit = sum(1 for f in log if (f['flight'], f['date_local'].replace('SEP26', '-09-').replace('SEP', ''),
                                 f['origin'], f['dest']) in bykey or
              (f['flight'], iso(f['date_local']), f['origin'], f['dest']) in bykey)
    print(f'\nSeptember log flights with a tail now: {hit} / {len(log)}')

    print('\nverified vs screenshot-only (all 233 records):')
    print('   verified in archive :', sum(1 for r in rows if r['verified_track'] == 'Y'))
    print('   screenshot only     :', sum(1 for r in rows if r['verified_track'] != 'Y'))
    print('\nper tail:')
    for t in ['5X-NIL', 'ET-APL', '5X-KOB', '5X-KDP', '5X-EQU']:
        rr = [r for r in rows if r['tail'] == t]
        print(f"   {t:6} {len(rr):3} records   {sum(1 for r in rr if r['verified_track']=='Y'):3} archive-verified   "
              f"tri {sum(1 for r in rr if r['triangle_sector']=='Y')}")


if __name__ == '__main__':
    main()
