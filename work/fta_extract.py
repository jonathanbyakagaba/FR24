#!/usr/bin/env python3
"""Split the pulled FTA boards into one self-contained plan extract per month.

    python3 work/fta_extract.py                     # 2026-09 and 2026-10
    python3 work/fta_extract.py --month 2026-09 --month 2026-08

Each month lands in work/fta/plans/<month>/ as:

    plan_legs.csv      one row per planned sector whose STD falls in the month
    plan_days.csv      the day boards those legs came from (state, stamp, counts, remarks)
    plan_fleet.csv     grounded / unallocated aircraft on those days
    plan_tails.csv     the aircraft that appear in the month, with type and legs
    boards_index.csv   date -> uuid, so any row can be walked back to the live page
    source_xlsx/       the airline's own per-day .xlsx, byte for byte, for those boards
    PLAN.md            what is in the folder, how the month was cut, what the month looks like

Two dates are in play and they are not the same thing, so the cut is stated everywhere:
a leg belongs to the month of its planned STD (std_iso), while a board belongs to the
month of its own date (ops_date). A board carries a rotation that can start on the
previous UTC evening, and the next month's first board can carry the last legs of this
one - so plan_legs.csv carries a board_date / board_month pair on every row.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FTA = os.path.join(ROOT, "work", "fta")
PLANS = os.path.join(FTA, "plans")


def read(name):
    path = os.path.join(FTA, name)
    if not os.path.exists(path):
        raise SystemExit("missing %s - run: python3 work/fta_pull.py derive" % path)
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def month_of(stamp, fallback):
    return (stamp or fallback)[:7]


def write(path, rows, order=None):
    if not rows:
        open(path, "w").close()
        return 0
    cols = order or list(rows[0])
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def fmt_row(label, n, extra=""):
    return "| %s | %s%s |" % (label, n, (" · " + extra) if extra else "")


def summary(month, legs, days, fleet, tails):
    """A page that explains the month without needing the source site open."""
    L = []
    w = L.append
    by_day = collections.Counter(l["ops_date"] for l in legs)
    st = collections.Counter(l["status"] for l in legs)
    w("# Utilisation plan extract - %s" % month)
    w("")
    w("Pulled from `fta.ugandairlines.com` (day boards / utilization plans) and split out of the")
    w("full pull by `work/fta_extract.py`. Every time here is **UTC**, taken from the board's own")
    w("`.xlsx`; the board pages themselves render Entebbe local (+3). No actual times exist on the")
    w("site - this is what ops planned, as amended, not what happened.")
    w("")
    w("## The month in one look")
    w("")
    w("| | |")
    w("|---|---|")
    w(fmt_row("planned sectors", len(legs),
              "%d boards, %d-%d a day" % (len({l['ops_date'] for l in legs}),
                                          min(by_day.values()), max(by_day.values()))))
    w(fmt_row("aircraft on the board", len({l["tail"] for l in legs if l["tail"]}),
              "excluding %d rows flying as TBN" % st_of(legs, "TBN")))
    w(fmt_row("statuses", ", ".join("%s %d" % (k, v) for k, v in st.most_common())))
    w(fmt_row("sectors", len({l["sector"] for l in legs}),
              "top: " + ", ".join("%s %d" % ("%s-%s" % k, v) for k, v in
                                  collections.Counter((l["origin"], l["dest"]) for l in legs).most_common(4))))
    w(fmt_row("cancellations", st.get("CANCELLED", 0),
              "on " + ", ".join(sorted({l["ops_date"] for l in legs if l["status"] == "CANCELLED"}))
              if st.get("CANCELLED", 0) else "none"))
    w(fmt_row("delays and re-timings", st.get("DELAYED", 0) + st.get("RESCHEDULED", 0),
              "%d DELAYED, %d RESCHEDULED" % (st.get("DELAYED", 0), st.get("RESCHEDULED", 0))))
    w(fmt_row("non-standard rows", st.get("NON_SCHEDULED", 0), "extra/ad-hoc sectors on the board"))
    blk = [int(l["block_min"]) for l in legs if l["block_min"].isdigit()]
    if blk:
        w(fmt_row("planned block time", "%d min median" % int(median(blk)),
                  "shortest %d, longest %d" % (min(blk), max(blk))))
    turns = ground_times(legs)
    if turns:
        w(fmt_row("turnaround planned", "%d min median" % int(median(turns)),
                  "%d turns under 30 min" % sum(1 for t in turns if t < 30)))
    w(fmt_row("grounded tail-days", len([f for f in fleet if f["kind"] == "grounded"]),
              "%d of %d days list at least one" % (len({f['ops_date'] for f in fleet if f['kind'] == 'grounded'}),
                                                   len(days))))
    w(fmt_row("boards amended after publication", sum(1 for d in days if d["state"] == "AMENDED"),
              "%d published, %d with no state token"
              % (sum(1 for d in days if d["state"] == "PUBLISHED"),
                 sum(1 for d in days if d["state"] not in ("AMENDED", "PUBLISHED")))))
    w("")
    w("Files: `plan_legs.csv` (%d rows) · `plan_days.csv` (%d) · `plan_fleet.csv` (%d) ·"
      % (len(legs), len(days), len(fleet)))
    w("`plan_tails.csv` (%d) · `boards_index.csv` (%d) · `source_xlsx/` (%d files, the airline's own)"
      % (len(tails), len(days), len(os.listdir(os.path.join(PLANS, month, "source_xlsx")) or ["-"])
         if os.path.isdir(os.path.join(PLANS, month, "source_xlsx")) else 0))
    w("")

    # ---- day by day
    w("## Day by day")
    w("")
    w("| board date | legs in this month | planned dates covered | tails | cancelled | delayed |")
    w("|---|---|---|---|---|---|")
    for d in sorted(days, key=lambda x: x["ops_date"]):
        sub = [l for l in legs if l["ops_date"] == d["ops_date"]]
        w("| %s | %d | %s | %d | %d | %d |"
          % (d["ops_date"], len(sub), span(sub),
             len({l["tail"] for l in sub if l["tail"]}),
             sum(1 for l in sub if l["status"] == "CANCELLED"),
             sum(1 for l in sub if l["status"] in ("DELAYED", "RESCHEDULED"))))
    w("")

    # ---- what the month says about itself
    w("## Sectors, in order of how often they were planned")
    w("")
    w("| sector | legs | median block | tails used | statuses other than SCHEDULED |")
    w("|---|---|---|---|---|")
    by_sec = collections.defaultdict(list)
    for l in legs:
        by_sec[(l["origin"], l["dest"])].append(l)
    rows = []
    for (o, dd), ls in by_sec.items():
        bl = [int(x["block_min"]) for x in ls if x["block_min"].isdigit()]
        odd = collections.Counter(x["status"] for x in ls if x["status"] != "SCHEDULED")
        rows.append((len(ls), "%s-%s" % (o, dd), int(median(bl)) if bl else 0,
                     len({x["tail"] for x in ls if x["tail"]}),
                     ", ".join("%s %d" % kv for kv in odd.most_common(3)) or "-"))
    for n, sec, bl, nt, odd in sorted(rows, key=lambda r: (-r[0], r[1]))[:20]:
        w("| %s | %d | %d | %d | %s |" % (sec, n, bl, nt, odd))
    w("")
    w("## Aircraft on the board")
    w("")
    w("| tail | type | legs | days | first | last | grounded days |")
    w("|---|---|---|---|---|---|---|")
    gdays = collections.Counter(f["reg"] for f in fleet if f["kind"] == "grounded")
    for t in sorted(tails, key=lambda x: -int(x["legs_month"] or 0)):
        w("| %s | %s | %s | %s | %s | %s | %s |"
          % (t["tail"], t["type"] or "-", t["legs_month"], t["days_month"],
             t["first_leg"], t["last_leg"], gdays.get(t["tail"], 0)))
    w("")
    if gdays:
        w("Grounding reasons recorded this month, by tail:")
        w("")
        seen = collections.defaultdict(collections.Counter)
        for f in fleet:
            if f["kind"] == "grounded":
                seen[f["reg"]][f["reason"] or f["status"]] += 1
        for reg, c in sorted(seen.items(), key=lambda kv: -sum(kv[1].values())):
            w("- `%s` - %s" % (reg, "; ".join("%s x%d" % (r or "?", n) for r, n in c.most_common(4))))
        w("")
    rem = [d for d in days if (d["remarks"] or "None").strip() not in ("", "None")]
    if rem:
        w("## Remarks carried on this month's boards")
        w("")
        for d in rem:
            w("- **%s** - %s" % (d["ops_date"], d["remarks"]))
        w("")
    canc = [l for l in legs if l["status"] == "CANCELLED"]
    if canc:
        w("## Cancelled sectors")
        w("")
        w("| planned date | flight | tail | sector | STD (UTC) | board state |")
        w("|---|---|---|---|---|---|")
        for l in sorted(canc, key=lambda x: x["std_iso"]):
            w("| %s | %s | %s | %s | %s | %s |"
              % (l["leg_date"] or l["ops_date"], l["flight"], l["tail"] or "-",
                 l["sector"], l["std_iso"], l["board_state"]))
        w("")
    w("## Verification")
    w("")
    w("If `FTA_findings_%s.md` sits in this folder it holds the same legs measured against the FR24"
      % month.replace("-", ""))
    w("log (on-time, turns, coverage): regenerate it with")
    w("`python3 work/fta_analysis.py --month %s --out work/fta/plans/%s/FTA_findings_%s.md`."
      % (month, month, month.replace("-", "")))
    w("")
    w("## How this month was cut, and what to be careful with")
    w("")
    cross = sum(1 for l in legs if l["board_month"] != month)
    w("- A leg is in this folder when the **date of its planned STD** falls in %s. %d of the %d rows"
      % (month, cross, len(legs)))
    w("  were lifted off a board dated in the neighbouring month, which is why every row carries")
    w("  `board_date` / `board_month` next to `leg_date`.")
    w("- Day-level rows (`plan_days.csv`, `plan_fleet.csv`) are keyed on the **board** date, because")
    w("  that is how the site files them.")
    w("- `crew_pt_utc` and `crew_config` are internal crew data and are here only because this is the")
    w("  workspace copy; strip them before this goes anywhere public.")
    w("- `status` is what ops last wrote, not a report: a leg left as `SCHEDULED` may well have flown")
    w("  late. Nothing on the site records an actual time.")
    w("- Times are as the board's `.xlsx` publishes them. `std_iso`/`sta_iso` carry the day derived by")
    w("  the wrap rule in `work/fta/FTA.md` §3, cross-checked against the airline's own dated leg pages.")
    w("")
    return "\n".join(L) + "\n"


def st_of(legs, tail):
    return sum(1 for l in legs if l["tail"] == tail)


def median(vals):
    vals = sorted(vals)
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0


def ground_times(legs):
    """Planned ground time between one tail's own consecutive sectors, in minutes."""
    seq = collections.defaultdict(list)
    for l in legs:
        if l["std_iso"] and l["sta_iso"]:
            seq[l["tail"]].append((dt.datetime.strptime(l["std_iso"], "%Y-%m-%d %H:%MZ"),
                                   dt.datetime.strptime(l["sta_iso"], "%Y-%m-%d %H:%MZ")))
    out = []
    for tail, rows in seq.items():
        rows.sort()
        for (_s0, e0), (s1, _e1) in zip(rows, rows[1:]):
            g = (s1 - e0).total_seconds() / 60.0
            if 0 <= g <= 360:
                out.append(g)
    return out


