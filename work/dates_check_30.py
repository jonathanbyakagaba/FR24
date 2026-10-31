#!/usr/bin/env python3
"""Pull out the date outliers in the 30 September batch and stack them for a read.

Every page holds about a hundred rows, so a tail's dates should be one unbroken run
ending on 30 September.  A dated row that sits far outside its neighbours' range, or
claims a day the month does not have, is either a misread or a real oddity, and both
want looking at.  Writes one labelled contact sheet per tail into work/shots30/dates/.

    python3 work/dates_check_30.py
"""
import collections
import csv
import json
import os

from PIL import Image, ImageDraw, ImageFont

SHOTS = 'work/shots30'
OUT = f'{SHOTS}/dates'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
PITCH = 203


def day(r):
    return int(r['date'][-2:]) if r['date'] else None


def main():
    os.makedirs(OUT, exist_ok=True)
    grid = {}
    for r in json.load(open(f'{SHOTS}/ocr_rows_30.json')):
        grid.setdefault(r['image'].replace('NORM_', ''), {})[r['idx']] = r['y']

    rows = list(csv.DictReader(open('work/screens_20260930_rows.csv')))
    per = collections.defaultdict(list)
    for r in rows:
        per[r['tail']].append(r)

    f = ImageFont.truetype(FONT, 28)
    for tail, rs in per.items():
        days = sorted(d for d in (day(r) for r in rs) if d)
        # an outlier is a dated row separated from the body of the run by a week or
        # more, or a day the month does not have
        body = [d for d in days if 1 <= d <= 30]
        med = body[len(body) // 2] if body else 0
        bad = []
        for r in rs:
            d = day(r)
            if d is None:
                continue
            near = [x for x in days if abs(x - d) <= 4 and x != d]
            if (d > 30 or d < 1) or (not near and abs(d - med) > 6 and
                                     (d > max(days) or d < min(days))):
                bad.append(r)
        # also catch a lone weekday inside the run (only one row on that date while
        # its neighbours carry several)
        cnt = collections.Counter(r['date'] for r in rs if r['date'])
        for r in rs:
            if r['date'] and 1 <= (day(r) or 0) <= 30 and cnt[r['date']] == 1 \
                    and r not in bad:
                lft = [c for d, c in cnt.items() if d and d < r['date']]
                rgt = [c for d, c in cnt.items() if d and d > r['date']]
                if lft and rgt and min(lft) >= 3 and min(rgt) >= 3:
                    bad.append(r)
        if not bad:
            print(f'{tail:8s} no outliers')
            continue
        bad.sort(key=lambda r: (r['date'] or '', int(r['idx'])))
        pieces = []
        for r in bad:
            y = grid.get(r['image'], {}).get(int(r['idx']))
            if y is None:
                continue
            src = Image.open(f"{SHOTS}/NORM_{r['image']}")
            crop = src.crop((0, max(0, y - 12), 1080, min(src.size[1], y + PITCH - 8)))
            lab = Image.new('RGB', (1080, 44), (0, 90, 160))
            d_ = ImageDraw.Draw(lab)
            d_.text((8, 6), f"{r['image'][15:21]} slot{r['slot']} idx{r['idx']} "
                            f"read={r['date']} {r['flight']} {r['origin']}-{r['dest']}",
                    font=f, fill=(255, 255, 255))
            pieces.append((lab, crop))
        H = sum(a.size[1] + b.size[1] for a, b in pieces)
        sheet = Image.new('RGB', (1080, H), (255, 255, 255))
        yy = 0
        for a, b in pieces:
            sheet.paste(a, (0, yy)); yy += a.size[1]
            sheet.paste(b, (0, yy)); yy += b.size[1]
        nm = f"{OUT}/{tail.replace('5X-','')}.png"
        sheet.save(nm)
        print(f'{tail:8s} {len(pieces)} outliers -> {nm}  '
              f'{[r["date"] for r in bad]}')


if __name__ == '__main__':
    main()
