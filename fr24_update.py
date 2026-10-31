#!/usr/bin/env python3
"""
fr24_update.py — fold a new arrival into the published set, in one command.

Designed for a daily cadence: you drop the updated `FR data.zip` into the repo,
run this, and it produces the whole publishable set with every count recomputed.

    python3 fr24_update.py                 # fetch the repo zip, rebuild everything
    python3 fr24_update.py --zip new.zip   # use a local zip instead
    python3 fr24_update.py --check         # report what would change, write nothing

What it does, in order:

  1. fetches `FR data.zip` from the repository (or takes a local file)
  2. cleans the archive — flattens folders, removes duplicate and row-identical
     copies, drops partial downloads, restores any fuller version that a previous
     build already had, renames to `<FLIGHT>-<8 hex>.csv`, normalises to LF
  3. rebuilds  FR data.zip, manifest.csv, all_flights_aeroroutes.md, flights.csv
  4. regenerates README.md with every figure recomputed from the data
  5. prints what changed since the last build

Nothing is ever guessed: every number in the README comes from the files it ships.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "work"))
import repo_layout as RL  # noqa: E402
import build_log as BL  # noqa: E402  (shares the log logic and the airport table)

# FR24_PUBLISH / FR24_STATE let a rehearsal run against a scratch tree — the same override
# every script under work/ already honours, so a build and its close can be pointed at one
# place together without touching the real publish dir
OUT = os.environ.get("FR24_PUBLISH") or os.path.join(HERE, "fr24_publish")
WORK = os.path.join(HERE, "work")
STATE = os.environ.get("FR24_STATE") or os.path.join(HERE, "fr24_state.json")
REPO = "jonathanbyakagaba/FR24"
ZIP_NAME = "FR data.zip"

CANON = re.compile(r"^([A-Z]{2}\d+[A-Z]?)-([0-9a-f]{8})\.csv$", re.I)
HEXNAME = re.compile(r"^[0-9a-f]{8}\.csv$", re.I)
OBSERVED_GAP_S = BL.OBSERVED_GAP_S
AIRBORNE_FT = BL.AIRBORNE_FT


# ----------------------------------------------------------------- utilities

def human(n: float) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024 or u == "GB":
            return f"{n:,.0f} {u}" if u == "B" else f"{n:,.1f} {u}"
        n /= 1024
    return f"{n:.1f} GB"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


csv.field_size_limit(1 << 24)          # a single field may be up to 16 MB before the
                                       # parser refuses; beats crashing on a stray file


def is_track(name: str, raw: bytes) -> bool:
    """True for the FR24 track exports, false for anything else that lands in the zip.

    The export header is `Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction`; a
    saved web page, a screenshot or a stray document must never reach the archive."""
    if not name.lower().endswith('.csv'):
        return False
    head = raw[:400].decode('utf-8-sig', errors='replace')
    return 'Timestamp' in head and 'Position' in head


def rows_of(raw: bytes) -> list[list[str]]:
    txt = raw.decode("utf-8-sig", errors="replace")
    return [r for r in list(csv.reader(io.StringIO(txt)))[1:] if r and r[0]]


def _sig_row(r: list[str]) -> tuple:
    """A row compared by meaning, not by spelling.

    Two copies of one track can differ in the last digit of a coordinate and nowhere
    else - FR24 writes 32.6953125 as 32.695313, a re-emitted copy rounds it to
    32.695312 - and byte-exact comparison then publishes the same flight twice, which
    doubles its fixes in the manifest and its day in any per-day count. So coordinates
    are quantised to 1e-4 degrees (~11 m, far finer than the 47 m the archive resolves)
    and plain integers are normalised before a row is ever compared.
    """
    out = []
    for i, v in enumerate(r):
        v = (v or '').strip()
        if i == 3:
            parts = v.split(',')
            if len(parts) == 2:
                try:
                    v = f'{float(parts[0]):.4f},{float(parts[1]):.4f}'
                except ValueError:
                    pass
        elif v.lstrip('-').isdigit():
            v = str(int(v))
        out.append(v)
    return tuple(out)


def rowset(raw: bytes) -> frozenset:
    return frozenset(_sig_row(r) for r in rows_of(raw))


def fixes(raw: bytes) -> int:
    n = 0
    for r in rows_of(raw):
        try:
            float(r[0])
            n += 1
        except (ValueError, IndexError):
            pass
    return n


def span(raw: bytes):
    ts = []
    for r in rows_of(raw):
        try:
            ts.append(float(r[0]))
        except (ValueError, IndexError):
            pass
    return (min(ts), max(ts)) if ts else (None, None)


def callsigns(raw: bytes) -> set:
    out = set()
    for r in rows_of(raw):
        if len(r) > 2 and r[2].strip():
            out.add(r[2].strip())
    return out


def name_penalty(entry_name: str) -> int:
    """Lower is better: prefer top-level, canonical, unsuffixed names."""
    base = entry_name.split("/")[-1]
    p = 0
    if "/" in entry_name:
        p += 10 + entry_name.count("/")
    if "CSVs for upload" in entry_name:
        p += 10
    if "(" in base or ")" in base:
        p += 5
    if re.search(r"[-_]\d+\.csv$", base):
        p += 3
    return p


def canonical_name(raw_name: str, used: set) -> str:
    base = raw_name.split("/")[-1]
    m = CANON.match(base)
    if m:
        name = f"{m.group(1).upper()}-{m.group(2).lower()}.csv"
    elif HEXNAME.match(base):
        name = base.lower()          # no flight number to invent
    else:
        name = re.sub(r"\s*\(\d+\)", "", base)
        name = re.sub(r"[-_](\d+)\.csv$", r".csv", name)
    stem, ext = os.path.splitext(name)
    n = 1
    while name.lower() in used:
        name = f"{stem}-{n}{ext}"
        n += 1
    used.add(name.lower())
    return name


# ----------------------------------------------------------------- 1. fetch

def fetch_zip(local: str | None) -> tuple[str, str]:
    if local:
        # read the caller's file in place: nothing downstream writes to it, and the
        # copy used to sit in work/incoming.zip (6.8 MB) after every run, --check included
        return os.path.abspath(local), os.path.abspath(local)
    os.makedirs(WORK, exist_ok=True)
    dest = os.path.join(WORK, "incoming.zip")
    # Read the archive straight off raw.githubusercontent: one GET, no token, no 60/hr API
    # quota, and a public repo answers anonymously.  The ghread helper this called went away
    # on 07 Oct, and the build never needed anything else from it.
    from urllib.parse import quote
    url = f"https://raw.githubusercontent.com/{REPO}/main/{quote(ZIP_NAME)}"
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    with open(dest, "wb") as fh:
        fh.write(data)
    return dest, f"{REPO}@main:{ZIP_NAME}"


# ----------------------------------------------------------------- 2. clean

def clean(incoming: str, previous: str | None) -> dict:
    zin = zipfile.ZipFile(incoming)
    entries, skipped = [], []
    for i in zin.infolist():
        if i.is_dir():
            continue
        raw = zin.read(i.filename)
        if is_track(i.filename, raw):
            entries.append((i.filename, raw))
        else:
            skipped.append((i.filename, len(raw)))
    rep = {"entries_in": len(entries), "removed_detail": [], "carried_forward": [],
           "missing_carried": [], "renamed": [], "skipped": skipped,
           "entries_seen": len(entries) + len(skipped)}

    # group by normalised content, keep the best-named copy
    groups = defaultdict(list)
    for name, raw in entries:
        groups[sha(raw)].append((name, raw))
    kept = []
    for h, cands in groups.items():
        cands.sort(key=lambda c: name_penalty(c[0]))
        kept.append(cands[0])
        for name, _ in cands[1:]:
            rep["removed_detail"].append((name, "duplicate content"))

    # drop row-identical copies, then partial downloads
    by_sig, stage2 = {}, []
    for name, raw in kept:
        s = rowset(raw)
        if s and s in by_sig:
            rep["removed_detail"].append((name, "row-identical copy"))
            continue
        if s:
            by_sig[s] = name
        stage2.append((name, raw))

    groups = defaultdict(list)
    for name, raw in stage2:
        groups[tuple(sorted(callsigns(raw))[:1]) or ("?",)].append((name, raw))
    stage3 = []
    for key, group in groups.items():
        group.sort(key=lambda c: -len(rowset(c[1])))
        for i, (name, raw) in enumerate(group):
            s = rowset(raw)
            if any(len(rowset(group[j][1])) > len(s) and (s - rowset(group[j][1])) == frozenset()
                   for j in range(i)):
                rep["removed_detail"].append((name, "partial download (rows are a subset)"))
                continue
            stage3.append((name, raw))

    # restore anything a previous build had that has gone missing or been truncated
    if previous and os.path.exists(previous):
        zprev = zipfile.ZipFile(previous)
        have = {sha(zprev.read(n)) for n in zprev.namelist()}
        present = {sha(r) for _, r in stage3}
        for n in zprev.namelist():
            raw = zprev.read(n)
            if sha(raw) in present:
                continue
            full = rowset(raw)
            flight = n.split("-")[0]
            # only a file whose rows are fully contained in the previous one is a
            # truncated re-download of it; anything else is a different flight
            shorter = [(m, r) for m, r in stage3
                       if m.split("/")[-1].startswith(flight + "-")
                       and len(rowset(r)) < len(full)
                       and (rowset(r) - full) == frozenset()]
            if shorter:
                stage3 = [x for x in stage3 if x not in shorter]
                stage3.append((n, raw))
                detail = ", ".join(f"`{m.split('/')[-1]}` ({len(rowset(r))} rows)"
                                   for m, r in shorter)
                rep["carried_forward"].append((n, detail, len(full)))

        # Second pass: tracks that are simply absent from the incoming archive.
        # The archive is published as append-only, so a track that has been
        # published once stays published even when a later export omits it -
        # otherwise a partial re-export silently deletes flight history.
        present = {sha(r) for _, r in stage3}
        rowsets = {frozenset(rowset(r)) for _, r in stage3}
        for n in zprev.namelist():
            raw = zprev.read(n)
            if sha(raw) in present:
                continue
            full = frozenset(rowset(raw))
            if not full or full in rowsets:
                continue
            flight = n.split("/")[-1].split("-")[0]
            # if the incoming archive carries a fuller version of the same flight,
            # the older copy is superseded and is not carried forward
            superseded = any(m.split("/")[-1].startswith(flight + "-")
                             and (full - frozenset(rowset(r))) == frozenset()
                             and len(rowset(r)) > len(full)
                             for m, r in stage3)
            if superseded:
                continue
            stage3.append((n, raw))
            present.add(sha(raw))
            rowsets.add(full)
            rep["missing_carried"].append((n.split("/")[-1], len(full)))

    # final naming
    used, tracks = set(), []
    for name, raw in sorted(stage3, key=lambda c: c[0].split("/")[-1]):
        out = canonical_name(name, used)
        if out != name.split("/")[-1]:
            rep["renamed"].append((name.split("/")[-1], out))
        tracks.append((out, raw.replace(b"\r\n", b"\n")))

    rep["tracks"] = tracks
    rep["removed"] = len(rep["removed_detail"])
    return rep


def write_zip(tracks, path: str) -> None:
    # a fixed stamp, not the clock: the zip is then a pure function of its contents, so
    # "the hash changed" always means real data changed (an FR24 export re-published
    # unchanged used to hash differently on every rebuild, which made the daily
    # round-trip unverifiable)
    stamp = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, raw in tracks:
            zi = zipfile.ZipInfo(name, date_time=stamp)
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, raw)


# ----------------------------------------------------------------- 3. stats

def analyse(path: str) -> dict:
    z = zipfile.ZipFile(path)
    names = z.namelist()
    st = {"tracks": len(names), "names": names, "zip_bytes": os.path.getsize(path)}
    st["uncompressed"] = sum(i.file_size for i in z.infolist())
    ops = {"UR": "Uganda Airlines", "ET": "Ethiopian Airlines", "QR": "Qatar Airways",
           "XY": "Flynas", "SN": "Brussels Airlines", "TK": "Turkish Airlines",
           "WB": "RwandAir", "KL": "KLM", "MS": "EgyptAir", "FZ": "flydubai",
           "KQ": "Kenya Airways", "GA": "Garuda Indonesia"}
    agg = defaultdict(lambda: {"n": 0, "f": 0, "a": None, "b": None})
    odd_cs = []
    months, routes, days = Counter(), Counter(), Counter()   # routes keyed by (from, to)
    calls, sizes, hdrs, gaps, maxgaps = set(), [], Counter(), [], []
    first = last = None
    offap = []
    for n in names:
        raw = z.read(n)
        sizes.append(len(raw))
        allrows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig", "replace"))))
        if allrows:
            hdrs[",".join(c.strip() for c in allrows[0])] += 1
        data = rows_of(raw)
        op = re.sub(r"\d+.*", "", n.split("-")[0]) or "??"
        ts = []
        for r in data:
            try:
                ts.append(float(r[0]))
            except (ValueError, IndexError):
                pass
            if len(r) > 2 and r[2].strip():
                calls.add(r[2].strip())
        if not ts:
            continue
        d = agg[op]
        d["n"] += 1
        d["f"] += len(ts)
        d["a"] = min(ts) if d["a"] is None else min(d["a"], min(ts))
        d["b"] = max(ts) if d["b"] is None else max(d["b"], max(ts))
        first = min(ts) if first is None else min(first, min(ts))
        last = max(ts) if last is None else max(last, max(ts))
        months[datetime.fromtimestamp(min(ts), timezone.utc).strftime("%Y-%m")] += 1
        days[datetime.fromtimestamp(min(ts), timezone.utc).strftime("%Y-%m-%d")] += 1
        here = sorted({r[2].strip() for r in data if len(r) > 2 and r[2].strip()})
        if re.match(r"^(UR|UG)\d", n) and here and not re.match(r"^(UGD|UR|UG)\d+[A-Z]?$", here[0]):
            odd_cs.append((n, "; ".join(here)))
        if len(ts) > 1:
            g = sorted(ts[i] - ts[i - 1] for i in range(1, len(ts)) if ts[i] > ts[i - 1])
            if g:
                gaps.append(g[len(g) // 2])
                maxgaps.append(max(g))
        try:
            a1, o1 = (float(x) for x in data[0][3].split(","))
            a2, o2 = (float(x) for x in data[-1][3].split(","))
            k1, d1 = BL.nearest_airport(a1, o1)
            k2, d2 = BL.nearest_airport(a2, o2)
            routes[(k1, k2)] += 1
            if d1 > 25 or d2 > 25:
                offap.append((n, k1, round(d1), k2, round(d2)))
        except (ValueError, IndexError):
            pass
    st.update({"ops": agg, "op_names": ops, "months": months, "days": days,
               "routes": routes, "callsigns": len(calls), "sizes": sizes,
               "headers": hdrs, "gaps": gaps, "maxgaps": maxgaps,
               "first": first, "last": last, "offap": offap})
    st["fixes"] = sum(agg[o]["f"] for o in agg)
    st["airports_seen"] = sorted({a for k in routes for a in k})
    st["odd_cs"] = odd_cs
    return st


# ----------------------------------------------------------------- 4. outputs

def manifest(tracks, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "flight", "callsign", "fixes", "first_utc", "last_utc",
                    "duration_min", "bytes"])
        for name, raw in tracks:
            m = CANON.match(name)
            a, b = span(raw)
            fmt = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ") if t else ""
            w.writerow([name, m.group(1).upper() if m else "", ";".join(sorted(callsigns(raw))),
                        fixes(raw), fmt(a), fmt(b),
                        round((b - a) / 60, 1) if a and b else "", len(raw)])


def log_and_flights(clean_zip: str, month: str, log_path: str, csv_path: str):
    flights, skipped = BL.build(clean_zip, month)
    if not flights:
        return None, None, skipped
    txt = BL.render(flights, month)
    head = txt.split("## ", 1)[0].rstrip()
    extra = ("\n\nGenerated from the position tracks in `FR data.zip`; `flights.csv` carries the same\n"
             "flights with UTC times, air time and the source file for each.\n")
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(head + extra + "\n" + "## " + txt.split("## ", 1)[1])
    flights.sort(key=lambda f: f["t_off_utc"])
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date_local", "flight", "origin", "takeoff_local", "departure_utc",
                    "arrival_local", "arrival_utc", "dest", "next_day",
                    "takeoff_not_observed", "landing_not_observed", "air_minutes",
                    "fixes", "source_file"])
        for f in flights:
            utc = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
            w.writerow([f["dep"].strftime("%d%b%y").upper(), f["fn"], f["origin"],
                        f["dep"].strftime("%H%M"), utc(f["t_off_utc"]), f["arr"].strftime("%H%M"),
                        utc(f["t_land_utc"]), f["dest"],
                        "Y" if f["arr"].date() > f["dep"].date() else "",
                        "Y" if f["est"] else "", "Y" if f["unobs"] else "",
                        round(f["dur"]), f["n"], f["name"]])
    return flights, txt, skipped


def write_readme(st: dict, flights, log_txt, rep: dict, skips, month: str, state: dict) -> str:
    f = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
    aggs = st["ops"]
    ops_sorted = sorted(aggs.items(), key=lambda kv: -kv[1]["n"])
    op_rows = "\n".join(
        f"| {st['op_names'].get(o, 'unrecognised prefix')} ({o}) | {d['n']} | {d['f']:,} | "
        f"{f(d['a'])} → {f(d['b'])} |" for o, d in ops_sorted if o != "??")
    if "??" in aggs:
        d = aggs["??"]
        op_rows += f"\n| *no callsign in file* | {d['n']} | {d['f']:,} | {f(d['a'])} |"

    routes = st["routes"]
    top = routes.most_common(12)
    route_line = "; ".join(f"{a}-{b} ({v})" for (a, b), v in top)
    months = "\n".join(f"{k}: {v:>3d}" for k, v in sorted(st["months"].items()))
    # the build month's day table, from the log (departure dates) and from track starts
    log_days = Counter()
    pat = re.compile(r"^(\d{2}[A-Z]{3}\d{2})\s")
    for line in (log_txt or "").split("\n"):
        m = pat.match(line)
        if m:
            log_days[m.group(1)] += 1
    trk_days = Counter()
    for d, n in st["days"].items():
        if d.startswith(month + "-"):
            trk_days[d[8:]] += n
    key = lambda d: datetime.strptime(d, "%d%b%y")
    if log_days:
        order = sorted(log_days, key=key)
        hdr = " | ".join(order)
        hdr2 = "|".join("---" for _ in order)
        row1 = " | ".join(str(trk_days.get(datetime.strptime(d, "%d%b%y").strftime("%d"), 0)) for d in order)
        row2 = " | ".join(str(log_days[d]) for d in order)
        sept_table = (f"| Day | {hdr} |\n|---|{hdr2}|\n| tracks | {row1} |\n"
                      f"| flights logged | {row2} |")
        log_range = f"{order[0]}–{order[-1]}"
    else:
        sept_table, log_range = "_(no log generated)_", "—"

    # illustrative examples for the README: a plain line, a +1 line, a marked line
    plain = plus = marked = None
    for line in (log_txt or "").split("\n"):
        t = line.strip()
        if not re.match(r"^\d{2}[A-Z]{3}\d{2}\s+[A-Z]{2,3}\d+[A-Z]?\s+[A-Z]{3}\d{4}\s+–\s+\d{4}", t):
            continue
        if t.endswith(("≈", "*")) and not marked:
            marked = t
        elif "+1" in t and not plus:
            plus = t
        elif not plain:
            plain = t
    example = "\n".join(x for x in (plain, plus, marked) if x) or "01SEP26  UGD713 JNB0255 – 0746EBB"

    nfl = len(flights) if flights else 0
    n_est = sum(1 for x in flights if x["est"]) if flights else 0
    n_unobs = sum(1 for x in flights if x["unobs"]) if flights else 0
    est_origins = Counter(x["origin"] for x in flights if x["est"]).most_common() if flights else []
    unobs_dests = Counter(x["dest"] for x in flights if x["unobs"]).most_common() if flights else []
    plus1 = sum(1 for x in flights if x["arr"].date() > x["dep"].date()) if flights else 0

    maxg = sorted(st["maxgaps"], reverse=True)[:3]
    zip_mb = st["zip_bytes"] / 1024 / 1024
    unc_mb = st["uncompressed"] / 1024 / 1024
    mtime = ["manifest.csv", "all_flights_aeroroutes.md", "flights.csv"]
    _look = RL.live_dir(OUT, month)
    def _sz(n):
        # the root first: `README.md` and `FR data.zip` are root files, and a month folder may
        # hold a file of its own with the same name (its freeze README).  Month tables are not
        # duplicated at the root, so they fall through to the folder on the second try.
        for d in (OUT, _look):
            q = os.path.join(d, n)
            if os.path.exists(q):
                return os.path.getsize(q)
        return 0
    sizes = {n: v for n in [ZIP_NAME] + mtime + ["README.md"] if (v := _sz(n))}
    kb = lambda n: f"{sizes[n]/1024/1024:.1f} MB" if sizes[n] > 1_000_000 else f"{round(sizes[n]/1024)} KB"

    removed_rows = Counter(r for _, r in rep["removed_detail"])
    removed_tbl = "\n".join(f"| {k} | {v} |" for k, v in removed_rows.most_common())
    cf = ""
    if rep["carried_forward"]:
        cf = ("\n**Restored this run.** These were present in the previous build but missing or "
              "truncated in the incoming archive, so the fuller version was put back:\n\n"
              + "\n".join(f"* `{n}` — the incoming archive carried only {detail}, against "
                          f"{total} rows in the previous build" for n, detail, total in rep["carried_forward"])
              + "\n")
    # anything that arrived that is not a track, named by type - KML exports in
    # particular, since those look like flight data but are not the CSV archive
    noncsv = rep.get("skipped", [])
    nc_tbl = ""
    if noncsv:
        byext = {}
        for n, _ in noncsv:
            ext = os.path.splitext(n.split("/")[-1].lower())[1] or "no extension"
            byext.setdefault(ext, []).append(n.split("/")[-1])
        rows = "\n".join(f"| `{e}` | {len(v)} | {', '.join(sorted(v)[:4])}"
                          f"{' and %d more' % (len(v)-4) if len(v) > 4 else ''} |"
                          for e, v in sorted(byext.items(), key=lambda kv: -len(kv[1])))
        nc_tbl = ("\n**Non-track files removed this run.** These were in the incoming archive but are "
                  "not part of the CSV archive, so they were dropped rather than published:\n\n"
                  "| type | count | files |\n|---|---|---|\n" + rows + "\n")

    mc = ""
    if rep.get("missing_carried"):
        mc = (f"\n**Carried forward this run.** {len(rep['missing_carried'])} track(s) that this "
              "repository already published were absent from the incoming archive, so the published "
              "copies were kept. The archive is append-only — a later export that omits a flight does "
              "not delete it:\n\n" +
              "\n".join(f"* `{n}` — {rows} position fixes" for n, rows in rep["missing_carried"]) + "\n")

    # main() has already folded this run into the state; just read it back
    cum = state.get("cumulative_removed", rep["removed"])
    ref = os.path.join(OUT, "reference")
    napt = nrwy = 0
    if os.path.exists(os.path.join(ref, "airports.csv")):
        napt = sum(1 for _ in csv.DictReader(open(os.path.join(ref, "airports.csv"))))
    if os.path.exists(os.path.join(ref, "runways.csv")):
        nrwy = sum(1 for _ in csv.DictReader(open(os.path.join(ref, "runways.csv"))))
    cum_runs = state.get("runs", 1)
    n_ref_files = len([x for x in os.listdir(ref) if x.endswith(".csv")]) if os.path.isdir(ref) else 0
    n_rt = 0
    if os.path.exists(os.path.join(ref, "route_distances.csv")):
        with open(os.path.join(ref, "route_distances.csv"), newline="") as fh:
            n_rt = sum(1 for _ in csv.reader(fh)) - 1
    ref_wx = ""
    _wxs = sorted(x for x in os.listdir(ref) if x.startswith("weather_") and x.endswith(".csv")) \
        if os.path.isdir(ref) else []
    _wx = os.path.join(ref, _wxs[-1]) if _wxs else None
    if _wx:
        with open(_wx, newline="") as fh:
            n_wx = sum(1 for _ in csv.reader(fh)) - 1
        ref_wx = (f"| `reference/{os.path.basename(_wx)}` | {n_wx:,} | published surface observations "
                  f"(METAR) for the airports this operation uses, one row per report | "
                  f"Iowa Environmental Mesonet ASOS archive — free to redistribute |\n")

    # ---- the analysis layer --------------------------------------------------
    # Each entry is (file, row unit, what it is, how it is rebuilt).  A file is
    # only listed when it is actually sitting in the output folder, so the README
    # can never advertise something that is not published.
    ANALYSIS = [
        ("tails.csv", "flights", "which aircraft flew which leg, from the per-tail app pages, "
                                  "with the app's own status flag and a track-verified marker",
         "PYTHONPATH=. python3 work/final.py"),
        ("fleet_summary.csv", "tails", "per-aircraft totals from the tracks: flights, air hours, "
                                       "routes, cruise and top of climb, with MSN and cabin",
         "PYTHONPATH=. python3 work/final.py"),
        ("fleet_meta.csv", "tails", "the hardware record behind those columns: MSN, ICAO type code, "
                                    "mode-S hex, build month, cabin split",
         "maintained by hand, then re-run work/final.py"),
        ("triangle_assignments.csv", "sectors", "the fifth-freedom legs flown away from Entebbe "
                                                "(LUN-HRE, ZNZ-JRO), with flight numbers",
         "PYTHONPATH=. python3 work/final.py"),
        ("triangle_routes.md", "", "the triangle-route write-up", "PYTHONPATH=. python3 work/triangle_report.py"),
        ("runway_usage.csv", "tracks", "runway identification and runway-use measurement per track: "
                                       "which end, where the roll started, how much runway was used",
         "PYTHONPATH=. python3 work/runways.py"),
        ("runway_usage.md", "", "the runway report, including the corrected Entebbe centreline",
         "python3 work/runway_report.py"),
        ("flight_conditions.csv", "flights", "the published weather at each end of every flight: wind, "
                                             "gust, visibility, temperature, and the head/crosswind "
                                             "component on the runway actually used",
         "PYTHONPATH=. python3 work/weather.py"),
        ("weather_analysis.md", "", "what the weather explains: runway-in-use, wind against the "
                                    "measured rolls, delayed sectors", "PYTHONPATH=. python3 work/weather.py"),
        ("punctuality.csv", "flights", "the app's status flag for each leg (on time / late / very late) "
                                       "and the measured minutes against the usual departure time",
         "python3 work/punctuality.py"),
        ("punctuality.md", "", "the punctuality write-up, by aircraft and by worst departure",
         "python3 work/punctuality.py"),
        ("app_status.csv", "rows", "the flag table underneath: every status dot read off the "
                                   "per-tail screenshots, matched to its flight",
         "python3 work/app_status.py"),
        ("date_coverage.md", "", "day-by-day coverage: which days of the month are complete, which "
                                 "are holed, which rotations never finished",
         "PYTHONPATH=. python3 work/date_coverage.py"),
        ("data_gaps.md", "", "what is missing and why, counted against the other files in this folder",
         "PYTHONPATH=. python3 work/report_gaps.py"),
        ("no_code_tracks.md", "", "tracks that arrived without a flight code, and every one the log "
                                   "does not cite — its own line says how wide the scan was",
         "PYTHONPATH=. python3 work/no_code_tracks.py"),
        ("schedule_delays.csv", "legs", "the published timetable joined to what the aircraft did: "
                                        "scheduled and observed instants in UTC, delay, and the block "
                                        "the fleet actually spends",
         "FR24_MONTH=<month> python3 work/schedule_delays.py"),
        ("schedule_delays.md", "", "the schedule write-up: the offsets the export actually uses, the "
                                   "legs measured so far, and the sectors blocked tighter than they fly",
         "FR24_MONTH=<month> python3 work/schedule_delays.py"),
        ("SUPPORTING.md", "", "one-line description and rebuild command for every derived file",
         "written by this same build: `python3 fr24_update.py --zip <export>`"),
    ]
    ABSENT_WHY = {
        "fleet_summary.csv": "hours and cycles per airframe, built from the per-tail screenshots — and "
                             "no October screenshots have arrived, so there is no October fleet to tabulate",
        "triangle_assignments.csv": "the fifth-freedom legs come from the same screenshots, whose window "
                                    "ends 30 Sep",
        "triangle_routes.md": "the write-up over those assignments; same reason",
        "FR data.zip": "the archive is cumulative and lives at the top level, one copy for every month",
        "README.md": "written when the month closes: `python3 work/close_month.py <month>`",
    }
    ana = []
    for name, unit, what, how in ANALYSIS:
        # the analysis tables live in this month's folder; the root is only a fallback for a
        # build that has not been moved over yet — without it the inventory below quietly
        # counts two files instead of ten
        path = next((q for q in (RL.live_dir(OUT, month), OUT)
                     if os.path.exists(os.path.join(q, name))), None)
        if path is None:
            continue
        path = os.path.join(path, name)
        rows = ""
        if name.endswith(".csv"):
            with open(path, newline="", encoding="utf-8", errors="replace") as fh:
                n = sum(1 for _ in csv.reader(fh)) - 1
            rows = f"{n:,} {unit}"
        ana.append((name, rows, what, how))
    metar_dir = os.path.join(OUT, "metar")
    n_metar = len([x for x in os.listdir(metar_dir)
                   if len(x) == 8 and x.endswith(".csv")]) if os.path.isdir(metar_dir) else 0
    ana_tbl = "\n".join(f"| `{n}` | {r or '—'} | {w} | `{h}` |" for n, r, w, h in ana)
    metar_row = ""
    if n_metar:
        metar_row = (f"| `metar/` | {n_metar} airports | every published METAR for each airport in this "
                     f"operation, one CSV per station plus `index.csv`, raw report text kept | "
                     f"`python3 work/metar_split.py` |\n")
    _sup_rows = "\n".join(f"| `{n}` | {r or '—'} | {w} | `{h}` |" for n, r, w, h in ana)
    if metar_row:
        _sup_rows += "\n" + metar_row.rstrip("\n")

    have = {n for n, _, _, _ in ana}
    try:                                   # one list of a month's files, defined in close_month
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work'))
        from close_month import FILES
    except Exception:
        FILES = []
    miss = [n for n in list(FILES) + ['README.md'] if n not in have and not os.path.exists(
        os.path.join(RL.live_dir(OUT, month), n))]
    absent_block = ""
    if miss:
        absent_block = ("\n## Deliberately absent\n\n"
                        "A month folder is not a smaller copy of the archive: some layers cannot be "
                        "written for a month that has no input for them. They are listed so their "
                        "absence is a fact and not an oversight.\n\n")
        for n in miss:
            absent_block += (f"* `{n}` — " + ABSENT_WHY.get(
                n, "not produced for this month; the command in `work/` will write it when the data "
                   "arrives") + "\n")
        absent_block += "\n"

    n_ana = len(ana) + (1 if n_metar else 0)
    ana_inventory = ""
    if n_ana:
        ana_inventory = (f"| analysis files | {n_ana} files | **Derived from the tracks**: aircraft "
                         f"assignment, runway use, weather, punctuality, triangles |")

    with open(os.path.join(RL.live_dir(OUT, month), "SUPPORTING.md"), "w", encoding="utf-8") as fh:
        fh.write(f'''# Supporting files — what each one is, and how to regenerate it

Derived from the tracks already published here. Nothing in this list is hand-edited:
every row count was read off the file itself when this index was written, and each
file has a one-line command that rebuilds it after a new daily upload.

| file | rows | what it is | rebuild with |
|---|---|---|---|
{_sup_rows}
{absent_block}
## Two things worth knowing

**The screenshots arrive in batches.** `tails.csv` is built from the per-tail app
pages, transcribed into `work/screens_extra/batch_<date>.csv` and merged by
`work/final.py`. A row that already exists is dropped rather than counted twice, so
adding a batch never inflates the totals. To add a day, save its rows as a CSV with
columns `tail,date,flight,origin,dest` in that folder and re-run the command.

**Weather comes from the Iowa Environmental Mesonet ASOS archive** — the same
published reports that feed NOAA's Integrated Surface Database, free and with no
account. It is a live service: each airport is cached in `weather/raw/<ICAO>.csv`,
so delete that folder to re-fetch. Harare files under **FVRG** and Lusaka under
**FLKK** (both re-coded since the runway datasets were compiled); Juba (HSSJ) has no
observations in the archive at all.

Licences: the OurAirports tables are public domain; METAR observations are US
government public-domain data redistributed by IEM under their free-use terms; the
Entebbe centreline geometry derived from OpenStreetMap is ODbL — attribute it rather
than republishing the geometry.
''')

    odd = st.get("odd_cs") or []
    if odd:
        fam = Counter((re.match(r"^[A-Z]+\d+", n).group(0), c) for n, c in odd)
        odd_note = (f"* **{len(odd)} track{'s' if len(odd) > 1 else ''} in the archive carr"
                    f"{'y' if len(odd) > 1 else 'ies'} a callsign outside the operator's series** — "
                    + "; ".join(f"`{fl}` ×{n} transmits `{c}`" for (fl, c), n in sorted(fam.items()))
                    + ". The log is built from the operator's own callsigns (`UGD…`, `UR…`, `UG…`), "
                      "so these tracks stay in the archive and out of the log. The per-tail app "
                      "pages do list them, under `UR523`, so they appear in `tails.csv` as rows "
                      "with no track match.")
    else:
        odd_note = ""

    seen = st.get("airports_seen") or []
    new_apt = ""
    for a in seen:
        if not a.isalpha():                      # an OurAirports ident, not an IATA code
            rows_ = [k for k in st["routes"] if a in k]
            new_apt += (f"* **`{a}` is a new airport in the data** — "
                        f"{sum(st['routes'][k] for k in rows_)} tracks touch it, and it carries no "
                        f"IATA or ICAO code yet, so the tables key it by its OurAirports ident. "
                        f"OurAirports still records it as under construction.\n")

    if st.get("last"):
        lt = datetime.fromtimestamp(st["last"], timezone.utc)
        loc = lt + timedelta(hours=3)                       # EAT, the operator's base
        lastday = max((f["dep"].date() for f in flights), default=None)
        if lastday and loc.date() <= lastday:
            tail2 = "so the final day of the log is a stub up to that moment, not a finished day"
        else:
            tail2 = ("which is past the end of the last logged day, so that day runs to its normal end")
        cut_note = (f"* **The download ends at {loc.strftime('%H:%M')} local on {loc.strftime('%d %b')}** "
                    f"({lt.strftime('%Y-%m-%d %H:%M:%SZ')} UTC) — the last position in the archive. "
                    f"Nothing after it is in this export yet, {tail2}.")
    else:
        cut_note = ""

    same = [f for f in flights if f["origin"] == f["dest"]]
    if same:
        one = same[0]
        s1 = "s" if len(same) > 1 else ""          # plural agreement, both verbs
        s2 = "" if len(same) > 1 else "s"
        same_ap = (f"* **{len(same)} logged flight{s1} take{s2} off and land{s2} at the same airport** — a "
                   f"local sortie (air test, crew training or a return to base), not a service. It still "
                   f"carries the day's flight number: `{one['fn']}` on {one['dep'].strftime('%d %b')} left "
                   f"and returned to {one['origin']} in {round(one['dur'])} min. Tracks of this shape that "
                   f"fail the callsign gate are counted in the bullet above, not here.")
    else:
        same_ap = "* **Every track departs one airport and lands at another.**"

    # ------------------------------------------------------- month folders in the build
    # a month folder is the unit the repository ships, so the index reads its size off that
    # folder's own flights.csv and can never drift from what is actually there
    q = lambda nm: nm.replace(" ", "%20")     # a folder name with spaces needs it in a link
    closed = []
    for m in RL.month_dirs(OUT):
        fp = os.path.join(m["path"], "flights.csv")
        if os.path.exists(fp):
            with open(fp, newline="", encoding="utf-8") as fh:
                closed.append((m["name"], m["ym"], max(0, sum(1 for _ in fh) - 1), m["closed"]))
    crows = "\n".join(
        f"| [`{m}/`]({q(m)}/) | {n} flights | "
        + ("closed: log, tables and the archive zip as published at the close" if cl
           else "the month being collected now — these files are rewritten by its next export")
        + f" | `python3 work/close_month.py {ym} --force` |"
        for m, ym, n, cl in closed)
    if not crows:
        crows = ("| *no closed month yet* | — | close a finished month with "
                 "`python3 work/close_month.py YYYY-MM` before the next month's first export | — |")
    cross = 0
    mpath = next((cand for cand in (os.path.join(RL.live_dir(OUT, month), "manifest.csv"),
                                    os.path.join(OUT, "manifest.csv")) if os.path.exists(cand)), None)
    if mpath:
        with open(mpath, newline="", encoding="utf-8") as fh:
            cross = sum(1 for r in csv.DictReader(fh)
                        if r["first_utc"][:7] != r["last_utc"][:7])
    if cross == 1:
        cross_note = ("**1 track in the archive changes month mid-flight**: it is stored whole in "
                      "the month it started in, never split across two zips.")
    elif cross:
        cross_note = (f"**{cross} tracks in the archive change month mid-flight**: each is stored "
                      "whole in the month it started in, never split across two zips.")
    else:
        cross_note = ("No track in the archive changes month mid-flight, so every file belongs to "
                      "exactly one month folder.")
    n_closed = len(closed)
    cur_lbl = "every month in the archive" if month == "all" else f"**{month}**"
    closed_row = (f"| month folders | {n_closed} | one per month, each listed under "
                  f"**Months** below |"
                  if closed else
                  "| *closed months* | none yet | freeze a finished month with "
                  "`python3 work/close_month.py YYYY-MM` |")
    vrb = "s" if plus1 == 1 else ""      # "1 flight arrives" / "52 flights arrive"
    # the close-the-month warning, named from the calendar rather than typed: it has to
    # read "the day October's data arrives, September's log ..." today and something
    # else entirely in November
    MON_NAMES = ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"]
    _mm = re.fullmatch(r"(\d{4})-(\d{2})", month or "")
    if _mm:
        _y, _m = int(month[:4]), int(month[5:7])
        _nxt = f"{_y + (_m == 12)}-{_m % 12 + 1:02d}"
        mdir_note = (f"today that is `{RL.month_folder(month)}/`; an export whose newest "
                     f"departures are next month's opens `{RL.month_folder(_nxt)}/` instead")
    else:
        mdir_note = "each month folder in the build is written only by that month's build"

    # fr24_publish/ is kept in the repository's shape now, so every path quoted below is both
    # the repo path and the local one: the README describes what you upload and what you can
    # open next to it, which are the same tree.
    mdir = month if _mm else None
    def rp(nm):
        return RL.repo_target(nm, mdir) if mdir else nm

    where = "" if not mdir else (
        "**Where things live.** `UR <MONTH> <YEAR>/` is one month: its log and every table derived "
        "from\nit. `" + RL.month_folder(mdir) + "/` is " + mdir + ", and it is the same folder in the "
        "build and in the\nrepository — a path needs no translating between the two. "
        "The root holds only what is shared or\ncumulative: `FR data.zip` (every month, because an "
        "export can arrive short and the previous build\nrestores what is missing), `README.md` "
        "(this index), `reference/` and `metar/`. `work/repo_layout.py`\nis the one module that names "
        "any of it, so the build and the repository cannot drift apart\non a path.\n\n---\n\n")

    return f"""# FR24 — Uganda Airlines flight log & ADS-B track archive

