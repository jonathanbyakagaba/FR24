#!/usr/bin/env python3
"""App status flags from the per-tail screenshots, joined to the flight records.

The dot colour on each app row is the app's own statement about the flight:

    green   normal          amber  delayed
    red     cancelled       grey   no data / duplicate row

and it is read mechanically in work/status_dots.py.  This script pairs each dot
with the row it belongs to — the earlier OCR pass for the 11 September captures,
the hand-checked transcription for the 12 September ones — and writes
app_status.csv, then folds the flag into tails.csv.

Where the same flight appears in both captures the later capture wins, because
a status can only firm up as the day goes on; disagreements are reported.
"""
import csv, json, collections, os

DOTS = 'work/status_dots.csv'
# one entry per capture batch, discovered rather than listed: a batch is
# `work/screens_<YYYYMMDD>_rows.csv`, or `..._final.csv` when the rows have been
# read back and checked (the checked file then replaces the raw one for that day).
import glob


def batch_files():
    found = {}
    for path in sorted(glob.glob('work/screens_20??????_*.csv')):
        stem = os.path.basename(path).split('_')[1]
        kind = 'final' if path.endswith('_final.csv') else 'rows'
        if kind == 'final' or stem not in found:
            found[stem] = path
    return [found[k] for k in sorted(found)]


ROWS12 = 'work/screens_20260912_rows.csv'
RECORDS = 'work/records.json'
OUT = 'app_status.csv'

OLD = {'Screenshot_20260911_124304_Flightradar24.jpg': '5X-NIL',
       'Screenshot_20260911_124414_Flightradar24.jpg': 'ET-APL',
       'Screenshot_20260911_124506_Flightradar24.jpg': '5X-KOB',
       'Screenshot_20260911_124545_Flightradar24.jpg': '5X-KDP',
       'Screenshot_20260911_124626_Flightradar24.jpg': '5X-EQU'}
NEW = {'Screenshot_20260912_093906_Flightradar24.jpg': '5X-KOB',
       'Screenshot_20260912_093928_Flightradar24.jpg': '5X-EQU',
       'Screenshot_20260912_094003_Flightradar24.jpg': '5X-NIL',
       'Screenshot_20260912_094017_Flightradar24.jpg': 'ET-APL',
       'Screenshot_20260912_094040_Flightradar24.jpg': '5X-KDP'}
MAP22 = {'Screenshot_20260922_075929_Flightradar24.jpg': 'ET-APL',
         'Screenshot_20260922_080019_Flightradar24.jpg': '5X-KDP',
         'Screenshot_20260922_080059_Flightradar24.jpg': '5X-KOB',
         'Screenshot_20260922_080302_Flightradar24.jpg': '5X-NIL',
         'Screenshot_20260922_080438_Flightradar24.jpg': '5X-EQU'}
MAP30 = {'Screenshot_20260930_204706_Flightradar24.jpg': '5X-EQU',
         'Screenshot_20260930_204740_Flightradar24.jpg': '5X-KDP',
         'Screenshot_20260930_204826_Flightradar24.jpg': '5X-EQU',
         'Screenshot_20260930_204933_Flightradar24.jpg': '5X-KOB',
         'Screenshot_20260930_205018_Flightradar24.jpg': 'ET-APL',
         'Screenshot_20260930_205121_Flightradar24.jpg': '5X-NIL'}
ROWS22 = 'work/screens_20260922_final.csv'
ROWS30 = 'work/screens_20260930_rows.csv'
CAPTURE = {'20260911': '2026-09-11 12:4x', '20260912': '2026-09-12 09:4x',
           '20260922': '2026-09-22 07:5x-08:0x',
           '20260930': '2026-09-30 20:4x-20:5x'}
def rank(cap):
    """later capture wins — the date in the filename *is* the order, so a new capture
    batch needs no table editing here"""
    return (cap or '')[:8]


def cap_of(image):
    if image in NEW:
        return '20260912'
    if image in MAP22:
        return '20260922'
    if image in MAP30:
        return '20260930'
    return '20260911'


