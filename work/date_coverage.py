#!/usr/bin/env python3
"""Date coverage: which days are in the export, which are unfinished, and what is missing.

Two independent kinds of evidence are used, and they are labelled differently
because they mean different things:

  * **app-confirmed missing** — a per-tail app page lists a leg for that date, and the
    export holds no track for it. The app is an independent record of what flew, so
    this is a firm statement that the export is short a flight.
  * **rotation hole** — a triangle rotation left Entebbe that day and came back, but a
    leg in between is not in the export. Nobody has seen the missing leg on a screen;
    it follows from the rotation's own chain, so it is reported as a hole in the
    rotation, not as a flight confirmed to have flown.
  * **tracked, but not logged** — the export *does* hold the track, yet the log has no
    leg for it, because the callsign it was transmitted under fails the gate in
    build_log.flight_number() (the Hoima legs fly as `AF523` while the app pages call
    them `UR523`). The flight data exists, so the day is not short of anything — the
    record is just filed outside the log. Reported separately for that reason.

Flight numbers are compared on digits alone: the log writes `UGD122`, the app pages and
the track filenames write `UR122`, and a join on the whole string matches nothing.

Rotations are grouped as *sequences* (outbound, middle, return), never by calendar
date alone, because a rotation's legs straddle local midnight.

Writes date_coverage.md.  Re-run after every build; the month it reports is read from
`fr24_publish/flights.csv` (override with FR24_MONTH=YYYY-MM).

    PYTHONPATH=. python3 work/date_coverage.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout as RL
import csv, collections, datetime as dt, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import month_ctx as MC                              # noqa: E402
from month_ctx import ctx          # which month the published log describes

C = ctx()
P = RL.live_dir()          # this month's folder inside fr24_publish/
OUT = 'date_coverage.md'
WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONN = {m: i for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                                    'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}
INV = {v: k.title() for k, v in MONN.items()}
# the three triangle rotations: the chain each one is supposed to fly
CHAINS = collections.OrderedDict([
    ('UGD720', [('EBB', 'LUN'), ('LUN', 'HRE'), ('HRE', 'EBB')]),
    ('UGD722', [('EBB', 'HRE'), ('HRE', 'LUN'), ('LUN', 'EBB')]),
    ('UGD334', [('EBB', 'ZNZ'), ('ZNZ', 'JRO'), ('JRO', 'EBB')]),
])


def iso(s):
    return f"20{s[5:7]}-{MONN[s[2:5]]:02d}-{s[:2]}"


def dlab(d):
    return f"{d[8:]} {INV[int(d[5:7])]}"


def rotations_for(fl, legs, ls):
    """Walk one flight number's legs in time order and cut them into rotations.

    Returns a list of dicts: {date, flight, have, missing, status} where `date` is
    the day the rotation left Entebbe (or the leg's own day for a stray leg).
    """
    x, y = ls[0][1], ls[1][1]
    out = []
    i = 0
    while i < len(legs):
        r = legs[i]
        arr = lambda z: z['arrival_utc'] if z else ''
        od = (r['origin'], r['dest'])
        d = iso(r['date_local'])
        if od == ('EBB', x):
            nxt = legs[i + 1] if i + 1 < len(legs) else None
            nxt2 = legs[i + 2] if i + 2 < len(legs) else None
            if nxt and (nxt['origin'], nxt['dest']) == (x, y):
                if nxt2 and (nxt2['origin'], nxt2['dest']) == (y, 'EBB'):
                    out.append(dict(date=d, flight=fl, status='complete',
                                    last_arr=arr(nxt2),
                                    have={(r['origin'], r['dest']),
                                          (nxt['origin'], nxt['dest']),
                                          (nxt2['origin'], nxt2['dest'])},
                                    missing=[]))
                    i += 3
                else:
                    out.append(dict(date=d, flight=fl, status='no return leg',
                                    last_arr=arr(nxt),
                                    have={(r['origin'], r['dest']),
                                          (nxt['origin'], nxt['dest'])},
                                    missing=[(y, 'EBB')]))
                    i += 2
            elif nxt and (nxt['origin'], nxt['dest']) == (y, 'EBB'):
                out.append(dict(date=d, flight=fl, status=f'no {x}–{y}',
                                last_arr=arr(nxt),
                                have={(r['origin'], r['dest']),
                                      (nxt['origin'], nxt['dest'])},
                                missing=[(x, y)]))
                i += 2
            else:
                out.append(dict(date=d, flight=fl, status='outbound only',
                                last_arr=arr(r),
                                have={(r['origin'], r['dest'])},
                                missing=[(x, y), (y, 'EBB')]))
                i += 1
        else:
            # a leg with no outbound before it in this month: the rotation left
            # Entebbe in the previous month, or its outbound is missing too
            out.append(dict(date=d, flight=fl, status=f'only {r["origin"]}–{r["dest"]}',
                            last_arr=arr(r),
                            have={(r['origin'], r['dest'])}, missing=[]))
            i += 1
    return out


def main():
    log = MC.log_rows(P)
    man = list(csv.DictReader(open(f'{P}/manifest.csv')))
    tails = list(csv.DictReader(open(f'{P}/tails.csv')))
    app = list(csv.DictReader(open(f'{P}/app_status.csv')))

    tracks = collections.Counter(r['first_utc'][:10] for r in man)
    flights = collections.Counter(iso(r['date_local']) for r in log)
    days = [d for d in sorted(flights) if C['first'] <= d <= C['last']]
    # A local day between the first and the last logged day that carries no leg at all is a
    # different finding from a day with a hole in it - and it cannot be found by walking `days`,
    # which is built out of the days that have data. The 12 Oct build is why: 10 Oct held no leg,
    # and the report still asserted that every day was present. Walk the span instead.
    dcur = dt.date.fromisoformat(days[0])
    dend = dt.date.fromisoformat(days[-1])
    absent = []
    while dcur < dend:
        ds = dcur.isoformat()
        if ds not in flights and C['first'] <= ds <= C['last']:
            absent.append(ds)
        dcur += dt.timedelta(days=1)
    all_days = sorted(set(days) | set(absent))
    # A day can carry a leg or two and still be barely captured, and neither counter above says
    # so - both of them are built out of what is present. Compare each day with the month's own
    # typical. The 15 Oct build is the case: 12 Oct held 4 tracks and 2 legs, both of them late-
    # evening departures, so the day looked like it ran to the end of its bank and was called
    # complete while 23 planned legs of it were missing.
    _present = [tracks.get(d, 0) for d in all_days if d not in absent]
    med_tracks = sorted(_present)[len(_present) // 2] if _present else 0
    thin = [d for d in all_days if d not in absent and med_tracks
            and tracks.get(d, 0) < 0.4 * med_tracks]
    if not days:
        raise SystemExit(f'no logged flights fall in {C["ym"]} ({C["first"]} .. {C["last"]}) — the month is read from {C["src"]}; run the build for this month first, '
                         f'or pass FR24_MONTH=YYYY-MM')

    # ------------------------------------------------------------------ rotations
    rots = []
    for fl, ls in CHAINS.items():
        legs = sorted([r for r in log if r['flight'] == fl], key=lambda r: r['departure_utc'])
        rots += rotations_for(fl, legs, ls)
    # ------------------------------------------------------------ export window
    # the last fix in the archive: anything after this is simply not downloaded
    cut = max(r['last_utc'] for r in man)
    cut_dt = dt.datetime.strptime(cut, '%Y-%m-%d %H:%M:%SZ')
    cut_local = cut_dt + dt.timedelta(hours=3)          # EAT
    cut_day = cut_local.date().isoformat()

    # a "hole" = a rotation that left Entebbe and whose chain is short a leg.
    # A rotation whose last recorded leg was still in the air at the cut is *pending*,
    # not holed — the remainder had not flown (or had only just departed) when the
    # export was taken. 3 h covers the leg-to-leg gaps these chains actually show.
    def holed_by_status(r):
        return r['missing'] and r['status'] != f'only {r["missing"][0][0]}–{r["missing"][0][1]}'

    # Only a rotation missing the *tail* of its chain can be pending: nothing after the last
    # observed leg has had time to happen.  A rotation missing its middle hop is provably
    # incomplete no matter how close to the cut it sits, because the leg that follows the gap
    # was flown - which is how a 03 Oct UGD722 (EBB-HRE, LUN-EBB, no HRE-LUN) got filed as
    # "still to fly" when the aircraft was already back at Entebbe.
    TAIL_MISSING = {'no return leg', 'outbound only'}

    def is_pending(r):
        if not holed_by_status(r) or r['status'] not in TAIL_MISSING or not r.get('last_arr'):
            return False
        a = dt.datetime.strptime(r['last_arr'], '%Y-%m-%d %H:%M:%SZ')
        return (cut_dt - a) <= dt.timedelta(hours=3)

    holes_by_day = collections.defaultdict(list)
    pending_by_day = collections.defaultdict(list)
    for r in rots:
        if is_pending(r):
            pending_by_day[r['date']].append(r)
        elif holed_by_status(r):
            holes_by_day[r['date']].append(r)
    rot_by_day = collections.defaultdict(dict)
    for r in rots:
        rot_by_day[r['date']][r['flight']] = r

    # ------------------------------------------------- app-confirmed missing legs
    # digits only: the log writes UGD122, the app pages write UR122
    fno = lambda s: re.sub(r'^(UGD|UR|UG)', '', (s or '').upper())
    legsets = collections.defaultdict(set)
    for r in log:
        legsets[iso(r['date_local'])].add((fno(r['flight']), r['origin'], r['dest']))
    # the same leg may sit in the export under a callsign the log gate rejects
    gated = collections.defaultdict(set)
    for r in man:
        cs = (r['callsign'] or '').upper()
        if fno(r['flight']) and not re.match(r'^(UGD|UR|UG)\d', cs):
            for day in {r['first_utc'][:10], r['last_utc'][:10]}:
                gated[(fno(r['flight']), day)].add(cs)
    # A through-labelled app row is not a missing flight.  On 29 Sep the page for 5X-KOB reads
    # `UR720 HRE–EBB`, while the archive holds `UGD720 HRE→NBO` and `UGD720X NBO→EBB`: the
    # movement is captured, the app just merged the two hops onto one itinerary row under the
    # pre-suffix callsign.  So if the same flight number's logged legs chain origin→x→dest on
    # that day (the log's day, or the next one, since the app dates by UTC and the log by
    # local), the row is reported as covered rather than as something to fetch.
    # digits only, suffix letters dropped: the log writes `UGD720X` for the second hop of a
    # through-flight whose app row is `UR720`, and matching the strings would hide the chain
    fdig = lambda x: re.sub(r'[^0-9]', '', fno(x))
    byfl = collections.defaultdict(set)
    for r in log:
        byfl[(fdig(r['flight']), iso(r['date_local']))].add((r['origin'], r['dest']))

    def chained(key, day):
        f, o, dd = fdig(key[0]), key[1], key[2]
        for d2 in (day, (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()):
            hops = byfl.get((f, d2), set())
            for (a, b) in hops:
                if (a, b) != (o, dd) and (b, dd) in hops and a == o:
                    return f'{o}→{b} + {b}→{dd}'
        return ''

    confirmed = collections.defaultdict(list)
    notlogged = collections.defaultdict(list)
    chaincov = collections.defaultdict(list)
    for r in tails:
        if r['verified_track'] == 'Y' or not (C['first'] <= r['date'] <= C['last']):
            continue
        d = r['date']
        nxt = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat()
        key = (fno(r['flight']), r['origin'], r['dest'])
        if key[1] and key[2] and (legsets.get(d, set()) & {key} or legsets.get(nxt, set()) & {key}):
            continue
        who = gated.get((key[0], d)) or gated.get((key[0], nxt))
        if who:                                   # flown, tracked, but not in the log
            notlogged[d].append((r, sorted(who)))
            continue
        via = chained(key, d)
        if via:                                   # two logged hops, one app row
            chaincov[d].append((r, via))
            continue
        confirmed[d].append(r)
    appdays = sorted({r['date'] for r in tails})

    L, w = [], None
    L.append('# Which dates are in the export — and which are unfinished\n')
    present_txt = (f'the export says nothing at all about {len(absent)} of them '
                   f'({", ".join(dlab(a) for a in absent)})' if absent else 'every date in it is present')
    L.append(f'The archive now runs **{dlab(days[0])} – {dlab(days[-1])}** — {len(all_days)} days, '
             f'{len(man)} tracks, {len(log)} logged flights, and {present_txt}. The question is which '
             'days are *complete*.\n')
    if cut_day <= days[-1]:
        tail_ = 'so the final day is a stub rather than a finished day'
    else:
        tail_ = (f'which is past the end of {dlab(days[-1])}, the last logged day, so that day runs '
                 'to its normal end')
    L.append(f'**The download ends at {cut_local.strftime("%H:%M")} local on {dlab(cut_day)}** '
             f'({cut} UTC) — the last fix in the archive. Whatever flew after that is not in this '
             f'export yet, {tail_}, and a rotation still in the air at the cut is marked *pending* '
             'instead of missing.\n')
    L.append('Three kinds of evidence, kept apart because they mean different things:\n')
    L.append('* **app-confirmed missing** — a per-tail app page shows the leg for that date and the\n'
             '  export has no track for it. Independent evidence: the export is short a flight.')
    L.append('* **rotation hole** — a triangle rotation left Entebbe and came back, but a leg in between\n'
             '  is not in the export. The chain is what proves it, so it is a hole in a rotation rather\n'
             '  than a flight confirmed to have flown.\n')
    L.append('* **tracked, but not logged** — the export holds the track and the log has no leg for it,\n'
             '  because the callsign it was transmitted under fails the log\'s gate. Nothing needs\n'
             f'  fetching; it is a question for the log. **{sum(len(v) for v in notlogged.values())} legs\n'
             '  this month** sit in that category, all of them the Hoima runs, confirmed by the\n'
             '  operator on 2 Oct 2026 as the `UR523` service, flown under the `AF523` callsign.\n')
    L.append('---\n')
    L.append('## Every date at a glance\n')
    L.append('| date | day | tracks | flights | rotation holes | app-confirmed missing | pending at cut | verdict |')
    L.append('|---|---|---|---|---|---|---|---|')
    partial, detail = [], []
    for d in all_days:
        wd = WD[dt.date.fromisoformat(d).weekday()]
        n_holes = len(holes_by_day.get(d, []))
        n_app = len(confirmed.get(d, []))
        n_pend = len(pending_by_day.get(d, []))
        if d in absent:
            verdict = 'absent from the export'
            partial.append(d)
            detail.append(d)
        elif d in thin:
            verdict = "thin \u2014 %d tracks against a median of %d" % (tracks.get(d, 0), med_tracks)
            partial.append(d)
            detail.append(d)
        elif d == cut_day:
            verdict = 'cut-off'
        else:
            verdict = 'complete' if not (n_holes or n_app) else 'partial'
            if verdict == 'partial':
                partial.append(d)
            if verdict == 'partial' or n_pend:
                detail.append(d)
        L.append(f'| {dlab(d)} | {wd} | {tracks.get(d, 0)} | {flights.get(d, 0)} | '
                 f'{n_holes or "—"} | {n_app or "—"} | {n_pend or "—"} | **{verdict}** |')
    L.append('')
    n_done = sum(1 for d in all_days if d != cut_day and d not in absent and d not in thin and
                 not holes_by_day.get(d) and not confirmed.get(d))
    if absent:
        gap = (f'**{len(absent)} date{"s" if len(absent) > 1 else ""} in the span carr{"ies" if len(absent) == 1 else "y"} '
               f'no leg at all** (' +
               ', '.join(f'{dlab(a)} ({WD[dt.date.fromisoformat(a).weekday()]})' for a in absent) + '). ')
    else:
        gap = 'No date is missing and '
    L.append(f'**{n_done} of {len(all_days)} days are complete.** The other {len(partial)} '
             'are set out below with exactly what each is short, along with any rotation that was '
             'still in the air at the cut. ' + gap +
             'Every complete day runs to the normal end of that weekday\'s evening bank.\n')

    if thin:
        L.append("**%d date%s in the span %s almost no capture at all** (%s). Those days are "
                 'short of a download, not of a flight: the export holds a handful of tracks where '
                 'a normal day holds %d.\n'
                 % (len(thin), '' if len(thin) == 1 else 's',
                    'carries' if len(thin) == 1 else 'carry',
                    ', '.join('%s (%s)' % (dlab(t), WD[dt.date.fromisoformat(t).weekday()])
                              for t in thin), med_tracks))

    L.append('---\n')
    L.append('## The unfinished dates, and what each is missing\n')
    for d in detail:
        wd = WD[dt.date.fromisoformat(d).weekday()]
        L.append(f'### {dlab(d)} ({wd}) — {flights.get(d, 0)} flights, {tracks.get(d, 0)} tracks\n')
        if d in thin:
            n = tracks.get(d, 0)
            f = flights.get(d, 0)
            L.append('**Barely captured.** The export holds %d track%s dated there against a month '
                     'median of %d, and logs %d flight%s. Whatever else flew that day is not in this '
                     'archive, so the day is short of a capture rather than short of flights. The '
                     'legs to ask for are the ones no track of that flight number answers to.\n'
                     % (n, '' if n == 1 else 's', med_tracks, f, '' if f == 1 else 's'))
            L.append('')
        if d in absent:
            n = tracks.get(d, 0)
            L.append('**No leg is logged on this local day.** ' + (
                f'The export holds {n} track{"" if n == 1 else "s"} whose first fix falls on {d} UTC, '
                'and each one departed after 21:00Z, so it is logged on the following local day: the '
                'day was never captured, rather than flown empty.' if n else
                'Nothing in the export is dated there at all, so no capture was taken for that day.')
                + '\n')
            L.append('')
            continue
        rows_ = confirmed.get(d, [])
        if rows_:
            L.append('**Missing, app-confirmed** (the app lists the leg, the export has no track):\n')
            L.append('| flight | tail | sector | app status | also flown on |')
            L.append('|---|---|---|---|---|')
            for r in sorted(rows_, key=lambda x: (x['flight'], x['dest'])):
                others = sorted({dlab(iso(x['date_local'])) for x in log
                                 if fno(x['flight']) == fno(r['flight'])
                                 and (x['origin'], x['dest']) == (r['origin'], r['dest'])
                                 and iso(x['date_local']) != d})
                L.append(f"| {r['flight']} | {r['tail']} | {r['origin']}–{r['dest']} | "
                         f"{r['app_status'] or '—'} | "
                         + (', '.join(others[:4]) + ('…' if len(others) > 4 else '') if others else '—')
                         + ' |')
            L.append('')
        gg = notlogged.get(d, [])
        if gg:
            L.append('**Tracked, but not in the log** — the export holds these tracks; they are absent '
                     'from the log because the callsign they were transmitted under fails the gate, so '
                     'the day is not short of a flight:\n')
            L.append('| flight | tail | sector | app status | transmitted as |')
            L.append('|---|---|---|---|---|')
            for r, who in sorted(gg, key=lambda x: (x[0]['flight'], x[0]['dest'])):
                L.append(f"| {r['flight']} | {r['tail']} | {r['origin']}–{r['dest']} | "
                         f"{r['app_status'] or '—'} | {', '.join(who)} |")
            L.append('')
        cc = chaincov.get(d, [])
        if cc:
            L.append("**App rows that are not missing flights** — the aircraft's movement that day is "
                     'already in the export, as two logged hops under a suffixed callsign, so the app '
                     'row is a through-label rather than a flight to fetch:\n')
            L.append('| flight | tail | sector as the app labels it | the export holds |')
            L.append('|---|---|---|---|')
            for r, via in sorted(cc, key=lambda x: (x[0]['flight'], x[0]['dest'])):
                L.append(f"| {r['flight']} | {r['tail']} | {r['origin']}–{r['dest']} | {via} |")
            L.append('')
        hh = holes_by_day.get(d, [])
        if hh:
            L.append('**Rotation holes** — the rotation left Entebbe and returned; this leg is not in '
                     'the export:\n')
            for r in sorted(hh, key=lambda x: x['flight']):
                miss = ', '.join(f'{o}–{t}' for o, t in r['missing'])
                have = ', '.join(f'{o}–{t}' for o, t in sorted(r['have']))
                L.append(f"* **{r['flight']}** — missing {miss} (the export holds {have}).")
            L.append('')
        pp = pending_by_day.get(d, [])
        if pp:
            L.append('**Pending at the export cut** — the rotation was still in the air when the '
                     'download stopped, so the rest of its chain is not late, just not captured yet:\n')
            for r in sorted(pp, key=lambda x: x['flight']):
                miss = ', '.join(f'{o}–{t}' for o, t in r['missing'])
                have = ', '.join(f'{o}–{t}' for o, t in sorted(r['have']))
                gap = int((cut_dt - dt.datetime.strptime(r['last_arr'], '%Y-%m-%d %H:%M:%SZ')
                           ).total_seconds() // 60)
                L.append(f"* **{r['flight']}** — {miss} still to fly (the export holds {have}; the "
                         f"download stops {gap} min after that leg landed).")
            L.append('')
        if not rows_ and not hh and not pp and d not in thin:
            L.append('Nothing outstanding.\n')

    L.append('---\n')
    L.append('## The triangle route flights\n')
    n_mid_all = sum(1 for r in rots if any(ls[1] in r['missing'] for ls in CHAINS.values()))
    L.append('Three rotations run through the month — `UGD720` Entebbe→Lusaka→Harare→Entebbe, '
             '`UGD722` Entebbe→Harare→Lusaka→Entebbe and `UGD334` Entebbe→Zanzibar→Kilimanjaro→'
             'Entebbe. The export carries the Entebbe legs almost every time they fly; the **middle '
             f'sector, the hop between the two outstations, is the recurring gap** — {n_mid_all} of the '
             f'{len(rots)} rotations found are missing it, and that is the single largest hole in the '
             'archive.\n')
    L.append('| rotation | chain | rotations | complete | no middle sector | no return leg |')
    L.append('|---|---|---|---|---|---|')
    for fl, ls in CHAINS.items():
        chain = ' → '.join([ls[0][0]] + [t for _, t in ls])
        rr = [r for r in rots if r['flight'] == fl]
        comp = sum(1 for r in rr if r['status'] == 'complete')
        mid = sum(1 for r in rr if ls[1] in r['missing'])
        noret = sum(1 for r in rr if ls[2] in r['missing'])
        L.append(f'| {fl} | `{chain}` | {len(rr)} | {comp} | {mid} | {noret} |')
    L.append('')
    L.append('### The rotation leaving Entebbe each day\n')
    L.append('| date | day | UGD720 | UGD722 | UGD334 |')
    L.append('|---|---|---|---|---|')
    for d in days:
        wd = WD[dt.date.fromisoformat(d).weekday()]
        cells = []
        for fl, ls in CHAINS.items():
            r = rot_by_day.get(d, {}).get(fl)
            if not r:
                cells.append('—')
            elif r['status'] == 'complete':
                cells.append('complete')
            elif r['status'].startswith('no ') or r['status'] in ('outbound only',):
                miss = ', '.join(f'{o}–{t}' for o, t in r['missing'])
                cells.append(f'**missing {miss}**')
            else:
                cells.append(r['status'])
        L.append(f'| {dlab(d)} | {wd} | ' + ' | '.join(cells) + ' |')
    L.append('')
    L.append('A dash means no rotation of that flight left Entebbe that day — the 720 and 722 '
             'alternate rather than running daily, and `UGD334` flies a few days a week. Rows marked '
             '`only …` are single legs whose partners fall outside the month or are themselves '
             'missing.\n')

    L.append('---\n')
    L.append('## What to ask for\n')
    nmid = 0
    nret = 0
    for r in rots:
        for fl, ls in CHAINS.items():
            if r['flight'] != fl:
                continue
            if ls[1] in r['missing']:
                nmid += 1
            if ls[2] in r['missing']:
                nret += 1
    L.append(f'1. **{nmid} missing middle sectors** — the outstation-to-outstation hop, in rotations '
             'whose other legs are all in the export.')
    L.append(f'2. **{nret} missing return legs** — a rotation left Entebbe and the leg home is absent.')
    L.append(f'3. **The {sum(len(v) for v in confirmed.values())} legs the app confirms but the export '
             'does not hold**, listed date by date above.')
    n_c = sum(len(v) for v in chaincov.values())
    if n_c:
        L.append(f'   (Also not counted: **{n_c} app row(s)** whose sector the app labels as one '
                 f'leg while the export holds the same aircraft\'s two hops that day, listed above '
                 'as "not missing flights".)')
    n_g = sum(len(v) for v in notlogged.values())
    if n_g:
        L.append(f'   (Not counted there: **{n_g} legs** the app lists which the export *does* hold, '
                 'under a callsign the log does not accept. They are filed above as "tracked, but not '
                 'logged" — a question for the log, not a fetch request.)')
    if appdays:
        last_app = max(appdays)
        nxt = (dt.date.fromisoformat(last_app) + dt.timedelta(days=1)).isoformat()
        L.append(f'4. **App pages from {dlab(nxt)} on**, so the days after the capture can be checked '
                 f'against a record as well as against the rotation pattern. The pages currently stop '
                 f'at {dlab(last_app)}.')
    L.append('')
    text = '\n'.join(L)
    open(OUT, 'w').write(text)
    print(f'wrote {OUT}: {len(text)} bytes, {text.count(chr(10))} lines, '
          f'{len(partial)} unfinished of {len(all_days)} days, '
          f'{sum(len(v) for v in holes_by_day.values())} rotations holed, '
          f'{sum(len(v) for v in pending_by_day.values())} pending at the cut')


if __name__ == '__main__':
    main()
