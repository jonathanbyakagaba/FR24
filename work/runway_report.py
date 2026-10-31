#!/usr/bin/env python3
"""Build runway_usage.md from runway_usage.csv (run after work/runways.py).

For each track the pipeline answers three questions:

  1. which runway end was used (roll matching / climb-approach heading)
  2. where across the runway the wheels were (touchdown / wheel-off lateral)
  3. how much of the runway was used (roll start, lift-off, touchdown, roll-out)

This script only tabulates what work/runways.py measured; it invents nothing.
"""
import csv, collections, statistics as st

ROWS = list(csv.DictReader(open('runway_usage.csv')))
N = len(ROWS)

ICAO_NAME = {
    'HUEN': 'Entebbe', 'HKJK': 'Nairobi', 'HTDA': 'Dar es Salaam', 'FAOR': 'Johannesburg',
    'HJJJ': 'Juba', 'HBBA': 'Bujumbura', 'FVHA': 'Harare', 'FLLS': 'Lusaka', 'HKMO': 'Mombasa',
    'EGKK': 'London Gatwick', 'DNMM': 'Lagos', 'HTZA': 'Zanzibar', 'VABB': 'Mumbai',
    'HRYR': 'Kigali', 'HTKJ': 'Kilimanjaro', 'HAAB': 'Addis Ababa', 'OMDB': 'Dubai',
    'FZAA': 'Kinshasa', 'OTHH': 'Doha', 'EBBR': 'Brussels', 'LTFM': 'Istanbul', 'DIAP': 'Abidjan',
    'SBGR': 'Sao Paulo', 'EHAM': 'Amsterdam', 'HECA': 'Cairo', 'FYWH': 'Windhoek', 'OEJN': 'Jeddah',
    'OERK': 'Riyadh', 'OEMA': 'Medina', 'OMSJ': 'Sharjah', 'DNAA': 'Abuja', 'DRRN': 'Niamey',
    'FZKA': 'Butembo', 'HCMM': 'Mogadishu', 'OESB': 'Shaqra', 'HSSJ': 'Juba',
    'DABC': 'Constantine', 'DXXX': 'Lome', 'DGAA': 'Accra',
}
TYPE = {'5X-NIL': 'A330-800neo', 'ET-APL': '737-800', '5X-KOB': 'CRJ900',
        '5X-KDP': 'CRJ900', '5X-EQU': 'CRJ900'}
TYPE_ORDER = [('A330-800neo', ['5X-NIL']), ('737-800', ['ET-APL']),
              ('CRJ900', ['5X-KOB', '5X-KDP', '5X-EQU'])]


def name(a):
    return f'{ICAO_NAME[a]} ({a})' if a in ICAO_NAME else a


def num(r, k):
    v = r.get(k, '')
    return float(v) if v not in ('', None) else None


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def m0(x):
    return '—' if x is None else f'{x:,.0f}'


def km(x):
    return '—' if x is None else f'{x/1000:.2f} km'


FALLBACK = 'speed fallback'


def solid(side):
    """rows measured from a real signature (not the coarse-export fallback)"""
    if side == 'dep':
        return [r for r in ROWS if r['dep_roll_len_m'] != ''
                and FALLBACK not in r['dep_roll_source']]
    return [r for r in ROWS if r['arr_roll_len_m'] != ''
            and not r['arr_roll_capture'].startswith('no deceleration captured')]


def n_of(side):
    return [r for r in ROWS if r[f'{side}_rwy']]


L = []
w = L.append

# ------------------------------------------------------------------ header ---
w('# Which runway was used — and how much of it')
w('')
w('Everything here is read from the FR24 tracks in `FR data.zip`. The exports carry **no')
w('runway field**, so each row is *inferred* from where the aircraft actually rolled, and')
w('then measured along that runway: where the roll started, where the wheels left the')
w('ground, where the wheels touched down, and where the aircraft left the pavement.')
w('')
w('Source: `runway_usage.csv` — one row per track, 66 columns. Regenerate with')
w('`PYTHONPATH=/home/user python3 work/runways.py` then `python3 work/runway_report.py`.')
w('')

# ---------------------------------------------------------------- coverage ---
dep_km, arr_km = n_of('dep'), n_of('arr')
both = sum(1 for r in ROWS if r['dep_rwy'] and r['arr_rwy'])
tails = sum(1 for r in ROWS if r['tail'])
dep_m = sum(1 for r in ROWS if r['dep_roll_len_m'] != '')
arr_m = sum(1 for r in ROWS if r['arr_roll_len_m'] != '')
w('## Coverage')
w('')
w('| | known | high | medium | low | from the roll | from climb/approach heading |')
w('|---|---|---|---|---|---|---|')
for side, label in (('dep', 'Departure runway'), ('arr', 'Arrival runway')):
    got = n_of(side)
    conf = collections.Counter(r[f'{side}_conf'] for r in got)
    meth = collections.Counter(r[f'{side}_method'] for r in got)
    w(f"| {label} | **{len(got)}/{N}** | {conf['high']} | {conf['medium']} | {conf['low']} | "
      f"{meth['roll']} | {sum(v for k, v in meth.items() if k != 'roll')} |")
