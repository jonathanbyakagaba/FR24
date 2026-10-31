#!/usr/bin/env python3
"""Infer the arrival and departure runway for every track in the published archive.

Method
------
1. airport      : the airport is taken from the aircraft's own position — the last
                  ground fix (< 500 ft) before the take-off, resp. the first ground
                  fix after the landing — matched against OurAirports (any airport
                  with a runway >= 4000 ft).  The flight-log label is kept alongside
                  for cross-checking only.
2. take-off roll = ground fixes (alt <= 150 ft, gs >= HEAD kt) at the departure
   landing roll = same at the arrival.  Direction of travel over the roll = runway
   heading; the rotation / touchdown point lies on the runway centreline.
3. Score every runway end on  heading error (deg) + cross-track distance (m)/60
   and take the best.
4. Fallback when the export is too coarse to capture a roll: the heading of the
   low-level fixes (climb-out / approach) is matched against the runway ends and
   the terminal ground position decides between parallels.  Flagged medium/low.

Output: runway_usage.csv  (one row per track)
"""
import csv, io, math, collections, zipfile, json, os, sys
import build_log as B
import apt_source   # the raw airport dump or the published subset, whichever is here

R = 6371000.0
HEAD = 25.0          # kt: at or above this the aircraft is rolling, not taxiing
MIN_RWY_FT = 4000    # ignore grass strips / airstrips in the airport match
CENTRELINE_FIXES = 'work/rwy/centreline_fixes.csv'   # reviewed corrections to published geometry


# ---------------------------------------------------------------- geometry ---
def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def dhead(a, b):
    return abs((a - b + 180) % 360 - 180)


def median(vals):
    v = sorted(vals)
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def median_angle(vals):
    """circular median: the value minimising the summed angular distance"""
    best, bs = vals[0], 1e9
    for v in vals:
        s = sum(dhead(v, w) for w in vals)
        if s < bs:
            best, bs = v, s
    return best % 360


def dist_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def xtrack(lat, lon, la1, lo1, la2, lo2):
    """distance (m) from a point to a runway centreline segment"""
    mlat = math.radians((la1 + la2) / 2)

    def xy(la, lo):
        return ((lo - lo1) * math.cos(mlat) * 111320.0, (la - la1) * 110540.0)
    px, py = xy(lat, lon)
    bx, by = xy(la2, lo2)
    t = 0.0 if (bx * bx + by * by) == 0 else max(0.0, min(1.0, (px * bx + py * by) / (bx * bx + by * by)))
    return math.hypot(px - t * bx, py - t * by)


# ---------------------------------------------------------------- airports ---
def load_airports():
    """ident -> dict(lat, lon, name, iata, runways=[{ident,hdg,lat,lon,olat,olon}])"""
    good = set()
    for r in csv.DictReader(open('work/rwy/runways.csv')):
        try:
            if r['closed'] == '1' or not r['le_latitude_deg'] or not r['he_latitude_deg']:
                continue
            if float(r['length_ft'] or 0) < MIN_RWY_FT:
                continue
        except ValueError:
            continue
        good.add(r['airport_ident'])
    apts, runways = {}, collections.defaultdict(list)
    for a in apt_source.rows():
        ident = a['ident']
        if ident not in good or not a['latitude_deg'] or not a['longitude_deg']:
            continue
        apts[ident] = dict(ident=ident, lat=float(a['latitude_deg']), lon=float(a['longitude_deg']),
                           name=a['name'], iata=(a['iata_code'] or '').strip().upper(),
                           type=a['type'], elev=float(a['elevation_ft'] or 0))
    for r in csv.DictReader(open('work/rwy/runways.csv')):
        if r['airport_ident'] not in apts or r['closed'] == '1':
            continue
        try:
            if r['length_ft'] and float(r['length_ft']) < MIN_RWY_FT:
                continue
        except ValueError:
            continue
        other = 'he' if r['le_ident'] else 'le'
        if not (r['le_latitude_deg'] and r['he_latitude_deg'] and r['le_heading_degT'] and r['he_heading_degT']):
            continue
        for end in ('le', 'he'):
            try:
                lat, lon = float(r[f'{end}_latitude_deg']), float(r[f'{end}_longitude_deg'])
                hdg = float(r[f'{end}_heading_degT'])
            except (ValueError, KeyError):
                continue
            try:
                olat, olon = (float(r[f'{"he" if end == "le" else "le"}_latitude_deg']),
                              float(r[f'{"he" if end == "le" else "le"}_longitude_deg']))
            except ValueError:
                continue
            try:
                width_ft = float(r['width_ft'] or 0)
            except ValueError:
                width_ft = 0.0
            runways[r['airport_ident']].append(dict(ident=r[f'{end}_ident'], hdg=hdg, lat=lat, lon=lon,
                                                    olat=olat, olon=olon,
                                                    length_ft=float(r['length_ft'] or 0),
                                                    width_ft=width_ft))
    # ---- corrected centrelines ------------------------------------------------
    # Where the published coordinates are demonstrably not the physical runway, a
    # reviewed correction in `work/rwy/centreline_fixes.csv` replaces them here, so
    # every measurement in this pipeline (and any future run) uses the corrected
    # line without needing a fit.  See work/fix_centreline.py for how each row was
    # derived and corroborated.
    fixed = 0
    if os.path.exists(CENTRELINE_FIXES):
        for f in csv.DictReader(open(CENTRELINE_FIXES)):
            for r in runways.get(f['airport'], []):
                if r['ident'] != f['ident']:
                    continue
                r['lat'], r['lon'] = float(f['thr_lat']), float(f['thr_lon'])
                r['olat'], r['olon'] = float(f['far_lat']), float(f['far_lon'])
                r['hdg'] = float(f['heading_degT'])
                r['fixed'] = f['source']
                r['fixed_evidence'] = f['evidence']
                fixed += 1
    # 1-degree grid for nearest-airport lookups
    grid = collections.defaultdict(list)
    for ap in apts.values():
        grid[(int(ap['lat']), int(ap['lon']))].append(ap)
    return apts, runways, grid


