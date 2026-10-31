#!/usr/bin/env python3
"""Where each published file lives in the GitHub repo, as the repository is actually organised.

The workspace and the repo have different shapes on purpose:

  workspace  `fr24_publish/` holds the **live month flat** (that is what every analysis
             script reads) and `fr24_publish/YYYY-MM/` holds a closed month's snapshot.
  repo       **one folder per month**, named `UR <MONTH> <YEAR>` — `UR SEPTEMBER 2026/`,
             `UR OCTOBER 2026/` — with the cumulative archive and the shared lookups at the
             top level: `FR data.zip`, `README.md`, `reference/`, `metar/`.

Only this module knows the second shape, so the build and a hand-assembled upload cannot
disagree about a target path.  The month
folder a file lands in is the month the build describes, read from the published log — so the
day October data arrives, the same command writes `UR OCTOBER 2026/` with no edit anywhere.

One rule the repo has already paid for: **do not move a binary with the web rename box.** Typing a
path into it makes GitHub re-commit the file from the editor rather than rename it in place — the
commit shows `added` + `removed`, and the added copy is what the editor held: 2 bytes, `\r\n`.
`UR September flights.zip` went from 4,809,098 B to that at commit `a28b728a` ("Rename UR September
flights.zip to UR SEPTEMBER/UR September flights.zip"), while the `.md` and `.csv` files moved the
same way came through to the byte.  A rename without a path (`97bfdc39`) preserved it.  So: move
text with the rename box, move an archive by uploading it at the new path and deleting the old one.
"""
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, REPO, BRANCH = 'jonathanbyakagaba', 'FR24', 'main'
CACHE = os.path.join(ROOT, 'work', 'repo_tree_cache.json')

# at the repo root: cumulative, or shared by every month
TOP_LEVEL = {'FR data.zip', 'README.md', 'fleet_meta.csv', 'reference/', 'metar/'}
# fleet_meta.csv belongs here as well as in publish_layers.CUMULATIVE: it is the hand-kept
# hardware record, one copy for every month, so a pack must not put a second one in a month folder.
# a repo path is <folder>/<file>; a pack path is <action>/<repo path>
MONTH_RE = re.compile(r'^(\d{4})-(\d{2})$')
NAME = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December']


PUBLISH = os.environ.get('FR24_PUBLISH') or os.path.join(ROOT, 'fr24_publish')
TZ = os.environ.get('FR24_TZ', 'Africa/Kampala')


def today():
    """The user's calendar day, not the sandbox's.  Kampala is UTC+3 with no DST, so an
    evening build would otherwise stamp a folder 'frozen 2026-10-01' on the day the user
    opens it and reads 2 October.  Falls back to the machine date if the zone is unknown."""
    import datetime as _dt
    try:
        from zoneinfo import ZoneInfo
        return _dt.datetime.now(ZoneInfo(TZ)).date()
    except Exception:
        return _dt.date.today()
CLOSED = '.closed'          # a marker file inside a frozen month folder


def live_dir(base=None, month=None):
    """The folder the current build's month files live in — a month folder in the publish
    dir, named exactly as the repo names it.  `fr24_publish/UR SEPTEMBER 2026/` for a
    September build, so the workspace and the repository have the same tree."""
    base = base or PUBLISH
    if month is None:
        from month_ctx import ctx
        month = ctx()['ym']
    if not re.fullmatch(r'\d{4}-\d{2}', month or ''):
        return base
    return os.path.join(base, month_folder(month))


def archive(ym=None, base=None):
    """Where this month's track archive is, for anything that has to check numbers against it.

    The publish root's `FR data.zip` is the build's own: flat, de-duplicated, byte-reproducible.
    A month folder's copy and the raw extract a month is named after are fallbacks, in that
    order — reading those first would check the tables against pre-clean data and report
    tracks the build deliberately dropped."""
    base = base or PUBLISH
    if ym is None:
        from month_ctx import ctx
        ym = ctx()['ym']
    word = month_folder(ym).split()[1].title() if re.fullmatch(r'\d{4}-\d{2}', ym or '') else None
    d = live_dir(base, ym)
    # order matters: the build's own zip is the cleaned, reproducible one, so it wins over a
    # month folder's copy and over the raw extract the month happens to be named after
    cands = [os.path.join(base, 'FR data.zip'), os.path.join(d, 'FR data.zip')]
    if word:
        cands += [os.path.join(d, f'UR {word} flights.zip'),
                  os.path.join(base, f'UR {word} flights.zip')]
    for q in cands:
        if os.path.exists(q):
            return q
    raise SystemExit(f'no track archive for {ym}: looked in {d} and {base} — '
                     f'run python3 fr24_update.py --zip "<export>" first')


def is_closed(folder):
    return os.path.exists(os.path.join(folder, CLOSED))


def mark_closed(folder):
    open(os.path.join(folder, CLOSED), 'w').write(
        'Frozen by work/close_month.py — the tables in this folder are not rewritten by later '
        'builds, because each month now owns its own folder.\n')


def month_folder(ym):
    """'2026-09' -> 'UR SEPTEMBER 2026'"""
    m = MONTH_RE.match(ym or '')
    if not m:
        return ym
    y, mo = int(m.group(1)), int(m.group(2))
    return f'UR {NAME[mo - 1].upper()} {y}'


