#!/usr/bin/env python3
"""
September 2026: join the FTA utilization plans (work/fta_sep2026.csv,
transcribed from fta.ugandairlines.com day plans 1-30 Sep 2026) to the
rebuilt flight log, producing schedule_delays.csv on the same basis as
October's (work/build_october_fta.py).

Run AFTER work/rebuild_month.py has produced UR SEPTEMBER 2026/flights.csv.

Writes:
  * UR SEPTEMBER 2026/schedule_delays.csv  (FTA basis)
  * UR SEPTEMBER 2026/data_gaps.md         (planned operating legs, no track)

Deliberately NOT touched (unlike October):
  * tails.csv      - September already has app-based tails (through 30 Sep)
  * punctuality.csv- September keeps its app-based frozen file; the FTA-basis
                     per-leg punctuality label lives in schedule_delays.csv

Conventions (same as October): CANCELLED and NON_SCHEDULED plan rows are
not operating legs and are excluded (14 + 5 rows in September). Duplicate
plan listings of one leg (same flight/route/STD) count once. The plan's
KBG/KGB code is the Hoima (Kabaale) field that flights.csv calls UGHO;
legs are normalised to UGHO for matching. The Hoima shuttle tracks fly
under the AF523 callsign, not the plan's UR130-UR133 numbers, so UGHO legs
fall back to route+time matching with the difference noted in
compare_note. Actual times are takeoff/landing (airborne events), so
departure delay vs STD includes taxi-out (~15-30 min).
"""
import csv, statistics, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from rebuild_month import AIRPORTS  # noqa: E402

FOLDER = Path("UR SEPTEMBER 2026")
TYPE_OF = {"5X-KDP": "CRJ9", "5X-EQU": "CRJ9", "5X-KOB": "CRJ9", "5X-NIL": "A332", "ET-APL": "A359"}

def parse_utc(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)

def norm(code):
    return "UGHO" if code in ("KBG", "KGB") else code

legs, seen = [], set()
n_cancelled = n_nonsked = 0
for r in csv.DictReader(open("work/fta_sep2026.csv")):
    if r["flight"] == "NONSKED" or r["status"] == "NON_SCHEDULED":
        n_nonsked += 1
        continue
    if r["status"] == "CANCELLED":
        n_cancelled += 1
        continue
    r = dict(r, origin=norm(r["origin"]), dest=norm(r["dest"]))
    otz = ZoneInfo(AIRPORTS[r["origin"]][4]); dtz = ZoneInfo(AIRPORTS[r["dest"]][4])
    d0 = datetime.strptime(r["date"] + " " + r["std"], "%Y-%m-%d %H:%M").replace(tzinfo=otz)
    a0 = datetime.strptime(r["date"] + " " + r["sta"], "%Y-%m-%d %H:%M").replace(tzinfo=dtz)
    std_utc = d0.astimezone(timezone.utc); sta_utc = a0.astimezone(timezone.utc)
    if sta_utc < std_utc + timedelta(minutes=20):
        sta_utc += timedelta(days=1)
    key = (r["flight"], r["origin"], r["dest"], std_utc)
    if key in seen:  # duplicate plan listing of one leg (e.g. two regs)
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
        fno = fno[:-1]  # UGD322D / UGD207D callsigns = UR322 / UR207
    f["_fno"] = fno

# Candidate generation, then global greedy assignment: the plan lists some
# overnight legs twice (e.g. UR323 DAR-EBB at 23:50 in one day-plan and
# 00:50 in the next). Nearest operated departure wins; the losing listing
# is a duplicate, counted once per the canonical rule, not a gap.
# Window: -240..+720 min (+720, not October's +480: the 10 Sep DAR
# rotation operated ~11 h late and its tracks exist).
cands = []  # (abs_dt, leg_idx, flight_idx, note)
for li, leg in enumerate(legs):
    leg["track"] = None
    for fi, f in enumerate(flights):
        if f["origin"] != leg["origin"] or f["dest"] != leg["dest"]:
            continue
        dt = (f["_dep"] - leg["std_utc"]).total_seconds() / 60.0
        if not (-240 <= dt <= 720):
            continue
        if f["_fno"] == leg["flight"]:
            cands.append((abs(dt), li, fi, ""))
        elif "UGHO" in (leg["origin"], leg["dest"]):
            # Hoima shuttle tracks fly as AF523, not the plan's UR13x numbers
            cands.append((abs(dt), li, fi,
                          "matched " + f["flight"] + " track (callsign differs from plan flight number)"))
    if leg["origin"] == "EBB" and leg["dest"] == "UGHO":
        # outbound shuttle sectors sometimes recorded as EBB-EBB round trips
        for fi, f in enumerate(flights):
            if f["flight"] == "AF523" and f["origin"] == "EBB" and f["dest"] == "EBB":
                dt = (f["_dep"] - leg["std_utc"]).total_seconds() / 60.0
                if -240 <= dt <= 720:
                    cands.append((abs(dt), li, fi,
                                  "matched AF523 EBB-EBB round-trip track (shuttle sector not split in the log)"))
