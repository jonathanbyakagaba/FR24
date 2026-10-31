#!/usr/bin/env python3
"""Regenerate the triangle-route write-up from the current published tables.

Reads triangle_assignments.csv, tails.csv and fleet_summary.csv, and writes
triangle_routes.md — the narrative companion to the flat tables, published by
work/publish_layers.py.
"""
import csv, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from month_ctx import ctx
import repo_layout
from datetime import datetime, timezone

TRI = 'triangle_assignments.csv'
TAILS = 'tails.csv'
FLEET = 'fleet_summary.csv'
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fr24_publish',
              os.path.basename(repo_layout.live_dir()), 'triangle_routes.md')   # this month's folder

MON = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
       '07': 'Jul', '08': 'Aug', '09': 'Sep'}
ROLE = {'long': 'long-haul', 'medium': 'medium-haul', 'short': 'short-haul'}


def pretty(d):
    y, m, dd = d.split('-')
    return f'{dd} {MON[m]}' if y == '2026' else d


def chain_of(legs):
    """Order the day's legs into a route string, starting at Entebbe if present."""
    segs = {}
    for c in legs:
        segs.setdefault(c['origin'], c['dest'])
    if not segs:
        return ''
    start = 'EBB' if 'EBB' in segs else sorted(segs)[0]
    order, cur = [], start
    for _ in range(len(segs)):
        nxt = segs.get(cur)
        if not nxt:
            break
        order.append(f'{cur}–{nxt}')
        cur = nxt
    rest = [f"{c['origin']}–{c['dest']}" for c in legs
            if f"{c['origin']}–{c['dest']}" not in order]
    return ' → '.join(order + rest)