def nearest_airport(apts, grid, lat, lon, max_km=30.0):
    """nearest airport with a >=4000 ft runway; None if further than max_km"""
    gx, gy = int(lat), int(lon)
    best, bd = None, 1e18
    for rad in range(0, 4):
        for i in range(gx - rad, gx + rad + 1):
            for j in range(gy - rad, gy + rad + 1):
                if rad and max(abs(i - gx), abs(j - gy)) != rad:
                    continue
                for ap in grid.get((i, j), ()):
                    d = dist_m(lat, lon, ap['lat'], ap['lon'])
                    if d < bd:
                        best, bd = ap, d
        if best and bd <= (rad + 1) * 111000:      # no closer cell can win
            break
    if best is None or bd > max_km * 1000:
        return None, bd
    return best, bd


# ------------------------------------------------------------------ tracks ---
def parse_track(raw):
    out = []
    for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig', errors='replace'))):
        try:
            lat, lon = (float(x) for x in r['Position'].split(','))
            out.append((float(r['Timestamp']), lat, lon, float(r['Altitude'] or 0),
                        float(r['Speed'] or 0), float(r['Direction'] or 0)))
        except (ValueError, KeyError, AttributeError):
            continue
    out.sort()
    return out



# ------------------------------------------------------------------ tracks ---
GROUND_FT = 5.0      # Altitude reads 0 on the ground (any airport) and MSL in the air
ROLL_KT = 15.0       # below this the aircraft is not yet rolling for take-off
STOP_KT = 3.0        # effectively stopped
CORRIDOR_M = 150.0   # lateral tolerance when fitting a track to a runway centreline


def ground_run_at(rows, idx):
    """Indices of the contiguous ground run (altitude reads 0) containing `idx`.

    FR24 reports Altitude as 0 while the aircraft is on the ground and as the MSL
    altitude in the air, at every airport - including those at 5,000-7,600 ft - so
    this separates rolling from flying cleanly.  Returns [] if `idx` is not a
    ground fix."""
    n = len(rows)
    if not (0 <= idx < n) or rows[idx][3] > GROUND_FT:
        return []
    a = idx
    while a > 0 and rows[a - 1][3] <= GROUND_FT:
        a -= 1
    b = idx
    while b + 1 < n and rows[b + 1][3] <= GROUND_FT:
        b += 1
    return list(range(a, b + 1))


def roll_runs(rows, elev=0.0, min_kt=55.0):
    """Contiguous stretches that could be a take-off / landing roll.

    Altitude cannot separate rolling from flying near a high-elevation field (the
    readings sit on the field elevation either way), so the roll is delimited by
    "low altitude for this airport" plus speed: a run must contain a fix at or
    above min_kt.  An index gap breaks a run.  This is used to find the roll for
    runway matching; the roll *metrics* use the sharper signatures below."""
    gmax = max(elev + 200.0, 200.0)
    keep = [(i, r) for i, r in enumerate(rows) if r[3] <= gmax and r[4] >= HEAD]
    runs, cur = [], []
    for i, r in keep:
        if cur and i - cur[-1][0] > 1:
            runs.append(cur); cur = []
        cur.append((i, r))
    if cur:
        runs.append(cur)
    return [ru for ru in runs if max(x[4] for (_, x) in ru) >= min_kt]


def run_heading(run):
    first, last = run[0][1], run[-1][1]
    brg = bearing(first[1], first[2], last[1], last[2])
    dirs = [x[5] for (_, x) in run if x[5] > 0]
    hdg = median_angle(dirs) if dirs else brg
    spread = max([dhead(d, hdg) for d in dirs], default=0.0)
    return hdg, brg, spread


def perp_along(lat, lon, rw):
    """Signed distance from the runway centreline (m, + = right of the direction of
    travel) and distance from the threshold actually used (m, along the runway)."""
    mlat = math.radians((rw['lat'] + rw['olat']) / 2)
    ux = (rw['olon'] - rw['lon']) * math.cos(mlat) * 111320.0
    uy = (rw['olat'] - rw['lat']) * 110540.0
    L = math.hypot(ux, uy)
    if L == 0:
        return 0.0, 0.0
    ux, uy = ux / L, uy / L
    px = (lon - rw['lon']) * math.cos(mlat) * 111320.0
    py = (lat - rw['lat']) * 110540.0
    return px * uy - py * ux, px * ux + py * uy


def fit_centreline(pts):
    """Fit  cross = a + b*along  to ground-roll fixes (all flights at that runway end).

    The fixes are physically on the pavement, so the fitted line is the centreline
    as the fleet actually rolled on it.  Two rounds of 3-sigma trimming keep a
    stray fix from bending it.  Returns (a, b, n_fixes, sd_of_residuals)."""
    pts = list(pts)
    if len(pts) < 25:
        return None
    sd = 0.0
    for _ in range(2):
        n = len(pts)
        sx = sum(x for x, _ in pts); sy = sum(y for _, y in pts)
        sxx = sum(x * x for x, _ in pts); sxy = sum(x * y for x, y in pts)
        den = n * sxx - sx * sx
        if den == 0:
            return None
        b = (n * sxy - sx * sy) / den
        a = (sy - b * sx) / n
        res = [y - (a + b * x) for x, y in pts]
        sd = (sum(r * r for r in res) / n) ** 0.5
        keep = [(x, y) for (x, y), r in zip(pts, res) if abs(r) <= 3 * max(sd, 1.0)]
        if len(keep) == n:
            break
        pts = keep
    return dict(a=a, b=b, n=len(pts), sd=sd, rot_deg=math.degrees(math.atan(b)))


# ------------------------------------------------- take-off / landing rolls ---
def descent_rate_fpm(a, b):
    """altitude trend between two fixes, ft/min (0 if unknown)"""
    dt = b[0] - a[0]
    if dt <= 0:
        return 0.0
    return (b[1] - a[1]) / dt * 60.0


def accel_kt_s(a, b):
    dt = b[0] - a[0]
    return (b[4] - a[4]) / dt if dt > 0 else 0.0


def _r(v):
    """Round a measured distance, or leave the cell blank when the window held no fix at or
    beyond the marker: the `''` that `next(..., '')` falls back to is not a measurement, and
    61 new tracks on 07-10 Oct were enough to reach that path (a departure whose whole capture
    window sits before `lo`)."""
    return round(v) if isinstance(v, (int, float)) else ''


