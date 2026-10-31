#!/usr/bin/env python3
"""METAR → flight conditions.

Answers the question "was the wind/weather behind what we can see in the tracks?".

  1. fetches published surface observations (METAR) for the airports in use, from
     the Iowa Environmental Mesonet ASOS archive — free, no account, same data as
     NOAA's Integrated Surface Database
  2. joins each flight to the observation in force at take-off (origin) and at
     landing (destination)
  3. resolves the wind into head- and cross-wind components for the runway the
     aircraft actually used, and works out which runway the wind favoured
  4. writes reference/weather_<month>.csv, flight_conditions.csv and
     weather_analysis.md

Run:  PYTHONPATH=/home/user python3 work/weather.py
"""
import csv
import sys, collections, datetime, os, statistics as st, sys, time, urllib.request, urllib.error

sys.path.insert(0, '/home/user')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_log as B
import month_ctx as MC        # noqa: E402  which month this build is for
import apt_source           # noqa: E402  the airport table, raw dump or published subset

TYPE = {'5X-NIL': 'A330-800neo', 'ET-APL': '737-800', '5X-KOB': 'CRJ900',
        '5X-KDP': 'CRJ900', '5X-EQU': 'CRJ900'}
IEM = 'https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py'
RAW = 'weather/raw_metar.csv'
# OUT and RAW_DIR are set from the log's month in main(): a fixed 2026-09 name would
# have October's run overwrite September's file, and a cache keyed only by station
# would hand back last month's observations
OUT = 'weather/metar_2026-09.csv'
COND = 'flight_conditions.csv'
REPORT = 'weather_analysis.md'

# OurAirports ICAO → the station the observations are filed under.  Two airports
# in this network have been re-coded, and Juba does not appear in the archive.
STATION = {'FVHA': 'FVRG',          # Harare: now Robert Gabriel Mugabe (FVRG)
           'FLLS': 'FLKK',          # Lusaka: now Kenneth Kaunda (FLKK)
           'HJJJ': ''}              # Juba: no METAR in the archive

FIELDS = ('station,valid,tmpf,dwpf,drct,sknt,gust,vsby,alti,wxcodes,metar')


def fetch(station, y1, m1, d1, y2, m2, d2, tries=5):
    """One station, one window.  The archive rate-limits bursts (HTTP 429), so
    back off and retry rather than losing the airport."""
    q = (f'{IEM}?station={station}&data=all&year1={y1}&month1={m1}&day1={d1}'
         f'&year2={y2}&month2={m2}&day2={d2}&tz=UTC&format=onlycomma&latlon=no'
         f'&missing=M&trace=T&direct=no&report_type=3&report_type=4')
    wait = 5
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(q, timeout=120) as fh:
                return fh.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            time.sleep(wait)
            wait *= 2
    raise RuntimeError('unreachable')


RAW_DIR = 'weather/raw'


def stations_needed():
    """every airport this data touches, as ICAO codes.

    B.AIRPORTS is keyed by IATA, so the airport table supplies the mapping; the
    runway analysis adds the airports used outside the logged network."""
    iata2icao = {}
    for r in apt_source.rows():
        if r['iata_code'].strip():
            iata2icao[r['iata_code'].strip().upper()] = r['ident']
    want = {iata2icao[i] for i in B.AIRPORTS if i in iata2icao}
    if os.path.exists('runway_usage.csv'):
        for r in csv.DictReader(open('runway_usage.csv')):
            for k in ('dep_apt', 'arr_apt'):
                if r[k]:
                    want.add(r[k])
    return sorted(want)


