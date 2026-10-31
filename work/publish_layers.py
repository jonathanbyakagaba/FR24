#!/usr/bin/env python3
"""Copy the analysis layers into `fr24_publish/`, so the build, the README and the upload
pack all describe the same bytes.

The recurring bug in this project has been a **stale publish copy**: a report script writes
`runway_usage.csv` beside the sources, `fr24_update.py` publishes only its own five core
files, and whatever was left in `fr24_publish/` from last time gets shipped as if it were
current.  Run this after the analysis scripts and before the build:

    python3 work/publish_layers.py            # copy what changed
    python3 work/publish_layers.py --check    # say what is stale, copy nothing

The four files the build writes itself (`FR data.zip`, `flights.csv`, `manifest.csv`,
`all_flights_aeroroutes.md`) are never touched — that is `fr24_update.py`'s work.  The file
list is shared with `work/close_month.py`, so a new published table is added in one place.

Three guards, because every stale copy in this project has arrived through one of these doors:

* a month product whose dated CSV reports on another month is refused (`month_signature`);
* the prose twin of a refused table is refused with it — `schedule_delays.md` carries no dates,
  so on its own it can be copied into any month and look entirely plausible;
* a cumulative layer is refused when the root copy is *smaller* than the published one: those
  layers are `append`-only like the archive, so a shrink means something rebuilt them from a
  narrower input (a one-off script once rewrote `tails.csv` from 701 records to 233).
  `--allow-shrink` overrides it when the archive really did lose rows.
"""
import argparse
import hashlib
import os
import csv
import shutil
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from close_month import FILES                          # noqa: E402
import repo_layout as RL                               # noqa: E402
from month_ctx import ctx                              # noqa: E402


ROOT = os.path.dirname(HERE)                            # workspace root, where layers are written
WRITTEN_BY_BUILD = {'FR data.zip', 'flights.csv', 'manifest.csv', 'all_flights_aeroroutes.md'}
# Reports that write *straight into* the live month folder.  They have no root copy, and
# publishing a root leftover over them would quietly replace a fresh build with last month's
# bytes — which is what happened to `triangle_routes.md` once.
MONTH_FOLDER_ONLY = {'triangle_routes.md'}

# Shared lookups, deliberately the same bytes in every month folder: the archive of tail claims,
# the app-flag table, the hardware record, and the runway measurement, which is one row per track of
# the whole archive.  Everything else in FILES is a *month product* — and a month product at the root
# that is byte-identical to a closed month's copy has not been regenerated, which is how a stale
# September report once landed in an October folder under October's name.
CUMULATIVE = {'tails.csv', 'app_status.csv', 'fleet_meta.csv', 'FR data.zip',
              'runway_usage.csv', 'runway_usage.md', 'no_code_tracks.md', 'no_code_tracks.csv',
              # both built by work/final.py from every screenshot record and the whole archive,
              # so they are one table shared by all month folders, like tails.csv
              'fleet_summary.csv', 'triangle_assignments.csv'}


def sibling_copies(dst_dir, name):
    """Other month folders that already hold a file of this name"""
    pub = os.path.dirname(dst_dir)
    out = []
    for d in sorted(os.listdir(pub)) if os.path.isdir(pub) else []:
        q = os.path.join(pub, d)
        if not os.path.isdir(q) or not re.match(r'^UR [A-Z]+ \d{4}$', d) or q == dst_dir:
            continue
        f = os.path.join(q, name)
        if os.path.exists(f):
            out.append((d, f))
    return out


