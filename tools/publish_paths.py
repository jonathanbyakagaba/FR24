#!/usr/bin/env python3
"""Put the flight paths where they can be read: one CSV per flight, loose in one folder.

`FR data.zip` is what the analysis layer reads — ten scripts open it through `repo_layout.archive()`,
and it is byte-reproducible and de-duplicated — but a 9 MB zip is not something anybody can look at on
github.com. This publishes the same files, with the same names and the same bytes, as plain CSVs in
`flight_paths/`, so the record is readable and diffable on the branch: 1,001 tracks today, plus
whatever the run captured, all in one place, no archive to open.

    python3 tools/publish_paths.py                        # mirror the published archive
    python3 tools/publish_paths.py --capture work/ci_capture     # plus a night's capture
    python3 tools/publish_paths.py --folder flight_paths --dry-run

`INDEX.csv` is the table of contents — file, flight, FR24's track id, callsign, fix count, first and
last observation, size, sha8 — because a folder of a thousand CSVs needs one row per file to be
searchable at all. It is rewritten every run; the CSVs are only touched when their bytes differ, so a
night that captures nothing changes nothing.

Two entries that map to the same name are resolved by length: the longer trail wins. That is a real
case, not a defensive flourish — the archive holds a handful of thin late captures of a flight whose
full trail was recorded elsewhere.
"""
import argparse
import csv
import hashlib
import os
import re
import sys
import zipfile

COLS = ['file', 'flight', 'track_id', 'callsign', 'fixes', 'first_utc', 'last_utc',
        'bytes', 'sha8', 'source']
NAME_RE = re.compile(r'^(?:([A-Z0-9]{2,3}\d{2,4}[A-Z]?)-)?([0-9a-f]{6,12})\.csv$')


def read_bytes(path):
    with open(path, 'rb') as fh:
        return fh.read()


def summarise(name, raw, source):
    """One INDEX row for one track. Never raises: a broken file is a row saying so."""
    m = NAME_RE.match(name) or re.match(r'^(.+)\.csv$', name)
    flight = (m.group(1) or '') if m and m.lastindex else ''
    track = (m.group(2) if m and m.lastindex == 2 else (name[:-4] if name.endswith('.csv') else ''))
    row = {'file': name, 'flight': flight, 'track_id': track, 'callsign': '', 'fixes': 0,
           'first_utc': '', 'last_utc': '', 'bytes': len(raw),
           'sha8': hashlib.sha256(raw).hexdigest()[:8], 'source': source}
    try:
        lines = [l for l in raw.decode('utf-8', 'replace').splitlines() if l.strip()]
        if lines and lines[0].lower().startswith('timestamp'):
            lines = lines[1:]
        data = [l.split(',') for l in lines if ',' in l]
        row['fixes'] = len(data)
        if data:
            row['callsign'] = (data[0][2] if len(data[0]) > 2 else '').strip()
            row['first_utc'] = (data[0][1] if len(data[0]) > 1 else '').strip()
            row['last_utc'] = (data[-1][1] if len(data[-1]) > 1 else '').strip()
    except Exception:                                    # noqa: BLE001
        row['fixes'] = -1                                # counted as unreadable, still published
    return row


def from_zip(path, log):
    out = {}
    try:
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if not n.lower().endswith('.csv'):
                    continue
                base = os.path.basename(n)
                raw = z.read(n)
                prev = out.get(base)
                if prev is None or len(raw) > len(prev[0]):
                    out[base] = (raw, 'archive')
    except (OSError, zipfile.BadZipFile) as e:
        log(f'  ! {path}: {e}')
    return out


