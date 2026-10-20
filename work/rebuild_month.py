#!/usr/bin/env python3
"""
Rebuild the track-derived tables in a month folder (UR SEPTEMBER 2026 /
UR OCTOBER 2026) from that folder's month zip.

Usage:
    python3 work/rebuild_month.py "UR SEPTEMBER 2026" "UR September flights.zip"
    python3 work/rebuild_month.py "UR OCTOBER 2026" "FR data.zip"

Overwrites in the month folder:
    manifest.csv, flights.csv, runway_usage.csv, fleet_summary.csv,
    triangle_assignments.csv, date_coverage.md, all_flights_aeroroutes.md,
    no_code_tracks.md

Reads if present:
    tails.csv       (tail per flight; Sept = FR24 app, Oct = app + FTA rows)
    fleet_summary.csv (fleet meta columns are carried over by tail)

METAR: fetched separately into <month folder>/metar/ (Iowa State IEM ASOS,
station HUEN etc.) and consumed by work/build_conditions.py. On a machine with
normal internet access:
  curl "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=HUEN&data=metar&year1=2026&month1=9&day1=1&year2=2026&month2=10&day2=1&tz=Etc%2FUTC&format=onlycomma&latlon=no&elev=no&missing=empty&trace=empty&direct=no&report_type=3" -o metar/HUEN_202609.csv
Repeat per station (HUEN HKJK HTDA HTZA HTKJ HJJJ HCMM HBBA HKMO FLLS FVHA
FAOR VABB EGKK DNMM HRYR) and month.

Method
------
* One flight row per track file (the frozen log's convention; multi-sector
  files flagged in sectors_in_file, routed endpoint to endpoint).
* Takeoff = first ground->airborne transition (altitude 0 -> >0); landing =
  last airborne fix before the final airborne->ground transition. Verified
  against the frozen log (UR720-4172c560: takeoff exact, landing within 3 s).
* Tracks starting/ending airborne get *_not_observed; the unobserved end's
  airport comes from the flight number's canonical route.
* origin/dest otherwise = nearest known airport to first/last fix.
* date_local = local date at origin (zoneinfo) of takeoff / first fix.
* Runways: mean ground-roll heading (speed > 20 kt) snapped to the airport's
  runway headings; confidence from the heading mismatch. Simplified model -
  no threshold/performance geometry (the frozen build's survey columns are
  not reproducible without its reference data; see runway_usage.md).
"""
import csv, io, math, re, sys, zipfile
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