def log_path():
    """Where this month's `flights.csv` is, in the order the rest of the build tries it.

    The log moved into `UR <MONTH> <YEAR>/, so a hard-coded `fr24_publish/flights.csv` failed
    quietly: the caller fell back to a twelve-day window, and that thinner scratch copy then
    replaced the published weather table.  A missing log is an error now, not a narrower fetch.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import repo_layout as RL
    except ImportError:                    # run from somewhere without the work dir on the path
        RL = None
    cands = []
    if RL is not None:
        cands.append(os.path.join(RL.live_dir(), 'flights.csv'))
        for d in RL.month_dirs():
            cands.append(os.path.join(d['path'] if isinstance(d, dict) else d, 'flights.csv'))
    cands += ['fr24_publish/flights.csv', 'flights.csv']
    for c in cands:
        if c and os.path.exists(c):
            return c
    raise SystemExit('weather.py: no flights.csv in the publish tree — run fr24_update.py first. '
                     'Guessing a window would fetch fewer observations than the published table '
                     'and then overwrite it with the shortfall.')


def window():
    """fetch the observations that bracket the log, whatever it now covers"""
    with open(log_path(), newline='') as fh:
        d = [r['departure_utc'][:10] for r in csv.DictReader(fh) if r['departure_utc']]
    if not d:
        raise SystemExit(f'weather.py: no departure times in {log_path()}')
    return min(d), max(d)


def collect(days=None, refresh=False):
    """Every station's observations for the window.

    Each airport is cached in its own file under weather/raw/, so a run that is interrupted (or
    rate-limited) resumes instead of starting again.  A cache file only says which station and which
    month, though, so it also records the window it covers: ask for a wider window than the cached
    one and the stale file is refetched instead of quietly published short.  (That is how a
    thirteen-day fetch once replaced a month of published observations.)"""
    days = days or window()
    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = os.path.join(RAW_DIR, '.window')
    want = f'{days[0]}..{days[1]}'
    have = open(stamp).read().strip() if os.path.exists(stamp) else ''
    if have and have != want:
        print(f'  cache window {have} != requested {want} — refetching every station')
        refresh = True
    if not os.path.exists(stamp) or have != want:
        with open(stamp, 'w') as fh:
            fh.write(want + '\n')
    y1, m1, d1 = days[0].split('-')
    # the archive treats the end date as exclusive, so ask for one day past the
    # last flight or the final day of observations is silently absent
    y2, m2, d2 = (datetime.date.fromisoformat(days[1]) + datetime.timedelta(days=1)).isoformat().split('-')
    rows, fetched, cached, failed = [], 0, 0, []
    for icao in stations_needed():
        st_ = STATION.get(icao, icao)
        if not st_:
            continue
        path = os.path.join(RAW_DIR, f'{icao}.csv')
        if refresh or not os.path.exists(path):
            try:
                txt = fetch(st_, int(y1), int(m1), int(d1), int(y2), int(m2), int(d2))
            except Exception as e:
                failed.append((icao, str(e)))
                print(f'  {icao}: fetch failed ({e})')
                continue
            with open(path, 'w') as fh:
                fh.write(txt)
            fetched += 1
            time.sleep(1.2)                     # be a good citizen between stations
        else:
            cached += 1
        with open(path, newline='') as fh:
            n = 0
            for r in csv.DictReader(fh):
                r['icao'] = icao
                r['station_query'] = st_
                rows.append(r)
                n += 1
        print(f'  {icao:5} via {st_:5} {n:5} observations'
              f'{"  (cached)" if "" else ""}')
    print(f'  {fetched} fetched, {cached} from cache, {len(failed)} failed')
    if rows:
        with open(RAW, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
    return rows


def fnum(r, k):
    v = (r.get(k) or '').strip()
    if v in ('', 'M', 'T'):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def tidy(rows):
    """one row per observation, in the units we care about"""
    out = []
    for r in rows:
        t = (r.get('valid') or '').strip()
        if not t or t == 'valid':
            continue
        try:
            ts = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        out.append(dict(
            icao=r['icao'], station=(r.get('station') or '').strip(),
            valid=ts.strftime('%Y-%m-%d %H:%M'),
            wind_from=fnum(r, 'drct'), wind_kt=fnum(r, 'sknt'), gust_kt=fnum(r, 'gust'),
            vis_sm=fnum(r, 'vsby'), temp_f=fnum(r, 'tmpf'), dew_f=fnum(r, 'dwpf'),
            qnh_inhg=fnum(r, 'alti'),
            wx=(r.get('wxcodes') or '').strip(),
            metar=(r.get('metar') or '').strip(), ts=ts))
    out.sort(key=lambda r: (r['icao'], r['ts']))
    return out


def runway_headings():
    """(icao, ident) -> heading in degrees (corrected geometry where we have it)"""
    fixed = {}
    if os.path.exists('work/rwy/centreline_fixes.csv'):
        for r in csv.DictReader(open('work/rwy/centreline_fixes.csv')):
            fixed[(r['airport'], r['ident'])] = float(r['heading_degT'])
    hdg = dict(fixed)
    for r in csv.DictReader(open('work/rwy/runways.csv')):
        if r['closed'] == '1' or not r['le_latitude_deg'] or not r['he_latitude_deg']:
            continue
        for end, other in (('le', 'he'), ('he', 'le')):
            k = (r['airport_ident'], r[f'{end}_ident'])
            if k in hdg or not r[f'{end}_heading_degT']:
                continue
            hdg[k] = float(r[f'{end}_heading_degT'])
    return hdg


def components(wind_from, wind_kt, rwy_hdg):
    """head (+) / cross (+) and tail (−) components, knots, for a runway heading"""
    if wind_from is None or wind_kt is None or rwy_hdg is None:
        return None, None
    import math
    a = math.radians(wind_from - rwy_hdg)
    return wind_kt * math.cos(a), wind_kt * math.sin(a)


def wind_text(direction, speed, vrb='var'):
    """`260° / 12 kt` out of a METAR wind group, and a legible answer for the two ways that
    group is incomplete: a calm or VRB report carries a speed with no direction, and a flight
    with no observation at that end has neither. Both are legitimate, so they render -
    `float(None)` in the report writer is what stopped the 12 Oct build."""
    try:
        s = float(speed)
    except (TypeError, ValueError):
        return '\u2014'
    try:
        return f'{float(direction):.0f}\u00b0 / {s:.0f} kt'
    except (TypeError, ValueError):
        return f'{vrb} / {s:.0f} kt'


def main():
    global OUT, RAW_DIR
    import argparse
    ap = argparse.ArgumentParser(description='fetch the METAR window for the log month')
    ap.add_argument('--refresh', action='store_true',
                    help='ignore weather/raw/ and re-fetch every station (the archive also '
                         'revises older reports now and then)')
    args = ap.parse_args()
    # label by the month the build is *for*, not by the first day the fetch happens to start on:
    # an October log begins on 30 Sep UTC (a leg that Entebbe dates 1 Oct), and keying the table to
    # that first day once wrote October's observations into `metar_2026-09.csv`.
    C = MC.ctx()
    y_m = C['ym']
    fw = window()
    if fw[0][:7] != y_m:
        print(f'  note: {y_m} build, fetch window starts {fw[0]} (the log dates legs by local day)')
    OUT = f'weather/metar_{y_m}.csv'
    RAW_DIR = f'weather/raw/{y_m}'
    print(f'window month {y_m}  ·  consolidated {OUT}  ·  station cache {RAW_DIR}/')
    print('fetching METAR (cached after the first run)…')
    rows = tidy(collect(refresh=args.refresh))
    os.makedirs('weather', exist_ok=True)
    cols = ['icao', 'station', 'valid', 'wind_from', 'wind_kt', 'gust_kt', 'vis_sm',
            'temp_f', 'dew_f', 'qnh_inhg', 'wx', 'metar']
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f'\nwrote {OUT}: {len(rows):,} observations, {len({r["icao"] for r in rows})} airports')

    # index by airport
    by = collections.defaultdict(list)
    for r in rows:
        by[r['icao']].append(r)
    hdg = runway_headings()

    def nearest(icao, when, window_h=3.0):
        """observation in force at `when` (latest at or before, else the next one)"""
        lst = by.get(icao)
        if not lst or when is None:
            return None
        before = [r for r in lst if r['ts'] <= when]
        cand = before[-1] if before else lst[0]
        if abs((cand['ts'] - when).total_seconds()) > window_h * 3600:
            return None
        return cand

    iata2icao = {}
    for r in apt_source.rows():
        if r['iata_code'].strip():
            iata2icao[r['iata_code'].strip().upper()] = r['ident']

    log = list(csv.DictReader(open(log_path())))
    usage = {r['file']: r for r in csv.DictReader(open('runway_usage.csv'))}
    out = []
    for f in log:
        u = usage.get(f['source_file'], {})
        dep_t = datetime.datetime.strptime(f['departure_utc'], '%Y-%m-%d %H:%M:%SZ').replace(
            tzinfo=datetime.timezone.utc)
        arr_t = datetime.datetime.strptime(f['arrival_utc'], '%Y-%m-%d %H:%M:%SZ').replace(
            tzinfo=datetime.timezone.utc)
        # flights.csv carries IATA codes, the observations are filed by ICAO
        d_m = nearest(iata2icao.get(f['origin'], f['origin']), dep_t)
        a_m = nearest(iata2icao.get(f['dest'], f['dest']), arr_t)
        dr, ar = u.get('dep_rwy', ''), u.get('arr_rwy', '')
        dh, ah = hdg.get((u.get('dep_apt', ''), dr)), hdg.get((u.get('arr_apt', ''), ar))
        d_head, d_cross = components(d_m['wind_from'], d_m['wind_kt'], dh) if d_m else (None, None)
        a_head, a_cross = components(a_m['wind_from'], a_m['wind_kt'], ah) if a_m else (None, None)

        # which runway end did the wind favour at each end?  (into-wind heading)
        def favour(apt, m):
            if not m or m['wind_kt'] is None or m['wind_from'] is None or m['wind_kt'] < 3:
                return ''
            ends = {i: h for (a, i), h in hdg.items() if a == apt}
            if not ends:
                return ''
            best = min(ends, key=lambda i: abs(((m['wind_from'] - ends[i] + 180) % 360) - 180))
            return best

        out.append(dict(
            file=f['source_file'], flight=f['flight'], date_local=f['date_local'],
            origin=f['origin'], dest=f['dest'],
            dep_rwy=dr, dep_rwy_hdg=dh, arr_rwy=ar, arr_rwy_hdg=ah,
            dep_metar=datetime.datetime.strftime(d_m['ts'], '%H:%M') if d_m else '',
            dep_wind_from=d_m['wind_from'] if d_m else '', dep_wind_kt=d_m['wind_kt'] if d_m else '',
            dep_gust_kt=d_m['gust_kt'] if d_m else '',
            dep_vis_sm=d_m['vis_sm'] if d_m else '', dep_wx=d_m['wx'] if d_m else '',
            dep_temp_c=round((d_m['temp_f'] - 32) * 5 / 9, 1) if d_m and d_m['temp_f'] is not None else '',
            dep_headwind_kt=round(d_head, 1) if d_head is not None else '',
            dep_crosswind_kt=round(d_cross, 1) if d_cross is not None else '',
            dep_wind_favours=favour(u.get('dep_apt', ''), d_m),
            arr_metar=datetime.datetime.strftime(a_m['ts'], '%H:%M') if a_m else '',
            arr_wind_from=a_m['wind_from'] if a_m else '', arr_wind_kt=a_m['wind_kt'] if a_m else '',
            arr_gust_kt=a_m['gust_kt'] if a_m else '',
            arr_vis_sm=a_m['vis_sm'] if a_m else '', arr_wx=a_m['wx'] if a_m else '',
            arr_temp_c=round((a_m['temp_f'] - 32) * 5 / 9, 1) if a_m and a_m['temp_f'] is not None else '',
            arr_headwind_kt=round(a_head, 1) if a_head is not None else '',
            arr_crosswind_kt=round(a_cross, 1) if a_cross is not None else '',
            arr_wind_favours=favour(u.get('arr_apt', ''), a_m),
            dep_qnh_inhg=d_m['qnh_inhg'] if d_m else '',
        ))
    with open(COND, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    matched = sum(1 for r in out if r['dep_metar'])
    print(f'wrote {COND}: {len(out)} flights, {matched} with a take-off observation, '
          f'{sum(1 for r in out if r["arr_metar"])} with a landing observation')

    # ---------------------------------------------------------------- report ---
    L = []
    w = L.append
    ok_dep = [r for r in out if r['dep_headwind_kt'] != '']
    ok_arr = [r for r in out if r['arr_headwind_kt'] != '']
    w('# Airport conditions and what they explain')
    w('')
    w(f'Published METAR observations joined to each flight: **{matched} of {len(out)}** take-offs and '
      f'**{sum(1 for r in out if r["arr_metar"])}** landings have an observation within three hours.')
    w(f'Source: Iowa Environmental Mesonet ASOS archive (the same reports feed NOAA\'s Integrated')
    w(f'Surface Database) for the build month, one row per observation in '
      f'`reference/weather_{y_m}.csv`.')
    w('')
    have = sorted({r['icao'] for r in rows})
    missing = [r for r in stations_needed() if r not in have]
    w(f'**Coverage: {len(have)} of {len(stations_needed())} airports** in this operation file reports. '
      + ("No observations exist for " + ', '.join(missing) + " — Juba simply does not appear in the "
         "archive, so any Juba analysis has to come from the aircraft's own track." if missing
         else "Every airport is covered."))
    w('')
    w('## Runway in use vs the wind')
    w('')
    w('| | flights with a wind observation | chose the into-wind runway | chose the other end | calm (<3 kt) |')
    w('|---|---|---|---|---|')
    for side, label in (('dep', 'Take-off'), ('arr', 'Landing')):
        ok = [r for r in out if r[f'{side}_headwind_kt'] != '' and r[f'{side}_wind_favours']]
        agree = [r for r in ok if r[f'{side}_rwy'] == r[f'{side}_wind_favours']]
        other = [r for r in ok if r[f'{side}_rwy'] != r[f'{side}_wind_favours']]
        calm = [r for r in out if r[f'{side}_wind_kt'] != '' and (r[f'{side}_wind_kt'] or 0) < 3]
        w(f'| {label} | {len(ok)} | **{len(agree)}** | {len(other)} | {len(calm)} |')
    w('')
    off = [r for r in out if r['dep_headwind_kt'] != '' and r['dep_wind_favours']
           and r['dep_rwy'] != r['dep_wind_favours']]
    off_tw = [r for r in off if r['dep_headwind_kt'] < -5]
    if off:
        byapt = collections.Counter(r['origin'] for r in off)
        w(f'Most of the "other end" cases are airports with a single physical runway where the difference '
          f'between the two ends is small; only **{len(off_tw)} of {len(off)}** of them actually took off '
          f'with more than 5 kt of tailwind. They cluster at '
          + ', '.join(f'{a} ({n})' for a, n in byapt.most_common(4)) + '.')
        w('')
    w('## Wind components on the runway actually used')
    w('')
    for side, label in (('dep', 'Take-off'), ('arr', 'Landing')):
        hw = [float(r[f'{side}_headwind_kt']) for r in out if r[f'{side}_headwind_kt'] != '']
        cw = [abs(float(r[f'{side}_crosswind_kt'])) for r in out if r[f'{side}_crosswind_kt'] != '']
        tail = [r for r in out if r[f'{side}_headwind_kt'] != ''
                and float(r[f'{side}_headwind_kt']) < -5]
        if not hw:
            # three different absences, and they mean different things: no observation, no runway
            # attribution to point the observation at, or neither. Say which one it is.
            n_obs = sum(1 for r in out if r[f'{side}_wind_kt'] != '')
            n_rwy = sum(1 for r in out if r[f'{side}_rwy'])
            why = ('there is no runway attribution for these legs to point the wind at \u2014 '
                   '`runway_usage.csv` does not cover them; re-run `PYTHONPATH=/home/user python3 '
                   'work/runways.py` after a build\u2019s tracks land'
                   if n_rwy == 0 and n_obs else (
                       'no observation fell inside the fetched window' if not n_obs else
                       'the observations that exist carry no wind group'))
            w(f'- **{label}**: nothing to report \u2014 {why}. A median of an empty set is not a '
              f'measurement, so the row is left blank.')
            continue
        w(f'- **{label}**: median headwind component {st.median(hw):.0f} kt, median crosswind '
          f'{st.median(cw):.0f} kt; **{len(tail)} of {len(hw)}** had more than 5 kt of tailwind.')
    w('')
    strong = sorted((r for r in ok_arr if abs(r['arr_crosswind_kt']) >= 15),
                    key=lambda r: -abs(r['arr_crosswind_kt']))[:10]
    if strong:
        w('Landings with the strongest crosswind component:')
        w('')
        w('| flight | date | airport | runway | wind | crosswind | gust |')
        w('|---|---|---|---|---|---|---|')
        for r in strong:
            w(f"| {r['flight']} | {r['date_local']} | {r['dest']} | {r['arr_rwy']} | "
              f"{wind_text(r['arr_wind_from'], r['arr_wind_kt'])} | {r['arr_crosswind_kt']:+.0f} kt | "
              f"{r['arr_gust_kt'] or '—'} |")
        w('')
    def real(code):
        """METAR 'M' is a missing field, not weather"""
        return code and code.strip() not in ('M', '')

    wx_events = [r for r in out if real(r['arr_wx']) or real(r['dep_wx'])]
    kinds = collections.Counter(
        ' / '.join(x for x in (('dep ' + r['dep_wx']) if real(r['dep_wx']) else '',
                               ('arr ' + r['arr_wx']) if real(r['arr_wx']) else '') if x)
        for r in wx_events)
    if wx_events:
        w(f'**{len(wx_events)} flights** took off or landed with weather actually in the report — '
          'these are the ones where conditions, not just traffic, were a factor:')
        w('')
        w('| condition | flights | examples |')
        w('|---|---|---|')
        for k, v in kinds.most_common(8):
            eg = [r for r in wx_events if ' / '.join(
                x for x in (('dep ' + r['dep_wx']) if real(r['dep_wx']) else '',
                            ('arr ' + r['arr_wx']) if real(r['arr_wx']) else '') if x) == k][:3]
            w(f"| `{k}` | {v} | " + ', '.join(f"{r['flight']} {r['date_local'][:5]} {r['origin']}-{r['dest']}"
                                              for r in eg) + ' |')
        w('')
    lowvis = [r for r in out if r['arr_vis_sm'] not in ('', None) and float(r['arr_vis_sm']) < 5]
    if lowvis:
        w(f'- **{len(lowvis)}** landings had visibility below 5 statute miles.')
        w('- ' + ', '.join(f"{r['flight']} {r['date_local'][:5]} {r['dest']} {float(r['arr_vis_sm']):.0f} SM"
                           for r in lowvis[:8]) + '.')
    hot = sorted({(r['flight'], r['date_local'], r['origin'], r['dep_temp_c'])
                  for r in ok_dep if r['dep_temp_c'] != ''}, key=lambda x: -float(x[3]))[:5]
    if hot:
        w('- Warmest departures — density altitude is the hidden variable on the long-roll days: '
          + ', '.join(f"{f} {d[:5]} {o} {t:.0f}°C" for f, d, o, t in hot) + '.')
    w('')

    # ------------------------------------------------- what the wind does to the numbers ---
    run = {r['file']: r for r in csv.DictReader(open('runway_usage.csv'))}
    w('## Does the wind show up in the measured distances?')
    w('')
    joined = []
    for r in out:
        u = run.get(r['file'], {})
        joined.append((r, u))

    def band(v, edges=(0, 5, 10, 15, 99)):
        for lo, hi in zip(edges, edges[1:]):
            if lo <= v < hi:
                return f'{lo}–{hi} kt' if hi < 99 else f'{lo}+ kt'
        return ''

    tail_of = {r['file']: r.get('tail', '') for r in run.values()}
    for side, col, label in (('dep', 'dep_roll_len_m', 'take-off run'),
                             ('arr', 'arr_roll_len_m', 'landing roll')):
        # control for aircraft type: compare each tail against its own calm-wind median,
        # otherwise the A330's long runs are read as a wind effect
        per_tail = collections.defaultdict(list)
        for r, u in joined:
            v, d = r[f'{side}_headwind_kt'], u.get(col)
            if v == '' or not d or float(d) <= 0:
                continue
            per_tail[(tail_of.get(r['file'], ''), float(v) >= 5)].append(float(d))
        deltas = []
        for t in {k[0] for k in per_tail if k[0]}:
            lo, hi = per_tail.get((t, False)), per_tail.get((t, True))
            if lo and hi:
                deltas.append((t, st.median(hi) - st.median(lo), len(hi), len(lo)))
        if deltas:
            w(f'**{label.capitalize()}, like for like** — each aircraft against its own median in winds '
              'below 5 kt (so the A330 cannot be mistaken for a wind effect):')
            w('')
            w('| tail | type | median change at 5 kt+ headwind | n (>=5 kt / <5 kt) |')
            w('|---|---|---|---|')
            for t, dd, n1, n0 in sorted(deltas, key=lambda x: x[1]):
                w(f'| {t} | {TYPE.get(t, "")} | {dd:+.0f} m | {n1} / {n0} |')
            w('')
            w(f'Mean change across the fleet: **{st.mean([d[1] for d in deltas]):+.0f} m**.')
            w('')
    # --------------------------------------------- do conditions show in the schedule? ---
    w('## Where the schedule stretched')
    w('')
    log = list(csv.DictReader(open(log_path())))
    cond = {r['file']: r for r in out}
    route_t = collections.defaultdict(list)
    for f in log:
        route_t[(f['origin'], f['dest'])].append(float(f['air_minutes']))
    slow = []
    for f in log:
        v = route_t[(f['origin'], f['dest'])]
        if len(v) < 6:
            continue
        med = st.median(v)
        m = float(f['air_minutes'])
        if m > med * 1.10:
            slow.append((m - med, m / med, f, med))
    slow.sort(key=lambda r: r[0], reverse=True)   # tuples hold dicts; never compare them
    if slow:
        w(f'{len(slow)} flights ran more than 10 % over the median for their own sector '
          f'(`flight_conditions.csv` carries the wind and weather for each):')
        w('')
        w('| flight | date | sector | air min | sector median | over | wind at departure | weather |')
        w('|---|---|---|---|---|---|---|---|')
        for over, ratio, f, med in slow[:12]:
            c = cond.get(f['source_file'], {})
            wx = ' / '.join(x for x in (c.get('dep_wx', ''), c.get('arr_wx', '')) if real(x)) or '—'
            wind = wind_text(c.get('dep_wind_from'), c.get('dep_wind_kt'))
            w(f"| {f['flight']} | {f['date_local'][:5]} | {f['origin']}-{f['dest']} | {float(f['air_minutes']):.0f} | "
              f"{med:.0f} | +{100 * (ratio - 1):.0f} % | {wind} | {wx} |")
        w('')
        flagged = [c for _, _, f, _ in slow if (c := cond.get(f['source_file'])) and
                   (real(c.get('dep_wx')) or real(c.get('arr_wx')))]
        w(f'Of those, **{len(flagged)} of {len(slow)}** had weather in the report at one end — '
          'so most of the stretch is traffic, sequencing or routeing, not the sky.')
        w('')
    w('')
    open(REPORT, 'w').write('\n'.join(L) + '\n')
    print(f'wrote {REPORT} ({len(L)} lines)')


if __name__ == '__main__':
    main()
