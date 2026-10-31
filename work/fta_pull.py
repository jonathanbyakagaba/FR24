#!/usr/bin/env python3
"""Pull the Uganda Airlines Flight Turn Around (FTA) boards into the workspace.

Source: https://fta.ugandairlines.com  (public; no sign-in needed for any of it)

What is fetched
    /utilization-plans?page=N     index of day boards, 12 rows, "Flight Date | Status | Action"
    /<uuid>                       one day board: leg table (local time) + unallocated + grounded + remarks
    /<uuid>/excel                 the same legs as .xlsx, 8 columns, UTC times, sheet named DD-MM-YYYY
    /flight-utilization-plans/<id>  one leg: Key/Value detail with DATED ETD/ETA in local time, airport names+ICAO, A/C type

Stages (each writes into work/fta/, each skips what it already has unless --force)
    index   crawl the index pages, print/collect the (date, uuid) list
    boards  per day: the HTML board and the xlsx, parsed to board/<ops-date>.json + xlsx/<ops-date>.xlsx
    legs    per day in --legs-since..: the leg detail pages (adds aircraft type, ICAO, dated ETD/ETA)
    derive  rebuild the flat CSVs from the JSON on disk
    all     index, boards, legs (if --legs-since), derive

Times, the one thing to get right
    .xlsx  STD/STA/Crew PT  = UTC, no dates, rows ordered from 00:00Z
    HTML board, leg detail  = Entebbe local (UTC+3), leg detail carries the date
    a STA <= STD in the xlsx means the arrival is next day (see the +1 rule in derive)

Only standard library + openpyxl.  Curl is used for transport so the sandbox proxy
settings are inherited.
"""
import argparse
import csv
import datetime as dt
import json
import collections
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "fta")
BASE = "https://fta.ugandairlines.com"
UA = "fr24-dataset/1.0 (+ops data pull; one request per page)"


