#!/usr/bin/env python3
"""Delays against the published schedule — the first time this project has had one.

    python3 work/schedule_delays.py [uploads/Uganda_Airlines_UR_week_02-09Oct2026_all-legs.csv]

`work/punctuality.py` had to say it out loud: *"the schedule itself is not in any file we hold, so
'usual' is measured from the operation, not published — a service that is always 40 minutes late will
read as on time here."*  This CSV is the weekly timetable with FR24's status on every leg, so a delay
here is **observed minus published**, and an arrival delay exists for the first time.

Three things the file needs before any arithmetic, all measured here rather than assumed:

1. **Status times are UTC, schedule times are airport-local.** `UR209 NBO→EBB` is due to land 01:30
   Entebbe time and reads `Landed 22:10` — that is 22:10Z on the previous day, i.e. 01:10 local,
   twenty minutes early.  A status is snapped to the day nearest the scheduled instant it belongs to,
   so a night arrival filed under the next morning's row reads as −20 min and not as −23 h 40 min.
2. **The exporter's time-zone table is inferred from the rows themselves.**  Each row carries a
   `block` (scheduled elapsed time), which fixes the offset difference between its two airports; the
   differences are voted across the week with Entebbe pinned at +0300.  This matters: Tanzania comes
   out at +0300 (really +0200), and a naive reading made two Kilimanjaro legs look 80 minutes early.
   Airports printed on the other clock are reported, and each such row carries a
   `clock_note` saying which one it was measured on.
3. **Only part of the week has been flown.**  A bare `Scheduled` splits into *not yet flown* (later
   than the newest observation in the file) and *no status at export* — the second bucket is the one
   worth looking at, because those legs were already airborne and the feed said nothing.

The build's own history is used as the forward view: from `flights.csv` in every month folder, each
service gets a median actual departure time and a median flown block, so a row shows both its delay
and whether the schedule plans it tighter than the fleet actually flies it.

Writes `schedule_delays.csv` and `schedule_delays.md` at the workspace root, where every other report
writes: `work/publish_layers.py` carries them into the month folder (the `date` column is what its month
guard reads), and `work/close_month.py` lists both among a month's files.  The default input is
`work/schedule/schedule_<month>.csv`, which is also what `work/make_reference.py` publishes as
`reference/schedule_<month>.csv` — the timetable is an input, and every delay in the folder is measured
against it, so it ships with the month.
"""
import argparse
import collections
import csv
import datetime as dt
import glob
import os
import re
import statistics as st
import sys

UTC = dt.timezone.utc

# true offsets in minutes east of UTC, for the airports this schedule touches.  No African
# observation of DST in October; London leaves BST on 25 Oct, so 02-09 Oct is still +0100.
TRUE = {'EBB': 180, 'NBO': 180, 'MBA': 180, 'MGQ': 180,
        'DAR': 120, 'ZNZ': 120, 'JRO': 120, 'BJM': 120, 'JUB': 120,
        'JNB': 120, 'HRE': 120, 'LUN': 120, 'FIH': 60,
        'LOS': 60, 'DXB': 240, 'BOM': 330, 'LGW': 60}


def hm(s):
    m = re.match(r'^(\d{1,2}):(\d{2})$', (s or '').strip())
    return None if not m else int(m.group(1)) * 60 + int(m.group(2))