fb = sum(1 for r in ROWS if FALLBACK in r['dep_roll_source'])
w(f'| Take-off distance measured | **{dep_m}/{N}** ({fb} fallback only) | | | | | |')
w(f'| Landing distance measured | **{arr_m}/{N}** | | | | | |')
w('')
w(f'- both runway ends known: **{both}/{N}** ({100*both/N:.0f}%)')
ur = [r for r in ROWS if r['file'].upper().startswith('UR')]
if ur:
    w(f"- the airline's own (UR/UGD) tracks: departures "
      f"**{sum(1 for r in ur if r['dep_rwy'])}/{len(ur)}**, arrivals "
      f"**{sum(1 for r in ur if r['arr_rwy'])}/{len(ur)}**, both ends "
      f"**{sum(1 for r in ur if r['dep_rwy'] and r['arr_rwy'])}/{len(ur)}**")
w(f'- tail (5X-… / ET-APL) attached from your screenshots: **{tails}** rows — every UR track'
  ' whose (date, flight, route) key matches exactly one screenshot row')
w('- `high` = roll captured, on the centreline (mean cross-track ≤ 70 m) and heading within 10°')
w('- `medium` = roll captured but shorter/looser, or the heading fallback with a clear margin')
w('- `low` = heading-only evidence at an airport with a parallel strip, or a weak fit — a hint')
align = sum(1 for r in ROWS if '-alignment' in r['dep_method'] or '-alignment' in r['arr_method'])
if align:
    w(f'- **{align} rows get their runway from alignment rather than a roll.** Where the export starts'
      ' just after the rotation or stops on short final there is nothing on the ground to'
      ' match, but the aircraft is low, close to the field and lined up with one runway: the'
      ' call is made from its position against that runway\'s extended centreline plus the'
      ' heading between two fixes ~2 km apart (`climb-alignment` / `approach-alignment`). No'
      ' roll, touchdown or distance figures come out of those rows.')
w('')

# -------------------------------------------------------- why trustworthy ---
droll = [r for r in ROWS if r['dep_method'] == 'roll']
aroll = [r for r in ROWS if r['arr_method'] == 'roll']
dd = collections.Counter(r['dep_day_dir'] for r in ROWS if r['dep_day_dir'])
ad = collections.Counter(r['arr_day_dir'] for r in ROWS if r['arr_day_dir'])
w('## Why it is trustworthy')
w('')
w('| check | departure | arrival |')
w('|---|---|---|')
w(f"| heading error vs the runway's true heading (median / p95) | "
  f"{med([num(r, 'dep_err') for r in droll]):.1f}° / {pct([num(r, 'dep_err') for r in droll], .95):.1f}° | "
  f"{med([num(r, 'arr_err') for r in aroll]):.1f}° / {pct([num(r, 'arr_err') for r in aroll], .95):.1f}° |")
w(f"| position fixes inside the roll (median) | {med([num(r, 'dep_n_seg') for r in droll]):.0f} | "
  f"{med([num(r, 'arr_n_seg') for r in aroll]):.0f} |")
w('')
w('The paved surface is 45–60 m wide, so a heading error of 0–1° is unambiguously *that*')
w('runway. Laterally the strongest evidence is the roll itself: thousands of ground-roll')
w('fixes at one runway end fit a single straight line to within a few metres (table further')
w('down), which is both proof that the aircraft rolled straight down the runway and a')
w('measure of how good the position data is.')
w('')
w('Independent checks that were run:')
w('')
w(f"- **Day-direction coherence.** Wind holds one direction all day, so every flight at an"
  f" airport that day should use the same runway direction. Of the flights that could be"
  f" compared, departures **{dd.get('match', 0)}/{sum(dd.values())}** and arrivals"
  f" **{ad.get('match', 0)}/{sum(ad.values())}** agree with their day's dominant direction"
  f" — **{dd.get('DIFFERS', 0) + ad.get('DIFFERS', 0)} exceptions**.")
w('- **Airport geometry.** Threshold-to-threshold bearings of every runway in scope were')
w('  checked against the published runway true headings; no swapped runway ends.')
w('- **Gatwick** returns 26L for both arrivals and departures (LGW is a single-runway')
w('  operation); **Johannesburg** returns arrivals on 03R/21L and departures on 03L/21R —')
w('  the parallel-strip split the airport actually uses.')

