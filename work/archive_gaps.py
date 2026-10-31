#!/usr/bin/env python3
"""What the archive says is missing, read against itself. No timetable, no airline board, no plan.

The export is self-evidencing in a way a schedule is not. A track ends on the ground at one
airport and the next file for that callsign starts on the ground at another: between those two
fixes the aircraft moved, and if no file covers the movement, the movement is a hole in the data
- which is a statement about the download, not about whether an airline operated anything. Three
tests, all from the fixes alone:

  dark    windows in a day where the archive holds no fix anywhere - the only honest reading of a
          day with "0 flights logged": the recorder was not there, so nothing can be concluded
  gaps    ground-to-ground discontinuities per callsign, with the month log checked so a leg the
          log already holds under another file is not reported as a hole
  unfiled captures no leg row cites: a track that starts and ends on the ground, sits in the
          month, and is used by nothing

Run:  python3 work/archive_gaps.py [--month 2026-10] [--wide]
"""
import argparse
import collections
import csv
import datetime as dt
import math
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(ROOT, "fr24_publish", "FR data.zip")
REF = os.path.join(ROOT, "fr24_publish", "reference", "airports.csv")
MONTHS = {"2026-09": "UR SEPTEMBER 2026", "2026-10": "UR OCTOBER 2026"}
NEAR_KM = 20.0                     # a fix this close to a reference point is "at" that airport
GROUND_FT, GROUND_KT = 1200.0, 120.0
# the reference extract is OurAirports idents and does not carry every airport this network uses;
# these are the ones it lacks, keyed by the code the log writes, with the codes that mean the same
# piece of ground. Anything the reference already has is ignored, so nothing is duplicated.
EXTRA = {
    "LUN": (["FWLI", "FWLU", "LWJA", "LUN"], (-15.3315, 28.4463)),   # Kenneth Kaunda Intl, Lusaka
    "JRO": (["HTKI", "JRO"], (-3.4294, 37.0745)),                    # Kilimanjaro
    "LOS": (["DNNN", "LOS"], (6.5774, 3.3210)),                       # Murtala Muhammed, Lagos
    "MGQ": (["HUGU", "MGQ"], (0.4917, 32.2893)),                       # Gulu
    "EBB": (["HUEN", "EBB"], (0.0445, 32.4480)),                       # Entebbe
    "NBO": (["HKJK", "NBO"], (-1.3192, 36.9278)),                      # JKIA, Nairobi
    "JNB": (["FACT", "JNB"], (-26.1300, 28.2300)),                     # OR Tambo
    "MBA": (["HKMO", "MBA"], (-4.0350, 39.5986)),                      # Moi, Mombasa
    "DAR": (["HTDA", "DAR"], (-6.8754, 39.2015)),                       # Julius Nyerere
    "ZNZ": (["HTZA", "ZNZ"], (-6.2220, 39.2249)),                       # Zanzibar
    "HRE": (["FVHA", "HRE"], (-17.9188, 31.0989)),                     # Harare
    "BJM": (["HBBA", "BJM"], (-3.3240, 29.3184)),                       # Bujumbura
    "JUB": (["HJJJ", "JUB"], (4.8720, 31.6011)),                        # Juba
    "KGL": (["HRYR", "KGL"], (-1.9686, 30.1395)),                       # Kigali
    "LGW": (["EGKK", "LGW"], (51.1481, -0.1903)),                       # Gatwick
    "BOM": (["VABB", "BOM"], (19.0894, 72.8656)),                       # Mumbai
    "DXB": (["OMDB", "DXB"], (25.2532, 55.3657)),                       # Dubai
    "FIH": (["FZAA", "FIH"], (-4.3858, 15.4446)),                       # Ndolo/Kinshasa
}


def airports():
    """coords keyed by one code per physical airport, plus every alias mapped onto it."""
    pos, alias, label = {}, {}, {}
    rows = []
    try:
        rows = list(csv.DictReader(open(REF, newline="", encoding="utf-8")))
    except OSError:
        pass
    for r in rows:
        try:
            p = (float(r["latitude_deg"]), float(r["longitude_deg"]))
        except (TypeError, ValueError):
            continue
        key = (r.get("iata_code") or r.get("gps_code") or r.get("ident") or "").strip()
        if not key:
            continue
        pos[key] = p
        label[key] = key
        for alt in (r.get("iata_code"), r.get("gps_code"), r.get("ident")):
            if alt:
                alias[alt.strip()] = key
    for key, (alts, p) in EXTRA.items():
        if any(k in pos for k in alts):          # the reference already carries this ground
            hit = next((k for k in alts if k in pos), None)
            for a in alts:
                alias[a] = hit
            continue
        pos[key] = p
        label[key] = key
        for a in alts:
            alias[a] = key
    return pos, alias, label