Raw flight-tracking data downloaded from FlightRadar24, plus a flight log in AeroRoutes notation.
Two datasets side by side: **what was flown** (the log) and **the recorded position tracks** (the archive).

Rebuilt: **{__import__('datetime').date.today().isoformat()}** from {st['tracks']} tracks of data through **{f(st['last']) if st['last'] else '—'}**.

---

{where}## What is in here

| File | Size | What it is |
|---|---|---|
| `FR data.zip` | {zip_mb:.1f} MB | **{st['tracks']} CSV tracks** · {st['fixes']:,} position fixes · flat, de-duplicated |
| `{rp('manifest.csv')}` | {kb('manifest.csv')} | One row per track: flight, callsign, fixes, first/last fix, duration |
| `{rp('all_flights_aeroroutes.md')}` | {kb('all_flights_aeroroutes.md')} | **The flight log** — {nfl} flights in AeroRoutes notation, {log_range}, generated from the tracks |
| `{rp('flights.csv')}` | {kb('flights.csv')} | The same {nfl} flights as a table: UTC times, air time, fixes, source track |
| `README.md` | this file | Inventory and format reference |
{ana_inventory}
| `reference/` | {n_ref_files} tables | **Static lookups**: the {napt} airports this data touches, their {nrwy} runways, route distances and haul bands, the five airframes, and the published weather — see `reference/README.md` |
{closed_row}
| `{RL.month_folder(mdir)}/` day-by-day reports | not rebuilt on a schedule | `date_coverage.md`, `data_gaps.md` and `no_code_tracks.md` are written at the workspace root and published into this month's folder | `PYTHONPATH=. python3 work/date_coverage.py` |

