#!/usr/bin/env python3
"""Crop a row range with a burned-in label so the read-back can't be mixed up."""
import json, sys
from PIL import Image, ImageDraw

IMGS = {
 'ET-APL': 'NORM_Screenshot_20260922_075929_Flightradar24.jpg',
 'KDP':    'NORM_Screenshot_20260922_080019_Flightradar24.jpg',
 'KOB':    'NORM_Screenshot_20260922_080059_Flightradar24.jpg',
 'NIL':    'NORM_Screenshot_20260922_080302_Flightradar24.jpg',
 'EQU':    'NORM_Screenshot_20260922_080438_Flightradar24.jpg',
}
raw = json.load(open('work/ocr_rows_new.json'))
Y = {(r['image'], r['idx']): r['y'] for r in raw}

def crop(tail, a, b):
    name = IMGS[tail]
    ya = max(0, Y[(name, a)] - 15)
    yb = min(Image.open('work/newshots/' + name).size[1], Y[(name, b)] + 175)
    im = Image.open('work/newshots/' + name).crop((0, ya, 1080, yb))
    band = Image.new('RGB', (1080, 70), (0, 0, 0))
    d = ImageDraw.Draw(band)
    d.text((20, 25), f'{tail}  rows {a}-{b}', fill=(255, 255, 0))
    out = Image.new('RGB', (1080, im.size[1] + 70), (0, 0, 0))
    out.paste(band, (0, 0)); out.paste(im, (0, 70))
    p = f'work/verify/{tail}_{a}-{b}.png'
    out.save(p)
    print(p, out.size)

if __name__ == '__main__':
    crop(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
