#!/usr/bin/env python3
"""
October 2026 origin-destination matrices, one per day, from the rebuilt
flight log (UR OCTOBER 2026/flights.csv). Also runs the diversion check:
every flight's actual O&D is compared with the sector set its flight
number operates in the FTA plans (work/fta_sep2026.csv +
work/fta_oct2026.csv); sectors outside that set, and suffixed callsigns
(UGD...D / UGD...X), are reported.

Outputs (in UR OCTOBER 2026/):
  od_matrix_october2026.pdf   readable report (matrices + diversion findings)
  od_matrix_october2026.xlsx  workbook: READ_ME, tidy, TOTAL, one sheet/day,
                              DIVERSION_CHECK
  od_matrix_october2026.csv   tidy export: date, origin, dest, flights

One flights.csv row = one flown sector. Day = origin-local departure
date (the log's date_local). October coverage is 1-16 Oct.
"""
import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from rebuild_month import AIRPORTS  # noqa: E402

FOLDER = Path("UR OCTOBER 2026")
MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}

flights = list(csv.DictReader(open(FOLDER / "flights.csv")))

def iso(date_local):
    return f"20{date_local[5:]}-{MONTHS[date_local[2:5]]:02d}-{date_local[:2]}"

for f in flights:
    f["date"] = iso(f["date_local"])

days = [f"2026-10-{d:02d}" for d in range(1, 17)]  # FTA/track coverage window
airports = sorted({f["origin"] for f in flights} | {f["dest"] for f in flights},
                  key=lambda a: (a != "EBB", a))

od = defaultdict(Counter)          # date -> (o,d) -> n
for f in flights:
    od[f["date"]][(f["origin"], f["dest"])] += 1
total = Counter()
for c in od.values():
    total.update(c)

# ---------------- diversion / suffix check ------------------------------------
sector_set = defaultdict(set)
for fn in ("work/fta_sep2026.csv", "work/fta_oct2026.csv"):
    for r in csv.DictReader(open(fn)):
        if r["flight"] != "NONSKED" and r["status"] != "NON_SCHEDULED":
            sector_set[r["flight"]].add((r["origin"], r["dest"]))

def base_no(cs):
    b = "UR" + cs[3:] if cs.startswith("UGD") else "UR" + cs[2:] if cs.startswith("UG") else cs
    return b[:-1] if b[-1:].isalpha() else b

anomalies, suffixed = [], []
for f in flights:
    b = base_no(f["flight"])
    suffix = f["flight"][len("UGD") + len(b) - 2:] if f["flight"].startswith("UGD") else ""
    is_suf = bool(suffix) and suffix.isalpha()
    off_plan = b in sector_set and (f["origin"], f["dest"]) not in sector_set[b]
    if is_suf:
        suffixed.append(f)
    if off_plan or is_suf:
        anomalies.append((f, b, is_suf, off_plan))

# ---------------- CSV (tidy) ----------------------------------------------------
with open(FOLDER / "od_matrix_october2026.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["date", "origin", "dest", "flights"])
    for d in days:
        for (o, dd), n in sorted(od[d].items()):
            w.writerow([d, o, dd, n])

# ---------------- XLSX -----------------------------------------------------------
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
hdr = Font(bold=True, color="FFFFFF")
fill = PatternFill("solid", fgColor="305496")
ctr = Alignment(horizontal="center")

def matrix_sheet(ws, counts, title):
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=13)
    ws.cell(row=3, column=1, value="from \\ to").font = hdr
    ws.cell(row=3, column=1).fill = fill
    for j, a in enumerate(airports, 2):
        c = ws.cell(row=3, column=j, value=a); c.font = hdr; c.fill = fill; c.alignment = ctr
    c = ws.cell(row=3, column=len(airports) + 2, value="TOTAL OUT"); c.font = hdr; c.fill = fill
    for i, o in enumerate(airports, 4):
        c = ws.cell(row=i, column=1, value=o); c.font = hdr; c.fill = fill
        row_tot = 0
        for j, d in enumerate(airports, 2):
            n = counts.get((o, d), 0)
            row_tot += n
            if n:
                cc = ws.cell(row=i, column=j, value=n); cc.alignment = ctr
        ws.cell(row=i, column=len(airports) + 2, value=row_tot).font = Font(bold=True)
    r = len(airports) + 4
    ws.cell(row=r, column=1, value="TOTAL IN").font = Font(bold=True)
    for j, d in enumerate(airports, 2):
        ws.cell(row=r, column=j,
                value=sum(counts.get((o, d), 0) for o in airports)).font = Font(bold=True)
    ws.cell(row=r, column=len(airports) + 2,
            value=sum(counts.values())).font = Font(bold=True)
    ws.column_dimensions["A"].width = 11
    for j in range(2, len(airports) + 3):
        ws.column_dimensions[chr(64 + j) if j <= 26 else "A" + chr(64 + j - 26)].width = 6