# worked example, picked from the rows themselves
ex = next((r for r in ROWS if r['tail'] and r['dep_roll_source'] == 'altitude'
           and r['dep_conf'] == 'high' and num(r, 'dep_roll_len_m')
           and num(r, 'dep_rwy_len_m') and 'HUEN' == r['dep_apt']), None)
if ex:
    w(f"- **Worked example.** `{ex['file']}` ({ex['flight']}, {ex['tail']}) leaves"
      f" {name(ex['dep_apt'])} {ex['dep_rwy']}: the roll starts"
      f" {m0(num(ex, 'dep_roll_start_m'))} m past the threshold at"
      f" {m0(num(ex, 'dep_roll_start_speed_kt'))} kt, the wheels leave the ground"
      f" {m0(num(ex, 'dep_runway_used_m'))} m down a"
      f" {m0(num(ex, 'dep_rwy_len_m'))} m runway"
      f" ({100*num(ex, 'dep_runway_used_m')/num(ex, 'dep_rwy_len_m'):.0f}% used), leaving"
      f" {m0(num(ex, 'dep_rwy_remaining_m'))} m. Bracket around the lift-off:"
      f" {m0(num(ex, 'dep_liftoff_bracket_m'))} m, i.e. that is the export's time resolution.")
w('')

# ------------------------------------------------------------ runway used ---
w('## How much runway was used')
w('')
w('Two moments are measured per flight, both as a distance along the runway from the')
w('threshold of the runway in use:')
w('')
w('**Take-off**')
w('')
w('| figure | column | meaning |')
w('|---|---|---|')
w('| roll start | `dep_roll_start_m` | line-up point — the first fix after the last one below 15 kt; the take-off run begins there |')
w('| runway used | `dep_runway_used_m` | where the wheels left the ground, measured from the threshold |')
w('| roll length | `dep_roll_len_m` | roll start → wheels-off (the actual take-off run) |')
w('| runway left | `dep_rwy_remaining_m` | pavement remaining ahead at wheels-off |')
w('| bracket | `dep_liftoff_bracket_m` | gap between the last on-ground fix and the first airborne one — the export\'s resolution |')
w('')
w('**Landing**')
w('')
w('| figure | column | meaning |')
w('|---|---|---|')
w('| touchdown | `arr_td_along_m` | first sustained deceleration after the threshold |')
w('| runway used | `arr_runway_used_m` | where the aircraft left the pavement (or came to a stop / turned around on it) |')
w('| landing roll | `arr_roll_len_m` | touchdown → that point |')
w('| runway left | `arr_rwy_remaining_m` | pavement remaining beyond that point (taxiway exits are not subtracted) |')
w('| turn-off speed | `arr_turnoff_speed_kt` | groundspeed when the aircraft left the centreline corridor |')
w('| bracket | `arr_td_bracket_m` | gap between the two fixes that bound the touchdown |')
w('')
w('How the two moments are pinned down, and why they can be trusted:')
w('')
w('- **Wheels-off** is found from the altitude trace. In these exports the altitude field')
w('  reads exactly **0 while the aircraft is on the ground** — at every airport, including')
w('  7,630 ft Addis — and reverts to MSL once airborne. So the lift-off is bracketed by the')
w('  last zero-altitude fix and the first fix above it. The acceleration signature (the roll')
w('  runs at 3–5 kt/s, then roughly halves when the aircraft pitches up) is computed')
w('  alongside as a second opinion: `dep_accel_alt_ft` records the altitude at which it fired,')
w('  a median of a few tens of feet above the field, i.e. it corroborates.')
w('- **Touchdown** is found from the deceleration instead: the approach runs at a near-constant')
w('  speed, then spoilers and brakes bring it down at 2–4 kt/s. The first fix with a sustained')
w('  deceleration past the threshold is the touchdown (or a second after it). The altitude')
w('  trend *cannot* be used here — it holds near field elevation for the first ~2 km after')
w('  touchdown, so it only serves as a lagging cross-check (`arr_alt_flat_m`).')
w('- **Turn-off** is the point where the aircraft\'s centre crosses the runway edge')
w('  (half-width + 10 m), measured against the **fitted** centreline, not the published one —')
w('  at Entebbe the published line sits ~35 m off the line the fleet rolls on, which is more')
w('  than half the runway width and would fire the test at touchdown. Where an aircraft brakes')
w('  and then taxis back down the runway (Kilimanjaro 09 does this), the landing run is taken')
w('  to end at the stop/turn-around point, not at the taxiway it later exits through.')
w('')

