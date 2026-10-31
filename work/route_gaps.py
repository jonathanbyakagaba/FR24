#!/usr/bin/env python3
"""Which triangle rotations and which out-and-back routes are not whole in fr24_publish.

    python3 work/route_gaps.py

Everything is keyed on the **plan** (the FTA month extracts, `work/fta/plans/<month>/plan_legs.csv`)
and then each planned leg is asked one question: is it in the FR data folder?

  matched          a row in that month's flights.csv lines up with it (sector + wheels-up within
                   180 min, callsign preferred, 1:1 greedy - the join from work/fta_analysis.py)
  track-not-in-log a track for that flight number exists in the archive manifest, but the month
                   log has no leg for it (usually a partial track, nothing to fetch)
  no-track         nothing in the archive at all - the fetch list
  cancelled        the board itself says CANCELLED
  beyond-capture   planned after the archive's newest fix, so no data is expected

"Rotation" = one of the three non-Entebbe circuits the fleet flies:
  UR722  EBB-HRE-LUN-EBB · UR720  EBB-LUN-HRE-EBB · UR334  EBB-ZNZ-JRO-EBB
"Route" = an out-and-back pair on one aircraft (A-B then B-A within a day), triangle sectors
excluded because their return is a different airport by design.
"""
import collections
import csv
import datetime as dt
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("fa", os.path.join(ROOT, "work", "fta_analysis.py"))
fa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fa)

MONTHS = ["2026-09", "2026-10"]
ROTATIONS = [
    ("UR722", "EBB-HRE-LUN-EBB", [("EBB", "HRE"), ("HRE", "LUN"), ("LUN", "EBB")]),
    ("UR720", "EBB-LUN-HRE-EBB", [("EBB", "LUN"), ("LUN", "HRE"), ("HRE", "EBB")]),
    ("UR334", "EBB-ZNZ-JRO-EBB", [("EBB", "ZNZ"), ("ZNZ", "JRO"), ("JRO", "EBB")]),
]
# the boards write Hoima/Kabalega two ways: EBB-KBG out, KGB-EBB back. Without this the
# outbound and the return never pair up and both look like holes.
CODE_FIX = {"KGB": "KBG"}


def ap(code):
    return CODE_FIX.get(code, code)


def norm(l):
    l["origin"], l["dest"] = ap(l["origin"]), ap(l["dest"])
    l["sector"] = "%s-%s" % (l["origin"], l["dest"])


TRIANGLE_SECTORS = {s for _, _, secs in ROTATIONS for s in secs} | {(b, a) for _, _, secs in ROTATIONS for a, b in secs}


def _h(a, b):
    """Hours between two legs' planned STD, None-safe."""
    x, y = fa.iso(a["std_iso"]), fa.iso(b["std_iso"])
    if x is None or y is None:
        return 0.0
    return (x - y).total_seconds() / 3600.0


def plan_legs():
    """The month extracts, one row per planned leg.

    A leg that is re-listed on a later board (the 23 Sep board has UR323 DAR-EBB at 20:50,
    the 24 Sep board has the same leg at 21:50) is counted once, from the newest board that
    carries it - otherwise the superseded copy shows up as a leg the folder never got.
    """
    kept, n = [], 0
    for m in MONTHS:
        path = os.path.join(ROOT, "work", "fta", "plans", m, "plan_legs.csv")
        rows = fa.read_csv(path)
        n += len(rows)
        for r in sorted(rows, key=lambda x: (x["board_date"], x["seq"]), reverse=True):
            r["month"] = m
            norm(r)
            dup = any(k["flight"] == r["flight"] and k["sector"] == r["sector"]
                      and k["leg_date"] == r["leg_date"] and abs(_h(k, r)) <= 3
                      for k in kept)
            if not dup:
                kept.append(r)
    legs = kept
    print("board rows read %d, duplicate re-listings dropped %d" % (n, n - len(legs)))
    return legs


def tri_slot(l):
    """Which triangle rotation this sector belongs to, and which part of it it is."""
    for flight, chain, secs in ROTATIONS:
        for i, s in enumerate(secs):
            if (l["origin"], l["dest"]) == s:
                return flight, chain, ("outbound", "middle sector", "return")[i]
    return "", "", ""