ws = wb.active
ws.title = "READ_ME"
notes = [
    "October 2026 origin-destination matrices — Uganda Airlines (UR), from the rebuilt flight log.",
    "",
    "One row of the source log = one flown sector; a day is the origin-local departure date.",
    "Coverage 1-16 Oct 2026 (track export window).",
    "Sheets: TOTAL (whole period), one sheet per day, tidy (long format for analysis),",
    "DIVERSION_CHECK (suffixed callsigns and sectors the flight number never operates).",
    "Generated by work/build_od_matrix_october.py from UR OCTOBER 2026/flights.csv.",
]
for i, t in enumerate(notes, 1):
    ws.cell(row=i, column=1, value=t)
ws.column_dimensions["A"].width = 110

ws = wb.create_sheet("tidy")
ws.append(["date", "origin", "dest", "flights"])
for c in ws[1]:
    c.font = hdr; c.fill = fill
for d in days:
    for (o, dd), n in sorted(od[d].items()):
        ws.append([d, o, dd, n])

matrix_sheet(wb.create_sheet("TOTAL"), total, "October 2026 (1-16 Oct) — all sectors")
for d in days:
    cnt = od[d]
    matrix_sheet(wb.create_sheet(d), cnt,
                 f"{d} — {sum(cnt.values())} sectors" + (" (no recorded departures)" if not cnt else ""))

ws = wb.create_sheet("DIVERSION_CHECK")
ws.append(["date", "callsign", "operated", "flight-number's planned sectors",
           "takeoff_local", "air_min", "source_file", "note"])
for c in ws[1]:
    c.font = hdr; c.fill = fill
for f, b, is_suf, off_plan in anomalies:
    note = []
    if is_suf:
        note.append("suffixed callsign")
    if off_plan:
        note.append("sector never planned for this flight number (diversion/off-plan)")
    ws.append([f["date"], f["flight"], f"{f['origin']}->{f['dest']}",
               ", ".join(f"{o}-{d}" for o, d in sorted(sector_set[b])),
               f["takeoff_local"], f["air_minutes"], f["source_file"], "; ".join(note)])
wb.save(FOLDER / "od_matrix_october2026.xlsx")

# ---------------- PDF --------------------------------------------------------------
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()
doc = SimpleDocTemplate(str(FOLDER / "od_matrix_october2026.pdf"),
                        pagesize=landscape(A4),
                        leftMargin=14 * mm, rightMargin=14 * mm,
                        topMargin=12 * mm, bottomMargin=12 * mm,
                        title="October 2026 OD matrices — Uganda Airlines",
                        author="FR24 rebuild (work/build_od_matrix_october.py)")
story = []
story.append(Paragraph("October 2026 — Origin–Destination matrices by day", styles["Title"]))
story.append(Paragraph(
    "Uganda Airlines (UR) sectors actually flown, from the rebuilt track log "
    f"(<i>UR OCTOBER 2026/flights.csv</i>, {len(flights)} sectors, 1–16 Oct 2026). "
    "Each matrix counts sectors departing that day (origin-local date): read across a row for "
    "where flights from that airport went; down a column for where arrivals came from. "
    "One row of the log is one sector, so a Harare–Lusaka–Entebbe triangle contributes to "
    "three cells on three (or fewer) days. The same data is in <i>od_matrix_october2026.xlsx</i> "
    "(one sheet per day plus TOTAL and a tidy long-format sheet) and "
    "<i>od_matrix_october2026.csv</i> for analysis.", styles["BodyText"]))
story.append(Spacer(1, 6))

story.append(Paragraph("First, your diversion question — checked against the map", styles["Heading2"]))
story.append(Paragraph(
    "Yes: comparing each flight's operated origin–destination with every sector its flight "
    "number is planned to fly (FTA plans, both months) finds exactly the pattern you described. "
    "The diversion leg itself usually keeps the <b>normal</b> callsign and simply lands at "
    "Nairobi instead of Entebbe; the <b>suffixed</b> flight is then the recovery leg out of "
    "Nairobi. All three October diversions went to NBO:", styles["BodyText"]))
