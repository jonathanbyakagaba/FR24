#!/usr/bin/env python3
"""
Build flight_conditions.csv for a month folder from the rebuilt flights.csv,
runway_usage.csv and the IEM ASOS METAR extracts in <folder>/metar/.

    python3 work/build_conditions.py "UR SEPTEMBER 2026"
    python3 work/build_conditions.py "UR OCTOBER 2026"

METAR source: Iowa State IEM ASOS, station HUEN (Entebbe), routine reports
(report_type=3), parsed fields drct/sknt/gust/vsby/tmpc/alti/wxcodes, UTC.
Archive files metar/HUEN_*_part*.csv are concatenated in name order before
parsing (the download arrives in chunks that can split a line; malformed
fragments are skipped - a handful of reports at chunk seams may be lost).

Scope: METAR was retrieved for HUEN only. Every flight with an Entebbe end
gets real conditions at that end (departure side if origin=EBB, arrival side
if dest=EBB); the other end is left blank. Outstation METARs can be added by
dropping IEM extracts for HKJK/HTDA/HTZA/HTKJ/HJJJ/HCMM/HBBA/HKMO/FLLS/FVHA/
FAOR/VABB/EGKK/DNMM into metar/ and re-running - the code picks up any
station file present. This replaces the frozen build's conditions, which
used its own (lost) metar/ archive; coverage differs accordingly.

Wind components use the runway heading implied by dep_rwy/arr_rwy from
runway_usage.csv (legacy schema headings: EBB 17=172, 35=352, etc.).
headwind = kt*cos(wind_from - runway_hdg); crosswind = kt*sin(...).
'favours' = headwind >= -2 kt (i.e. no meaningful tailwind), blank if calm/no rwy.
dep_metar/arr_metar hold the IEM valid time of the report used (nearest
within +/-60 min), since raw METAR strings were not archived in this pass.
"""
import csv, glob, math, re, sys
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path

RWY_HDG = {"17": 172, "35": 352, "06": 61, "24": 241, "05": 46, "23": 226,
           "18": 183, "36": 3, "09": 92, "27": 272, "13": 126, "31": 306,
           "03": 33, "21": 213, "10": 104, "28": 284, "08": 84, "26": 264,
           "14": 140, "32": 320}
ICAO_OF = {"EBB": "HUEN", "NBO": "HKJK", "DAR": "HTDA", "ZNZ": "HTZA", "JRO": "HTKJ",
           "JUB": "HJJJ", "MGQ": "HCMM", "BJM": "HBBA", "MBA": "HKMO", "LUN": "FLLS",
           "HRE": "FVHA", "JNB": "FAOR", "BOM": "VABB", "LGW": "EGKK", "LOS": "DNMM",
           "KGL": "HRYR"}

