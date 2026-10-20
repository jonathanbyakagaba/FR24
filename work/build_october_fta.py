#!/usr/bin/env python3
"""
October 2026: join the FTA utilization plans (work/fta_oct2026.csv, transcribed
from fta.ugandairlines.com day plans 1-16 Oct 2026) to the rebuilt flight log.

Run AFTER work/rebuild_month.py has produced UR OCTOBER 2026/flights.csv,
then run rebuild_month.py once more so tails attach to flights/fleet/triangles.

Writes:
  * appends FTA-based rows to UR OCTOBER 2026/tails.csv (app_status left blank;
    provenance: FTA plan, see README/SUPPORTING)
  * UR OCTOBER 2026/schedule_delays.csv  (FTA basis, replaces the timetable build)
  * UR OCTOBER 2026/punctuality.csv      (FTA-STD basis for matched flights)
  * UR OCTOBER 2026/data_gaps.md         (planned legs with no FR24 track)

Matching: same flight number + endpoints, actual takeoff within [-90 min, +8 h]
of the plan STD (takeoff lags off-block by taxi-out). Multi-sector track files
(sectors_in_file > 1 in the internal rebuild) also match legs whose STD falls
inside the file's flown window. Actual times are takeoff/landing (airborne
events), so departure delay vs STD includes taxi-out (~15-30 min): read
dep_delay_min with that offset in mind.
"""
import csv, statistics, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from rebuild_month import AIRPORTS  # noqa: E402

FOLDER = Path("UR OCTOBER 2026")
TYPE_OF = {"5X-KDP": "CRJ9", "5X-EQU": "CRJ9", "5X-KOB": "CRJ9", "5X-NIL": "A332", "ET-APL": "A359"}
TRI_SECTOR = {"UR207", "UR209", "UR334", "UR343"}

def parse_utc(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)

legs, seen = [], set()
for r in csv.DictReader(open("work/fta_oct2026.csv")):
    if r["flight"] == "NONSKED":
        continue
    otz = ZoneInfo(AIRPORTS[r["origin"]][4]); dtz = ZoneInfo(AIRPORTS[r["dest"]][4])
    d0 = datetime.strptime(r["date"] + " " + r["std"], "%Y-%m-%d %H:%M").replace(tzinfo=otz)
    a0 = datetime.strptime(r["date"] + " " + r["sta"], "%Y-%m-%d %H:%M").replace(tzinfo=dtz)
    std_utc = d0.astimezone(timezone.utc); sta_utc = a0.astimezone(timezone.utc)
    if sta_utc < std_utc + timedelta(minutes=20):
        sta_utc += timedelta(days=1)
    key = (r["flight"], r["origin"], r["dest"], std_utc)
    if key in seen:  # duplicate plan listing of one leg (e.g. UR323 1 Oct, two regs)
        continue
    seen.add(key)
    legs.append(dict(**r, std_utc=std_utc, sta_utc=sta_utc))

flights = list(csv.DictReader(open(FOLDER / "flights.csv")))
for f in flights:
    f["_dep"] = parse_utc(f["departure_utc"]); f["_arr"] = parse_utc(f["arrival_utc"])
    fno = f["flight"]
    if fno.startswith("UGD"):
        fno = "UR" + fno[3:]
    elif fno.startswith("UG"):
        fno = "UR" + fno[2:]
    if fno.startswith("UR") and fno.endswith("D") and fno[2:-1].isdigit():
        fno = fno[:-1]  # suffixed recovery legs: UGD323D = UR323, UGD121D = UR121, UGD207D = UR207
    f["_fno"] = fno

used = set()
for leg in legs:
    best, best_dt = None, None
    for f in flights:
        if f["_fno"] != leg["flight"] or f["origin"] != leg["origin"] or f["dest"] != leg["dest"]:
            continue
        dt = (f["_dep"] - leg["std_utc"]).total_seconds() / 60.0
        if -240 <= dt <= 480 and (best_dt is None or abs(dt) < abs(best_dt)):
            best, best_dt = f, dt
    if best is None:  # multi-sector file: leg inside the flown window
        for f in flights:
            if f["_fno"] == leg["flight"] and f["_dep"] - timedelta(minutes=90) <= leg["std_utc"] <= f["_arr"]:
                best, best_dt = f, (f["_dep"] - leg["std_utc"]).total_seconds() / 60.0
                break
    leg["track"] = best
    if best is not None:
        used.add(best["source_file"])