div_rows = [["date", "what operated", "what was planned", "reading"],
            ["2026-10-11", "UR323 Dar es Salaam → <b>Nairobi</b> (151 min), then <b>UGD323D</b> Nairobi → Entebbe 05:18",
             "UR323 Dar es Salaam → Entebbe", "diverted to NBO; D-suffix continuation next morning — the 11 Oct FTA plan was itself amended to add a UR323 NBO→EBB 05:00 leg, so ops recorded the recovery"],
            ["2026-10-13", "UR121 Juba → <b>Nairobi</b> (111 min), then <b>UGD121D</b> Nairobi → Entebbe 20:30",
             "UR121 Juba → Entebbe", "diverted to NBO; D-suffix continuation same evening"],
            ["2026-10-05", "<b>UGD207D</b> Nairobi → Entebbe 23:32", "UR207 Nairobi → Entebbe (evening)",
             "route is the planned one; the D here marks a heavily delayed return (no separate UR207 that day)"],
            ["2026-09-29*", "UR720 Harare → <b>Nairobi</b> (206 min), then <b>UGD720X</b> Nairobi → Entebbe",
             "UR720 Harare → Entebbe", "same pattern in September (*shown for context; not in the October matrices)"]]
t = Table(div_rows, colWidths=[24 * mm, 82 * mm, 52 * mm, 82 * mm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#305496")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))
story.append(t)
story.append(Paragraph(
    "So the suffix alone isn't the tell — the tell is a sector the flight number never "
    "operates (DAR→NBO, JUB→NBO, HRE→NBO above). Of October's 335 sectors, exactly two "
    "operated off-plan, and both are the NBO diversions; both were recovered by a D-suffix "
    "leg. (The third D flight, UGD207D, is a delay, not a diversion.) The DIVERSION_CHECK "
    "sheet of the workbook reproduces this audit.", styles["BodyText"]))
story.append(PageBreak())

def pdf_matrix(title, counts):
    head = ["from \\ to"] + airports + ["OUT"]
    data = [head]
    for o in airports:
        row = [o] + [(str(counts[(o, d)]) if counts.get((o, d)) else "·") for d in airports]
        row.append(str(sum(counts.get((o, d), 0) for d in airports)))
        data.append(row)
    data.append(["IN"] + [str(sum(counts.get((o, d), 0) for o in airports)) for d in airports]
                + [str(sum(counts.values()))])
    tt = Table(data, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#305496")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#D9E2F3")),
        ("BACKGROUND", (-1, 1), (-1, -1), colors.HexColor("#FFF2CC")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FFF2CC")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]
    for i, o in enumerate(airports, 1):
        for j, d in enumerate(airports, 1):
            if o == d and counts.get((o, d)):
                style.append(("BACKGROUND", (j, i), (j, i), colors.HexColor("#FCE4E4")))
    tt.setStyle(TableStyle(style))
    return [Paragraph(title, styles["Heading2"]), tt, Spacer(1, 4)]

story += pdf_matrix("Whole period — 1–16 Oct 2026 (335 sectors)", total)
story.append(Paragraph(
    "Entebbe is the hub: 161 departures and 158 arrivals of the 335 sectors (the small "
    "imbalance is sectors still airborne or begun outside the window). Off-diagonal "
    "cells away from the EBB row/column are the fifth-freedom triangle sectors "
    "(ZNZ–JRO, HRE–LUN, LUN–HRE) — and the two diversion cells DAR→NBO and JUB→NBO. "
    "Airport codes: EBB Entebbe, NBO Nairobi, DAR Dar es Salaam, ZNZ Zanzibar, "
    "JRO Kilimanjaro, JUB Juba, MGQ Mogadishu, BJM Bujumbura, MBA Mombasa, LUN Lusaka, "
    "HRE Harare, JNB Johannesburg, BOM Mumbai, LGW London Gatwick, LOS Lagos.", styles["BodyText"]))
story.append(PageBreak())

for d in days:
    cnt = od[d]
    dt = date.fromisoformat(d)
    title = f"{d} ({dt.strftime('%A')}) — {sum(cnt.values())} sectors"
    if not cnt:
        title += " — no recorded departures"
    story += pdf_matrix(title, cnt)
    if not cnt:
        story.append(Paragraph(
            "No sectors in the rebuilt log carry this origin-local departure date.",
            styles["BodyText"]))
    story.append(Spacer(1, 6))

doc.build(story)
print(f"days {len(days)}, sectors {len(flights)}, anomalies {len(anomalies)}, suffixed {len(suffixed)}")
print("wrote od_matrix_october2026.pdf/.xlsx/.csv")
