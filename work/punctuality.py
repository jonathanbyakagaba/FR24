#!/usr/bin/env python3
"""Departure punctuality for the logged flights.

Primary flag: the app's own status dot, read from the screenshots
(work/status_dots.py -> app_status.csv).  The dot says how the operator's app
judged each leg: green normal, amber delayed, red badly late, grey no data.

Backup number: how far each departure sits from the usual departure time for
that service (median across the month, UTC).  The schedule itself is not in any
file we hold, so "usual" is measured from the operation, not published - a
service that is always 40 minutes late will read as on time here, which is why
the app flag stays the headline.

Writes punctuality.csv and punctuality.md.
"""
import csv, collections, datetime, os, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import month_ctx as MC        # noqa: E402  the log lives in this month's folder, which MC knows
MON = {m: i for i, m in enumerate(
    ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}
OUT = 'punctuality.csv'
REPORT = 'punctuality.md'

digits = lambda s: ''.join(ch for ch in (s or '') if ch.isdigit())
wraps = lambda d: (d + 720) % 1440 - 720


def ldate(s):
    d, m, y = s[:2], s[2:5], s[5:7]
    return f'20{y}-{MON[m.upper()]:02d}-{int(d):02d}'


def load_schedule(ym):
    """The published timetable for this month, if the build holds one.

    `reference/schedule_<month>.csv` is what `work/make_reference.py` ships from `work/schedule/`,
    and the time-zone handling is `work/schedule_delays.py`'s — the same calibration, not a second
    copy of it, because a schedule read with the wrong offsets turns a 20-minute-early arrival into
    a three-hour one.

    Returns ({(flight, origin, dest, local date): (sched dep, sched arr)}, path used).
    """
    import schedule_delays as SD
    for q in (f'{MC.RL.PUBLISH}/reference/schedule_{ym}.csv',
              f'work/schedule/schedule_{ym}.csv'):
        if not os.path.exists(q):
            continue
        rows = list(csv.DictReader(open(q, newline='', encoding='utf-8-sig')))
        off = SD.calibrate(rows)
        out = {}
        for r in rows:
            d, a = SD.sched_instants(r, off)
            if d is None:
                continue
            k = SD.svc_key(r.get('flight', ''), r.get('from', ''), r.get('to', ''))
            if k:
                out[(k[0], r['from'], r['to'], r['date_local_dep'])] = (d, a)
        return out, q
    return {}, None


def main():
    log = MC.log_rows()
    flags = {(f['tail'], f['date'], digits(f['flight']), f['origin'], f['dest']): f
             for f in csv.DictReader(open('app_status.csv'))}

    # One service = one flight number on one sector.  The key keeps the full
    # callsign (UGD207D is not UGD207) and the slot is only trusted where the
    # service actually keeps to one time of day - the ZNZ triangle departs at
    # different hours on different days, so its "usual time" is meaningless.
    svc = collections.defaultdict(list)
    for r in log:
        t = datetime.datetime.strptime(r['departure_utc'], '%Y-%m-%d %H:%M:%SZ')
        svc[(r['flight'].upper(), r['origin'], r['dest'])].append(t.hour * 60 + t.minute)
    med, spread = {}, {}
    for k, v in svc.items():
        if len(v) < 4:
            continue
        v = sorted(v)
        q1, q3 = v[len(v) // 4], v[(3 * len(v)) // 4]
        spread[k] = q3 - q1
        if q3 - q1 <= 45:
            med[k] = st.median(v)

    # key the app rows by the log date they were matched on (track_date), which for a
    # late-evening leg is the day after the app's own date; the app flag is still
    # filed under the app's date, so both are carried through
    tail_of, app_date = {}, {}
    for r in csv.DictReader(open('tails.csv')):
        k = ((r.get('track_date') or r['date']), digits(r['flight']), r['origin'], r['dest'])
        tail_of.setdefault(k, r['tail'])
        app_date.setdefault(k, r['date'])

    label = {'green': 'on time', 'amber': 'late', 'red': 'very late', 'grey': 'no data'}
    sched, sched_path = load_schedule(MC.ctx()['ym'])
    rows, matched, scored = [], 0, 0
    for r in log:
        k = (r['flight'].upper(), r['origin'], r['dest'])          # slot measure: UGD form
        fk = (digits(r['flight']), r['origin'], r['dest'])          # app flag: UR form
        t = datetime.datetime.strptime(r['departure_utc'], '%Y-%m-%d %H:%M:%SZ')
        # against the timetable when this month has one for this date, against the habit when not.
        # The two are different questions: the timetable asks whether the plan was kept, the habit
        # whether the day looked like the rest of the month.
        sk = ('UR' + fk[0], r['origin'], r['dest'], ldate(r['date_local']))
        sp = sched.get(sk)
        delay = wraps(t.hour * 60 + t.minute - med[k]) if k in med else ''
        src_slot = 'usual time (no timetable for this date)'
        sched_dep = sched_arr = arr_delay = ''
        if sp:
            sd, sa = sp
            delay = round((t.replace(tzinfo=datetime.timezone.utc) - sd).total_seconds() / 60)
            src_slot = 'published schedule'
            sched_dep, sched_arr = sd.strftime('%Y-%m-%d %H:%MZ'), sa.strftime('%Y-%m-%d %H:%MZ')
            if (r.get('arrival_utc') or '').strip():
                ta = datetime.datetime.strptime(r['arrival_utc'], '%Y-%m-%d %H:%M:%SZ')
                arr_delay = round((ta.replace(tzinfo=datetime.timezone.utc) - sa).total_seconds() / 60)
            scored += 1
        lk = (ldate(r['date_local']),) + fk
        tail = tail_of.get(lk, '')
        f = flags.get((tail, app_date.get(lk, ldate(r['date_local']))) + fk)
        status = f['app_status'] if f else ''
        if f:
            matched += 1
        rows.append(dict(
            date=ldate(r['date_local']), flight=r['flight'], origin=r['origin'], dest=r['dest'],
            tail=tail, dep_local=r['takeoff_local'], dep_utc=r['departure_utc'],
            app_status=status, punctuality=label.get(status, 'not captured'),
            dep_delay_min=round(delay) if delay != '' else '',
            arr_delay_min=arr_delay, sched_dep_utc=sched_dep, sched_arr_utc=sched_arr,
            slot_basis=src_slot,
            slot_regular='Y' if k in med else ('irregular' if k in spread else 'too few flights'),
            source_file=r['source_file']))

    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    have = [r for r in rows if r['app_status']]
    by = collections.Counter(r['app_status'] for r in have)
    print(f'wrote {OUT}: {len(rows)} flights, {matched} carry an app flag ({len(rows)-matched} not '
          f'captured), {scored} scored against a published timetable'
          + ('' if not sched_path else f' ({os.path.basename(sched_path)})'))
    print('  ' + ', '.join(f'{k} {v}' for k, v in by.most_common()))

    # ------------------------------------------------------------------ md ---
    L = []
    w = L.append
    w('# Departure punctuality')
    w('')
    w(f'The app status dot is available for **{matched} of {len(rows)}** logged flights. '
      'It is the operator-facing judgement; the delay column is our own measurement.')
    w('')
    if scored:
        w(f'**{scored} of {len(rows)}** legs are measured against the published timetable '
          f'(`{os.path.basename(sched_path)}`) — the only basis that can call a habit late. The rest '
          f'fall back to each service\u2019s usual time, because the build holds no timetable for '
          f'their date. The `slot_basis` column says which of the two every row used; a table that '
          f'mixed them without saying so would be comparing two different questions.')
    else:
        w(f'No leg in this month can be scored against a timetable: '
          + (f'the file on hand (`{os.path.basename(sched_path)}`) does not cover these dates'
             if sched_path else
             'the build holds no `reference/schedule_<month>.csv` for this month')
          + f'. Every delay below is therefore measured against the service\u2019s own usual time, '
            f'which cannot see a habit \u2014 a service that always leaves 40 minutes late scores '
            f'zero here.'
            + ('' if any(r['dep_delay_min'] != '' for r in rows) else
               ' In a month this short even that baseline is mostly unavailable: a usual time needs '
               'three logged legs of the same service, and these services have fewer.')
            + ' Where a timetable exists for a date, `schedule_delays.csv` is the file that answers '
              'the scheduling question instead.')
    w('')
    if not have:
        w(f'No leg in this month carries a status dot: the per-tail app screenshots for these dates '
          f'have not arrived, so the operator\u2019s own judgement is simply not in the build yet. '
          f'Everything below is measured here, from the tracks.')
    else:
        w('| app dot | flights | what it means | measured departure delay (median) |')
        w('|---|---|---|---|')
        for s in ('green', 'amber', 'red', 'grey'):
            sub = [r for r in have if r['app_status'] == s]
            if not sub:
                continue
            d = [r['dep_delay_min'] for r in sub if r['dep_delay_min'] != '']
            w(f'| {s} | {len(sub)} | {label[s]} | {st.median(d):+.0f} min |' if d
              else f'| {s} | {len(sub)} | {label[s]} | — |')
        w('')
        if any(r['app_status'] == 'red' for r in have):
            w('**The dot is not a cancellation flag.** Every red-flagged leg in this set still flew — '
              'it left late.')
    w('')
    w('## Worst departures in the month')
    w('')
    scored_rows = [r for r in rows if r['dep_delay_min'] != '']
    if not scored_rows:
        few = sum(1 for r in rows if r['slot_regular'] == 'too few flights')
        w(f'Nothing to rank: {few} of {len(rows)} legs belong to a service with fewer than three '
          f'logged departures this month, and the usual-time baseline needs three to say anything. '
          f'A published slot has no such floor \u2014 which is the practical case for '
          f'`schedule_delays.csv` over this table in a short month.')
        w('')
        open(REPORT, 'w').write('\n'.join(L) + '\n')
        print(f'wrote {REPORT} ({len(L)} lines)')
        return
    w('| date | flight | tail | sector | dep (local) | app dot | vs usual |')
    w('|---|---|---|---|---|---|---|')
    worst = sorted(scored_rows, key=lambda r: -r['dep_delay_min'])[:12]
    for r in worst:
        dot = r['app_status'] or '—'
        w(f"| {r['date']} | {r['flight']} | {r['tail']} | {r['origin']}-{r['dest']} | "
          f"{r['dep_local']} | {dot} | {r['dep_delay_min']:+d} min |")
    w('')
    w('## By aircraft')
    w('')
    w('| tail | flights | on time | late | very late | not captured |')
    w('|---|---|---|---|---|---|')
    for tail in sorted({r['tail'] for r in rows}):
        sub = [r for r in rows if r['tail'] == tail]
        c = collections.Counter(r['app_status'] for r in sub)
        w(f"| {tail} | {len(sub)} | {c['green']} | {c['amber']} | {c['red']} | "
          f"{sum(1 for r in sub if not r['app_status'])} |")
    w('')
    open(REPORT, 'w').write('\n'.join(L) + '\n')
    print(f'wrote {REPORT} ({len(L)} lines)')


if __name__ == '__main__':
    main()