def ym_of_folder(path):
    """'UR SEPTEMBER 2026/x.csv' -> '2026-09' when the folder is a month folder"""
    m = re.match(r'^UR ([A-Za-z]+) (\d{4})/', path + '/')
    if not m:
        return None
    names = {n.lower(): i + 1 for i, n in enumerate(NAME)}
    mo = names.get(m.group(1).lower())
    return f'{m.group(2)}-{mo:02d}' if mo else None


def month_dirs(base=None):
    """Month folders in `base`, either naming — `2026-09` or `UR SEPTEMBER 2026` — as
    {'ym':…, 'name':…, 'path':…, 'closed': bool} sorted by month."""
    base = base or PUBLISH
    out = {}
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return []
    for n in names:
        p = os.path.join(base, n)
        if not os.path.isdir(p):
            continue
        ym = n if MONTH_RE.match(n) else ym_of_folder(n + '/')
        if ym and MONTH_RE.match(ym):
            out[ym] = {'ym': ym, 'name': n, 'path': p, 'closed': is_closed(p)}
    return [out[k] for k in sorted(out)]


def repo_target(rel, live_month):
    """a path inside `fr24_publish/` -> its path in the repo"""
    rel = rel.replace(os.sep, '/')
    top = rel.split('/')[0]
    m = MONTH_RE.match(top)
    if m:                                                    # a frozen month snapshot
        return '/'.join([month_folder(top)] + rel.split('/')[1:])
    if rel in TOP_LEVEL or any(rel.startswith(t) for t in TOP_LEVEL if t.endswith('/')):
        return rel                                             # shared or cumulative
    return f'{month_folder(live_month)}/{rel}'                # the build month's own folder


# ------------------------------------------------------------------ repo state
def fetch_tree(offline_ok=True):
    """`{path: size}` for every blob, from the GitHub API.  Cached in `work/`, because
    the build should describe the repo as it is without needing the network twice."""
    try:
        url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'fr24-pack',
                                                   'Accept': 'application/vnd.github+json'})
        with urllib.request.urlopen(req, timeout=40) as r:
            t = json.load(r)
        if 'tree' not in t:
            raise OSError(t.get('message', 'no tree'))
        head = {}
        try:
            hurl = f'https://api.github.com/repos/{OWNER}/{REPO}/commits?per_page=1'
            with urllib.request.urlopen(urllib.request.Request(
                    hurl, headers={'User-Agent': 'fr24-pack'}), timeout=40) as r:
                h = json.load(r)[0]
            head = {'sha': h['sha'][:8], 'date': h['commit']['author']['date']}
        except Exception:                                    # noqa: BLE001 - commit info only
            pass
        blobs = {e['path']: e['size'] for e in t['tree'] if e['type'] == 'blob'}
        dirs = sorted({e['path'] for e in t['tree'] if e['type'] == 'tree'})
        out = {'blobs': blobs, 'dirs': dirs, **head}
        json.dump(out, open(CACHE, 'w'), indent=1)
        return out
    except Exception as e:                                   # noqa: BLE001
        if offline_ok and os.path.exists(CACHE):
            print(f'  ! repo unreachable ({e}) — using the cached tree from {os.path.getmtime(CACHE):.0f}')
            return json.load(open(CACHE))
        raise


def classify(rows, live_month, tree=None):
    """rows: [{name, target, bytes}] -> verdict per row.

    ok          the repo has that path at that size
    wrong-size  right name, different bytes
    wrong-name  the bytes/name exist under a mangled filename (a space, or ' (1)')
    no-folder   its folder does not exist in the repo yet
    missing     not in the repo at all
    """
    tree = tree or fetch_tree()
    blobs, dirs = tree['blobs'], set(tree['dirs'])

    def norm(name):
        n = os.path.basename(name)
        n = re.sub(r'\s*\(\d+\)(?=\.[A-Za-z0-9]+$)', '', n)      # 'README (1).md' -> 'README.md'
        n = re.sub(r'\s+(?=\.[A-Za-z0-9]+$)', '', n)             # 'punctuality .md'
        return n.lower()

    by_dir = {}
    for p, s in blobs.items():
        by_dir.setdefault(os.path.dirname(p), {})[norm(p)] = (p, s)

    out = []
    for r in rows:
        want, exp = r['target'], r['bytes']
        d, f = os.path.dirname(want), os.path.basename(want)
        got = blobs.get(want)
        if got == exp:
            verdict, note = 'ok', ''
        elif got is not None:
            verdict, note = 'wrong-size', f'repo holds {got:,} B'
        else:
            hit = by_dir.get(d, {}).get(norm(f))
            if hit:
                verdict = 'wrong-name'
                note = (f'repo has it as {hit[0]!r} ({hit[1]:,} B)'
                        + ('' if hit[1] == exp else ' — and those bytes are older'))
            elif d and d not in dirs:
                verdict, note = 'no-folder', f'create {d}/ first'
            else:
                verdict, note = 'missing', ''
        out.append({**r, 'verdict': verdict, 'note': note})
    return out


def damage(tree, min_bytes=4096):
    """Repo binaries too small to be what their name claims — the shape a destroyed
    binary leaves behind after a web-UI rename."""
    out = []
    for p, s in tree['blobs'].items():
        if p.lower().endswith(('.zip', '.gz', '.png', '.jpg', '.parquet')) and s < min_bytes:
            out.append((p, s))
    return sorted(out)