AIRPORTS = {
    "EBB": ("HUEN", "Entebbe",            0.042386,  32.443503, "Africa/Kampala",       [172, 352]),
    "NBO": ("HKJK", "Nairobi JKIA",      -1.319239,  36.927775, "Africa/Nairobi",       [61, 241]),
    "DAR": ("HTDA", "Dar es Salaam",     -6.878111,  39.202611, "Africa/Dar_es_Salaam", [46, 226]),
    "ZNZ": ("HTZA", "Zanzibar",          -6.222025,  39.224847, "Africa/Dar_es_Salaam", [183, 3]),
    "JRO": ("HTKJ", "Kilimanjaro",       -3.429406,  37.074461, "Africa/Dar_es_Salaam", [92, 272]),
    "JUB": ("HJJJ", "Juba",               4.872019,  31.601117, "Africa/Juba",          [126, 306]),
    "MGQ": ("HCMM", "Mogadishu",          2.014444,  45.304722, "Africa/Mogadishu",     [50, 230]),
    "BJM": ("HBBA", "Bujumbura",         -3.324019,  29.318519, "Africa/Bujumbura",     [174, 354]),
    "MBA": ("HKMO", "Mombasa",           -4.034830,  39.594250, "Africa/Nairobi",       [33, 213]),
    "LUN": ("FLLS", "Lusaka",           -15.330817,  28.452608, "Africa/Lusaka",        [104, 284]),
    "HRE": ("FVHA", "Harare",           -17.931806,  31.092847, "Africa/Harare",        [50, 230]),
    "JNB": ("FAOR", "Johannesburg",     -26.136673,  28.241146, "Africa/Johannesburg",  [32, 212]),
    "BOM": ("VABB", "Mumbai",            19.089559,  72.865614, "Asia/Kolkata",         [90, 270, 140, 320]),
    "LGW": ("EGKK", "London Gatwick",    51.153662,  -0.182063, "Europe/London",        [84, 264]),
    "LOS": ("DNMM", "Lagos",              6.577369,   3.321156, "Africa/Lagos",         [184, 4]),
    "KGL": ("HRYR", "Kigali",            -1.968628,  30.139450, "Africa/Kigali",        [100, 280]),
    "UGHO":("HKHO", "Hoima (Kabaale)",    1.563900,  31.319700, "Africa/Kampala",       []),
}
RWY_LABEL = {
    ("EBB",172):"17", ("EBB",352):"35", ("NBO",61):"06", ("NBO",241):"24",
    ("DAR",46):"05", ("DAR",226):"23", ("ZNZ",183):"18", ("ZNZ",3):"36",
    ("JRO",92):"09", ("JRO",272):"27", ("JUB",126):"13", ("JUB",306):"31",
    ("MGQ",50):"05", ("MGQ",230):"23", ("BJM",174):"17", ("BJM",354):"35",
    ("MBA",33):"03", ("MBA",213):"21", ("LUN",104):"10", ("LUN",284):"28",
    ("HRE",50):"05", ("HRE",230):"23", ("JNB",32):"03", ("JNB",212):"21",
    ("BOM",90):"09", ("BOM",270):"27", ("BOM",140):"14", ("BOM",320):"32",
    ("LGW",84):"08", ("LGW",264):"26", ("LOS",184):"18", ("LOS",4):"36",
    ("KGL",100):"10", ("KGL",280):"28",
}
ROUTES = {
    "UR110":("EBB","LGW"), "UR111":("LGW","EBB"), "UR120":("EBB","JUB"), "UR121":("JUB","EBB"),
    "UR122":("EBB","JUB"), "UR123":("JUB","EBB"), "UR200":("EBB","NBO"), "UR201":("NBO","EBB"),
    "UR202":("EBB","NBO"), "UR203":("NBO","EBB"), "UR206":("EBB","NBO"), "UR207":("NBO","EBB"),
    "UR208":("EBB","NBO"), "UR209":("NBO","EBB"), "UR320":("EBB","DAR"), "UR321":("DAR","EBB"),
    "UR322":("EBB","DAR"), "UR323":("DAR","EBB"), "UR334":("EBB","ZNZ"), "UR342":("EBB","MBA"),
    "UR343":("MBA","EBB"), "UR360":("EBB","BJM"), "UR361":("BJM","EBB"), "UR430":("EBB","BOM"),
    "UR431":("BOM","EBB"), "UR520":("EBB","MGQ"), "UR521":("MGQ","EBB"), "UR523":("EBB","EBB"),
    "UR710":("EBB","JNB"), "UR711":("JNB","EBB"), "UR712":("EBB","JNB"), "UR713":("JNB","EBB"),
    "UR720":("EBB","LUN"), "UR722":("EBB","HRE"), "UR900":("EBB","LOS"), "UR901":("LOS","EBB"),
    "UR903":("LOS","EBB"),
}
TRIANGLE_OF = {
    "UR206":("Nairobi (A330)","outbound"), "UR207":("Nairobi (A330)","middle"),
    "UR208":("Nairobi (A330)","closing"),  "UR209":("Nairobi (A330)","closing"),
    "UR720":("Harare-Lusaka","triangle sector"), "UR722":("Harare-Lusaka","triangle sector"),
    "UR334":("Zanzibar-Kilimanjaro","multi-sector"),
    "UR342":("Mombasa","outbound"), "UR343":("Mombasa","closing"),
}