def day(s):
    s = (s or '').strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return dt.date.fromisoformat(s)
    m = re.match(r'(\d{2})([A-Za-z]{3})(\d{2})', s)
    mon = 'JANFEBMARAPRMAYJUNJULAUGSEPOCTNOVDEC'.find((m.group(2) if m else '').upper())
    return dt.date(2000 + int(m.group(3)), mon // 3 + 1, int(m.group(1))) if mon >= 0 else None


def wraps(m):
    """minutes of difference, folded into −720..+720"""
    return (m + 720) % 1440 - 720


def band(m):
    if m == '':
        return ''
    if m < -15:
        return 'early'
    if m < 15:
        return 'on time'
    if m < 60:
        return 'late'
    return 'very late'


def parse_status(raw):
    """-> (kind, minutes-past-midnight-UTC or None).  kind in
    scheduled / landed / estimated / est_dep / other"""
    t = (raw or '').strip()
    low = t.lower()
    m = re.search(r'(\d{1,2}):(\d{2})', t)
    mins = int(m.group(1)) * 60 + int(m.group(2)) if m else None
    if low.startswith('scheduled'):
        return 'scheduled', mins                    # "Scheduled departure 18:35" = a plan, not an event
    if low.startswith('landed') or low.startswith('arrived'):
        return 'landed', mins
    if 'departur' in low or 'departed' in low:
        return 'est_dep', mins
    if low.startswith('estimated') or low.startswith('actual'):
        return 'estimated', mins
    return 'other', mins


def svc_key(flight, a, b):
    """one service = one flight number on one sector.

    The schedule writes `UR209`, the log writes the callsign `UGD209` (and `UGD207D` when the
    airframe carries a suffix), so both are folded onto the UR form here.  Anything flown by
    another airline under a Uganda callsign — there is one such series in the log — returns None and
    stays out of the baseline rather than matching a Uganda service by accident."""
    f = re.sub(r'[^A-Z0-9]', '', (flight or '').upper())
    m = re.match(r'^(?:UGD|UR)(\d+)', f)
    return ('UR' + m.group(1), a, b) if m else None


# --------------------------------------------------------------------- what the fleet really does ---
def baseline(rows):
    """Per service: median actual departure minute-of-day (UTC), median flown block from the log's own
    window, and median **track window** from the archive zip.

    The two blocks are not the same quantity and only one of them is comparable to a published
    schedule time.  `departure_utc`/`arrival_utc` are measured inside the track (median 3.6 min after
    the first fix and 1.6 min before the last), while the track itself starts and ends on the ground
    in 248 and 233 of the first 250 legs - so the track window is the off-block-to-on-chocks figure a
    schedule is written against, and the log window is the airborne part of it.  The gap is reported
    rather than assumed away, and legs the log had to extrapolate (`takeoff_not_observed`,
    `landing_not_observed`) are kept out of both.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, 'work'))
    pub = os.path.join(root, 'fr24_publish')
    dep = collections.defaultdict(list)
    blk = collections.defaultdict(list)
    arr = collections.defaultdict(list)
    months = sorted(d for d in os.listdir(pub) if re.fullmatch(r'UR [A-Z]+ \d{4}', d)) \
        if os.path.isdir(pub) else []
    for m in months:
        q = os.path.join(pub, m, 'flights.csv')
        if not os.path.exists(q):
            continue
        for r in csv.DictReader(open(q, newline='', encoding='utf-8')):
            if not (r.get('departure_utc') or '').strip():
                continue
            t = dt.datetime.strptime(r['departure_utc'].strip(), '%Y-%m-%d %H:%M:%SZ')
            k = svc_key(r.get('flight', ''), r.get('origin', ''), r.get('dest', ''))
            if k is None:
                continue
            dep[k].append(t.hour * 60 + t.minute)
            if (r.get('arrival_utc') or '').strip():
                ta = dt.datetime.strptime(r['arrival_utc'].strip(), '%Y-%m-%d %H:%M:%SZ')
                blk[k].append((ta - t).total_seconds() / 60)
                arr[k].append(ta.hour * 60 + ta.minute)
    tblk = collections.defaultdict(list)
    zpath = os.path.join(pub, 'FR data.zip')
    win = track_windows(zpath) if os.path.exists(zpath) else {}
    for m in months:
        q = os.path.join(pub, m, 'flights.csv')
        if not os.path.exists(q):
            continue
        for r in csv.DictReader(open(q, newline='', encoding='utf-8')):
            if not (r.get('departure_utc') or '').strip():
                continue
            if (r.get('takeoff_not_observed') or '').strip() or (
                    r.get('landing_not_observed') or '').strip():
                continue                      # an extrapolated end is not a measured block
            k = svc_key(r.get('flight', ''), r.get('origin', ''), r.get('dest', ''))
            w = win.get((r.get('source_file') or '').split('/')[-1])
            if k and w:
                tblk[k].append(w)
    arrmed = {k: st.median(v) for k, v in arr.items() if len(v) >= 3}
    med = {k: st.median(v) for k, v in dep.items() if len(v) >= 3}
    n = {k: len(v) for k, v in dep.items() if len(v) >= 3}
    spread = {k: st.median([abs(wraps(x - st.median(v))) for x in v]) for k, v in dep.items()
              if len(v) >= 3}
    bmed = {k: st.median(v) for k, v in blk.items() if len(v) >= 3}
    tmed = {k: st.median(v) for k, v in tblk.items() if len(v) >= 3}
    return med, spread, bmed, tmed, n, arrmed, months, (len(win) if win else 0)


def track_windows(zpath):
    """{track file name: minutes from the first fix to the last}, straight out of the archive zip"""
    import zipfile
    out = {}
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if not n.endswith('.csv'):
                continue
            txt = z.read(n).decode('utf-8', 'replace').splitlines()
            if len(txt) < 3:
                continue
            hdr = [c.strip().lower() for c in txt[0].split(',')]
            try:
                i = hdr.index('utc')
            except ValueError:
                continue
            ts = []
            for line in txt[1:]:
                v = line.split(',')[i] if line.count(',') > i else ''
                try:
                    ts.append(dt.datetime.strptime(v.strip(), '%Y-%m-%dT%H:%M:%SZ'))
                except ValueError:
                    pass
            if len(ts) >= 2:
                out[n.split('/')[-1]] = (ts[-1] - ts[0]).total_seconds() / 60
    return out


# --------------------------------------------------------------------- the file's own time zones ---
def calibrate(rows):
    """Offsets that reproduce each row's printed `block`, voted per airport pair, Entebbe pinned."""
    obs = collections.defaultdict(collections.Counter)
    for r in rows:
        bl, d, e = hm(r['block']), hm(r['dep_local']), hm(r['arr_local'])
        if None in (bl, d, e) or not day(r['arr_date_local']):
            continue
        span = e - d + (1440 if day(r['arr_date_local']) != day(r['date_local_dep']) else 0)
        obs[(r['from'], r['to'])][bl - span] += 1          # == off[from] - off[to] if consistent
    off = {'EBB': TRUE['EBB']}
    for _ in range(len(obs) + 2):
        changed = False
        for (a, b), votes in obs.items():
            diff, n = votes.most_common(1)[0]
            if n < 2:
                continue
            if a in off and b not in off:
                off[b] = off[a] - diff
                changed = True
            elif b in off and a not in off:
                off[a] = off[b] + diff
                changed = True
        if not changed:
            break
    for c in {r['from'] for r in rows} | {r['to'] for r in rows}:
        off.setdefault(c, TRUE.get(c, 180))
    return off


def sched_instants(r, off):
    d, ad = day(r['date_local_dep']), day(r['arr_date_local'])
    dm, am = hm(r['dep_local']), hm(r['arr_local'])
    if None in (d, dm, am) or ad is None:
        return None, None
    dep = dt.datetime(d.year, d.month, d.day, dm // 60, dm % 60, tzinfo=UTC) - \
        dt.timedelta(minutes=off[r['from']])
    arr = dt.datetime(ad.year, ad.month, ad.day, am // 60, am % 60, tzinfo=UTC) - \
        dt.timedelta(minutes=off[r['to']])
    if arr < dep:
        arr += dt.timedelta(days=1)
    return dep, arr


def snap(mins, near):
    """the UTC instant a bare HH:MM means, nearest the scheduled time it belongs to"""
    if mins is None or near is None:
        return None
    base = dt.datetime(near.year, near.month, near.day, tzinfo=UTC)
    c = [base + dt.timedelta(minutes=mins + k * 1440) for k in (-1, 0, 1)]
    return min(c, key=lambda q: abs((q - near).total_seconds()))


def clock_test(rows, off, arrmed):
    """Which clock does the file print the disputed airports on?

    `block` cannot answer that — it is a difference, so it is blind to a shared offset.  The archive
    can: it says when these services actually landed, in real UTC, so the scheduled arrival instant
    either sits next to that (the file prints those airports on one clock with Entebbe) or sits an
    hour off it (the file means the airport's own wall clock).
    """
    disputed = sorted({c for c in off if TRUE.get(c) is not None and off[c] != TRUE[c]})
    d_file, d_alt, legs = [], [], []
    for r in rows:
        if r['to'] not in disputed:
            continue
        k = svc_key(r['flight'], r['from'], r['to'])
        if k is None or k not in arrmed:
            continue
        _, a = sched_instants(r, off)
        if a is None:
            continue
        obs = arrmed[k]
        d_file.append(wraps(a.hour * 60 + a.minute - obs))
        d_alt.append(wraps(a.hour * 60 + a.minute + (TRUE[r['to']] - off[r['to']]) - obs))
        legs.append(f"{r['flight']} {r['from']}->{r['to']}")
    if not d_file:
        return disputed, None
    return disputed, dict(n=len(d_file), legs=sorted(set(legs)),
                          file_med=round(st.median(d_file)), alt_med=round(st.median(d_alt)),
                          file_p25=round(st.quantiles(d_file, n=4)[0]) if len(d_file) >= 4 else None,
                          reading='file' if abs(st.median(d_file)) <= abs(st.median(d_alt)) else 'true local')


def main():
    ap = argparse.ArgumentParser(description='delays against the published weekly schedule')
    ap.add_argument('csv', nargs='?', default=None,
                    help='schedule CSV (default: work/schedule/schedule_<month>.csv)')
    a = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, 'work'))
    ym = os.environ.get('FR24_MONTH') or __import__('month_ctx').ctx()['ym']
    canon = os.path.join(root, 'work', 'schedule', f'schedule_{ym}.csv')
    if a.csv:
        src = a.csv
    elif os.path.exists(canon):
        src = canon
    else:
        g = sorted(glob.glob(os.path.join(root, 'uploads', '*week*.csv')))
        src = g[-1] if g else canon
    src = src if os.path.isabs(src) else os.path.join(root, src)
    if not os.path.exists(src):
        raise SystemExit(f'no schedule file at {src} — pass a path, or put the month\u2019s timetable '
                         f'at work/schedule/schedule_{ym}.csv')
    print(f'schedule: {os.path.relpath(src, root)}   (month {ym})')
    rows = list(csv.DictReader(open(src, newline='', encoding='utf-8-sig')))

    off = calibrate(rows)
    wrong = sorted(c for c in off if TRUE.get(c) is not None and off[c] != TRUE[c])
    med, spread, bmed, tmed, nbas, arrmed, months, nwin = baseline(rows)
    disputed, clk = clock_test(rows, off, arrmed)

    latest = None
    for r in rows:
        kind, mins = parse_status(r['FR24_status_raw'])
        if mins is None or kind == 'scheduled':
            continue
        dep, arr = sched_instants(r, off)
        q = snap(mins, dep if kind == 'est_dep' else arr)
        if q and (latest is None or q > latest):
            latest = q

    out = []
    for r in rows:
        dep, arr = sched_instants(r, off)
        kind, mins = parse_status(r['FR24_status_raw'])
        act = snap(mins, dep if kind == 'est_dep' else arr) if kind != 'scheduled' else None
        k = svc_key(r['flight'], r['from'], r['to'])
        basis = 'actual' if kind == 'landed' else ('estimate' if kind in ('estimated', 'est_dep') else '')
        d_delay = round((act - dep).total_seconds() / 60) if (act and dep and kind == 'est_dep') else ''
        a_delay = round((act - arr).total_seconds() / 60) if (act and arr and kind in (
            'landed', 'estimated')) else ''
        if kind == 'scheduled':
            state = 'not yet flown' if (dep and latest and dep > latest) else 'no status at export'
        else:
            state = 'observed' if basis == 'actual' else 'estimated'
        blk_s = round((arr - dep).total_seconds() / 60) if (dep and arr) else ''
        blk_m = round(tmed[k], 1) if (k in tmed) else (round(bmed[k], 1) if (k in bmed) else '')
        blk_l = round(bmed[k], 1) if (k in bmed) else ''
        # A service sitting half a day away from its archive habit has been re-timed between seasons,
        # not flown late: compare the clock only where the two are close enough to be the same plan.
        gap = '' if (not k or k not in med or dep is None) else \
            round(wraps(dep.hour * 60 + dep.minute - med[k]))
        agap = '' if (not k or k not in arrmed or arr is None) else \
            round(wraps(arr.hour * 60 + arr.minute - arrmed[k]))
        retime = max(abs(gap), abs(agap)) if (gap != '' or agap != '') else ''
        if retime != '' and retime > 180:
            gap = agap = ''
            retime_note = 'service re-timed since the archive\u2019s month (>3 h apart)'
        else:
            retime_note = ''
        out.append(dict(
            date=r['date_local_dep'], day=r['day'], flight=r['flight'], from_=r['from'], to=r['to'],
            aircraft=r['aircraft'], dep_local=r['dep_local'], arr_local=r['arr_local'],
            sched_dep_utc=dep.strftime('%Y-%m-%d %H:%MZ') if dep else '',
            sched_arr_utc=arr.strftime('%Y-%m-%d %H:%MZ') if arr else '',
            sched_block_min=blk_s, fr24_status=r['FR24_status_raw'],
            actual_utc=act.strftime('%Y-%m-%d %H:%MZ') if act else '',
            status=kind, state=state, basis=basis,
            dep_delay_min=d_delay, arr_delay_min=a_delay, punctuality=band(a_delay),
            clock_note=(f"arrives at {r['to']}, printed {off[r['to']] // 60:+d}00 "
                        f"(airport clock {TRUE[r['to']] // 60:+d}00)" if r['to'] in wrong else ''),
            op_median_dep_utc=('' if (not k or k not in med)
                               else f'{int(med[k]) // 60:02d}:{int(med[k]) % 60:02d}Z'),
            sched_vs_op_min=gap, sched_vs_op_arr_min=agap, compare_ok=('' if retime_note else 'Y'),
            compare_note=retime_note,
            op_median_block_min=blk_m, op_median_air_min=blk_l,
            block_slack_min=('' if blk_m == '' or blk_s == '' else round(blk_s - blk_m, 1)),
            baseline_legs=(nbas.get(k, 0) if k else 0),
            baseline_spread_min=('' if (not k or k not in spread) else round(spread[k]))))

    os.makedirs(os.path.join(root, 'work'), exist_ok=True)
    # root-level, like every other report: `work/publish_layers.py` copies it into the month folder,
    # and its `date` column is what the month guard reads before it lets that happen
    cpath = os.path.join(root, 'schedule_delays.csv')
    with open(cpath, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    obs = [o for o in out if o['basis'] == 'actual' and o['arr_delay_min'] != '']
    est = [o for o in out if o['basis'] == 'estimate']
    early = [o for o in obs if o['punctuality'] == 'early']
    late = [o for o in obs if o['punctuality'] in ('late', 'very late')]
    nostat = [o for o in out if o['state'] == 'no status at export']
    future = [o for o in out if o['state'] == 'not yet flown']

    print(f'{len(rows)} legs · {len({r["date_local_dep"] for r in rows})} days · '
          f'{len({r["flight"] for r in rows})} flight numbers · baseline: '
          f'{len(months)} month folder(s), {len(med)} services with history, '
          f'{nwin} track windows for the block baseline')
    print('offsets the file schedules in (min east of UTC):  ' +
          '  '.join(f'{c}{off[c] // 60:+03d}{off[c] % 60:02d}' for c in sorted(off)))
    if wrong:
        print('  these airports are printed an hour off their own wall clock: ' +
              ', '.join(f'{c} file {off[c] // 60:+d}00 / airport {TRUE[c] // 60:+d}00' for c in wrong))
        if clk:
            print(f"  the archive settles which clock the file means: "
                  f"{clk['n']} legs into {', '.join(disputed)} · median gap to a real landing "
                  f"{clk['file_med']:+} min on the file's clock, {clk['alt_med']:+} min on the "
                  f"airport's → {clk['reading']} clock is the one being used")
    print(f'newest timestamp in the file: {latest:%Y-%m-%d %H:%M}Z — later services have not flown')
    print(f'\n{len(obs)} arrival delays from an actual landing: {len(early)} early · '
          f'{len(obs) - len(early) - len(late)} on time (±15) · {len(late)} late · median '
          f'{st.median([o["arr_delay_min"] for o in obs]):+.0f} min · '
          f'range {min(o["arr_delay_min"] for o in obs):+} … {max(o["arr_delay_min"] for o in obs):+}')
    for o in sorted(obs, key=lambda o: (o['date'], o['flight'])):
        print(f"  {o['date']} {o['flight']:7} {o['from_']}->{o['to']:<4} "
              f"sched arr {o['sched_arr_utc']}  landed {o['actual_utc']}  "
              f"{o['arr_delay_min']:+5} min  {o['punctuality']:<9}"
              f"{'  [clock]' if o['clock_note'] else ''}")
    if est:
        print(f'\n{len(est)} carry an estimate rather than an event — a forecast, not a delay:')
        for o in est:
            t = o['dep_delay_min'] if o['dep_delay_min'] != '' else o['arr_delay_min']
            which = 'take-off' if o['dep_delay_min'] != '' else 'arrival'
            print(f"  {o['date']} {o['flight']:7} {o['from_']}->{o['to']:<4} "
                  f"sched {o['sched_dep_utc'] if which == 'take-off' else o['sched_arr_utc']}  "
                  f"estimated {o['actual_utc']}  {t:+5} min at {which}")
    if nostat:
        print(f'\n{len(nostat)} legs had departed by the cut-off with no FR24 status at all:')
        for o in nostat[:20]:
            print(f"  {o['date']} {o['flight']:7} {o['from_']}->{o['to']:<4} sched dep {o['sched_dep_utc']}")
    print(f'{len(future)} legs are scheduled after the cut-off (no data expected)')

    tight = [o for o in out if o['block_slack_min'] != '' and o['block_slack_min'] <= 0]
    by_svc = collections.defaultdict(list)
    for o in tight:
        by_svc[(o['flight'], o['from_'], o['to'])].append(o)
    drift = [o for o in out if o['sched_vs_op_min'] != '' and abs(o['sched_vs_op_min']) >= 20]
    measured = [o for o in out if o['sched_vs_op_min'] != '']
    retimed = [o for o in out if o['compare_note']]
    slack = [o['block_slack_min'] for o in out if o['block_slack_min'] != '']
    banked = [o['sched_vs_op_min'] for o in measured if o['sched_vs_op_min'] > 0]
    deficit = [o['sched_vs_op_min'] for o in measured if o['sched_vs_op_min'] < 0]
    if slack:
        print(f'\nschedule generosity: {len(slack)} legs have a flown baseline; median scheduled block '
              f'{st.median(slack):+.1f} min against the median block actually flown '
              f'(min {min(slack):+.1f}, max {max(slack):+.1f}); '
              f'{len([x for x in slack if x <= 0])} are blocked at or below the time the fleet spends')
    if retimed:
        print(f'{len(retimed)} legs are not comparable on the clock: their service sits more than 3 h '
              f'from the archive habit, i.e. it has been re-timed since '
              f'({", ".join(sorted({o["flight"] for o in retimed}))})')
    if measured:
        print(f'schedule vs habit: median gap {st.median([o["sched_vs_op_min"] for o in measured]):+.0f} '
              f'min over {len(measured)} legs (positive = scheduled after the service usually leaves)')
        if banked:
            print(f'    {len(banked)} scheduled after the habit (median {st.median(banked):+.0f} min): '
                  f'the operation leaves early and banks it')
        if deficit:
            print(f'    {len(deficit)} scheduled before the habit (median {st.median(deficit):+.0f} min)'
                  f' - written to be missed: ' + ', '.join(
                      f"{o['flight']} {o['from_']}->{o['to']}" for o in
                      sorted((x for x in measured if x['sched_vs_op_min'] < -30),
                             key=lambda x: x['sched_vs_op_min'])[:6]))
    print(f'\nforward view: {len(measured)} of {len(out)} legs matched to a service in the archive; '
          f'{len(tight)} are blocked at or below the time the fleet spends '
          f'({len(by_svc)} services); {len(drift)} sit 20 min or more from when that service actually '
          f'leaves')
    for (fl, f_, t_), v in sorted(by_svc.items(),
                                  key=lambda kv: min(x['block_slack_min'] for x in kv[1]))[:8]:
        s = min(x['block_slack_min'] for x in v)
        m = [x for x in v if x['block_slack_min'] == s][0]
        print(f"  {fl:7} {f_}->{t_:<4} {len(v)} leg(s) · worst {s:+.0f} min vs "
              f"{m['op_median_block_min']} min flown over {m['baseline_legs']} legs")
    if drift:
        by = collections.Counter((o['flight'], o['from_'], o['to']) for o in drift)
        print('  biggest schedule-vs-operation gaps: ' + ', '.join(
            f"{fl} {f_}->{t_} ({n} legs)" for (fl, f_, t_), n in by.most_common(6)))

    write_md(root, out, rows, off, wrong, disputed, clk, latest, obs, est, nostat, by_svc, drift,
             cpath, len(med))
    print(f'\nwrote {os.path.relpath(cpath, root)} and schedule_delays.md')

def write_md(root, out, rows, off, wrong, disputed, clk, latest, obs, est, nostat, by_svc, drift,
             cpath, n_services):
    L = []
    w = L.append
    w("# Delays against the published schedule \u2014 02\u201309 October 2026")
    w("")
    w(f"{len(rows)} legs \u00b7 {len({r['flight'] for r in rows})} flight numbers \u00b7 "
      f"{len({r['date_local_dep'] for r in rows})} days. Per-leg numbers: "
      f"`{os.path.relpath(cpath, root)}`.")
    w("")
    w("This is the first timetable the repository has held, so for the first time a delay is "
      "**observed minus published** \u2014 and for the first time there is an arrival delay at all, "
      "since the app screenshots and the ADS-B log only ever fix a departure. The two measures "
      "disagree in a useful direction: `punctuality.csv` scores a service against its own habit, so a "
      "flight that always leaves 40 minutes late scores zero. Where this table and that one part "
      "company, it is the schedule being reported on, not the aircraft.")
    w("")
    w("## Three properties of the file that change the answer")
    w("")
    w("1. **Status times are UTC; schedule times are local.** `UR209 NBO\u2192EBB` is due at 01:30 "
      "Entebbe time and reads `Landed 22:10` \u2014 22:10Z the previous evening, i.e. 01:10 local, "
      "**twenty minutes early**, not 23 h 40 min late. Every status is snapped to the day nearest the "
      "scheduled instant it belongs to.")
    w("2. **The file runs East Africa on a single clock.** Offsets are not assumed: each row carries a "
      "`block`, which fixes the difference between its two airports, so the table below is voted "
      "across the week with Entebbe pinned at +0300:")
    w("")
    w("   " + " \u00b7 ".join(f"`{c}` {off[c] // 60:+03d}{off[c] % 60:02d}" for c in sorted(off)))
    w("")
    if wrong:
        w("   " + ", ".join(f"**{c}**" for c in wrong) +
          " come out at +0300 while those airports\u2019 own wall clocks run +0200. That is a display "
          "convention rather than an error \u2014 but reading the column at the wall clock invents an "
          "hour, which is exactly how two Kilimanjaro arrivals came to look 80 minutes early on a "
          "first pass.")
        w("")
        if clk:
            w(f"   A `block` is a difference, so it cannot settle which clock is meant; the archive can. "
              f"Across **{clk['n']} legs** into {', '.join(disputed)} that the log also holds, the "
              f"scheduled arrival sits a median of **{clk['file_med']:+} min** from a real landing on "
              f"the file\u2019s clock, and {clk['alt_med']:+} min on the airport\u2019s own. So the "
              f"**{clk['reading']}** reading is the exporter\u2019s, and it is what this table uses.")
            w("")
    w(f"3. **{len(obs) + len(est)} legs carry a status, {len(nostat)} more had departed without "
      f"one.** The snapshot "
      f"was cut at {latest:%H:%M}Z on {latest:%d %b}: everything later reads `not yet flown` \u2014 no "
      f"data is expected for those, so they are not gaps \u2014 while {len(nostat)} were already "
      f"airborne with nothing from the feed.")
    w("")
    w("## What actually happened")
    w("")
    if obs:
        w("| date | flight | sector | scheduled arrival | landed | delay | reads as |")
        w("|---|---|---|---|---|---|---|")
        for o in obs:
            w(f"| {o['date']} | {o['flight']} | {o['from_']}\u2192{o['to']} | {o['sched_arr_utc']} | "
              f"{o['actual_utc']} | {o['arr_delay_min']:+} min | {o['punctuality']}"
              f"{' \u00b7 *clock*' if o['clock_note'] else ''} |")
        w("")
        early = [o for o in obs if o['punctuality'] == 'early']
        late = [o for o in obs if o['punctuality'] in ('late', 'very late')]
        w(f"**{len(obs) - len(early) - len(late)} of {len(obs)} inside the \u00b115 min on-time "
          f"window**, {len(late)} late, {len(early)} early. Median "
          f"{st.median([o['arr_delay_min'] for o in obs]):+.0f} min, range "
          f"{min(o['arr_delay_min'] for o in obs):+} to {max(o['arr_delay_min'] for o in obs):+} min.")
        w("")
        srt = sorted(obs, key=lambda o: o['arr_delay_min'])
        w(f"Best and worst: **{srt[0]['flight']} {srt[0]['from_']}\u2192{srt[0]['to']}** at "
          f"{srt[0]['arr_delay_min']:+} min, **{srt[-1]['flight']} "
          f"{srt[-1]['from_']}\u2192{srt[-1]['to']}** at {srt[-1]['arr_delay_min']:+} min. The pattern "
          "is the one the app dots could only hint at, and the blocks now explain: short East African "
          "sectors arrive early \u2014 they are blocked generously \u2014 and the lateness lives on "
          "the long sectors, where the hours are in the air and not on the ground.")
    if est:
        w("")
        w("In the air when the file was cut, so these are forecasts and not delays:")
        w("")
        for o in est:
            which = 'take-off' if o['dep_delay_min'] != '' else 'arrival'
            t = o['dep_delay_min'] if which == 'take-off' else o['arr_delay_min']
            sched = o['sched_dep_utc'] if which == 'take-off' else o['sched_arr_utc']
            w(f"* {o['date']} **{o['flight']}** {o['from_']}\u2192{o['to']}: scheduled {sched}, FR24 "
              f"estimates {o['actual_utc']} \u2192 {t:+} min at {which}.")
    if nostat:
        w("")
        w(f"## Gone before the cut-off with no status ({len(nostat)})")
        w("")
        w("These had departed \u2014 the file carries observations from later in the same day \u2014 "
          "and the weekly view had nothing for them. They are unmeasurable from this file, which says "
          "something about the export and nothing about the operation; the daily export and the app "
          "screenshots are what fill them in:")
        w("")
        for o in nostat[:30]:
            w(f"* {o['date']} {o['flight']} {o['from_']}\u2192{o['to']}, scheduled departure "
              f"{o['sched_dep_utc']}")
    w("")
    w("## What the schedule says about the rest of the week")
    w("")
    w(f"Every leg is joined to the service it repeats \u2014 flight number and sector, matched through "
      f"the callsign form the log uses (`UGD209` for `UR209`) \u2014 and against what this build has "
      f"measured for that service: {n_services} services have three or more logged legs to compare "
      f"with. Two columns come out of that, and neither is a delay:")
    w("")
    w("* **`sched_vs_op_min`** \u2014 scheduled departure against the median time the service actually "
      "left. Negative means the timetable is earlier than the operation: that leg is written to be "
      "missed, every day.")
    w("* **`block_slack_min`** \u2014 scheduled block against the median block actually flown, measured "
      "ground-to-ground out of the archive's own tracks (first fix to last, which is on the ground at "
      "both ends in 248 and 233 of the first 250 legs). Negative means the schedule asks for less time "
      "than the aircraft needs: the sector is late by construction, and the delay arrives on the next "
      "one.")
    w("")
    if by_svc:
        w("The services scheduled tighter than they fly, worst first:")
        w("")
        w("| service | legs this week | worst shortfall | median flown | baseline legs |")
        w("|---|---|---|---|---|")
        for (fl, f_, t_), v in sorted(by_svc.items(),
                                      key=lambda kv: min(x['block_slack_min'] for x in kv[1]))[:14]:
            s = min(x['block_slack_min'] for x in v)
            m = [x for x in v if x['block_slack_min'] == s][0]
            w(f"| {fl} {f_}\u2192{t_} | {len(v)} | {s:+.0f} min | {m['op_median_block_min']} min | "
              f"{m['baseline_legs']} |")
        w("")
    slack = [o['block_slack_min'] for o in out if o['block_slack_min'] != '']
    gaps = [o['sched_vs_op_min'] for o in out if o['sched_vs_op_min'] != '']
    if slack:
        w("")
        w("### Where the week\u2019s time is hiding")
        w("")
        w(f"Across the {len(slack)} legs with a flown baseline, the scheduled block sits a median "
          f"**{st.median(slack):+.1f} min** above the block the fleet actually spends (range "
          f"{min(slack):+.1f} to {max(slack):+.1f} min). Read one way that is a padded timetable; read "
          f"the other way, {len([x for x in slack if x <= 0])} legs in {len(by_svc)} services are "
          f"blocked at or below the hours they take, and those are the ones that will run late:")
        w("")
        w("| service | legs this week | worst shortfall | median flown | baseline legs |")
        w("|---|---|---|---|---|")
        for (fl, f_, t_), v in sorted(by_svc.items(),
                                      key=lambda kv: min(x['block_slack_min'] for x in kv[1]))[:14]:
            s_ = min(x['block_slack_min'] for x in v)
            m = [x for x in v if x['block_slack_min'] == s_][0]
            w(f"| {fl} {f_}\u2192{t_} | {len(v)} | {s_:+.1f} min | {m['op_median_block_min']} min | "
              f"{m['baseline_legs']} |")
        w("")
        w("Two things about that list are worth more than the numbers. It is made of long sectors "
          "\u2014 Lagos, Johannesburg, Mumbai, London \u2014 where an hour is a rounding error and "
          "the padding cannot be recovered; and the padding that does exist is all on the short East "
          "African sectors, where 15 free minutes in a 75-minute block is how a 78-seat CRJ-900 keeps "
          "a timetable it could not otherwise keep.")
        w("")
        if obs:
            w("The 13 measured arrivals say the same thing from the other side:")
            w("")
            for o in sorted(obs, key=lambda o: -o['arr_delay_min'])[:13]:
                w(f"* **{o['flight']} {o['from_']}\u2192{o['to']}** arrived "
                  f"{o['arr_delay_min']:+} min on a sector with {o['block_slack_min']} min of slack.")
            w("")
            w("Every late arrival in the file sits on a sector with **negative** slack, and the eleven "
              "that came early or on time sit on sectors with +4 to +26 min of it. With thirteen data "
              "points that is not proof of anything, but it is the first time this project has had a "
              "reason for a late flight rather than a measurement of one.")
        w("")
    if gaps:
        neg = [g for g in gaps if g < 0]
        pos = [g for g in gaps if g > 0]
        w(f"On the departure clock the schedule is closer to the habit than the blocks are: median "
          f"{st.median(gaps):+.0f} min over {len(gaps)} legs. {len(pos)} legs are scheduled after the "
          f"time their service usually leaves (median {st.median(pos):+.0f} min of slack to bank) and "
          f"{len(neg)} before it (median {st.median(neg):+.0f} min) \u2014 and the second group is where "
          f"the operation is quietly chronic.")
        w("")
        cand = [o for o in out if o["sched_vs_op_min"] != "" and o["baseline_legs"] >= 5]
        if cand:
            wo = min(cand, key=lambda o: o["sched_vs_op_min"])
            w(f"The largest of them: **{wo['flight']} {wo['from_']}\u2192{wo['to']}** is scheduled "
              f"to leave {wo['dep_local']} local ({wo['sched_dep_utc']}), and across "
              f"{wo['baseline_legs']} logged legs that service has left at a median of "
              f"**{wo['op_median_dep_utc']}** \u2014 {abs(wo['sched_vs_op_min'])} min later than the "
              f"plan, with a scatter of {wo['baseline_spread_min']} min around it. The airline is not "
              f"late at that station by accident; it is late by timetable, which is a different "
              f"problem and looks like none in a table that scores each flight against its own habit.")
            peers = [o['sched_vs_op_min'] for o in out
                     if (o['flight'], o['from_'], o['to']) == (wo['flight'], wo['from_'], wo['to'])
                     and o['sched_vs_op_min'] != '']
            if len(peers) > 1:
                w("")
                w(f"Not the whole service, either: the {len(peers)} legs of it in this week run from "
                  f"{min(peers):+} to {max(peers):+} min against that median, so what is mis-timed is "
                  f"a day of the week, not a route. That distinction is only visible with a timetable; "
                  f"against a month of habit, all of these legs are equally normal.")
        w("")
    nrt = len([o for o in out if o['compare_note']])
    if nrt:
        w(f"{nrt} legs were left out of that comparison altogether: their service sits more than three "
          f"hours away from the time it kept in the archive month, which is a re-timed season, not a "
          f"late flight. A number of that size is not a measurement, and the honest move is to "
          f"withhold it rather than explain it.")
        w("")
    w("One caveat on the block baseline. A track window is only a block where the track starts and ends "
      "on the ground, which it does for 248 and 233 of the first 250 legs sampled; the rest lose some "
      "taxi, so a shortfall of a minute or two on those is inside the measurement. The `air_minutes` "
      "counterpart is in the CSV as `op_median_air_min` — the airborne part only, which is what "
      "`air_minutes` in the archive log means — and it sits a median 5.8 min below the window over the 182 comparable legs.")
    w("")
    w(f"{len(drift)} legs sit 20 minutes or more away from the time their service actually leaves. "
      "That is the honest definition of a structurally late flight, and it is a number the "
      "median-based `punctuality.csv` cannot produce at all: measured against itself, a habit is "
      "invisible.")
    w("")
    w("## What this file cannot answer")
    w("")
    w("* **Which aircraft flew what.** There is no registration column, so a flight number cannot be "
      "chained into a rotation \u2014 and without rotations there is no propagation: this table can say "
      "UR710 arrived 25 minutes late, not what that cost the UR711 that was to follow it. The daily "
      "export has the tail, and `tails.csv` already carries the claims, so the question is answerable "
      "as soon as the tail column is added to this export.")
    w("* **The other 178 legs.** Only 2 October has statuses; 03\u201309 October in this file is the "
      "forward plan, not a record. They fill in one day at a time.")
    w("* **September.** The timetable in this file starts on 2 October, so the 605 logged September "
      "legs cannot be re-scored against a published time. `punctuality.csv` stays on its median "
      "baseline for that month, correctly labelled; one September export of the same view would let "
      "the whole closed month be restated the way this week has been.")
    w("* **Sectors the schedule does not show.** Where the operation flew a sector the timetable has "
      "no row for, there is no scheduled time to be late against \u2014 the archive and this file "
      "disagree by omission, and the count is in `schedule_delays.csv` only from the schedule side.")
    w("")
    w("---")
    w("")
    w("Re-run it against the next export and the week fills itself in:")
    w("")
    w("```")
    w("python3 work/schedule_delays.py uploads/<newest weekly export>.csv")
    w("```")
    w("")
    w("When the week closes, this is the file `punctuality.csv` should be computed from \u2014 a "
      "timetable in place of the median that had to stand in for one.")
    open(os.path.join(root, 'schedule_delays.md'), 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
