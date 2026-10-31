#!/usr/bin/env python3
"""Crop row ranges out of a capture for visual verification."""
import json, sys
from PIL import Image

IMGS = {
 'ET-APL': 'NORM_Screenshot_20260922_075929_Flightradar24.jpg',
 'KDP':    'NORM_Screenshot_20260922_080019_Flightradar24.jpg',
 'KOB':    'NORM_Screenshot_20260922_080059_Flightradar24.jpg',
 'NIL':    'NORM_Screenshot_20260922_080302_Flightradar24.jpg',
 'EQU':    'NORM_Screenshot_20260922_080438_Flightradar24.jpg',
}
raw = json.load(open('work/ocr_rows_new.json'))
Y = {(r['image'], r['idx']): r['y'] for r in raw}
PITCH = 203

def crop(tail, a, b, tag=''):
    name = IMGS[tail]
    ya = max(0, Y[(name, a)] - 25)
    yb = min(Image.open('work/newshots/' + name).size[1], Y[(name, b)] + 180)
    im = Image.open('work/newshots/' + name).crop((0, ya, 1080, yb))
    out = f'work/verify/{tail}_rows{a}-{b}{tag}.png'
    im.save(out)
    print(out, im.size)

if __name__ == '__main__':
    crop(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