def main():
    tri = list(csv.DictReader(open(TRI)))
    tails = list(csv.DictReader(open(TAILS)))
    fleet = list(csv.DictReader(open(FLEET)))
    by = collections.defaultdict(list)
    for r in tails:
        by[(r['tail'], r['date'], r['callsign'])].append(r)

    hz = [t for t in tri if {t['origin'], t['dest']} == {'HRE', 'LUN'}]
    zj = [t for t in tri if {t['origin'], t['dest']} == {'ZNZ', 'JRO'}]
    per_tail = collections.Counter(t['tail'] for t in tri)
    ver = sum(1 for t in tri if t['verified_track'] == 'Y')
    dates = sorted(t['date'] for t in tri)

    L = []
    L.append('# Triangle (fifth-freedom) routes — aircraft assignment\n')
    L.append('**Source:** the FR24 aircraft-history screenshots for all five airframes — '
             'three captures (11 Sep 12:43–12:46, 12 Sep 09:39–09:40, 22 Sep 07:59–08:04).')
    L.append(f"**Window covered:** {pretty(dates[0])} – {pretty(dates[-1])} 2026 "
             f"({len(tails)} screenshot rows, {len(tri)} non-Entebbe sectors).")
    L.append(f"**Rebuilt:** {datetime.now(timezone.utc):%d %b %Y} from the published tables "
             '(`triangle_assignments.csv`, `tails.csv`, `fleet_summary.csv`).\n')
    L.append('---\n')
    L.append('## 1. The two triangle routes\n')
    L.append('Both triangles exist in the archive as well as in the screenshots.\n')
    L.append('**Triangle A — Entebbe / Harare / Lusaka (true fifth freedom)**\n'
             '`UR722 = EBB → HRE → LUN → EBB` and `UR720 = EBB → LUN → HRE → EBB`.\n'
             'The **HRE–LUN / LUN–HRE sector** is flown between Zimbabwe and Zambia by a Ugandan\n'
             'carrier — a genuine fifth-freedom sector (2,004 km / 1,765 km legs).\n')
    L.append('**Triangle B — Entebbe / Zanzibar / Kilimanjaro**\n'
             '`UR334 = EBB → ZNZ → JRO → EBB`.\n'
             'The **ZNZ–JRO sector** is inside Tanzania, so it is cabotage rather than fifth\n'
             'freedom — worth keeping distinct in any traffic-rights or yield work.\n')
    L.append('---\n')
    L.append('## 2. Every non-Entebbe sector flown (the fifth-freedom legs)\n')
    L.append('| Date (app) | Flight | Callsign | Sector | Aircraft | That day\'s chain | In archive |')
    L.append('|---|---|---|---|---|---|---|')
    for t in sorted(tri, key=lambda x: (x['date'], x['tail'], x['flight'])):
        ch = chain_of(by.get((t['tail'], t['date'], t['callsign']), []))
        L.append(f"| {pretty(t['date'])} | {t['flight']} | {t['callsign']} | "
                 f"{t['origin']}–{t['dest']} | **{t['tail']}** | {ch} | "
                 f"{'yes' if t['verified_track'] == 'Y' else '—'} |")
    L.append('')
    who = ' · '.join(f'{k} **{v}**' for k, v in per_tail.most_common())
    hz_who = collections.Counter(t['tail'] for t in hz).most_common()
    zj_who = collections.Counter(t['tail'] for t in zj).most_common()
    L.append(f'**Who flew them:** {who}.\n')
    L.append(f"- HRE–LUN / LUN–HRE (**{len(hz)}** legs): "
             + ', '.join(f'{k} {v}' for k, v in hz_who) + '.')
    L.append(f"- ZNZ–JRO (**{len(zj)}** legs): " + ', '.join(f'{k} {v}' for k, v in zj_who) + '.')
    L.append(f'\n**{ver} of {len(tri)}** legs are matched by a track in the published archive; the rest were '
             'flown on days the daily export does not cover, or depart after 21:00 UTC, where the app dates '
             'the leg to the UTC day and the archive files it on the next local day.\n')
    L.append('---\n')
    L.append('## 3. Fleet summary (archive-verified flying only)\n')
    L.append('| Tail | Type | Role | Flights | Air hours | Routes | Median cruise | Typical FL | Min to FL300 |')
    L.append('|---|---|---|---|---|---|---|---|---|')
    order = ['5X-NIL', 'ET-APL', '5X-KOB', '5X-KDP', '5X-EQU']
    for t in order:
        r = next((x for x in fleet if x['tail'] == t), None)
        if not r:
            continue
        L.append(f"| {t} | {r['type']}{' (wet lease)' if r['ownership'].startswith('wet') else ''} | "
                 f"{ROLE.get(r['role'], r['role'])} | {r['flights_matched']} | {r['air_hours']} | "
                 f"{r['routes']} | {r['median_cruise_kt']} kt | FL{r['median_max_FL']} | "
                 f"{r['median_min_to_FL300']} |")
    L.append('')
    L.append('---\n')
    L.append('## 4. Things worth checking\n')
    L.append('1. **Night legs sit a day apart in the two sources.** The app dates a leg by its UTC\n'
             '   departure day, `flights.csv` by the departure airport\'s local day. A 23:22Z Mombasa\n'
             '   return shows as "Sep 20" in the app and `21SEP26` in the log, so the two cannot be\n'
             '   joined on date alone. Seven rows are bridged that way, each one provable because the\n'
             '   track left inside the last hours of the app\'s UTC day — including the four\n'
             f'   MBA–EBB / EBB–MBA legs that were the last gap in the {ctx()["name"]} aircraft cover.\n'
             '   Where the app\'s date is a day earlier and the export\'s track left in daylight, the\n'
             '   two readings cannot be told apart, so those 17 rows stay unjoined and are listed in\n'
             '   `data_gaps.md` instead.\n')
    L.append('2. **CRJ900 legs to Johannesburg.** Rows place JNB on CRJ900 pages (e.g. `5X-KOB 16 Sep\n'
             '   UR711 JNB–EBB`, `5X-EQU 18 Sep UR710 EBB–JNB`). EBB–JNB is 2,946 km — at the\n'
             '   published limit of the type — so either those were payload-restricted legs or FR24\n'
             '   mis-assigned the aircraft. The screen rows themselves were confirmed at 4× zoom.\n')
    L.append('3. **The app prints some legs twice.** Four rows (UR430 9 Sep BOM, UR207 1 Sep NBO,\n'
             '   UR200 7 Sep NBO, UR206 8 Sep NBO) appear once with a callsign and once without;\n'
             '   `final.py` collapses them, and the coloured row wins over the grey one.\n')
    L.append('4. **Lagos is clean.** Every LOS row is ET-APL; the earlier "CRJ900 to Lagos" flag was a\n'
             '   first-pass transcription error and is closed.\n')
    L.append('---\n')
    L.append('## 5. Files\n')
    L.append('| File | Contents |')
    L.append('|---|---|')
    L.append(f"| `tails.csv` | all {len(tails)} screenshot rows: tail, date, flight, callsign, origin, dest, "
             'triangle flag, archive-verified flag, app status |')
    L.append(f"| `triangle_assignments.csv` | the {len(tri)} non-Entebbe sectors only, with aircraft |")
    L.append('| `fleet_summary.csv` | per-tail type, ownership, role and flying statistics |')
    L.append('| `work/screens_20260922_final.csv` | the 22 Sep batch as transcribed and verified against the '
             'captures — the audit trail back to the screenshots |')
    L.append('| `work/records.json` | raw parsed rows from the 11 Sep batch |\n')

    text = '\n'.join(L)
    open(OUT, 'w').write(text)
    print(f'wrote {OUT}: {len(text)} bytes, {text.count(chr(10))} lines')


if __name__ == '__main__':
    main()
