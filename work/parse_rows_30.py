#!/usr/bin/env python3
"""Parse the OCR'd 30 September screenshot rows into flight records.

Same three-line row shape as the earlier captures:
    Sep 30   UR342 (UGD342)        <- date, commercial flight no, callsign
    Entebbe (EBB)                  <- origin
    Mombasa (MBA)                  <- destination

Reads work/shots30/ocr_rows_30.json (produced from the normalised captures by
work/ocr_rows_tall.py) and writes work/shots30/records_30.json.  The tail comes
from the registration printed in the app header, which the OCR also reads, so the
mapping is checked rather than assumed: every capture's header line is printed
next to the tail this script assigns to it.

These captures list the whole month, so the header block (photo + aircraft
particulars) occupies several grid slots before the first flight row; slots that
do not carry a date and a flight number are flagged, not silently kept.
"""
import json
import re
import collections

TAIL = {   # normalised capture -> registration read from that capture's header
    'NORM_Screenshot_20260930_204706_Flightradar24.jpg': '5X-EQU',
    'NORM_Screenshot_20260930_204740_Flightradar24.jpg': '5X-KDP',
    'NORM_Screenshot_20260930_204826_Flightradar24.jpg': '5X-EQU',
    'NORM_Screenshot_20260930_204933_Flightradar24.jpg': '5X-KOB',
    'NORM_Screenshot_20260930_205018_Flightradar24.jpg': 'ET-APL',
    'NORM_Screenshot_20260930_205121_Flightradar24.jpg': '5X-NIL',
}
MONTH = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7,
         'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
CODES = {'EBB', 'NBO', 'DAR', 'JNB', 'LUN', 'HRE', 'BJM', 'MGQ', 'ZNZ', 'JRO',
         'MBA', 'LGW', 'BOM', 'DXB', 'DOH', 'ADD', 'KGL', 'FIH', 'LOS', 'ABJ',
         'JUB', 'SEZ', 'MRU', 'CAI', 'IST', 'BRU', 'AMS', 'JED', 'KRT', 'CPT'}


def parse_row(rec, tail):
    txt = ' \n '.join(l['text'] for l in rec['lines'])
    conf = [l['conf'] for l in rec['lines']]
    r = {'image': rec['image'], 'idx': rec['idx'], 'tail': tail,
         'raw': txt.replace('\n', ' | ')}

    m = re.search(r'\b([A-Za-z]{3})\s*(\d{1,2})\b', txt)
    r['month'] = MONTH.get(m.group(1).upper()) if m else None
    r['day'] = int(m.group(2)) if m else None

    flat = txt.replace(' ', '')
    m = re.search(r'UR[/Il]?(\d{1,4})', flat)
    r['ur_ocr'] = f'UR{m.group(1)}' if m else None

    m = re.search(r'\(\s*[uU]{1,3}[gG6][a-zA-Z]{0,3}\s*(\d{3})[a-zA-Z]?\s*\)', txt)
    if not m:
        m = re.search(r'\(\s*[uU]{1,2}[gG6]\s*(\d{3})\s*\)', txt)
    r['callsign'] = f'UGD{m.group(1)}' if m else None

    digits = None
    if r['callsign']:
        digits = r['callsign'][3:]
    elif r['ur_ocr']:
        digits = r['ur_ocr'][2:]
    r['flight'] = f'UR{digits}' if digits else None
    r['ur_mismatch'] = bool(r['ur_ocr'] and r['callsign']
                            and r['ur_ocr'][2:] != r['callsign'][3:])

    codes = [c for c in re.findall(r'\(\s*([A-Z0-9]{3})\s*\)', txt) if c in CODES]
    r['origin'] = codes[0] if len(codes) >= 1 else None
    r['dest'] = codes[1] if len(codes) >= 2 else None
    r['codes_all'] = codes
    r['conf'] = round(sum(conf) / len(conf), 1) if conf else 0
    r['n_codes'] = len(codes)
    return r


def main():
    rows = json.load(open('work/shots30/ocr_rows_30.json'))
    out = []
    for rec in rows:
        tail = TAIL[rec['image']]
        out.append(parse_row(rec, tail))
    json.dump(out, open('work/shots30/records_30.json', 'w'), indent=1)

    # the header slot of each capture carries the registration the app displays
    print('capture header check:')
    for img in sorted({r['image'] for r in out}):
        hdr = [r for r in rows if r['image'] == img and r['idx'] == 0]
        txt = ' '.join(l['text'] for l in hdr[0]['lines']) if hdr else ''
        reg = re.search(r'5X-[A-Z]{3}|ET-APL', txt.upper())
        want = TAIL[img]
        print(f"  {img[-30:]:30s} OCR header {txt.strip()[:38]!r:42s} "
              f"-> {want}  {'OK' if (not reg or reg.group(0) == want) else 'CHECK'}")

    bad = [r for r in out if not all([r['month'], r['day'], r['flight'],
                                      r['origin'], r['dest']])]
    print(f'\nrecords: {len(out)}   incomplete: {len(bad)}')
    holes = collections.Counter()
    for r in bad:
        miss = [k for k in ('month', 'day', 'flight', 'origin', 'dest') if not r[k]]
        holes[tuple(miss)] += 1
    for k, n in holes.most_common():
        print(f'   missing {", ".join(k)}: {n}')

    print('\nrecords per tail:')
    by = collections.defaultdict(list)
    for r in out:
        by[r['tail']].append(r)
    for t, rs in sorted(by.items()):
        good = [x for x in rs if x['day']]
        days = [x['day'] for x in good]
        print(f'  {t:7s} {len(rs):>3} rows  {len(good):>3} with a date  '
              f'days {min(days)}–{max(days)} Sep' if days else f'  {t}: no dated rows')

    print('\nUR number vs callsign mismatches (OCR suspicion):')
    seen = 0
    for r in out:
        if r['ur_mismatch']:
            seen += 1
            print(f"  [{r['tail']}] row{r['idx']:>3} {r['ur_ocr']} vs {r['callsign']} "
                  f"| {r['raw'][:80]}")
    if not seen:
        print('  none')


if __name__ == '__main__':
    main()