def dep_roll(rows, seg, rw, apt_elev=0.0, run=None):
    """Take-off: line-up point, wheel-off bracket, roll length, runway used/remaining.

    Two independent signatures locate the moment the wheels leave the runway:

    * acceleration - the roll runs at 3-5 kt/s; once the aircraft pitches up to
      climb, the acceleration drops to about half.
    * altitude     - the FR24 altitude field only reports MSL above roughly 100 kt
      of ground speed (it is 0 below that), so it is only useful late in a heavy
      take-off; where it is available it sits on the field-elevation baseline
      while rolling and climbs away from it once airborne.

    Both give an interval between two fixes, so the answer is a bracket.  The
    altitude break is taken as the answer (it is the direct marker of leaving the
    ground); the acceleration break is kept alongside as `accel_alt_ft`, the
    altitude at which the second signature fired, which normally lags it.
    """
    L = dist_m(rw['lat'], rw['lon'], rw['olat'], rw['olon'])
    gidx = [i for (i, _) in seg]
    # start 40 fixes before the roll: the roll run only contains fixes >= HEAD kt,
    # so the line-up / brake release sits just outside it
    i0 = max(0, (run[0][0] if run else gidx[0]) - 40)
    i1 = min(len(rows) - 1, gidx[-1] + 6)
    on = [(i, rows[i]) + perp_along(rows[i][1], rows[i][2], rw) for i in range(i0, i1 + 1)]
    on = [p for p in on if abs(p[2]) <= CORRIDOR_M and -250 <= p[3] <= L + 400]
    if len(on) < 2:
        return None
    # ---- roll start: the first fix after the last sub-ROLL_KT fix
    last_slow = None
    for k, p in enumerate(on[:-1]):
        if p[1][4] < ROLL_KT:
            last_slow = k
    start, capture = (on[last_slow + 1], 'full') if last_slow is not None \
        else (on[0], 'no stop captured (rolling take-off)')
    # window: the roll plus a few fixes beyond it (the wheels-off may sit outside
    # the ground run, since the ground run ends where the altitude field starts)
    hi_i = min(len(rows) - 1, on[-1][0] + 6)
    win = [(i, rows[i]) + perp_along(rows[i][1], rows[i][2], rw)
           for i in range(start[0], hi_i + 1)]
    win = [p for p in win if abs(p[2]) <= CORRIDOR_M and -250 <= p[3] <= L + 400]
    # ---- signature A: acceleration drop
    acc = []
    for k in range(len(win) - 3):
        acc.append((win[k], accel_kt_s(win[k][1], win[k + 3][1])))
    brk_a = None
    k_last_fast = None
    for k, (p, a) in enumerate(acc):
        if a >= 2.5:
            k_last_fast = k
        elif k_last_fast is not None and a <= 1.5:
            brk_a = (acc[k_last_fast][0][3], acc[k][0][3])
            break
    # ---- signature B: altitude leaves the rolling baseline
    valid = [p for p in win if p[1][3] > GROUND_FT and p[3] >= start[3]]
    base = None
    brk_b = None
    if len(valid) >= 4:
        m = min(p[1][3] for p in valid)
        if apt_elev and abs(m - apt_elev) <= 500:    # sanity: readings sit near this field
            base = m
        for k in range(3, len(valid)):
            local = min(p[1][3] for p in valid[k - 3:k])
            nxt = valid[k + 1][1][3] if k + 1 < len(valid) else valid[k][1][3]
            if valid[k][1][3] >= local + 100 and nxt >= valid[k][1][3] - 75:
                brk_b = (valid[k - 1][3], valid[k][3])
                break
    # ---- combine: the altitude trend is the direct signal (it marks leaving the
    # ground); the acceleration gives a second opinion that is reported alongside
    accel_alt = None
    if brk_a:            # second opinion, kept as a column (it normally lags the alt break)
        accel_alt = min(p[1][3] for p in win if min(brk_a) <= p[3] <= max(brk_a)) or win[-1][1][3]
    if brk_b:
        lo, hi, src = min(brk_b), max(brk_b), 'altitude'
    elif brk_a:
        lo, hi, src = min(brk_a), max(brk_a), 'acceleration'
    else:
        cand = [p for p in on if 35 <= p[1][4] < 95 and p[3] >= start[3] - 50]
        if not cand:
            return None
        p = cand[-1]
        lo = hi = p[3]
        src = 'speed fallback (below the altitude-valid speed)'
        capture += ' / no wheel-off signature'
    along = (lo + hi) / 2
    wo_speed = next((p[1][4] for p in win if p[3] >= lo), '')
    wo_cross = next((p[2] for p in win if p[3] >= lo), '')
    return dict(roll_start=round(start[3]), start_speed=start[1][4],
                accel_alt_ft=round(accel_alt) if accel_alt else '',
                along=round(along), along_lo=round(lo), along_hi=round(hi),
                bracket=round(hi - lo), speed=wo_speed, base=base, source=src,
                roll_len=round(along - start[3]), remaining=round(L - along),
                capture=capture, xt=_r(wo_cross))


