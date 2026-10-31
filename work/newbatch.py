#!/usr/bin/env python3
"""Start a new screenshot capture batch without renaming anything by hand.

The OCR chain that turns the app pages into `work/screens_extra/batch_*.csv` was copied by
hand for every capture date — `parse_rows_30.py`, `crosscheck_30.py`, `make_batch_30.py` and
seven siblings, each named after the 30 September batch it was written for.  This does the
copy and the rewrite in one step:

    python3 work/newbatch.py 03Oct --date 2026-10-03
    python3 work/newbatch.py 03Oct --date 2026-10-03 --dry-run    # show, change nothing

What changes in the copies:

| was | becomes |
|---|---|
| `work/shots30/` | `work/shots<TAG>/` |
| `records_30.json`, `ocr_rows_30.json`, `crosscheck_30.csv` | the same with `_<TAG>` |
| `work/screens_20260930_rows.csv` | `work/screens_<YYYYMMDD>_rows.csv` |
| `work/screens_extra/batch_2026-09-30.csv` | `.../batch_<date>.csv` |
| `1 <= d <= 30` day bounds | the capture month's real last day |
| "30 September" in prose | the new date, spelled |

The one thing a script cannot know is which page belongs to which airframe — the app prints
the registration in the page header, so that map is read off the captures.  Drop it beside the
images before running this and the copies read it from there instead of from a dictionary baked
into the source:

    work/shots03Oct/tailmap.json
    {"images": {"NORM_Screenshot_20261003_071213_Flightradar24.jpg": "5X-EQU", ...},
     "norm":   {"Screenshot_20261003_071213_Flightradar24.jpg": "NORM_Screenshot_20261003_071213_Flightradar24.jpg"}}

(the keys are what the copied stages look for, so an unmapped batch is a visible gap rather
than a silent one: without the file the dictionaries carry the previous batch's filenames and
the tool says so, listing the lines to fill.)

Without that file the stages are still written; the tool just prints the lines to fill in.
`work/ocr_rows_tall.py` needs no copy — it already takes its images and output path as arguments.
"""
import argparse
import calendar
import datetime as dt
import glob
import json
import os
import re
import sys

WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work')

STAGES = ['parse_rows_30.py', 'merge_rows_30.py', 'crosscheck_30.py', 'dates_check_30.py',
          'crop_rows30.py', 'page_meta_30.py', 'reocr_rows_30.py', 'make_batch_30.py',
          'tail_conflicts_30.py', 'tail_overlaps_30.py']
RUN_ORDER = ['ocr_rows_tall (args)', 'parse_rows', 'merge_rows', 'crosscheck', 'dates_check',
             'crop_rows', 'page_meta', 'make_batch', 'tail_conflicts', 'tail_overlaps']


def dst_name(src_name, tag):
    """`parse_rows_30.py` / `crop_rows30.py` -> `parse_rows_<tag>.py` / `crop_rows_<tag>.py`"""
    stem = re.sub(r'_?30$', '', re.sub(r'\.py$', '', src_name))
    return f'{stem}_{tag}.py'


def rewrite(text, tag, date, src, src_last_day):
    """One batch's identity -> another's.  Longest, most specific tokens first."""
    ymd, iso = f'{date:%Y%m%d}', f'{date:%Y-%m-%d}'
    s_ymd, s_iso = f'{src:%Y%m%d}', f'{src:%Y-%m-%d}'
    s_day, src_tag = f'{src.day}', '30'
    out = text
    out = out.replace(f'screens_{s_ymd}_rows.csv', f'screens_{ymd}_rows.csv')
    out = out.replace(f'batch_{s_iso}.csv', f'batch_{iso}.csv')
    out = out.replace(f'_2026{src.month:02d}{s_day.zfill(2)}_', f'_{ymd}_')      # image stems
    out = out.replace(f'crop_rows{src_tag}.py', f'crop_rows_{tag}.py')
    out = out.replace(f'shots{src_tag}', f'shots{tag}')
    out = out.replace(f'rows{src_tag}', f'rows{tag}')
    # every artefact of a batch carries the tag after an underscore: ocr_rows_30.json,
    # crosscheck_30.csv, records_30_checked.json.  Dates use `-30`, not `_30`, so the
    # plain swap cannot touch them.
    out = out.replace(f'_{src_tag}', f'_{tag}')
    out = out.replace(f'{src_tag}.py', f'{tag}.py')
    out = out.replace(s_iso, iso)
    out = out.replace(f'{int(s_day)} September', f'{date.day} {date:%B}')
    out = out.replace(f'{int(s_day)} Sep', f'{date.day} {date:%b}')
    out = out.replace(f'ending on {int(s_day)} {date:%B}', f'ending on {date.day} {date:%B}')
    out = re.sub(rf'\ble {src_last_day}\b', f'le {date.day}', out)
    # the day-of-month bounds in the date-outlier check follow the month, not the batch
    last = calendar.monthrange(date.year, date.month)[1]
    for was, now in ((f'1 <= d <= {src_last_day}', f'1 <= d <= {last}'),
                     (f'(d > {src_last_day} or d < 1)', f'(d > {last} or d < 1)'),
                     (f'1 <= (day(r) or 0) <= {src_last_day}', f'1 <= (day(r) or 0) <= {last}')):
        out = out.replace(was, now)
    return out


