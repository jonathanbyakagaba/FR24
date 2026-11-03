#!/usr/bin/env python3
r"""Run the whole FR24 build from a checkout of this repository, and nothing else.

    python3 tools/ci_run.py --plan            # what would run, and why each skipped step is skipped
    python3 tools/ci_run.py --fetch           # fetch first, then build
    python3 tools/ci_run.py --changed-file /tmp/changed   # plus the paths to commit

The workspace and the repository have the same tree, so the scripts run unchanged: `fr24_publish`
is a symlink to the checkout root, which is where `FR data.zip`, `reference/`, `metar/` and the
month folders live. The flat copies the analysis scripts read and write *beside* themselves
(`fleet_summary.csv`, `app_status.csv`, …) are unbundled from the newest month folder before the
build and are gitignored, so they never look like output.

Three rules this obeys, because every broken version of this process broke one of them:

* **A missing input is a skip with a reason, never a silent blank.** The layers that need a human
  (app-status screenshots, timetable OCR) are copied forward untouched and reported as stale when
  the newest capture lags the newest fix by more than `--stale-days`.
* **Never commit — the workflow does that**, so this can be run by hand as often as you like.
* **A month is not frozen here.** `close_month.py` moves tables into a folder that later builds
  stop touching; that stays a `workflow_dispatch` decision (`tools/ci_run.py --close-month 2026-10`).
"""
import argparse
import csv
import datetime as dt
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'fr24_publish')


def sh(cmd, env=None, timeout=1500):
    """Run one build step. Returns (ok, tail-of-output)."""
    e = dict(os.environ)
    e['PYTHONPATH'] = ROOT + os.pathsep + os.path.join(ROOT, 'work')
    e.update(env or {})
    p = subprocess.run(cmd, cwd=ROOT, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors='replace', timeout=timeout)
    out = (p.stdout or '').strip().split('\n')
    return p.returncode == 0, '\n'.join(out[-6:])