---

## Months: what is live and what is frozen

Everything above describes {cur_lbl} — the month the log was built for. Each month owns a folder,
and a closed one is never rewritten, so this table is the only part of the index that grows:

| month folder | flights | what it holds | re-freeze with |
|---|---|---|---|
{crows}

* **A flight belongs to the month its departure falls in, local time.** A leg that leaves on the
  last day of a month and lands on the 1st is counted in the month it left, which is why
  {plus1} flight{'' if plus1 == 1 else 's'} in this log arrive{vrb} the next day and stay where
  they started.
* {cross_note}
* **The archive zip is cumulative, and the derived files are not.** `FR data.zip` holds every
  track ever published here ({st['tracks']} now), because a month's export can arrive short and
  the previous build restores what is missing; the log and every analysis file cover one month.
  A closed month's folder therefore keeps its **own copy** of the archive as it stood that day.
* **A month is protected by its folder, not by a ritual.** `--month auto` builds the latest month
  in the archive, and that month's folder is the only thing that build writes: {mdir_note}.
  Closing a month (`python3 work/close_month.py {month if month != 'all' else 'YYYY-MM'}`) is what
  freezes its numbers, writes the folder's own README and leaves the `.closed` marker — it is not
  what keeps an old month safe, because the folder already does that.
* **A month is a folder named `UR <MONTH> <YEAR>`, in the build as in the repository.**
  `fr24_publish/UR SEPTEMBER 2026/` and `UR OCTOBER 2026/` are the same trees, file for file, so
  a path in this README is readable in either place. `work/repo_layout.py` is the one module that
  knows the naming, so a table the build writes appears in the repository at the same path —
  nothing between the two is renamed, repacked or re-addressed.