def arr_roll(rows, seg, rw, halfw, run=None):
    """Landing: threshold crossing, touchdown bracket, roll, turn-off, runway used.

    Touchdown is located from the deceleration: the approach runs at roughly
    constant speed, then spoilers, brakes and reverse bring it down fast.  The
    first fix with a sustained deceleration past the threshold therefore sits at
    (or a second or two after) the moment of touchdown; the bracket is the fix
    before it.  The point where the altitude trend flattens is reported too - it
    lags the touchdown by a few seconds and is only a cross-check.
    """
    L = dist_m(rw['lat'], rw['lon'], rw['olat'], rw['olon'])
    gidx = [i for (i, _) in seg]
    allp = [(i, rows[i]) + perp_along(rows[i][1], rows[i][2], rw) for i in range(len(rows))]
    if run:
        i1 = max(i for (i, _) in run)
    else:
        i1 = gidx[-1]
    near = [p for p in allp if p[0] <= i1 + 4 and -3000 <= p[3] <= L + 500 and abs(p[2]) <= 800]
    # ---- threshold crossing (interpolated)
    thr = None
    for a, b in zip(near, near[1:]):
        if a[3] < 0 <= b[3] and b[0] - a[0] <= 4:
            f = (0 - a[3]) / (b[3] - a[3]) if b[3] != a[3] else 0.0
            thr = dict(speed=a[1][4] + f * (b[1][4] - a[1][4]),
                       height=a[1][3] + f * (b[1][3] - a[1][3]))
            break
    # ---- touchdown bracket from the deceleration
    td_a = None
    w = [p for p in near if p[3] > -50]
    for k in range(len(w) - 1):
        p = w[k]
        if p[3] < 60 or p[1][4] < 60:
            continue
        j = min(k + 3, len(w) - 1)
        dt = w[j][1][0] - p[1][0]
        if dt > 0 and (w[j][1][4] - p[1][4]) / dt <= -1.8 and w[k + 1][1][4] < p[1][4] + 1:
            td_a = (w[k - 1][3] if k else p[3], p[3])
            break
    # ---- cross-check: where the altitude trend flattens
    alt_flat = None
    va = [p for p in near if p[1][3] > GROUND_FT and p[3] > 0]
    for k in range(len(va) - 1):
        dt = va[k + 1][1][0] - va[k][1][0]
        if dt <= 0:
            continue
        if (va[k + 1][1][3] - va[k][1][3]) / dt * 60.0 >= -150:
            alt_flat = va[k][3]
            break
    if td_a is None:
        p = next((p for p in near if p[0] == gidx[0]), None)
        if p is None:
            return None
        td_lo = td_hi = p[3]
        capture = 'no deceleration captured (coarse export)'
    else:
        td_lo, td_hi = min(td_a), max(td_a)
        capture = 'full'
    td_along = (td_lo + td_hi) / 2
    # ---- turn-off: the aircraft centre crosses the runway edge
    after = [p for p in allp if p[0] >= (next((q[0] for q in near if q[3] >= td_hi), gidx[0]))]
    ex = next((p for p in after if abs(p[2]) > halfw + 10), None)
    if ex is None:
        ex = after[-1]
        capture += ' / track ends on the runway (roll is a lower bound)'
    stop = next((p for p in after if p[1][4] <= STOP_KT), None)
    td_speed = next((p[1][4] for p in near if p[3] >= td_lo), '')
    td_cross = next((p[2] for p in near if p[3] >= td_lo), '')
    return dict(thr_speed=round(thr['speed']) if thr else '',
                thr_height=round(thr['height']) if thr else '',
                td_lo=round(td_lo), td_hi=round(td_hi), td_along=round(td_along),
                td_bracket=round(td_hi - td_lo), td_speed=td_speed,
                alt_flat_m=round(alt_flat) if alt_flat is not None else '',
                roll_len=round(ex[3] - td_along), used=round(ex[3]),
                remaining=round(L - ex[3]), end_speed=ex[1][4],
                stop_along=round(stop[3]) if stop else '',
                capture=capture, xt=_r(td_cross),
                track=[(p[1][0], p[3], p[2], p[1][4]) for p in after])


def match_runway(rwys, run, where):
    """Match a ground run against every runway end.

    For each runway we take the longest contiguous stretch of fixes lying within
    150 m of its centreline that contains a real roll fix (>= 55 kt), score it on
    mean cross-track + 20 m per degree of heading error, and prefer stretches
    close to the take-off (where='dep') resp. touchdown (where='arr') end of the
    run.  Returns (best_dict, margin) or (None, 0)."""
    if not rwys or len(run) < 2:
        return None, 0.0
    cands = []
    for r in rwys:
        cts = [xtrack(p[1], p[2], r['lat'], r['lon'], r['olat'], r['olon']) for (_, p) in run]
        i, n = 0, len(run)
        while i < n:
            if abs(cts[i]) > 150:
                i += 1
                continue
            j = i
            while j + 1 < n and abs(cts[j + 1]) <= 150:
                j += 1
            seg = run[i:j + 1]
            if len(seg) >= 2 and max(p[4] for (_, p) in seg) >= 55:
                dirs = [p[5] for (_, p) in seg if p[5] > 0]
                geo = bearing(seg[0][1][1], seg[0][1][2], seg[-1][1][1], seg[-1][1][2])
                hdg = median_angle(dirs) if len(dirs) >= 2 else geo
                dh = dhead(hdg, r['hdg'])
                pos = seg[-1][0] if where == 'dep' else seg[0][0]
                pen = 2.0 * ((pos - run[0][0]) if where == 'dep' else (run[-1][0] - pos))
                mct = sum(abs(c) for c in cts[i:j + 1]) / len(seg)
                cands.append(dict(score=mct + 20.0 * dh + pen, rwy=r['ident'], mean_xtrack_m=mct,
                                  hdg_err=dh, n=len(seg), hdg=hdg, brg=geo, i0=i, i1=j,
                                  gi0=seg[0][0], gi1=seg[-1][0], rw=r))
            i = j + 1
    if not cands:
        return None, 0.0
    cands.sort(key=lambda c: c['score'])
    best = cands[0]
    # margin: how much better than the best candidate that is a *different* runway
    others = [c['score'] for c in cands if c['rwy'] != best['rwy']]
    margin = round(min(others) - best['score'], 1) if others else 999.0
    best['mean_xtrack_m'] = round(best['mean_xtrack_m'])
    best['hdg_err'] = round(best['hdg_err'], 1)
    best['hdg'] = round(best['hdg'], 1)
    best['brg'] = round(best['brg'], 1)
    best['margin'] = margin
    return best, margin


def pick_runway(rwys, points, hdg=None):
    """score every runway end on mean cross-track of `points` (m) + 20 m per degree

    Also reports how the runner-up differs (parallel strip or a genuinely
    different direction) so the caller can tell what evidence decided it."""
    scored = []
    for r in rwys:
        ct = sum(xtrack(p[1], p[2], r['lat'], r['lon'], r['olat'], r['olon']) for p in points) / len(points)
        dh = dhead(hdg, r['hdg']) if hdg is not None else 0.0
        scored.append((ct + 20.0 * dh, ct, dh, r))
    if not scored:
        return None, 0.0
    scored.sort(key=lambda s: s[0])
    s0 = scored[0]
    other = [x for x in scored[1:] if x[3]['ident'] != s0[3]['ident']]
    margin = round(other[0][0] - s0[0], 1) if other else 999.0
    # is the closest competing runway end a parallel strip (same heading, other side)?
    par = [x for x in other if dhead(x[3]['hdg'], s0[3]['hdg']) < 30]
    return dict(rwy=s0[3]['ident'], mean_xtrack_m=round(s0[1]), hdg_err=round(s0[2], 1),
                margin=margin, parallel_rival=bool(par),
                rival_xt=round(min(x[1] for x in par)) if par else ''), margin


# -------------------------------------------------------------------- main ---


