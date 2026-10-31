#!/usr/bin/env python3
"""Where the airport table comes from, so a thinned workspace still rebuilds every report.

`work/rwy/airports.csv` is the raw OurAirports dump (12 MB, public domain / Unlicense) and is the
full answer for every airport on earth.  `fr24_publish/reference/airports.csv` is the published
subset — every airport these tracks touch plus the log's network — with the same column names,
because `work/make_reference.py` writes it out of the raw file.  The reports below only ever ask
about airports in this operation, so either file answers them identically, and the raw dump can be
removed to save space without making the tree unrebuildable.

Re-download it if a report ever needs an airport the reference subset does not hold:
[ourairports.com/data](https://ourairports.com/data/) — `airports.csv.gz` in the
`databases.mourairports.com/v<date>/` bundle — unpacked to `work/rwy/airports.csv`.
"""
import csv
import os

RAW = 'work/rwy/airports.csv'
REF = 'fr24_publish/reference/airports.csv'


def path(root=None):
    """The airport table to read: the raw dump when it is here, else the published subset."""
    for p in (RAW, REF):
        if os.path.exists(p if root is None else os.path.join(root, p)):
            return p
    raise SystemExit(f'no airport table: neither {RAW} nor {REF} exists — re-download the '
                     f'public-domain dump from https://ourairports.com/data/ into {RAW}')


def rows(root=None):
    return csv.DictReader(open(path(root)))


if __name__ == '__main__':
    p = path()
    n = sum(1 for _ in csv.DictReader(open(p)))
    print(f'{p}: {n} airports' + ('' if p == RAW else '  (published subset; the raw dump is absent)'))
