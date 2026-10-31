#!/usr/bin/env python3
"""Close a finished month in `fr24_publish/UR SEPTEMBER 2026/`.

The month's files usually already live in that folder — `fr24_update.py` writes a live month
straight into its own folder, exactly as the repository keeps them — so closing is mostly:
complete whatever is missing, write the folder's README with the numbers current at close,
and drop the `.closed` marker that tells the reports, the pack and the README that this month
is a finished snapshot.  Nothing is re-derived and nothing is filtered: the tables keep
whatever they held, and the README says exactly what that includes and where it reaches
outside the month.

Freezing is no longer what protects a closed month from the next export — the folder does
that, because a build only ever writes the month it is building.

The month folder deliberately does not carry `reference/` or `metar/`: those are shared
lookups that live at the top level and change with the network, not with the month.

Run it *before* the first export of the next month, because `fr24_update.py --month auto`
rebuilds the top-level log for the latest month in the archive: once October tracks arrive,
September's log only exists in this folder.

    python3 work/close_month.py 2026-09
    python3 work/close_month.py 2026-09 --dry-run
    python3 work/close_month.py 2026-09 --force        # re-freeze over an existing folder
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import os
import re
import shutil
import sys
import zipfile

import repo_layout as RL     # the folder is named the way the repo names it.  RL, not L:
#                  every report here uses a local `L = []` for its output lines
P = RL.PUBLISH                                # the build, FR24_PUBLISH-aware
ROOT = RL.ROOT                                # evidence files that live beside the build
FILES = ['all_flights_aeroroutes.md', 'flights.csv', 'manifest.csv', 'FR data.zip',
         'tails.csv', 'app_status.csv', 'punctuality.csv', 'punctuality.md',
         'triangle_assignments.csv', 'triangle_routes.md', 'fleet_summary.csv',
         'runway_usage.csv', 'runway_usage.md', 'flight_conditions.csv',
         'weather_analysis.md', 'date_coverage.md', 'data_gaps.md', 'no_code_tracks.md',
         'schedule_delays.csv', 'schedule_delays.md']


def last_day(ym):
    """'2026-09' -> '2026-09-30', from the calendar rather than from memory"""
    y, m = int(ym[:4]), int(ym[5:7])
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    return (nxt - dt.timedelta(days=1)).isoformat()


def fmt_counts(c, focus=None):
    """{'2026-03': 80, ...} -> '610 in 2026-09, the rest 2026-03 ×80, 2026-08 ×20'

    Written out rather than printed as a dict, because this lands in a published README.
    """
    items = [(k, v) for k, v in sorted(c.items()) if k != focus]
    head = f"**{c[focus]:,} in {focus}**" if focus in c else ""
    if not items:
        return head or "—"
    if len(items) > 6:
        tail = ', '.join(f'{k} ×{v}' for k, v in items[-6:])
        tail += f' and {len(items) - 6} more'
    else:
        tail = ', '.join(f'{k} ×{v}' for k, v in items)
    return f"{head}, the rest {tail}" if head else tail


def sha16(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def rows(path):
    with open(path, newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def month_of(s):
    return (s or '')[:7]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('month', help='YYYY-MM to freeze')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}', a.month):
        # the repo names folders `UR SEPTEMBER 2026`; accept that form too and read the month
        # off it, so a command copied out of the README or a folder listing just works
        parsed = RL.ym_of_folder((a.month or '').rstrip('/') + '/')
        if parsed:
            print(f'  ({a.month!r} read as {parsed})')
            a.month = parsed
    if not re.fullmatch(r'\d{4}-\d{2}', a.month):
        raise SystemExit(f'month must look like 2026-09, got {a.month!r}')
    dst = os.path.join(P, RL.month_folder(a.month))   # 'UR SEPTEMBER 2026', not '2026-09'
    if os.path.isdir(dst) and not a.force:
        raise SystemExit(f'{dst} already exists — pass --force to re-freeze over it')

    # a file may already sit in this folder: the build writes a live month straight into it,
    # and the root copies are where the day-by-day reports are generated
    def find(n):
        """this month's copy of a file: the folder first, then the publish root for anything
        shared.  Not the workspace root — the tables there belong to whatever month last ran
        the analysis, and falling back to them once froze September's numbers into October."""
        return next((q for q in (os.path.join(dst, n), os.path.join(P, n))
                     if os.path.exists(q)), None)

    have = {n: q for n in FILES if n != 'FR data.zip' and (q := find(n))}
    # The archive keeps whatever name this month actually uses for it — look that name up in
    # the build rather than deriving it, because a derived name once left `UR 26- flights.zip`
    # sitting in a month folder next to the real file.
    want = f'ur {month_word(a.month)} flights.zip'.lower()
    where = [ROOT] + ([dst] if os.path.isdir(dst) else [])
    # safe to look this one up by name anywhere: the name itself says which month it is
    named = next((n for d in where for n in os.listdir(d) if n.lower() == want), None)
    arch = named or ('FR data.zip' if find('FR data.zip') else None)
    if arch:
        have[arch] = find(arch)
    # the archive is cumulative, so a month folder carries one copy of it under one name —
    # shipping both names would put 6 MB of identical bytes into every upload
    # 'FR data.zip' is only "absent" from the folder when the month has its own archive name
    missing = [n for n in FILES if n not in have and not (n == 'FR data.zip' and arch)]

    log_p = find('flights.csv')
    log = rows(log_p) if log_p else []
    log_m = collections.Counter(month_of(iso_of(r['date_local'])) for r in log)
    man = rows(find('manifest.csv'))
    tr_m = collections.Counter(month_of(r['first_utc']) for r in man)
    straddle = [r for r in man if month_of(r['first_utc']) != month_of(r['last_utc'])
                and a.month in (month_of(r['first_utc']), month_of(r['last_utc']))]
    tp = find('tails.csv')
    t = rows(tp) if tp else []
    spread = {c: sorted({month_of(r[c]) for r in t if r.get(c)})
              for c in ('date',) if t and 'date' in t[0]}

    if log_m and max(log_m, key=log_m.get) != a.month:
        print(f'  ! the build log is mostly {max(log_m, key=log_m.get)} '
              f'({log_m[max(log_m, key=log_m.get)]} flights), not {a.month} — '
              f'freeze the month the build actually holds')

    print(f'freeze {a.month} -> {dst}/')
    print(f'  log: {len(log)} flights, months {dict(log_m)}')
    print(f'  archive: {len(man)} tracks, months {dict(sorted(tr_m.items()))}')
    print(f'  tracks crossing into/out of {a.month}: {len(straddle)}')
    for r in straddle[:6]:
        print(f"     ~ {r['file']:26s} {r['flight']:8s} {r['first_utc'][:16]} -> {r['last_utc'][:16]}")
    print(f'  archive in the folder: {arch or "none found"}')
    print(f'  files: {len(have)} to copy' + (f', {len(missing)} absent ({", ".join(missing)})'
                                             if missing else ''))
    if missing:
        print('  ! absent means the analysis for this month was never published into the '
              'folder —\n    run the layers, then `python3 work/publish_layers.py`, then close again.\n'
              '    Nothing from an earlier month is copied in to fill the gap.')
    if a.dry_run:
        print('\ndry run: nothing written')
        return 0

    os.makedirs(dst, exist_ok=True)
    moved = held = 0
    for n, src in have.items():
        tgt = os.path.join(dst, n)
        if os.path.abspath(src) == os.path.abspath(tgt):
            held += 1                                # already exactly where it belongs
            continue
        if os.path.exists(tgt) and open(tgt, 'rb').read() == open(src, 'rb').read():
            held += 1                                # same bytes, nothing to do
            continue
        shutil.copy2(src, tgt)
        moved += 1
    print(f'  wrote {moved} file(s) into the folder, {held} already in place')

    sizes = {n: os.path.getsize(os.path.join(dst, n)) for n in os.listdir(dst)
             if not n.startswith('.')}
    zpath = os.path.join(dst, arch or 'FR data.zip')
    zsha = sha16(zpath) if os.path.exists(zpath) else None
    top = os.path.join(P, 'FR data.zip')
    same = (os.path.exists(zpath) and os.path.exists(top)
            and os.path.getsize(zpath) == os.path.getsize(top)
            and zsha == sha16(top))

    L = []
    w = L.append
    w(f'# {a.month} — closed flight log and track archive')
    w('')
    w(f'Frozen **{RL.today().isoformat()}** from the build of that name. This folder is a '
      'snapshot: nothing here is regenerated when a new export arrives, and the top level of the '
      'repository now describes the month being collected. The rule used throughout: **a flight '
      'belongs to the month its departure falls in, local time** — so a leg that departs '
      f'{last_day(a.month)} and lands on the 1st of the next month is counted here, and a track that '
      'starts in this month is a track of this month even if it ends outside it.')
    w('')
    all_in = set(log_m) == {a.month}
    w(f'* **{len(log)} logged flights**'
      + (f', every one dated in {a.month}.' if all_in
         else f' — {fmt_counts(log_m, a.month)}.'))
    w(f'* **{len(man)} tracks · {sum(int(r["fixes"]) for r in man):,} fixes** in the archive zip: '
      f'{fmt_counts(tr_m, a.month)} — the archive is cumulative, so earlier months stay in it and '
      f'nothing here was pruned to fit the calendar.')
    n_s = len(straddle)
    w(f'* **{n_s} track{" crosses" if n_s == 1 else " tracks cross"} this month\'s boundary**'
      + (': ' + ', '.join(f'`{r["file"]}` ({r["first_utc"][:10]} → {r["last_utc"][:10]})'
                          for r in straddle[:4]) if straddle else '')
      + (f'. {"It is" if n_s == 1 else "They are"} stored whole — one track is never split across '
         'two zips.' if n_s else ', so every file here belongs to exactly one month.'))
    if spread.get('date'):
        w(f'* `tails.csv` rows reach **{spread["date"][0]} → {spread["date"][-1]}**: the per-tail app '
          'pages are rolling history rather than a calendar month, so a closed month keeps whatever '
          'the pages held on the day it was captured. Rows outside this month are the older tail-end '
          'of those pages, not contamination.')
    w('')
    w('## What is in this folder')
    w('')
    w('| file | size | rows |')
    w('|---|---|---|')
    for n in sorted(sizes):
        if n == 'README.md':
            continue
        cnt = ''
        if n.endswith('.csv'):
            try:
                cnt = f'{max(0, len(open(os.path.join(dst, n), encoding="utf-8").read().splitlines()) - 1):,}'
            except OSError:
                pass
        elif n == 'FR data.zip':
            cnt = f'{len([x for x in zipfile.ZipFile(os.path.join(dst, n)).namelist() if x.endswith(".csv")]):,} tracks'
        elif n.endswith('.md'):
            cnt = f'{len(open(os.path.join(dst, n), encoding="utf-8").read().splitlines())} lines'
        w(f'| `{n}` | {sizes[n] / 1024:.0f} KB | {cnt or "—"} |')
    w('')
    if zsha:
        w('## Verifying the freeze')
        w('')
        w(f'`FR data.zip` sha256 `{zsha}`.')
        if same:
            w('It is byte-identical to the top-level archive **at freeze time** (the archive is '
              'cumulative, so the two diverge as soon as the next month\'s export is published — '
              f'this copy is the {a.month} edition, permanently).')
            w('')
            w('Because the bytes are already published at the top level, the upload pack leaves this '
              'copy out: `manifest.csv` here names every track of the month, and they are in the '
              'archive one level up. The folder still holds its own copy on disk, so the month can be '
              're-derived from this folder alone, whatever the top level becomes.')
        else:
            w('It differs from the top-level archive, which has moved on since this month closed: '
              'this copy is the one that matches the tables beside it.')
    w('')
    w('`reference/` and `metar/` are not duplicated here: they are shared lookups described by the '
      'top-level README, and the weather this month was measured against is the month-stamped file '
      'named in `flight_conditions.csv`\'s own rebuild line.')
    w('')
    w('## How this folder was made')
    w('')
    w('```')
    w(f'python3 work/close_month.py {a.month}')
    w('```')
    w('')
    w('Re-running it with `--force` re-freezes from the current build, which is only correct if the '
      'build still holds this month\'s log.')
    w('')
    with open(os.path.join(dst, 'README.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')

    tot = sum(sizes.values()) + sizes.get('README.md', 0)
    n_here = len([n for n in os.listdir(dst) if not n.startswith('.')])
    print(f'\nwrote {dst}/: {n_here} files ({tot:,} B) plus the .closed marker')
    # the marker, not the folder's existence, is what says "this month is finished": a live
    # month is a folder too, and the next export must still be allowed to write into its own
    RL.mark_closed(dst)
    print('  .closed written — the pack and the reports now treat this month as read-only')
    for n in sorted(os.listdir(dst)):
        if n.startswith('.'):
            continue
        print(f'  {os.path.getsize(os.path.join(dst, n)):>10,}  {n}')
    return 0


MONN = {m: i for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                                    'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}
def month_word(ym):
    """'2026-09' -> 'September', read off repo_layout's folder naming so the two can never
    disagree about what a month is called"""
    return RL.month_folder(ym).split()[1].title()


def iso_of(dlocal):
    """the log writes 01SEP26; anything already ISO passes through"""
    m = re.match(r'^(\d{2})([A-Z]{3})(\d{2})$', dlocal or '')
    if not m:
        return dlocal
    d, mon, y = m.groups()
    return f'20{y}-{MONN.get(mon.upper(), 1):02d}-{d}'


if __name__ == '__main__':
    sys.exit(main())