def lined_up(rwys, rows, side):
    """Runway call for a track that starts or ends in the air, near the field.

    When the export begins just after the rotation (or ends on short final) there is
    no ground fix to anchor on.  What there is, is geometry: the aircraft is low,
    close to the field, and lined up with one particular runway, so its position and
    ground track pick that runway out directly.  Returns a result shaped like
    `pick_runway` (no `seg`, so no roll metrics are produced from it)."""
    n = len(rows)
    win = rows[:max(12, int(n * 0.4))] if side == 'dep' else rows[min(n - 4, int(n * 0.6)):]
    cand = [r for r in win if GROUND_FT < r[3] and r[3] <= 3000
            and min(dist_m(r[1], r[2], w['lat'], w['lon']) for w in rwys) < 12000]
    if not cand:
        return None
    a0 = min(cand, key=lambda r: r[3])                    # lowest fix = closest to lined up
    # heading over a long baseline, not from the instantaneous track field (which is
    # noisy at low speed and swings through any gentle turn): the bearing from the
    # anchor to the fix ~2 km away along the direction of travel
    far = None
    for r in (win if side == 'dep' else list(reversed(win))):
        d = dist_m(a0[1], a0[2], r[1], r[2])
        if (r[0] > a0[0] if side == 'dep' else r[0] < a0[0]) and 800 <= d <= 6000:
            far = r if far is None or abs(d - 2000) < abs(dist_m(a0[1], a0[2], far[1], far[2]) - 2000) else far
    if far is not None:
        hdg = bearing(a0[1], a0[2], far[1], far[2]) if side == 'dep' else bearing(far[1], far[2], a0[1], a0[2])
    else:
        dirs = [r[5] for r in win if r[5] > 60]
        hdg = median_angle(dirs[-5:] if side == 'arr' else dirs[:5]) if len(dirs) >= 2 else None
    best = None
    for w in rwys:
        c, a = perp_along(a0[1], a0[2], w)
        if not (-6500 <= a <= 400 if side == 'arr' else -400 <= a <= 6500):
            continue
        if abs(c) > 600:
            continue
        dh = dhead(hdg, w['hdg']) if hdg is not None else 0.0
        if dh > 30:
            continue
        score = abs(c) / 4.0 + 20.0 * dh
        best = best if best and best[0] <= score else (score, w, c, a, dh)
    if not best:
        return None
    score, w, c, a, dh = best
    others = []
    for o in rwys:
        if o['ident'] == w['ident']:
            continue
        c2, a2 = perp_along(a0[1], a0[2], o)
        if abs(c2) > 1500:
            continue
        dh2 = dhead(hdg, o['hdg']) if hdg is not None else 0.0
        others.append(abs(c2) / 4.0 + 20.0 * dh2)
    margin = round(min(others) - score, 1) if others else 999.0
    ok = abs(c) <= 200 and dh <= 15 and margin >= 150
    par = [o for o in rwys if o['ident'] != w['ident'] and abs(dhead(hdg, o['hdg']) if hdg is not None else 99) < 30]
    return dict(rwy=w['ident'], mean_xtrack_m=round(abs(c)), hdg_err=round(dh, 1),
                margin=margin, parallel_rival=bool(par), rival_xt='',
                hdg=round(hdg, 1) if hdg is not None else '',
                n=1, along_m=round(a), conf='medium' if ok else 'low')


def infer(rows, rwys_dep, rwys_arr, elev_dep=0.0, elev_arr=0.0):
    """Which runway end was used, from the roll itself (positions, not altitude)."""
    out = [None, None]
    if len(rows) < 4:
        return out
    runs = roll_runs(rows, max(elev_dep, elev_arr))
    # ---- departure -----------------------------------------------------
    if rwys_dep:
        cand = [ru for ru in runs if ru[0][0] <= max(6, len(rows) * 0.35)
                and min(dist_m(ru[-1][1][1], ru[-1][1][2], w['lat'], w['lon']) for w in rwys_dep) < 20000]
        best = None
        for ru in cand:
            res, margin = match_runway(rwys_dep, ru, 'dep')
            if not res:
                continue
            conf = ('high' if res['mean_xtrack_m'] <= 70 and res['hdg_err'] <= 10
                    and res['n'] >= 3 and margin >= 150
                    else 'medium' if res['mean_xtrack_m'] <= 150 and res['hdg_err'] <= 20 else 'low')
            if best is None or (conf == 'high' and best['conf'] != 'high'):
                best = dict(res, method='roll', conf=conf, seg=ru[res['i0']:res['i1'] + 1], run=ru)
        out[0] = best
    if out[0] is None and rwys_dep:
        # Fallback: the roll was not captured.  Use the climb-out direction with an
        # anchor on the airport; with no anchor the runway cannot be placed.
        near = lambda r, km: min(dist_m(r[1], r[2], w['lat'], w['lon']) for w in rwys_dep) < km * 1000
        ground = [r for r in rows[:max(8, int(len(rows) * 0.35))] if r[3] <= GROUND_FT and near(r, 20)]
        air = [r for r in rows[:max(12, int(len(rows) * 0.45))] if r[3] > 50 and near(r, 8)]
        if ground and len(air) >= 1:
            a0 = ground[-1]
            dirs = [r[5] for r in air if r[5] > 0]
            far = air[-1]
            hdg = median_angle(dirs) if len(dirs) >= 2 else bearing(a0[1], a0[2], far[1], far[2])
            res, margin = pick_runway(rwys_dep, [a0], hdg)
            if res:
                ok = res['hdg_err'] <= 12 and margin >= 150
                if ok and res['parallel_rival'] and res['mean_xtrack_m'] > 400:
                    ok = False
                out[0] = dict(res, method='climb-heading', hdg=round(hdg, 1), n=len(air),
                              conf='medium' if ok else 'low')
        if out[0] is None:
            res = lined_up(rwys_dep, rows, 'dep')
            if res:
                out[0] = dict(res, method='climb-alignment')
    # ---- arrival -------------------------------------------------------
    if rwys_arr:
        cand = [ru for ru in runs if ru[-1][0] >= min(len(rows) - 4, len(rows) * 0.65)
                and min(dist_m(ru[0][1][1], ru[0][1][2], w['lat'], w['lon']) for w in rwys_arr) < 20000]
        best = None
        for ru in reversed(cand):
            res, margin = match_runway(rwys_arr, ru, 'arr')
            if not res:
                continue
            conf = ('high' if res['mean_xtrack_m'] <= 70 and res['hdg_err'] <= 10
                    and res['n'] >= 3 and margin >= 150
                    else 'medium' if res['mean_xtrack_m'] <= 150 and res['hdg_err'] <= 20 else 'low')
            if best is None or (conf == 'high' and best['conf'] != 'high'):
                best = dict(res, method='roll', conf=conf, seg=ru[res['i0']:res['i1'] + 1], run=ru)
        out[1] = best
    if out[1] is None and rwys_arr:
        j = min(len(rows) - 4, int(len(rows) * 0.65))
        near = lambda r, km: min(dist_m(r[1], r[2], w['lat'], w['lon']) for w in rwys_arr) < km * 1000
        ground = [r for r in rows[j:] if r[3] <= GROUND_FT and near(r, 20)]
        air = [r for r in rows[j:] if r[3] > 50 and near(r, 8)]
        if ground and len(air) >= 1:
            a0 = ground[0]
            dirs = [r[5] for r in air if r[5] > 0]
            hdg = median_angle(dirs) if len(dirs) >= 2 else bearing(air[0][1], air[0][2], a0[1], a0[2])
            res, margin = pick_runway(rwys_arr, [a0], hdg)
            if res:
                ok = res['hdg_err'] <= 12 and margin >= 150
                if ok and res['parallel_rival'] and res['mean_xtrack_m'] > 400:
                    ok = False
                out[1] = dict(res, method='approach-heading', hdg=round(hdg, 1), n=len(air),
                              conf='medium' if ok else 'low')
        if out[1] is None:
            res = lined_up(rwys_arr, rows, 'arr')
            if res:
                out[1] = dict(res, method='approach-alignment')
    return out


