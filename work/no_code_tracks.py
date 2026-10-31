#!/usr/bin/env python3
"""Tracks that arrived without a flight code — where each one started and ended.

A track normally carries its code in the file name (`<FLIGHT>-<8 hex>.csv`). Two
things can be missing, and they are checked separately:

  * **no code in the name** — the file is `<8 hex>.csv`, so nothing ties the track
    to a flight number. The transmitted callsign may still be there.
  * **no callsign in the file** — every `Callsign` field is empty, so there is no
    flight number, no operator and nothing to attribute the track to.

A third, related class is reported because it has the same practical effect — the
track cannot enter the flight log:

  * **callsign outside the operator's series** — a code is present, but the
    transmitted callsign is not one of the operator's (`UGD…`/`UR…`/`UG…`), so the
    log builder skips it.

Every start and end is resolved from the first and last position in the track: the
nearest of the 39 operational airports is named, with its distance, and the full
OurAirports list (86k airports) is used to name anything outside that list.

Writes no_code_tracks.md.  Re-run after every build.

    PYTHONPATH=. python3 work/no_code_tracks.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout as RL
import month_ctx as MC
import apt_source   # the airport table, raw dump or published subset
import csv
import io
import math
import re
import sys
import zipfile
import datetime as dt

sys.path.insert(0, '/home/user')
import build_log as BL

P = RL.live_dir()          # this month's folder inside fr24_publish/
OUT = 'no_code_tracks.md'
ZIP = RL.archive()          # the month folder may hold its own copy; the root one is cumulative
NAME_RE = re.compile(r'^[A-Z]{2,3}\d+[A-Z]?-[0-9a-f]{8}\.csv$', re.I)
OPS = 'UGD|UR|UG'
SERIES_RE = re.compile(rf'^({OPS})\d+[A-Z]?$')


def hav(a, b, c, d):
    r = 3440.065
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def load_apts():
    out = []
    for r in apt_source.rows():
        try:
            out.append((r['ident'], r['name'], r['type'], r['iso_country'],
                        r.get('municipality', ''), float(r['latitude_deg']),
                        float(r['longitude_deg']), r.get('iata_code', '').strip()))
        except (ValueError, KeyError):
            pass
    return out


APTS = load_apts()


def name_place(lat, lon, k=2):
    """the operational list first (it is what the datasets use), then OurAirports"""
    code, d = BL.nearest_airport(lat, lon)
    near = sorted(((hav(lat, lon, a[5], a[6]), a) for a in APTS), key=lambda x: x[0])[:k]
    n = near[0][1]
    return code, d, n, near


def rows_of(z, name):
    raw = z.read(name).decode('utf-8', 'replace')
    return [r for r in list(csv.reader(io.StringIO(raw)))[1:] if len(r) >= 6]


def local(iso, code):
    t = dt.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ')
    off = BL.AIRPORTS.get(code, (0, 0, 0))[2]
    return (t + dt.timedelta(hours=off)).strftime('%d %b %H:%M')


def dlab(iso):
    t = dt.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ')
    return t.strftime('%d %b %Y')


def describe(z, name):
    rows = rows_of(z, name)
    out = {}
    for tag, r in (('first', rows[0]), ('last', rows[-1])):
        lat, lon = [float(x) for x in r[3].split(',')]
        code, d, n, near = name_place(lat, lon)
        out[tag] = dict(utc=r[1], code=code, d=d, oap=n, near=near,
                        lat=lat, lon=lon, alt=int(r[4]), spd=int(r[5]),
                        local=local(r[1], code))
    alts = [int(r[4]) for r in rows]
    out['fixes'] = len(rows)
    out['maxalt'] = max(alts)
    out['ground'] = sum(1 for a in alts if a == 0)
    return out


def place_str(p):
    ident, nm, typ, cc, mun, la, lo, iata = p['oap']
    tag = f"{p['code']}" + (f"/{iata}" if iata and iata != p['code'] else '')
    return (f"**{tag}** — {nm} ({ident}, {typ.replace('_', ' ')}, {cc}"
            f"{', ' + mun if mun else ''}), {p['d']:.0f} NM from the fix")


def main():
    z = zipfile.ZipFile(ZIP)
    names = sorted(n for n in z.namelist() if n.lower().endswith('.csv'))
    rows = []
    for full in names:
        base = full.split('/')[-1]
        r = rows_of(z, full)
        if not r:
            continue
        cs = sorted({x[2].strip() for x in r if x[2].strip()})
        rows.append(dict(file=base, full=full, cs=cs, r=r))

    no_code = [r for r in rows if not NAME_RE.match(r['file'])]
    no_cs = [r for r in rows if not r['cs']]
    off_series = [r for r in rows
                  if r['cs'] and not SERIES_RE.match(r['cs'][0])
                  and NAME_RE.match(r['file'])
                  and re.match(rf'^({OPS})\d', r['file'])]
    off_pat = [r for r in rows if r['cs'] and r['cs'][0].startswith('UGD')
               and not r['cs'][0][3:].isdigit() and r not in no_code]

    # the archive is one table shared by every month, so "is this track in the log?" has to be
    # asked of *every* published log: reading only the live month's folder once called a 29 Sep
    # track "not in the log" because the build happened to be running for October
    log = []
    for _lp in MC.logs_found():
        log += list(csv.DictReader(open(_lp)))
    logkeys = {(x['source_file'], x['flight']) for x in log}

    L = []
    w = L.append
    w('# Tracks that arrived without a flight code')
    w('')
    w(f'Every track in the archive carries its flight code in the file name, '
      f'`<FLIGHT>-<8 hex>.csv`. A few do not, and this is what each of them is — '
      f'start and end resolved from the first and last position in the track.')
    w('')
    w(f'Archive checked: **{len(rows)} tracks** (`{os.path.relpath(ZIP, RL.ROOT)}`).')
    w('')
    w('---')
    w('')
    w(f'## 1. Tracks whose name carries no code — {len(no_code)}')
    w('')
    if no_code:
        w('| file | callsign | date | started | ended | air time | fixes | in the log? |')
        w('|---|---|---|---|---|---|---|---|')
        for r in no_code:
            d1 = describe(z, r['full'])
            inlog = ', '.join(sorted({fl for f, fl in logkeys if f == r['file']})) or 'not in the log'
            dur = (dt.datetime.strptime(d1['last']['utc'], '%Y-%m-%dT%H:%M:%SZ')
                   - dt.datetime.strptime(d1['first']['utc'], '%Y-%m-%dT%H:%M:%SZ'))
            w(f"| `{r['file']}` | {r['cs'][0] if r['cs'] else '*(none)*'} | "
              f"{dlab(d1['first']['utc'])} | **{d1['first']['code']}** | **{d1['last']['code']}** | "
              f"{int(dur.total_seconds() // 60)} min | {d1['fixes']} | {inlog} |")
        w('')
        for r in no_code:
            d1 = describe(z, r['full'])
            w(f"### `{r['file']}` — {d1['first']['code']} → {d1['last']['code']}")
            w('')
            w(f"* **Callsign in the file**: "
              f"{', '.join('`' + c + '`' for c in r['cs']) if r['cs'] else '**empty on every row** — '
                 'no flight number, no operator'}")
            w(f"* **Started**: {place_str(d1['first'])} — {d1['first']['local']} local, "
              f"{d1['first']['utc']} UTC, on the ground, {d1['first']['alt']:,} ft, "
              f"{d1['first']['spd']} kt")
            w(f"* **Ended**: {place_str(d1['last'])} — {d1['last']['local']} local, "
              f"{d1['last']['utc']} UTC, {d1['last']['alt']:,} ft")
            w(f"* **Profile**: {d1['fixes']} fixes, {d1['ground']} of them on the ground, "
              f"highest {d1['maxalt']:,} ft")
            w(f"* **File**: `{r['file']}` — {len(z.read(r['full'])):,} bytes")
            # what the log shows for that airport pair on the same local day
            fmt = lambda y: f"`{y['flight']}` {y['origin']}→{y['dest']} " \
                            f"{y['takeoff_local'][:4]}–{y['arrival_local'][:4]} local"
            day = dt.datetime.strptime(d1['first']['utc'], '%Y-%m-%dT%H:%M:%SZ')
            dlocal = (day + dt.timedelta(hours=3)).strftime('%d%b%y').upper()   # EAT
            a, b = d1['first']['code'], d1['last']['code']
            leg = [x for x in log
                   if {x['origin'], x['dest']} == {a, b} and x['source_file'] != r['file']]
            same = sorted((x for x in leg if x['date_local'] == dlocal),
                          key=lambda y: y['departure_utc'])
            other = sorted((x for x in leg if x['date_local'] != dlocal),
                           key=lambda y: y['departure_utc'])
            if same:
                w(f"* **The same day's log on this pair** ({dlocal}): "
                  + '; '.join(fmt(x) for x in same[:6])
                  + (f' — this pair carries {len(other)} further legs on other days' if other else '') + '.')
                cross = [x for x in same
                         if {x['origin'], x['dest']} == {b, a} and abs(
                             (dt.datetime.strptime(x['departure_utc'], '%Y-%m-%d %H:%M:%SZ')
                              - day).total_seconds()) < 5400]
                if cross:
                    w(f"* **Two aircraft crossed the pair inside 90 minutes** — "
                      + '; '.join(fmt(x) for x in cross)
                      + f", against this track's {d1['first']['code']}→{d1['last']['code']} "
                        f"{d1['first']['local'][-5:]}–{d1['last']['local'][-5:]} local. That is what "
                        "an extra/positioning leg looks like in the data.")
            w('')
    else:
        w('*None.*')
        w('')

    w('---')
    w('')
    w(f'## 2. Tracks with no callsign at all — {len(no_cs)}')
    w('')
    for r in no_cs:
        d1 = describe(z, r['full'])
        w(f"* `{r['file']}` — {dlab(d1['first']['utc'])}, {d1['first']['code']} → "
          f"{d1['last']['code']}, {int(d1['fixes'])} fixes. Every `Callsign` field is empty, so "
          f"nothing in the file says who flew it or under what number.")
    if not no_cs:
        w('*None — every track carries a callsign.*')
    w('')

    w('---')
    w('')
    w(f'## 3. Coded tracks the log excludes: callsign outside the operator series — '
      f'{len(off_series)}')
    w('')
    if off_series:
        w('| file | callsign | date | started | ended | max alt |')
        w('|---|---|---|---|---|---|')
        for r in off_series:
            d1 = describe(z, r['full'])
            w(f"| `{r['file']}` | {r['cs'][0]} | {dlab(d1['first']['utc'])} | "
              f"**{d1['first']['code']}** | **{d1['last']['code']}** | {d1['maxalt']:,} ft |")
        w('')
        w('These are the Entebbe↔Hoima shuttles of 27 and 29 Sep 2026 — Kabalega '
          'International (`UG-0013`), which has no IATA or ICAO code yet. They are in the '
          'archive but not in the flight log, exactly as README §5 states.')
        w('')
        w('The 29 Sep leg is the only one that ends away from Entebbe with the aircraft still '
          'airborne — the track stops 10 NM short of Hoima at 10,225 ft, so its landing was not '
          'captured. The five on 27 Sep all show ground contact at both ends, and the first of '
          'them (06:39–07:44 UTC) is a local sortie: it takes off and lands at Entebbe without '
          'Hoima appearing at either end.')
        w('')
    else:
        w('*None.*')
        w('')

    if off_pat:
        w('---')
        w('')
        w(f'## 4. Operator flights whose callsign came out off-pattern — {len(off_pat)}')
        w('')
        w('These **did** arrive with a code in the file name, so they are logged normally; the '
          'transmitted callsign just does not follow the usual `UGD###` form. Each carries a '
          'letter suffix (`X`, `D`) after the number rather than the bare callsign. What that '
          'suffix signals is not recorded in this dataset — it is left as it was transmitted.')
        w('')
        w('The same pattern appears on the code-less track in section 1 (`UGD720X`), so the '
          'suffix is not the reason a track has no file code; the two things are independent.')
        w('')
        w('| file | callsign | date | started | ended |')
        w('|---|---|---|---|---|')
        for r in sorted(off_pat, key=lambda x: describe(z, x['full'])['first']['utc']):
            d1 = describe(z, r['full'])
            w(f"| `{r['file']}` | {r['cs'][0]} | {dlab(d1['first']['utc'])} | "
              f"{d1['first']['code']} | {d1['last']['code']} |")
        w('')

    w('---')
    w('')
    w('## What would close these out')
    w('')
    w(f"1. `41e29857.csv` can be renamed in the published archive to carry its code: "
      f"`UR720X-41e29857.csv`, following the `<FLIGHT>-<8 hex>.csv` convention (the operator's "
      f"own prefix with the callsign's number). The manifest would then show `UR720X` in its "
      f"`flight` column instead of an empty cell.")
    w(f"2. `3e02c7e0.csv` cannot be named from the data — no callsign means no flight number. "
      f"An FR24 flight record or an app page for Entebbe→Kigali on 22 Jan 2026 would name it.")
    w(f"3. **Settled, 2 Oct 2026: these are the operator's `UR523` Hoima legs**, flown under the "
      f"airline's `AF523` callsign — which is what the file names already say (`UR523-*.csv`) and "
      f"what the app pages show (5X-EQU and 5X-KDP, grey status). They stay out of the log while the "
      f"gate keys on the *transmitted* callsign; accepting `<FLIGHT>-` file names as well would add "
      f"these {len(off_series)} tracks to it, which is a build decision rather than a data gap.")
    w('')
    text = '\n'.join(L) + '\n'
    open(OUT, 'w').write(text)
    print(f'wrote {OUT}: {len(text)} bytes, {len(L)} lines')
    print(f'  no code in name : {len(no_code)}')
    print(f'  no callsign     : {len(no_cs)}')
    print(f'  off-series cs   : {len(off_series)}')
    print(f'  off-pattern op  : {len(off_pat)}')


if __name__ == '__main__':
    main()
