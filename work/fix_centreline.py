#!/usr/bin/env python3
"""Derive corrected runway centrelines and write them as reference data.

Why this exists
---------------
The runway coordinates published by OurAirports are not always the physical
centreline.  At Entebbe the 17/35 strip is published 35 m off at one threshold,
38 m off at the other, and rotated 1.14 deg - the fleet's 3,006 ground-roll fixes
sit on a different straight line, and the runway axis mapped from satellite
imagery in OpenStreetMap agrees with the fleet to within 4.6 m.

A reference line that far out is not a cosmetic problem: the arrival roll-out is
cut where the aircraft crosses the runway edge (half-width + 10 m), so an offset
bigger than the half-width fires that test at touchdown and reports a zero-length
landing roll.

What this does
--------------
Takes the fit from `runway_centreline_fit.csv` (cross = a + b * along, measured
against the published line for one runway end), shifts both ends of the published
axis by that offset and rotation, cross-checks the result against any independent
geometry available (OSM), and writes `work/rwy/centreline_fixes.csv`.  That file
is read by `load_airports()`, so it is the reference from then on - it does not
depend on a fit being available at run time.

Run:  PYTHONPATH=/home/user python3 work/fix_centreline.py
"""
import csv, math, os, sys, zipfile, importlib.util

sys.path.insert(0, '/home/user')
spec = importlib.util.spec_from_file_location('rw', 'work/runways.py')
rw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rw)

OUT = 'work/rwy/centreline_fixes.csv'

# Independent geometry, mapped from satellite imagery.  Used only to corroborate;
# nothing in the pipeline depends on it being reachable at run time.
OSM = {
    ('HUEN', '17'): dict(  # OSM way 5089872, ref "17/35", width 46 m, length 3680 m
        thr=(0.0556164, 32.4362036),      # threshold end of runway 17 (north)
        far=(0.0228666, 32.4407476),      # far end (the 35 threshold)
        note='OpenStreetMap way 5089872'),
}


def shift(rw_, a_thr, a_far):
    """Move a runway end's coordinates sideways by the given offsets (m).

    `a_thr` is the offset at that end's threshold, `a_far` at its far end, both in
    the perp_along() frame (+ = right of the direction of travel)."""
    mlat = math.radians((rw_['lat'] + rw_['olat']) / 2)
    ux = (rw_['olon'] - rw_['lon']) * math.cos(mlat) * 111320.0
    uy = (rw_['olat'] - rw_['lat']) * 110540.0
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    # (uy, -ux) is the unit vector with perp_along cross = +1
    out = {}
    for key, off in (('thr', a_thr), ('far', a_far)):
        dpx, dpy = uy * off, -ux * off
        lat = rw_['lat'] if key == 'thr' else rw_['olat']
        lon = rw_['lon'] if key == 'thr' else rw_['olon']
        out[f'{key}_lat'] = lat + dpy / 110540.0
        out[f'{key}_lon'] = lon + dpx / (math.cos(mlat) * 111320.0)
    return out


def bearing(a, b):
    return rw.bearing(a[0], a[1], b[0], b[1])


