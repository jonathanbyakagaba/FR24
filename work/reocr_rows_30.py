#!/usr/bin/env python3
"""Second-pass OCR for the 30 September rows the first pass could not read.

The grid pass OCRs a whole slice at 2x.  That is right for most rows, but on these
tall captures the date line comes back mangled on some of them: the app renders the
day number in a way that ghosts a second token into the text, so a row that reads
`Sep 26` in the pixels can arrive as `Sep 74 26`.  For every suspect row this script
crops the row's three text lines out of the normalised capture using the *positions*
the first pass found (its positions are reliable even where its text was not), blows
each line up 4x, and OCRs it alone.

A row is suspect when, on the running set of records, it

  * is missing a date, a flight number, an origin or a destination, or
  * carries a date the calendar does not have (31 September, 26/74), or
  * disagrees with the run of dates either side of it (the app lists one aircraft's
    flights in order, so a row dated differently from both neighbours is a misread).

The retry is cumulative and idempotent: it starts from work/shots30/records_30_checked
.json where that exists, so re-running never loses an earlier repair.  A retry only
overwrites a field when it beats what is already there; `N/A` is kept as a value,
because that is what the app itself prints for a leg whose airport it does not hold.

    python3 work/reocr_rows_30.py            # writes records_30_checked.json
"""
import collections
import csv
import datetime
import json
import os
import re
import subprocess

from PIL import Image

SHOTS = 'work/shots30'
OCR = f'{SHOTS}/ocr_rows_30.json'
BASE = f'{SHOTS}/records_30.json'
FIXED = f'{SHOTS}/records_30_checked.json'
PITCH = 203
CODES = {'EBB', 'NBO', 'DAR', 'JNB', 'LUN', 'HRE', 'BJM', 'MGQ', 'ZNZ', 'JRO',
         'MBA', 'LGW', 'BOM', 'DXB', 'DOH', 'ADD', 'KGL', 'FIH', 'LOS', 'ABJ',
         'JUB', 'SEZ', 'MRU', 'CAI', 'IST', 'BRU', 'AMS', 'JED', 'N/A'}
MONTHS = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7,
          'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
MONTH_RE = '|'.join(MONTHS)


def ocr_line(im, tag):
    p = f'work/ocr/rb_{tag}.png'
    im.save(p)
    r = subprocess.run(['tesseract', p, 'stdout', '--psm', '7'],
                       capture_output=True, text=True)
    return ' '.join(r.stdout.split())


def valid(rec):
    if not (rec.get('month') and rec.get('day')):
        return False
    try:
        datetime.date(2026, rec['month'], rec['day'])
    except ValueError:
        return False
    return True


def iso(rec):
    return f"2026-{rec['month']:02d}-{rec['day']:02d}" if valid(rec) else None


def complete(rec):
    return bool(iso(rec) and (rec.get('flight') or rec.get('callsign')
                              or rec.get('label'))
                and rec.get('origin') and rec.get('dest'))


def suspects(recs):
    """The rows worth a second look, judged against the whole record set."""
    order = collections.defaultdict(list)
    for r in sorted(recs, key=lambda r: r['idx']):
        d = iso(r)
        if d:
            order[r['image']].append((r['idx'], d))
    out = []
    for r in recs:
        if r.get('header'):
            continue                       # the photo/header block, not a flight row
        if not complete(r):
            out.append(r)
            continue
        run = order[r['image']]
        i = [j for j, (k, _) in enumerate(run) if k == r['idx']][0]
        prev = run[i - 1][1] if i > 0 else None
        nxt = run[i + 1][1] if i + 1 < len(run) else None
        if prev and nxt and prev == nxt and iso(r) != prev and len(run) > 4:
            out.append(r)
    return out


