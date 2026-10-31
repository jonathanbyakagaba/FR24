#!/usr/bin/env python3
"""Can any aircraft be in two places at once?

Each leg now carries the tail the app's own page gave it.  The log carries each leg's
departure and arrival in UTC.  Put the two together and the assignments can be tested
against the physical constraint that one airframe flies one leg at a time: two legs
of the same tail overlapping in time mean one of the two is misassigned.

The archive works on UTC days while the app lists local days, so legs are placed by
their UTC departure and closing time, and a small overlap is tolerated (the times are
wheels-up/wheels-down from the tracks, and a quick turnaround can look like a overlap
if a track's end is under-reported).

    python3 work/tail_overlaps_30.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout as RL
import collections
import csv
import datetime as dt

P = RL.live_dir()          # this month's folder inside fr24_publish/
TOLERANCE_MIN = 20


def stamp(s):
    return dt.datetime.strptime(s[:16], '%Y-%m-%d %H:%M') if s else None


def main():
    def tod(iso):                       # 2026-09-18 -> 18SEP26, as the log writes it
        d = dt.date.fromisoformat(iso)
        return f'{d.day:02d}{d.strftime("%b").upper()}{d.strftime("%y")}'

    log = collections.defaultdict(list)
    for r in csv.DictReader(open(f'{P}/flights.csv')):
        log[(r['date_local'], r['flight'].lstrip('UGD'), r['origin'], r['dest'])].append(r)

    per_tail = collections.defaultdict(list)
    unattached = 0
    for r in csv.DictReader(open(f'{P}/tails.csv')):
        if r['verified_track'] != 'Y':
            continue
        legs = (log.get((tod(r['track_date'] or r['date']), r['flight'].lstrip('UR'),
                         r['origin'], r['dest']))
                or log.get((tod(r['date']), r['flight'].lstrip('UR'),
                            r['origin'], r['dest'])))
        if not legs:
            unattached += 1
            continue
        if len(legs) > 1:
            # two legs of one flight number on one local day (a red-eye and its
            # evening repeat both land on the earlier date): the app row can name
            # either, so this is a key collision, not a second aircraft
            per_tail[r['tail']].extend((stamp(l['departure_utc']), stamp(l['arrival_utc']), l)
                                       for l in legs if l['departure_utc'])
            continue
        leg = legs[0]
        d0, d1 = stamp(leg['departure_utc']), stamp(leg['arrival_utc'])
        if not d0 or not d1:
            continue
        per_tail[r['tail']].append((d0, d1, leg))

    # one app row can attach both rotations of a flight number that repeats within a
    # local day (the red-eye and its evening repeat), and two app rows of the same leg
    # attach them both: keep each distinct log leg once per tail
    for tail in per_tail:
        seen, keep = set(), []
        for d0, d1, leg in sorted(per_tail[tail], key=lambda z: (z[0], z[1])):
            k = (leg['source_file'], leg['date_local'], leg['flight'])
            if k not in seen:
                seen.add(k)
                keep.append((d0, d1, leg))
        per_tail[tail] = keep

    print(f'{sum(len(v) for v in per_tail.values())} verified legs carry times '
          f'({unattached} without a matching log row)')
    clashes = 0
    for tail, legs in sorted(per_tail.items()):
        legs.sort(key=lambda z: (z[0], z[1]))
        for (a0, a1, la), (b0, b1, lb) in zip(legs, legs[1:]):
            gap = (b0 - a1).total_seconds() / 60.0
            if la['flight'] == lb['flight'] and la['date_local'] == lb['date_local']:
                continue          # the same flight number twice in one day
            if gap < -TOLERANCE_MIN:
                clashes += 1
                print(f'  {tail}  {la["date_local"]} {la["flight"]} '
                      f'{la["origin"]}-{la["dest"]} ends {a1:%d %H:%M}Z  overlaps  '
                      f'{lb["date_local"]} {lb["flight"]} {lb["origin"]}-{lb["dest"]} '
                      f'from {b0:%d %H:%M}Z  ({gap:+.0f} min)')
    print(f'\noverlapping legs beyond {TOLERANCE_MIN} min: {clashes}')

    turn = collections.defaultdict(list)
    n_turn_skip = 0
    for tail, legs in per_tail.items():
        legs.sort(key=lambda z: (z[0], z[1]))
        for (a0, a1, la), (b0, _, lb) in zip(legs, legs[1:]):
            if la['flight'] == lb['flight'] and la['date_local'] == lb['date_local']:
                n_turn_skip += 1      # a flight number twice in one local day is not a turnaround
                continue
            turn[tail].append((b0 - a1).total_seconds() / 60.0)
    print('\nturnaround between consecutive legs (minutes):')
    for tail, gs in sorted(turn.items()):
        gs.sort()
        print(f'  {tail:8s} n={len(gs):3d}  median {gs[len(gs)//2]:6.0f}  '
              f'min {gs[0]:6.0f}  max {gs[-1]:6.0f}')
    print(f'  ({n_turn_skip} consecutive pairs left out: the same flight number twice in one local day)')


if __name__ == '__main__':
    main()
