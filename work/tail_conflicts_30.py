#!/usr/bin/env python3
"""Tail conflicts between the 30 September captures and the already-built tails.csv.

The captures are later than everything folded so far, so on the standing rule the
later capture wins.  That rule is only safe if the disagreements are small and
explicable, so this prints every leg where the two sources name a *different*
aircraft, both ways round, and counts them per tail.  Nothing is written: the point
is the tally, and the rows that need a human read.

    python3 work/tail_conflicts_30.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout as RL
import collections
import csv
import re

P = RL.live_dir()          # this month's folder inside fr24_publish/
ROWS = 'work/screens_20260930_rows.csv'
MONN = {m: i for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                                    'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}


def iso(s):
    return f"20{s[5:7]}-{MONN[s[2:5]]:02d}-{s[:2]}"


def dig(s):
    return re.sub(r'\D', '', s or '')


def main():
    new = collections.defaultdict(list)
    for r in csv.DictReader(open(ROWS)):
        if r['date'] and r['flight'] and r['origin'] and r['dest']:
            new[(r['date'], dig(r['flight']), r['origin'], r['dest'])].append(r['tail'])

    old = collections.defaultdict(set)
    for r in csv.DictReader(open(f'{P}/tails.csv')):
        k = (r['track_date'] or r['date'], dig(r['flight']), r['origin'], r['dest'])
        old[k].add(r['tail'])

    agree = collections.Counter()
    clash = []
    for k, tails in new.items():
        if k not in old:
            continue
        for t in set(tails):
            if t in old[k]:
                agree[t] += 1
            else:
                clash.append((k, t, sorted(old[k])))

    print(f'legs named by both sources      : '
          f'{sum(1 for k in new if k in old)}')
    print('agreeing rows per tail (new vs existing tails.csv):')
    for t, n in agree.most_common():
        print(f'   {t:8s} {n}')
    print(f'\ndisagreeing rows: {len(clash)}')
    seen = collections.Counter()
    for (d, fl, o, de), t, olds in sorted(clash):
        seen[(t, tuple(olds))] += 1
    for (t, olds), n in seen.most_common():
        print(f'   new {t:8s} vs existing {olds}   x{n}')
    print('\nfirst 40 in detail:')
    for (d, fl, o, de), t, olds in sorted(clash)[:40]:
        print(f'   {d} UR{fl:4s} {o}-{de:4s}  new={t:8s} old={",".join(olds)}')


if __name__ == '__main__':
    main()