def main():
    os.makedirs('work/ocr', exist_ok=True)
    src = FIXED if os.path.exists(FIXED) else BASE
    recs = json.load(open(src))
    print(f'base: {src}  ({len(recs)} records)')

    grid, boxes = {}, {}
    for r in json.load(open(OCR)):
        k = (r['image'].replace('NORM_', ''), r['idx'])
        grid.setdefault(k[0], {})[k[1]] = r['y']
        boxes[k] = [l['top'] for l in r['lines']]

    todo = suspects(recs)
    print(f'rows to re-read: {len(todo)}')

    fixed = 0
    for rec in todo:
        img = rec['image'].replace('NORM_', '')
        idx = rec['idx']
        y = grid.get(img, {}).get(idx)
        lb = boxes.get((img, idx))
        if y is None or not lb:
            print(f'{img[-10:-4]} idx{idx:>3} no grid/line box — skipped')
            continue
        if len(lb) < 3:
            # one or two lines only: the header and photo block at the top of a
            # capture, which the grid counts as slots but which carries no flight
            rec['header'] = True
            print(f'{img[-10:-4]} idx{idx:>3} header block ({len(lb)} line(s)) — skipped')
            continue
        srci = Image.open(f'{SHOTS}/NORM_{img}')
        got = []
        for i, top2 in enumerate(sorted(lb)[:3]):
            y0 = max(0, top2 // 2 - 16)
            y1 = min(srci.size[1], y0 + 62)
            ln = srci.crop((0, y0, 560, y1))          # text column only
            up = ln.convert('L').resize((ln.width * 4, ln.height * 4), Image.LANCZOS)
            up = up.point(lambda p: 0 if p < 140 else 255)
            got.append(ocr_line(up, f'{img[-10:-4]}_{idx}_{i}'))
        head, orig, dest = got

        m = re.search(rf'({MONTH_RE})\s*(\d{{1,2}})', head.upper())
        if m:
            rec['month'], rec['day'] = MONTHS[m.group(1)[:3]], int(m.group(2))
            if not valid(rec):
                rec['day'] = None
        m = re.search(r'UR\s*[/Il]?(\d{2,4})[A-Z]?', head.upper())
        if m:
            rec['ur_ocr'] = 'UR' + m.group(1)
        m = re.search(r'\(\s*[A-Z]{1,3}[UuGg][Dd]\s*(\d{3})', head)
        if m:
            rec['callsign'] = 'UGD' + m.group(1)
        elif not m:
            m = re.search(r'\b(UGD\d{3}[A-Z]?)\b', head.upper())
            if m:
                rec['callsign'] = m.group(1)
            else:
                m = re.search(r'\b(TEST|KDP|EQU|KOB|NIL|APL)\b', head.upper())
                if m:
                    rec['label'] = m.group(1)
        digits = (rec['callsign'][3:] if rec.get('callsign')
                  else (rec.get('ur_ocr') or '')[2:] or None)
        if digits:
            rec['flight'] = 'UR' + digits

        # where the retry line is unreadable, fall back to the first pass's own read
        first = [x.strip() for x in (rec.get('raw', '').split('||')[0]).split(' | ')]
        for key, txt, alt in (('origin', orig, first[1] if len(first) > 1 else ''),
                              ('dest', dest, first[2] if len(first) > 2 else '')):
            for src_txt in (txt, alt):
                codes = [c for c in re.findall(r'\(\s*([A-Z0-9]{3})\s*\)', src_txt)
                         if c in CODES]
                if codes:
                    rec[key] = codes[0]
                    break
                if re.search(r'\bN\s*/\s*A\b', src_txt, re.I):
                    rec[key] = 'N/A'
                    break
        rec['raw'] = (rec.get('raw', '').split(' ||RETRY||')[0]
                      + f'  ||RETRY|| {" | ".join(got)}').strip()
        if complete(rec):
            fixed += 1
        print(f"{img[-10:-4]} idx{idx:>3} {'OK ' if complete(rec) else 'STILL'} "
              f"{rec.get('day')}/{rec.get('month')} "
              f"{rec.get('flight') or rec.get('callsign') or rec.get('label') or '—'} "
              f"{rec.get('origin')}->{rec.get('dest')}   {head[:40]!r}")

    json.dump(recs, open(FIXED, 'w'), indent=1)
    print(f'\nwrote {FIXED}: {len(recs)} records; '
          f'{sum(1 for r in recs if complete(r))} complete')

    print('\nstill incomplete:')
    for r in recs:
        if not complete(r) and iso(r) is None or not complete(r):
            if complete(r):
                continue
            print(f"  {r['image'][-22:]} idx{r['idx']:>3} {iso(r) or '—'} "
                  f"{r.get('flight') or r.get('callsign') or r.get('label') or '—'} "
                  f"{r.get('origin') or '—'}->{r.get('dest') or '—'}")


if __name__ == '__main__':
    main()
