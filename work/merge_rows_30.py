#!/usr/bin/env python3
"""Merge the OCR'd 30 September rows with their status dots.

The dot reader (work/status_dots.py) works in the original capture's pixels; the
OCR ran on the normalised capture.  Both grids are put on the same scale and each
dot is matched to the row whose top sits nearest it, as in the 22 September pass.
Residuals are printed so an off-by-one row would be visible.

Writes work/screens_20260930_rows.csv
  (image, slot, tail, date, flight, callsign, origin, dest, dot, conf, raw)
"""
import csv
import collections
import json

from PIL import Image

IMAGES = {   # capture as the dot reader saw it -> normalised file the OCR ran on
    'Screenshot_20260930_204706_Flightradar24.jpg': 'NORM_Screenshot_20260930_204706_Flightradar24.jpg',
    'Screenshot_20260930_204740_Flightradar24.jpg': 'NORM_Screenshot_20260930_204740_Flightradar24.jpg',
    'Screenshot_20260930_204826_Flightradar24.jpg': 'NORM_Screenshot_20260930_204826_Flightradar24.jpg',
    'Screenshot_20260930_204933_Flightradar24.jpg': 'NORM_Screenshot_20260930_204933_Flightradar24.jpg',
    'Screenshot_20260930_205018_Flightradar24.jpg': 'NORM_Screenshot_20260930_205018_Flightradar24.jpg',
    'Screenshot_20260930_205121_Flightradar24.jpg': 'NORM_Screenshot_20260930_205121_Flightradar24.jpg',
}
TAIL = {'NORM_Screenshot_20260930_204706_Flightradar24.jpg': '5X-EQU',
        'NORM_Screenshot_20260930_204740_Flightradar24.jpg': '5X-KDP',
        'NORM_Screenshot_20260930_204826_Flightradar24.jpg': '5X-EQU',
        'NORM_Screenshot_20260930_204933_Flightradar24.jpg': '5X-KOB',
        'NORM_Screenshot_20260930_205018_Flightradar24.jpg': 'ET-APL',
        'NORM_Screenshot_20260930_205121_Flightradar24.jpg': '5X-NIL'}
FIXED = 'work/shots30/records_30_checked.json'      # written after read-back


def load_records():
    import os
    src = FIXED if os.path.exists(FIXED) else 'work/shots30/records_30.json'
    print(f'records: {src}')
    return json.load(open(src))


def main():
    dots = collections.defaultdict(dict)
    for r in csv.DictReader(open('work/status_dots.csv')):
        dots[r['image']][int(r['slot'])] = (int(r['y']), r['colour'])

    raw_rows = json.load(open('work/shots30/ocr_rows_30.json'))
    recs = load_records()
    rowy = {(rr['image'].replace('NORM_', ''), rr['idx']): rr['y'] for rr in raw_rows}
    checked = {(r['image'], r['idx']): r for r in recs}

    out = []
    for img_dot, img_ocr in IMAGES.items():
        d = dict(dots.get(img_dot, {}))
        sc = (Image.open('work/shots30/' + img_ocr).size[1]
              / Image.open('uploads/' + img_dot).size[1])
        if abs(sc - 1.0) > 0.01:
            d = {k: (int(round(y * sc)), c) for k, (y, c) in d.items()}
            print(f'    (scaled dot ys x{sc:.2f})')
        tail = TAIL[img_ocr]
        slots = sorted(d)
        print(f'--- {img_dot}  tail={tail}  dots={len(slots)}')
        used, no_row = set(), 0
        for slot in slots:
            dy, col = d[slot]
            best, bestdy = None, 9999
            for idx in range(1, 300):
                y = rowy.get((img_dot, idx))
                if y is None:
                    continue
                if abs(y - dy) < bestdy:
                    best, bestdy = idx, abs(y - dy)
            r = checked.get((img_ocr, best))
            used.add(best)
            if bestdy > 60 or r is None:
                no_row += 1
                print(f'    slot {slot:>3} y={dy} -> NO ROW (nearest idx {best} at {bestdy} px)')
                continue
            # the app prints N/A for a leg whose airport it does not hold.  Every
            # such row in this batch is the Hoima service, for which the app has no
            # airport record and which this build carries as UG-0013, so the code is
            # mapped here, once, and what the app actually printed is kept alongside
            shows = [r.get('origin'), r.get('dest')]
            hoima = '523' in str(r.get('flight') or '') or '523' in str(r.get('callsign') or '')
            o, de = ('UG-0013' if (x == 'N/A' and hoima) else x for x in shows)
            out.append(dict(image=img_dot, slot=slot, tail=tail,
                            date=(f"2026-{r['month']:02d}-{r['day']:02d}"
                                  if r.get('month') and r.get('day') else ''),
                            flight=r.get('flight'), callsign=r.get('callsign'),
                            origin=o, dest=de, app_shows='/'.join(str(x) for x in shows),
                            dot=col, conf=r.get('conf'), raw=r.get('raw'),
                            idx=best, res=bestdy))
        missing = [i for i in range(1, 300)
                   if rowy.get((img_dot, i)) is not None and i not in used]
        if missing:
            print(f'    NOTE rows without a dot slot: {missing}')
        print(f'    dots matched: {len(slots) - no_row}/{len(slots)}')

    with open('work/screens_20260930_rows.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['image', 'slot', 'tail', 'date', 'flight',
                                           'callsign', 'origin', 'dest', 'dot', 'conf',
                                           'idx', 'res', 'raw'], extrasaction='ignore')
        w.writeheader()
        w.writerows(out)
    print(f'\nwrote work/screens_20260930_rows.csv: {len(out)} rows')

    bad = [r for r in out if not all([r['date'], r['flight'], r['origin'], r['dest']])]
    print(f'rows with a field missing: {len(bad)}')
    for r in bad[:40]:
        print(f"   {r['image'][-22:]} slot{r['slot']:>3} {r['date'] or '—':10s} "
              f"{r['flight'] or '—':7s} {r['origin'] or '—'}->{r['dest'] or '—'} "
              f"{r['dot']:5s} | {(r['raw'] or '')[:70]}")

    by = collections.Counter((r['tail'], r['date'][:10]) for r in out)
    print(f'\nrows per tail: {dict(collections.Counter(r["tail"] for r in out))}')
    dots_by = collections.Counter(r['dot'] for r in out)
    print(f'dots: {dict(dots_by)}')


if __name__ == '__main__':
    main()