def span(legs):
    """The calendar days the legs on one board actually fly, as dd..dd."""
    d = sorted({l["std_iso"][8:10] for l in legs if l["std_iso"]})
    if not d:
        return "-"
    if len(d) == 1:
        return d[0]
    return "%s-%s" % (d[0], d[-1])


def build(month, legs, days, fleet, tails_all, detail):
    out = os.path.join(PLANS, month)
    os.makedirs(os.path.join(out, "source_xlsx"), exist_ok=True)
    mlegs = [l for l in legs if month_of(l["std_iso"], l["ops_date"]) == month]
    if not mlegs:
        print("skip %s: no legs" % month)
        return
    dates = {l["ops_date"] for l in mlegs}
    mdays = [d for d in days if d["ops_date"] in dates
             or d["ops_date"][:7] == month and int(d["legs"]) > 0]
    # a board is in the month if its own date is, or if it contributed legs to it
    mdays = sorted({d["ops_date"]: d for d in mdays}.values(), key=lambda x: x["ops_date"])
    ddates = {d["ops_date"] for d in mdays}
    mfleet = [f for f in fleet if f["ops_date"] in ddates]
    used = collections.Counter(l["tail"] for l in mlegs if l["tail"])
    days_by_tail = collections.defaultdict(set)
    first_last = {}
    for l in mlegs:
        if not l["tail"]:
            continue
        days_by_tail[l["tail"]].add(l["ops_date"])
        d0 = l["std_iso"][:10] or l["ops_date"]
        cur = first_last.get(l["tail"])
        if not cur:
            first_last[l["tail"]] = (d0, d0)
        else:
            first_last[l["tail"]] = (min(cur[0], d0), max(cur[1], d0))
    type_of = {}
    for r in detail:
        reg = (r["reg_type"] or "").split(" : ")[0].strip()
        if reg and r["type"] and r["ops_date"] in ddates:
            type_of.setdefault(reg, r["type"])
    pull_tails = {x["tail"]: x for x in tails_all}
    mtails = [{"tail": t, "type": type_of.get(t, "") or pull_tails.get(t, {}).get("type", ""),
               "legs_month": n, "days_month": len(days_by_tail[t]),
               "first_leg": first_last.get(t, ("", ""))[0],
               "last_leg": first_last.get(t, ("", ""))[1],
               "legs_whole_pull": pull_tails.get(t, {}).get("legs_planned", "")}
              for t, n in used.most_common()]

    for l in mlegs:
        l["board_month"] = l["ops_date"][:7]
        l["board_date"] = l["ops_date"]
        l["leg_date"] = l["std_iso"][:10]
    mlegs.sort(key=lambda x: (x["std_iso"], x["seq"]))
    dcols = ["ops_date", "board_date_label", "board_stamp_local", "state", "excel_sheet", "uuid",
             "legs", "tails", "tails_list", "grounded", "unallocated", "remarks"]
    write(os.path.join(out, "plan_legs.csv"), mlegs,
          ["leg_date", "std_iso", "sta_iso", "block_min", "status", "flight", "sector", "origin",
           "dest", "tail", "crew_pt_utc", "crew_config", "board_date", "board_month", "board_state",
           "seq", "uuid", "date_source"])
    write(os.path.join(out, "plan_days.csv"), mdays, dcols)
    write(os.path.join(out, "plan_fleet.csv"), mfleet,
          ["ops_date", "kind", "reg", "status", "reason"])
    write(os.path.join(out, "plan_tails.csv"), mtails,
          ["tail", "type", "legs_month", "days_month", "legs_whole_pull", "first_leg", "last_leg"])
    write(os.path.join(out, "boards_index.csv"),
          [{"board_date": d["ops_date"], "month_of_board": d["ops_date"][:7],
            "legs_from_it": sum(1 for l in mlegs if l["ops_date"] == d["ops_date"]),
            "legs_in_this_month": sum(1 for l in mlegs if l["ops_date"] == d["ops_date"]
                                      and month_of(l["std_iso"], l["ops_date"]) == month),
            "uuid": d["uuid"], "excel_on_disk": os.path.exists(os.path.join(FTA, "xlsx", d["ops_date"] + ".xlsx")),
            "page_url": "https://fta.ugandairlines.com/" + d["uuid"] if d["uuid"] else "",
            "excel_url": "https://fta.ugandairlines.com/%s/excel" % d["uuid"] if d["uuid"] else "",
            "pdf_url": "https://fta.ugandairlines.com/%s/pdf" % d["uuid"] if d["uuid"] else ""}
           for d in mdays],
          ["board_date", "month_of_board", "legs_from_it", "legs_in_this_month", "uuid",
           "excel_on_disk", "page_url", "excel_url", "pdf_url"])
    copied = 0
    for d in mdays:
        src = os.path.join(FTA, "xlsx", d["ops_date"] + ".xlsx")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out, "source_xlsx", d["ops_date"] + ".xlsx"))
            copied += 1
    open(os.path.join(out, "PLAN.md"), "w").write(summary(month, mlegs, mdays, mfleet, mtails))
    print("%s: %4d legs · %2d boards · %2d tails · %d source xlsx -> work/fta/plans/%s"
          % (month, len(mlegs), len(mdays), len(mtails), copied, month))
    return len(mlegs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", action="append", default=[])
    a = ap.parse_args()
    legs = read("fta_legs.csv")
    days = read("fta_days.csv")
    fleet = read("fta_fleet.csv")
    tails = read("fta_tails.csv")
    detail = read("fta_leg_detail.csv")
    months = a.month or ["2026-09", "2026-10"]
    os.makedirs(PLANS, exist_ok=True)
    made = [build(m, legs, days, fleet, tails, detail) for m in months]
    # what the two months hold compared with the whole pull, so nothing is silently dropped
    all_m = collections.Counter(month_of(l["std_iso"], l["ops_date"]) for l in legs)
    print("whole pull, legs by planned month: " + ", ".join("%s %d" % kv for kv in sorted(all_m.items())))
    picked = sum(x for x in made if x)
    print("extracted %d of %d legs; the rest sit in months not asked for" % (picked, len(legs)))


if __name__ == "__main__":
    main()
