#!/usr/bin/env python3
"""Read the pulled FTA boards against the FR24 log: punctuality, turnarounds, coverage.

    python3 work/fta_analysis.py            # everything
    python3 work/fta_analysis.py --month 2026-10

Inputs
    work/fta/fta_legs.csv        planned legs, UTC  (from the boards' .xlsx)
    work/fta/fta_days.csv        one row per day board (state, counts, remarks)
    work/fta/fta_fleet.csv       grounded / unallocated aircraft per day
    fr24_publish/<month>/flights.csv   actual wheels-up / wheels-down from the ADS-B tracks

Matching rule
    a planned leg and a logged leg are the same flight when the sector is identical
    (origin, destination) and the observed wheels-up is within --window minutes of
    the planned STD, and the callsign agrees if the log has one (UR209 <-> UGD209).
    Assignment is greedy and 1:1, so no track is credited to two plans.

Writes work/fta/FTA_findings.md and prints the same tables.
"""
import argparse
import collections
import csv
import datetime as dt
import os
import re
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOVER_AFTER = 360   # minutes
MAX_DEP_OFF = 360   # a plan-vs-track departure gap beyond this is not a delay, it is a mismatch
MAX_ARR_OFF = 720   # idem for the arrival of ground time after which this is a layover, not a turn
FTA = os.path.join(ROOT, "work", "fta")
PUB = os.path.join(ROOT, "fr24_publish")
MONTHS = {"2026-09": "UR SEPTEMBER 2026", "2026-10": "UR OCTOBER 2026"}


def iso(s):
    """'2026-10-03 14:12Z' (FTA) or '2026-10-03 14:12:59Z' (FR24 log)."""
    s = (s or "").strip().replace("Z", "")
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def logs(months):
    """Logged legs: sector, wheels-up/down as datetimes, plus provenance."""
    out = []
    for m in months:
        folder = MONTHS.get(m)
        if not folder:
            continue
        for r in read_csv(os.path.join(PUB, folder, "flights.csv")):
            dep, arr = iso(r.get("departure_utc", "")), iso(r.get("arrival_utc", ""))
            if not dep:
                continue
            out.append({"month": m, "origin": r["origin"].strip(), "dest": r["dest"].strip(),
                        "callsign": r["flight"].strip().upper(), "dep": dep, "arr": arr,
                        "dep_raw": r.get("takeoff_not_observed", "").strip(),
                        "arr_raw": r.get("landing_not_observed", "").strip(),
                        "file": r.get("source_file", ""), "fixes": r.get("fixes", "")})
    return out


def join(legs, logged, window):
    """Greedy 1:1 match of planned legs to logged legs."""
    by_sector = collections.defaultdict(list)
    for lg in logged:
        by_sector[(lg["origin"], lg["dest"])].append(lg)
    pairs, cands = [], []
    for i, pl in enumerate(legs):
        std = iso(pl["std_iso"])
        if not std:
            continue
        for lg in by_sector.get((pl["origin"], pl["dest"]), []):
            dmin = (lg["dep"] - std).total_seconds() / 60.0
            if abs(dmin) > window:
                continue
            callsign = "UGD" + pl["flight"][2:] if pl["flight"].upper().startswith("UR") else pl["flight"]
            same_cs = lg["callsign"] == callsign.upper()
            cands.append((abs(dmin), 0 if same_cs else 1, i, lg["file"]))
    cands.sort()
    used_leg, used_log = set(), set()
    for _abs, _cs, i, f in cands:
        if i in used_leg or f in used_log:
            continue
        used_leg.add(i)
        used_log.add(f)
        pairs.append((legs[i], f))
    pair_by_leg = {id(l): f for l, f in pairs}
    log_by_file = {l["file"]: l for l in logged}
    matched = []
    for pl in legs:
        f = pair_by_leg.get(id(pl))
        if not f:
            continue
        lg = log_by_file[f]
        std, sta = iso(pl["std_iso"]), iso(pl["sta_iso"])
        matched.append({"leg": pl, "log": lg,
                        "dep_min": (lg["dep"] - std).total_seconds() / 60.0 if std else None,
                        "arr_min": ((lg["arr"] - sta).total_seconds() / 60.0) if (lg["arr"] and sta) else None})
    return matched


