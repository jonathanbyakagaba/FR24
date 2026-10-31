#!/usr/bin/env python3
"""OCR very tall FR24 aircraft-history captures, in row-aligned slices.

work/ocr_rows.py OCRs a capture in one pass, which works while the page is a few
thousand pixels tall.  The 30 September captures list the whole month: at the
1080-px grid they run to ~22,000 px, and tesseract returns nothing for an image
that large.  This variant cuts each capture into slices *aligned to the row grid*
(15 rows plus the header), OCRs each slice, shifts the word coordinates back to
full-image scale and then buckets the words into grid rows exactly as
work/ocr_rows.py does.

Output: the same JSON shape, so work/parse_rows_new.py can read it.

    python3 work/ocr_rows_tall.py work/shots30/NORM_*.jpg work/shots30/ocr_rows_30.json
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, '/home/user/work')
import ocr_rows as base          # tsv_words / lines_of, unchanged
import status_dots as sd         # colour_blobs: size-bounded blob detection

ROWS_PER_SLICE = 15
MARGIN = 12                      # the same 12 px the parent script uses


def grid(path):
    """Row grid anchored on the *status dots*, not on any saturated pixel.

    ocr_rows.dot_ys() accepts any saturated run in the left margin, which on these
    captures includes the aircraft photo in the header; that anchors the grid 76 px
    off and every row lands between two slots.  colour_blobs() bounds each blob's
    height and width, so only the row dots survive.
    """
    im = Image.open(path).convert('RGB')
    best = []
    for params in ((6, 18, 16), (8, 28, 28), (10, 40, 40)):
        b = sd.colour_blobs(im, *params)
        if len(b) > len(best):
            best = b
    if len(best) < 3:
        raise SystemExit(f'no dots found in {path}')
    xs = sorted(x for x, _ in best)
    xc = xs[len(xs) // 2]
    ys = sorted(y for x, y in best if abs(x - xc) <= 6)
    diffs = [b - a for a, b in zip(ys, ys[1:]) if 25 < b - a < 900]
    small = sorted(d for d in diffs if d < min(diffs) * 1.8)
    pitch = int(round(small[len(small) // 2] if small else min(diffs)))
    y0 = ys[0] % pitch                      # keep the grid aligned to the dots
    while y0 - pitch > 150:
        y0 -= pitch
    h = im.size[1]
    nrows = int((h - y0) // pitch) + 1
    return y0, pitch, nrows, ys


def words_of_slice(path, ytop, ybot, png):
    """OCR one slice, return words in FULL-image, tesseract-upscaled coordinates"""
    im = Image.open(path).convert('L').crop((0, ytop, Image.open(path).size[0], ybot))
    im = im.resize((im.width * base.SCALE, im.height * base.SCALE), Image.LANCZOS)
    im = im.point(lambda p: 0 if p < 140 else 255)
    im.save(png)
    import subprocess
    r = subprocess.run(['tesseract', png, 'stdout', '--psm', '6', 'tsv'],
                       capture_output=True, text=True)
    out = []
    for ln in r.stdout.splitlines()[1:]:
        f = ln.split('\t')
        if len(f) < 12 or f[0] != '5':
            continue
        try:
            conf = float(f[10])
        except ValueError:
            continue
        txt = f[11].strip()
        if not txt or conf < 0:
            continue
        out.append({'t': txt, 'conf': conf,
                    'l': int(f[6]),
                    'top': int(f[7]) + ytop * base.SCALE,      # back to full-image scale
                    'w': int(f[8]), 'h': int(f[9])})
    return out


def main(paths, out_json):
    allrows = []
    os.makedirs('work/ocr', exist_ok=True)
    for p in paths:
        y0, pitch, nrows, ys = grid(p)
        H = Image.open(p).size[1]
        base_ = os.path.basename(p)
        words = []
        # slot 0 is the header block (the app's first grid slot); flight rows start
        # at k=1.  Slices are row-aligned and must not overlap the header slice, or
        # the same text is OCR'd twice.
        bounds = [(0, min(H, y0 + pitch - MARGIN))]
        k = 1
        while y0 + k * pitch < H:
            top = max(0, y0 + k * pitch - MARGIN)
            bot = min(H, y0 + (k + ROWS_PER_SLICE) * pitch + MARGIN)
            bounds.append((top, bot))
            k += ROWS_PER_SLICE
        for i, (a, b) in enumerate(bounds):
            if b - a < 20:
                continue
            words += words_of_slice(p, a, b, f'work/ocr/{base_}.{i:02d}.png')
        print(f'{base_}: grid y0={y0} pitch={pitch} rows={nrows} '
              f'first dot y={ys[0]} (header slots 0..{ys[0] // pitch - 1}) '
              f'slices={len(bounds)} words={len(words)}', file=sys.stderr)
        for i in range(nrows):
            top = y0 + i * pitch
            row_lines = base.lines_of(words, (top - MARGIN) * base.SCALE,
                                      (top + pitch - MARGIN) * base.SCALE)
            allrows.append({'image': base_, 'idx': int(i), 'y': int(top),
                            'lines': row_lines})
    with open(out_json, 'w') as fh:
        json.dump(allrows, fh, indent=1)
    print(f'wrote {out_json}: {len(allrows)} rows')


if __name__ == '__main__':
    main(sys.argv[1:-1], sys.argv[-1])