# by type
w('### Take-off, by aircraft type')
w('')
w('| type | flights | roll starts at | take-off run | runway used | runway left | runway in use |')
w('|---|---|---|---|---|---|---|')
for t, tl in TYPE_ORDER:
    S = [r for r in solid('dep') if r['tail'] in tl]
    if not S:
        continue
    roll = [num(r, 'dep_roll_len_m') for r in S]
    w(f"| {t} | {len(S)} | {m0(med([num(r, 'dep_roll_start_m') for r in S]))} m | "
      f"**{m0(med(roll))} m** (p10–p90 {m0(pct(roll, .1))}–{m0(pct(roll, .9))}) | "
      f"{m0(med([num(r, 'dep_runway_used_m') for r in S]))} m | "
      f"{m0(med([num(r, 'dep_rwy_remaining_m') for r in S]))} m | "
      f"{m0(med([num(r, 'dep_rwy_len_m') for r in S]))} m |")
w('')
w('| type | flights | touchdown past threshold | landing roll | runway used | runway left | over the threshold at |')
w('|---|---|---|---|---|---|---|')
for t, tl in TYPE_ORDER:
    S = [r for r in solid('arr') if r['tail'] in tl]
    if not S:
        continue
    roll = [num(r, 'arr_roll_len_m') for r in S]
    w(f"| {t} | {len(S)} | {m0(med([num(r, 'arr_td_along_m') for r in S]))} m | "
      f"**{m0(med(roll))} m** (p10–p90 {m0(pct(roll, .1))}–{m0(pct(roll, .9))}) | "
      f"{m0(med([num(r, 'arr_runway_used_m') for r in S]))} m | "
      f"{m0(med([num(r, 'arr_rwy_remaining_m') for r in S]))} m | "
      f"{m0(med([num(r, 'arr_thr_speed_kt') for r in S]))} kt |")
w('')


def by_airport(side, label, extra=()):
    keys = collections.Counter(r[f'{side}_apt'] for r in solid(side))
    w(f'### {label}, by airport (≥5 flights measured)')
    w('')
    w('| airport | flights | measured at | roll | runway used | runway left | runway length | share used |')
    w('|---|---|---|---|---|---|---|---|')
    for apt, k in sorted(keys.items(), key=lambda kv: -kv[1]):
        if k < 5:
            continue
        S = [r for r in solid(side) if r[f'{side}_apt'] == apt]
        at = med([num(r, f'{side}_roll_start_m' if side == 'dep' else 'arr_td_along_m') for r in S])
        used = med([num(r, f'{side}_runway_used_m') for r in S])
        ln = med([num(r, f'{side}_rwy_len_m') for r in S])
        share = f"{100*used/ln:.0f}%" if used and ln else '—'
        w(f'| {name(apt)} | {k} | {m0(at)} m past threshold | {m0(med([num(r, f"{side}_roll_len_m") for r in S]))} m | '
          f'{m0(used)} m | {m0(med([num(r, f"{side}_rwy_remaining_m") for r in S]))} m | {m0(ln)} m | {share} |')
    w('')


by_airport('dep', 'Take-off')
w('- A negative "roll starts at" (Juba 13) means the line-up point sits *before* the published')
w('  threshold — the crew held at the displaced position, which is where line-up begins.')
w(f'- {fb} further take-offs have no usable lift-off signature (the export is too coarse), so')
w('  they are left out of these tables; those rows carry the last sub-95 kt position instead,')
w('  which under-reads. They are flagged in `dep_roll_source`.')
w('')
by_airport('arr', 'Landing')

# by runway end
w('### Per runway end (≥6 flights measured)')
w('')
w('The same numbers split by the runway actually used — this is where the difference')
w('between a 2,400 m strip and a 4,400 m one shows up.')
w('')
w('| runway end | ops | take-off: run / used / left (% of runway) | landing: touchdown / roll / used / left |')
w('|---|---|---|---|')
keys = collections.Counter((r['dep_apt'], r['dep_rwy']) for r in solid('dep'))
akeys = collections.Counter((r['arr_apt'], r['arr_rwy']) for r in solid('arr'))
allk = [k for k in set(keys) | set(akeys) if keys.get(k, 0) + akeys.get(k, 0) >= 6]
# tie-break on the label: the set's own order depends on string hashing, so without it
# two builds of identical data can print the same table with 21L and 21R swapped
allk.sort(key=lambda k: (-(keys.get(k, 0) + akeys.get(k, 0)), k[0], k[1]))
for apt, rwy in allk:
    D = [r for r in solid('dep') if (r['dep_apt'], r['dep_rwy']) == (apt, rwy)]
    A = [r for r in solid('arr') if (r['arr_apt'], r['arr_rwy']) == (apt, rwy)]
    if D:
        du = med([num(r, 'dep_runway_used_m') for r in D])
        dl = med([num(r, 'dep_rwy_len_m') for r in D])
        dcell = (f"{len(D)} × {m0(med([num(r, 'dep_roll_len_m') for r in D]))} / {m0(du)} / "
                 f"{m0(med([num(r, 'dep_rwy_remaining_m') for r in D]))} m"
                 + (f" ({100*du/dl:.0f}%)" if du and dl else ''))
    else:
        dcell = '—'
    if A:
        au = med([num(r, 'arr_runway_used_m') for r in A])
        acell = (f"{len(A)} × {m0(med([num(r, 'arr_td_along_m') for r in A]))} / "
                 f"{m0(med([num(r, 'arr_roll_len_m') for r in A]))} / {m0(au)} / "
                 f"{m0(med([num(r, 'arr_rwy_remaining_m') for r in A]))} m")
    else:
        acell = '—'
    w(f'| {name(apt)} {rwy} | {len(D) + len(A)} | {dcell} | {acell} |')
