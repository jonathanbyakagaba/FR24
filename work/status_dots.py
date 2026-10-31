#!/usr/bin/env python3
"""Status dots from the FR24 per-tail screenshots.

Every flight row on the aircraft page carries a small coloured dot at the left
edge of the list:

    green   normal / landed
    amber   delayed
    red     cancelled
    grey    no data for the leg

The dot column sits at a fixed x per screenshot and the rows are evenly spaced,
so the dots can be read mechanically and matched, top to bottom, with the rows
the earlier transcription already captured.

Writes work/status_dots.csv : image, slot, y, colour, rgb
"""
import csv, os, collections
from PIL import Image

UP = 'uploads'
OUT = 'work/status_dots.csv'
XMAX = 64          # the dot never sits further right than this


def dot_pixel(rgb):
    r, g, b = rgb
    sat = max(rgb) - min(rgb)
    mean = (r + g + b) / 3
    if sat > 40:                     # coloured dot
        return True
    return 150 < mean < 215          # grey dot against the white / 237 background


def colour_blobs(im, hmin=6, hmax=18, wmax=16):
    """coloured (saturated) blobs in the left margin: (x centre, y centre)"""
    W, H = im.size
    px = im.load()
    found = []
    run = None
    for y in range(H):
        xs = [x for x in range(4, min(XMAX, W))
              if (lambda c: max(c) - min(c) > 40)(px[x, y])]
        if xs:
            run = [y, y, min(xs), max(xs)] if run is None else \
                  [run[0], y, min(run[2], min(xs)), max(run[3], max(xs))]
        elif run is not None:
            if hmin <= run[1] - run[0] + 1 <= hmax and run[3] - run[2] <= wmax:
                found.append(((run[2] + run[3]) // 2, (run[0] + run[1]) // 2))
            run = None
    if run is not None and hmin <= run[1] - run[0] + 1 <= hmax:
        found.append(((run[2] + run[3]) // 2, (run[0] + run[1]) // 2))
    return found


def classify(im, xc, y):
    px = im.load()
    vals = [px[x, yy] for x in range(xc - 5, xc + 6) for yy in range(y - 4, y + 5)]
    vals.sort(key=lambda c: sum(c))
    med = vals[len(vals) // 2]
    r, g, b = med
    sat = max(med) - min(med)
    mean = (r + g + b) / 3
    if sat > 40:
        if g > r + 20 and g > b + 20:
            return 'green', med
        if r > 180 and g >= 150:
            return 'amber', med
        if r > 180 and g < 150:
            return 'red', med
        return 'other', med
    if 140 < mean < 222:
        return 'grey', med
    return 'none', med


def analyse(path):
    """geometry from the coloured dots; then every slot on that grid is read.

    The coloured dots give the column x and the row pitch.  Where two coloured
    dots sit more than one pitch apart, the rows between them exist but carry a
    grey dot — those are filled back in.
    """
    im = Image.open(path).convert('RGB')
    # dot size depends on the capture: phone screenshots have ~11 px dots on a
    # 108 px pitch, the long stitched captures ~21 px dots on a 203 px pitch
    best = []
    for hmin, hmax, wmax in ((6, 18, 16), (8, 28, 28)):
        b = colour_blobs(im, hmin, hmax, wmax)
        if len(b) > len(best):
            best = b
    blobs = best
    if not blobs:
        return [], None, None, None
    xs = sorted(x for x, _ in blobs)
    xc = xs[len(xs) // 2]
    ys = sorted(y for x, y in blobs if abs(x - xc) <= 6)
    diffs = [b - a for a, b in zip(ys, ys[1:]) if 25 < b - a < 900]
    if not diffs:
        return [], xc, None, None
    step = min(diffs)
    small = sorted(d for d in diffs if d < step * 1.8)
    pitch = small[len(small) // 2] if small else step

    filled = [ys[0]]
    for y in ys[1:]:
        for _ in range(1, max(1, round((y - filled[-1]) / pitch))):
            filled.append(filled[-1] + pitch)
        filled.append(y)

    out = []
    for i, y in enumerate(filled, 1):
        col, rgb = classify(im, xc, y)
        out.append((i, y, col, rgb))
    return out, xc, pitch, (ys[0], ys[-1])


def main():
    rows = []
    for fn in sorted(os.listdir(UP)):
        if not fn.lower().endswith('.jpg'):
            continue
        found, xc, pitch, span = analyse(os.path.join(UP, fn))
        by = collections.Counter(c for _, _, c, _ in found)
        print(f'{fn:52s} x={xc} pitch={pitch} span={span} {len(found):3d} slots  {dict(by)}')
        for i, y, col, rgb in found:
            rows.append(dict(image=fn, slot=i, y=y, colour=col,
                             rgb='%d,%d,%d' % rgb))
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['image', 'slot', 'y', 'colour', 'rgb'])
        w.writeheader(); w.writerows(rows)
    print(f'\nwrote {OUT}: {len(rows)} slots')


if __name__ == '__main__':
    main()