# -------------------------------------------------------------------- main ---
def main(zip_path='fr24_publish/FR data.zip', out='runway_usage.csv'):
    apts, runways, grid = load_airports()
    print(f'airports indexed        : {len(apts)}')
    applied = [r for rl in runways.values() for r in rl if r.get('fixed')]
    if applied:
        print('corrected centrelines   : ' + ', '.join(f"{r['ident']} ({r['fixed']})" for r in applied))
    z = zipfile.ZipFile(zip_path)
    meta = {}
    for mo in [f'{y}-{m:02d}' for y in (2025, 2026) for m in range(1, 13)]:
        fl, _ = B.build(zip_path, mo)
        for f in fl:
            meta[f['name']] = f
    rows_out = []
    roll_pts = collections.defaultdict(list)      # (apt, rwy) -> [[(along, cross), ...], ...]
    arr_tracks = {}                               # file -> arrival roll track, for the calibrated pass
    for name in sorted(z.namelist()):
        if not name.endswith('.csv') or '/' in name:
            continue
        rows = parse_track(z.read(name))
        if len(rows) < 4:
            continue
        f = meta.get(name)
        # ---- airport from the aircraft's own position ---------------------
        lo_dep = [r for r in rows[:max(8, int(len(rows) * 0.25))] if r[3] <= 500 or r[4] <= 30]
        lo_arr = [r for r in rows[-max(8, int(len(rows) * 0.25)):] if r[3] <= 500 or r[4] <= 30]
        pdep = lo_dep[-1] if lo_dep else rows[0]
        parr = lo_arr[0] if lo_arr else rows[-1]
        ap_dep, d_dep = nearest_airport(apts, grid, pdep[1], pdep[2])
        ap_arr, d_arr = nearest_airport(apts, grid, parr[1], parr[2])

        def on_ground(window, ap):
            if not ap:
                return ''
            for r in window:
                if (r[3] <= GROUND_FT or r[4] <= 30) and dist_m(r[1], r[2], ap['lat'], ap['lon']) < 5000:
                    return 'yes'
            return 'no'

        dep_ground = on_ground(rows[:max(4, int(len(rows) * 0.25))], ap_dep)
        arr_ground = on_ground(rows[-max(4, int(len(rows) * 0.25)):], ap_arr)
        ed = ap_dep['elev'] if ap_dep else 0.0
        ea = ap_arr['elev'] if ap_arr else 0.0
        res = infer(rows, runways[ap_dep['ident']] if ap_dep else [],
                    runways[ap_arr['ident']] if ap_arr else [], ed, ea)
        dep, arr = res[0], res[1]

        dm = am = None
        if dep and dep.get('seg'):
            rw = next(r for r in runways[ap_dep['ident']] if r['ident'] == dep['rwy'])
            dm = dep_roll(rows, dep['seg'], rw, ed, dep.get('run'))
            dep['rwy_len_m'] = round(dist_m(rw['lat'], rw['lon'], rw['olat'], rw['olon']))
            dep['rwy_width_m'] = round(rw['width_ft'] * 0.3048) if rw.get('width_ft') else ''
            cut = dm['along_lo'] if dm else 10 ** 9
            roll_pts[(ap_dep['ident'], dep['rwy'])].append(
                [(a, c) for (_, x) in dep['seg'] for c, a in [perp_along(x[1], x[2], rw)] if a <= cut])
        if arr and arr.get('seg'):
            rw = next(r for r in runways[ap_arr['ident']] if r['ident'] == arr['rwy'])
            halfw = (rw['width_ft'] * 0.3048 / 2) if rw.get('width_ft') else 22.9
            am = arr_roll(rows, arr['seg'], rw, halfw, arr.get('run'))
            arr_tracks[name] = dict(track=am['track'] if am else None, apt=ap_arr['ident'],
                                    rwy=arr['rwy'], L=dist_m(rw['lat'], rw['lon'], rw['olat'], rw['olon']),
                                    halfw=halfw, capture=am['capture'] if am else '')
            arr['halfw_m'] = round(halfw, 1)
            arr['rwy_len_m'] = round(dist_m(rw['lat'], rw['lon'], rw['olat'], rw['olon']))
            roll_pts[(ap_arr['ident'], arr['rwy'])].append(
                [(a, c) for (_, x) in arr['seg'] for c, a in [perp_along(x[1], x[2], rw)]])

        org = dst = fn = when = ''
        if f:
            org, dst, fn, when = f['origin'], f['dest'], f['fn'], f['dep'].strftime('%Y-%m-%d %H:%M')

        def g(d, k):
            return d.get(k, '') if d else ''

        row = dict(
            file=name, flight=fn or name.split('-')[0], log_origin=org, log_dest=dst, when=when,
            dep_apt=ap_dep['ident'] if ap_dep else '',
            dep_apt_dist_km=round(d_dep / 1000, 1) if ap_dep else '', dep_apt_ground=dep_ground,
            dep_rwy=g(dep, 'rwy'), dep_conf=g(dep, 'conf'), dep_method=g(dep, 'method'),
            dep_hdg=g(dep, 'hdg'), dep_n_seg=g(dep, 'n'), dep_err=g(dep, 'hdg_err'),
            dep_xt=g(dep, 'mean_xtrack_m'), dep_rival_xt=g(dep, 'rival_xt'),
            dep_margin=g(dep, 'margin'),
            dep_rwy_len_m=g(dep, 'rwy_len_m'), dep_rwy_width_m=g(dep, 'rwy_width_m'),
            dep_roll_start_m=g(dm, 'roll_start'),
            dep_roll_start_speed_kt=g(dm, 'start_speed'),
            dep_liftoff_along_lo=g(dm, 'along_lo'), dep_liftoff_along_hi=g(dm, 'along_hi'),
            dep_runway_used_m=g(dm, 'along'), dep_liftoff_bracket_m=g(dm, 'bracket'),
            dep_liftoff_speed_kt=g(dm, 'speed'), dep_roll_len_m=g(dm, 'roll_len'),
            dep_rwy_remaining_m=g(dm, 'remaining'), dep_roll_source=g(dm, 'source'),
            dep_roll_capture=g(dm, 'capture'), dep_liftoff_xt_m=g(dm, 'xt'),
            dep_accel_alt_ft=g(dm, 'accel_alt_ft'),
            arr_apt=ap_arr['ident'] if ap_arr else '',
            arr_apt_dist_km=round(d_arr / 1000, 1) if ap_arr else '', arr_apt_ground=arr_ground,
            arr_rwy=g(arr, 'rwy'), arr_conf=g(arr, 'conf'), arr_method=g(arr, 'method'),
            arr_hdg=g(arr, 'hdg'), arr_n_seg=g(arr, 'n'), arr_err=g(arr, 'hdg_err'),
            arr_xt=g(arr, 'mean_xtrack_m'), arr_rival_xt=g(arr, 'rival_xt'),
            arr_margin=g(arr, 'margin'),
            arr_rwy_len_m=g(arr, 'rwy_len_m'), arr_rwy_halfwidth_m=g(arr, 'halfw_m'),
            arr_thr_speed_kt=g(am, 'thr_speed'), arr_thr_height_ft=g(am, 'thr_height'),
            arr_td_along_lo=g(am, 'td_lo'), arr_td_along_hi=g(am, 'td_hi'),
            arr_td_along_m=g(am, 'td_along'), arr_td_bracket_m=g(am, 'td_bracket'),
            arr_td_speed_kt=g(am, 'td_speed'), arr_alt_flat_m=g(am, 'alt_flat_m'),
            arr_roll_len_m=g(am, 'roll_len'), arr_runway_used_m=g(am, 'used'),
            arr_rwy_remaining_m=g(am, 'remaining'), arr_turnoff_speed_kt=g(am, 'end_speed'),
            arr_stop_along_m=g(am, 'stop_along'), arr_roll_capture=g(am, 'capture'),
            arr_td_xt_m=g(am, 'xt'),
        )
        rows_out.append(row)

    # ---- fit the centrelines the fleet actually rolled on ------------------
    fits = {}
    for key, groups in roll_pts.items():
        ft = fit_centreline([p for g in groups for p in g])
        if ft:
            ft['flights'] = len(groups)
            fits[key] = ft
    rwy_len = {}
    for r in rows_out:
        if r['dep_rwy'] and r['dep_rwy_len_m']:
            rwy_len[(r['dep_apt'], r['dep_rwy'])] = r['dep_rwy_len_m']
        if r['arr_rwy'] and r['arr_rwy_len_m']:
            rwy_len[(r['arr_apt'], r['arr_rwy'])] = r['arr_rwy_len_m']
    with open('runway_centreline_fit.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['airport', 'runway', 'flights', 'fixes', 'offset_at_threshold_m',
                    'offset_at_far_end_m', 'rotation_deg', 'residual_sd_m'])
        for (apt, rwy), ft in sorted(fits.items(), key=lambda kv: -kv[1]['flights']):
            L = rwy_len.get((apt, rwy), 3000)
            w.writerow([apt, rwy, ft['flights'], ft['n'], round(ft['a']), round(ft['a'] + ft['b'] * L),
                        round(ft['rot_deg'], 2), round(ft['sd'], 1)])
    # apply the fitted line to the touchdown / lift-off lateral deviation
    for r in rows_out:
        for pre in ('dep_exit', 'arr_td'):
            apt = r['dep_apt'] if pre == 'dep_exit' else r['arr_apt']
            rwy = r['dep_rwy'] if pre == 'dep_exit' else r['arr_rwy']
            along = r['dep_runway_used_m'] if pre == 'dep_exit' else r['arr_td_along_m']
            raw = r['dep_liftoff_xt_m'] if pre == 'dep_exit' else r['arr_td_xt_m']
            if raw == '' or not rwy:
                continue
            ft = fits.get((apt, rwy))
            corr = round(raw - (ft['a'] + ft['b'] * along)) if ft else raw
            if pre == 'dep_exit':
                r['dep_liftoff_xt_cal_m'] = corr
            else:
                r['arr_td_xt_cal_m'] = corr

    # ---- redo the arrival turn-off against the fitted centreline ---------------
    # The published centrelines can sit 30-40 m off the line the fleet actually
    # rolls on (EBB 17 is the worst case).  Against the published line that offset
    # exceeds the runway half-width, so the turn-off fires at touchdown and the
    # landing roll comes out as zero.  With a per-runway fit to hand, the exit is
    # measured from the line the aircraft was actually on.
    recal = 0
    for r in rows_out:
        info = arr_tracks.get(r['file'])
        if not info or not info['track'] or r['arr_roll_len_m'] == '':
            continue
        ft = fits.get((info['apt'], info['rwy']))
        if not ft:
            continue
        lim = info['halfw'] + 10
        pts = [(t, a, c - (ft['a'] + ft['b'] * a), v) for (t, a, c, v) in info['track']]
        ex = next((p for p in pts if abs(p[2]) > lim), None)
        # the landing run also ends where the aircraft stops or turns around; a few
        # arrivals (JRO 09 among them) brake, then taxi back down the runway, and the
        # lateral exit only shows up during the taxi - that must not be counted
        mx = pts[0][1]
        rev = None
        for i, p in enumerate(pts):
            mx = max(mx, p[1])
            if mx - p[1] > 150:
                rev = i
                break
        ends = [i for i in (pts.index(ex) if ex else None, rev, len(pts) - 1) if i is not None]
        e = min(ends)
        used, tag = pts[e][1], ''
        if ex is None or pts.index(ex) > e:
            tag = ' / track ends on the runway (roll is a lower bound)'
        stop = next((p for p in pts if p[0] >= pts[e][0] and p[3] <= STOP_KT), None)
        td = float(r['arr_td_along_m'])
        r['arr_runway_used_m'] = round(used)
        r['arr_roll_len_m'] = round(used - td)
        r['arr_rwy_remaining_m'] = round(info['L'] - used)
        r['arr_turnoff_speed_kt'] = pts[e][3]
        r['arr_stop_along_m'] = round(stop[1]) if stop else ''
        r['arr_roll_capture'] = info['capture'].split(' / ')[0] + tag
        recal += 1

    # ---- attach the tail (5X-...) where the screenshots give a unique match ----
    tails = collections.defaultdict(list)
    if os.path.exists('tails.csv'):
        for t in csv.DictReader(open('tails.csv')):
            tails[(t['date'], t['flight'])].append(t)
    for r in rows_out:
        pre = r['file'].split('-')[0]
        if not pre.upper().startswith('UR') or not r['when']:
            r['tail'] = ''
            continue
        cand = tails.get((r['when'][:10], pre.upper()), [])
        hit = [t for t in cand if t['origin'] == r['log_origin'] and t['dest'] == r['log_dest']]
        r['tail'] = hit[0]['tail'] if len(hit) == 1 else (cand[0]['tail'] if len(cand) == 1 else '')

    # ---- day-direction QA ---------------------------------------------------
    def canon(ident):
        d = ''.join(ch for ch in ident if ch.isdigit())
        if not d:
            return ident
        n = int(d)
        return '%02d' % min(n, n + 18 if n <= 18 else n - 18)
    for side, aptk in (('dep', 'dep_apt'), ('arr', 'arr_apt')):
        byday = collections.defaultdict(collections.Counter)
        for r in rows_out:
            if r[f'{side}_rwy'] and r['when'] and r[f'{side}_conf'] in ('high', 'medium'):
                byday[(r[aptk], r['when'][:10])][canon(r[f'{side}_rwy'])] += 1
        for r in rows_out:
            r[f'{side}_day_dir'] = ''
            if r[f'{side}_rwy'] and r['when']:
                c = byday.get((r[aptk], r['when'][:10]), {})
                if sum(c.values()) >= 2:
                    mode = max(c, key=c.get)
                    r[f'{side}_day_dir'] = 'match' if canon(r[f'{side}_rwy']) == mode else 'DIFFERS'

    cols = ['file', 'flight', 'tail', 'when', 'log_origin', 'log_dest',
            'dep_apt', 'dep_apt_dist_km', 'dep_apt_ground', 'dep_rwy', 'dep_conf', 'dep_method',
            'dep_hdg', 'dep_n_seg', 'dep_err', 'dep_xt', 'dep_rival_xt', 'dep_margin', 'dep_day_dir',
            'dep_rwy_len_m', 'dep_rwy_width_m',
            'dep_roll_start_m', 'dep_roll_len_m', 'dep_runway_used_m', 'dep_rwy_remaining_m',
            'dep_roll_start_speed_kt', 'dep_liftoff_speed_kt', 'dep_liftoff_bracket_m',
            'dep_liftoff_along_lo', 'dep_liftoff_along_hi', 'dep_roll_source', 'dep_roll_capture',
            'dep_accel_alt_ft',
            'dep_liftoff_xt_m', 'dep_liftoff_xt_cal_m',
            'arr_apt', 'arr_apt_dist_km', 'arr_apt_ground', 'arr_rwy', 'arr_conf', 'arr_method',
            'arr_hdg', 'arr_n_seg', 'arr_err', 'arr_xt', 'arr_rival_xt', 'arr_margin', 'arr_day_dir',
            'arr_rwy_len_m', 'arr_rwy_halfwidth_m',
            'arr_thr_speed_kt', 'arr_thr_height_ft',
            'arr_td_along_m', 'arr_td_along_lo', 'arr_td_along_hi', 'arr_td_bracket_m',
            'arr_td_speed_kt', 'arr_alt_flat_m',
            'arr_roll_len_m', 'arr_runway_used_m', 'arr_rwy_remaining_m', 'arr_turnoff_speed_kt',
            'arr_stop_along_m', 'arr_roll_capture', 'arr_td_xt_m', 'arr_td_xt_cal_m']
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows_out)

    # ---------------------------------------------------------------- report ---
    tot = len(rows_out)
    print(f'tracks analysed         : {tot}')
    for side in ('dep', 'arr'):
        got = [r for r in rows_out if r[f'{side}_rwy']]
        print(f'{side}: runway known {len(got):3}/{tot}  '
              f'{dict(collections.Counter(r[f"{side}_method"] for r in got))}  '
              f'conf {dict(collections.Counter(r[f"{side}_conf"] for r in got))}')
    print(f'both ends known         : {sum(1 for r in rows_out if r["dep_rwy"] and r["arr_rwy"])}')
    for side in ('dep', 'arr'):
        c = collections.Counter(r[f'{side}_day_dir'] for r in rows_out if r[f'{side}_day_dir'])
        print(f'   {side} day-direction QA: {dict(c)}')
    d = [r for r in rows_out if r['dep_roll_len_m'] != '']
    a = [r for r in rows_out if r['arr_roll_len_m'] != '']
    print(f'roll metrics: take-off {len(d)}, landing {len(a)}')
    print('   take-off wheel-off source:', dict(collections.Counter(r['dep_roll_source'] for r in d)))
    print('   take-off capture :', dict(collections.Counter(r['dep_roll_capture'] for r in d)))
    print('   landing capture  :', dict(collections.Counter(r['arr_roll_capture'] for r in a)))
    print(f"tail attached           : {sum(1 for r in rows_out if r['tail'])}")
    print(f"arrival turn-off re-cut vs fitted centreline: {recal}")
    print(f'\nwrote {out} and runway_centreline_fit.csv')


if __name__ == '__main__':
    main(*sys.argv[1:])