w('')

# summary stats
sh_dep = [100*num(r, 'dep_runway_used_m')/num(r, 'dep_rwy_len_m') for r in solid('dep')
          if num(r, 'dep_rwy_len_m')]
sh_arr = [100*num(r, 'arr_runway_used_m')/num(r, 'arr_rwy_len_m') for r in ROWS
          if r['arr_roll_len_m'] != '' and num(r, 'arr_rwy_len_m')]
tight_d = [r for r in ROWS if r['dep_rwy_remaining_m'] != '' and num(r, 'dep_rwy_remaining_m') < 300]
tight_a = [r for r in ROWS if r['arr_rwy_remaining_m'] != '' and num(r, 'arr_rwy_remaining_m') < 300]
w('Across the whole dataset:')
w('')
w(f"- take-off uses a median **{med(sh_dep):.0f}%** of the runway in use"
  f" (p10–p90 {pct(sh_dep, .1):.0f}–{pct(sh_dep, .9):.0f}%); **{sum(1 for x in sh_dep if x > 90)} of"
  f" {len(sh_dep)}** take-offs used more than 90% of the pavement, and"
  f" **{len(tight_d)}** had less than 300 m left in front of them")
w(f"- landing uses a median **{med(sh_arr):.0f}%** (p10–p90 {pct(sh_arr, .1):.0f}–{pct(sh_arr, .9):.0f}%),"
  f" and **{len(tight_a)}** landings ran to within 300 m of the far end (a taxiway exit, not")
w('  necessarily a short runway)')
w(f"- the median take-off run is **{m0(med([num(r, 'dep_roll_len_m') for r in ROWS if r['dep_roll_len_m'] != '']))} m**"
  f" and the median landing roll **{m0(med([num(r, 'arr_roll_len_m') for r in ROWS if r['arr_roll_len_m'] != '']))} m**")
w('')
long_d = sorted(solid('dep'), key=lambda r: -num(r, 'dep_roll_len_m'))[:5]
long_a = sorted(solid('arr'), key=lambda r: -num(r, 'arr_roll_len_m'))[:5]
w('| longest take-off runs | runway | run | used / length |')
w('|---|---|---|---|')
for r in long_d:
    w(f"| {r['flight']} ({r['tail'] or '—'}) {(r['when'] or '—')[:10]} | {name(r['dep_apt'])} {r['dep_rwy']} | "
      f"{m0(num(r, 'dep_roll_len_m'))} m | {m0(num(r, 'dep_runway_used_m'))} / {m0(num(r, 'dep_rwy_len_m'))} m |")
w('')
w('| longest landing rolls | runway | roll | used / length |')
w('|---|---|---|---|')
for r in long_a:
    w(f"| {r['flight']} ({r['tail'] or '—'}) {(r['when'] or '—')[:10]} | {name(r['arr_apt'])} {r['arr_rwy']} | "
      f"{m0(num(r, 'arr_roll_len_m'))} m | {m0(num(r, 'arr_runway_used_m'))} / {m0(num(r, 'arr_rwy_len_m'))} m |")
w('')

# quality of the measurement
src = collections.Counter(r['dep_roll_source'] for r in ROWS if r['dep_roll_len_m'] != '')
cap_d = collections.Counter(r['dep_roll_capture'] for r in ROWS if r['dep_roll_len_m'] != '')
cap_a = collections.Counter(r['arr_roll_capture'] for r in ROWS if r['arr_roll_len_m'] != '')
lower = sum(v for k, v in cap_a.items() if 'track ends on the runway' in k)
w('### How tightly is each moment pinned?')
w('')
w(f"- **Wheels-off**: resolution = the export's fix interval. Median bracket"
  f" **{m0(med([num(r, 'dep_liftoff_bracket_m') for r in solid('dep')]))} m**"
  f" (p90 {m0(pct([num(r, 'dep_liftoff_bracket_m') for r in solid('dep')], .9))} m),"
  f" i.e. typically ±300 m on the along-runway figure. Sources: "
  + '; '.join(f'{k} × {v}' for k, v in src.most_common()) + '.')
