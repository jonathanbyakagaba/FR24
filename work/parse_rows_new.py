#!/usr/bin/env python3
"""Parse the OCR'd 22 September screenshot rows into flight records.

Same three-line row shape as the earlier captures:
    Sep 18   UR209 (UGD209)        <- date, commercial flight no, callsign
    Entebbe (EBB)                  <- origin
    Nairobi (NBO)                  <- destination

Reads work/ocr_rows_new.json (produced from the upscaled captures) and writes
work/records_new.json.  Tail mapping is taken from the image header, which sits
in a different order than the filenames suggest.
"""
import json, re, sys, collections

TAIL = {   # screenshot file -> registration printed in the app header
    'NORM_Screenshot_20260922_075929_Flightradar24.jpg': 'ET-APL',
    'NORM_Screenshot_20260922_080019_Flightradar24.jpg': '5X-KDP',
    'NORM_Screenshot_20260922_080059_Flightradar24.jpg': '5X-KOB',
    'NORM_Screenshot_20260922_080302_Flightradar24.jpg': '5X-NIL',
    'NORM_Screenshot_20260922_080438_Flightradar24.jpg': '5X-EQU',
}
MONTH = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7,
         'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
CODES = {'EBB', 'NBO', 'DAR', 'JNB', 'LUN', 'HRE', 'BJM', 'MGQ', 'ZNZ', 'JRO',
         'MBA', 'LGW', 'BOM', 'DXB', 'DOH', 'ADD', 'KGL', 'FIH', 'LOS', 'ABJ',
         'JUB', 'NBO', 'DZA', 'HAH', 'SEZ', 'MRU', 'CAI', 'IST', 'BRU', 'AMS'}


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
    rows = json.load(open('work/ocr_rows_new.json'))
    out = []
    for rec in rows:
        if rec['idx'] == 0:              # header block (AIRCRAFT / YEAR 2026)
            continue
        tail = TAIL[rec['image']]
        out.append(parse_row(rec, tail))
    json.dump(out, open('work/records_new.json', 'w'), indent=1)

    bad = [r for r in out if not all([r['month'], r['day'], r['flight'],
                                      r['origin'], r['dest']])]
    print(f'records: {len(out)}   incomplete: {len(bad)}')
    for r in bad:
        print(f"  [{r['tail']}] row{r['idx']:>3} conf={r['conf']:5} "
              f"m={r['month']} d={r['day']} fl={r['flight']} "
              f"{r['origin']}->{r['dest']} | {r['raw'][:100]}")

    print('\nrecords per tail:')
    by = collections.defaultdict(list)
    for r in out:
        by[r['tail']].append(r)
    for t, rs in sorted(by.items()):
        days = [x['day'] for x in rs if x['day']]
        print(f'  {t}: {len(rs):>3} rows  days {min(days)}–{max(days)} Sep')

    print('\nUR number vs callsign mismatches (OCR suspicion):')
    for r in out:
        if r['ur_mismatch']:
            print(f"  [{r['tail']}] row{r['idx']:>3} {r['ur_ocr']} vs {r['callsign']} "
                  f"| {r['raw'][:90]}")


if __name__ == '__main__':
    main()