def fetch(path, binary=False, tries=3):
    """GET BASE+path via curl. Returns text or bytes, or None on failure."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin" if binary else ".html")
    tmp.close()
    cmd = ["curl", "-sL", "-m", "90", "-A", UA, "-o", tmp.name,
           "-w", "%{http_code}", BASE + path]
    for attempt in range(tries):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            code = (r.stdout or "").strip()[-3:]
            if code == "200" and os.path.getsize(tmp.name) > 0:
                if binary:
                    return open(tmp.name, "rb").read()
                return open(tmp.name, encoding="utf-8", errors="replace").read()
            sys.stderr.write("  ! %s -> http %s (%d B), attempt %d\n"
                             % (path, code, os.path.getsize(tmp.name), attempt + 1))
        except Exception as exc:                                   # noqa: BLE001
            sys.stderr.write("  ! %s -> %s, attempt %d\n" % (path, exc, attempt + 1))
    os.unlink(tmp.name)
    return None


# ---------------------------------------------------------------- HTML helpers
def strip_tags(fragment, keep_plus=False):
    """Cell text; a <br> inside a cell is the board's way of writing '+1'."""
    if keep_plus:
        fragment = re.sub(r"<br\s*/?>", " +1 ", fragment)
    else:
        fragment = re.sub(r"<br\s*/?>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = (fragment.replace("&nbsp;", " ").replace("&amp;", "&")
                        .replace("&quot;", '"').replace("&#39;", "'")
                        .replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", fragment).strip()


def tables(html):
    """Every <table> as (headers, [row cells]) with rows of only-<td> kept."""
    out = []
    for tbl in re.findall(r"<table.*?</table>", html, re.S):
        head = [strip_tags(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tbl, re.S)]
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S):
            if "<td" not in tr:
                continue
            cells = [strip_tags(x, keep_plus=True)
                     for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if any(cells):
                rows.append(cells)
        out.append((head, rows))
    return out


# -------------------------------------------------------------------- 1. index
def stage_index(max_pages, sleep, fresh=False):
    """Return {ops_date_iso: {uuid, state, label}} walking the index pages back in time."""
    os.makedirs(OUT, exist_ok=True)
    seen, days = set(), {}
    for page in range(1, max_pages + 1):
        path = "/utilization-plans" + ("" if page == 1 else "?page=%d" % page)
        html = fetch(path)
        if html is None:
            print("index: page %d unreachable, stopping" % page)
            break
        new = 0
        for tr in re.findall(r"<tr.*?</tr>", html, re.S):
            if "View" not in tr:
                continue
            uuids = re.findall(r'href="/([0-9a-f]{8}-[0-9a-f-]{27,})"', tr)
            label = strip_tags(tr)
            if not uuids:
                continue
            m = re.search(r"(\d{1,2})(?:st|nd|rd|th)\s+([A-Z][a-z]+),?\s+(\d{4})", label)
            if not m:
                continue
            try:
                year = int(m.group(3))
                if year < 100:                              # the site writes "26" sometimes
                    year += 2000
                day = dt.datetime.strptime("%s %s %s" % (m.group(1), m.group(2), year),
                                          "%d %b %Y").date()
            except ValueError:
                continue
            if not (2000 < day.year < 2100):
                continue
            state = (re.search(r"\b(AMENDED|PUBLISHED|DRAFT)\b", label) or [None, ""])[1]
            if uuids[0] in seen:
                continue
            seen.add(uuids[0])
            new += 1
            days[day.isoformat()] = {"uuid": uuids[0], "state": state,
                                     "label": label.split("View")[0].strip(),
                                     "index_date": day.isoformat()}
        print("index page %2d: %2d rows (%2d new)  -> %s .. %s"
              % (page, len(re.findall(r"View", html or "")), new,
                 min(days) if days else "-", max(days) if days else "-"))
        if new == 0:
            print("index: page %d added nothing, stopping" % page)
            break
        if sleep:
            _sleep(sleep)
    # merge, never clobber: a short crawl must not shrink the archive map we hold
    ipath = os.path.join(OUT, "index.json")
    before = 0
    if os.path.exists(ipath) and not fresh:
        old = json.load(open(ipath))
        before = len(old)
        days = dict(old, **days)
    with open(ipath, "w") as fh:
        json.dump(days, fh, indent=1, sort_keys=True)
    print("index: %d day boards (%d already known), %s .. %s -> work/fta/index.json"
          % (len(days), before, min(days), max(days)))
    return days


# ------------------------------------------------------------------- 2. boards
def parse_board(html):
    """Day board HTML -> dict of the leg table, fleet blocks, stamp."""
    titles = [strip_tags(x) for x in re.findall(r"<h[123][^>]*>(.*?)</h[123]>", html, re.S)]
    legs, unalloc, grounded = [], [], []
    for head in tables(html):
        hdr = [h.lower() for h in head[0]]
        if "flight" in hdr and "std" in hdr:
            legs = head[1]
        elif "type" in hdr and "reason" not in hdr:
            unalloc = head[1]
        elif "reason" in hdr:
            grounded = head[1]
    stamp = {"board_date": titles[0] if titles else "",
             "board_time": titles[1] if len(titles) > 1 else "",
             "state": titles[2] if len(titles) > 2 else ""}
    if stamp["state"] not in ("AMENDED", "PUBLISHED", "DRAFT"):
        m = re.search(r">\s*(AMENDED|PUBLISHED|DRAFT)\s*<", html)
        stamp["state"] = m.group(1) if m else ""
    rem = re.search(r"Remarks(.*?)Back", strip_tags(html[html.find("Remarks"):]), re.S)
    return {"stamp": stamp, "legs_local": legs,
            "unallocated": [r[0] + (" : " + r[1] if len(r) > 1 else "") for r in unalloc],
            "grounded": [{"reg": r[0], "status": r[1] if len(r) > 1 else "",
                          "reason": r[2] if len(r) > 2 else ""} for r in grounded],
            "remarks": (rem.group(1).strip() if rem else "") or "None"}


def parse_excel(blob):
    """The board's .xlsx (bytes) -> (sheet name = DD-MM-YYYY, rows of 8 values)."""
    import openpyxl
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.write(blob)
    tmp.close()
    try:
        ws = openpyxl.load_workbook(tmp.name).active
        rows = []
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            if r[1] in (None, ""):
                continue
            rows.append([("" if v is None else str(v).strip()) for v in r[:8]])
        return ws.title, rows
    finally:
        os.unlink(tmp.name)


def stage_boards(days, sleep, force, since="", until=""):
    os.makedirs(os.path.join(OUT, "board"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "xlsx"), exist_ok=True)
    done = skipped = bad = 0
    todo = [d for d in sorted(days) if (not since or d >= since) and (not until or d <= until)]
    print("boards: %d days in window %s..%s" % (len(todo), since or "-", until or "-"))
    for ops_date in todo:
        rec = days[ops_date]
        out = os.path.join(OUT, "board", ops_date + ".json")
        if os.path.exists(out) and not force:
            skipped += 1
            continue
        uuid = rec["uuid"]
        html = fetch("/" + uuid)
        blob = fetch("/%s/excel" % uuid, binary=True)
        if html is None or blob is None:
            print("boards: %s INCOMPLETE (html=%s xlsx=%s)"
                  % (ops_date, html is not None, blob is not None))
            bad += 1
            continue
        parsed = parse_board(html)
        parsed["uuid"] = uuid
        parsed["ops_date"] = ops_date
        parsed["index_state"] = rec["state"]
        try:
            sheet, rows = parse_excel(blob)
        except Exception as exc:                                    # noqa: BLE001
            print("boards: %s xlsx unreadable (%s)" % (ops_date, exc))
            sheet, rows = "", []
            bad += 1
        parsed["excel_sheet"] = sheet
        parsed["legs_utc"] = rows
        with open(os.path.join(OUT, "xlsx", ops_date + ".xlsx"), "wb") as fh:
            fh.write(blob)
        with open(out, "w") as fh:
            json.dump(parsed, fh, indent=1)
        done += 1
        if done % 15 == 0:
            print("boards: %d/%d written, newest %s" % (done, len(todo), ops_date), flush=True)
        if sleep:
            _sleep(sleep)
    print("boards: %d written, %d already there, %d incomplete" % (done, skipped, bad))


# ---------------------------------------------------------------------- 3. legs
DETAIL_KEYS = ("Flight Number", "Routing", "Origin Airport", "Destination Airport",
               "Crew Reporting Time", "ETD", "ETA", "A/C Reg and Type", "Crew Config",
               "Flight Status")


def stage_legs(days, sleep, force, since, until=""):
    """Fetch the per-leg detail pages for days >= since (they are the only place
    with the aircraft TYPE and with DATED ETD/ETA, which pins the +1 crossings)."""
    os.makedirs(os.path.join(OUT, "legs"), exist_ok=True)
    fetched = cached = failed = 0
    window = [d for d in sorted(days) if (not since or d >= since) and (not until or d <= until)]
    for ops_date in window:
        board = os.path.join(OUT, "board", ops_date + ".json")
        if not os.path.exists(board):
            continue
        out = os.path.join(OUT, "legs", ops_date + ".json")
        if os.path.exists(out) and not force:
            cached += 1
            continue
        data = json.load(open(board))
        ids = []
        html = fetch("/" + data["uuid"])
        if html is None:
            print("legs: %s board unreachable" % ops_date)
            failed += 1
            continue
        for tr in re.findall(r"<tr[^>]*>.*?</tr>", html, re.S):
            m = re.search(r'href="(/flight-utilization-plans/\d+)"', tr)
            if m:
                ids.append(m.group(1))
        rows = []
        for link in ids:
            page = fetch(link)
            if page is None:
                failed += 1
                rows.append({"link": link, "error": "unreachable"})
                continue
            kv = {}
            for head in tables(page):
                if [h.lower() for h in head[0]] == ["key", "value"]:
                    for r in head[1]:
                        if len(r) >= 2 and not r[0].lower().startswith("this is an old"):
                            kv[r[0]] = r[1]
            # an archived leg still prints its identity and the ETD date in the heading
            hdr = re.search(r"Flight Details:\s*([^<]+)</h1>", page)
            etd = re.search(r"<h3>\s*ETD:\s*(\d{4}-\d{2}-\d{2})\s*</h3>", page)
            if hdr:
                fl, _, sec = hdr.group(1).partition(" : ")
                kv.setdefault("Flight Number", fl.strip())
                kv.setdefault("Routing", sec.strip())
            if etd:
                kv["ETD_DATE_LOCAL"] = etd.group(1)
                if not kv.get("ETD"):
                    kv["old_flight"] = "yes"
            kv["link"] = link
            kv["plan_id"] = link.rsplit("/", 1)[-1]
            rows.append(kv)
            if sleep:
                _sleep(sleep)
        with open(out, "w") as fh:
            json.dump(rows, fh, indent=1)
        fetched += 1
        print("legs: %s %d details (%d/%d)" % (ops_date, len(rows), fetched, len(window)), flush=True)
    print("legs: %d days fetched, %d cached, %d failed requests" % (fetched, cached, failed))


# -------------------------------------------------------------------- 4. derive
# -------------------------------------------------------------------- 4. derive
LOCAL_OFFSET_H = 3          # the HTML board and the leg detail pages are Entebbe local


def hm_to_min(hhmm):
    m = re.match(r"(\d{1,2}):(\d{2})", hhmm or "")
    return None if not m else int(m.group(1)) * 60 + int(m.group(2))


def parse_dated_local(text):
    """'26/09/2026 05:00' on a detail page (local) -> UTC datetime, or None."""
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}):(\d{2})", (text or "").strip())
    if not m:
        return None
    d = dt.datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)),
                    int(m.group(4)), int(m.group(5)))
    return d - dt.timedelta(hours=LOCAL_OFFSET_H)


