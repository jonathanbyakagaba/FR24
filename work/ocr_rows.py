#!/usr/bin/env python3
"""OCR the five FR24 aircraft-history screenshots row by row.

Rows in the FR24 app list sit on a fixed 203 px grid; the coloured status dot at
the left margin marks the top of each row.  We detect the dots, fit the grid,
run tesseract once per screenshot (TSV output = words with coordinates), then
bucket words into grid rows.  Output: work/ocr_rows.json
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image

PITCH = 203          # px between row tops in the original screenshots
SCALE = 2            # upscale factor fed to tesseract


def dot_ys(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.int16)
    strip = a[:, 5:95, :]
    sat = strip.max(axis=2) - strip.min(axis=2)
    frac = (sat > 40).mean(axis=1)
    ys = np.where(frac > 0.12)[0]
    if not len(ys):
        return []
    runs, start, prev = [], ys[0], ys[0]
    for y in ys[1:]:
        if y - prev > 12:
            runs.append((start, prev)); start = y
        prev = y
    runs.append((start, prev))
    return [(s + e) // 2 for s, e in runs if e - s >= 4]


def grid(path):
    """Return (y0, nrows) for the row grid of one screenshot."""
    ys = dot_ys(path)
    if len(ys) < 2:
        raise SystemExit(f'no dots in {path}')
    diffs = [b - a for a, b in zip(ys, ys[1:])]
    pitch = int(round(np.median([d for d in diffs if d < PITCH * 1.5])))
    y0 = int(ys[0]) % pitch
    # walk up in case the first dot was missed
    while y0 - pitch > 150:
        y0 -= pitch
    h = Image.open(path).size[1]
    nrows = int((h - y0) // pitch) + 1   # include the final (possibly cut) row
    return y0, pitch, nrows, ys


def tsv_words(path, work_png):
    im = Image.open(path).convert('L')
    im = im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)
    im = im.point(lambda p: 0 if p < 140 else 255)      # hard binarise
    im.save(work_png)
    r = subprocess.run(['tesseract', work_png, 'stdout', '--psm', '6', 'tsv'],
                       capture_output=True, text=True)
    words = []
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
        words.append({'t': txt, 'conf': conf,
                      'l': int(f[6]), 'top': int(f[7]),
                      'w': int(f[8]), 'h': int(f[9])})
    return words


def lines_of(words, ytop, ybot, gap=22):
    """Cluster words into text lines by vertical position."""
    sel = sorted([w for w in words if ytop <= w['top'] + w['h'] / 2 < ybot],
                 key=lambda w: (w['top'], w['l']))
    out, cur, cur_y = [], [], None
    for w in sel:
        cy = w['top'] + w['h'] / 2
        if cur_y is None or abs(cy - cur_y) <= gap:
            cur.append(w); cur_y = cy if cur_y is None else (cur_y + cy) / 2
        else:
            out.append(cur); cur = [w]; cur_y = cy
    if cur:
        out.append(cur)
    res = []
    for ln in out:
        ln = sorted(ln, key=lambda w: w['l'])
        res.append({'text': ' '.join(w['t'] for w in ln),
                    'conf': round(float(np.mean([w['conf'] for w in ln])), 1),
                    'top': min(w['top'] for w in ln),
                    'left': min(w['l'] for w in ln)})
    return res


def main(paths, out_json):
    allrows = []
    for p in paths:
        y0, pitch, nrows, ys = grid(p)
        base = os.path.basename(p)
        wpng = f'work/ocr/{base}.png'
        words = tsv_words(p, wpng)
        print(f'{base}: grid y0={y0} pitch={pitch} rows={nrows} words={len(words)}',
              file=sys.stderr)
        for i in range(nrows):
            top = y0 + i * pitch
            row_lines = lines_of(words, (top - 12) * SCALE, (top + pitch - 12) * SCALE)
            allrows.append({'image': base, 'idx': int(i), 'y': int(top),
                            'lines': row_lines})
    with open(out_json, 'w') as fh:
        json.dump(allrows, fh, indent=1)
    print(f'wrote {out_json}: {len(allrows)} rows')


if __name__ == '__main__':
    os.makedirs('work/ocr', exist_ok=True)
    main(sys.argv[1:-1], sys.argv[-1])
