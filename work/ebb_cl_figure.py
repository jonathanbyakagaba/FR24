#!/usr/bin/env python3
"""Draw the Entebbe centreline correction: one picture, two panels, before and after.

Top    - every EBB 17/35 ground-roll fix measured against the ORIGINAL centreline
         published by OurAirports (y = 0).  The fleet looks as if it rolls
         diagonally across the runway and off both edges, because the published
         coordinates are 35-38 m off the physical strip and rotated 1.14 degrees.
Bottom - the same fixes measured against the CORRECTED centreline now used by the
         pipeline (work/rwy/centreline_fixes.csv).  Flat, because the reference
         now describes the runway the aircraft actually roll on.

The runway axis mapped in OpenStreetMap from satellite imagery is drawn on both
panels: it agrees with the correction to 1.8 m and with the original line it was
35 m out at one end, 38 m out at the other.
"""
import csv, math, sys, zipfile, importlib.util
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, '/home/user')
spec = importlib.util.spec_from_file_location('rw', 'work/runways.py')
rw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rw)

apts, rwys, grid = rw.load_airports()
corrected = next(x for x in rwys['HUEN'] if x['ident'] == '17')      # corrected: used now
L = rw.dist_m(corrected['lat'], corrected['lon'], corrected['olat'], corrected['olon'])
HALF = 23.0                                    # OSM tags the runway as 46 m wide

# the ORIGINAL OurAirports geometry, straight from the download (bypassing the fix)
orig = None
for r in csv.DictReader(open('work/rwy/runways.csv')):
    if r['airport_ident'] == 'HUEN' and r['le_ident'] == '17':
        orig = dict(lat=float(r['le_latitude_deg']), lon=float(r['le_longitude_deg']),
                    olat=float(r['he_latitude_deg']), olon=float(r['he_longitude_deg']))
assert orig

# OSM way 5089872, ref "17/35" (fetched from the Overpass API, mapped from imagery)
osm = dict(lat=0.0556164, lon=32.4362036, olat=0.0228666, olon=32.4407476)

pts = []                                       # (along, cross) in the ORIGINAL frame
flights = {}
z = zipfile.ZipFile('fr24_publish/FR data.zip')
for r in csv.DictReader(open('runway_usage.csv')):
    end = None
    if r['dep_apt'] == 'HUEN' and r['dep_rwy'] in ('17', '35'):
        end = ('dep', r['dep_rwy'])
    elif r['arr_apt'] == 'HUEN' and r['arr_rwy'] in ('17', '35'):
        end = ('arr', r['arr_rwy'])
    if not end:
        continue
    rwy = orig if end[1] == '17' else dict(lat=orig['olat'], lon=orig['olon'],
                                           olat=orig['lat'], olon=orig['lon'])
    for x in rw.parse_track(z.read(r['file'])):
        if x[3] > 0.1:                         # ground fixes only (FR24 altitude reads 0 on the ground)
            continue
        c, a = rw.perp_along(x[1], x[2], rwy)
        if end[1] == '35':
            a, c = L - a, -c
        if -150 <= a <= L + 150 and abs(c) <= 120:
            pts.append((a, c))
            flights.setdefault(r['file'], []).append((a, c, x[4]))

# where each reference line sits in the original frame, at along = 0 and along = L
def line_in_orig(frame):
    e0 = rw.perp_along(frame['lat'], frame['lon'], orig)[0]
    e1 = rw.perp_along(frame['olat'], frame['olon'], orig)[0]
    return e0, e1

corr0, corr1 = line_in_orig(corrected)
osm0, osm1 = line_in_orig(osm)

fig, (ax, bx) = plt.subplots(2, 1, figsize=(11.5, 9.2), sharex=True,
                             gridspec_kw=dict(hspace=0.16))
fig.patch.set_facecolor('white')

# ---------------------------------------------------------------- top panel --
ax.axhspan(-HALF, HALF, color='#dddddd', zorder=0)
ax.plot([0, L], [0, 0], color='#8a8a8a', lw=1.0, ls=(0, (6, 4)), zorder=1)
ax.plot([0, L], [osm0, osm1], color='#1a9850', lw=2.6, zorder=2)
ax.plot([0, L], [corr0, corr1], color='#d73027', lw=1.3, zorder=3)
ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=2.2, c='#2b6cb0', alpha=0.20,
           linewidths=0, zorder=4)
ax.text(0.985, 0.06, 'original published centreline (OurAirports) — y = 0', color='#555555',
        fontsize=9, ha='right', transform=ax.transAxes)
ax.text(0.985, 0.145, 'corrected centreline now in use (= the fleet line, = OSM)',
        color='#d73027', fontsize=9, ha='right', transform=ax.transAxes)
ax.text(0.985, 0.23, 'runway axis mapped in OpenStreetMap from imagery',
        color='#1a9850', fontsize=9, ha='right', transform=ax.transAxes)