* **Never *move* a `.zip` with the web rename box.** Typing a path into that box (`UR SEPTEMBER/…`)
  makes GitHub re-commit the file from the browser editor instead of renaming it in place: text
  comes through intact — every `.md` and `.csv` in the same batch did — and a binary comes back as
  two bytes. `UR September flights.zip` went from 4,809,098 B to 2 B at commit `a28b728a`, and the
  plain rename that followed (`97bfdc39`, no path) changed nothing. Treat an archive as: upload to
  the new path, delete the old one.
* The per-tail app pages are rolling history, not a calendar month, so `tails.csv` can carry rows
  from before the month it describes; a closed month keeps exactly what the pages held on the day
  they were captured, and says so in its own README.

---

## Rebuilding it

Nothing in this folder is hand-written. In order, starting from a fresh export dropped in `incoming/`:

1. `python3 fr24_update.py --zip "incoming/FR data NN.zip"` — the archive, `manifest.csv`, the log, `flights.csv`
2. `python3 work/weather.py`, then `python3 work/metar_split.py` and `PYTHONPATH=. python3 work/make_reference.py` — the month's METARs
3. `PYTHONPATH=. python3 work/final.py`, then `work/app_status.py`, `work/runway_report.py`, `work/punctuality.py`, `work/triangle_report.py` — the layers
4. `python3 work/publish_layers.py` — copies the layers into this month's folder, so the build and the repository read the same bytes
5. `PYTHONPATH=. python3 work/date_coverage.py`, `work/report_gaps.py`, `work/no_code_tracks.py` — the day-by-day reports, which read the published tables
6. `python3 fr24_update.py --zip "incoming/FR data NN.zip"` once more — this README quotes file sizes, so it has to be written last
7. when a month closes: `python3 work/close_month.py {month if month != 'all' else 'YYYY-MM'}` (its folder's README and the `.closed` marker)

From step 2 on, every script takes the month from the log it is reading (`work/month_ctx.py`) rather
than from a date written into its source, so the steps above run in October, in November and next
year without an edit — a month with no logged departure in it is the one thing that will stop the
build, and it stops with a message rather than a silently empty folder.

---

## 1. `FR data.zip` — the track archive

**{st['tracks']} tracks · {st['fixes']:,} position fixes · {st['callsigns']} distinct callsigns**
**Coverage: {f(st['first'])} → {f(st['last'])}**

Every file sits flat at the top level and is named `<FLIGHT>-<8 hex>.csv`, where the hex is the FR24
download identifier. One CSV per flight, one flight per CSV.

### What flies in here

| Operator | Track files | Fixes | Coverage |
|---|---:|---:|---|
{op_rows}

Endpoints are matched to the nearest airport in a **{len(BL.AIRPORTS)}-airport reference list**,
taking a match at 25 NM or closer. On that basis the tracks touch **{len(st['airports_seen'])} airports**
and form **{len(routes)} route pairs**. The busiest: {route_line}.

These figures move if the reference list changes — adding an airport reclassifies endpoints that were
previously attributed to a neighbour. The list above is the one used throughout this README.

**{len(st['offap'])} tracks begin or end more than 25 NM from any airport**, meaning the record starts
airborne or stops before landing. Treat their first or last fix as a partial flight, not a take-off or
landing.

### Coverage by month

```
{months}
```

This is an ad-hoc collection rather than a continuous feed: some months carry hundreds of tracks and
others none at all.

### CSV format

Every file shares the same seven-column header:

```csv
Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction
1788681009,2026-09-06T07:50:09Z,UGD110,"0.04533,32.441788",0,2,84
```

| Column | Meaning |
|---|---|
| `Timestamp` | Unix epoch seconds (UTC) |
| `UTC` | ISO-8601 timestamp, same instant, human-readable |
| `Callsign` | Callsign as transmitted — **not the same as the filename**: `UR110-….csv` carries `UGD110`, `ET332-….csv` carries `ETH332` |
| `Position` | `"latitude,longitude"` in WGS-84, quoted because of the comma |
| `Altitude` | Barometric altitude in **feet** |
| `Speed` | **Ground** speed in knots |
| `Direction` | True track in degrees (0–360) |

Files run {round(min(st['sizes'])/1024)}–{round(max(st['sizes'])/1024)} KB. Sampling follows flight phase and
ground-station coverage: the median gap between fixes is about {round(sorted(st['gaps'])[len(st['gaps'])//2])} s, but the
largest gap inside a track has a median of {round(sorted(st['maxgaps'])[len(st['maxgaps'])//2]/60, 1)} minutes, and
{sum(1 for g in st['maxgaps'] if g >= 600)} of the {st['tracks']} tracks contain at least one gap over 10 minutes. The worst
cases are {", ".join(f"{round(g/60)}" for g in maxg)} minutes. **{sum(1 for g in st['maxgaps'] if g >= 1500)} tracks have a gap longer
than 25 minutes and {sum(1 for g in st['maxgaps'] if g >= 2700)} exceed 45 minutes**, so any en-route timing, wind or fuel analysis built
on this data will be working from very sparse stretches. Take-off, landing and total distance are reliable.

---

## 2. `all_flights_aeroroutes.md` — the flight log

**{nfl} flights · {log_range}**

```text
{example}
```

`DDMMMYY  FLIGHT ORIGhhmm – hhmm[+1]DEST[marker]`

* **Times are local at each end** — take-off in the origin's local time, landing in the destination's.
  This is why a short regional flight can appear to arrive "before" it departs (e.g. `EBB1621 – 1609BJM`:
  Entebbe is UTC+3, Bujumbura UTC+2).
* **Dates are local departure dates**, so a flight landing after local midnight is listed under the day
  it left and marked `+1`. {plus1} flights in this log are marked `+1`.
* **`≈` = take-off not observed** ({n_est} flights{', all leaving ' + str(est_origins[0][0]) if len(est_origins) == 1 else ''}).
  The aircraft was first reported already airborne, so the logged time is that first report, not lift-off.
* **`*` = landing not observed** ({n_unobs} flights{', mostly into ' + str(unobs_dests[0][0]) if unobs_dests else ''}).
  The track ends with the aircraft still airborne, so the logged time is the last report, not touchdown.

{sept_table}

Track counts are by UTC start; log entries are by local departure date, so the two differ on the days
that straddle midnight.

**Every line comes from a track**, so the two datasets cover the same window. To pair a line with its
source file, match the flight number to the callsign (`UGD713` → `UR713-….csv`) and convert between
local and UTC — the log's times are local, the CSV timestamps are UTC. `flights.csv` does that
pairing for you, with the source filename on each row.

---

## 3. Analysis files

Anything derived from the tracks sits beside them, at the top level, so the raw archive and the
analysis of it never have to be untangled. Every row count below is read off the file itself when
this README is rebuilt.

| File | Rows | What it is | Rebuild |
|---|---|---|---|
{ana_tbl}
{metar_row}
The rebuild commands refer to the small toolkit kept beside this data (the `work/` scripts); the
files themselves are the deliverable, and every count above can be checked directly against them.

Two notes on the derived files:

* **`tails.csv` is the only place an aircraft is tied to a flight.** The FR24 exports carry no
  registration, so the assignment comes from the per-tail app pages and the track archive; a row
  marked verified is one whose flight number and sector were found in `FR data.zip`.
* **Nothing here is an estimate of a schedule.** `punctuality.csv` measures each departure against
  the usual departure time for that service as flown, because the published timetable is not part
  of this dataset.

---

## 4. Reference data (`reference/`)

The static lookups every analysis here leans on, so the whole thing can be recomputed from
the repository alone:

| File | Rows | What it is | Source |
|---|---:|---|---|
| `reference/airports.csv` | {napt} | every airport these tracks touch, plus the log's network | OurAirports — public domain |
| `reference/runways.csv` | {nrwy} | runway geometry and orientation for those airports | OurAirports — public domain |
| `reference/route_distances.csv` | {n_rt} | great-circle distance per route pair (km, nm) and the haul band | our own calculation |
| `reference/fleet.csv` | 5 | the airframes: type, ownership, haul band | the operator |
{ref_wx}
Haul bands follow the Eurocontrol distance convention: short < 1,500 km, medium
1,500–4,000 km, long > 4,000 km. Notes and licences: `reference/README.md`.

---

## 5. Remaining data notes

* **A track with no callsign cannot be attributed.** Any file whose `Callsign` field is empty on every
  row has no airline and no flight number; it is kept because the positions are valid, and renamed by
  hand once identified.
* **{len(st['offap'])} tracks begin or end more than 25 NM from any airport** (see §1).
{cut_note}
{odd_note}
{new_apt}{same_ap}
* **Markers mark what was not seen** — they are not estimates. Where an event was not witnessed the
  logged time is the nearest real observation and the marker says so.

---

## 6. Daily update

The archive grows by **appending**: existing tracks are never rewritten. One command does the whole
rebuild after you replace the zip in the repository:

```bash
python3 fr24_update.py            # fetch the repo zip, clean, rebuild every output
python3 fr24_update.py --check    # report what would change, write nothing
```

It removes duplicate and row-identical copies, drops partial downloads, restores any fuller version an
earlier build already had, flattens folders, renames to `<FLIGHT>-<8 hex>.csv`, normalises line endings
to LF, then regenerates `manifest.csv`, the log, `flights.csv` and this README with every count
recomputed.

Keep new files in the same seven-column format, one file per flight, named `<FLIGHT>-<8 hex>.csv`.
Avoid `-1`/`_1`/`(1)` suffixes: those are repeat-save artefacts, not versions, and they are what makes
duplicates accumulate.

---

## 7. Cleaning log

This run received **{rep['entries_seen']} entries** ({len(rep.get('skipped', []))} of them not track files,
skipped) and published **{st['tracks']} tracks**
({unc_mb:.2f} MB uncompressed). Cumulative across {cum_runs} run(s): **{cum} files removed**.

| Removed | Count |
|---|---:|
{removed_tbl or '| _none_ | 0 |'}
{cf}{mc}{nc_tbl}
Also normalised: all line endings to LF, and all names to canonical form.

---

## Provenance

Tracks downloaded from FlightRadar24 — hence the repo name and the hex identifiers in the filenames.
The log is generated from those tracks and is written in the notation used by aeroroutes.com. The
archive is raw data as downloaded: values are as reported by the source, with no cleaning,
interpolation or gap filling. Times in the log are observations, never extrapolations — where an event
was not witnessed, a marker says so.
"""


# ----------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", dest="local", help="use a local zip instead of fetching")
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--keep-temp", action="store_true",
                    help="leave work/cleaned.zip in place afterwards (it is 6 MB and rebuilt by every run)")
    ap.add_argument("--month", default="auto",
                    help="month for the log: auto (latest with UR tracks), YYYY-MM, or all")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    prev = os.path.join(OUT, ZIP_NAME)
    try:
        src, label = fetch_zip(a.local)
    except Exception as e:
        # Right after a reorganisation the repository legitimately has no root zip (it was
        # deleted at 2aa4d575 and the upload that puts it back had not gone up yet).  A --check
        # is still useful then, against the build's own copy, so say what is being compared.
        if a.local or not os.path.exists(prev):        # --zip is stored as `local`
            raise
        print(f"  the repository has no {ZIP_NAME} at its root ({type(e).__name__}: {str(e)[:60]}…)")
        src, label = prev, f"local build: {os.path.relpath(prev, HERE)} (no repository copy to compare with)"
    print(f"source: {label}  ({human(os.path.getsize(src))})")

    rep = clean(src, prev)
    if rep.get('skipped'):
        tot = sum(n for _, n in rep['skipped'])
        kml = [n for n, _ in rep['skipped'] if n.lower().endswith(('.kml', '.kmz'))]
        print(f"  {len(rep['skipped'])} file(s) skipped — not FR24 tracks ({human(tot)}):")
        if kml:
            print(f"    (of which {len(kml)} KML track export(s) — the archive is CSV only)")
        for n, sz in rep['skipped'][:8]:
            print(f"    - {n.split('/')[-1]:52s} {human(sz):>9s}")
        if len(rep['skipped']) > 8:
            print(f"    ... {len(rep['skipped'])-8} more")
    print(f"  {rep['entries_in']} entries in → {len(rep['tracks'])} tracks after cleaning")
    if rep.get("missing_carried"):
        print(f"  {len(rep['missing_carried'])} track(s) missing from the incoming archive — "
              f"carried forward from the previous build:")
        for n, rows in rep["missing_carried"][:10]:
            print(f"    ~ {n:46s} {rows:5d} rows")
        if len(rep["missing_carried"]) > 10:
            print(f"    ... {len(rep['missing_carried'])-10} more")
    print(f"  {rep['removed']} removed, {len(rep['carried_forward'])} restored, "
          f"{len(rep['renamed'])} renamed")
    for n, why in rep["removed_detail"][:6]:
        print(f"    - {n.split('/')[-1]:40s} {why}")
    if rep["removed"] > 6:
        print(f"    ... {rep['removed']-6} more")
    for n, detail, total in rep["carried_forward"]:
        print(f"    + restored {n} (incoming carried only {detail}; previous build had {total} rows)")

    if a.check:
        print("\ncheck only: nothing written")
        return 0

    tmp_zip = os.path.join(WORK, "cleaned.zip")
    write_zip(rep["tracks"], tmp_zip)
    st = analyse(tmp_zip)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}

    months_ur = Counter()
    for n, raw in rep["tracks"]:
        if not n.startswith("UR"):
            continue
        a0, _ = span(raw)
        if a0:
            months_ur[datetime.fromtimestamp(a0, timezone.utc).strftime("%Y-%m")] += 1
    if a.month == "auto":
        month = (max(months_ur) if months_ur else
                 max(st["months"]) if st["months"] else
                 datetime.now(timezone.utc).strftime("%Y-%m"))
        others = {k: v for k, v in months_ur.items() if k != month}
        if others:
            print(f"  note: the log covers {month} only; UR tracks also exist in "
                  f"{', '.join(f'{k} ({v})' for k, v in sorted(others.items()))} "
                  f"— pass --month to change this")
    elif a.month == "all":
        month = "all"
    else:
        month = a.month

    # a month owns a folder in the build, exactly as it does in the repository, so building
    # October can never rewrite September again: the files simply live in different places
    MOUT = RL.live_dir(OUT, month)
    os.makedirs(MOUT, exist_ok=True)
    log_path = os.path.join(MOUT, "all_flights_aeroroutes.md")
    csv_path = os.path.join(MOUT, "flights.csv")
    if month == "all":
        allf, alltxt = [], ""
        for m in sorted(months_ur):
            fl, tx, _ = log_and_flights(tmp_zip, m, os.path.join(WORK, f"log-{m}.md"),
                                        os.path.join(WORK, f"fl-{m}.csv"))
            if fl:
                allf += fl
        flights, _ = None, None
        # merge per-month outputs
        import csv as _csv
        merged = {}
        for m in sorted(months_ur):
            p = os.path.join(WORK, f"fl-{m}.csv")
            if os.path.exists(p):
                for r in _csv.DictReader(open(p, encoding="utf-8")):
                    merged[(r["date_local"], r["flight"], r["takeoff_local"])] = r
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = _csv.writer(fh)
            cols = ["date_local", "flight", "origin", "takeoff_local", "departure_utc",
                    "arrival_local", "arrival_utc", "dest", "next_day",
                    "takeoff_not_observed", "landing_not_observed", "air_minutes",
                    "fixes", "source_file"]
            w.writerow(cols)
            for k in sorted(merged):
                w.writerow([merged[k][c] for c in cols])
        with open(log_path, "w", encoding="utf-8") as fh:
            fh.write("# All Flights — AeroRoutes Notation with Departure Dates\n\n")
            fh.write(f"**{len(merged)} flights**, all months present in the archive.\n")
        flights = list(merged.values()) or None
        log_txt = open(log_path, encoding="utf-8").read()
    else:
        flights, log_txt, skips = log_and_flights(tmp_zip, month, log_path, csv_path)

    shutil.copy2(tmp_zip, prev)
    if not a.keep_temp and os.path.exists(tmp_zip) and os.path.abspath(tmp_zip) != os.path.abspath(prev):
        os.remove(tmp_zip)          # the cleaned archive now lives in the build folder
    manifest(rep["tracks"], os.path.join(MOUT, "manifest.csv"))
    state["cumulative_removed"] = state.get("cumulative_removed", 0) + rep["removed"]
    state["runs"] = state.get("runs", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    readme = write_readme(st, flights, log_txt, rep, None, month, state)
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme)

    json.dump(state, open(STATE, "w"), indent=2)

    print(f"\nwrote to {OUT}/:")
    for n in [ZIP_NAME, "README.md", "all_flights_aeroroutes.md", "flights.csv", "manifest.csv"]:
        p = next((q for q in (os.path.join(OUT, n), os.path.join(MOUT, n)) if os.path.exists(q)), None)
        if p:
            print(f"  {os.path.relpath(p, OUT):46s} {human(os.path.getsize(p)):>10s}")
    if flights:
        print(f"\nlog: {len(flights)} flights, "
              f"{sum(1 for x in flights if x['est'])} take-offs not observed, "
              f"{sum(1 for x in flights if x['unobs'])} landings not observed")
    print(f"archive: {st['tracks']} tracks, {st['fixes']:,} fixes, "
          f"{st['callsigns']} callsigns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
