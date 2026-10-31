#!/usr/bin/env python3
"""Detect FR24 app list rows in a tall phone screenshot by finding the coloured
status dot at the left margin of each entry. Then crop each entry and OCR it."""
import sys, os, subprocess, json
import numpy as np
from PIL import Image

def dot_centers(path, x0=5, x1=95, min_run=4):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    strip = a[:, x0:x1, :]
    mx = strip.max(axis=2); mn = strip.min(axis=2)
    sat = mx - mn                      # coloured => high saturation
    mask = (sat > 40)                  # dots are saturated; greys are not
    frac = mask.mean(axis=1)           # per-row fraction of coloured pixels
    ys = np.where(frac > 0.12)[0]
    if len(ys) == 0:
        return np.array([], dtype=int)
    # group consecutive ys into runs
    runs = []
    start = ys[0]; prev = ys[0]
    for y in ys[1:]:
        if y - prev > 12:
            runs.append((start, prev)); start = y
        prev = y
    runs.append((start, prev))
    runs = [(s, e) for s, e in runs if (e - s) >= min_run]
    return np.array([(s + e) // 2 for s, e in runs])

def ocr(path):
    r = subprocess.run(['tesseract', path, 'stdout', '--psm', '6'],
                       capture_output=True, text=True)
    return r.stdout

def main():
    for path in sys.argv[1:]:
        dot = dot_centers(path)
        im = Image.open(path)
        w, h = im.size
        print(f"=== {os.path.basename(path)}  size={w}x{h}  dots={len(dot)}")
        print("   dot ys:", list(dot))

if __name__ == '__main__':
    main()
