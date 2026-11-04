#!/usr/bin/env python3
"""Carry the cumulative tables into a month folder that has only just been created.

The first run that finds data in a new month creates `UR NOVEMBER 2026/` with the four files the
build owns (`flights.csv`, `manifest.csv`, the log, `all_flights_aeroroutes.md`). Everything else in
a month folder — `tails.csv`, `app_status.csv`, the runway tables, `fleet_summary.csv`, the triangle
tables — is cumulative: one table spanning months, published per folder. A brand-new folder has none
of them, and the readers assume they are there: `work/date_coverage.py` opened `{live}/tails.csv` and
the whole build died on FileNotFoundError the first night November began.

So copy them forward, and say so. This is a starting point, not a rebuild: the analysis steps then
rewrite these files against the archive as it now stands, exactly as they do for the live month.

Exit status is 0 even when nothing was copied, because "the folder is already seeded" is the normal
answer.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work'))
from repo_layout import PUBLISH, month_dirs                     # noqa: E402

# the tables one month's folder shares with the next; keep in step with publish_layers.CUMULATIVE
CUMULATIVE = ('tails.csv', 'app_status.csv', 'runway_usage.csv', 'runway_usage.md',
              'no_code_tracks.csv', 'no_code_tracks.md', 'fleet_summary.csv',
              'triangle_assignments.csv', 'flight_conditions.csv')


def main():
    dirs = month_dirs(PUBLISH)
    if len(dirs) < 2:
        print('only one month folder on the branch; nothing to carry forward')
        return 0
    live, prev = dirs[-1], dirs[-2]
    os.makedirs(live['path'], exist_ok=True)
    moved = []
    for f in CUMULATIVE:
        src, dst = os.path.join(prev['path'], f), os.path.join(live['path'], f)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copyfile(src, dst)
                moved.append(f)
            except OSError as e:
                print(f'  ! {f}: {e}')
    print(f'seeded {live["name"]} from {prev["name"]}: '
          + (', '.join(moved) if moved else 'already had every cumulative table'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
