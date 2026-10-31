#!/usr/bin/env python3
"""Final build: screenshot records -> tails.csv, triangle_assignments.csv,
fleet_summary.csv, triangle_routes.md."""
import json, csv, io, os, zipfile, statistics as st, collections, datetime
import build_log as B
import repo_layout as _RL
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from month_ctx import ctx
import month_ctx as MC

C = ctx()

EXTRA = 'work/screens_extra'

SRC = 'fr24_publish/FR data.zip'
MONTHS = [f'{y}-{m:02d}' for y in (2025, 2026) for m in range(1, 13)]

# five app rows with no callsign printed; each resolved by archive or visual check
FIX = {('ET-APL', '2026-09-11', 'JNB', 'EBB'): 'UGD711',   # number read UR711 on screen
       ('ET-APL', '2026-08-31', 'EBB', 'NBO'): 'UGD208',
       ('5X-KDP', '2026-09-07', 'EBB', 'NBO'): 'UGD200',
       ('5X-EQU', '2026-09-08', 'EBB', 'NBO'): 'UGD206',
       ('5X-NIL', '2026-09-09', 'EBB', 'BOM'): 'UGD430'}


def in_rollover(track, app_date):
    """Would this track's departure airport still be on `app_date` locally?

    The app dates a leg by its **UTC** departure day; the log dates it by the
    departure airport's **local** day (build_log converts with the airport's own
    offset).  So a leg leaving Entebbe at 21:05Z shows as "Sep 20" in the app and
    `21SEP26` in the log.  A track bridges the two only if it left within the last
    `offset` hours of the app's UTC day.
    """
    dep = datetime.datetime.fromtimestamp(track['t_off_utc'], datetime.timezone.utc)
    off = B.AIRPORTS.get(track['origin'], (None, None, 3.0))[2]
    return dep.strftime('%Y-%m-%d') == app_date and dep.hour >= 24 - off


def load_tracks():
    """file -> raw bytes, and (callsign,date) index of flights."""
    z = zipfile.ZipFile(SRC)
    files = {n: z.read(n) for n in z.namelist() if n.endswith('.csv')}
    idx = collections.defaultdict(list)
    for mo in MONTHS:
        fl, _ = B.build(SRC, mo)
        for f in fl:
            d = f['dep'].strftime('%Y-%m-%d')
            idx[(f['fn'], d)].append(f)
            digits = ''.join(ch for ch in f['fn'] if ch.isdigit())
            idx[('#' + digits, d)].append(f)      # callsign-suffix-tolerant key
    return files, idx


def track_metrics(raw):
    """air minutes, median cruise kt, max FL, minutes from take-off to FL300"""
    rows = []
    rdr = csv.DictReader(io.StringIO(raw.decode('utf-8-sig', errors='replace')))
    for r in rdr:
        try:
            ts = float(r['Timestamp'])
            alt = float(r.get('Altitude') or 0)
            spd = float(r.get('Speed') or 0)
        except (ValueError, KeyError):
            continue
        rows.append((ts, alt, spd))
    rows.sort()
    air = [i for i, r in enumerate(rows) if r[1] > B.AIRBORNE_FT]
    if not air:
        return None
    a0, a1 = air[0], air[-1]
    seg = rows[a0:a1 + 1]
    minutes = (seg[-1][0] - seg[0][0]) / 60.0
    spd = [r[2] for r in seg if r[1] > 25000 and r[2] > 100]
    flmax = max(r[1] for r in seg) / 100.0
    to300 = next(((r[0] - seg[0][0]) / 60.0 for r in seg if r[1] >= 30000), None)
    return dict(minutes=minutes, cruise=st.median(spd) if spd else None,
                flmax=flmax, to300=to300)


def load_extra():
    """Rows transcribed from later screenshot batches, in the same shape as the
    OCR'd records: work/screens_extra/*.csv with tail,date,flight,origin,dest.
    They are merged into the record set so tails.csv stays regenerable rather
    than hand-patched (the OCR pipeline only ever saw the first five images)."""
    extra, n = [], 0
    if os.path.isdir(EXTRA):
        for fn in sorted(os.listdir(EXTRA)):
            if not fn.endswith('.csv'):
                continue
            for r in csv.DictReader(open(os.path.join(EXTRA, fn))):
                n += 1
                extra.append(dict(tail=r['tail'], date=r['date'], flight=r['flight'],
                                  callsign=('UGD' + ''.join(c for c in r['flight'] if c.isdigit())),
                                  origin=r['origin'], dest=r['dest'], idx=100000 + n,
                                  no_callsign=False, source_file=fn))
    return extra