def dist_km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def _row(line, hdr):
    d = dict(zip(hdr, next(csv.reader([line]))))
    pos = (d.get("Position") or "").strip('"').split(",")
    try:
        lat, lon = float(pos[0]), float(pos[1])
    except (ValueError, IndexError):
        return None
    t = (d.get("UTC") or "").replace("T", " ").replace("Z", "")
    try:
        when = dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    def num(k):
        try:
            return float(d.get(k) or "")
        except ValueError:
            return None
    return dict(t=when, pos=(lat, lon), alt=num("Altitude"), spd=num("Speed"),
                cs=(d.get("Callsign") or "").strip())


def tracks():
    """One record per track file: where it starts and ends, and whether each end is on the ground."""
    pos, alias, label = airports()
    out = []
    with zipfile.ZipFile(ZIP) as z:
        for name in z.namelist():
            if not name.endswith(".csv"):
                continue
            txt = z.read(name).decode("utf-8", "replace").strip().split("\n")
            if len(txt) < 3:
                continue
            hdr = next(csv.reader([txt[0]]))
            a, b = _row(txt[1], hdr), _row(txt[-1], hdr)
            if a is None or b is None:
                continue
            fname = name.split("/")[-1]
            cs = a["cs"] or (fname.split("-")[0] if "-" in fname else "")

            def at(p):
                best, code = None, ""
                for k, q in pos.items():
                    d = dist_km(p, q)
                    if best is None or d < best:
                        best, code = d, k
                if best is not None and best <= NEAR_KM:
                    return label.get(code, code)
                return ""
            out.append(dict(file=fname, cs=cs, n=len(txt) - 1, first=a["t"], last=b["t"],
                            start=at(a["pos"]), end=at(b["pos"]),
                            s_ground=(a["alt"] or 0) < GROUND_FT and (a["spd"] or 999) < GROUND_KT,
                            e_ground=(b["alt"] or 0) < GROUND_FT and (b["spd"] or 999) < GROUND_KT))
    out.sort(key=lambda r: r["first"])
    return out


def dark_windows(tr, min_gap_min=120):
    """for every UTC day, the stretches inside it holding no fix from any file at all. A dark
    stretch is not the network sitting still: it is the export not covering that time, so no absence
    inside it can be read as a flight that did not happen."""
    days = sorted({r["first"].date() for r in tr} | {r["last"].date() for r in tr})
    out = {}
    for d in days:
        t0 = dt.datetime.combine(d, dt.time())
        t1 = t0 + dt.timedelta(days=1)
        iv = sorted((max(r["first"], t0), min(r["last"], t1)) for r in tr
                    if r["first"] < t1 and r["last"] > t0)
        if not iv:
            out[d] = [(t0, t1)]
            continue
        cur, gaps = t0, []
        for s_, e_ in iv:
            if s_ > cur:
                gaps.append((cur, s_))
            cur = max(cur, e_)
        if cur < t1:
            gaps.append((cur, t1))
        out[d] = [g for g in gaps if (g[1] - g[0]).total_seconds() >= min_gap_min * 60]
    return out


def overlap_min(t0, t1, dark):
    """minutes of [t0, t1] that fall inside a dark stretch"""
    tot = 0.0
    for s_, e_ in dark:
        lo_, hi_ = max(t0, s_), min(t1, e_)
        if hi_ > lo_:
            tot += (hi_ - lo_).total_seconds() / 60.0
    return tot


def log_rows():
    rows = []
    for m, folder in MONTHS.items():
        p = os.path.join(ROOT, "fr24_publish", folder, "flights.csv")
        try:
            for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
                r["month"] = m
                rows.append(r)
        except OSError:
            pass
    return rows


MON = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
       "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}