had_cand = {li for _, li, _, _ in cands}
row_used = set()
for absdt, li, fi, note in sorted(cands):
    if legs[li]["track"] is not None or fi in row_used:
        continue
    legs[li]["track"] = flights[fi]
    if note:
        legs[li]["callsign_note"] = note
    row_used.add(fi)
for li, leg in enumerate(legs):  # multi-sector file: leg inside the flown window
    if leg["track"] is None and li not in had_cand:
        for f in flights:
            if f["_fno"] == leg["flight"] and f["_dep"] - timedelta(minutes=90) <= leg["std_utc"] <= f["_arr"]:
                leg["track"] = f
                break
n_dup_listing = sum(1 for li, l in enumerate(legs) if l["track"] is None and li in had_cand)
legs = [l for li, l in enumerate(legs) if l["track"] is not None or li not in had_cand]

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
        sched_vs_op_arr_min="", compare_ok="Y" if t else "",
        compare_note=leg.get("callsign_note", "") if t else "planned leg, no track in FR data",
        op_median_block_min=round((med_arr - med_dep).total_seconds()/60.0) if med_dep and med_arr else "",
        op_median_air_min="", block_slack_min="", baseline_legs=len(op_dep[k]),
        baseline_spread_min=""))
cols = list(rows[0].keys())
with open(FOLDER / "schedule_delays.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)

# ---- data_gaps.md --------------------------------------------------------------
missing = [l for l in legs if not l["track"]]
lines = ["# Data gaps — FTA-planned legs with no FR24 track (added 2026-10-20)", "",
         f"{len(missing)} planned operating legs (1–30 Sep 2026) have no track in",
         "`UR September flights.zip`. Source: FTA utilization plans",
         "(work/fta_sep2026.csv) joined to flights.csv by work/build_september_fta.py.",
         f"CANCELLED ({n_cancelled}) and NON_SCHEDULED ({n_nonsked}) plan rows are not gaps;",
         f"{n_dup_listing} duplicate plan listings of a leg (listed twice across",
         "adjacent day-plans) were counted once, against the closest operated departure.",
         "The plan's KBG/KGB code is Hoima (Kabaale), `UGHO` in flights.csv; the",
         "Hoima shuttle tracks fly as AF523, not the plan's UR130–UR133 numbers.", "",
         "## Legs with no track", "",
         "| date | flight | route | STD (local) | reg | plan status |", "|---|---|---|---|---|---|"]
for l in sorted(missing, key=lambda l: (l["std_utc"], l["flight"])):
    lines.append(f"| {l['date']} | {l['flight']} | {l['origin']}-{l['dest']} | {l['std']} | {l['reg']} | {l['status']} |")
lines += ["", "Track-side notes (from the rebuilt log): 10 tracks start airborne and 40 end",
          "airborne, so some ends are routed/timed by first/last fix; the AF523 Hoima",
          "and UGD720X test tracks are in flights.csv but carry no scheduled identity.",
          "5X-KNP and 5X-CRN were grounded (AOG) in every September plan; 5X-EQU was",
          "also out of service for part of 7–23 Sep ('UNDER MX AT EBB')."]
(FOLDER / "data_gaps.md").write_text("\n".join(lines) + "\n")

labels = defaultdict(int)
for leg in legs:
    if leg["track"]:
        labels[delay_label(round((leg["track"]["_dep"] - leg["std_utc"]).total_seconds() / 60.0))] += 1
print(f"FTA operating legs {len(legs)} (cancelled {n_cancelled}, non-sked {n_nonsked} excluded, "
      f"{n_dup_listing} duplicate listings counted once), "
      f"matched {sum(1 for l in legs if l['track'])}, missing {len(missing)}")
print("labels:", dict(labels))
