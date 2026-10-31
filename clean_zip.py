#!/usr/bin/env python3
"""clean_zip.py — reduce a messy FR24 export zip to a clean, CSV-only archive.

Takes any zip and returns a zip that contains **nothing but track CSVs**: no KML
track exports, no saved web pages, no spreadsheets, no screenshots, no nested
folders, no duplicate copies. Every track that survives keeps its canonical name
`<FLIGHT>-<8 hex>.csv`.

    python3 clean_zip.py "FR data.zip"                  # -> FR data_clean.zip
    python3 clean_zip.py "FR data.zip" -o clean.zip     # choose the output name
    python3 clean_zip.py "FR data.zip" --list-only      # report, write nothing
    python3 clean_zip.py "FR data.zip" --keep-kml       # keep KML after all

What counts as a duplicate, in the order it is applied:

  1. identical bytes, however the file is named (`x.csv` and `x_1.csv`)
  2. the same fixes under two names (a re-download that came back renamed)
  3. a partial download whose fixes are all contained in a fuller copy

KML files are reported by name, and the report says whether any flight exists
*only* as KML — in which case dropping it is a real loss of data rather than
just tidying up.
"""
from __future__ import annotations

import argparse
import collections
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fr24_update import (canonical_name, fixes, is_track, name_penalty,  # noqa: E402
                         rowset, rows_of, sha)

# things that turn up in these exports, and what to call them in the report
KIND = {'.kml': 'KML track export',
        '.kmz': 'KML track export (zipped)',
        '.mht': 'saved web page', '.mhtml': 'saved web page',
        '.html': 'saved web page', '.htm': 'saved web page',
        '.xlsx': 'spreadsheet', '.xls': 'spreadsheet', '.csv~': 'spreadsheet backup',
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'image',
        '.pdf': 'document', '.docx': 'document', '.doc': 'document',
        '.txt': 'text note', '.json': 'metadata', '.xml': 'metadata',
        '.ds_store': 'system file'}


def kind_of(name: str) -> str:
    base = os.path.basename(name).lower()
    if base == '.ds_store':
        return 'system file'
    ext = os.path.splitext(base)[1]
    return KIND.get(ext, f'{ext or "no"} file')


def flight_of(name: str) -> str:
    return os.path.basename(name).split('-')[0].upper()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('zipfile')
    ap.add_argument('-o', '--out', help='output zip name')
    ap.add_argument('--list-only', action='store_true', help='report only, write nothing')
    ap.add_argument('--keep-kml', action='store_true', help='keep KML files')
    a = ap.parse_args()

    src = a.zipfile
    if not zipfile.is_zipfile(src):
        print(f'{src} is not a zip file', file=sys.stderr)
        return 2
    out = a.out or f'{os.path.splitext(src)[0]}_clean.zip'

    zin = zipfile.ZipFile(src)
    before_bytes = sum(i.file_size for i in zin.infolist())

    kept, dropped, kml = [], collections.OrderedDict(), collections.OrderedDict()
    for i in zin.infolist():
        if i.is_dir():
            continue
        raw = zin.read(i.filename)
        if is_track(i.filename, raw):
            kept.append((i.filename, raw))
            continue
        base = os.path.basename(i.filename)
        dropped.setdefault(kind_of(i.filename), []).append((base, len(raw)))
        if base.lower().endswith(('.kml', '.kmz')):
            kml[base] = len(raw)

    print(f'{src}')
    print(f'  {len(kept) + sum(len(v) for v in dropped.values())} files in'
          f'  ({before_bytes/1024/1024:.2f} MB uncompressed)')
    print(f'  {len(kept)} track CSVs')
    noncsv = sum(len(v) for v in dropped.values())
    print(f'  {noncsv} non-CSV file(s) removed:')

    if a.keep_kml and kml:
        for base, size in kml.items():
            kept.append((base, zin.read([n for n in zin.namelist()
                                         if os.path.basename(n) == base][0])))
        dropped.pop('KML track export', None)
        print(f'    (--keep-kml: {len(kml)} KML file(s) kept)')

    for kind, items in sorted(dropped.items(), key=lambda kv: -len(kv[1])):
        names = ', '.join(n for n, _ in items[:4])
        more = f' and {len(items)-4} more' if len(items) > 4 else ''
        size = sum(s for _, s in items)
        print(f'    {kind:26s} {len(items):4d} file(s)  {size/1024:8.1f} KB   {names}{more}')

    # does any flight exist only as KML?
    csv_flights = {flight_of(n) for n, _ in kept}
    kml_flights = {flight_of(n) for n in kml}
    if kml_flights:
        only_kml = sorted(kml_flights - csv_flights)
        print(f'\n  KML files: {len(kml)} — flight numbers present: {len(kml_flights)}')
        if only_kml:
            print(f'  ** {len(only_kml)} flight(s) exist ONLY as KML and will be lost: '
                  f'{", ".join(only_kml[:10])}')
        else:
            print('  every KML flight also has a CSV, so nothing is lost by dropping them')

    # ------------------------------------------------------------------ dedupe
    groups = collections.defaultdict(list)
    for name, raw in kept:
        groups[sha(raw)].append((name, raw))
    stage, dupes = [], []
    for _, cands in groups.items():
        cands.sort(key=lambda c: name_penalty(c[0]))
        stage.append(cands[0])
        for name, _ in cands[1:]:
            dupes.append((name, 'identical copy'))

    seen_rows, stage2 = {}, []
    for name, raw in stage:
        s = rowset(raw)
        if s and s in seen_rows:
            dupes.append((name, f'same fixes as {seen_rows[s]}'))
            continue
        if s:
            seen_rows[s] = os.path.basename(name)
        stage2.append((name, raw))

    by_flight = collections.defaultdict(list)
    for name, raw in stage2:
        by_flight[flight_of(name)].append((name, raw))
    stage3 = []
    for flight, group in by_flight.items():
        group.sort(key=lambda c: -len(rowset(c[1])))
        for idx, (name, raw) in enumerate(group):
            s = rowset(raw)
            fuller = [m for m, r in group[:idx]
                      if (s - rowset(r)) == frozenset() and len(rowset(r)) > len(s)]
            if fuller:
                dupes.append((name, f'partial copy of {os.path.basename(fuller[0])}'))
                continue
            stage3.append((name, raw))

    print(f'\n  {len(dupes)} duplicate file(s) removed:')
    counts = collections.Counter(why.split(' as ')[0].split(' of ')[0] for _, why in dupes)
    for why, n in counts.most_common():
        print(f'    {why:26s} {n:4d} file(s)')

    used, tracks = set(), []
    for name, raw in sorted(stage3, key=lambda c: os.path.basename(c[0])):
        out_name = canonical_name(name, used)
        tracks.append((out_name, raw.replace(b'\r\n', b'\n')))

    if a.list_only:
        print(f'\n--list-only: would write {len(tracks)} tracks to {out}')
        return 0

    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, raw in tracks:
            z.writestr(name, raw)

    after = os.path.getsize(out)
    print(f'\nwrote {out}')
    print(f'  {len(tracks)} tracks  ({after/1024/1024:.2f} MB)  '
          f'was {len(kept) + noncsv} files ({before_bytes/1024/1024:.2f} MB uncompressed)')
    print(f'  every entry is a .csv: '
          f'{all(n.endswith(".csv") for n, _ in tracks)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