def logday(lab):
    """'03OCT26' -> a date. The log buckets a leg by the local date where it lifts off."""
    if len(lab) == 7 and lab[2:5] in MON:
        try:
            return dt.date(2000 + int(lab[5:7]), MON[lab[2:5]], int(lab[:2]))
        except ValueError:
            return None
    return None


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--month", default="2026-10")
    ap_.add_argument("--wide", action="store_true", help="print every discontinuity, not just the holes")
    a = ap_.parse_args()
    m = a.month
    y, mo = int(m[:4]), int(m[5:7])
    lo = dt.datetime(y, mo, 1)
    hi = dt.datetime(y + (mo == 12), (mo % 12) + 1, 1)

    tr = tracks()
    inmonth = [r for r in tr if lo <= r["first"] < hi]
    newest = max(r["last"] for r in tr)
    print("archive read: %d track files · %d with a first fix inside %s · newest fix anywhere %sZ"
          % (len(tr), len(inmonth), m, newest))

    # ---------------- 1. how much of each day the export can see at all
    dark = dark_windows(tr)
    days = sorted(d for d in dark if lo.date() - dt.timedelta(days=1) <= d < hi.date())
    byday = collections.defaultdict(list)
    for r in tr:
        byday[r["first"].date()].append(r)
    alldark = [g for d in days for g in dark[d]]
    print("\n== what the export can see, by UTC day ==")
    print("  dark = a stretch of that day holding no fix from any callsign at all (>= 2 h); files,")
    print("  fixes and the two times count the tracks that START that day, dark uses every track's span.")
    print("  date          files  fixes     first fix   last fix    dark")
    for d in days:
        rows = byday.get(d, [])
        txt = ", ".join("%s-%s (%d min)" % (s.strftime("%H:%M"), e.strftime("%H:%M"),
                                            (e - s).total_seconds() // 60) for s, e in dark[d]) or "-"
        if not rows:
            print("  %s      0       0        -           -     %s" % (d, txt))
            continue
        print("  %s  %5d %7d   %s    %s   %s"
              % (d, len(rows), sum(r["n"] for r in rows),
                 min(r["first"] for r in rows).strftime("%H:%M:%S"),
                 max(r["last"] for r in rows).strftime("%H:%M:%S"), txt))

    # ---------------- 2. movements the fixes do not cover
    log = log_rows()
    cited = {r["source_file"] for r in log}
    legs = collections.defaultdict(list)
    for r in log:
        legs[(r["flight"][-3:], r["origin"], r["dest"])].append(logday(r["date_local"]))
    by_cs = collections.defaultdict(list)
    for r in tr:
        if r["cs"]:
            by_cs[r["cs"].upper()].append(r)
    live = sorted((r["first"], r["last"]) for r in tr)
    def airborne_n(t0, t1):
        """how many other files hold fixes across this interval: if the answer is not zero, the
        export was looking at the sky at that moment and this movement is absent from it."""
        return sum(1 for a, b in live if a < t1 and b > t0)

    print("\n== a callsign is last seen on the ground at A and next seen on the ground at B ==")
    print("  the A-B movement is in the data as nothing at all. \"the log holds a X-Y row then\" and")
    print("  \"another callsign covers it\" mean the absence is a file-keeping artefact, not a missing flight.")
    print("  \"blind for N%\" / \"unobservable\" mean the export holds no fix from any callsign across that")
    print("  much of the interval, so nothing follows from an absence inside it. \"thin sky\" and \"the export")
    print("  was watching\" count other tracks overlapping the interval: how much of the sky was recorded,")
    print("  never whether this particular flight flew.")
    holes = 0
    lines = []
    for cs, rows in sorted(by_cs.items()):
        rows.sort(key=lambda r: r["first"])
        for x, y_ in zip(rows, rows[1:]):
            if not (x["end"] and y_["start"]) or x["end"] == y_["start"]:
                continue
            if not (lo <= x["last"] < hi):
                continue
            gap = (y_["first"] - x["last"]).total_seconds() / 60.0
            if gap < 15 or gap > 100 * 60:
                continue
            key = (cs[-3:], x["end"], y_["start"])
            near = any(dd and abs((dd - x["last"].date()).days) <= 1 for dd in legs.get(key, []))
            other = sum(1 for r in tr if r["start"] == x["end"] and r["end"] == y_["start"]
                        and x["last"] - dt.timedelta(hours=6) <= r["first"] <= y_["first"] + dt.timedelta(hours=6))
            n_live = airborne_n(x["last"], y_["first"]) - 2
            blind = overlap_min(x["last"], y_["first"], alldark)
            pct = 100.0 * blind / max(gap, 1)
            inside = [(min(y_["first"], e_) - max(x["last"], s_), s_.date()) for s_, e_ in alldark
                      if min(y_["first"], e_) > max(x["last"], s_)]
            worst = max(inside, key=lambda t: t[0]) if inside else None
            if pct >= 60:
                verdict = "blind for %d%% of the interval" % round(pct)
            elif worst and worst[0].total_seconds() >= 6 * 3600:
                verdict = "unobservable: a blind stretch of %d h on %s sits inside" \
                          % (worst[0].total_seconds() // 3600, worst[1])
            elif n_live <= 3:
                verdict = "thin sky: %d other track(s) up then" % n_live
            else:
                verdict = "the export was watching: %d tracks up" % n_live
            if near:
                verdict = "the log holds a %s-%s row then" % key[1:]
            elif other:
                verdict = "another callsign covers it (%d file(s))" % other
            if (near or other) and not a.wide:
                continue
            holes += 1
            lines.append("  %s  %-8s %-4s->%-4s  %7.0f min apart  %-40s  %s / %s"
                         % (x["last"].strftime("%d %b %H:%M"), cs, x["end"], y_["start"], gap,
                            verdict, x["file"], y_["file"]))
    for l in sorted(lines):
        print(l)
    print("  %d shown" % holes)

    # ---------------- 3. captures nobody used
    print("\n== track files in %s that no leg row cites ==" % m)
    un = [r for r in inmonth if r["file"] not in cited]
    both = [r for r in un if r["s_ground"] and r["e_ground"] and r["start"] and r["end"]]
    air = [r for r in un if not (r["s_ground"] and r["e_ground"])]
    print("  %d of %d. %d start and end on the ground at named airports (a real flight the log did"
          " not take), %d are cut in the air (partial captures)." % (len(un), len(inmonth), len(both), len(air)))
    for r in sorted(both, key=lambda x: x["first"]):
        print("   %-22s %-8s %4d fixes  %sZ -> %sZ   %s -> %s"
              % (r["file"], r["cs"] or "-", r["n"], r["first"].strftime("%d %b %H:%M"),
                 r["last"].strftime("%d %b %H:%M"), r["start"], r["end"]))
    print("   cut in the air (first 12 of %d), which is where a truncated capture masquerades as a"
          " flight that started or ended somewhere odd:" % len(air))
    for r in sorted(air, key=lambda x: x["first"])[:12]:
        print("   %-22s %-8s %4d fixes  %sZ -> %sZ   %s%s -> %s%s"
              % (r["file"], r["cs"] or "-", r["n"], r["first"].strftime("%d %b %H:%M"),
                 r["last"].strftime("%d %b %H:%M"), r["start"] or "(airborne)",
                 "" if r["s_ground"] else "*", r["end"] or "(airborne)", "" if r["e_ground"] else "*"))


    print("\n== captures with one end missing (%s) ==" % m)
    s_air = [r for r in inmonth if not r["start"]]
    e_air = [r for r in inmonth if not r["end"]]
    print("  %d of %d files are already on the move at their first fix (the departure was not"
          " captured) and %d are still airborne at their last (the arrival was not). The archive"
          " lost the end of those flights, so any count of legs at either end of the month is"
          " short for that reason alone." % (len(s_air), len(inmonth), len(e_air)))
    for r in s_air[:10]:
        print("   start missing  %-20s %-8s %4d fixes  %s -> %s   first fix at %s%s"
              % (r["file"], r["cs"] or "-", r["n"], r["first"].strftime("%d %b %H:%M"),
                 r["last"].strftime("%d %b %H:%M"), r["start"] or "(in the air)", ""))
    for r in e_air[:10]:
        print("   end missing    %-20s %-8s %4d fixes  %s -> %s   last fix at %s"
              % (r["file"], r["cs"] or "-", r["n"], r["first"].strftime("%d %b %H:%M"),
                 r["last"].strftime("%d %b %H:%M"), r["end"] or "(in the air)"))



if __name__ == "__main__":
    main()
