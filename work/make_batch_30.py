#!/usr/bin/env python3
"""Turn the checked 30 September rows into the batch the build reads, and record
the few rows that cannot be a flight.

work/final.py merges every csv in work/screens_extra/ as (tail,date,flight,origin,dest)
records, so the batch is written in exactly that shape.  Rows that carry a date, a
flight number, an origin and a destination go in — including the Hoima legs, whose
tail is *only* ever going to come from the app pages, because the archive's own
records for them are the airline's AF523 callsign and never reach the flight log.

Rows the app shows without a flight number cannot be joined to anything, so they are
excluded here and written out to work/shots30/non_flight_rows.md instead: dropping
them silently would hide that the app carries a row labelled TEST.

    python3 work/make_batch_30.py
"""
import csv
import collections

SRC = 'work/screens_20260930_rows.csv'
OUT = 'work/screens_extra/batch_2026-09-30.csv'
NOTES = 'work/shots30/non_flight_rows.md'


def main():
    rows = list(csv.DictReader(open(SRC)))
    keep, partial, noflight = [], [], []
    for r in rows:
        if not all([r['date'], r['flight'], r['origin'], r['dest']]):
            (noflight if r['date'] and not r['flight'] else partial).append(r)
            continue
        keep.append(dict(tail=r['tail'], date=r['date'], flight=r['flight'],
                         origin=r['origin'], dest=r['dest']))

    # the same leg can appear on two pages of one aircraft (the captures overlap);
    # keep one row per leg, first occurrence wins
    seen, out = set(), []
    for r in keep:
        k = (r['tail'], r['date'], r['flight'], r['origin'], r['dest'])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    dupes = len(keep) - len(out)

    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['tail', 'date', 'flight', 'origin', 'dest'])
        w.writeheader()
        w.writerows(out)

    with open(NOTES, 'w') as fh:
        fh.write('# 30 September captures — rows that are not flights\n\n')
        fh.write(f'From `work/screens_20260930_rows.csv`, written by '
                 f'`work/make_batch_30.py`.\n\n')
        fh.write('## No flight number in the app\n\n')
        fh.write('| capture | slot | tail | date | origin | dest | dot | what the page shows |\n')
        fh.write('|---|---|---|---|---|---|---|---|\n')
        for r in noflight:
            fh.write(f"| {r['image'][-22:-4]} | {r['slot']} | {r['tail']} | {r['date']} | "
                     f"{r['origin']} | {r['dest']} | {r['dot']} | "
                     f"`{(r['raw'] or '').split('||')[0].strip()[:60]}` |\n")
        fh.write('\n## Row left incomplete by the capture\n\n')
        for r in partial:
            fh.write(f"- {r['image'][-22:-4]} slot {r['slot']} ({r['tail']}): "
                     f"{r['date'] or 'no date'} {r['flight'] or 'no flight'} — the row is cut "
                     f"off at the foot of the capture, so it carries no route; the archive "
                     f"has the leg.\n")
        fh.write('\n## Header and photograph block\n\n')
        fh.write('The slots above the first flight row hold the aircraft photograph and its\n'
                 'specification block; they are not flights and are excluded by\n'
                 '`work/page_meta_30.py`. The block itself is kept in\n'
                 '`work/shots30/airframes.csv`.\n')

    per = collections.Counter(r['tail'] for r in out)
    print(f'wrote {OUT}: {len(out)} rows ({dupes} repeated rows dropped)')
    print(f'  per tail: {dict(per)}')
    print(f'  dates: {min(r["date"] for r in out)} .. {max(r["date"] for r in out)}')
    print(f'wrote {NOTES}: {len(noflight)} rows with no flight number, '
          f'{len(partial)} partial row(s)')


if __name__ == '__main__':
    main()