def stage_derive(days):
    """Flat CSVs from the per-day JSON.

    Day assignment, in order of authority:
      1. the leg detail page, which prints ETD/ETA with a date (local time, +3)
      2. tail-chain rule: a row whose STD is earlier than the same tail's previous
         arrival on the board belongs to the next day (the board carries rotations
         that run past 00:00Z)
      3. otherwise STD is on the board day and STA = STD + block, the block being
         (STA - STD) mod 24h, so a next-day arrival is picked up automatically
    """
    legs, fleet, dlines, detail = [], [], [], []
    shifts = mism = checks = det_total = matched_det = header_fix = sta_guard = 0
    for ops_date in sorted(days):
        path = os.path.join(OUT, "board", ops_date + ".json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        day0 = dt.date.fromisoformat(ops_date)
        det_by_key = collections.defaultdict(list)
        dpath = os.path.join(OUT, "legs", ops_date + ".json")
        if os.path.exists(dpath):
            for r in json.load(open(dpath)):
                if not (r.get("Flight Number") or r.get("ETD_DATE_LOCAL")):
                    continue
                det_by_key[(r.get("Flight Number", ""),
                            r.get("Routing", "").replace(" +1", "").strip())].append(r)
        used_det = set()

        board_key_count = collections.Counter(
            (r[1], (r[2] or "").replace(" +1", "").strip()) for r in (d.get("legs_utc") or []))

        def pick_detail(flight, routing, tail):
            """A board can carry the same flight number and sector twice (two
            aircraft flying one schedule), so match on the tail when the detail
            page still shows it, and never guess between two live candidates."""
            cands = [i for i in range(len(det_by_key.get((flight, routing), [])))
                     if (flight, routing, i) not in used_det]
            if not cands:
                return {}, False
            for i in cands:
                reg = (det_by_key[(flight, routing)][i].get("A/C Reg and Type")
                       or "").split(" : ")[0].strip()
                if reg and reg == tail:
                    used_det.add((flight, routing, i))
                    return det_by_key[(flight, routing)][i], True
            if len(cands) == 1 and board_key_count.get((flight, routing), 0) <= 1:
                used_det.add((flight, routing, cands[0]))
                return det_by_key[(flight, routing)][cands[0]], True
            return cands and det_by_key[(flight, routing)][cands[0]] or {}, False
        # The sheet has no dates and its rows run in clock order with one wrap:
        # everything above the wrap (a drop in clock time) is the day before the board.
        clock = [hm_to_min((r + [""] * 8)[5]) for r in (d.get("legs_utc") or [])]
        wrap = 0
        for i in range(1, len(clock)):
            if None not in (clock[i], clock[i - 1]) and clock[i] < clock[i - 1]:
                wrap = i
                break
        det_total += sum(len(v) for v in det_by_key.values())
        floor = {}
        for i, row in enumerate(d.get("legs_utc") or [], 1):
            row = (row + [""] * 8)[:8]
            tail, flight, routing, status, cpt, std, sta, cfg = row
            routing = routing.replace(" +1", "").strip()
            o, _, dst = routing.partition("-")
            mstd, msta = hm_to_min(std), hm_to_min(sta)
            block = (msta - mstd) % 1440 if None not in (mstd, msta) else None
            base = dt.datetime.combine(day0, dt.time()) - (dt.timedelta(days=1) if i - 1 < wrap else dt.timedelta())
            std_dt = base + dt.timedelta(minutes=mstd) if mstd is not None else None
            sta_dt = std_dt + dt.timedelta(minutes=block) if std_dt is not None and block is not None else None
            source = "wrap" if std_dt else "no-time"
            if std_dt and tail and tail in floor and std_dt < floor[tail]:
                shifted = std_dt + dt.timedelta(days=1)
                if (shifted - floor[tail]).total_seconds() <= 12 * 3600:
                    # a rotation that carries on past 00:00Z: the next day, and a
                    # ground time a real crew could have. A bigger gap than that is the
                    # board's own overlap (plan optimistic), not a missing day.
                    std_dt = shifted
                    if sta_dt:
                        sta_dt += dt.timedelta(days=1)
                    source = "wrap+tail-chain"
                    shifts += 1
            extra, sure = pick_detail(flight, routing, tail)
            if extra:
                matched_det += 1
            det_std, det_sta = parse_dated_local(extra.get("ETD")), parse_dated_local(extra.get("ETA"))
            if extra.get("ETD_DATE_LOCAL") and std_dt and sure:      # archived leg: local date only
                want = dt.datetime.strptime(extra["ETD_DATE_LOCAL"], "%Y-%m-%d")
                while (std_dt + dt.timedelta(hours=LOCAL_OFFSET_H)).date() != want.date():
                    std_dt += dt.timedelta(days=1)
                    if sta_dt:
                        sta_dt += dt.timedelta(days=1)
                    if (std_dt + dt.timedelta(hours=LOCAL_OFFSET_H)).date() - want.date() > dt.timedelta(days=1):
                        break                                # never found it, leave as derived
                    header_fix += 1
                source = "header-date" if std_dt and (std_dt + dt.timedelta(hours=3)).date() == want.date() else source
            if det_std and std_dt and sure:
                checks += 1
                if abs((det_std - std_dt).total_seconds()) > 90:
                    mism += 1
            # The detail pages are hand-edited when a leg is delayed and the typing is
            # not always right (several legs in Oct 2026 carry an ETA whose MONTH is a
            # month out), so the dated ETD/ETA are only used where they agree with the
            # board's own clock times and block.
            if det_std and sure and std_dt and abs((det_std - std_dt).total_seconds()) <= 12 * 3600:
                std_dt = det_std
                ok_sta = (det_sta is not None and (block is None
                           or abs(int((det_sta - det_std).total_seconds() // 60) - block) <= 360))
                if ok_sta and det_sta is not None:
                    sta_dt = det_sta if det_sta >= det_std else det_sta + dt.timedelta(days=1)
                    if block is None:
                        block = int((sta_dt - std_dt).total_seconds() // 60)
                    source = "leg-detail"
                else:
                    sta_dt = std_dt + dt.timedelta(minutes=block) if block is not None else None
                    source = "leg-detail(ETA date rejected)" if det_sta else "leg-detail(no ETA)"
                    sta_guard += 1
            elif det_std and sure:
                source = source + " (ETD date rejected)"
                sta_guard += 1
            if std_dt and tail:
                floor[tail] = sta_dt or std_dt
            legs.append({
                "ops_date": ops_date, "seq": i, "uuid": d.get("uuid", ""),
                "tail": tail, "flight": flight, "sector": routing,
                "origin": o, "dest": dst, "status": status,
                "crew_pt_utc": cpt, "std_utc": std, "sta_utc": sta,
                "std_iso": std_dt.strftime("%Y-%m-%d %H:%M") + "Z" if std_dt else "",
                "sta_iso": sta_dt.strftime("%Y-%m-%d %H:%M") + "Z" if sta_dt else "",
                "block_min": "" if block is None else block, "crew_config": cfg,
                "board_state": d["stamp"].get("state", ""), "date_source": source,
            })
            if extra:
                regtype = extra.get("A/C Reg and Type", "")
                detail.append({"ops_date": ops_date, "plan_id": extra.get("plan_id", ""),
                               "flight": flight, "routing": routing,
                               "origin_full": extra.get("Origin Airport", ""),
                               "dest_full": extra.get("Destination Airport", ""),
                               "origin_icao": (re.findall(r"\((\w{4})/(\w{4})\)", extra.get("Origin Airport", "")) or [("", "")])[0][1],
                               "dest_icao": (re.findall(r"\((\w{4})/(\w{4})\)", extra.get("Destination Airport", "")) or [("", "")])[0][1],
                               "crew_report_local": extra.get("Crew Reporting Time", ""),
                               "etd_local": extra.get("ETD", ""), "eta_local": extra.get("ETA", ""),
                               "reg_type": regtype,
                               "type": regtype.split(":")[-1].strip() if ":" in regtype else "",
                               "crew_config": extra.get("Crew Config", ""),
                               "status_detail": extra.get("Flight Status", "")})
        for r in d.get("unallocated") or []:
            head, _, rest = r.partition(" : ")
            if not re.fullmatch(r"[A-Z0-9]{2}-[A-Z0-9]{2,4}", (head or "").strip()) and head.strip() != "TBN":
                continue
            fleet.append({"ops_date": ops_date, "kind": "unallocated", "reg": head.strip(),
                          "status": "", "reason": rest.strip().replace("AIR_CRAFT : ", "").strip()})
        for g in d.get("grounded") or []:
            if not re.fullmatch(r"[A-Z0-9]{2}-[A-Z0-9]{2,4}", (g["reg"] or "").strip()):
                continue                      # "No grounded aircrafts" and other empty-state text
            fleet.append({"ops_date": ops_date, "kind": "grounded", "reg": g["reg"].strip(),
                          "status": g["status"], "reason": g["reason"]})
        flown = sorted({x["tail"] for x in legs if x["ops_date"] == ops_date and x["tail"]})
        dlines.append({"ops_date": ops_date, "uuid": d.get("uuid", ""),
                       "board_date_label": d["stamp"].get("board_date", ""),
                       "board_stamp_local": d["stamp"].get("board_time", ""),
                       "state": d["stamp"].get("state", ""),
                       "index_state": d.get("index_state", ""),
                       "excel_sheet": d.get("excel_sheet", ""),
                       "legs": len(d.get("legs_utc") or []), "tails": len(flown),
                       "tails_list": " ".join(flown),
                       "grounded": len(d.get("grounded") or []),
                       "unallocated": len(d.get("unallocated") or []),
                       "remarks": (d.get("remarks") or "None")[:600]})
    if checks:
        print("derive: wrap-rule STD checked against %d leg-detail dates, %d disagreed >90 min"
              % (checks, mism))
    print("derive: %d of %d leg-detail pages matched a board row" % (matched_det, det_total))
    print("derive: %d rows needed the tail-chain correction on top of the wrap rule; "
          "%d day assignments taken from an archived leg page; %d detail dates rejected "
          "as inconsistent with the board" % (shifts, header_fix, sta_guard))
    # tail -> aircraft type, from whatever leg-detail pages we have
    types, seen = {}, collections.defaultdict(lambda: [None, None, 0])
    for r in detail:
        reg = (r["reg_type"] or " : ").split(" : ")[0].strip()
        if reg and r["type"]:
            types.setdefault(reg, collections.Counter())[r["type"]] += 1
    for l in legs:
        if not l["tail"]:
            continue
        rec = seen[l["tail"]]
        d = l["std_iso"][:10] or l["ops_date"]
        rec[0] = min(rec[0], d) if rec[0] else d
        rec[1] = max(rec[1], d) if rec[1] else d
        rec[2] += 1
    tails = [{"tail": t, "type": (", ".join("%s x%d" % (a, b) for a, b in types[t].most_common())
                                 if t in types else ""),
              "legs_planned": v[2], "first_board": v[0], "last_board": v[1]}
             for t, v in sorted(seen.items(), key=lambda kv: -kv[1][2])]
    for name, rows in (("fta_legs.csv", legs), ("fta_days.csv", dlines),
                       ("fta_fleet.csv", fleet), ("fta_leg_detail.csv", detail),
                       ("fta_tails.csv", tails)):
        path = os.path.join(OUT, name)
        if not rows:
            print("derive: %s has no rows yet, not written" % name)
            continue
        with open(path, "w", newline="") as fh:
            w_ = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w_.writeheader()
            w_.writerows(rows)
        print("derive: %-18s %5d rows" % (name, len(rows)))


def _sleep(s):
    import time
    time.sleep(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["index", "boards", "legs", "derive", "all"])
    ap.add_argument("--max-pages", type=int, default=15)
    ap.add_argument("--sleep", type=float, default=0.15, help="seconds between requests")
    ap.add_argument("--force", action="store_true", help="refetch what is already on disk")
    ap.add_argument("--legs-since", default="", help="YYYY-MM-DD, first day to pull leg details for")
    ap.add_argument("--from", dest="since", default="", help="YYYY-MM-DD, first day to pull boards for")
    ap.add_argument("--to", dest="until", default="", help="YYYY-MM-DD, last day to pull (boards and legs)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    ipath = os.path.join(OUT, "index.json")
    if a.stage in ("index", "all"):
        # the window applies to what gets FETCHED, never to what gets derived -
        # a filtered index would rebuild the CSVs from two days and drop the rest
        days = stage_index(a.max_pages, a.sleep, fresh=False)
    else:
        days = json.load(open(ipath))
    if a.stage in ("boards", "all"):
        stage_boards(days, a.sleep, a.force, a.since, a.until)
    if a.stage == "legs" or (a.stage == "all" and a.legs_since):
        stage_legs(days, a.sleep, a.force, a.legs_since or a.since, a.until)
    stage_derive(days)


if __name__ == "__main__":
    main()
