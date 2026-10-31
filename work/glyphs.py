#!/usr/bin/env python3
"""Classify the digits of the commercial number shown left of the callsign.

The flight line looks like:   Sep 11   UR521 (UGD321)
Segments glyphs by column projection, harvests digit prototypes from the
parenthetical callsign (whose digits the archive corroborates), then classifies
the digits of the UR number against those prototypes.
"""
import json
import numpy as np
from PIL import Image

BOX = (24, 32)


def norm(g):
    im = Image.fromarray((~g).astype(np.uint8) * 255)
    return np.asarray(im.resize(BOX, Image.LANCZOS)).astype(float) / 255.0


def glyphs(im):
    """Return [(x0, x1, bitmap)] left-to-right for dark glyphs on light ground."""
    g = np.asarray(im.convert('L'), dtype=np.uint8)
    dark = g < 140
    cols = dark.sum(axis=0)
    out, x = [], 0
    while x < len(cols):
        if cols[x]:
            x0 = x
            while x < len(cols) and (cols[x] or (x + 3 < len(cols) and cols[x:x + 4].any())):
                x += 1
            sub = dark[:, x0:x]
            rows = np.where(sub.any(axis=1))[0]
            if len(rows):
                sub = sub[rows[0]:rows[-1] + 1]
            if 3 <= (x - x0) <= 90 and sub.size:
                out.append((x0, x, sub))
        x += 1
    return out


def digit_boxes(gs, start):
    """three consecutive digit-width glyphs starting at index `start`"""
    res = []
    for x0, x1, sub in gs[start:start + 3]:
        res.append(sub)
    return res


def main():
    recs = json.load(open('work/records.json'))
    rows = {(r['image'], r['idx']): r for r in json.load(open('work/ocr_rows.json'))}

    proto = {d: [] for d in '0123456789'}
    parsed = []
    for r in recs:
        if not r['callsign'] or not r['month']:
            continue
        rec = rows[(r['image'], r['idx'])]
        im = Image.open('uploads/' + rec['image']).crop((100, rec['y'] + 6, 760, rec['y'] + 84))
        gs = glyphs(im)
        # locate 'U','R' then 3 digits, and '(' then 'U','G','D' then 3 digits
        idx_ur = None
        for i in range(len(gs) - 4):
            idx_ur = i
            break
        # simpler: find the group sequence ending at the last three glyphs before a ')'
        # last glyph is ')' : identified as narrow tall glyph at the end of the callsign
        try:
            cs_end = max(i for i, g in enumerate(gs) if g[2].shape[0] > 10)
        except ValueError:
            continue
        # digits of callsign = glyphs at cs_end-4 .. cs_end-2   ( U G D d d d )  -> cs_end = ')'
        if cs_end < 6:
            continue
        cs_digits = gs[cs_end - 3:cs_end]
        ur_digits = gs[cs_end - 8:cs_end - 5]
        if len(cs_digits) != 3 or len(ur_digits) != 3:
            continue
        cd = r['callsign'][3:]
        for d, (_, _, sub) in zip(cd, cs_digits):
            proto[d].append(norm(sub))
        parsed.append((r, ur_digits, cd))

    ref = {d: np.mean(v, axis=0) for d, v in proto.items() if v}
    print('prototypes harvested from callsigns:', {d: len(v) for d, v in proto.items()})

    def classify(sub):
        v = norm(sub)
        scores = sorted(((float(np.abs(v - ref[d]).mean()), d) for d in ref))
        return scores[0][1], round(scores[0][0], 4), scores[1][1], round(scores[1][0], 4)

    # report rows where the UR digits differ from the callsign digits
    print('\nrow-by-row check of the UR number (independent glyph read):')
    disagree = 0
    for r, ur_digits, cd in parsed:
        got = ''.join(classify(s[2])[0] for s in ur_digits)
        if got != cd:
            disagree += 1
            sc = [classify(s[2]) for s in ur_digits]
            print(f"  {r['tail']:6} {r['month']:02d}/{r['day']:02d} {r['origin']}->{r['dest']}: "
                  f"callsign {r['callsign']}  UR digits read '{got}'  "
                  f"(best/second: {[(a, b, c, d_) for a, b, c, d_ in sc]})")
    print(f'\nrows where the glyph read disagrees with the callsign digits: {disagree} / {len(parsed)}')


if __name__ == '__main__':
    main()