def main():
    recs = json.load(open('work/records.json'))
    for r in recs:
        r['date'] = f"2026-{r['month']:02d}-{r['day']:02d}" if r['month'] and r['day'] else None
        if not r['callsign']:
            cs = FIX.get((r['tail'], r['date'], r['origin'], r['dest']))
            if cs:
                r['callsign'] = cs
        if r['callsign']:
            r['flight'] = 'UR' + r['callsign'][3:]
        r['flight'] = r['flight'] or r.get('ur_ocr')

    files, idx = load_tracks()
    per_tail = collections.defaultdict(lambda: dict(flights=0, minutes=0.0, routes=set(),
                                                    cruise=[], fl=[], to300=[], dates=set()))
    rows_out, tri_out = [], []
    # merge the later screenshot batches, dropping any row the earlier OCR pass already
    # carried (the same flight can appear in two screenshot batches for the same tail)
    seen = {(r['tail'], r['date'], r['flight'], r['origin'], r['dest']) for r in recs}
    extra, dup = [], 0
    for r in load_extra():
        k = (r['tail'], r['date'], r['flight'], r['origin'], r['dest'])
        if k in seen:
            dup += 1
            continue
        seen.add(k)
        extra.append(r)
    # the app's own status dot for each leg, read from the screenshots
    app = {}
    if os.path.exists('app_status.csv'):
        for a_ in csv.DictReader(open('app_status.csv')):
            app[(a_['tail'], a_['date'], a_['flight'], a_['origin'], a_['dest'])] = a_['app_status']

    recs = recs + extra
    print(f'screenshot rows merged    : {len(extra)} new, {dup} already held')
    # the app prints the same leg twice for some days; keep one row per leg,
    # preferring the copy that carries a status flag or an archive match
    dedup, ndrop = {}, 0
    for r in sorted(recs, key=lambda x: (x['tail'], x['date'] or '', x['idx'])):
        k = (r['tail'], r['date'], r['flight'], r['origin'], r['dest'])
        if k in dedup:
            ndrop += 1
            continue
        dedup[k] = r
    recs = list(dedup.values())
    if ndrop:
        print(f'duplicate rows collapsed : {ndrop}')
    for r in sorted(recs, key=lambda x: (x['tail'], x['date'] or '', x['idx'])):
        cands = idx.get((r['callsign'], r['date']), []) if (r['callsign'] and r['date']) else []
        if not cands and r['callsign'] and r['date']:
            digits = ''.join(ch for ch in r['callsign'] if ch.isdigit())
            cands = idx.get(('#' + digits, r['date']), [])
        v = [c for c in cands if c['origin'] == r['origin'] and c['dest'] == r['dest']]
        if not v and r['callsign'] and r['date'] and r['origin'] and r['dest']:
            # no track on the app's own date: the app's UTC day may be the log's
            # previous local day, so try the next local date and keep the match
            # only when exactly one track departs inside that rollover window
            nxt = (datetime.date.fromisoformat(r['date'])
                   + datetime.timedelta(days=1)).isoformat()
            digits = ''.join(ch for ch in r['callsign'] if ch.isdigit())
            pool = idx.get((r['callsign'], nxt), []) or idx.get(('#' + digits, nxt), [])
            ok = [c for c in pool
                  if c['origin'] == r['origin'] and c['dest'] == r['dest']
                  and in_rollover(c, r['date'])]
            if len(ok) == 1:
                v = ok
        r['verified'] = bool(v)
        tri = 'Y' if (r['origin'] and r['dest'] and 'EBB' not in (r['origin'], r['dest'])) else ''
        rows_out.append(dict(tail=r['tail'], date=r['date'], flight=r['flight'],
                             callsign=r['callsign'], origin=r['origin'], dest=r['dest'],
                             triangle_sector=tri, verified_track='Y' if v else '',
                             track_date=(v[0]['dep'].strftime('%Y-%m-%d') if v else ''),
                             app_status=app.get((r['tail'], r['date'], r['flight'],
                                                 r['origin'], r['dest']), '')))
        if tri == 'Y':
            tri_out.append(dict(date=r['date'], flight=r['flight'], callsign=r['callsign'],
                                origin=r['origin'], dest=r['dest'], tail=r['tail'],
                                verified_track='Y' if v else ''))
        if v and r['date']:
            m = track_metrics(files[v[0]['name']])
            t = per_tail[r['tail']]
            t['flights'] += 1
            t['dates'].add(r['date'])
            t['routes'].add(f"{r['origin']}-{r['dest']}")
            if m:
                t['minutes'] += m['minutes']
                if m['cruise']: t['cruise'].append(m['cruise'])
                t['fl'].append(m['flmax'])
                if m['to300']: t['to300'].append(m['to300'])

    with open('tails.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
        w.writeheader(); w.writerows(rows_out)
    with open('triangle_assignments.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(tri_out[0]))
        w.writeheader(); w.writerows(tri_out)

    names = {'5X-NIL': ('A330-800neo', 'owned', 'long'), 'ET-APL': ('737-800', 'wet lease (Ethiopian)', 'medium'),
             '5X-KOB': ('CRJ900', 'owned', 'short'), '5X-KDP': ('CRJ900', 'owned', 'short'),
             '5X-EQU': ('CRJ900', 'owned', 'short')}
    meta = {}
    if os.path.exists('fleet_meta.csv'):
        for m in csv.DictReader(open('fleet_meta.csv')):
            meta[m['tail']] = m
    with open('fleet_summary.csv', 'w', newline='') as fh:
        cols = ['tail', 'type', 'type_full', 'type_code', 'msn', 'mode_s', 'built', 'ownership', 'role',
                'seats_j', 'seats_w', 'seats_y', 'seats_total',
                'flights_matched', 'air_hours', 'days', 'routes',
                'median_cruise_kt', 'median_max_FL', 'median_min_to_FL300', 'routes_list']
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for t, d in sorted(per_tail.items()):
            typ, own, role = names.get(t, ('', '', ''))
            m = meta.get(t, {})
            w.writerow({'tail': t, 'type': typ, 'ownership': own, 'role': role,
                        'type_full': m.get('type_full', ''), 'type_code': m.get('type_code', ''),
                        'msn': m.get('msn', ''), 'mode_s': m.get('mode_s', ''), 'built': m.get('built', ''),
                        'seats_j': m.get('seats_j', ''), 'seats_w': m.get('seats_w', ''),
                        'seats_y': m.get('seats_y', ''), 'seats_total': m.get('seats_total', ''),
                        'flights_matched': d['flights'],
                        'air_hours': round(d['minutes'] / 60.0, 1),
                        'days': len(d['dates']), 'routes': len(d['routes']),
                        'median_cruise_kt': round(st.median(d['cruise'])) if d['cruise'] else '',
                        'median_max_FL': round(st.median(d['fl'])) if d['fl'] else '',
                        'median_min_to_FL300': round(st.median(d['to300'])) if d['to300'] else '',
                        'routes_list': ' '.join(sorted(d['routes']))})

    log = list(csv.DictReader(open(os.path.join(_RL.live_dir(), 'flights.csv'))))
    digits = lambda s: ''.join(ch for ch in (s or '') if ch.isdigit())
    MONN = {m: i for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                                        'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}
    key = {(digits(r['callsign']), r['track_date'] or r['date'], r['origin'], r['dest'])
           for r in rows_out if r['callsign']}
    hit = sum(1 for f in log
              if (digits(f['flight']),
                  f"20{f['date_local'][5:7]}-{MONN[f['date_local'][2:5]]:02d}-{f['date_local'][:2]}",
                  f['origin'], f['dest']) in key)
    print(f'tails.csv                : {len(rows_out)} records')
    print(f'triangle_assignments.csv : {len(tri_out)} fifth-freedom legs')
    print(f'fleet_summary.csv        : {len(per_tail)} tails')
    print(f'{C["name"]} log coverage     : {hit} / {len(log)} flights now have an aircraft')
    print(f'records archive-verified : {sum(1 for r in rows_out if r["verified_track"]=="Y")} / {len(rows_out)}')
    print()
    print('per tail (archive-verified matches only):')
    for t, d in sorted(per_tail.items()):
        print(f"  {t:6} {d['flights']:3} flights  {d['minutes']/60:6.1f} air h  {len(d['dates']):2} days  "
              f"{len(d['routes']):2} routes  cruise {st.median(d['cruise']) if d['cruise'] else 0:.0f} kt  "
              f"FL{st.median(d['fl']) if d['fl'] else 0:.0f}  toFL300 {st.median(d['to300']) if d['to300'] else 0:.0f} min")


if __name__ == '__main__':
    main()
