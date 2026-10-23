#!/usr/bin/env python3
"""Download FR24 playback tracks for a list of target flights.

Phase B (gap recovery): reads a targets CSV produced by matching the
enumerated flight lists against work/missing_legs.csv, downloads the
playback track for each flight_id, and writes it in the repo's track
format:

    Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction
    1753640785,2025-07-27T18:26:25Z,UGD111,"51.155525,-0.169954",0,0,165

one file per flight, named <NUMBER>-<hexid>.csv (e.g. UR720-4172c560.csv),
into --out (default tracks_out/). Files already present are skipped, so
the run is resumable. A 1.5 s pause between requests keeps it gentle.

Targets CSV columns: flight_id_hex, number, callsign, date, from, to
(only flight_id_hex and number are strictly required).

Run in the (fr24env) venv on the user's Windows machine:
    python fetch_tracks.py targets.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from fr24.authentication import login
from fr24.clients.curl import CurlAsyncClient
from fr24.json import PlaybackParams, get_json_headers, playback, playback_df

from fetch_fr24 import read_subscription_key

DELAY_S = 1.5


async def fetch_one(client, headers, auth, target: dict, out_dir: Path) -> str:
    hex_id = target["flight_id_hex"].strip().lower().removeprefix("0x")
    number = (target.get("number") or "UNKNOWN").strip()
    dest = out_dir / f"{number}-{hex_id}.csv"
    if dest.exists() and dest.stat().st_size > 0:
        return f"skip {dest.name} (already downloaded)"

    resp = await playback(
        client, PlaybackParams(flight_id=hex_id), headers=headers, auth=auth
    )
    resp.raise_for_status()
    raw = resp.json()
    df = playback_df(raw)
    if df.height == 0:
        return f"EMPTY {number} {hex_id}: playback returned no track points"

    # Callsign: prefer the playback metadata, fall back to the target row.
    callsign = target.get("callsign") or ""
    try:
        flight = raw["result"]["response"]["data"]["flight"]
        callsign = flight["identification"]["callsign"] or callsign
    except Exception:
        pass

    with dest.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["Timestamp", "UTC", "Callsign", "Position", "Altitude", "Speed", "Direction"]
        )
        for row in df.iter_rows(named=True):
            ts = int(row["timestamp"])
            utc = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            pos = f"{row['latitude']:.6f},{row['longitude']:.6f}"
            w.writerow(
                [ts, utc, callsign, pos, int(row["altitude"]),
                 int(row["ground_speed"]), int(row["track"])]
            )
    first = datetime.fromtimestamp(int(df["timestamp"].min()), timezone.utc)
    last = datetime.fromtimestamp(int(df["timestamp"].max()), timezone.utc)
    return f"ok {dest.name}: {df.height} points, {first} .. {last}"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", help="targets CSV (flight_id_hex, number, ...)")
    ap.add_argument("--out", default="tracks_out", help="output directory")
    args = ap.parse_args()

    with open(args.targets, newline="") as f:
        targets = list(csv.DictReader(f))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{len(targets)} targets -> {out_dir}/")

    headers = get_json_headers()
    done = failed = 0
    async with CurlAsyncClient() as client:
        auth = await login(
            client,
            creds={"subscriptionKey": read_subscription_key(), "token": None},
        )
        print("auth:", auth.get("message"))
        for i, target in enumerate(targets, 1):
            try:
                msg = await fetch_one(client, headers, auth, target, out_dir)
            except Exception as e:  # keep going; report at the end
                msg = f"FAIL {target.get('number')} {target.get('flight_id_hex')}: {e}"
                failed += 1
            else:
                if msg.startswith(("ok", "skip")):
                    done += 1
                else:
                    failed += 1
            print(f"[{i}/{len(targets)}] {msg}")
            if i < len(targets):
                await asyncio.sleep(DELAY_S)
    print(f"finished: {done} ok/skipped, {failed} empty/failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