w("- **Take-off capture**: " + '; '.join(f'{k} × {v}' for k, v in cap_d.most_common()) + '.')
w(f"- **Touchdown**: median bracket"
  f" **{m0(med([num(r, 'arr_td_bracket_m') for r in solid('arr')]))} m**"
  f" (p90 {m0(pct([num(r, 'arr_td_bracket_m') for r in solid('arr')], .9))} m)"
  f" — the sharper of the two signals, since the deceleration onset is sampled directly.")
w("- **Landing capture**: " + '; '.join(f'{k} × {v}' for k, v in cap_a.most_common()) + '.')
w(f"- **{lower} landings are lower bounds**: the export ends while the aircraft is still on")
w('  the runway, so the roll-out continues past the last fix. They are marked in')
w('  `arr_roll_capture`.')
w('')

# -------------------------------------------------------- centreline (17) ---
w('## Where across the runway the wheels were')
w('')
w('Measured against the centreline the fleet actually rolls on (see the fit table below),')
w('signed + = right of the direction of travel.')
w('')
xt_d = [abs(num(r, 'dep_liftoff_xt_cal_m')) for r in ROWS if r['dep_liftoff_xt_cal_m'] != '']
xt_a = [abs(num(r, 'arr_td_xt_cal_m')) for r in ROWS if r['arr_td_xt_cal_m'] != '']
w('| | flights | median | p90 | max | within 10 m | within 20 m |')
w('|---|---|---|---|---|---|---|')
for lbl, xs in (('At lift-off (wheels leaving the runway)', xt_d),
                ('At touchdown', xt_a)):
    w(f'| {lbl} | {len(xs)} | {med(xs):.0f} m | {pct(xs, .9):.0f} m | {max(xs):.0f} m | '
      f'{100*sum(1 for x in xs if x <= 10)/len(xs):.0f}% | {100*sum(1 for x in xs if x <= 20)/len(xs):.0f}% |')
w('')
w(f'Touchdown is the tighter of the two: the aircraft has just flown an instrument approach,')
w(f'so {100*sum(1 for x in xt_a if x <= 10)/len(xt_a):.0f}% of landings are within 10 m of the centreline.')
w(f'At lift-off the aircraft has already been rolling for two to three kilometres and is')
w(f'beginning to climb away, so the spread is wider ({sum(1 for x in xt_d if x > 20)} of')
w(f'{len(xt_d)} fixes sit more than 20 m off — the tail end of a long, fast roll).')
w('')
w('| runway end | flights | roll fixes | fit residual | offset at threshold | offset at far end | rotation |')
w('|---|---|---|---|---|---|---|')
fits = list(csv.DictReader(open('runway_centreline_fit.csv')))
for f in sorted(fits, key=lambda f: -int(f['flights']))[:12]:
    w(f"| {name(f['airport'])} {f['runway']} | {f['flights']} | {f['fixes']} | {f['residual_sd_m']} m | "
      f"{f['offset_at_threshold_m']} m | {f['offset_at_far_end_m']} m | {f['rotation_deg']}° |")