def use_tailmap(text, tag, tailmap):
    """Swap an inline `TAIL = {...}` / `NORM = {...}` dict for a read from tailmap.json.

    Done only when the folder carries the file and the script can already read JSON, so a
    batch whose pages have not been mapped yet keeps its shape rather than losing data.
    """
    keys = set(json.load(open(tailmap)))
    if 'import json' not in text:
        return text

    def sub(m):
        var = m.group(1)
        # TAIL(S) maps a capture to its registration, IMAGES/NAME maps a file to its
        # normalised copy — the two per-batch tables a script cannot invent
        key = 'images' if var.startswith('TAIL') else 'norm'
        return (m.group(0) if key not in keys else
                f"{var} = json.load(open('work/shots{tag}/tailmap.json'))['{key}']")

    # a dict of strings, no nesting: match to the brace that closes it, wherever it sits
    return re.sub(r'^(TAILS?|NORM|IMAGES|NORMS)\s*=\s*\{(?:[^{}]|\{[^{}]*\})*\}',
                  sub, text, flags=re.M)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tag', help="short label for the batch, e.g. 03Oct")
    ap.add_argument('--date', help='capture date YYYY-MM-DD (default: today)')
    ap.add_argument('--from-date', default='2026-09-30', help='the batch being copied from')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    date = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    src = dt.date.fromisoformat(a.from_date)
    src_last = calendar.monthrange(src.year, src.month)[1]
    shots_dir = os.path.join(WORK, f'shots{a.tag}')
    tailmap = os.path.join(shots_dir, 'tailmap.json')
    imgs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(shots_dir, '*Screenshot*.jpg')))

    print(f'batch {a.tag}  ·  captured {date:%d %B %Y}  ·  work/shots{a.tag}/')
    print(f'  {len(imgs)} capture image(s) in place · tailmap.json '
          f'{"found — inline maps replaced by a read from it" if os.path.exists(tailmap) else "absent"}')

    written = []
    for stage in STAGES:
        src_path = os.path.join(WORK, stage)
        if not os.path.exists(src_path):
            print(f'  ! {stage} is not in work/ — skipped')
            continue
        text = open(src_path).read()
        out = rewrite(text, a.tag, date, src, src_last)
        if os.path.exists(tailmap):
            out = use_tailmap(out, a.tag, tailmap)
        name = dst_name(stage, a.tag)
        dst = os.path.join(WORK, name)
        current = os.path.exists(dst) and open(dst).read() == out
        written.append(name)
        print(f'  {"=" if current else "+"} work/{name}')
        if not a.dry_run and not current:
            open(dst, 'w').write(out)

    if a.dry_run:
        print(f'\ndry run: {len(written)} stage(s) would be written — nothing changed')
        return 0
    os.makedirs(shots_dir, exist_ok=True)

    todo = []
    for name in written:
        for i, line in enumerate(open(os.path.join(WORK, name)).read().splitlines(), 1):
            if re.match(r'^(TAILS?|NORM|IMAGES|NORMS)\s*=\s*\{', line) or "'NORM_Screenshot_" in line:
                todo.append(f'work/{name}:{i}')
    if todo and not os.path.exists(tailmap):
        print(f'\nfill in the image→tail map — read off each page header ({len(todo)} place(s)):')
        for t in todo[:12]:
            print(f'  {t}')
        if imgs:
            print('  images waiting:')
            for im in imgs[:8]:
                print(f'    {im}')
    elif todo:
        print(f'\n{len(todo)} map line(s) still inline — tailmap.json exists but was not read; check it')

    print('\nrun order:')
    print(f'  1. python3 work/ocr_rows_tall.py work/shots{a.tag}/*Screenshot*.jpg '
          f'work/shots{a.tag}/ocr_rows_{a.tag}.json')
    n = 2
    for stage in RUN_ORDER[1:]:
        cand = [w for w in written if w.startswith(stage)]
        if cand:
            print(f'  {n}. python3 work/{cand[0]}')
            n += 1
    print(f'  {n}. PYTHONPATH=. python3 work/final.py        # folds the batch into tails.csv')
    print(f'  {n + 1}. python3 work/publish_layers.py && python3 fr24_update.py --zip "incoming/…"')
    return 0


if __name__ == '__main__':
    sys.exit(main())
