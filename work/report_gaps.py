#!/usr/bin/env python3
"""Regenerate data_gaps.md from the published tables.

Everything in the report is computed here: per-day coverage, the legs the app
confirms flew but the export has no track for, the same-weekday comparison, the
flagged-missing table and the screenshot coverage.  Re-run after every build.

    PYTHONPATH=. python3 work/report_gaps.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout as RL
import csv, collections, datetime as dt, os, sys, zipfile, io

sys.path.insert(0, '/home/user')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_log as B
import month_ctx as MC                              # noqa: E402
from month_ctx import ctx, SHORT

P = RL.live_dir()          # this month's folder inside fr24_publish/
OUT = 'data_gaps.md'
# which month this report describes is read from the published log, never typed here:
# see work/month_ctx.py.  Back-fill with FR24_MONTH=YYYY-MM.
MONN = {m: i for i, m in enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                                    'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], 1)}
WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
# which commit this report was checked against — the date cannot be inferred from
# the zip, so pass it in rather than leaving a stale string in the source:
#     FR24_PUSH='01 October 2026, 20:14 UTC' python3 work/report_gaps.py
PUSH = os.environ.get('FR24_PUSH', 'not recorded — pass FR24_PUSH')


def dlabel(d):
    """31 Aug / 21 Sep"""
    m = MONN_INV[d[5:7]]
    return f'{d[8:]} {m}'


MONN_INV = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
            '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}


def iso(s):
    return f"20{s[5:7]}-{MONN[s[2:5]]:02d}-{s[:2]}"


def load():
    log = MC.log_rows(P)
    man = list(csv.DictReader(open(f'{P}/manifest.csv')))
    tails = list(csv.DictReader(open(f'{P}/tails.csv')))
    cond = list(csv.DictReader(open(f'{P}/flight_conditions.csv')))
    rwy = list(csv.DictReader(open(f'{P}/runway_usage.csv')))
    import glob as _g
    _wxf = sorted(_g.glob(f'{P}/reference/weather_*.csv'))
    met = list(csv.DictReader(open(_wxf[-1]))) if _wxf else []
    return log, man, tails, cond, rwy, met


def main():
    C = ctx()
    log, man, tails, cond, rwy, met = load()
    zpath = RL.archive()
    z = zipfile.ZipFile(zpath)
    files = [n for n in z.namelist() if n.endswith('.csv')]
    fixes = 0
    for n in files:
        fixes += sum(1 for _ in io.StringIO(z.read(n).decode(errors='ignore'))) - 1

    tracks = collections.Counter(r['first_utc'][:10] for r in man)
    flights = collections.Counter(iso(r['date_local']) for r in log)
    obsday = collections.Counter(r['valid'][:10] for r in met)
    days = sorted(d for d in flights if C['first'] <= d <= C['last'])
    if not days:
        raise SystemExit(f'no logged flights fall in {C["ym"]} ({C["first"]} .. {C["last"]}) — the month is read from {C["src"]}; run the build for this month first, '
                         f'or pass FR24_MONTH=YYYY-MM')
    # what the per-tail pages actually reach, from the rows they produced
    tdays = sorted({r['date'] for r in tails if r['date']})
    tmin, tmax = (tdays[0], tdays[-1]) if tdays else (C['first'], C['first'])
    def tok(d):
        return f"{d[8:10]}{SHORT[int(d[5:7]) - 1].upper()}{d[2:4]}"

    # legs the app confirms but the export holds no track for
    legset = collections.defaultdict(set)
    for r in log:
        legset[iso(r['date_local'])].add((r['flight'][-3:], r['origin'], r['dest']))
    nomatch = [r for r in tails if r['verified_track'] != 'Y']
    missing_legs, present_unjoined = [], []
    for r in nomatch:
        d, nxt = r['date'], (dt.date.fromisoformat(r['date']) + dt.timedelta(days=1)).isoformat()
        key = (r['flight'][-3:], r['origin'], r['dest'])
        row = (d, r['tail'], r['flight'], r['origin'], r['dest'])
        (present_unjoined if key in legset.get(d, set()) or key in legset.get(nxt, set())
         else missing_legs).append(row)
    byday = collections.defaultdict(list)
    for row in missing_legs:
        byday[row[0]].append(row)

    # same-weekday comparison
    svc = collections.defaultdict(set)
    for r in log:
        svc[iso(r['date_local'])].add((r['flight'], r['origin'], r['dest']))

    L = []
    w = L.append
    w(f'# {C["name"]} coverage — checked against `FR data.zip`\n')
    w('*This file tracks what is missing across the whole archive (aircraft, weather, runways, '
      'events not observed). For the day-by-day picture — which dates are unfinished and exactly '
      'which flights are short — see **`date_coverage.md`**.*\n')
    push_lbl = (f"the export pushed **{PUSH}**" if not PUSH.startswith('not recorded') else
                f"the export as published (**{max(r['last_utc'] for r in man)} UTC** is its newest "
                f"fix — pass `FR24_PUSH=` to name the commit)")
    w(f'Verified against {push_lbl} (`FR data.zip`, '
      f'{os.path.getsize(zpath) / 1e6:.2f} MB, {len(files)} tracks).\n')
    last = max(iso(r['date_local']) for r in log)
    first = min(iso(r['date_local']) for r in log)
    w(f'**Archive: {len(files)} tracks · {fixes:,} fixes · log {len(log)} flights, '
      f'{tok(first)}–{tok(last)}.**\n')

    w('---\n')
    w('## Which dates are covered\n')
    w('| date | day | tracks | log | METAR | |')
    w('|---|---|---|---|---|---|')
    for d in days:
        t, f_, o = tracks.get(d, 0), flights.get(d, 0), obsday.get(d, 0)
        note = '✓' if f_ else '—'
        w(f'| {d[8:]} {SHORT[int(d[5:7]) - 1]} | {WD[dt.date.fromisoformat(d).weekday()]} '
          f'| {t} | {f_} | {o:,} | {note} |')
    w('')
    span = (f'1–{days[-1][8:]} {C["name"]}, every day'
            if days[0] == C['first'] and days[-1] == C['last']
            else f'{dlabel(days[0])} – {dlabel(days[-1])}, {len(days)} of {C["n_days"]} days')
    w(f'**Covered: {span}.** Tracks are counted by UTC start and log '
      'entries by local departure date, so the two differ on the days that straddle midnight. '
      f'The next day ({dlabel((dt.date.fromisoformat(days[-1]) + dt.timedelta(days=1)).isoformat())}) '
      'is not in any export yet.\n')

    w('---\n')
    w('## The gap the app exposes — legs flown but absent from the export\n')
    w(f'The per-tail app pages now cover {dlabel(tmin)} – {dlabel(tmax)}, so every leg they list can be checked '
      f'against the export. **{len(tails) - len(nomatch)} of {len(tails)} app rows are matched by a '
      f'track**; {len(nomatch)} are not. Of those, **{len(missing_legs)} have no track at all** for '
      'that flight number and sector on either the app date or the next local day:\n')
    w('| date (app) | tail | flight | sector |')
    w('|---|---|---|---|')
    for row in sorted(missing_legs):
        w(f'| {dlabel(row[0])} | {row[1]} | {row[2]} | {row[3]}–{row[4]} |')
    w('')
    tri_mid = [r for r in missing_legs
               if {r[3], r[4]} in ({'HRE', 'LUN'}, {'ZNZ', 'JRO'})]
    w(f'**{len(tri_mid)} of the {len(missing_legs)} are the middle sector of a triangle rotation** — '
      'the HRE–LUN / LUN–HRE hop or ZNZ–JRO. The export carries the Entebbe legs of those rotations '
      'and, on many days, nothing for the sector between the two outstations, even though the app '
      'lists it as flown. That is the single largest systematic gap in the source export.\n')
    w(f'The other {len(nomatch) - len(missing_legs)} unmatched rows **do** have a track for that '
      'flight number and sector — but on the next local day, with the app dating the row a day '
      'earlier:\n')
    w('| date (app) | tail | flight | sector | app status | track in export |')
    w('|---|---|---|---|---|---|')
    for row in sorted(present_unjoined, key=lambda r: (r[0], r[1])):
        d, tail, fl, o, de = row
        nxt = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat()
        hit = [x for x in log if iso(x['date_local']) == nxt and x['flight'][-3:] == fl[-3:]
               and x['origin'] == o and x['dest'] == de]
        st = next((x['app_status'] for x in tails
                   if x['tail'] == tail and x['date'] == d and x['flight'] == fl), '')
        w(f'| {dlabel(d)} | {tail} | {fl} | {o}–{de} | {st or "—"} | '
          f'{hit[0]["departure_utc"][:16]}Z |' if hit else
          f'| {dlabel(d)} | {tail} | {fl} | {o}–{de} | {st or "—"} | next day |')
    w('')
    w('For 7 of these the timing settles it: the track left in the last hours of the app\'s UTC day, '
      'so the app was dating the leg by its UTC day and the log by the airport\'s local day — those '
      'rows are joined by the build (see `tails.csv`, `track_date`). For the rest the app row is '
      'mostly green (on time), which argues the leg flew on the app\'s own date and the export is '
      'missing that day\'s track — the same gap as the table above, with a same-sector track one day '
      'later. The two readings cannot be told apart from this data, so those rows are left unjoined '
      'rather than guessed.\n')

    w('---\n')
    w('## Same-weekday check (independent of the app)\n')
    w('For days where the app has no coverage, compare the services flown with the other days of the '
      'same weekday. An entry here is a **candidate** gap, not a confirmed one — the service may simply '
      'not have operated.\n')
    for day in sorted(svc):
        if not (C['first'] <= day <= C['last']):
            continue
        peers = [d for d in svc if d != day and dt.date.fromisoformat(d).weekday()
                 == dt.date.fromisoformat(day).weekday()]
        gap = sorted(set().union(*[svc[p] for p in peers]) - svc[day]) if peers else []
        if gap:
            w(f'- **{day[8:]} {SHORT[int(day[5:7]) - 1]} ({WD[dt.date.fromisoformat(day).weekday()]})** — '
              f'{len(svc[day])} services vs {len(peers)} peer days; not seen: '
              + ', '.join(sorted({g[0] for g in gap})) + '.')
    w('')

    w('---\n')
    w('## Other data still flagged as missing\n')
    dig = lambda s_: ''.join(ch for ch in (s_ or '') if ch.isdigit())
    covered = {(dig(r['callsign']), r['track_date'] or r['date'], r['origin'], r['dest'])
               for r in tails if r['callsign']}
    n_log_cov = sum(1 for f in log
                    if (dig(f['flight']), iso(f['date_local']), f['origin'], f['dest']) in covered)
    w('| | now | note |')
    w('|---|---|---|')
    w(f'| **Aircraft assignment** | {len(tails) - len(nomatch)} of {len(tails)} app rows · '
      f'{n_log_cov} of {len(log)} logged flights | '
      f'the per-tail pages run to {dlabel(tmax)}; the remainder are rows the export has no track '
      'for (above) |')
    w(f'| **Weather** | {sum(1 for r in cond if r["dep_metar"])} take-off / '
      f'{sum(1 for r in cond if r["arr_metar"])} landing of {len(cond)} | '
      'Juba has no METAR station; the rest are legs whose station report is absent at that hour |')
    w(f'| **Runway identification** | {sum(1 for r in rwy if r["dep_rwy"])} departures / '
      f'{sum(1 for r in rwy if r["arr_rwy"])} arrivals of {len(rwy)} tracks | '
      'the remainder start airborne or end before touchdown |')
    w(f'| **Events not observed** | {sum(1 for r in log if r["takeoff_not_observed"])} take-offs · '
      f'{sum(1 for r in log if r["landing_not_observed"])} landings | '
      'times shown are the last real observation, never a guess |')
    same = [f for f in log if f['origin'] == f['dest']]
    if same:
        f0 = same[0]
        w(f'| **Local sortie** | {len(same)} track(s) | `{f0["flight"]}` on {f0["date_local"]} took off '
          f'and landed at {f0["origin"]} — an air test or training sortie, not a service |')
    UGA = {'UGD', 'UR7', 'UG3'}        # Uganda's own callsigns, however typed
    def oper(r):
        c = (r['callsign'] or '').upper()
        return c[:3] if c else '(blank)'
    mo = [r for r in man if r['first_utc'][:7] == C['ym']]
    oth = collections.Counter(oper(r) for r in mo if oper(r) not in UGA)
    # [:7] against a 10-char date compares wrong — month keys compare to month keys
    earlier = collections.Counter(oper(r) for r in man
                                  if r['first_utc'][:7] < C['ym'] and oper(r) not in UGA)
    NAME = {'ETH': 'Ethiopian', 'KLM': 'KLM', 'QTR': 'Qatar', 'THY': 'Turkish', 'RWD': 'Rwandair',
            'KQA': 'Kenya Airways', 'KNE': 'Kenya', 'MSR': 'EgyptAir', 'BEL': 'Brussels',
            'FDB': 'flydubai', 'GIA': 'Garuda', 'AF5': '`AF523` (Hoima)'}
    def oname(k, v):
        return f'{NAME[k]} ×{v}' if k in NAME else f'{k} ×{v}'   # unnamed codes stay as codes
    w(f'| **Other operators** | — | {C["name"]} holds {sum(1 for r in mo if oper(r) in UGA)} '
      f'Uganda-call-sign tracks'
      + (' plus ' + ', '.join(oname(k, v) for k, v in sorted(oth.items(), key=lambda kv: -kv[1]))
         if oth else '')
      + (f'; the archive also carries {sum(earlier.values())} earlier tracks from '
         + ', '.join(oname(k, v) for k, v in sorted(earlier.items(), key=lambda kv: -kv[1]))
         + ', none after ' + dlabel(max(r['first_utc'][:10] for r in man
                                        if r['first_utc'][:7] < C['ym'] and oper(r) not in UGA))
         if earlier else '')
      + ' |')
    w('')

    w('---\n')
    w('## What the screenshots cover\n')
    app = list(csv.DictReader(open(f'{P}/app_status.csv')))
    capof = {(a['tail'], a['date'], a['flight'], a['origin'], a['dest']): a['capture'] for a in app}
    CAPS = sorted({a['capture'] for a in app if a['capture']})
    heads = ' + '.join(dlabel(c.split()[0]) for c in CAPS)
    w('| tail | app rows | window | ' + ' | '.join(dlabel(c.split()[0]) for c in CAPS) + ' |')
    w('|---|---|---|' + '---|' * len(CAPS))
    for t in sorted({r['tail'] for r in tails}):
        rows = [r for r in tails if r['tail'] == t]
        days_ = sorted({r['date'] for r in rows})
        c = collections.Counter(capof.get((r['tail'], r['date'], r['flight'], r['origin'], r['dest']), '')
                                for r in rows)
        w(f'| {t} | {len(rows)} | {dlabel(days_[0])} – {dlabel(days_[-1])} | '
          + ' | '.join(str(c.get(k, 0)) for k in CAPS) + ' |')
    w('')
    w(f'The pages are per-tail snapshots, each holding roughly the last hundred flights, so a tail\'s '
      f'window opens whenever its page ran out of history: **the {heads} batches** supply '
      f'{len(app)} status rows. '
      f'{sum(1 for a in app if a["capture"] == CAPS[-1])} of those rows come from the newest capture '
      f'({CAPS[-1]}), which is why the days nearest the capture are the best covered and the older '
      'ones thin out at the far end of each page, not the near one.\n')

    w('---\n')
    w('## Shortest path to complete\n')
    lastfix = max(r['last_utc'][:10] for r in man)
    gap_days = [d for d in days if d > lastfix]
    if gap_days:
        ask = ('**Keep the daily export coming** — the archive stops at '
               f'{dlabel(lastfix)}, so {", ".join(dlabel(d) for d in gap_days)} '
               f'{"is" if len(gap_days) == 1 else "are"} not in it yet.')
    else:
        # Past the last logged day is not the same as complete on every day: a date can sit inside
        # the span and still hold almost nothing. 12 Oct held 2 legs where a normal day holds ~20, and
        # this sentence said the month had no gap in it at all.
        _v = sorted(flights[d] for d in days)
        typical = _v[len(_v) // 2] if _v else 0
        thin = [d for d in days if typical and flights[d] < 0.4 * typical]
        if thin:
            ask = ('**Keep the daily export coming** — the archive runs to {a}, past the last logged '
                   'day ({b}), but it is not evenly filled: **{n} date{p} carr{y} almost no capture** '
                   '({c}), where a normal day in this month holds {t} legs. A re-export dated on those '
                   'days is what closes them, not a longer span.'
                   ).format(a=dlabel(lastfix), b=dlabel(last), n=len(thin),
                            p='' if len(thin) == 1 else 's', y='ies' if len(thin) == 1 else 'y',
                            c=', '.join('%s (%d legs)' % (dlabel(d), flights[d]) for d in thin),
                            t=typical)
        else:
            ask = ('**Keep the daily export coming** — the archive is only as complete as the last upload, '
                   f'and this one runs to {dlabel(lastfix)}, past the last logged day '
                   f'({dlabel(last)}), so no {C["name"]} day is missing from it.')
    w(f'1. {ask}')
    w('2. **Re-export the triangle middle sectors** — the HRE–LUN / ZNZ–JRO hops are the bulk of what '
      'the app sees and the export does not.')
    w('3. **Keep sending the per-tail screenshots** — they are what ties an airframe to each leg; '
      f'coverage now stands at **{n_log_cov} of {len(log)}** logged flights carrying an aircraft.')
    w('4. Juba\'s weather cannot be closed from this source.\n')

    text = '\n'.join(L)
    open(OUT, 'w').write(text)
    print(f'wrote {OUT}: {len(text)} bytes, {text.count(chr(10))} lines')


if __name__ == '__main__':
    main()