def delay_label(d):
    return "early" if d < 0 else "on time" if d <= 15 else "delayed" if d <= 60 else "heavily delayed"

# ---- schedule_delays.csv -----------------------------------------------------
op_dep = defaultdict(list); op_arr = defaultdict(list)
for leg in legs:
    if leg["track"]:
        k = (leg["flight"], leg["origin"], leg["dest"])
        op_dep[k].append(leg["track"]["_dep"].timestamp()); op_arr[k].append(leg["track"]["_arr"].timestamp())
rows = []
for leg in sorted(legs, key=lambda l: (l["std_utc"], l["flight"])):
    t = leg["track"]; k = (leg["flight"], leg["origin"], leg["dest"])
    dep_d = arr_d = ""
    if t:
        dep_d = round((t["_dep"] - leg["std_utc"]).total_seconds() / 60.0)
        arr_d = round((t["_arr"] - leg["sta_utc"]).total_seconds() / 60.0)
    med_dep = datetime.fromtimestamp(statistics.median(op_dep[k]), timezone.utc) if len(op_dep[k]) >= 3 else None
    med_arr = datetime.fromtimestamp(statistics.median(op_arr[k]), timezone.utc) if len(op_arr[k]) >= 3 else None
    rows.append(dict(
        date=leg["date"], day=leg["std_utc"].astimezone(ZoneInfo(AIRPORTS[leg["origin"]][4])).strftime("%a"),
        flight=leg["flight"], from_=leg["origin"], to=leg["dest"], aircraft=TYPE_OF.get(leg["reg"], ""),
        dep_local=leg["std"], arr_local=leg["sta"],
        sched_dep_utc=leg["std_utc"].strftime("%Y-%m-%d %H:%MZ"),
        sched_arr_utc=leg["sta_utc"].strftime("%Y-%m-%d %H:%MZ"),
        sched_block_min=round((leg["sta_utc"] - leg["std_utc"]).total_seconds() / 60.0),
        fr24_status=("flown (track " + t["source_file"] + ")") if t else "no FR24 track",
        actual_utc=t["departure_utc"] if t else "", status=leg["status"].lower(),
        state="observed" if t else "no_track", basis="FTA utilization plan",
        dep_delay_min=dep_d, arr_delay_min=arr_d,
        punctuality=delay_label(dep_d) if dep_d != "" else "",
        clock_note="delays vs FTA STD/STA; actual = takeoff/landing (airborne), so dep delay includes taxi-out",
        op_median_dep_utc=med_dep.strftime("%H:%MZ") if med_dep else "",
        sched_vs_op_min=(lambda dd: round(dd - 1440 if dd > 720 else dd))(((med_dep.hour*60+med_dep.minute) - (leg["std_utc"].hour*60+leg["std_utc"].minute)) % 1440) if med_dep else "",
        sched_vs_op_arr_min="", compare_ok="Y" if t else "", compare_note="" if t else "planned leg, no track in FR data",
        op_median_block_min=round((med_arr - med_dep).total_seconds()/60.0) if med_dep and med_arr else "",
        op_median_air_min="", block_slack_min="", baseline_legs=len(op_dep[k]),
        baseline_spread_min=""))