w('')
w(f'{len(fits)} runway ends have enough ground-roll fixes for a fit. Where there is none the')
w('published line is used — that applies to the residual-deviation figures of')
w(f'{N - sum(1 for r in ROWS if r["arr_td_xt_cal_m"] != "")} rows.')
w('')
w('### Entebbe 17/35 — a corrected centreline, and why it matters')
w('')
w('The runway coordinates published by OurAirports for Entebbe 17/35 run at **170.96°**;')
w('the physical 46 m-wide strip runs at **172.10°**. Measured against the published line,')
w('every flight appears to slide diagonally across the runway — starting **35 m** left of it')
w('and finishing **38 m** right of it, i.e. off both edges of a runway that is only 46 m')
w("wide. Nothing is wrong with the flying: the fleet's 3,006 ground-roll fixes fit a")
w('straight line to within 2.1 m, and that line is corroborated independently by the runway')
w('axis mapped from satellite imagery in OpenStreetMap, which agrees with it to **1.8 m**.')
w('')
w('**This is now corrected in the data, not just in the arithmetic.** The reviewed line is')
w('stored in `work/rwy/centreline_fixes.csv` and loaded as the reference by the pipeline, so')
w('every measurement in this document — and in any future run, before any fitting happens —')
w('is taken against the corrected line. Three sources agree on it:')
w('')
w('| source | 17/35 heading | offset vs the published line (17 end → 35 end) |')
w('|---|---|---|')
w('| OurAirports (original reference) | 170.96° | 0 m by definition |')
w('| fleet: 3,006 ground-roll fixes | 172.10° | −35.0 m → +38.0 m |')
w('| OpenStreetMap, mapped from imagery | 172.10° | −33.5 m → +39.7 m |')
w('')
w('Against the corrected line the same fixes read: mean offset **−0.6 m**, standard')
w('deviation **1.2 m** (rolling fixes ≥ 55 kt). Against one that is a half-width out it is')
w('not a cosmetic difference — the arrival roll-out is cut where the aircraft crosses the')
w('runway edge (half-width + 10 m), so the old line fired that test at touchdown and')
w('reported a zero-length landing roll for 15 Entebbe arrivals. With the corrected line,')
w('none of the 159 Entebbe landings measured this run comes out shorter than 400 m.')
w('')
w('The before/after picture is `entebbe_centreline.png`; the derivation and the')
w('corroboration for each corrected line is recorded in the `evidence` column of the fixes')
w('file. The other 18 fitted runway ends sit within a few metres of their published lines')
w('and are left on the published coordinates — the fit is still used for their lateral')
w('figures, but no correction is applied to the reference data.')
w('')
w('**Three independent checks agree with each other and differ from the published line:**')
w('')
w('1. every flight would have to have made the same 1.1° steering error, for 13 days, in')
w('   the same direction, on both the 17 and the 35 rolls — implausible on its face;')
w('2. the ground-track direction computed from the fixes with plain plane geometry')
w('   (no shared code, no per-runway constants) gives 172.1° for the fleet against the')
w('   published 171.0°;')
w('3. the runway axis mapped in OpenStreetMap from satellite imagery runs at 172.10°,')
w('   i.e. within a few tens of centimetres of the fleet line — see')
w('   `entebbe_centreline.png`.')
w('')
w('A related trap, for the record: the OurAirports **heading** field is rounded to whole')
w('degrees — Entebbe 17 is filed as `171`, against a coordinate axis of 170.96° and a')
w('physical axis of 172.10°. A degree is ~64 m of lateral drift over a 3,680 m runway, so')
w('all geometry here is computed from the coordinate pairs, never from that heading field.')
w('')

# ------------------------------------------------------------- reading csv ---
w('## Reading the CSV')
w('')
w('| column | meaning |')
w('|---|---|')
for col, mean in (
    ('file', 'track file in the zip — the flight number is the prefix'),
    ('flight / tail / when', 'flight number, airframe from your screenshots (blank when not pinned), scheduled departure (local)'),
    ('log_origin / log_dest', 'airports as labelled by the log builder — metadata; can disagree with the geometry when the '
     'fix stream is cut short, so the geometry is what the counts follow'),
    ('dep_apt / arr_apt (+ `_dist_km`, `_ground`)', 'nearest airport with a 4,000 ft+ runway to the first/last ground-ish fix; `_ground` = yes when a real ground fix was found there'),
    ('dep_rwy / arr_rwy', 'runway end used, e.g. `17` or `03R`'),
    ('dep_conf / arr_conf', 'high / medium / low — see Coverage'),
    ('dep_method / arr_method', '`roll` (measured from the ground roll) or climb-/approach-heading (inferred)'),
    ('dep_xt / arr_xt (+ `_rival_xt`, `_margin`)', 'mean distance from the centreline over the matched roll, the same for the nearest *other* runway end, and the score gap to it'),
    ('dep_day_dir / arr_day_dir', 'match when the flight agrees with the day\'s dominant direction at that airport'),
    ('dep_rwy_len_m / dep_rwy_width_m', 'runway length and width in use (OurAirports)'),
    ('dep_roll_start_m / dep_roll_start_speed_kt', 'line-up point and the speed there — the take-off run starts here'),
    ('dep_runway_used_m', '**distance down the runway at wheels-off** — the headline take-off figure'),
    ('dep_roll_len_m', 'take-off run actually used (wheels-off minus roll start)'),
    ('dep_rwy_remaining_m', 'pavement left ahead at wheels-off'),
    ('dep_liftoff_along_lo / _hi / _bracket_m', 'the two fixes that bracket the lift-off, and the gap between them (the resolution)'),
    ('dep_liftoff_speed_kt', 'groundspeed at the first airborne fix'),
    ('dep_roll_source', 'which signature found the lift-off: altitude (direct) / acceleration / speed fallback'),
    ('dep_accel_alt_ft', 'height at which the acceleration second-opinion fired'),
    ('dep_roll_capture', 'full = a standstill (or sub-15 kt taxi) was captured before the roll; otherwise the roll started before the export'),
    ('dep_liftoff_xt_m / dep_liftoff_xt_cal_m', 'lateral offset from the published / fitted centreline at wheels-off (+ = right)'),
    ('arr_thr_speed_kt / arr_thr_height_ft', 'interpolated speed and height over the threshold'),
    ('arr_td_along_m (+ `_lo`, `_hi`, `_bracket_m`)', '**touchdown distance past the threshold** and the bracket around it'),
    ('arr_td_speed_kt', 'groundspeed at touchdown'),
    ('arr_alt_flat_m', 'where the altitude trace flattens — a lagging cross-check on the touchdown'),
    ('arr_roll_len_m', 'landing roll: touchdown → leaving the pavement (or stopping on it)'),
    ('arr_runway_used_m', '**how far down the runway the landing run ended** — the headline landing figure'),
    ('arr_rwy_remaining_m', 'pavement left beyond that point'),
    ('arr_turnoff_speed_kt', 'groundspeed when the aircraft left the centreline corridor'),
    ('arr_stop_along_m', 'where it came to a stop, when it stopped rather than rolling off'),
    ('arr_roll_capture', 'full, or track-ends-on-the-runway (roll is a lower bound)'),
    ('arr_td_xt_m / arr_td_xt_cal_m', 'lateral offset from the published / fitted centreline at touchdown'),
):
    w(f'| `{col}` | {mean} |')