def sibling(man, l, horizon_h=None):
    """The nearest track in the archive carrying this flight number, whatever day it sits on.

    The presence test looks twelve hours out, and that window is the difference between a leg that
    was lost and a board row whose date moved.  The search is unbounded, so the
    reader can see how far the nearest one really is: a track 2 h off and a track 3 days off are
    different findings.  14 Oct `UR111` LGW-EBB (STD 17:10Z) has no track
    near it - but the archive does hold `UR111-421b7cd4.csv`, airborne 13 Oct 19:03Z to 14 Oct
    03:30Z, already logged as the 13 Oct rotation.  Returns (hours_signed, first, last, file).
    """
    std = fa.iso(l["std_iso"])
    if std is None:
        return None
    best = None
    for first, last, fname in man.get(l["flight"].upper(), []):
        off = (first - std).total_seconds() / 3600.0
        if (horizon_h is None or abs(off) <= horizon_h) and (best is None or abs(off) < abs(best[0])):
            best = (off, first, last, fname)
    return best


def write_csv(legs, path, log_day, man, log_src):
    """One row per planned leg the folder does not hold, plainly: what, where, why, whether closing
    it needs a fetch or only a log rebuild, and - for every `no-track` - the nearest track the
    archive does hold under that flight number, so a day that moved is never read as a flight that
    vanished. The markdown is for reading; this is for working through."""
    NEEDS = {"no-track": "fetch", "beyond-capture": "nothing yet", "cancelled": "nothing",
             "track-under-alias": "log rebuild", "track-not-in-log": "log rebuild"}
    days = sorted({l["leg_date"] for l in legs if l["leg_date"]})
    plan_day = collections.Counter(l["leg_date"] for l in legs)
    held = sorted(v for v in (log_day.get(d, 0) for d in days) if v)
    med = held[len(held) // 2] if held else 0
    cols = ["leg_date", "month", "flight", "sector", "tail", "board_status", "board_state",
            "std_iso", "sta_iso", "why", "needs", "rotation", "rotation_slot", "planned_that_day",
            "logged_that_day", "sibling_track", "sibling_gap_h", "note"]
    out, n = [], 0
    for l in sorted(legs, key=lambda x: (x["leg_date"] or "", x["flight"], x["seq"])):
        v = l["_v"]
        if v == "matched":
            continue
        fl, chain, slot = tri_slot(l)
        d = l["leg_date"] or ""
        got = log_day.get(d, 0)
        sib = sibling(man, l)
        sfile = sib[3] if sib else ""
        sgap = round(sib[0], 1) if sib else ""
        if l["origin"] == l["dest"] or l["flight"] == l["tail"]:
            # a board row with no sector on it (15 Oct: `5X-KDP EBB-EBB NON_SCHEDULED`, the flight
            # field holding a tail). Nothing to fetch and nothing missing - the row is unusable.
            out.append(dict(zip(cols, [d, l["month"], l["flight"], l["sector"], l.get("tail") or "",
                                       l["status"], l.get("board_state") or "", l.get("std_iso") or "",
                                       l.get("sta_iso") or "", "board-row-unusable", "nothing", "", "",
                                       plan_day.get(d, 0), got, "", "",
                                       "the board row names no sector, so it cannot be checked here"])))
            n += 1
            continue
        # the sibling track is named in the `sibling_track` column; the note only repeats it where
        # the day itself - not the track - is the reason this row is open
        tail_note = ""
        if sib and (got == 0 or (med and got < 0.4 * med)):
            tail_note = ("; the archive's nearest %s track is %s, %+.0f h from this STD (%s to %s)"
                         % (l["flight"], sfile, sib[0], sib[1].strftime("%d %b %H:%M"),
                            sib[2].strftime("%d %b %H:%M")))
        sfiled = log_src.get(sfile) if sfile else None
        ssame = bool(sfiled) and sfiled[2] == "%s-%s" % (l["origin"], l["dest"])
        shown = "no log row of its own" if sfiled is None else "%s %s %s" % sfiled
        std = fa.iso(l["std_iso"])
        sta = fa.iso(l["sta_iso"]) or std
        clock = None
        if sib and std is not None:
            x = sib[1].hour * 60 + sib[1].minute
            y = std.hour * 60 + std.minute
            clock = min(abs(x - y), 1440 - abs(x - y))
        if v == "no-track" and got == 0:
            needs, note = "fetch", ("no leg at all is logged on this date - the capture skipped "
                                    "the day" + tail_note)
        elif v == "no-track" and med and got < 0.4 * med:
            needs, note = "fetch", ("only %d legs logged on this date against a typical %d - the day "
                                    "is barely captured" % (got, med) + tail_note)
        elif v == "no-track" and sib and ssame and 18 <= abs(sib[0]) <= 30 and \
                clock is not None and clock <= 180:
            # the same rotation, one day off the board: same clock time, a day apart, and the log has
            # already filed that track on the day it really flew. Not a hole - a plan date to ignore.
            needs = "check the day it flew"
            note = ("the archive holds %s airborne %s to %s on the same sector and the log files it "
                    "as %s: same clock time, a day off, so this row is the board's date, not a lost "
                    "flight" % (sfile, sib[1].strftime("%d %b %H:%M"), sib[2].strftime("%H:%M"), shown))
        elif v == "no-track" and sib and abs(sib[0]) <= 12 and std and sta \
                and sib[1] <= sta and sib[2] >= std:
            needs = "check"
            note = ("this number's nearest file (%s, %s to %s) runs into this leg's window and the log "
                    "files it as %s: either the log has the sector wrong, which is a row to fix, or "
                    "this leg has no capture of its own - one look at the fixes settles it"
                    % (sfile, sib[1].strftime("%d %b %H:%M"), sib[2].strftime("%H:%M"), shown))
        elif v == "no-track" and sib and std and sib[2] < std \
                and (std - sib[2]).total_seconds() <= 6 * 3600:
            needs = "fetch"
            note = ("the nearest %s track (%s) ends %s, %.1f h before this leg leaves %s, and the log "
                    "files that track as %s: the archive has the aircraft on the ground ahead of this "
                    "departure and nothing of it after%s"
                    % (l["flight"], sfile, sib[2].strftime("%d %b %H:%M"),
                       (std - sib[2]).total_seconds() / 3600.0, l["origin"], shown, tail_note))
        elif v == "no-track" and sib:
            needs = "fetch"
            note = ("the nearest %s track (%s) does not overlap this window - %s, %+.1f h from this "
                    "STD, filed as %s"
                    % (l["flight"], sfile, sib[1].strftime("%d %b %H:%M"), sib[0], shown))
        elif v == "no-track" and slot == "middle sector":
            needs, note = "fetch", ("hole inside the %s rotation (%s) - its other legs are in the "
                                    "folder and no track of this flight number exists in the archive "
                                    "at all" % (fl, chain))
        elif v == "no-track" and slot:
            needs, note = "fetch", ("%s rotation, %s leg - no track of this flight number in the "
                                    "archive at all" % (chain, slot))
        elif v == "no-track":
            needs, note = "fetch", "no track of this flight number exists in the archive at all"
        elif v == "beyond-capture":
            needs, note = NEEDS[v], "due after the newest fix in the archive - not a gap yet"
        elif v == "cancelled":
            needs, note = NEEDS[v], "the board cancelled it, so nothing was due to fly"
        elif v == "track-under-alias":
            needs, note = NEEDS[v], ("the track is in manifest.csv under another number - rebuild the "
                                     "log, do not fetch")
        else:
            needs, note = NEEDS[v], "the track is in the archive, the log has no row for it - rebuild"
        out.append({"leg_date": d, "month": l["month"], "flight": l["flight"], "sector": l["sector"],
                    "tail": l.get("tail") or "", "board_status": l["status"],
                    "board_state": l.get("board_state") or "", "std_iso": l.get("std_iso") or "",
                    "sta_iso": l.get("sta_iso") or "", "why": v, "needs": needs, "rotation": fl,
                    "rotation_slot": slot, "planned_that_day": plan_day.get(d, 0),
                    "logged_that_day": got, "sibling_track": sfile, "sibling_gap_h": sgap,
                    "note": note})
        n += 1
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    by = collections.Counter(r["needs"] for r in out)
    print("csv: %d rows to %s - %s" % (n, path, ", ".join("%s %d" % kv for kv in sorted(by.items()))))
    print("     by kind:", ", ".join("%s %d" % kv for kv in sorted(collections.Counter(
        r["why"] for r in out).items())))
    print("     triangle legs:", sum(1 for r in out if r["rotation"]),
          "(%d of them the middle sector)" % sum(1 for r in out if r["rotation_slot"] == "middle sector"))



def main():
    legs = plan_legs()
    logged = fa.logs(MONTHS)
    for r in logged:
        r["origin"], r["dest"] = ap(r["origin"]), ap(r["dest"])
    matched = fa.join(legs, logged, 180)
    matched_ids = {id(m["leg"]) for m in matched}
    by_id = {id(l): l for l in legs}
    man = fa.manifest_windows()
    man_rows = fa.read_csv(os.path.join(ROOT, "fr24_publish", fa.MONTHS["2026-10"], "manifest.csv"))
    last_fix = max(r["last_utc"] for r in man_rows if r["last_utc"])
    n_tracks = len(man_rows)                     # never hard-coded: this said 850 after a +22 ingest
    log_counts = {m: len(fa.read_csv(os.path.join(ROOT, "fr24_publish", fa.MONTHS[m], "flights.csv")))
                  for m in MONTHS}

    # Presence, not bookkeeping. The greedy 1:1 join is too strict for this question - on a
    # thrice-daily sector it hands the one observed log leg to a single rotation and calls
    # every neighbour a hole. So: does the log have a leg of that sector at all around then?
    # Tight for a departure from Entebbe (that is the leg that starts a route-day, and EBB
    # has traffic every day, so letting it slide a day would hide a real hole); one day of
    # slack afterwards, where a delay or a post-midnight departure moves the date but not
    # the flight.
    # Presence, judged the way the folder itself is organised: the month log buckets a leg
    # by its **ops day** (`date_local`, the landing day for a red-eye), so compare buckets,
    # not timestamps. One day of extra slack where the board already says DELAYED or
    # RESCHEDULED, or where a night departure can land after midnight.
    MON = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,
           "NOV":11,"DEC":12}
    seen = collections.defaultdict(set)
    log_day = collections.Counter()      # logged legs per local day, for the thin-day test
    log_src = {}                              # track file -> how the log filed it
    for m in MONTHS:
        for r in fa.read_csv(os.path.join(ROOT, "fr24_publish", fa.MONTHS[m], "flights.csv")):
            day, mo = r["date_local"][:2], r["date_local"][2:5]
            if mo not in MON:
                continue
            d = "%s-%02d-%02d" % (m[:4], MON[mo], int(day))
            seen[(d, (ap(r["origin"]), ap(r["dest"])))].add(r["flight"])
            log_day[d] += 1
            log_src[r.get("source_file") or ""] = (r["date_local"], r["flight"],
                                                    "%s-%s" % (r["origin"], r["dest"]))

    def present(l):
        if not l["leg_date"]:
            return False
        d0 = dt.date.fromisoformat(l["leg_date"][:10])
        days = {d0}
        # Deliberately tight, and judged on the board's own clock, not on the origin's local time:
        # a day of slack on a *daily* sector excuses the leg before or after it, so an EBB departure
        # at 22:10 local would be "matched" by the next day's flight. Where a leg really did slip past
        # midnight and is logged a day on (24 Sep `UR902` EBB-LOS, STD 19:10Z, airborne 21:40Z, filed
        # on 25 Sep), the gap row says so in its note and names the log row instead of hiding here.
        night = l["std_iso"] and l["std_iso"][11:13] >= "21"
        if night or l["status"] in ("DELAYED", "RESCHEDULED"):
            days |= {d0 + dt.timedelta(days=1)}
        if l["origin"] != "EBB":                 # the return of a red-eye can sit a day early
            days |= {d0 - dt.timedelta(days=1)} if night else set()
        return any((d.isoformat(), (l["origin"], l["dest"])) in seen for d in days)

    # Which track, if any, belongs to this planned leg: each track in the manifest is given
    # to the closest planned leg carrying that flight number, so a track is not counted for
    # two neighbouring legs (15 Sep: the 13:32 UR722 track belongs to HRE-LUN, not to the
    # EBB-HRE leg that left EBB at 10:00 and was never captured at all).
    owners = collections.defaultdict(list)
    for i, l in enumerate(legs):
        std = fa.iso(l["std_iso"])
        if std is None:
            continue
        for key in {l["flight"].upper(), "UGD" + l["flight"][2:].upper()}:
            owners[key].append((std, i))
    assigned = set()
    for key, windows in man.items():
        cand = owners.get(key.upper(), [])
        if not cand:
            continue
        for first, last, fname in windows:
            best = min(cand, key=lambda t: abs((first - t[0]).total_seconds()))
            if abs((first - best[0]).total_seconds()) <= 7 * 3600:
                assigned.add((best[1], fname))

    def has_own_track(l):
        return any(i == id_idx[id(l)] for i, _ in assigned)

    def track_spans(l):
        """Not merely that a track of this number lies near the leg: the log spends one leg's file
        on the leg before or after it all day, and calling that "tracked but not logged" tells the
        reader to rebuild a log that is right. The file has to cover this leg's own window."""
        std = fa.iso(l["std_iso"])
        if std is None:
            return ""
        sta = fa.iso(l["sta_iso"]) or std + dt.timedelta(minutes=30)
        for first, last, fname in man.get(l["flight"].upper(), []):
            if first <= std + dt.timedelta(minutes=60) and last >= sta - dt.timedelta(minutes=60):
                return fname
        return ""

    id_idx = {id(l): i for i, l in enumerate(legs)}

    def verdict(l):
        if present(l) or id(l) in matched_ids:
            return "matched"
        if l["status"] == "CANCELLED":
            return "cancelled"
        if l["std_iso"] and l["std_iso"].rstrip("Z") > last_fix[:16]:
            return "beyond-capture"
        if has_own_track(l) and track_spans(l):
            return "track-not-in-log"
        # Hoima/Kabalega: the archive has those legs, filed under the wrong flight number
        if "KBG" in (l["origin"], l["dest"]) and man.get("UR523"):
            return "track-under-alias"
        return "no-track"

    for l in legs:
        l["_v"] = verdict(l)
    print("FR data folder: %d logged legs · archive newest fix %s" % (len(logged), last_fix))
    print("plan legs read: %d (%s)" % (len(legs), ", ".join("%s %d" % (m, sum(1 for l in legs if l["month"] == m)) for m in MONTHS)))
    print("verdicts:", dict(collections.Counter(l["_v"] for l in legs)))

    # `--csv PATH` also puts the same answer in a file, one row per leg the folder does not hold
    arg = sys.argv[1:]
    csv_out = arg[arg.index("--csv") + 1] if "--csv" in arg and len(arg) > arg.index("--csv") + 1 else ""
    if csv_out:
        write_csv(legs, csv_out, log_day, man, log_src)

    L = ["# Triangle rotations and route pairs, against the FR data folder", "",
         "Plan of record: the FTA boards (`work/fta/plans/`). Ground truth for what the dataset holds:",
         "`fr24_publish/UR SEPTEMBER 2026/flights.csv` (%d) and `UR OCTOBER 2026/flights.csv` (%d),"
         % (log_counts["2026-09"], log_counts["2026-10"]),
         "with `manifest.csv` (%d tracks, newest fix **%s**) used to tell a lost leg from a partial track."
         % (n_tracks, last_fix), ""]

    # ---------------- 1. rotations
    L.append("## 1. Triangle rotations")
    L.append("")
    summary = {}
    for flight, name, secs in ROTATIONS:
        # a circuit starts at the first sector; the next two can fall on the following
        # board, because the rotation runs on past midnight UTC
        idx = collections.defaultdict(list)
        for l in legs:
            if (l["origin"], l["dest"]) in secs:
                idx[(l["leg_date"] or l["board_date"], (l["origin"], l["dest"]))].append(l)
        starts = sorted({d for (d, sec) in idx if sec == secs[0]})
        whole, holes = 0, []
        for d in starts:
            d0 = dt.date.fromisoformat(d)
            row, seen_from = {}, []
            anchor = sorted(idx[(d, secs[0])], key=lambda x: x["std_iso"])[0]
            for k, sec in enumerate(secs):
                if k == 0:
                    row[sec] = (anchor, d)
                    continue
                cand = []
                for off in (0, 1):
                    dd = (d0 + dt.timedelta(days=off)).isoformat()
                    cand += [l for l in idx.get((dd, sec), []) if l is not anchor]
                same_matched = [l for l in cand if l["tail"] == anchor["tail"] and l["_v"] == "matched"]
                same = [l for l in cand if l["tail"] == anchor["tail"]]
                pick = (same_matched or same or cand or [None])[0]
                if pick is not None:
                    row[sec] = (pick, (pick["std_iso"] or pick["leg_date"] or d)[:10])
            got = sum(1 for sec in secs if sec in row and row[sec][0]["_v"] == "matched")
            if got == len(secs):
                whole += 1
                continue
            miss = []
            for sec in secs:
                if sec not in row:
                    miss.append("%s-%s not on the board" % sec)
                elif row[sec][0]["_v"] != "matched":
                    note = row[sec][0]["_v"]
                    if row[sec][1] != d:
                        note += " (on the %s board)" % row[sec][1][8:]
                    miss.append("%s-%s: %s" % (sec[0], sec[1], note))
            holes.append((d, got, "; ".join(miss) or "-", anchor["tail"]))
        summary[flight] = (len(starts), whole, len(holes))
        L.append("**`%s` %s** - circuit starts on %d days, all three legs logged on %d, "
                 "**short on %d**:"
                 % (flight, name, len(starts), whole, len(holes)))
        L.append("")
        if holes:
            L.append("| start | legs with a log row | what the log or the archive is missing | tail |")
            L.append("|---|---|---|---|")
            for d, n, miss, tail in holes:
                L.append("| %s | %d of 3 | %s | %s |" % (d, n, miss, tail or "-"))
        else:
            L.append("- no short circuit in either month.")
        L.append("")

    # ---------------- 2. out-and-back routes
    L.append("## 2. Out-and-back routes with only one side in the folder")
    L.append("")
    # One line per planned departure from Entebbe on a round-trip route. The leg that comes
    # back to Entebbe is looked for on the same date or the next, because the boards date a
    # night rotation by the day it starts. Presence per leg is already decided in the verdict
    # table, so there is no 1:1 matching to get wrong here.
    rets_idx = collections.defaultdict(list)
    for l in legs:
        if l["origin"] != "EBB" and l["leg_date"]:
            rets_idx[(l["leg_date"][:10], (l["origin"], l["dest"]))].append(l)
    out_idx = collections.defaultdict(list)
    for l in legs:
        if l["origin"] == "EBB" and l["leg_date"]:
            out_idx[(l["leg_date"][:10], (l["origin"], l["dest"]))].append(l)
    rows, thin, no_ret, complete, absent = [], [], [], 0, []
    for (d, sec), outs in sorted(out_idx.items()):
        if sec in TRIANGLE_SECTORS:
            continue
        x = sec[1]
        pool = list(rets_idx.get((d, (x, "EBB")), [])) + list(
            rets_idx.get(((dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat(), (x, "EBB")), []))
        held_out = sum(1 for l in outs if l["_v"] == "matched")
        held_ret = sum(1 for l in pool if l["_v"] == "matched")
        if not pool:
            no_ret.append((d, sec, outs))
            continue
        short = [l for l in outs + pool if l["_v"] != "matched"]

        def fmt(n, h, a, bb):
            return "%s-%s %d planned, %d in the folder" % (a, bb, n, h)

        if held_out and held_ret and len(outs) == held_out and len(pool) == held_ret:
            complete += 1
            continue
        line = "| %s | %s-%s / %s-EBB | %s | %s | %s | %s | %s | %s |" % (
            d, sec[0], x, x,
            fmt(len(outs), held_out, sec[0], x), fmt(len(pool), held_ret, x, "EBB"),
            "/".join(sorted({l["_v"] for l in short})) or "-",
            "/".join(sorted({l["status"] for l in short})) or "-",
            "/".join(sorted({l["tail"] or "-" for l in short})) or "-",
            "/".join(sorted({l["flight"] for l in short})) or "-")
        if bool(held_out) != bool(held_ret):
            rows.append(line)
        elif held_out == 0 and held_ret == 0:
            absent.append(line)
        else:
            thin.append(line)
    n_outs = sum(len(v) for k, v in out_idx.items() if k[1] not in TRIANGLE_SECTORS)
    L.append("%d Entebbe round-trip route-days in the two months (%d planned legs out): **%d both sides "
             "in the folder**, **%d with exactly one side in the folder**, %d with one leg short of the "
             "plan on both sides, %d with neither side, and %d whose return was never on the board."
             % (complete + len(rows) + len(thin) + len(absent) + len(no_ret), n_outs,
                complete, len(rows), len(thin), len(absent), len(no_ret)))
    L.append("")
    L.append("| date | route | out | back | why | status | tail | flight |")
    L.append("|---|---|---|---|---|---|---|---|")
    L.extend(rows)
    L.append("")
    if thin:
        L.append("Both sides present, fewer legs than the plan (same table format):")
        L.append("")
        L.append("| date | route | out | back | why | status | tail | flight |")
        L.append("|---|---|---|---|---|---|---|---|")
        L.extend(thin)
        L.append("")
    if absent:
        L.append("Neither side in the folder - these are the 6-7 Oct legs after the last fix, and the "
                 "Hoima shuttles:")
        L.append("")
        L.append("| date | route | out | back | why | status | tail | flight |")
        L.append("|---|---|---|---|---|---|---|---|")
        L.extend(absent)
        L.append("")
    if no_ret:
        L.append("No return leg on the board at all (the airline ended the rotation there, so the "
                 "folder is not at fault):")
        for d, sec, outs in no_ret:
            L.append("- %s %s-%s (planned %s, %s)" % (d, sec[0], sec[1],
                       ", ".join(sorted({l["flight"] for l in outs})),
                       "/".join(sorted({l["status"] for l in outs}))))
        L.append("")
    L.append("Hoima/Kabalega is in the folder as data but absent from the log: nine shuttle tracks "
             "(27, 29 and 30 Sep) sit in `manifest.csv` as `UR523` with callsign `AF523`, while the "
             "boards number the same legs `UR130`-`UR133` and never write a KBG row. §4 lists them as "
             "a log rebuild, not a fetch. Nothing here is 'before capture': the archive holds at "
             "least one track on every date in September.")
    L.append("")

    # per-sector totals, so a route can be seen as a habit rather than a one-off
    L.append("## 3. Sector totals in the folder vs the plan")
    L.append("")
    plan_n = collections.Counter((l["origin"], l["dest"]) for l in legs
                                if (l["origin"], l["dest"]) not in TRIANGLE_SECTORS)
    log_n = collections.Counter((r["origin"], r["dest"]) for r in logged)
    L.append("| sector | planned on the boards | legs in the month log | short |")
    L.append("|---|---|---|---|")
    rows = []
    for sec in sorted(set(plan_n) | set(log_n)):
        p, g = plan_n.get(sec, 0), log_n.get(sec, 0)
        rows.append((p - g, sec, p, g))
    for short, sec, p, g in sorted(rows, key=lambda x: (-x[0], x[1])):
        if short or g < p:
            L.append("| %s-%s | %d | %d | **%+d** |" % (sec[0], sec[1], p, g, -short if short else g - p))
    L.append("")
    L.append("(triangle sectors are in §1; only sectors where the folder holds fewer legs than the plan "
             "are listed. EBB-KBG / KBG-EBB are short in the log only - the tracks are there as UR523.)")
    L.append("")

    # ---------------- 4. what to fetch
    L.append("## 4. The fetch list")
    L.append("")
    need = [l for l in legs if l["_v"] == "no-track"]
    moved = [l for l in need if sibling(man, l, 48)]
    L.append("%d planned legs have no track of that flight number within twelve hours of their STD "
             "(and no leg of that sector logged on that day or the next), across %s. %d of them have "
             "a same-number track somewhere in the archive within two days, and that neighbour is "
             "worth reading before any fetch: one to two days off at the same clock time is the "
             "board's date having moved, a track ending an hour before this leg is due is the capture "
             "stopping at a ground stop, and a track the log has spent on the sector either side of "
             "this one is a leg that crossed midnight. `work/fta/missing_flights.csv` gives every row "
             "its `sibling_track`, that gap in hours, how the log filed the sibling, and a `needs` "
             "value saying whether to fetch, look at the day it flew, or rebuild the log."
             % (len(need), " and ".join(sorted({l["month"] for l in need})), len(moved)))
    L.append("")
    L.append("| date | flight | sector | tail | status | STD |")
    L.append("|---|---|---|---|---|---|")
    for l in sorted(need, key=lambda x: (x["leg_date"], x["flight"])):
        L.append("| %s | %s | %s | %s | %s | %s |"
                 % (l["leg_date"], l["flight"], l["sector"], l["tail"] or "-", l["status"],
                    (l["std_iso"] or "")[:16]))
    L.append("")
    thin = [l for l in legs if l["_v"] != "matched" and l["_v"] != "no-track"
            and l["_v"] != "cancelled" and l["_v"] != "beyond-capture"]
    L.append("%d more are in the archive but not in the month log, so they need a **log rebuild**, "
             "not a fetch:" % len(thin))
    L.append("")
    L.append("| date | flight | sector | tail | status | STD | note |")
    L.append("|---|---|---|---|---|---|---|")
    for l in sorted(thin, key=lambda x: (x["leg_date"], x["flight"])):
        L.append("| %s | %s | %s | %s | %s | %s | %s |"
                 % (l["leg_date"], l["flight"], l["sector"], l["tail"] or "-", l["status"],
                    (l["std_iso"] or "")[:16],
                    "held as `UR523`/`AF523`" if l["_v"] == "track-under-alias"
                    else "track overlaps, no log row"))
    L.append("")
    def nearby(l):
        std = fa.iso(l["std_iso"])
        if std is None:
            return ""
        best = None
        for first, last, fname in man.get(l["flight"].upper(), []):
            off = abs((first - std).total_seconds())
            if off <= 12 * 3600 and (best is None or off < best[0]):
                best = (off, fname)
        return best[1] if best else ""

    near = [l for l in need if nearby(l)]
    if near:
        L.append("")
        L.append("Of those, %d do have a track of that flight number in the same window, but the track "
                 "is nearer another leg of the same flight and is already used by it - usually that "
                 "file dies on the ground or mid-descent at the airport this leg leaves from, so the "
                 "continuation was never captured. Worth a manual look before fetching:" % len(near))
        L.append("")
        L.append("| date | flight | sector | STD | track the window holds |")
        L.append("|---|---|---|---|---|")
        for l in sorted(near, key=lambda x: (x["leg_date"], x["flight"])):
            L.append("| %s | %s | %s | %s | `%s` |" % (l["leg_date"], l["flight"], l["sector"],
                                                        (l["std_iso"] or "")[:16], nearby(l)))
        L.append("")
    L.append("Three of the no-track legs (14 Sep `UR720` EBB-LUN and LUN-HRE, 20 Sep `UR900` EBB-LOS) "
             "are not holes in the folder: no track of that flight number exists on that day at all, "
             "and on 14 Sep the board cancels the third leg too, so the rotation never went out.")
    L.append("")

    text = "\n".join(L) + "\n"
    open(os.path.join(ROOT, "work", "route_gaps.md"), "w").write(text)
    print(text)
    print("[written] work/route_gaps.md")


if __name__ == "__main__":
    main()