def newest_fix():
    """The last fix the archive actually holds, from the published manifest. The build's own
    clock is not evidence: only the tracks say what has been recorded."""
    best = None
    for man in sorted(glob.glob(os.path.join(PUB, 'UR *', 'manifest.csv'))):
        try:
            for r in csv.DictReader(open(man, newline='', encoding='utf-8', errors='replace')):
                v = (r.get('last_utc') or '').strip().replace('T', ' ').rstrip('Z')
                if v and (best is None or v > best):
                    best = v
        except Exception:                                        # noqa: BLE001
            continue
    if not best:
        return None
    try:
        # the manifest stamps `2026-10-15 00:46:11Z`, the logs use `T`. Read either.
        return dt.datetime.strptime(best.replace('T', ' ').rstrip('Z')[:19],
                                     '%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def newest_month_folder():
    """The folder a build would rewrite: the newest `UR <MONTH> <YEAR>` in the tree."""
    NAME = {m.lower(): i + 1 for i, m in enumerate(
        'January February March April May June July August September October November December'.split())}
    best = None
    for d in sorted(glob.glob(os.path.join(PUB, 'UR *'))):
        m = re.fullmatch(r'UR ([A-Za-z]+) (\d{4})', os.path.basename(d))
        if not m or m.group(1).lower() not in NAME:
            continue
        ym = f"{m.group(2)}-{NAME[m.group(1).lower()]:02d}"
        if best is None or ym > best[0]:
            best = (ym, d)
    return best or (None, None)


FLAT = ['fleet_summary.csv', 'tails.csv', 'app_status.csv', 'fleet_meta.csv', 'flight_conditions.csv',
        'weather_analysis.md', 'punctuality.csv', 'punctuality.md', 'runway_usage.csv', 'runway_usage.md',
        'schedule_delays.csv', 'schedule_delays.md', 'no_code_tracks.md', 'date_coverage.md',
        'data_gaps.md', 'route_distances.csv', 'runway_centreline_fit.csv']


def unbundle():
    """Put the newest month's tables at the root, where the analysis scripts read them."""
    ym, folder = newest_month_folder()
    if not folder:
        return 0, None
    n = 0
    for name in FLAT:
        src = os.path.join(folder, name)
        if os.path.exists(src):
            with open(src, 'rb') as fh:
                data = fh.read()
            with open(os.path.join(ROOT, name), 'wb') as fh:
                fh.write(data)
            n += 1
    ref = os.path.join(PUB, 'reference', 'route_distances.csv')
    if os.path.exists(ref) and not os.path.exists(os.path.join(ROOT, 'route_distances.csv')):
        with open(ref, 'rb') as fh:
            data = fh.read()
        with open(os.path.join(ROOT, 'route_distances.csv'), 'wb') as fh:
            fh.write(data)
    return n, ym


def screenshot_latest():
    """The newest date a human capture claims, from `work/screens_YYYYMMDD*` and the dots file."""
    days = []
    for p in glob.glob(os.path.join(ROOT, 'work', 'screens_*')):
        m = re.search(r'(20\d{6})', os.path.basename(p))
        if m:
            days.append(m.group(1))
    try:
        # only a name that parses as a real date counts: a folder called `shots30` says which day
        # it was shot on far less reliably than `screens_20260930_rows.csv`, and trusting it once
        # turned a staleness warning into a crash on month 30.
        return dt.datetime.strptime(max(days), '%Y%m%d').strftime('%Y%m%d')
    except (ValueError, TypeError):
        return ''


SKIP_DIRS = {'.git', '__pycache__', 'node_modules'}


def tracked():
    """mtime of every path the build may publish, keyed relative to the checkout root.

    The root's flat copies are left out on purpose: they are scratch this tool unbundles, and
    counting them would make every run look like it had published fifteen files.
    """
    out = {}
    for dirpath, dirs, files in os.walk(PUB):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if os.path.realpath(dirpath) == os.path.realpath(ROOT):
            dirs[:] = [d for d in dirs if d in ('reference', 'metar') or d.startswith('UR ')]
            files = [f for f in files if f in ('FR data.zip', 'README.md', 'fleet_meta.csv')]
        for f in files:
            if f == '.closed':
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT).replace(os.sep, '/')
            if rel.startswith(('work/', 'tools/', '.github/', 'incoming/', 'uploads/')):
                continue
            try:
                out[rel] = os.path.getmtime(full)
            except OSError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--plan', action='store_true', help='print the step plan and stop')
    ap.add_argument('--fetch', action='store_true', help='run tools/fetch_fr24.py first')
    ap.add_argument('--since', default='', help='fetch window start (default: newest fix - 3 days)')
    ap.add_argument('--until', default='', help='fetch window end (default: today)')
    ap.add_argument('--capture-zip', default='work/ci_capture/FR data.zip')
    ap.add_argument('--stale-days', type=int, default=5, help='how long a human layer may lag before it is flagged')
    ap.add_argument('--close-month', default='', help='run close_month.py for this YYYY-MM and stop')
    ap.add_argument('--changed-file', default='', help='write the published paths that changed here, one per line')
    ap.add_argument('--allow-archive-fallback', action='store_true',
                    help='with no capture, rebuild from FR data.zip as it sits on the branch')
    ap.add_argument('--skip', action='append', default=[], metavar='STEP',
                    help='skip a step by name (repeatable): weather, fta, gaps, ocr')
    a = ap.parse_args()

    fix = newest_fix()
    today = dt.datetime.now(dt.timezone.utc)
    print(f'checkout      : {ROOT}')
    print(f'publish dir   : {"fr24_publish -> repo root" if os.path.islink(PUB) or PUB == ROOT else PUB}')
    print(f'newest fix    : {fix.strftime("%Y-%m-%d %H:%M:%SZ") if fix else "(no manifest yet)"}')
    print(f'month folder  : {newest_month_folder()[1] or "(none)"}')

    if a.close_month:
        ok, tail = sh(['python3', 'work/close_month.py', a.close_month, '--force'])
        print(f'close {a.close_month}: {"ok" if ok else "FAILED"}\n  ' + tail.replace('\n', '\n  '))
        return 0 if ok else 1

    steps = []
    if a.fetch and 'fetch' not in a.skip:
        since = a.since or ((fix or today).date() - dt.timedelta(days=3)).isoformat()
        until = a.until or today.date().isoformat()
        steps.append(('fetch', ['python3', 'tools/fetch_fr24.py', '--since', since, '--until', until,
                                '--out', os.path.dirname(a.capture_zip)],
                      'the trails expire in ~4 days: this is the reason the job is scheduled'))
    # The capture, if there is one: the build is supposed to run on the flights FR24 has, not on
    # whatever archive a person last uploaded. `--allow-archive-fallback` is the old behaviour.
    cap = os.path.exists(a.capture_zip)
    if not cap and not a.allow_archive_fallback:
        print(f'\nno capture at {a.capture_zip}: nothing was fetched, so there is nothing new to build '
              f'on. The archive on the branch is left alone. (--allow-archive-fallback rebuilds it.)')
        return 0
    ing_src = a.capture_zip if cap else os.path.join(PUB, 'FR data.zip')
    if 'ingest' not in a.skip:
        steps.append(('ingest', ['python3', 'fr24_update.py', '--zip', ing_src, '--month', 'auto'],
                      'the archive, manifest.csv, flights.csv and the log'))
    for name, cmd, why, needs in (
        ('weather', ['python3', 'work/weather.py'], 'published METAR per airport', []),
        ('metar', ['python3', 'work/metar_split.py'], 'the per-station METAR lookups', ['weather']),
        ('reference', ['python3', 'work/make_reference.py'], 'reference/ lookups', []),
        ('final', ['python3', 'work/final.py'], 'tails.csv, fleet_summary.csv, triangle tables', ['work/records_checked.json']),
        ('app_status', ['python3', 'work/app_status.py'], 'the app status flags', ['work/status_dots.csv']),
        ('runways', ['python3', 'work/runways.py'], 'runway use per track', ['work/rwy/runways.csv']),
        ('runway_report', ['python3', 'work/runway_report.py'], 'runway_usage.md', []),
        ('punctuality', ['python3', 'work/punctuality.py'], 'punctuality.csv/.md', []),
        ('triangles', ['python3', 'work/triangle_report.py'], 'triangle_routes.md', []),
        ('gaps', ['python3', 'work/date_coverage.py'], 'date_coverage.md', []),
        ('gap_report', ['python3', 'work/report_gaps.py'], 'data_gaps.md', []),
        ('no_code', ['python3', 'work/no_code_tracks.py'], 'no_code_tracks.md', []),
        ('delays', ['python3', 'work/schedule_delays.py'], 'schedule_delays.csv/.md', ['work/screens_20260930_rows.csv']),
        ('missing', ['python3', 'work/missing_flights.py'], 'missing_flights.md', []),
        ('publish', ['python3', 'work/publish_layers.py'], 'copy the layers into the month folder', []),
    ):
        if name in a.skip or (name == 'weather' and 'weather' in a.skip) or (name == 'metar' and 'weather' in a.skip):
            steps.append((name, cmd, 'skipped by --skip'))
            continue
        missing = [n for n in needs if not os.path.exists(os.path.join(ROOT, n))]
        if missing:
            steps.append((name, cmd, 'SKIPPED, needs ' + ', '.join(missing)))
            continue
        steps.append((name, cmd, why))

    print('\nsteps')
    for name, cmd, why in steps:
        print(f'  {name:<14} {" ".join(cmd[1:]):<62} {why}')
    if a.plan:
        return 0

    n, ym = unbundle()
    snap = tracked()          # mtimes to compare against once the steps have run
    print(f'\nunbundled {n} tables from {os.path.basename(ym or "")} to the checkout root')

    done, failed, skipped, warned = [], [], [], []
    SOFT = {'missing', 'gaps', 'gap_report', 'no_code', 'triangles', 'runway_report'}
    for name, cmd, why in steps:
        if why.startswith('skipped by') or why.startswith('SKIPPED'):
            print(f'--  {name}: {why}')
            skipped.append(name)
            continue
        print(f'->  {name}: {" ".join(cmd[1:])}')
        try:
            ok, tail = sh(cmd)
        except Exception as e:                                   # noqa: BLE001
            ok, tail = False, f'{type(e).__name__}: {e}'
        print(('    ok' if ok else '    FAILED') + (('\n    ' + tail.replace('\n', '\n    ')) if (tail and not ok) else ''))
        # A prose report is allowed to break: its output is a .md nobody computes from, and one
        # stale stub in a month folder once turned the whole nightly build red and stopped commits.
        if not ok and name in SOFT:
            print('    warned (soft step, the build continues):\n    ' + tail.replace('\n', '\n    '))
            warned.append(name)
            continue
        (done if ok else failed).append(name)
    # a re-publish after the reports, since the reports write at the root
    if 'publish' not in done + skipped:
        sh(['python3', 'work/publish_layers.py'])

    stale = ''
    if fix:
        cap = screenshot_latest()
        if cap:
            lag = (fix.date() - dt.date(int(cap[:4]), int(cap[4:6]), int(cap[6:]))).days
            if lag > a.stale_days:
                stale = (f'human captures are {lag} days behind the data (newest capture {cap}, '
                         f'newest fix {fix.date()}) — app flags and timetable delays are copied forward')
        else:
            stale = 'no screenshot inputs in this checkout: app flags and delays are whatever the last build published'
    after = tracked()
    changed = sorted(r for r, m in after.items() if m > snap.get(r, 0))
    if a.changed_file:
        with open(a.changed_file, 'w') as fh:
            fh.write('\n'.join(changed) + ('\n' if changed else ''))
    print(f'\nran {len(done)}, failed {len(failed)}, warned {len(warned)}, skipped {len(skipped)} '
          f'· {len(changed)} published file(s) touched')
    if stale:
        print('::warning::' + stale)
    with open(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null'), 'a', encoding='utf-8') as fh:
        fh.write(f'### FR24 build {today:%Y-%m-%d %H:%M}Z\n\n')
        fh.write(f'- archive newest fix **{fix.date() if fix else "?"}**, month folder `{os.path.basename(ym or "?")}`\n')
        fh.write(f'- steps ok {len(done)}: {", ".join(done) or "-"}\n')
        if warned:
            fh.write(f'- reported on but soft-failed {len(warned)}: {", ".join(warned)}\n')
        if failed:
            fh.write(f'- **failed {len(failed)}**: {", ".join(failed)}\n')
        if skipped:
            fh.write(f'- skipped {len(skipped)}: {", ".join(skipped)}\n')
        fh.write(f'- published files touched: {len(changed)}\n')
        if stale:
            fh.write(f'- :warning: {stale}\n')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