def hav_nm(a, b, c, d):
    p = math.pi / 180.0
    x = 0.5 - math.cos((c-a)*p)/2 + math.cos(a*p)*math.cos(c*p)*(1-math.cos((d-b)*p))/2
    return 3440.065 * 2 * math.asin(math.sqrt(max(0.0, x)))

def nearest_airport(lat, lon):
    best, bd = None, 1e9
    for code, (_, _, alat, alon, _, _) in AIRPORTS.items():
        d = hav_nm(lat, lon, alat, alon)
        if d < bd: best, bd = code, d
    return best, bd

def parse_track(text):
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        try:
            lat, lon = (float(x) for x in r["Position"].split(","))
            rows.append(dict(t=int(r["Timestamp"]), utc=r["UTC"], cs=(r["Callsign"] or "").strip(),
                             lat=lat, lon=lon, alt=int(float(r["Altitude"] or 0)),
                             spd=int(float(r["Speed"] or 0)), dir=int(float(r["Direction"] or 0))))
        except Exception:
            continue
    rows.sort(key=lambda x: x["t"])
    return rows

def fmt_utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def analyse(rows):
    n = len(rows)
    ground = [r["alt"] == 0 for r in rows]
    tk_i = next((i for i in range(1, n) if ground[i-1] and not ground[i]), None)
    takeoff_not_obs = tk_i is None and not ground[0]
    ld_i = next((i for i in range(n-1, 0, -1) if ground[i] and not ground[i-1]), None)
    landing_not_obs = ld_i is None and not ground[-1]
    sectors, in_g, start = 1, False, None
    for i in range(1, n):
        if ground[i] and not ground[i-1] and (ld_i is None or i < ld_i):
            in_g, start = True, i
        if in_g and not ground[i]:
            if rows[i]["t"] - rows[start]["t"] > 180: sectors += 1
            in_g = False
    takeoff_t = rows[tk_i]["t"] if tk_i is not None else None
    landing_t = rows[ld_i-1]["t"] if ld_i is not None else None
    dist = sum(hav_nm(a["lat"], a["lon"], b["lat"], b["lon"]) for a, b in zip(rows, rows[1:]))
    # roll/touchdown facts
    liftoff_i = tk_i if tk_i is not None else None
    touchdown_i = ld_i if ld_i is not None else None
    roll_m, rot_kt = "", ""
    if liftoff_i:
        j = liftoff_i
        while j > 0 and rows[j-1]["spd"] > 5 and rows[j-1]["alt"] == 0: j -= 1
        roll_m = round(sum(hav_nm(a["lat"], a["lon"], b["lat"], b["lon"])
                           for a, b in zip(rows[j:liftoff_i], rows[j+1:liftoff_i+1])) * 1852)
        rot_kt = rows[liftoff_i]["spd"]
    td_m, td_kt = "", ""
    if touchdown_i:
        td_kt = rows[touchdown_i-1]["spd"] if touchdown_i else ""
    t_fl300 = ""
    if takeoff_t:
        for r in rows:
            if r["alt"] >= 30000: t_fl300 = round((r["t"] - takeoff_t) / 60.0, 1); break
    return dict(n=n, takeoff_t=takeoff_t, landing_t=landing_t,
                takeoff_not_obs=takeoff_not_obs, landing_not_obs=landing_not_obs,
                liftoff_i=liftoff_i, touchdown_i=touchdown_i, sectors=sectors,
                dist_nm=dist, roll_m=roll_m, rot_kt=rot_kt, td_kt=td_kt, t_fl300=t_fl300,
                max_alt=max(r["alt"] for r in rows), max_spd=max(r["spd"] for r in rows))

