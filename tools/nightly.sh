#!/usr/bin/env bash
# One command, in a codespace terminal, for the night's whole run: ask FR24, build, publish, push.
#
#     cd /workspaces/FR24 && ./tools/nightly.sh
#
# Why it lives here and not only in Actions: run #10 (3 Nov, scheduled) fetched from a GitHub runner
# and got nothing back at all — `Flightradar24 answered nothing from this runner`. The build and the
# commit work fine from Actions; the *asking* is what the runner cannot always do. This script does
# the same steps from a machine you choose, and pushes, which is what the rest of the pipeline is
# already built to react to.
#
#   --no-pull   work on the checkout as it is (default pulls first)
#   --no-push   build and commit locally, push nothing — use this to see what it would do
#   --dry-run   print the plan and the reachability probe, touch nothing
#   --hours N   how far back to ask FR24 for (default 96 = 4 days, its trail horizon)
#   --skip-fetch / --skip-weather
#
# Exit codes: 0 pushed or nothing to push, 2 the machine could not reach FR24 at all (see PROBE
# below), 3 built and committed but the push failed, 4 nothing new anywhere and nothing was written.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

pull=1 push=1 dry=0 dofetch=1 doweather=1 hours=96
while [ $# -gt 0 ]; do
  case "$1" in
    --no-pull) pull=0 ;;
    --no-push) push=0 ;;
    --dry-run) dry=1 ;;
    --skip-fetch) dofetch=0 ;;
    --skip-weather) doweather=0 ;;
    --hours) shift; hours="${1:-96}" ;;
    *) echo "unknown flag: $1"; exit 2 ;;
  esac
  shift
done

# The publish dir is the checkout root in CI; here it is the same, and saying so in the environment
# means no `fr24_publish` symlink has to exist for the scripts to find their own data.
export FR24_PUBLISH="$PWD"
say() { printf '%s\n' "$*"; }
stamp=$(date -u +%Y-%m-%dT%H:%MZ)

say "== FR24 reachability from this machine"
probe=$(curl -s -m 25 -o /dev/null -w '%{http_code}' \
  -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36' \
  'https://api.flightradar24.com/common/v1/flight/list.json?query=UR110&fetchBy=flight&mode=original&limit=1')
case "$probe" in
  200) say "  HTTP $probe — this machine can ask FR24 directly." ;;
  429) say "  HTTP 429 — reachable but throttled: raise --sleep, or run it again in a few minutes." ;;
  000) say "  no answer at all — no route, DNS or TLS. Nothing here will fetch until that changes." ;;
  *)   say "  HTTP $probe — FR24 refused this network the way it refused the runner." ;;
esac
if [ "$dry" = 1 ]; then
  say "-- dry run: would pull, fetch ${hours}h into work/ci_capture, build, publish flight_paths/,"
  say "  snapshot the weather, then $([ "$push" = 1 ] && echo 'commit and push' || echo 'commit only')."
  [ "$probe" = 200 ] || exit 2
  exit 0
fi

[ "$pull" = 1 ] && { say "== pull"; git pull --ff-only || say "  (not a fast-forward; carrying on with what is here)"; }

say "== fetch, last ${hours}h of trails"
mkdir -p work/ci_capture
frc=0
if [ "$dofetch" = 1 ]; then
  if [ "$probe" = 200 ] || [ "$probe" = 429 ]; then
    python3 tools/fetch_fr24.py --source board --out work/ci_capture --sleep 3 || frc=$?
    say "  fetch exit $frc (0 captured, 3 nothing in the window, 5 refused to name a flight, 4 no answer)"
  else
    frc=4
    say "  skipped the fetch: the probe above says this network gets nothing back (exit 4)"
  fi
else
  say "  --skip-fetch"
fi

# Keep the raw pull where it is committed. work/ci_capture is gitignored and a codespace stops after
# half an hour of idleness: a capture that only ever lived there is a capture that can vanish.
cap=""
if [ -f work/ci_capture/"FR data.zip" ]; then
  keep="capture/$stamp"
  mkdir -p "$keep"
  cp work/ci_capture/*.csv work/ci_capture/capture_manifest.json "$keep"/ 2>/dev/null
  cp work/ci_capture/"FR data.zip" "$keep"/"capture.zip"
  cap="--capture-zip $keep/capture.zip"
  say "  raw pull kept at $keep ($(ls "$keep" | wc -l) files)"
fi

say "== build"
if [ -n "$cap" ]; then
  python3 tools/ci_run.py $cap --changed-file /tmp/nightly_changed.txt || say "  ! the build said no (see above); publishing whatever it did write"
else
  say "  no capture to build on; rebuilding the tables from the archive on the branch"
  python3 tools/ci_run.py --allow-archive-fallback --changed-file /tmp/nightly_changed.txt || say "  ! build failed"
fi

say "== weather snapshot (aviationweather.gov keeps ~8 days, and SIGMETs only until they expire)"
if [ "$doweather" = 1 ]; then
  python3 tools/fetch_awx.py --hours "$hours" --out work/awx --commit-dir reference/weather ||
    say "  ! aviationweather did not answer; the run carries on without weather"
fi

say "== what moved"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  say "  this is not a git checkout, so there is nothing to commit or push - the files above are the output"
  [ "$frc" = 4 ] && exit 2
  exit 0
fi
git add -A
st=$(git status --porcelain | wc -l | tr -d ' ')
git status --short | head -25
if [ "$st" = 0 ]; then
  say "  nothing to commit: the archive, the tables and the paths already hold everything this run found"
  [ "$frc" = 4 ] && exit 2
  exit 4
fi
git commit -q -m "Nightly $stamp — fr24-ci (from codespace): ${st} file(s), fetch exit $frc"
if [ "$push" = 1 ]; then
  say "== push"
  if git push; then
    say "  pushed. Actions will run off this push: it re-checks the freeze and the notifier, and it"
    say "  will not rebuild the tables, because there is no capture in the runner to build from."
    exit 0
  fi
  say "  ! push failed — the commit is safe locally; run 'git push' when the network is back"
  exit 3
fi
say "  --no-push: commit $(git rev-parse --short HEAD) is local only. 'git push' to publish it."
exit 0
