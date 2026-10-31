#!/usr/bin/env python3
"""Exactly which flights are missing, as one table per month.

Everything is read from the published tree, so the list is reproducible by anyone holding the
repository: each month folder's `date_coverage.md` (app-confirmed gaps, rotation holes,
pending-at-cut, tracked-but-unlogged, and the app rows that are *not* missing flights), the month
`flights.csv`, `tails.csv` for the per-tail claims, `manifest.csv` for where the archive stops,
`schedule_delays.csv` for what the timetable said and when the app capture stopped talking, and
`work/schedule/schedule_<month>.csv` where a timetable is published.

Two windows are kept apart, because conflating them is how a report over-counts:

  * the **archive** ends at its last fix (per month, from `manifest.csv`);
  * the app's **status capture** ends earlier still — the newest timestamp its status strings
    carry.  A leg due after that says `Scheduled` whatever actually happened, so it cannot be
    used as evidence in either direction.

    python3 work/missing_flights.py        # writes missing_flights.md at the workspace root
"""
import csv
import datetime as dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
FULL = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December']
NUM = {m: i for i, m in enumerate(
    'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split(), 1)}


def folder(ym):
    """The month folder as the repository names it: `UR SEPTEMBER 2026`."""
    y, mo = ym.split('-')
    return f'fr24_publish/UR {FULL[int(mo) - 1].upper()} {y}'


def dlabel(iso_s):
    return f'{int(iso_s[8:10])} {SHORT[int(iso_s[5:7]) - 1]}'


def day_to_iso(label, ym):
    """'15 Sep' (as the report labels a day) or '2026-09-15' -> ISO"""
    m = re.match(r'^(\d{1,2})\s+(\w{3})$', (label or '').strip())
    if not m:
        return label
    return f'{ym[:4]}-{NUM[m.group(2).upper()]:02d}-{int(m.group(1)):02d}'


def _utc(s):
    """'2026-10-05 02:23:07Z' / '2026-10-05 02:30Z' -> naive UTC datetime, or None"""
    s = (s or '').strip().rstrip('Z').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def parse_report(ym):
    """The categories the coverage report keeps apart, keyed by ISO date."""
    txt = open(f'{folder(ym)}/date_coverage.md').read()
    body = txt.split('## The unfinished dates')[1].split('## The triangle')[0]
    out = {'app': [], 'hole': [], 'pend': [], 'notlogged': [], 'chain': []}
    day = mode = None
    for line in body.splitlines():
        m = re.match(r'^### (\d\d \w\w\w) ', line)
        if m:
            day, mode = day_to_iso(m.group(1), ym), None
            continue
        if day is None:
            continue
        pats = (('**Missing, app-confirmed**', 'app'), ('**Rotation holes**', 'hole'),
                ('**Pending at the export cut**', 'pend'),
                ('**Tracked, but not in the log**', 'notlogged'),
                ('**App rows that are not missing flights**', 'chain'))
        hit = next((k for pat, k in pats if line.startswith(pat)), None)
        if hit:
            mode = hit
            continue
        # blank lines sit between a category's heading and its rows, so they must not clear
        # `mode` — only a new `### date` header does that
        if not (line.startswith('|') or line.startswith('*')):
            continue
        if mode == 'app':
            g = re.match(r'^\| (UR\d+\w*) \| (\S+) \| ([A-Z0-9\-]+)–([A-Z0-9\-]+) \| (\w+) \|', line)
            if g:
                out['app'].append((day, g.group(1), g.group(2), f'{g.group(3)}–{g.group(4)}',
                                   g.group(5)))
        elif mode == 'hole':
            g = re.match(r'^\* \*\*(UGD\d+\w*)\*\* — missing ([A-Z0-9\-]+)–([A-Z0-9\-]+) '
                         r'\(the export holds ([^)]+)\)', line)
            if g:
                out['hole'].append((day, g.group(1), f'{g.group(2)}–{g.group(3)}', g.group(4).strip()))
        elif mode == 'pend':
            g = re.match(r'^\* \*\*(UGD\d+\w*)\*\* — (.+?) still to fly \(the export holds '
                         r'([^)]*)\)', line)
            if g:
                out['pend'].append((day, g.group(1), g.group(2).strip(), g.group(3).strip()))
        elif mode in ('notlogged', 'chain'):
            g = re.match(r'^\| (UR\d+\w*) \| (\S+) \| ([A-Z0-9\-]+)–([A-Z0-9\-]+) \|', line)
            if g:
                who = line.rstrip().rstrip('|').split('|')[-1].strip()
                out[mode].append((day, g.group(1), g.group(2), f'{g.group(3)}–{g.group(4)}', who))
    return out


def unlogged_from_tails(ym):
    """The log-gate category, straight from the claims table: complete even on days the report
    files as closed, so no section for that day exists to parse."""
    return [r for r in csv.DictReader(open('tails.csv'))
            if not r['verified_track'] and r['date'].startswith(ym)]


def report_unlogged_count(ym):
    txt = open(f'{folder(ym)}/date_coverage.md').read()
    m = re.search(r'\*\*(\d+) legs\s*\n?\s*this month\*\* sit in that category', txt)
    return int(m.group(1)) if m else 0


def last_fix(ym):
    """The archive's newest fix, as a naive UTC datetime, from the month's own manifest."""
    rows = list(csv.DictReader(open(f'{folder(ym)}/manifest.csv')))
    s = max((r['last_utc'] for r in rows if r['last_utc']), default='')
    return _utc(s)


def capture_end(ym):
    """The newest moment the app's own status strings name, from the published join.

    `schedule_delays.csv` carries `actual_utc` only where the capture said something with a time
    in it (`Landed 22:10`, `Estimated departure 18:35`), so its maximum is where the capture stops
    talking: every leg due after that reads `Scheduled` whatever happened, and that word is not
    evidence of anything."""
    p = f'{folder(ym)}/schedule_delays.csv'
    if not os.path.exists(p):
        return None, p
    seen = [_utc(r['actual_utc']) for r in csv.DictReader(open(p))
            if r['actual_utc'] and r['basis'] in ('actual', 'estimate')]
    seen = [x for x in seen if x]
    return (max(seen) if seen else None), p


def all_log_legs(months):
    """Every leg in every published month log: [flight, sector, origin, dest, date, gate, claimed]

    All logs are read, not just the build month's: the layers are cumulative, so a question like
    "is this in the log?" has to be asked of the whole published set, and a leg can also sit on the
    other side of a month boundary.  `gate` keeps the `take-off not observed` flag, which is how a
    leg whose track begins in the cruise is identified below."""
    out = []
    for ym in months:
        p = f'{folder(ym)}/flights.csv'
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            d = _iso_compact(r['date_local'])
            out.append([r['flight'].replace('UGD', 'UR'), f"{r['origin']}–{r['dest']}",
                        r['origin'], r['dest'], d, r.get('takeoff_not_observed', '').strip(), False])
    return out


def _iso_compact(d):
    """`29SEP26` (how `flights.csv` stamps a day) -> '2026-09-29'; ISO passes through."""
    m = re.match(r'^(\d{2})([A-Za-z]{3})(\d{2})$', (d or '').strip())
    if not m:
        return d
    return f'20{m.group(3)}-{NUM[m.group(2).upper()]:02d}-{m.group(1)}'


def match_schedule(months):
    """Claim each schedule row against the log, same day first, then a neighbouring day.

    Three ways a schedule row is satisfied, in this order:

    * **same day, same sector** — the ordinary case;
    * **same day, same destination, `take-off not observed`** — a track that starts in the cruise
      has an inferred origin, so `UR711 JNB→EBB` is logged as `KGL→EBB`.  That is the flight, not a
      gap, and the row is kept for the report as a `partial` so the wording can say so;
    * **a neighbouring day** — the log files a leg by *local* time, so a 22:30Z departure off
      Entebbe belongs to the next date.  Only an unclaimed leg may explain a row, so a genuinely
      missing hop cannot be talked away by the same flight number flying the day before or after.
    """
    legs = all_log_legs(months)
    by_flight_date = {}
    for i, L in enumerate(legs):
        by_flight_date.setdefault((L[0], L[4]), []).append(i)
    by_key = {}
    for i, L in enumerate(legs):
        by_key.setdefault((L[0], L[1]), []).append(i)
    sched = []
    for ym in months:
        p = f'work/schedule/schedule_{ym}.csv'
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            sched.append((ym, r['date_local_dep'], (r['flight'], f"{r['from']}–{r['to']}"),
                          r['from'], r['to'], r))
    claimed, partial, unresolved = {}, {}, []
    for ym, d, k, frm, to, r in sorted(sched, key=lambda x: (x[1], x[2])):
        hit = next((i for i in by_key.get(k, ()) if legs[i][4] == d and not legs[i][6]), None)
        if hit is None:
            # an inferred-origin leg that still ends where this one was due
            hit = next((i for i in by_flight_date.get((k[0], d), ())
                        if not legs[i][6] and legs[i][3] == to and legs[i][2] != frm
                        and legs[i][5] == 'Y'), None)
            if hit is not None:
                legs[hit][6] = True
                partial[(k, d)] = legs[hit]
                continue
            unresolved.append((ym, d, k, r))
            continue
        legs[hit][6] = True
        claimed[(k, d)] = legs[hit]
    folds = {}
    for ym, d, k, r in unresolved:
        try:
            want = dt.date.fromisoformat(d)
        except ValueError:
            continue
        cand = []
        for i in by_key.get(k, ()):
            if legs[i][6]:
                continue
            try:
                near = abs((dt.date.fromisoformat(legs[i][4]) - want).days)
            except ValueError:
                continue
            if near <= 1:
                cand.append((near, i))
        if cand:
            _, i = min(cand)
            legs[i][6] = True
            folds[(k, d)] = legs[i]
    return claimed, folds, partial


def scheduled_without_track(ym, hole_keys, pend_keys, months):
    """Timetable legs the archive should have covered and does not, minus the holes and pending
    rows the coverage report already counts.  Returns ([], [], reason) with no timetable.

    A leg is only *expected* when its scheduled arrival precedes the archive's last fix; the rest
    are counted separately, because they are not downloaded rather than missing.  Legs the log
    holds on a neighbouring day come back flagged as folds, not as gaps."""
    p = f'work/schedule/schedule_{ym}.csv'
    if not os.path.exists(p):
        return [], [], [], f'{p} (none published)'
    cut = last_fix(ym)
    jpath = f'{folder(ym)}/schedule_delays.csv'
    joined = {}
    if os.path.exists(jpath):
        joined = {(r['flight'], r['date'], f"{r['from_']}–{r['to']}"): r
                  for r in csv.DictReader(open(jpath))}
    claimed, folds, partial = match_schedule(months)
    gap, later, folded = [], [], []
    for r in csv.DictReader(open(p)):
        d = r['date_local_dep']
        k = (r['flight'], f"{r['from']}–{r['to']}")
        j = joined.get((r['flight'], d, f"{r['from']}–{r['to']}"))
        arr = _utc(j['sched_arr_utc']) if j else None
        if arr is None:      # no joined row: fall back on the local date against the cut day
            arr = _utc(f'{d} 23:59')
        if (k, d) in claimed:
            continue
        if (k, d) in partial:
            folded.append((d, r, partial[(k, d)], 'partial'))
            continue
        if (k[0], d, k[1]) in hole_keys or (k[0], d, k[1]) in pend_keys:
            continue
        if arr > cut:
            later.append((d, r))
            continue
        if (k, d) in folds:
            folded.append((d, r, folds[(k, d)], 'fold'))
            continue
        gap.append((d, r, j or {}))
    return gap, later, folded, None


def main():
    months = sys.argv[1:] or sorted({f'2026-{m:02d}' for m in (9, 10)})
    n_tracks = sum(1 for _ in open(f'{folder(months[-1])}/manifest.csv')) - 1
    cut = last_fix(months[-1])
    L = ['# Exactly which flights are missing',
         '',
         f'One row = one sector, not one aircraft.  Built from the published tree on an archive of '
         f'**{n_tracks:,} track files** (`FR data.zip`) whose last fix is '
         f'**{cut:%Y-%m-%d %H:%M}Z**: each month\'s `date_coverage.md` and `flights.csv`, the '
         'per-tail app pages (`tails.csv`), and the timetable where one is published.  '
         '`python3 work/missing_flights.py` regenerates it.',
         '']
    for ym in months:
        mcut = last_fix(ym)
        R = parse_report(ym)
        hole_keys = {(f'UR{f[3:]}', d, s) for d, f, s, _ in R['hole']}
        # a pending bullet can name both legs of the rotation ("LUN–HRE, HRE–EBB"), so the
        # timetable comparison has to match it sector by sector
        pend_keys = {(f'UR{f[3:]}', d, x.strip()) for d, f, s, _ in R['pend'] for x in s.split(',')
                     if '–' in x}
        n_unlogged = report_unlogged_count(ym) or len(
            [r for r in unlogged_from_tails(ym) if r['flight'] == 'UR523'])
        L.append(f'## {FULL[int(ym[5:7]) - 1]} {ym[:4]} — {len(R["app"])} app-confirmed '
                 f'legs · {len(R["hole"])} rotation holes · {n_unlogged} '
                 'tracked-but-unlogged')
        L.append('')
        L.append('| # | date | flight | sector | why we know it is missing | what the export holds |')
        L.append('|---|---|---|---|---|---|')
        i = 0
        for d, f, tail, s, col in R['app']:
            i += 1
            extra = next((h for dd, ff, ss, h in R['hole']
                           if dd == d and f'UR{ff[3:]}' == f and ss == s), None)
            ev = f'the app page for {tail} lists the leg ({col} dot)'
            if extra:
                ev += ' — **and** it is a hole in a rotation that closed'
            L.append(f'| {i} | {dlabel(d)} | {f} | {s} | {ev} | {extra or "nothing"} |')
        for d, f, s, hold in R['hole']:
            if (d, f'UR{f[3:]}', s) in {(a[0], a[1], a[3]) for a in R['app']}:
                continue
            i += 1
            L.append(f'| {i} | {dlabel(d)} | {f.replace("UGD", "UR")} | {s} | a hole in a rotation '
                     f'that closed: the export holds {hold} | {hold} |')
        for d, f, s, hold in R['pend']:
            L.append(f'| — | {dlabel(d)} | {f.replace("UGD", "UR")} | {s} | **not missing** — still '
                     f'to fly when the download stopped | {hold or "—"} |')
        # the log-gate category: the report's own rows, topped up from the claims table so that
        # days the report calls complete are not skipped
        seen = {(d, f, s) for d, f, t, s, who in R['notlogged']}
        for d, f, tail, s, who in R['notlogged']:
            i += 1
            L.append(f'| {i} | {dlabel(d)} | {f} | {s} | the track exists, transmitted as '
                     f'**{who}**, so the log will not take it ({tail}) — nothing to fetch '
                     f'| as {who} |')
        for r in unlogged_from_tails(ym):
            key = (r['date'], r['flight'], f"{r['origin']}–{r['dest']}")
            if key in seen or r['flight'] != 'UR523':
                continue
            i += 1
            L.append(f'| {i} | {dlabel(r["date"])} | {r["flight"]} | {key[2]} | the track exists, '
                     f'transmitted as **AF523**, so the log will not take it ({r["tail"]}) — '
                     f'nothing to fetch | as AF523 |')
        for d, f, tail, s, who in R['chain']:
            L.append(f'| — | {dlabel(d)} | {f} | {s} | **not missing** — the app labels the day\'s '
                     f'two hops as one leg; the export holds {who} | {who} |')
        L.append('')
        gap, later, folded, why = scheduled_without_track(ym, hole_keys, pend_keys, months)
        if why:
            L.append(f'*Timetable check: no schedule for {ym} — {why}.*')
        else:
            if folded:
                L.append(f'### Also {FULL[int(ym[5:7]) - 1]}: {len(folded)} scheduled legs the log '
                         'holds in another shape — not a gap')
                L.append('')
                L.append('| scheduled | flight | sector | logged instead | why |')
                L.append('|---|---|---|---|---|')
                for d, r, lg, kind in folded:
                    if kind == 'partial':
                        why = (f'the track starts in the cruise, so the log infers the origin: it '
                               f'files this as {lg[0]} **{lg[2]}–{lg[3]}** on {dlabel(lg[4])} with '
                               'take-off not observed')
                    else:
                        why = (f'the log files a leg by local time, and this one crosses midnight '
                               f'under {lg[0]} on {dlabel(lg[4])} ({lg[4]})')
                    L.append(f'| {dlabel(d)} {r["dep_local"]} | {r["flight"]} | {r["from"]}–{r["to"]} '
                             f'| {dlabel(lg[4])} {lg[2]}–{lg[3]} | {why} |')
                L.append('')
            if gap:
                cap, _ = capture_end(ym)
                def due_earlier(j):
                    """Was this leg already due when the capture last said anything with a time?"""
                    d0 = _utc(j.get('sched_dep_utc', ''))
                    return cap is None or (d0 is not None and d0 <= cap)
                hard = [g for g in gap if due_earlier(g[2])]
                L.append(f'### Also {FULL[int(ym[5:7]) - 1]}: {len(gap)} scheduled legs with '
                         'no track, that are not rotation holes or pending legs')
                L.append('')
                L.append('| date | flight | sector | scheduled off | status in the capture | '
                         'what that word means |')
                L.append('|---|---|---|---|---|---|')
                for d, r, j in gap:
                    verdict = ('the leg was due while the capture was still reporting, and it still '
                               'reads `Scheduled`' if due_earlier(j) else
                               f'the capture stops at {cap:%d %b %H:%M}Z, before this leg was due')
                    L.append(f'| {dlabel(d)} | {r["flight"]} | {r["from"]}–{r["to"]} | '
                             f'{r["dep_local"]} local | `{r["FR24_status_raw"]}` | {verdict} |')
                L += ['', f'**{len(hard)}** of them were due while the app capture was still naming '
                      f'landings (its newest is {cap:%d %b %Y %H:%M}Z) and still read `Scheduled`: '
                      'no track and no claimed landing, which is as close as this data gets to a '
                      f'service that did not operate as published. The other **{len(gap) - len(hard)}** '
                      'sit past that stamp, so nothing here classifies them either way: no track is '
                      'not proof of no flight. A fresh timetable capture with the matching export '
                      'settles both groups.', '']
            if later:
                L += [f'*Counted nowhere above: **{len(later)}** scheduled legs are due to land after '
                      f'the archive\'s last fix ({mcut:%Y-%m-%d %H:%M}Z), so they are not downloaded '
                      'yet rather than missing.*', '']
    txt = '\n'.join(L).rstrip() + '\n'
    open('missing_flights.md', 'w').write(txt)
    print(txt)
    print(f'wrote missing_flights.md ({os.path.getsize("missing_flights.md"):,} B)')


if __name__ == '__main__':
    main()
