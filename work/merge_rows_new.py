#!/usr/bin/env python3
"""Merge the OCR'd 22 September rows with the status dots into one table.

Both come out of their own detectors, so the two grids are aligned by y: the dot
whose y sits nearest a row's top is that row's dot.  Residuals are printed so an
off-by-one row would be visible.

Writes work/screens_20260922_rows.csv  (image,slot,tail,date,flight,origin,dest,dot,conf)
"""
import json, csv, collections, os

IMAGES = {           # capture file as the dot reader saw it -> normalised file used for OCR
    'Screenshot_20260922_075929_Flightradar24.jpg': 'NORM_Screenshot_20260922_075929_Flightradar24.jpg',
    'Screenshot_20260922_080019_Flightradar24.jpg': 'NORM_Screenshot_20260922_080019_Flightradar24.jpg',
    'Screenshot_20260922_080059_Flightradar24.jpg': 'NORM_Screenshot_20260922_080059_Flightradar24.jpg',
    'Screenshot_20260922_080302_Flightradar24.jpg': 'NORM_Screenshot_20260922_080302_Flightradar24.jpg',
    'Screenshot_20260922_080438_Flightradar24.jpg': 'NORM_Screenshot_20260922_080438_Flightradar24.jpg',
}
TAIL = {'NORM_Screenshot_20260922_075929_Flightradar24.jpg': 'ET-APL',
        'NORM_Screenshot_20260922_080019_Flightradar24.jpg': '5X-KDP',
        'NORM_Screenshot_20260922_080059_Flightradar24.jpg': '5X-KOB',
        'NORM_Screenshot_20260922_080302_Flightradar24.jpg': '5X-NIL',
        'NORM_Screenshot_20260922_080438_Flightradar24.jpg': '5X-EQU'}


def main():
    dots = collections.defaultdict(dict)
    for r in csv.DictReader(open('work/status_dots.csv')):
        dots[r['image']][int(r['slot'])] = (int(r['y']), r['colour'])

    raw_rows = json.load(open('work/ocr_rows_new.json'))
    recs = json.load(open('work/records_new_checked.json'))
    rowy = {}
    for rr in raw_rows:
        rowy[(rr['image'].replace('NORM_', ''), rr['idx'])] = rr['y']
    # rebuild the callsign->record map (checked file is a superset of records_new)
    checked = {}
    for r in recs:
        checked[(r['image'], r['idx'])] = r

    out = []
    from PIL import Image
    for img_dot, img_ocr in IMAGES.items():
        d = dict(dots.get(img_dot, {}))
        # one capture is a half-scale copy; put its dot grid on the same scale as
        # the normalised image the OCR ran on
        sc = Image.open('work/newshots/' + img_ocr).size[1] / Image.open('uploads/' + img_dot).size[1]
        if abs(sc - 1.0) > 0.01:
            d = {k: (int(round(y * sc)), c) for k, (y, c) in d.items()}
            print(f'    (scaled dot ys x{sc:.2f})')
        tail = TAIL[img_ocr]
        slots = sorted(d)
        print(f'--- {img_dot}  tail={tail}  dots={len(slots)}')
        used = set()
        for slot in slots:
            dy, col = d[slot]
            # nearest OCR row top on the full-res-normalised grid
            best, bestdy = None, 999
            for idx in range(1, 200):
                y = rowy.get((img_dot, idx))
                if y is None:
                    continue
                if abs(y - dy) < bestdy:
                    best, bestdy = idx, abs(y - dy)
            r = checked.get((img_ocr, best))
            used.add(best)
            if bestdy > 60:
                print(f'    slot {slot:>3} y={dy} -> no row (nearest row {best} at {bestdy} px)')
                continue
            out.append(dict(image=img_dot, slot=slot, tail=tail,
                            date=r.get('date'), flight=r.get('flight'),
                            callsign=r.get('callsign'), origin=r.get('origin'),
                            dest=r.get('dest'), dot=col, conf=r.get('conf'),
                            match=r.get('match'), raw=r.get('raw')))
        missing = [i for i in range(1, 200) if rowy.get((img_dot, i)) is not None and i not in used]
        if missing:
            print(f'    NOTE rows without a dot slot: {missing}')

    with open('work/screens_20260922_rows.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['image', 'slot', 'tail', 'date', 'flight',
                                           'callsign', 'origin', 'dest', 'dot', 'conf',
                                           'match', 'raw'], extrasaction='ignore')
        w.writeheader(); w.writerows(out)
    print(f'\nwrote work/screens_20260922_rows.csv: {len(out)} rows')
    by = collections.Counter((r['tail'], r['date'][:10] if r['date'] else None) for r in out)
    for (t, d), n in sorted(by.items()):
        print(f'   {t:7s} {d}  {n}')


if __name__ == '__main__':
    main()
