#!/usr/bin/env python3
"""Which month does this build describe?  One answer, shared by the report scripts.

The published log is the authority: `fr24_update.py` rebuilds `flights.csv` for a single
month, so the latest departure month in that file *is* the month every report below should
cover.  Reading it here rather than typing `2026-09` into each script is what stops a
report from carrying a month name that was simply true when the script was written — the
failure mode that would have published September's weather table as October's.

Back-fill a different month with `FR24_MONTH=2026-08 python3 work/<report>.py`.

    from month_ctx import ctx
    C = ctx()
    days = [d for d in all_days if C['first'] <= d <= C['last']]
    w(f'# {C["name"]} coverage\\n')
"""
import argparse
import collections
import csv
import datetime as dt
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys
_sys.path.insert(0, _HERE)   # repo_layout lives beside this file
import repo_layout as RL     # noqa: E402  (same tree, two ends of it)

P = os.environ.get('FR24_PUBLISH', '/home/user/fr24_publish')

MON = {m: i for i, m in enumerate(
    ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}
NUM = {v: k for k, v in MON.items()}
NAME = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December']
SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
         'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def iso_date(s):
    """01SEP26 -> 2026-09-01.  The log writes `date_local` as DDMMMYY; anything
    already ISO, or empty, passes through unchanged."""
    s = (s or '').strip()
    if len(s) == 7 and s[2:5].isalpha():
        try:
            return f"20{s[5:7]}-{MON[s[2:5].upper()]:02d}-{s[:2]}"
        except KeyError:
            return s
    return s


def logs_found(pub=None):
    """Every `flights.csv` the build may have written: the flat one (pre-month-folder
    layout) and one inside each month folder, however that is named."""
    pub = pub or P
    found = [os.path.join(pub, 'flights.csv')]
    try:
        names = sorted(os.listdir(pub))
    except OSError:
        return found
    for n in names:
        d = os.path.join(pub, n)
        if os.path.isdir(d) and RL.ym_of_folder(n + '/') and os.path.exists(os.path.join(d, 'flights.csv')):
            found.append(os.path.join(d, 'flights.csv'))
    return [f for f in found if os.path.exists(f)]


def _month_counts(path):
    c = collections.Counter()
    with open(path, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            d = iso_date(r.get('date_local') or r.get('date') or '')
            if len(d) == 10:
                c[d[:7]] += 1
    return c


def months_in_log(pub=None):
    """{YYYY-MM: flights} across the published logs.  A month counted in more than one
    log — a leftover flat file and the month folder's copy — keeps the larger count, not
    the sum, so seeing the same flights twice cannot invent flights."""
    best = {}
    for path in logs_found(pub):
        for k, v in _month_counts(path).items():
            best[k] = max(best.get(k, 0), v)
    return collections.Counter(best)


def log_rows(pub=None):
    """The published log for the build month, as dicts.  A missing month folder means the
    build has not run for that month yet: say that, instead of raising FileNotFoundError a
    few lines into a script nobody reads on the day it matters."""
    p = os.path.join(pub or RL.live_dir(), 'flights.csv')
    if not os.path.exists(p):
        raise SystemExit(f'no published log at {p}\n'
                         f'  build the month first:  python3 fr24_update.py --zip "incoming/<export>.zip"')
    with open(p, newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def log_source(ym, pub=None):
    """Name the published log that holds this month, relative to the workspace, so a
    report can say where its month came from instead of assuming a flat file."""
    for path in logs_found(pub):
        if _month_counts(path).get(ym):
            return os.path.relpath(path, RL.ROOT)
    return "no published log"


def ctx(pub=None):
    """Everything a report needs to talk about one calendar month."""
    ym = os.environ.get('FR24_MONTH')
    src = 'FR24_MONTH'
    if not ym:
        m = months_in_log(pub).most_common()
        m = [k for k, _ in m if k]
        ym = max(m) if m else None
        src = log_source(ym, pub) if ym else "no published log"
    if not ym:
        ym = dt.date.today().strftime('%Y-%m')
        src = 'today (no log published yet)'
    y, mo = int(ym[:4]), int(ym[5:7])
    first = dt.date(y, mo, 1)
    nxt = dt.date(y + (mo == 12), mo % 12 + 1, 1)
    last = nxt - dt.timedelta(days=1)
    prev_first = first - dt.timedelta(days=first.day)
    return {
        'ym': ym, 'src': src,
        'year': y, 'm': mo,
        'first': first.isoformat(), 'last': last.isoformat(),
        'n_days': last.day,
        'name': NAME[mo - 1], 'short': SHORT[mo - 1], 'mon': NUM[mo],
        'label': f'{NAME[mo - 1]} {y}',
        'prev_ym': prev_first.isoformat()[:7],
        'prev_name': NAME[prev_first.month - 1],
        'prev_last': (first - dt.timedelta(days=1)).isoformat(),
    }


def inside(d, c=None):
    """Is this ISO date inside the build month?"""
    c = c or ctx()
    return bool(d) and c['first'] <= d <= c['last']


def dlabel(d):
    """2026-09-05 -> 5 Sep"""
    return f'{int(d[8:10])} {SHORT[int(d[5:7]) - 1]}'


def add_month_arg(ap, help_='month to report, YYYY-MM (default: the published build month)'):
    ap.add_argument('--month', help=help_)
    return ap


def resolve(argv=None):
    """For scripts that take a --month flag: env, then flag, then the published log."""
    ap = add_month_arg(argparse.ArgumentParser(add_help=False))
    a, rest = ap.parse_known_args(argv)
    if a.month:
        os.environ['FR24_MONTH'] = a.month
    return ctx(), rest


if __name__ == '__main__':
    c = ctx()
    print(f"build month {c['ym']}  ·  {c['first']} .. {c['last']}  ({c['n_days']} days)"
          f"  ·  from {c['src']}")
    for k, v in months_in_log().most_common():
        print(f'  {k}: {v} logged flights')
