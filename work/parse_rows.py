#!/usr/bin/env python3
"""Parse the OCR'd screenshot rows into flight records.

Each FR24 aircraft-history row has three text lines:
    Sep 11   UR110 (UGD110)        <- date, commercial flight no, callsign
    Entebbe (EBB)                  <- origin
    London (LGW)                   <- destination
"""
import json, re, sys, csv
import build_log as B

TAIL = {                       # screenshot file -> registration shown in the header
    'Screenshot_20260911_124304_Flightradar24.jpg': '5X-NIL',
    'Screenshot_20260911_124414_Flightradar24.jpg': 'ET-APL',
    'Screenshot_20260911_124506_Flightradar24.jpg': '5X-KOB',
    'Screenshot_20260911_124545_Flightradar24.jpg': '5X-KDP',
    'Screenshot_20260911_124626_Flightradar24.jpg': '5X-EQU',
}
MONTH = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7,
         'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
CODES = set(B.AIRPORTS) | {'ABJ', 'KGL', 'ADD', 'DXB', 'DOH', 'FIH', 'WDH', 'MED',
                           'BRU', 'AMS', 'CAI', 'IST', 'GRU', 'HRE', 'LUN', 'LOS'}


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

    # callsign: OCR renders it as UG D 7 1 0 with assorted case/spacing damage
    m = re.search(r'\(\s*[uU]{1,3}[gG6][a-zA-Z]{0,3}\s*(\d{3})[a-zA-Z]?\s*\)', txt)
    if not m:
        m = re.search(r'\(\s*[uU]{1,2}[gG6]\s*(\d{3})\s*\)', txt)
    r['callsign'] = f'UGD{m.group(1)}' if m else None
    # the commercial number and the callsign carry the same digits on every
    # independently verified row, so the callsign wins when OCR mangles one of them
    digits = None
    if r['callsign']:
        digits = r['callsign'][3:]
    elif r['ur_ocr']:
        digits = r['ur_ocr'][2:]
    elif r.get('ur_ocr') is None and r.get('callsign') is None:
        digits = None
    r['flight'] = f'UR{digits}' if digits else None
    r['ur_mismatch'] = bool(r['ur_ocr'] and r['callsign']
                            and r['ur_ocr'][2:] != r['callsign'][3:])

    codes = [c for c in re.findall(r'\(\s*([A-Z0-9]{3})\s*\)', txt) if c in CODES]
    # drop a code that is really the callsign (3 alnum codes only exist for airports here)
    r['origin'] = codes[0] if len(codes) >= 1 else None
    r['dest'] = codes[1] if len(codes) >= 2 else None
    r['codes_all'] = codes
    r['conf'] = round(sum(conf) / len(conf), 1) if conf else 0
    r['n_codes'] = len(codes)
    return r


def main():
    rows = json.load(open('work/ocr_rows.json'))
    out = []
    for rec in rows:
        if rec['idx'] == 0:          # header row (AIRCRAFT / YEAR 2026)
            continue
        tail = TAIL[rec['image']]
        out.append(parse_row(rec, tail))
    json.dump(out, open('work/records.json', 'w'), indent=1)

    bad = [r for r in out if not all([r['month'], r['day'], r['flight'], r['origin'], r['dest']])]
    print(f'records: {len(out)}   incomplete: {len(bad)}')
    for r in bad:
        print(f"  [{r['tail']}] row{r['idx']} conf={r['conf']:5} "
              f"m={r['month']} d={r['day']} fl={r['flight']} {r['origin']}->{r['dest']} "
              f"| {r['raw'][:110]}")

    print('\nrecords per tail:')
    for t in ['5X-NIL', 'ET-APL', '5X-KOB', '5X-KDP', '5X-EQU']:
        n = [r for r in out if r['tail'] == t]
        print(f'  {t}: {len(n)}  ({min(r["day"] for r in n)}–{max(r["day"] for r in n)} Sep)')


if __name__ == '__main__':
    main()