def quantiles(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    def q(p):
        return vals[min(len(vals) - 1, int(round(p * (len(vals) - 1))))]
    return {"n": len(vals), "mean": st.mean(vals), "median": st.median(vals),
            "p90": q(0.90), "p99": q(0.99), "min": vals[0], "max": vals[-1],
            "otp15": 100.0 * sum(1 for v in vals if -15 <= v <= 15) / len(vals)}


def fmt(d, unit=" min"):
    if not d:
        return "no matches"
    return ("n %d · mean %+.0f%s · median %+.0f · p90 %+.0f · worst %+.0f · within ±15 min %.0f%%"
            % (d["n"], d["mean"], unit, d["median"], d["p90"], d["max"], d["otp15"]))


def manifest_windows():
    """Every track we hold, keyed by flight number / callsign, as (start, end, file).
    Used to tell a plan with no data at all from a plan whose track exists but did not
    make it into the month log."""
    out = collections.defaultdict(list)
    for mth, folder in MONTHS.items():
        path = os.path.join(PUB, folder, "manifest.csv")
        if not os.path.exists(path):
            continue
        for r in read_csv(path):
            a, b = iso(r.get("first_utc", "")), iso(r.get("last_utc", ""))
            if not a:
                continue
            for key in filter(None, (r.get("flight", "").strip().upper(),
                                     r.get("callsign", "").strip().upper())):
                out[key].append((a, b or a, r.get("file", "")))
    return out


def has_track(plan, man):
    """Is any fix for this flight number seen in the window of the planned leg?"""
    std, sta = iso(plan["std_iso"]), iso(plan["sta_iso"])
    if not std:
        return ""
    end = (sta or std) + dt.timedelta(hours=6)
    std = std - dt.timedelta(hours=3)
    for key in {plan["flight"].upper(), "UGD" + plan["flight"][2:].upper()}:
        for a, b, f in man.get(key, []):
            if a <= end and b >= std:
                return f
    return ""


def turns(legs, cross_days=True):
    """Planned ground time per aircraft: next STD minus previous STA, UTC."""
    seq = collections.defaultdict(list)
    for pl in legs:
        std, sta = iso(pl["std_iso"]), iso(pl["sta_iso"])
        if std and sta:
            seq[pl["tail"]].append((std, sta, pl))
    out = []
    for tail, rows in seq.items():
        rows.sort(key=lambda x: (x[0], x[2]["seq"]))
        for (std0, sta0, p0), (std1, sta1, p1) in zip(rows, rows[1:]):
            if not cross_days and std1.date() != sta0.date():
                continue
            g = (std1 - sta0).total_seconds() / 60.0
            if g < -5 or g > 20 * 60:
                continue                     # a new aircraft, or the tail number changed hands
            out.append({"tail": tail, "in": p0, "out": p1, "airport": p0["dest"],
                        "start": sta0, "ground": g})
    out.sort(key=lambda r: (r["start"], r["tail"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="", help="YYYY-MM, e.g. 2026-10 (default: all pulled)")
    ap.add_argument("--window", type=int, default=180, help="max |wheels-up - STD| minutes")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", default="", help="write the tables here instead of work/fta/FTA_findings.md")
    args = ap.parse_args()

    legs = read_csv(os.path.join(FTA, "fta_legs.csv"))
    fleet = read_csv(os.path.join(FTA, "fta_fleet.csv"))
    days = read_csv(os.path.join(FTA, "fta_days.csv"))
    if not legs:
        raise SystemExit("work/fta/fta_legs.csv is empty - run: python3 work/fta_pull.py all")
    def leg_month(l):
        return (l["std_iso"] or l["ops_date"])[:7]
    if args.month:
        # the month of the leg's own planned STD, which is what work/fta_extract.py cuts on
        legs = [l for l in legs if leg_month(l) == args.month]
        fleet = [f for f in fleet if f["ops_date"].startswith(args.month)]
        days = [d for d in days if d["ops_date"].startswith(args.month)]
    else:
        legs = [l for l in legs if leg_month(l) in MONTHS or True]
    months = [args.month] if args.month else sorted({l["ops_date"][:7] for l in legs if l["ops_date"][:7] in MONTHS})
    logged = logs(months)

    L = []
    w = L.append
    scope = (args.month + " (by planned STD date)" if args.month
             else "%s .. %s" % (min(l["ops_date"] for l in legs), max(l["ops_date"] for l in legs)))
    w("# FTA boards read against the FR24 log")
    w("")
    w("Scope `%s` · %d planned legs on %d day boards · %d logged legs from %s"
      % (scope, len(legs), len(days), len(logged), ", ".join(months) or "no month log"))
    w("")

    # the FR24 log exists for these months only, so coverage/punctuality is scoped to them
    verifiable = [l for l in legs if l["ops_date"][:7] in MONTHS] if months else []
    # ---- 1. coverage: was the plan flown, and did we see it?
    matched = join(verifiable, logged, args.window)
    matched_ids = {id(m["leg"]) for m in matched}
    w("## 1. Coverage - planned legs with a track in the export")
    w("")
    w("Scoped to the months the FR24 log covers (%s); the other sections use every board pulled."
      % ", ".join(months) if months else "no log month in scope")
    w("")
    w("| month | planned legs | matched to a track | no track | day boards |")
    w("|---|---|---|---|---|")
    for mth in sorted({(l["std_iso"] or l["ops_date"])[:7] for l in verifiable}):
        pl = [l for l in verifiable if (l["std_iso"] or l["ops_date"])[:7] == mth]
        n_match = sum(1 for l in pl if id(l) in matched_ids)
        n_days = len({l["ops_date"] for l in pl})
        pl_ids = {id(l) for l in pl}
        w("| %s | %d | %d | %d | %d |" % (mth, len(pl), n_match, len(pl) - n_match, n_days))
    w("")
    unobs = [l for l in verifiable if id(l) not in matched_ids]
    verifiable = [l for l in verifiable if id(l) in pl_ids or True]
    w("| month | planned | with a track | no track | of those: cancelled | still due |")
    w("|---|---|---|---|---|---|")
    for mth in sorted({l["ops_date"][:7] for l in verifiable}):
        u = [l for l in unobs if (l["std_iso"] or l["ops_date"])[:7] == mth]
        can = sum(1 for l in u if l["status"] == "CANCELLED")
        w("| %s | %d | %d | %d | %d | %d |"
          % (mth, len([l for l in verifiable if l["ops_date"].startswith(mth)]),
             len([l for l in verifiable if l["ops_date"].startswith(mth)]) - len(u),
             len(u), can, len(u) - can))
    w("")
    due = [l for l in unobs if l["status"] != "CANCELLED"]
    man = manifest_windows()
    verdicts = collections.Counter()
    for l in due:
        l["_track"] = has_track(l, man)
        verdicts["track exists, not in the log" if l["_track"] else "no track in the archive"] += 1
    if verdicts:
        w("Split of those %d legs: %s"
          % (len(due), " · ".join("%s **%d**" % (k, v) for k, v in verdicts.most_common())))
        w("")
    if due and months:
        by_day = collections.Counter(l["ops_date"] for l in due)
        w("Legs the board expected but the export has no track for (%d), worst days: %s"
          % (len(due), ", ".join("%s (%d)" % (d, n) for d, n in by_day.most_common(6))))
        w("")
        w("| date | flight | tail | sector | STD (UTC) | status | track in archive? |")
        w("|---|---|---|---|---|---|---|")
        for l in sorted(due, key=lambda x: (bool(x["_track"]), x["std_iso"]))[:args.top * 3]:
            w("| %s | %s | %s | %s | %s | %s | %s |"
              % (l["ops_date"], l["flight"], l["tail"], l["sector"], l["std_utc"],
                 l["status"], l["_track"] or "none - fetch candidate"))
        w("")

    # ---- 2. punctuality
    w("## 2. On-time performance, planned (FTA) vs actual (FR24)")
    w("")
    # A leg whose wheels-up is hours off the plan, or whose track ends mid-flight, is not
    # a usable punctuality sample: keep the sane ones and say how many were dropped.
    dep_ok = [m for m in matched if m["dep_min"] is not None and not m["log"]["dep_raw"]
              and abs(m["dep_min"]) <= MAX_DEP_OFF]
    arr_ok = [m for m in matched if m["arr_min"] is not None and not m["log"]["arr_raw"]
              and abs(m["arr_min"]) <= MAX_ARR_OFF]
    dropped = (len(matched) - len(dep_ok)) + (len(matched) - len(arr_ok))
    dep = quantiles([m["dep_min"] for m in dep_ok])
    arr = quantiles([m["arr_min"] for m in arr_ok])
    w("- **departure** vs STD: " + fmt(dep))
    w("- **arrival** vs STA: " + fmt(arr))
    if matched:
        w("- matched legs: %d of %d planned (%.0f%%), across %d days"
          % (len(matched), len(verifiable), 100.0 * len(matched) / len(verifiable),
             len({m["leg"]["ops_date"] for m in matched})))
    w("")
    w("%d of %d matched legs sit outside %d min (departure) / %d min (arrival) of the plan, or"
      % (dropped, len(matched), MAX_DEP_OFF, MAX_ARR_OFF))
    w("have no observed wheels-up/down, and are left out of the two lines above.")
    w("")
    w("`+` is late, `-` is early. Wheels-up/wheels-down come from the track, so a leg whose")
    w("first or last fix is off the ground is skipped (that is what the two flags mean).")
    w("")
    if matched:
        w("### Late and early by origin")
        w("")
        w("| origin | legs | median dep | median arr | worst dep | p90 dep |")
        w("|---|---|---|---|---|---|")
        by_ap = collections.defaultdict(list)
        for m in dep_ok:
            by_ap[m["leg"]["origin"]].append({"leg": m["leg"], "log": m["log"],
                                              "dep_min": m["dep_min"],
                                              "arr_min": m["arr_min"] if m in arr_ok else None})
        rows = []
        for ap_, ms in by_ap.items():
            d = quantiles([m["dep_min"] for m in ms if not m["log"]["dep_raw"]])
            ar = quantiles([m["arr_min"] for m in ms if not m["log"]["arr_raw"]])
            if d:
                rows.append((d["median"], ap_, d, ar))
        for med, ap_, d, ar in sorted(rows, reverse=True)[:args.top]:
            w("| %s | %d | %+.0f | %s | %+.0f | %+.0f |"
              % (ap_, d["n"], d["median"], ("%+.0f" % ar["median"]) if ar else "-", d["max"], d["p90"]))
        w("")
        w("### The %d latest departures" % args.top)
        w("")
        w("| date | flight | tail | sector | STD | wheels-up | dep | STA | landing | arr |")
        w("|---|---|---|---|---|---|---|---|---|---|")
        worst = sorted(dep_ok, key=lambda m: -m["dep_min"])[:args.top]
        for m in worst:
            l, g = m["leg"], m["log"]
            w("| %s | %s | %s | %s | %s | %s | %+.0f | %s | %s | %s |"
              % (l["ops_date"], l["flight"], l["tail"], l["sector"], l["std_utc"],
                 g["dep"].strftime("%H:%M"), m["dep_min"], l["sta_utc"],
                 g["arr"].strftime("%H:%M") if g["arr"] else "-",
                 ("%+.0f" % m["arr_min"]) if m["arr_min"] is not None else "-"))
        w("")
        st_count = collections.Counter(m["leg"]["status"] for m in matched)
        all_count = collections.Counter(l["status"] for l in verifiable)
        w("Status labels on the boards, all legs vs matched legs: "
          + ", ".join("%s %d/%d" % (k, st_count.get(k, 0), v) for k, v in all_count.most_common()))
        w("")

    # ---- 2b. the board against the published timetable (the app's own file)
    w("## 2b. Board times vs the published timetable")
    w("")
    w("`schedule_delays.csv` measures the same tracks against the **published** timetable")
    w("(captured 02 Oct 18:35Z). The board carries whatever ops last amended. So the gap")
    w("between the two planned instants is the amendment, and it should never be invented")
    w("by my date rules.")
    w("")
    sd = []
    for mth in months:
        path = os.path.join(PUB, MONTHS[mth], "schedule_delays.csv")
        sd += [r for r in read_csv(path)]
    if sd:
        by_leg = collections.defaultdict(list)
        for l in legs:
            if l["std_iso"]:
                by_leg[(l["flight"].upper(), l["origin"], l["dest"])].append(l)
        diffs, same, rows_out, day_pairs = [], 0, [], []
        for r in sd:
            std_t = iso(r.get("sched_dep_utc", "").replace("Z", ""))
            if not std_t:
                continue
            cands = [l for l in by_leg.get((r["flight"].upper(), r["from_"], r["to"]), [])
                     if abs((iso(l["std_iso"]) - std_t).total_seconds()) <= 6 * 3600]
            if not cands:
                continue
            l = min(cands, key=lambda x: abs((iso(x["std_iso"]) - std_t).total_seconds()))
            d = (iso(l["std_iso"]) - std_t).total_seconds() / 60.0
            diffs.append(d)
            day_pairs.append((r["date"], d))
            if abs(d) <= 2:
                same += 1
            if abs(d) > 2:
                rows_out.append((r["date"], r["flight"], r["from_"] + "-" + r["to"],
                                 r["sched_dep_utc"], l["std_iso"], "%+.0f" % d, l["status"],
                                 r.get("arr_delay_min", "")))
        by_day = collections.defaultdict(lambda: [0, 0])
        for d_, dd in day_pairs:
            b = "captured day (01-02 Oct)" if d_ <= "2026-10-02" else "later days"
            by_day[b][0] += 1
            by_day[b][1] += 1 if abs(dd) <= 2 else 0
        for b, (n, same_b) in sorted(by_day.items()):
            w("- %s: %d of %d board STD values equal the timetable to the minute (%.0f%%)"
              % (b, same_b, n, 100.0 * same_b / n))
        q = quantiles(diffs)
        w("- %d legs common to both; %d (%.0f%%) have the board STD equal to the timetable"
          % (len(diffs), same, 100.0 * same / len(diffs) if diffs else 0))
        w("  (that is the check that the UTC/local and midnight handling are right).")
        if q:
            w("- where they differ: median %+.0f min, p90 %+.0f, max %+.0f, min %+.0f"
              % (q["median"], q["p90"], q["max"], q["min"]))
        if rows_out:
            w("")
            w("| date | flight | sector | timetable STD | board STD | board - timetable | board status | arr delay vs timetable |")
            w("|---|---|---|---|---|---|---|---|")
            for r in sorted(rows_out, key=lambda x: -abs(float(x[5])))[:args.top]:
                w("| %s |" % " | ".join(str(x) for x in r))
        w("")

    # ---- 3. turnarounds
    w("## 3. Turnaround time (planned ground time between a tail's own legs)")
    w("")
    tr = [t for t in turns(legs) if t["ground"] >= 0]
    g = quantiles([t["ground"] for t in tr if t["ground"] <= LAYOVER_AFTER])
    if not g:
        w("- no back-to-back legs on this scope")
    if g:
        w("- planned ground time: median **%.0f min**, mean %.0f, shortest %.0f, longest %.0f; "
          "%d of %d turns are under 30 min; %d gaps over %d min counted as layovers"
          % (g["median"], g["mean"], g["min"], g["max"],
             sum(1 for t in tr if t["ground"] < 30), len(tr),
             sum(1 for t in tr if t["ground"] > LAYOVER_AFTER), LAYOVER_AFTER))
    w("")
    w("A turn is the ground time a tail gets between two of its own legs; over %d min is"
      % LAYOVER_AFTER)
    w("counted as a layover, not a turn (that is where overnights and AOG sit).")
    w("")
    w("| airport | turns | median min | 25th | 75th | under 30 min | shortest plan | layovers |")
    w("|---|---|---|---|---|---|---|---|")
    w("|---|---|---|---|---|---|---|")
    by_ap = collections.defaultdict(list)
    for t in tr:
        by_ap[t["airport"]].append(t["ground"])
    rows = []
    lay = collections.Counter(t["airport"] for t in tr if t["ground"] > LAYOVER_AFTER)
    for ap_, vals in by_ap.items():
        vals = [v for v in sorted(vals) if v <= LAYOVER_AFTER]
        if not vals:
            continue
        rows.append((len(vals), ap_, st.median(vals), vals[len(vals) // 4], vals[len(vals) * 3 // 4],
                     sum(1 for v in vals if v < 30), vals[0], lay.get(ap_, 0)))
    for n, ap_, med, q1, q3, under, mn, over in sorted(rows, key=lambda r: -r[0])[:args.top]:
        w("| %s | %d | %.0f | %.0f | %.0f | %d | %.0f | %d |"
          % (ap_, n, med, q1, q3, under, mn, over))
    w("")
    w("- logged legs with no matching plan row: %d of %d (the board had no such leg, or the"
      " track is a partial/section of a planned one)" % (len(logged) - len(matched), len(logged)))
    w("")
    if tr and months:
        # actual ground time, where both consecutive legs have a track
        key = {(m["leg"]["origin"], m["leg"]["dest"], m["leg"]["ops_date"]): m for m in matched}
        pairs = collections.defaultdict(list)
        for t in tr:
            a0 = key.get((t["in"]["origin"], t["in"]["dest"], t["in"]["ops_date"]))
            a1 = key.get((t["out"]["origin"], t["out"]["dest"], t["out"]["ops_date"]))
            if a0 and a1 and a0["log"]["arr"] and a1["log"]["dep"]:
                actual = (a1["log"]["dep"] - a0["log"]["arr"]).total_seconds() / 60.0
                if 0 <= actual <= LAYOVER_AFTER and 0 <= t["ground"] <= LAYOVER_AFTER:
                    pairs[t["airport"]].append((actual, t["ground"], t))
        w("### Planned vs executed, turns where both legs have a track")
        w("")
        w("| airport | turns | planned median | actual median | delta | worst actual |")
        w("|---|---|---|---|---|---|")
        rows = []
        for ap_, vals in pairs.items():
            if len(vals) < 3:
                continue
            act = sorted(v[0] for v in vals)
            pla = sorted(v[1] for v in vals)
            rows.append((len(vals), ap_, st.median(pla), st.median(act),
                         st.median(act) - st.median(pla), act[-1]))
        for n, ap_, p, ac, d, mx in sorted(rows, key=lambda r: -r[0])[:args.top]:
            w("| %s | %d | %.0f | %.0f | %+.0f | %.0f |" % (ap_, n, p, ac, d, mx))
        w("")

    # ---- 4. fleet state and utilisation
    w("## 4. Fleet: who was flying, who was stuck")
    w("")
    per_tail = collections.Counter(l["tail"] for l in legs if l["tail"])
    w("| tail | legs planned | days on the board | grounded days | reasons seen |")
    w("|---|---|---|---|---|")
    grounded = collections.defaultdict(list)
    for f in fleet:
        if f["kind"] == "grounded":
            grounded[f["reg"]].append((f["ops_date"], f["status"], f["reason"]))
    for tail, n in per_tail.most_common():
        gd = grounded.pop(tail, [])
        w("| %s | %d | %d | %d | %s |"
          % (tail, n, len({l["ops_date"] for l in legs if l["tail"] == tail}), len(gd),
             ", ".join(sorted({r for _, _s, r in gd}))[:70] or "-"))
    for reg, gd in sorted(grounded.items(), key=lambda kv: -len(kv[1])):
        w("| %s | 0 | 0 | %d | %s |" % (reg, len(gd),
                                        ", ".join(sorted({r for _, _s, r in gd}))[:70] or "-"))
    w("")
    if days:
        states = collections.Counter(d["state"] for d in days)
        rem = [d for d in days if (d["remarks"] or "None").strip() not in ("", "None")]
        w("Board states: " + ", ".join("%s %d" % (k or "-", v) for k, v in states.most_common())
          + " · days carrying a Remark: %d" % len(rem))
        for d in rem[:args.top]:
            w("- %s: %s" % (d["ops_date"], d["remarks"]))
        w("")
    # ---- 4b. does the board agree with the tail work in the month folders?
    tails = []
    for mth in months:
        path = os.path.join(PUB, MONTHS[mth], "tails.csv")
        for r in read_csv(path):
            r["month"] = mth
            tails.append(r)
    if tails:
        by_leg = {}
        for l in legs:
            d = l["std_iso"][:10] or l["ops_date"]
            by_leg.setdefault((d, l["flight"].upper(), l["origin"], l["dest"]), []).append(l)
        same = diff = none = 0
        conflicts = []
        for t in tails:
            d = (t.get("date") or "").strip()
            fl = (t.get("flight") or "").strip().upper()
            if re.match(r"^\d{2}[A-Z]{3}\d{2}$", d):
                d = dt.datetime.strptime(d, "%d%b%y").date().isoformat()
            key = (d, fl, (t.get("origin") or "").strip(), (t.get("dest") or "").strip())
            cands = by_leg.get(key, [])
            tt = (t.get("tail") or "").strip().upper()
            if not cands:
                none += 1
                continue
            if any(c["tail"].upper() == tt for c in cands):
                same += 1
            else:
                diff += 1
                conflicts.append((d, fl, key[2] + "-" + key[3], tt, cands[0]["tail"], cands[0]["status"]))
        w("## 4b. tails.csv vs the boards")
        w("")
        w("%d of %d tail rows in the month `tails.csv` files are confirmed by the board that was"
          % (same, len(tails)))
        w("flying that day, %d disagree, %d legs are not on any board we hold." % (diff, none))
        if conflicts:
            w("")
            w("| date | flight | sector | tails.csv | FTA board | board status |")
            w("|---|---|---|---|---|---|")
            for c in conflicts[:args.top]:
                w("| %s | %s | %s | %s | %s | %s |" % c)
        w("")

    # ---- 5. planned block times, for later delay attribution
    w("## 5. Planned block times by sector (the timetable the board was built from)")
    w("")
    blk = collections.defaultdict(list)
    for l in legs:
        if l["block_min"] and l["block_min"].isdigit():
            blk[(l["origin"], l["dest"])].append(int(l["block_min"]))
    w("| sector | legs | median block | min | max |")
    w("|---|---|---|---|---|")
    rows = [(len(v), k, st.median(v), min(v), max(v)) for k, v in blk.items() if len(v) >= 5]
    for n, k, med, mn, mx in sorted(rows, key=lambda r: -r[0])[:args.top]:
        w("| %s-%s | %d | %.0f | %d | %d |" % (k[0], k[1], n, med, mn, mx))
    w("")
    # ---- 6. how firm is the "no track" list?
    if due:
        any_rec = 0
        for l in due:
            d = l["std_iso"][:10]
            for k in {l["flight"].upper(), "UGD" + l["flight"][2:].upper()}:
                for first, last, fname in man.get(k, []):
                    if abs((first.date() - dt.date.fromisoformat(d)).days) <= 1:
                        any_rec += 1
                        break
                else:
                    continue
                break
        w("Of the %d legs the board expected with no match in the log, %d have at least one track"
          % (len(due), any_rec))
        w("for that flight number within a day (a partial or mislabelled track); **%d have no track**"
          % (len(due) - any_rec))
        w("at all - that is the honest fetch list, and it carries a tail and a STD with it.")
        w("")

    out = args.out or os.path.join(FTA, "FTA_findings.md")
    if not out.startswith("/"):
        out = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\n[written] %s" % out)


if __name__ == "__main__":
    main()