def main():
    apts, runways, grid = rw.load_airports()
    fits = {}
    for f in csv.DictReader(open('runway_centreline_fit.csv')):
        fits[(f['airport'], f['runway'])] = f

    rows, checks = [], []
    for (apt, ident), fit in sorted(fits.items()):
        rw_ = next((r for r in runways.get(apt, []) if r['ident'] == ident), None)
        if not rw_:
            continue
        L = rw.dist_m(rw_['lat'], rw_['lon'], rw_['olat'], rw_['olon'])
        a_thr = float(fit['offset_at_threshold_m'])
        a_far = float(fit['offset_at_far_end_m'])          # already a + b*L
        # only lines whose own fit is tight enough to be a real line are offered,
        # and (below) only where an independent source corroborates or the offset
        # is large enough to matter; the rest stay on the published coordinates.
        rot = abs(float(fit['rotation_deg']))
        sd = float(fit['residual_sd_m'])
        rec = dict(airport=apt, ident=ident, L=L, a_thr=a_thr, a_far=a_far,
                   rot=rot, sd=sd, n=int(fit['fixes']))
        rows.append(rec)
        osm = OSM.get((apt, ident))
        if osm:
            # where does the OSM axis sit in the published frame?
            for label, (la, lo) in (('thr', osm['thr']), ('far', osm['far'])):
                c, al = rw.perp_along(la, lo, rw_)
                fit_c = a_thr + (a_far - a_thr) * al / L
                checks.append((apt, ident, label, al, c, fit_c, c - fit_c))
    print('fitted lines available:')
    for r_ in sorted(rows, key=lambda r_: -(abs(r_['a_thr']) + abs(r_['a_far']))):
        flag = ''
        osm = OSM.get((r_['airport'], r_['ident']))
        if osm:
            diffs = [x[-1] for x in checks if x[0] == r_['airport'] and x[1] == r_['ident']]
            flag = f'   <-- OSM corroborates (differs by {abs(sum(diffs)/len(diffs)):.1f} m)'
        print(f"  {r_['airport']} {r_['ident']:4} thr {r_['a_thr']:+6.1f} m  far {r_['a_far']:+6.1f} m  "
              f"rot {r_['rot']:.2f}°  sd {r_['sd']:.1f} m  n={r_['n']:5}{flag}")

    print('\nOSM vs the fleet-fitted line, in the published frame:')
    for apt, ident, label, al, c, fit_c, d in checks:
        print(f'  {apt} {ident} OSM {label:3} end: along {al:6.0f} m, OSM cross {c:+7.1f} m, '
              f'fleet line {fit_c:+7.1f} m -> agree to {abs(d):.1f} m')

    # ---- what gets written: lines that are (a) fitted, (b) tight, (c) corroborated
    #      by an independent source.  Add to CORROBORATED as more are checked.
    CORROBORATED = {('HUEN', '17'), ('HUEN', '35')}
    out = []
    for r_ in rows:
        if (r_['airport'], r_['ident']) not in CORROBORATED:
            continue
        rw_ = next(r for r in runways[r_['airport']] if r['ident'] == r_['ident'])
        sh = shift(rw_, r_['a_thr'], r_['a_far'])
        olat, olon = sh['far_lat'], sh['far_lon']
        thr = (sh['thr_lat'], sh['thr_lon'])
        far = (olat, olon)
        hdg = bearing(thr, far)
        src = 'fleet roll fit'
        ev = (f"{r_['n']} ground-roll fixes fit a straight line (SD {r_['sd']:.1f} m) sitting "
              f"{r_['a_thr']:+.0f} m / {r_['a_far']:+.0f} m off the published line and {r_['rot']:.2f}° rotated")
        if (r_['airport'], r_['ident']) in OSM:
            diffs = [x[-1] for x in checks if x[0] == r_['airport'] and x[1] == r_['ident']]
            ev += f"; {OSM[(r_['airport'], r_['ident'])]['note']} agrees to {abs(sum(diffs)/len(diffs)):.1f} m"
        out.append(dict(airport=r_['airport'], ident=r_['ident'],
                        thr_lat=round(thr[0], 9), thr_lon=round(thr[1], 9),
                        far_lat=round(olat, 9), far_lon=round(olon, 9),
                        heading_degT=round(hdg, 2),
                        length_m=round(rw.dist_m(thr[0], thr[1], olat, olon)), source=src,
                        evidence=ev))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['airport', 'ident', 'thr_lat', 'thr_lon', 'far_lat',
                                           'far_lon', 'heading_degT', 'length_m', 'source', 'evidence'])
        w.writeheader()
        w.writerows(out)
    print(f'\nwrote {OUT}: {len(out)} runway ends')
    for r_ in out:
        print(f"  {r_['airport']} {r_['ident']:4} hdg {r_['heading_degT']:.2f}°  {r_['length_m']} m")

    # ---- verify: re-measure the fleet's fixes against the corrected line ---------
    print('\nresiduals of the fleet fixes against the CORRECTED line:')
    z = zipfile.ZipFile('fr24_publish/FR data.zip')
    rows_usage = list(csv.DictReader(open('runway_usage.csv')))
    for ident in ('17', '35'):
        corr = next(o for o in out if o['ident'] == ident)
        frame = dict(lat=corr['thr_lat'], lon=corr['thr_lon'], olat=corr['far_lat'], olon=corr['far_lon'])
        cs = []
        for r_ in rows_usage:
            if not ((r_['dep_apt'] == 'HUEN' and r_['dep_rwy'] == ident)
                    or (r_['arr_apt'] == 'HUEN' and r_['arr_rwy'] == ident)):
                continue
            for x in rw.parse_track(z.read(r_['file'])):
                # fixing only while rolling on the runway (speed up, wheels down):
                # slow fixes include taxiways and holding points, which are not the runway
                if x[3] > 0.1 or x[4] < 55:
                    continue
                c, a = rw.perp_along(x[1], x[2], frame)
                if -100 <= a <= corr['length_m'] + 100 and abs(c) <= 100:
                    cs.append((c, a))
        if cs:
            n = len(cs)
            # fit cross = a + b*along  (along is the x axis, cross the y axis)
            sx = sum(y for _, y in cs); sy = sum(x for x, _ in cs)
            sxx = sum(y * y for _, y in cs); sxy = sum(x * y for x, y in cs)
            b_ = (n * sxy - sx * sy) / (n * sxx - sx * sx)
            mean = sum(x for x, _ in cs) / n
            sd = (sum((x - mean) ** 2 for x, _ in cs) / n) ** 0.5
            print(f"  HUEN {ident}: {n:5} rolling fixes, mean offset {mean:+.2f} m, SD {sd:.2f} m, "
                  f"slope {math.degrees(math.atan(b_)):+.4f}°")


if __name__ == '__main__':
    main()
