#!/usr/bin/env python3
"""Cross-check the 22 September screenshot records against the published tracks.

The archive is authoritative for which callsign flew which route on which date,
so it catches OCR slips in the transcribed rows: a row that names a callsign the
archive has no track for, or a different route than the track shows, is flagged
for a visual re-read.
"""
import json, csv, collections


def archive():
    idx = collections.defaultdict(list)
    for r in csv.DictReader(open('fr24_publish/flights.csv')):
        d = r['date_local']                     # 01SEP26
        mon = {'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,'JUL':7,'AUG':8,
               'SEP':9,'OCT':10,'NOV':11,'DEC':12}[d[2:5]]
        iso = f"20{d[5:7]}-{mon:02d}-{d[0:2]}"
        idx[(r['flight'], iso)].append((r['origin'], r['dest'], r.get('source_file', '')))
    return idx


def main():
    idx = archive()
    recs = json.load(open('work/records_new.json'))
    out = collections.Counter()
    problems = []
    for r in recs:
        if not (r['month'] and r['day']):
            out['no-date'] += 1
            problems.append(('no-date', r))
            continue
        date = f"2026-{r['month']:02d}-{r['day']:02d}"
        r['date'] = date
        cs = r['callsign']
        if not cs:
            out['no-callsign'] += 1
            problems.append(('no-callsign', r))
            continue
        cands = idx.get((cs, date), [])
        r['archive_files'] = [c[2] for c in cands]
        r['archive_routes'] = [f'{c[0]}->{c[1]}' for c in cands]
        if not cands:
            r['match'] = 'none'
            out['none'] += 1
            problems.append(('none', r))
        elif any(c[0] == r['origin'] and c[1] == r['dest'] for c in cands):
            r['match'] = 'exact'
            out['exact'] += 1
        else:
            r['match'] = 'route-differs'
            out['route-differs'] += 1
            problems.append(('route-differs', r))
    print(dict(out), '\n')
    for kind, r in problems:
        print(f"{kind:14} [{r['tail']}] row{r['idx']:>3} {r.get('date')} "
              f"{r.get('flight')}/{r.get('callsign')} {r.get('origin')}->{r.get('dest')} "
              f"| archive {r.get('archive_routes', r.get('codes_all'))} "
              f"| {r['raw'][:70]}")
    json.dump(recs, open('work/records_new_checked.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