cols = list(rows[0].keys())
with open(FOLDER / "schedule_delays.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)

# ---- punctuality.csv ----------------------------------------------------------
prows = []
for leg in sorted(legs, key=lambda l: (l["std_utc"], l["flight"])):
    t = leg["track"]
    if not t: continue
    dep_d = round((t["_dep"] - leg["std_utc"]).total_seconds() / 60.0)
    arr_d = round((t["_arr"] - leg["sta_utc"]).total_seconds() / 60.0)
    prows.append(dict(date=t["date_local"], flight=t["flight"], origin=leg["origin"], dest=leg["dest"],
        tail=leg["reg"], dep_local=t["takeoff_local"], dep_utc=t["departure_utc"], app_status="",
        punctuality=delay_label(dep_d), dep_delay_min=dep_d, arr_delay_min=arr_d,
        sched_dep_utc=leg["std_utc"].strftime("%Y-%m-%d %H:%M:%SZ"),
        sched_arr_utc=leg["sta_utc"].strftime("%Y-%m-%d %H:%M:%SZ"),
        slot_basis="FTA utilization plan STD", slot_regular="Y", source_file=t["source_file"]))
# date_local back to ISO for punctuality
MONTHS = {m: i for i, m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"], 1)}
for r in prows:
    d = r["date"]; r["date"] = f"20{d[5:]}-{MONTHS[d[2:5]]:02d}-{d[:2]}"
pcols = ["date","flight","origin","dest","tail","dep_local","dep_utc","app_status","punctuality",
         "dep_delay_min","arr_delay_min","sched_dep_utc","sched_arr_utc","slot_basis","slot_regular","source_file"]
with open(FOLDER / "punctuality.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=pcols); w.writeheader(); w.writerows(prows)

# ---- tails.csv additions -------------------------------------------------------
existing = list(csv.DictReader(open(FOLDER / "tails.csv")))
have = {(r["date"], r["flight"], r["origin"], r["dest"]) for r in existing}
tcols = list(existing[0].keys())
added = 0
with open(FOLDER / "tails.csv", "a", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=tcols)
    for leg in sorted(legs, key=lambda l: (l["date"], l["std_utc"])):
        key = (leg["date"], leg["flight"], leg["origin"], leg["dest"])
        if key in have: continue
        have.add(key)
        w.writerow(dict(tail=leg["reg"], date=leg["date"], flight=leg["flight"],
                        callsign="UGD" + leg["flight"][2:], origin=leg["origin"], dest=leg["dest"],
                        triangle_sector="Y" if leg["flight"] in TRI_SECTOR and leg["origin"] != "EBB" else "",
                        verified_track="", track_date="", app_status=""))
        added += 1

# ---- data_gaps.md --------------------------------------------------------------
man = list(csv.DictReader(open(FOLDER / "manifest.csv")))
last_fix = max(datetime.strptime(r["last_utc"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) for r in man)
missing = [l for l in legs if not l["track"] and l["status"] in ("SCHEDULED", "DELAYED", "RESCHEDULED")]
at_end = [l for l in missing if l["std_utc"] > last_fix - timedelta(hours=2)]
true_gaps = [l for l in missing if l not in at_end]
lines = ["# Data gaps — FTA-planned legs with no FR24 track (rebuilt 2026-10-20)", "",
         f"{len(true_gaps)} planned operating legs (1–16 Oct 2026) have no track in `FR data.zip`, plus",
         f"{len(at_end)} leg(s) scheduled at/after the export's last fix ({last_fix.strftime('%Y-%m-%d %H:%MZ')})",
         "that cannot be verified either way.",
         "Source: FTA utilization plans (work/fta_oct2026.csv) joined to flights.csv by",
         "work/build_october_fta.py. CANCELLED and NON_SCHEDULED plan rows are not gaps.", "",
         "## Legs with no track", "",
         "| date | flight | route | STD (local) | reg | plan status |", "|---|---|---|---|---|---|"]
for l in true_gaps:
    lines.append(f"| {l['date']} | {l['flight']} | {l['origin']}-{l['dest']} | {l['std']} | {l['reg']} | {l['status']} |")
lines += ["", "## Legs at/after the export end (unverifiable)", "",
          "| date | flight | route | STD (local) | reg | plan status |", "|---|---|---|---|---|---|"]
for l in at_end:
    lines.append(f"| {l['date']} | {l['flight']} | {l['origin']}-{l['dest']} | {l['std']} | {l['reg']} | {l['status']} |")
lines += ["", "Recurring gap patterns: triangle middle sectors (UR720 LUN-HRE, UR722 HRE-LUN,",
          "UR334 ZNZ-JRO), late UR343 MBA-EBB and the overnight UR111 LGW-EBB.",
          "Note: 10 Oct originally looked like a total recording blackout (1 track); the",
          "main-repo export of 2026-10-19 added 18 tracks (17 on 10 Oct plus the UR111",
          "inbound of 9 Oct) and that day now matches like any other."]
(FOLDER / "data_gaps.md").write_text("\n".join(lines) + "\n")

print(f"FTA legs {len(legs)} (deduped), matched {sum(1 for l in legs if l['track'])}, "
      f"missing {len(missing)}, tails rows added {added}, punctuality rows {len(prows)}")