def month_signature(path):
    """The month a CSV reports on, read off its first data row, or None if it does not say.

    Only the month-keyed columns count, and a file that mixes months (tails.csv spans three) has no
    single signature: those are cumulative lookups and travel as they are.
    """
    if not path.endswith('.csv'):
        return None
    try:
        with open(path, newline='', encoding='utf-8', errors='replace') as fh:
            rd = csv.DictReader(fh)
            cols = rd.fieldnames or []
            key = next((c for c in ('first_utc', 'departure_utc', 'when_utc', 'when', 'date',
                                    'day', 'date_local', 'track_date', 'valid') if c in cols), None)
            if not key:
                return None
            mon = {m: i + 1 for i, m in enumerate(
                'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
            months = set()
            for i, r in enumerate(rd):
                v = (r.get(key) or '').strip()
                if re.fullmatch(r'\d{4}-\d{2}.*', v):
                    months.add(v[:7])
                elif re.fullmatch(r'\d{2}[A-Za-z]{3}\d{2}.*', v):          # 18SEP26, the log's own
                    months.add(f'20{v[-2:]}-{mon[v[2:5].title()]:02d}')
                if i > 4000:
                    break
            return months.pop() if len(months) == 1 else None
    except Exception:
        return None


def csv_twin_refused(n, src, ym, dst_dir, names):
    """For `X.md`: is `X.csv` being refused this round, and if so why?

    A `.md` has no date column, so `month_signature` cannot see it — the pair rule is what stops
    a table's prose from landing in a folder the table itself was turned away from.
    """
    stem, ext = os.path.splitext(n)
    if ext.lower() != '.md':
        return None
    twin = stem + '.csv'
    if twin not in names:
        return None
    tsrc = os.path.join(os.path.dirname(src), twin)
    if not os.path.exists(tsrc):
        return f'`{twin}` is missing at the root'
    sig = month_signature(tsrc)
    if sig and sig != ym:
        return f'its table `{twin}` reports on {sig}, not {ym}'
    if twin not in CUMULATIVE:
        dup = next((d for d, q in sibling_copies(dst_dir, twin) if sha16(q) == sha16(tsrc)), None)
        if dup:
            return f'its table `{twin}` is byte-identical to {dup}/'
    return None


def sha16(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='report only, copy nothing')
    ap.add_argument('--allow-shrink', action='store_true',
                    help='let a cumulative layer get smaller (the archive lost rows for a reason)')
    a = ap.parse_args()

    dst_dir = RL.live_dir()
    C = ctx()
    moved = stale = 0
    print(f'layers -> {os.path.relpath(dst_dir, ROOT)}/   (build month {C["ym"]})')
    ym = ctx()['ym']
    for n in FILES:
        if n in WRITTEN_BY_BUILD:
            continue
        if n in MONTH_FOLDER_ONLY:
            print(f'  m {n:26s} not published')
            continue
        src, dst = os.path.join(ROOT, n), os.path.join(dst_dir, n)
        if not os.path.exists(src):
            if os.path.exists(dst):
                print(f'  ! {n:26s} only in the publish dir — nothing at the root to copy from')
                stale += 1
            continue
        # a root analysis file carries the month it was last regenerated for, and the live month
        # folder is not where another month's numbers belong — that is how a two-day-old October
        # folder ended up holding September's runway report
        if n in CUMULATIVE and os.path.exists(dst) and os.path.getsize(src) < os.path.getsize(dst):
            prior, now = os.path.getsize(dst), os.path.getsize(src)
            if a.allow_shrink:
                print(f'  ! {n:26s} shrinking {prior:,d} -> {now:,d} B, allowed by --allow-shrink')
            else:
                print(f'  x {n:26s} root copy is smaller than the published one ({prior:,d} -> '
                      f'{now:,d} B); a cumulative layer only shrinks if it was rebuilt from a '
                      f'narrower input — --allow-shrink to override')
                stale += 1
                continue
        pair = csv_twin_refused(n, src, ym, dst_dir, set(FILES))
        if pair:
            print(f'  x {n:26s} refused with its table: {pair}')
            stale += 1
            continue
        sig = month_signature(src)
        if sig and sig != ym:
            print(f'  x {n:26s} root copy is {sig}, not {ym} — run FR24_MONTH={ym} python3 work/<report>.py')
            stale += 1
            continue
        if n not in CUMULATIVE:
            dup = next((d for d, q in sibling_copies(dst_dir, n) if sha16(q) == sha16(src)), None)
            if dup:
                print(f'  x {n:26s} byte-identical to {dup}/ \u2014 the root copy is that month\u2019s '
                      f'numbers, not {ym}\u2019s; regenerate it: '
                      f'FR24_MONTH={ym} python3 work/<report>.py')
                stale += 1
                continue
        same = os.path.exists(dst) and sha16(src) == sha16(dst)
        if same:
            print(f'  = {n:26s} already current')
            continue
        moved += 1
        print(f'  {"~" if os.path.exists(dst) else "+"} {n:26s} '
              f'{os.path.getsize(src):>9,d} B' + ('' if a.check else '  copied'))
        if not a.check:
            shutil.copy2(src, dst)
    if moved:
        stale += moved
        if a.check:
            print(f'\n{moved} file(s) out of date — run without --check')
            return 1
    else:
        print('\nnothing to copy: the publish dir matches the root analyses')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
