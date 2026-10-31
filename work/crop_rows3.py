#!/usr/bin/env python3
"""Crop a row range with a legible burned-in label."""
import json, sys
from PIL import Image, ImageDraw, ImageFont

IMGS = {
 'ET-APL': 'NORM_Screenshot_20260922_075929_Flightradar24.jpg',
 'KDP':    'NORM_Screenshot_20260922_080019_Flightradar24.jpg',
 'KOB':    'NORM_Screenshot_20260922_080059_Flightradar24.jpg',
 'NIL':    'NORM_Screenshot_20260922_080302_Flightradar24.jpg',
 'EQU':    'NORM_Screenshot_20260922_080438_Flightradar24.jpg',
}
raw = json.load(open('work/ocr_rows_new.json'))
Y = {(r['image'], r['idx']): r['y'] for r in raw}
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 44)

def crop(tail, a, b):
    name = IMGS[tail]
    p = 'work/newshots/' + name
    ya = max(0, Y[(name, a)] - 15)
    yb = min(Image.open(p).size[1], Y[(name, b)] + 175)
    im = Image.open(p).crop((0, ya, 1080, yb))
    band = Image.new('RGB', (1080, 64), (200, 0, 0))
    ImageDraw.Draw(band).text((14, 8), f'{tail} rows {a}-{b}', font=F, fill=(255, 255, 255))
    out = Image.new('RGB', (1080, im.size[1] + 64), (0, 0, 0))
    out.paste(band, (0, 0)); out.paste(im, (0, 64))
    out.save(f'work/verify/{tail}_{a}-{b}.png')
    print(f'{tail}_{a}-{b}.png', out.size)

if __name__ == '__main__':
    crop(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
