#!/usr/bin/env python3
"""Cross-check the screenshot records against every track in the published zip."""
import json, collections, csv
import build_log as B

SRC = 'fr24_publish/FR data.zip'
MONTHS = [f'{y}-{m:02d}' for y in (2025, 2026) for m in range(1, 13)]


def archive_index():
    idx = collections.defaultdict(list)          # (callsign, YYYY-MM-DD) -> [(origin,dest,file)]
    for mo in MONTHS:
        try:
            flights, _ = B.build(SRC, mo)
        except Exception as e:
            continue
        for f in flights:
            d = f['dep'].strftime('%Y-%m-%d')
            idx[(f['fn'], d)].append((f['origin'], f['dest'], f['name']))
    return idx


def main():
    idx = archive_index()
    print(f'archive index: {sum(len(v) for v in idx.values())} UGD tracks, '
          f'{len(idx)} (callsign,date) keys\n')
    recs = json.load(open('work/records.json'))

    exact = partial = none = 0
    unknown_flight, no_route = [], []
    mism = collections.Counter()
    for r in recs:
        if r['month'] is None or r['day'] is None:
            continue
        date = f"2026-{r['month']:02d}-{r['day']:02d}"
        cands = []
        if r['callsign']:
            cands = idx.get((r['callsign'], date), [])
        r['date'] = date
        r['archive'] = [c[2] for c in cands]
        r['archive_routes'] = [f'{c[0]}->{c[1]}' for c in cands]
        if not cands:
            r['match'] = 'none'
            none += 1
        elif r['origin'] and any(c[0] == r['origin'] and c[1] == r['dest'] for c in cands):
            r['match'] = 'exact'
            exact += 1
        else:
            r['match'] = 'callsign_only'
            partial += 1
            mism[(r['callsign'], date)] += 1

        if r['origin'] is None:
            no_route.append(r)
        if r['flight'] and r['callsign'] and r['flight'][2:] != r['callsign'][3:]:
            unknown_flight.append(r)

    print(f'exact (callsign+date+route): {exact}')
    print(f'callsign+date only         : {partial}')
    print(f'no archive match           : {none}')
    print(f'incomplete route OCR       : {len(no_route)}')
    print(f'UR no != callsign no (OCR?): {len(unknown_flight)}')
    for r in unknown_flight:
        print(f"   {r['tail']} {r['date']} UR{r['flight'][2:]} vs {r['callsign']} | {r['raw'][:80]}")
    print('\nroute conflicts (record vs archive):')
    for r in recs:
        if r['match'] == 'callsign_only' and r['origin'] and r['dest']:
            print(f"   {r['tail']} {r['date']} {r['callsign']}: record {r['origin']}->{r['dest']} "
                  f"vs archive {r['archive_routes']}")
    print('\nno archive match (first 25):')
    for r in [x for x in recs if x.get('match') == 'none'][:25]:
        print(f"   {r['tail']} {r['date']} {r['flight']} {r['callsign']} "
              f"{r['origin']}->{r['dest']} conf={r['conf']} | {r['raw'][:70]}")
    json.dump(recs, open('work/records_checked.json', 'w'), indent=1)
    print('\nwrote work/records_checked.json')


if __name__ == '__main__':
    main()
