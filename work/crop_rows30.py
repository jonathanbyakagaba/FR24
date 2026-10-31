#!/usr/bin/env python3
"""Read-back sheets for the 30 September rows the cross-check could not settle.

Crops each named row out of the normalised capture and stacks them under a red
label band carrying `capture index / tail / slot`, so a doubtful reading can be
checked against the pixels rather than re-run through OCR.

    python3 work/crop_rows30.py            # every row flagged in crosscheck_30.csv
"""
import csv
import collections
import os

from PIL import Image, ImageDraw, ImageFont

OCR = 'work/shots30/ocr_rows_30.json'
SHOTS = 'work/shots30'
OUT = 'work/shots30/readback'
PITCH = 203
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
import json


def main():
    os.makedirs(OUT, exist_ok=True)
    grid = {}
    for r in json.load(open(OCR)):
        grid.setdefault(r['image'].replace('NORM_', ''), {})[r['idx']] = r['y']
    flags = collections.defaultdict(list)
    for r in csv.DictReader(open('work/shots30/crosscheck_30.csv')):
        if r['verdict'] in ('incomplete', 'unknown-flight'):
            flags[r['image']].append(r)

    for img, rows in flags.items():
        rows.sort(key=lambda r: int(r['idx']))
        f = ImageFont.truetype(FONT, 30)
        pieces = []
        for r in rows:
            idx = int(r['idx'])
            y = grid[img].get(idx)
            if y is None:
                continue
            src = Image.open(f'{SHOTS}/NORM_{img}')
            top = max(0, y - 14)
            bot = min(src.size[1], y + PITCH - 10)
            crop = src.crop((0, top, 1080, bot))
            lab = Image.new('RGB', (1080, 46), (198, 0, 0))
            d = ImageDraw.Draw(lab)
            d.text((8, 6), f"{img[15:21]} {r['tail']} slot{r['slot']} idx{idx} "
                           f"{r['verdict']}", font=f, fill=(255, 255, 255))
            pieces.append((lab, crop))
        H = sum(l.size[1] + c.size[1] for l, c in pieces)
        sheet = Image.new('RGB', (1080, H), (255, 255, 255))
        yy = 0
        for l, c in pieces:
            sheet.paste(l, (0, yy)); yy += l.size[1]
            sheet.paste(c, (0, yy)); yy += c.size[1]
        name = f"{OUT}/{img.split('_')[2]}_{flags[img][0]['tail'].replace('5X-','')}.png"
        sheet.save(name)
        print(f'{name}  {len(pieces)} rows  {sheet.size}')


if __name__ == '__main__':
    main()
