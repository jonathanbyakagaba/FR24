#!/usr/bin/env python3
"""One CSV that consolidates lateness and turn-around time, plan against the tracks.

The plan of record is the FTA (Flight Turn Around) board for the ops day; the actual is the FR24
log built from the track archive. Every row is one **planned leg**, so a leg nobody ever captured
still appears, with its lateness columns empty - which is the point: a missing flight is not the
same as a flight on time.

    python3 work/turnaround_csv.py                       # every month the log covers
    python3 work/turnaround_csv.py --month 2026-10
    python3 work/turnaround_csv.py --out work/fta/x.csv

What each side contributes
  FTA board   std_iso / sta_utc per leg, the tail, the crew reporting time, the status the board
              held when it was snapshotted (SCHEDULED / DELAYED / RESCHEDULED / CANCELLED)
  FR24 log    wheels-up and wheels-down in UTC, fixes per track, and whether the take-off or the
              landing was simply not in the export

Match rule (inherited from work/fta_analysis.py, deliberately the same one): same sector, same
callsign, wheels-up within 180 min of the planned STD, greedy and 1:1 so one track is never
credited to two plans.

Turn-around is the ground time a tail gets between two of its own legs - the previous arrival into
this airport and this departure out of it. `turn_plan_min` is board STA to board STD; `turn_act_min`
is the observed wheels-down to observed wheels-up. Planned ground over 360 min is labelled a
layover rather than a turn, because that is where overnights and AOG sit.

All times are UTC. The `*_local` columns are the same instants at the airport's own offset.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import importlib.util
import os
import re
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(WORK, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


fa = load("fta_analysis")
OFF = load("schedule_delays").TRUE          # minutes east of UTC, per airport
LAY = fa.LAYOVER_AFTER


def board_dt(ops_date, clock, before):
    """The board writes crew reporting as a clock reading only (`01:50`), with no date, and the
    row can belong to the previous ops day when the day's board wraps past midnight. Land it on
    ops_date, then walk back a day at a time until it is not later than the STD it precedes."""
    base = dt.datetime.strptime(ops_date, "%Y-%m-%d")
    h, mi = (clock or "").strip()[:5].split(":")[:2] if clock else ("", "")
    if not h:
        return None
    v = base + dt.timedelta(hours=int(h), minutes=int(mi))
    for _ in range(3):
        if before is None or v <= before:
            return v
        v -= dt.timedelta(days=1)
    return v


def local(ts, apt):
    if not ts or apt not in OFF:
        return ""
    v = ts + dt.timedelta(minutes=OFF[apt])
    return v.strftime("%Y-%m-%d %H:%M")


def mins(a, b):
    """b - a in minutes, or '' when either end is unknown"""
    if not a or not b:
        return ""
    return round((b - a).total_seconds() / 60.0, 1)


def fmt(ts):
    return ts.strftime("%Y-%m-%d %H:%M:%SZ") if ts else ""


def quant(vals):
    if not vals:
        return {}
    v = sorted(vals)
    pick = lambda p: v[min(len(v) - 1, int(len(v) * p))]
    return {"n": len(v), "median": round(st.median(v), 1), "mean": round(st.fmean(v), 1),
            "p90": round(pick(0.90), 1), "worst": round(v[-1], 1), "best": round(v[0], 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="", help="YYYY-MM, e.g. 2026-10 (default: every log month)")
    ap.add_argument("--window", type=int, default=180, help="max |wheels-up - STD| minutes")
    ap.add_argument("--out", default=os.path.join(WORK, "fta", "turnaround_and_lateness.csv"))
    a = ap.parse_args()

    # the newest fix anywhere in the archive: anything planned after it is not late, just not
    # downloaded yet - and a CSV that cannot tell those apart invites exactly that mistake
    cut = None
    for folder in (fa.MONTHS["2026-10"], fa.MONTHS["2026-09"]):
        man = fa.read_csv(os.path.join(ROOT, "fr24_publish", folder, "manifest.csv"))
        vals = [r["last_utc"] for r in man if r.get("last_utc")]
        if vals:
            cut = fa.iso(max(v[:16] for v in vals))     # ISO sorts as a string
            break

    months = [a.month] if a.month else list(fa.MONTHS)
    all_legs = fa.read_csv(os.path.join(WORK, "fta", "fta_legs.csv"))
    if not all_legs:
        raise SystemExit("work/fta/fta_legs.csv is empty - run: python3 work/fta_pull.py all")
    legs = [l for l in all_legs if l["ops_date"][:7] in months]
    logged = fa.logs(months)
    # what each callsign normally flies. The board absorbs a diversion by re-timing or re-labelling
    # the row, so plan-vs-actual on that row looks clean; comparing the sector against the number's
    # usual one is what exposes the section that was never in the plan.
    # the set of sectors a number flies, from its unsuffixed legs only - otherwise the odd
    # section votes for its own normality. A set, not the mode: UR722/UR720/UR334 legitimately
    # fly three sectors apiece on a triangle, and flagging those would be a false alarm.
    usual = collections.defaultdict(set)
    for r in logged:
        base = re.sub(r"[A-Z]+$", "", r["callsign"])
        if base == r["callsign"]:
            usual[base].add("%s-%s" % (r["origin"], r["dest"]))
    matched = fa.join(legs, logged, a.window)
    by_leg = {id(m["leg"]): m for m in matched}
    # turns are paired across the tail's whole sequence, so the first leg of a day still gets the
    # overnight ground before it rather than nothing
    turn_by_out = {id(t["out"]): t for t in fa.turns(legs)}
    # tracks no board row claimed, kept so an unmatched row can say whether the flight is missing
    # or the capture is: a same-number track that landed at the planned airport but whose logged
    # origin is a nearest-airport guess (takeoff_not_observed) is a truncated track, not a cancel
    claimed = {id(m["log"]) for m in matched}
    free_by_num = collections.defaultdict(list)
    for r in logged:
        if id(r) in claimed:
            continue
        free_by_num[re.sub(r"\D+", "", r["callsign"])].append(r)

    rows = []
    for pl in sorted(legs, key=lambda l: (l["std_iso"], l["flight"])):
        std, sta = fa.iso(pl["std_iso"]), fa.iso(pl["sta_iso"])
        report = board_dt(pl["ops_date"], pl.get("crew_pt_utc", ""), std)
        m = by_leg.get(id(pl))
        lg = m["log"] if m else None
        b = re.fullmatch(r"(?:UR|QU|UG)?(\d{2,4})([A-Z]*)", pl["flight"].strip().upper())
        sfx_board, base_num = (b.group(2), b.group(1)) if b else ("", "")
        call = lg["callsign"] if lg else ""
        sfx_call = re.fullmatch(r"\D*\d+([A-Z]+)", call).group(1) if call and re.fullmatch(r"\D*\d+([A-Z]+)", call) else ""
        call_base = re.sub(r"[A-Z]+$", "", call)
        usual_secs = sorted(usual.get(call_base) or [])
        sector_changed = ""
        if lg and usual_secs:
            sector_changed = "no" if pl["sector"] in usual_secs else "yes"
        suffix_source = ("board and callsign" if (sfx_board and sfx_call)
                         else "callsign only" if sfx_call else "board only" if sfx_board else "")
        dep, arr = (lg["dep"], lg["arr"]) if lg else (None, None)
        t = turn_by_out.get(id(pl))
        prev, prev_log = None, None
        if t:
            prev = t["in"]
            pm = by_leg.get(id(prev))
            prev_log = pm["log"] if pm else None
        plan_ground = round(t["ground"], 1) if t else ""
        late = mins(std, dep)
        # crew reporting to off-block is only meaningful inside one duty period: a board whose
        # dated STD sits further from its own ops_date than a day makes the arithmetic nonsense,
        # so those rows stay blank and say why instead of polluting the median
        raw_crew = mins(report, dep)
        crew_gap = raw_crew if isinstance(raw_crew, (int, float)) and 0 <= raw_crew <= 720 else ""
        notes = []
        if report and crew_gap == "":
            notes.append("crew report time unusable against the dated STD")
        if not m:
            notes.append("cancelled on the board" if pl["status"] == "CANCELLED"
                         else ("planned after the archive cut" if cut and std and std > cut
                               else "no track in the export"))
        if isinstance(late, (int, float)) and late < -30:
            notes.append("wheels-up well before the board STD")   # the minutes are in dep_late_min
        if lg and lg["dep_raw"]:
            notes.append("take-off not observed in the export")
        if lg and lg["arr_raw"]:
            notes.append("landing not observed in the export")
        if sfx_call:
            notes.append("flew a suffixed callsign - a section the plan did not carry")
        elif sfx_board:
            notes.append("board-only suffix - plan stub, no such callsign was ever tracked")
        if sector_changed == "yes":
            notes.append("sector is outside %s's usual set (%s)"
                         % (call_base.replace("UGD", "UR"), ", ".join(usual_secs)))
        if prev and prev["dest"] != pl["origin"]:
            notes.append("the tail's previous planned leg ends at %s, not %s - a sector is missing"
                         % (prev["dest"], pl["origin"]))
        unclaimed = ""
        if not m and std:
            num = re.sub(r"\D+", "", pl["flight"])
            near = [r for r in free_by_num.get(num, ())
                    if abs((r["dep"] - std).total_seconds()) <= 8 * 3600
                    and (r["dest"] == pl["dest"] or r["origin"] == pl["origin"])]
            if near:
                r = min(near, key=lambda x: abs((x["dep"] - std).total_seconds()))
                unclaimed = r["file"]
                if r["dest"] == pl["dest"] and r["origin"] != pl["origin"]:
                    notes.append("an unclaimed track lands at %s under this number but its logged "
                                 "origin is %s, not %s - the capture starts in the air"
                                 % (r["dest"], r["origin"], pl["origin"]))
                elif r["origin"] == pl["origin"] and r["dest"] != pl["dest"]:
                    notes.append("an unclaimed track for this number leaves %s but lands at %s, not "
                                 "%s - a re-route, not counted here"
                                 % (r["origin"], r["dest"], pl["dest"]))
                else:
                    notes.append("this number's only track was credited to another row of the same "
                                 "leg on another board")
        act_ground = mins(prev_log["arr"] if prev_log else None, dep)
        rows.append({
            "month": pl["ops_date"][:7],
            "ops_date": pl["ops_date"],
            "tail": pl["tail"],
            "flight": pl["flight"],
            "sector": pl["sector"],
            "flight_suffix": sfx_board,
            "base_flight": ("UR" + base_num) if base_num else "",
            "callsign": call,
            "callsign_suffix": sfx_call,
            "suffix_source": suffix_source,
            "sectors_usual": " ".join(usual_secs)[:60],
            "sector_changed": sector_changed,
            "origin": pl["origin"],
            "dest": pl["dest"],
            "board_status": pl["status"],
            "board_state": pl["board_state"],
            "date_source": pl["date_source"],
            "std_utc": fmt(std),
            "sta_utc": fmt(sta),
            "std_local": local(std, pl["origin"]),
            "sta_local": local(sta, pl["dest"]),
            "block_plan_min": pl["block_min"] or "",
            "off_block_utc": fmt(dep),
            "on_block_utc": fmt(arr),
            "off_block_local": local(dep, pl["origin"]),
            "on_block_local": local(arr, pl["dest"]),
            "block_act_min": mins(dep, arr),
            "dep_late_min": late,
            "arr_late_min": mins(sta, arr),
            "matched": "yes" if m else ("cancelled" if pl["status"] == "CANCELLED" else "no track"),
            "crew_report_utc": fmt(report),
            "crew_report_to_off_block_min": crew_gap,
            # the join that says "this tail did not come from where this leg departs" is the only
            # way the file can see a re-routing: a diverted flight keeps its destination and changes
            # its origin, so nothing in the lateness columns would ever show it
            "turn_prev_dest": prev["dest"] if prev else "",
            "turn_chain_ok": ("" if not prev else
                              ("yes" if prev["dest"] == pl["origin"] else "no")),
            "turn_airport": prev["dest"] if prev else "",
            "turn_prev_flight": prev["flight"] if prev else "",
            "turn_prev_sta_utc": fmt(fa.iso(prev["sta_iso"])) if prev else "",
            "turn_prev_on_block_utc": fmt(prev_log["arr"]) if prev_log else "",
            "turn_plan_min": plan_ground,
            "turn_act_min": act_ground,
            "turn_delta_min": ("" if plan_ground == "" or act_ground == ""
                               else round(act_ground - plan_ground, 1)),
            "turn_kind": ("" if not t else ("turn" if 0 <= t["ground"] <= LAY else
                                            ("layover" if t["ground"] > LAY else "overlap"))),
            "turn_has_both_tracks": "yes" if (prev_log and lg) else "no",
            "takeoff_not_observed": lg["dep_raw"] if lg else "",
            "landing_not_observed": lg["arr_raw"] if lg else "",
            "fixes": lg["fixes"] if lg else "",
            "track_file": lg["file"] if lg else "",
            "unclaimed_track": unclaimed,
            "note": "; ".join(notes),
        })

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    cols = list(rows[0])
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {a.out.replace(ROOT + '/', '')}: {len(rows)} rows, {len(cols)} columns, "
          f"{os.path.getsize(a.out):,} B")

    # ------------------------------------------------------------------ the same summary, on stdout
    num = lambda k: [r[k] for r in rows if isinstance(r[k], (int, float))]
    print(f"\nscope {months} · planned legs {len(rows)} · matched to a track "
          f"{sum(1 for r in rows if r['matched'] == 'yes')} · cancelled "
          f"{sum(1 for r in rows if r['matched'] == 'cancelled')} · no track "
          f"{sum(1 for r in rows if r['matched'] == 'no track')}")
    for key, label in (("dep_late_min", "departure lateness (wheels-up - STD)"),
                       ("arr_late_min", "arrival lateness (wheels-down - STA)"),
                       ("crew_report_to_off_block_min", "crew reporting time to wheels-up"),
                       ("turn_delta_min", "turn-around overrun (actual - planned ground)")):
        q = quant(num(key))
        if q:
            print(f"  {label:44s} n={q['n']:<4} median {q['median']:>6}  mean {q['mean']:>6}  "
                  f"p90 {q['p90']:>6}  worst {q['worst']:>6}  best {q['best']:>6}")
    late_vals = num("dep_late_min")
    ontime = sum(1 for v in late_vals if abs(v) <= 15)
    pct = (100.0 * ontime / len(late_vals)) if late_vals else 0.0
    print(f"  departures within +/-15 min of the board: {ontime} of {len(late_vals)} ({pct:.0f} %)")

    by_ap = collections.defaultdict(lambda: {"plan": [], "act": []})
    for r in rows:
        ap_ = r["turn_airport"]
        if not ap_ or r["turn_kind"] != "turn" or r["turn_has_both_tracks"] != "yes":
            continue
        by_ap[ap_]["plan"].append(r["turn_plan_min"])
        by_ap[ap_]["act"].append(r["turn_act_min"])
    print("\n  turns where both legs have a track (planned vs executed ground minutes):")
    print("    airport   turns   plan med   act med   delta    longest act")
    out = []
    for ap_, d in by_ap.items():
        if len(d["act"]) < 3:
            continue
        out.append((len(d["act"]), ap_, st.median(d["plan"]), st.median(d["act"]),
                    st.median(d["act"]) - st.median(d["plan"]), max(d["act"])))
    for n, ap_, p, ac, dl, mx in sorted(out, key=lambda x: -x[0]):
        print(f"    {ap_:8s} {n:>6}   {p:>8.0f}   {ac:>8.0f}   {dl:>+6.0f}   {mx:>10.0f}")
    worst = sorted((r for r in rows if isinstance(r["dep_late_min"], (int, float))),
                   key=lambda r: -r["dep_late_min"])[:10]
    sfx = [r for r in rows if r["callsign_suffix"] or r["flight_suffix"]]
    if sfx:
        print(f"\n  {len(sfx)} legs with a suffix on the flight number or the callsign:")
        for r in sfx:
            print(f"    {r['ops_date']}  board {r['flight']:9s} {r['sector']:9s} {r['board_status']:11s} "
                  f"· callsign {r['callsign'] or '—':9s} {r['suffix_source']:18s} "
                  f"usual set: {r['sector_changed'] or '—':3s} · {r['matched']}")
    print("\n  the 10 latest departures:")
    for r in worst:
        print(f"    {r['ops_date']}  {r['flight']:7s} {r['sector']:9s} {r['tail']:7s} "
              f"STD {r['std_utc'][11:16]}  off-block {r['off_block_utc'][11:16]}  "
              f"+{r['dep_late_min']:.0f} min   arr late {r['arr_late_min'] if r['arr_late_min'] != '' else '-'}")


if __name__ == "__main__":
    main()
