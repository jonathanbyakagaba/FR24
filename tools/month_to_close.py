#!/usr/bin/env python3
"""Print the finished month that is still open on the branch, or nothing.

The point of this is that nobody has to remember. A month is closed once its `.closed` marker
exists, and `work/close_month.py` is what writes it; until now that only happened when a person put
`2026-10` into a box on the Actions page, and October sat open for 3 days after it ended.

A month counts as finished when it is older than this month AND it is not the live month of the
archive — the live one is what the build is still writing into. So a run that captured nothing does
not freeze October out of impatience; the run that lands November data closes it on its own.

Exit status is always 0: "nothing to close" is the normal answer, not a failure.
"""
import os
import sys
import datetime as dt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work'))
from repo_layout import live_dir, month_dirs, ym_of_folder   # noqa: E402


def basename_ym(path):
    return ym_of_folder(os.path.basename((path or '').rstrip('/')) + '/')


def main():
    argv = sys.argv[1:]
    live = argv[argv.index('--live') + 1] if '--live' in argv else basename_ym(live_dir())
    this = dt.date.today().strftime('%Y-%m')
    for m in month_dirs():                       # sorted oldest first
        ym = m['ym']
        if m['closed'] or ym >= this or ym == live:
            continue
        print(ym)
        return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