def dots():
    out = collections.defaultdict(dict)
    for r in csv.DictReader(open(DOTS)):
        out[r['image']][int(r['slot'])] = r['colour']
    return out


def rows_old():
    """the OCR rows, in the order they appear down the capture"""
    recs = json.load(open(RECORDS))
    by = collections.defaultdict(list)
    for r in recs:
        by[r['image']].append(r)
    out = []
    for img, rs in by.items():
        for i, r in enumerate(sorted(rs, key=lambda x: x['idx']), 1):
            out.append(dict(image=img, slot=i, tail=r['tail'],
                            date=f"2026-{r['month']:02d}-{r['day']:02d}",
                            flight=r['flight'], origin=r['origin'], dest=r['dest']))
    return out


def main():
    d = dots()
    rows = rows_old()
    for src in batch_files():
        for r in csv.DictReader(open(src)):
            r['slot'] = int(r['slot'])
            rows.append(r)

    seen, flags = {}, []
    for r in rows:
        col = d.get(r['image'], {}).get(r['slot'], '')
        if not col or col == 'none':
            continue
        cap = cap_of(r['image'])
        key = (r['tail'], r['date'], r['flight'], r['origin'], r['dest'])
        rec = dict(tail=r['tail'], date=r['date'], flight=r['flight'],
                   origin=r['origin'], dest=r['dest'], app_status=col,
                   capture=CAPTURE.get(cap) or f'{cap[:4]}-{cap[4:6]}-{cap[6:]} (time not recorded)',
                   image=r['image'], slot=r['slot'],
                   note=(r.get('note') or ''))
        if key in seen:
            prev = seen[key]
            prev_cap = cap_of(prev['image'])
            if cap == prev_cap:
                # the app prints a grey ghost row next to the real one for some
                # legs; the coloured row is the one carrying the status
                if prev['app_status'] == 'grey' and col != 'grey':
                    rec['note'] = (rec.get('note', '') + ' the same capture also carried a grey row').strip()
                    seen[key] = rec
                else:
                    prev['note'] = (prev.get('note', '') + 'repeated in the same capture').strip()
                continue
            if rank(cap) > rank(prev_cap):
                older, newer = prev, rec
            else:
                older, newer = rec, prev
            if older['app_status'] != newer['app_status']:
                newer['note'] = (f"earlier capture said {older['app_status']}"
                                 + (f"; {newer['note']}" if newer['note'] else ''))
            seen[key] = newer
            continue
        seen[key] = rec

    flags = list(seen.values())
    flags.sort(key=lambda r: (r['date'], r['flight'], r['tail']))
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['tail', 'date', 'flight', 'origin', 'dest',
                                           'app_status', 'capture', 'image', 'slot', 'note'])
        w.writeheader()
        for r in flags:
            w.writerow({k: r.get(k, '') for k in w.fieldnames})

    by = collections.Counter(r['app_status'] for r in flags)
    print(f'wrote {OUT}: {len(flags)} flagged rows  {dict(by)}')
    for r in flags:
        if r['app_status'] != 'green' or r.get('note'):
            print(f"  {r['date']} {r['tail']:7s} {r['flight']} {r['origin']}-{r['dest']:4s} "
                  f"{r['app_status']:6s} {r.get('note','')}")

    # ---------------------------------------------------------- validation ---
    tails = list(csv.DictReader(open('tails.csv')))
    arch = {(r['tail'], r['date'], r['flight'], r['origin'], r['dest']): r for r in tails}
    print('\nagainst the track archive:')
    for status in ('green', 'amber', 'red', 'grey'):
        sub = [r for r in flags if r['app_status'] == status]
        if not sub:
            continue
        have = sum(1 for r in sub
                   if (r['tail'], r['date'], r['flight'], r['origin'], r['dest']) in arch)
        print(f'  {status:6s} {have:3d} of {len(sub):3d} present in tails.csv')


if __name__ == '__main__':
    main()