ax.annotate('', xy=(L, corr1), xytext=(L, 0), arrowprops=dict(arrowstyle='<->', color='#333', lw=0.9))
ax.text(L - 40, corr1 / 2, f'  {corr1:+.0f} m', fontsize=9, va='center', color='#333')
ax.annotate('', xy=(0, corr0), xytext=(0, 0), arrowprops=dict(arrowstyle='<->', color='#333', lw=0.9))
ax.text(60, corr0 / 2, f'{corr0:+.0f} m  ', fontsize=9, va='center', ha='right', color='#333')
ax.set_title('BEFORE — the reference line the pipeline used to measure against\n'
             'the fleet looks like it rolls diagonally across the runway and off both edges',
             fontsize=11, pad=8)
ax.set_ylabel('distance from the original\npublished centreline (m)', fontsize=10)
ax.set_ylim(-70, 70)
ax.grid(axis='x', color='#eeeeee')
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)

# ------------------------------------------------------------- bottom panel --
# re-measure exactly the same fixes against the corrected line
a0c, a1c = float(corrected['lat']), float(corrected['lon'])
pts2 = []
for r in csv.DictReader(open('runway_usage.csv')):
    end = None
    if r['dep_apt'] == 'HUEN' and r['dep_rwy'] in ('17', '35'):
        end = ('dep', r['dep_rwy'])
    elif r['arr_apt'] == 'HUEN' and r['arr_rwy'] in ('17', '35'):
        end = ('arr', r['arr_rwy'])
    if not end:
        continue
    rwy = corrected if end[1] == '17' else next(x for x in rwys['HUEN'] if x['ident'] == '35')
    for x in rw.parse_track(z.read(r['file'])):
        if x[3] > 0.1:
            continue
        c, a = rw.perp_along(x[1], x[2], rwy)
        if -150 <= a <= L + 150 and abs(c) <= 120:
            pts2.append((a, c, x[4]))

# statistics on the fixes where the aircraft is actually rolling on the runway
# (>= 55 kt); slower positions include taxiways and holding points, which are not
# the runway and would inflate the spread.
roll = sorted(c for _, c, v in pts2 if v >= 55)
mean_dev = sum(roll) / len(roll)
sd_dev = (sum((c - mean_dev) ** 2 for c in roll) / len(roll)) ** 0.5
med_fix = abs(roll[len(roll) // 2])

bx.axhspan(-HALF, HALF, color='#dddddd', zorder=0)
bx.scatter([p[0] for p in pts2], [p[1] for p in pts2], s=2.2, c='#2b6cb0', alpha=0.20,
           linewidths=0, zorder=3)
bx.plot([0, L], [0, 0], color='#d73027', lw=1.2, zorder=2)
bx.text(0.985, 0.06, 'corrected centreline — y = 0', color='#d73027', fontsize=9,
        ha='right', transform=bx.transAxes)
bx.set_title(f'AFTER — the same fixes against the corrected reference\n'
             f'{len(roll):,} rolling fixes (≥55 kt): mean offset {mean_dev:+.1f} m, S.D. {sd_dev:.1f} m '
             f'— the spread collapses onto the runway',
             fontsize=11, pad=8)
bx.set_ylabel('distance from the corrected\ncentreline (m)', fontsize=10)
bx.set_xlabel('distance from the runway 17 threshold (m)', fontsize=10)
bx.set_ylim(-70, 70)
bx.set_xlim(-150, L + 150)
bx.grid(axis='x', color='#eeeeee')
for s in ('top', 'right'):
    bx.spines[s].set_visible(False)

fig.text(0.012, 0.012,
         'Original reference: OurAirports runway coordinates (grey, heading 170.96°). Corrected reference: '
         'work/rwy/centreline_fixes.csv (red, 172.10°).\n'
         f'Independent geometry: OpenStreetMap way 5089872 mapped from satellite imagery (green, 172.10°) — it agrees with the\n'
         f'correction to 1.8 m. Fixes: {len(pts):,} wheels-on-ground positions from {len(flights)} EBB 17/35 flights in FR data.zip.\n'
         'The runway is 46 m wide (half-width 23 m), so the original line was over a half-width out at both ends.',
         fontsize=8.5, color='#444444', linespacing=1.5)
fig.subplots_adjust(top=0.905, bottom=0.185, left=0.085, right=0.985)
fig.savefig('entebbe_centreline.png', dpi=150)
print(f'wrote entebbe_centreline.png  ({len(pts):,} fixes, {len(flights)} flights)')
print(f'  original line: {corr0:+.1f} m at the 17 end, {corr1:+.1f} m at the 35 end')
print(f'  rolling fixes: mean {mean_dev:+.2f} m, SD {sd_dev:.2f} m, median |fix| {med_fix:.2f} m')
print(f'  OSM line     : {osm0:+.1f} m at the 17 end, {osm1:+.1f} m at the 35 end')