def from_dir(path, log):
    out = {}
    if not path or not os.path.isdir(path):
        return out
    for n in sorted(os.listdir(path)):
        if not n.lower().endswith('.csv') or n == 'INDEX.csv':
            continue
        try:
            out[n] = (read_bytes(os.path.join(path, n)), 'capture')
        except OSError as e:
            log(f'  ! {n}: {e}')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=os.environ.get('FR24_PUBLISH') or 'fr24_publish',
                    help='the publish directory (repo root in CI)')
    ap.add_argument('--folder', default='flight_paths', help='folder name inside the root')
    ap.add_argument('--zip', default='FR data.zip', help='the archive to mirror ("none" to skip)')
    ap.add_argument('--capture', action='append', default=[],
                    help='a capture dir of loose CSVs to add; repeatable')
    ap.add_argument('--prune', action='store_true',
                    help='delete files in the folder that the sources no longer name')
    ap.add_argument('--readme', action='store_true', help='(re)write the folder README')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    log = lambda m: (print(m), sys.stdout.flush())

    root = os.path.abspath(a.root)
    dest = os.path.join(root, a.folder)
    zp = os.path.join(root, a.zip) if a.zip != 'none' else ''
    tracks = {}
    if zp and os.path.exists(zp):
        tracks.update(from_zip(zp, log))
        log(f'  {os.path.basename(zp)}: {len(tracks)} track(s)')
    for c in a.capture:
        before = len(tracks)
        got = from_dir(c, log)
        tracks.update(got)
        log(f'  {c}: {len(got)} file(s), {len(tracks) - before} new name(s)')
    if not tracks:
        print(f'nothing to publish: no archive at {zp or "(disabled)"} and no readable --capture dir')
        return 1

    rows, written = [], 0
    os.makedirs(dest, exist_ok=True)
    for name in sorted(tracks):
        raw, src = tracks[name]
        p = os.path.join(dest, name)
        have = read_bytes(p) if os.path.exists(p) else None
        if have == raw:
            status = 'kept'
        else:
            status = 'refreshed' if have is not None else 'added'
            if not a.dry_run:
                tmp = p + '.tmp'
                with open(tmp, 'wb') as fh:
                    fh.write(raw)
                os.replace(tmp, p)
            written += 1
        rows.append(summarise(name, raw, src))
    rows.sort(key=lambda r: r['file'])
    tot = sum(r['bytes'] for r in rows)
    if not a.dry_run:
        with open(os.path.join(dest, 'INDEX.csv'), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
    extra = sorted(set(f for f in os.listdir(dest)
                       if f.endswith('.csv') and f not in tracks and f != 'INDEX.csv'))
    if extra:
        if a.prune and not a.dry_run:
            for f in extra:
                os.remove(os.path.join(dest, f))
            log(f'  pruned {len(extra)} file(s) no source names')
        else:
            log(f'  {len(extra)} file(s) in the folder that no source names (left alone; --prune removes)')
    if a.readme or not os.path.exists(os.path.join(dest, 'README.md')):
        with open(os.path.join(dest, 'README.md'), 'w') as fh:
            fh.write(
                '# flight paths\n\n'
                'One CSV per flight, as Flightradar24 recorded it: `Timestamp,UTC,Callsign,Position,'
                'Altitude,Speed,Direction`, positions as `lat,lon`, altitudes and speeds in feet and '
                'knots, times in UTC. Names are `<flight>-<fr24 track id>.csv` (a bare `<id>.csv` is a '
                'capture whose flight number the listing did not carry).\n\n'
                f'`INDEX.csv` is the table of contents: {len(rows)} files, {tot:,} bytes, newest '
                'observation last in each row. The build writes these files from `FR data.zip` and from '
                'each night\'s capture — `python3 tools/publish_paths.py` — and the archive stays the '
                'input to the analysis, which reads it through `work/repo_layout.py`.\n')
    fix = sum(max(r['fixes'], 0) for r in rows)
    obs = sorted({r['first_utc'][:10] for r in rows if r['first_utc']} |
                 {r['last_utc'][:10] for r in rows if r['last_utc']})
    log(f'{a.folder}: {len(rows)} track(s), {written} written, {fix:,} fixes, {tot / 1e6:.1f} MB'
        + (f' · observation dates {obs[0]} to {obs[-1]}' if obs else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