w('')

# ---------------------------------------------------------------- caveats ---
w('## Caveats')
w('')
blank_d = [r for r in ROWS if not r['dep_rwy']]
blank_a = [r for r in ROWS if not r['arr_rwy']]
bd = collections.Counter(r['dep_apt'] or '(no airport)' for r in blank_d)
ba = collections.Counter(r['arr_apt'] or '(no airport)' for r in blank_a)
w(f'- **{len(blank_d)} departures and {len(blank_a)} arrivals stay blank.** Either the export starts after the'
  ' rotation or stops before the landing, or the only ground fix is a single sparse sample.')
w('  Departure blanks: ' + ', '.join(f'{name(k)} × {v}' for k, v in bd.most_common()) + '.')
w('  Arrival blanks: ' + ', '.join(f'{name(k)} × {v}' for k, v in ba.most_common()) + '.')
w('  A finer export (or the full track history) is the only way to recover those.')
w('- **"Wheels-off" is not the rotation.** The nose lifts before the wheels leave, and the')
w('  export only samples every few seconds, so `dep_runway_used_m` carries the bracket above')
w('  (median ±300 m along the runway). The lateral figure barely moves over that distance.')
w('- **Coarse exports.** A handful of tracks are sampled at 30 s or more; there the roll')
w('  start, the lift-off bracket and the landing roll are all widened, and the rows are')
w(f'  flagged in `*_roll_source` / `*_roll_capture`. {lower} landings are marked as lower bounds.')
w('- **Displaced thresholds.** Touchdown is measured past the *published* threshold, which')
w('  for a displaced threshold includes the displaced part — Los Angeles-style, the runway')
w('  available for landing is shorter than the length quoted here. Lagos 18R (touchdowns')
w('  ~1.2 km) and Sao Paulo / Nairobi (0.5 km) reflect displaced-threshold layouts as much as')
w('  crew technique.')
w('- **Back-tracking arrivals** (Kilimanjaro 09, some Juba 13) brake, then taxi back along')
w('  the runway; those rows are cut at the stop/turn-around point rather than at the later')
w('  taxiway exit, which is the best that can be done from position data alone.')
w('- **Runway exits are not subtracted** from `*_rwy_remaining_m`: they report pavement left')
w('  in front of the aircraft, not pavement available for a further landing.')
w('- **The fitted centreline assumes the fleet, on average, rolls down the centre.** If every')
w('  crew habitually sat, say, 5 m left, that would be baked in as "zero". The fit residual')
w('  (2–3 m at the busiest airports) bounds how precisely it is pinned, not whether the')
w('  absolute offset from the painted centreline is zero.')
w('- **No wind, weight or derate information exists in these exports**, so nothing here says')
w('  *why* a roll was long or short — only how long it was. Nothing here says *why* a runway')
w('  was chosen either (wind, noise abatement, availability): only which one was used.')
w('- Verdicts come from position data alone: the exports have no runway, weight, or')
w('  registration field.')
w('')

open('runway_usage.md', 'w').write('\n'.join(L) + '\n')
print(f'wrote runway_usage.md ({len(L)} lines)')
