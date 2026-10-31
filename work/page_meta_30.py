#!/usr/bin/env python3
"""Sort the non-row slots in the 30 September captures, and keep the airframe facts.

Each capture opens with the aircraft's own page: a photograph, then a specification
block (type code, MSN, mode-S, age, operator).  The row grid counts that block as
ordinary slots, so the parse reports it as a run of unreadable flights.  It is not:
it is the identification of the aircraft whose flights follow, and it is worth
reading on its own terms.

This marks those slots in work/shots30/records_30_checked.json as `header` (so the
next OCR pass leaves them alone) and writes the specification block to
work/shots30/airframes.csv for comparison with the fleet reference.

    python3 work/page_meta_30.py
"""
import csv
import json
import re

CHECKED = 'work/shots30/records_30_checked.json'
OUT = 'work/shots30/airframes.csv'
MARKERS = ('AIRCRAFT TYPE CODE', 'SERIAL NUMBER', 'MODE S', 'MODES',
           'COUNTRY OF REGISTRATION', 'OPERATOR CODE', 'AIRLINE CODE',
           'AIRCRAFT', 'MSN')
TYPE_RE = re.compile(r'([A-Z][A-Za-z0-9\- ]{3,28}?)\s+(A\d{3}|B\d{3}|CRJ\d?)\b')
MSN_RE = re.compile(r'\b(1[45]\d{3}|19\d{2})\b')
MODES_RE = re.compile(r'\b(0[0-9A-F]{5})\b')


def main():
    recs = json.load(open(CHECKED))
    marked = 0
    pages = {}
    for r in recs:
        raw = (r.get('raw') or '')
        if not r.get('header'):
            up = raw.upper()
            hits = sum(1 for m in MARKERS if m in up)
            if hits >= 2 or not r.get('month'):
                r['header'] = True
                marked += 1
        if r.get('header'):
            pages.setdefault(r['image'], []).append(raw)

    rows = []
    for img, texts in pages.items():
        blob = ' | '.join(texts)
        up = blob.upper()
        typ = TYPE_RE.search(blob)
        msn = MSN_RE.search(blob)
        modes = MODES_RE.search(up)
        rows.append(dict(image=img.replace('NORM_', ''),
                         type_code=(typ.group(2) if typ else ''),
                         type_name=(typ.group(1).strip() if typ else ''),
                         msn=(msn.group(1) if msn else ''),
                         mode_s=(modes.group(1) if modes else '')))
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['image', 'type_code', 'type_name',
                                           'msn', 'mode_s'])
        w.writeheader()
        w.writerows(rows)
    json.dump(recs, open(CHECKED, 'w'), indent=1)

    print(f'marked {marked} further slots as the header/spec block')
    print(f'wrote {OUT}:')
    for r in rows:
        print(f"   {r['image'][-14:-4]:>6}  {r['type_code']:5s} {r['type_name']:22s} "
              f"MSN {r['msn']:6s} mode-S {r['mode_s']}")


if __name__ == '__main__':
    main()