def roll_runway(rows, i0, i1, airport):
    hdgs = [rows[i]["dir"] for i in range(max(0, i0), min(len(rows), i1)) if rows[i]["spd"] > 20]
    if not hdgs or airport not in AIRPORTS or not AIRPORTS[airport][5]: return "", "", ""
    sx = sum(math.cos(math.radians(h)) for h in hdgs); sy = sum(math.sin(math.radians(h)) for h in hdgs)
    mean = (math.degrees(math.atan2(sy, sx)) + 360) % 360
    best = min(AIRPORTS[airport][5], key=lambda c: min(abs(mean-c), 360-abs(mean-c)))
    diff = min(abs(mean-best), 360-abs(mean-best))
    return RWY_LABEL.get((airport, best), ""), int(round(mean)), ("high" if diff <= 12 else "medium" if diff <= 25 else "low")

def main():
    folder = Path(sys.argv[1]); zipname = sys.argv[2]
    zf = zipfile.ZipFile(folder / zipname)
    names = sorted(n for n in zf.namelist() if n.endswith(".csv"))

    # existing fleet meta (carried over) + tails (for attachment), read before overwriting
    fleet_meta = {}
    fs_path = folder / "fleet_summary.csv"
    if fs_path.exists():
        for r in csv.DictReader(open(fs_path)):
            fleet_meta[r["tail"]] = r
    tail_rows = []
    t_path = folder / "tails.csv"
    if t_path.exists():
        tail_rows = list(csv.DictReader(open(t_path)))
    def find_tail(date_iso, fno, o, d):
        from datetime import date, timedelta
        y, mo, dd = (int(x) for x in date_iso.split("-"))
        for delta in (0, -1, 1):  # plan/app date can sit either side of the origin-local date
            want = (date(y, mo, dd) + timedelta(days=delta)).isoformat()
            for r in tail_rows:
                if r["date"] == want and r["flight"] == fno and r["origin"] == o and r["dest"] == d:
                    return r["tail"], r.get("verified_track", "")
        return "", ""

    flights, manifest = [], []
    for name in names:
        base = Path(name).name
        m = re.match(r"(UR\d+|AF\d+)-([0-9a-f]+)\.csv", base)
        flight_no, fr24id = (m.group(1), m.group(2)) if m else ("", base[:-4])
        rows = parse_track(zf.read(name).decode("utf-8", "replace"))
        if not rows: continue
        a = analyse(rows)
        cs = next((r["cs"] for r in rows if r["cs"]), "")
        if not flight_no and cs.startswith("UGD"):
            mm = re.match(r"UGD(\d+)", cs); flight_no = "UR" + mm.group(1) if mm else ""
        can_o, can_d = ROUTES.get(flight_no, ("", ""))
        origin, od = nearest_airport(rows[0]["lat"], rows[0]["lon"])
        dest, dd = nearest_airport(rows[-1]["lat"], rows[-1]["lon"])
        # unobserved end: trust the nearest airport when the track already starts
        # near one (sector file picked up airborne); canonical route only when
        # the first/last fix is far from every airport (truncated en route)
        if a["takeoff_not_obs"] and can_o and od > 80: origin = can_o
        if a["landing_not_obs"] and can_d and dd > 80: dest = can_d
        otz = ZoneInfo(AIRPORTS.get(origin, AIRPORTS["EBB"])[4])
        dtz = ZoneInfo(AIRPORTS.get(dest, AIRPORTS["EBB"])[4])
        dep_t = a["takeoff_t"] or rows[0]["t"]           # proxy: first fix
        arr_t = a["landing_t"] or rows[-1]["t"]          # proxy: last fix
        dep_loc = datetime.fromtimestamp(dep_t, timezone.utc).astimezone(otz)
        arr_loc = datetime.fromtimestamp(arr_t, timezone.utc).astimezone(dtz)
        date_local = dep_loc.strftime("%Y-%m-%d")
        tail, verified = find_tail(date_local, flight_no, origin, dest)
        dep_rwy = dep_hdg = dep_conf = arr_rwy = arr_hdg = arr_conf = ""
        if a["liftoff_i"] is not None:
            dep_rwy, dep_hdg, dep_conf = roll_runway(rows, a["liftoff_i"] - 40, a["liftoff_i"] + 2, origin)
        if a["touchdown_i"] is not None:
            arr_rwy, arr_hdg, arr_conf = roll_runway(rows, a["touchdown_i"] - 2, a["touchdown_i"] + 40, dest)
        cruise = sorted(r["spd"] for r in rows if r["alt"] >= 25000)
        flights.append(dict(
            flight=cs, flight_no=flight_no, date_local=date_local, source_file=base,
            origin=origin, dest=dest,
            takeoff_local=dep_loc.strftime("%H%M"), departure_utc=fmt_utc(dep_t).replace("T", " "),
            arrival_local=arr_loc.strftime("%H%M"), arrival_utc=fmt_utc(arr_t).replace("T", " "),
            next_day="Y" if arr_loc.date() > dep_loc.date() else "",
            takeoff_not_observed="Y" if a["takeoff_not_obs"] else "",
            landing_not_observed="Y" if a["landing_not_obs"] else "",
            air_minutes=round((arr_t - dep_t) / 60.0),
            fixes=a["n"], sectors_in_file=a["sectors"], tail=tail, verified_track=verified,
            dep_rwy=dep_rwy, arr_rwy=arr_rwy, max_alt_ft=a["max_alt"],
            cruise_kt=cruise[len(cruise)//2] if cruise else "",
            _dep_hdg=dep_hdg, _arr_hdg=arr_hdg, _dep_conf=dep_conf, _arr_conf=arr_conf, _a=a,
            _dep_dist_km=round(hav_nm(rows[0]["lat"], rows[0]["lon"],
                                      AIRPORTS[origin][2], AIRPORTS[origin][3]) * 1.852, 1) if origin in AIRPORTS else "",
            _arr_dist_km=round(hav_nm(rows[-1]["lat"], rows[-1]["lon"],
                                      AIRPORTS[dest][2], AIRPORTS[dest][3]) * 1.852, 1) if dest in AIRPORTS else "",
            _first_ground = "yes" if rows[0]["alt"] == 0 else "no",
            _last_ground = "yes" if rows[-1]["alt"] == 0 else "no"))
        manifest.append(dict(file=base, flight=flight_no, callsign=cs, fixes=a["n"],
                             first_utc=rows[0]["utc"], last_utc=rows[-1]["utc"],
                             duration_min=round((rows[-1]["t"]-rows[0]["t"])/60.0, 1),
                             bytes=zf.getinfo(name).file_size))
    flights.sort(key=lambda f: (f["departure_utc"] or "9999-99", f["flight"]))

    def write_csv(fn, cols, rows):
        with open(folder / fn, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
            for r in rows: w.writerow({k: r.get(k, "") for k in cols})

    write_csv("manifest.csv", ["file","flight","callsign","fixes","first_utc","last_utc","duration_min","bytes"], manifest)
    fcols = ["date_local","flight","origin","takeoff_local","departure_utc","arrival_local","arrival_utc",
             "dest","next_day","takeoff_not_observed","landing_not_observed","air_minutes","fixes","source_file"]
    out = []
    for f in flights:
        r = {k: f[k] for k in fcols}
        y, mo, d = f["date_local"].split("-")
        r["date_local"] = f"{d}{['','JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'][int(mo)]}{y[2:]}"
        out.append(r)
    write_csv("flights.csv", fcols, out)

    # runway_usage.csv - legacy header, simplified model fills what it can (see runway_usage.md)
    RWY_HDR = ("file,flight,tail,when,log_origin,log_dest,dep_apt,dep_apt_dist_km,dep_apt_ground,dep_rwy,"
      "dep_conf,dep_method,dep_hdg,dep_n_seg,dep_err,dep_xt,dep_rival_xt,dep_margin,dep_day_dir,dep_rwy_len_m,"
      "dep_rwy_width_m,dep_roll_start_m,dep_roll_len_m,dep_runway_used_m,dep_rwy_remaining_m,dep_roll_start_speed_kt,"
      "dep_liftoff_speed_kt,dep_liftoff_bracket_m,dep_liftoff_along_lo,dep_liftoff_along_hi,dep_roll_source,"
      "dep_roll_capture,dep_accel_alt_ft,dep_liftoff_xt_m,dep_liftoff_xt_cal_m,arr_apt,arr_apt_dist_km,arr_apt_ground,"
      "arr_rwy,arr_conf,arr_method,arr_hdg,arr_n_seg,arr_err,arr_xt,arr_rival_xt,arr_margin,arr_day_dir,arr_rwy_len_m,"
      "arr_rwy_halfwidth_m,arr_thr_speed_kt,arr_thr_height_ft,arr_td_along_m,arr_td_along_lo,arr_td_along_hi,"
      "arr_td_bracket_m,arr_td_speed_kt,arr_alt_flat_m,arr_roll_len_m,arr_runway_used_m,arr_rwy_remaining_m,"
      "arr_turnoff_speed_kt,arr_stop_along_m,arr_roll_capture,arr_td_xt_m,arr_td_xt_cal_m").split(",")
    rrows = []
    for f in flights:
        a = f["_a"]
        rrows.append(dict(file=f["source_file"], flight=f["flight"], tail=f["tail"],
            when=f["departure_utc"][:16], log_origin=f["origin"], log_dest=f["dest"],
            dep_apt=AIRPORTS.get(f["origin"], ("",))[0], dep_apt_dist_km=f["_dep_dist_km"],
            dep_apt_ground=f["_first_ground"], dep_rwy=f["dep_rwy"], dep_conf=f["_dep_conf"],
            dep_method="roll" if f["dep_rwy"] else "", dep_hdg=float(f["_dep_hdg"]) if f["_dep_hdg"] != "" else "",
            dep_roll_len_m=a["roll_m"], dep_liftoff_speed_kt=float(a["rot_kt"]) if a["rot_kt"] != "" else "",
            dep_roll_capture="full" if not f["takeoff_not_observed"] else "partial",
            arr_apt=AIRPORTS.get(f["dest"], ("",))[0], arr_apt_dist_km=f["_arr_dist_km"],
            arr_apt_ground=f["_last_ground"], arr_rwy=f["arr_rwy"], arr_conf=f["_arr_conf"],
            arr_method="roll" if f["arr_rwy"] else "", arr_hdg=float(f["_arr_hdg"]) if f["_arr_hdg"] != "" else "",
            arr_td_speed_kt=float(a["td_kt"]) if a["td_kt"] != "" else "",
            arr_roll_capture="full" if not f["landing_not_observed"] else "partial"))
    write_csv("runway_usage.csv", RWY_HDR, rrows)

    # fleet_summary.csv - legacy header; fleet meta carried over, stats rebuilt for this month
    by_tail = defaultdict(list)
    for f in flights:
        if f["tail"]: by_tail[f["tail"]].append(f)
    frows = []
    for tail, fl in sorted(by_tail.items()):
        m = fleet_meta.get(tail, {})
        cr = sorted(f["cruise_kt"] for f in fl if f["cruise_kt"] != "")
        fl300 = sorted(f["_a"]["t_fl300"] for f in fl if f["_a"]["t_fl300"] != "")
        frows.append(dict(tail=tail, type=m.get("type",""), type_full=m.get("type_full",""),
            type_code=m.get("type_code",""), msn=m.get("msn",""), mode_s=m.get("mode_s",""),
            built=m.get("built",""), ownership=m.get("ownership",""), role=m.get("role",""),
            seats_j=m.get("seats_j",""), seats_w=m.get("seats_w",""), seats_y=m.get("seats_y",""),
            seats_total=m.get("seats_total",""), flights_matched=len(fl),
            air_hours=round(sum(f["air_minutes"] for f in fl)/60.0, 1),
            days=len({f["date_local"] for f in fl}),
            routes=len({(f["origin"], f["dest"]) for f in fl}),
            median_cruise_kt=cr[len(cr)//2] if cr else "",
            median_max_FL=sorted(f["max_alt_ft"] for f in fl)[len(fl)//2] // 100,
            median_min_to_FL300=fl300[len(fl300)//2] if fl300 else "",
            routes_list=" ".join(sorted({f"{f['origin']}-{f['dest']}" for f in fl}))))
    if frows:
        write_csv("fleet_summary.csv", list(frows[0].keys()), frows)

    # triangle_assignments.csv - legacy header
    trows = []
    for f in flights:
        if f["flight_no"] in TRIANGLE_OF:
            trows.append(dict(date=f["date_local"], flight=f["flight_no"], callsign=f["flight"],
                origin=f["origin"], dest=f["dest"], tail=f["tail"], verified_track=f["verified_track"]))
    if trows:
        write_csv("triangle_assignments.csv", ["date","flight","callsign","origin","dest","tail","verified_track"], trows)

    # date_coverage.md
    by_date = Counter(f["date_local"] for f in flights)
    lines = ["# Date coverage (rebuilt from month zip)", "",
             f"{len(flights)} flight rows from {len(manifest)} track files.", "",
             "| date (origin local) | flights |", "|---|---:|"]
    lines += [f"| {d} | {by_date[d]} |" for d in sorted(by_date)]
    (folder / "date_coverage.md").write_text("\n".join(lines) + "\n")

    # all_flights_aeroroutes.md
    by_route = defaultdict(list)
    for f in flights: by_route[(f["flight_no"], f["origin"], f["dest"])].append(f)
    lines = ["# All flights by route (rebuilt from month zip)", ""]
    for (fno, o, d), fl in sorted(by_route.items()):
        lines += [f"## {fno} {o}-{d} — {len(fl)} flight(s)", "",
                  "| date | callsign | departure UTC | arrival UTC | air min | source |",
                  "|---|---|---|---|---:|---|"]
        for f in fl:
            lines.append(f"| {f['date_local']} | {f['flight']} | {f['departure_utc']} | {f['arrival_utc']} | {f['air_minutes']} | {f['source_file']} |")
        lines.append("")
    (folder / "all_flights_aeroroutes.md").write_text("\n".join(lines) + "\n")

    # no_code_tracks.md - tracks whose callsign carries no clean UR flight identity
    odd = [f for f in flights if not re.fullmatch(r"UGD\d+", f["flight"] or "")]
    lines = ["# Tracks without a clean UR flight identity (rebuilt)", "",
             "Tracks whose transmitted callsign is not a plain UGD<flight number>:", ""]
    if odd:
        lines += ["| date | callsign | route | source | note |", "|---|---|---|---|---|"]
        for f in odd:
            note = ("AF-prefix domestic/test callsign (Hoima shuttle / EBB local flying)" if f["flight"].startswith("AF")
                    else "suffixed/test callsign" if f["flight"].startswith("UGD") else "no UGD callsign transmitted")
            lines.append(f"| {f['date_local']} | {f['flight']} | {f['origin']}-{f['dest']} | {f['source_file']} | {note} |")
    else:
        lines.append("None in this month's zip.")
    (folder / "no_code_tracks.md").write_text("\n".join(lines) + "\n")

    print(f"{folder}: {len(manifest)} tracks -> {len(flights)} flights; "
          f"tails attached {sum(1 for f in flights if f['tail'])}, triangle rows {len(trows)}")

if __name__ == "__main__":
    main()