def load_metar(folder):
    series = {}
    for path in sorted(glob.glob(str(folder / "metar" / "*_part*.csv")) + glob.glob(str(folder / "metar" / "HUEN_*.csv"))):
        text = Path(path).read_text()
        for line in text.splitlines():
            if line.startswith(",202"):
                line = "HUEN" + line
            m = re.match(r"([A-Z]{4}),(\d{4}-\d{2}-\d{2} \d{2}:\d{2}),([\d.]*),([\d.]*),([\d.]*),([\d.]*),([-\d.]*),([\d.]*),(.*)$", line)
            if not m:
                continue
            stn, valid, drct, sknt, gust, vsby, tmpc, alti, wx = m.groups()
            try:
                t = datetime.strptime(valid, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                series.setdefault(stn, []).append((t, dict(
                    valid=valid, drct=float(drct) if drct else "", sknt=float(sknt) if sknt else "",
                    gust=float(gust) if gust else "", vsby=float(vsby) if vsby else "",
                    tmpc=float(tmpc) if tmpc else "", alti=float(alti) if alti else "", wx=wx.strip())))
            except ValueError:
                continue
    for stn in series:
        series[stn].sort()
    return series

def nearest(series, stn, t, tol_min=75):
    if stn not in series:
        return None
    rows = series[stn]
    times = [r[0] for r in rows]
    i = bisect_left(times, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(rows):
            d = abs((rows[j][0] - t).total_seconds()) / 60.0
            if d <= tol_min and (best is None or d < best[0]):
                best = (d, rows[j][1])
    return best[1] if best else None

def components(rep, rwy):
    if not rep or rep["drct"] == "" or rep["sknt"] == "" or rwy not in RWY_HDG:
        return "", "", ""
    rel = math.radians(rep["drct"] - RWY_HDG[rwy])
    hw = round(rep["sknt"] * math.cos(rel), 1)
    xw = round(abs(rep["sknt"] * math.sin(rel)), 1)
    return hw, xw, ("yes" if hw >= -2 else "no")

def main():
    folder = Path(sys.argv[1])
    series = load_metar(folder)
    rwy = {r["file"]: r for r in csv.DictReader(open(folder / "runway_usage.csv"))}
    flights = list(csv.DictReader(open(folder / "flights.csv")))
    out, cov = [], [0, 0]
    for f in flights:
        ru = rwy.get(f["source_file"], {})
        dep_t = datetime.strptime(f["departure_utc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
        arr_t = datetime.strptime(f["arrival_utc"], "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
        row = dict(file=f["source_file"], flight=f["flight"], date_local=f["date_local"],
                   origin=f["origin"], dest=f["dest"],
                   dep_rwy=ru.get("dep_rwy", ""), dep_rwy_hdg=RWY_HDG.get(ru.get("dep_rwy", ""), ""),
                   arr_rwy=ru.get("arr_rwy", ""), arr_rwy_hdg=RWY_HDG.get(ru.get("arr_rwy", ""), ""))
        for side, apt, t, rwykey in (("dep", f["origin"], dep_t, "dep_rwy"), ("arr", f["dest"], arr_t, "arr_rwy")):
            rep = nearest(series, ICAO_OF.get(apt, ""), t)
            if apt == "EBB":
                cov[side == "arr"] += 1 if rep else 0
            hw, xw, fav = components(rep, ru.get(rwykey, ""))
            row[f"{side}_metar"] = rep["valid"] + "Z" if rep else ""
            row[f"{side}_wind_from"] = int(rep["drct"]) if rep and rep["drct"] != "" else ""
            row[f"{side}_wind_kt"] = int(rep["sknt"]) if rep and rep["sknt"] != "" else ""
            row[f"{side}_gust_kt"] = int(rep["gust"]) if rep and rep["gust"] != "" else ""
            row[f"{side}_vis_sm"] = rep["vsby"] if rep else ""
            row[f"{side}_wx"] = rep["wx"] if rep else ""
            row[f"{side}_temp_c"] = int(rep["tmpc"]) if rep and rep["tmpc"] != "" else ""
            row[f"{side}_headwind_kt"] = hw
            row[f"{side}_crosswind_kt"] = xw
            row[f"{side}_wind_favours"] = fav
            if side == "dep":
                row["dep_qnh_inhg"] = rep["alti"] if rep else ""
        out.append(row)
    cols = ["file","flight","date_local","origin","dest","dep_rwy","dep_rwy_hdg","arr_rwy","arr_rwy_hdg",
            "dep_metar","dep_wind_from","dep_wind_kt","dep_gust_kt","dep_vis_sm","dep_wx","dep_temp_c",
            "dep_headwind_kt","dep_crosswind_kt","dep_wind_favours","arr_metar","arr_wind_from","arr_wind_kt",
            "arr_gust_kt","arr_vis_sm","arr_wx","arr_temp_c","arr_headwind_kt","arr_crosswind_kt",
            "arr_wind_favours","dep_qnh_inhg"]
    with open(folder / "flight_conditions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(out)
    print(f"{folder}: {len(out)} condition rows; EBB-end reports found dep {cov[0]}, arr {cov[1]}")

if __name__ == "__main__":
    main()
