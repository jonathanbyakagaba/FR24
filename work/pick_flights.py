#!/usr/bin/env python3
"""Hand-pick flights by flight number + date and download their tracks.

Companion to fetch_tracks.py (which works from a precomputed target
list). Here the picks are resolved live: for each pick, FR24's flight
list is queried by flight number, flights whose actual departure falls
on the requested date (East Africa Time, UTC+3) are kept, optionally
filtered by route, and their tracks are downloaded in repo format into
--out (default tracks_out/), named <NUMBER>-<hexid>.csv as usual.

Picks CSV columns: flight,date[,from,to]   (from/to are IATA, optional)
Example:
    flight,date,from,to
    UR111,2026-10-05,LGW,EBB
    UR720,2026-09-14,,

Run in the (fr24env) venv on the user's Windows machine:
    python pick_flights.py picks.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from fr24.authentication import login
from fr24.clients.curl import CurlAsyncClient
from fr24.json import FlightListParams, flight_list, flight_list_df, get_json_headers

from fetch_fr24 import read_subscription_key
from fetch_tracks import fetch_one

EAT = timezone(timedelta(hours=3))
MAX_PAGES = 5

# Our stations: IATA -> ICAO (flight-list responses use ICAO).
IATA_TO_ICAO = {
    "EBB": "HUEN", "NBO": "HKJK", "DAR": "HTDA", "JNB": "FAOR",
    "LGW": "EGKK", "LOS": "DNMM", "BOM": "VABB", "MBA": "HKMO",
    "MGQ": "HCMM", "JUB": "HSSJ", "HRE": "FVHA", "ZNZ": "HTZA",
    "JRO": "HTKJ", "BJM": "HBBA", "LUN": "FLKK",
}


def route_ok(row: dict, pick: dict) -> bool:
    for key, col in (("from", "origin"), ("to", "destination")):
        want = (pick.get(key) or "").strip().upper()
        if not want:
            continue
        got = (row.get(col) or "").upper()
        if got not in {want, IATA_TO_ICAO.get(want, want)}:
            return False
    return True


async def resolve(client, headers, auth, pick: dict) -> list[dict]:
    """Return flight-list rows matching the pick (may be >1 on
    multi-sector days; route columns disambiguate)."""
    flight_no = pick["flight"].strip().upper()
    day = datetime.fromisoformat(pick["date"].strip()).date()
    # Anchor just after the date; list returns flights with ATD < timestamp.
    timestamp: datetime | str = datetime.combine(
        day + timedelta(days=3), time.min, tzinfo=timezone.utc
    )
    matches: list[dict] = []
    page = 1
    while page <= MAX_PAGES:
        resp = await flight_list(
            client,
            FlightListParams(flight=flight_no, page=page, limit=100, timestamp=timestamp),
            headers=headers,
            auth=auth,
        )
        resp.raise_for_status()
        raw = resp.json()
        response_obj = raw.get("result", {}).get("response", {})
        if not response_obj.get("data"):
            break
        df = flight_list_df(raw)
        for row in df.iter_rows(named=True):
            atod = row.get("ATOD")
            if atod is None:
                continue
            if atod.astimezone(EAT).date() == day and route_ok(row, pick):
                matches.append(row)
        if not response_obj.get("page", {}).get("more"):
            break
        stod_min = df["STOD"].min()
        if stod_min is not None:
            timestamp = stod_min
        page += 1
        await asyncio.sleep(1)
    return matches


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("picks", help="picks CSV (flight,date[,from,to])")
    ap.add_argument("--out", default="tracks_out", help="output directory")
    args = ap.parse_args()

    with open(args.picks, newline="") as f:
        picks = list(csv.DictReader(f))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{len(picks)} picks -> {out_dir}/")

    headers = get_json_headers()
    unresolved = 0
    async with CurlAsyncClient() as client:
        auth = await login(
            client,
            creds={"subscriptionKey": read_subscription_key(), "token": None},
        )
        print("auth:", auth.get("message"))
        for i, pick in enumerate(picks, 1):
            label = f"{pick['flight']} {pick['date']}"
            try:
                rows = await resolve(client, headers, auth, pick)
            except Exception as e:
                print(f"[{i}/{len(picks)}] {label}: resolve FAILED: {e}")
                unresolved += 1
                continue
            if not rows:
                print(f"[{i}/{len(picks)}] {label}: no matching flight found")
                unresolved += 1
                continue
            for row in rows:
                target = {
                    "flight_id_hex": f"{int(row['flight_id']):08x}",
                    "number": row.get("number") or pick["flight"],
                    "callsign": row.get("callsign") or "",
                }
                try:
                    msg = await fetch_one(client, headers, auth, target, out_dir)
                except Exception as e:
                    msg = f"FAIL {target['number']} {target['flight_id_hex']}: {e}"
                print(f"[{i}/{len(picks)}] {label}: {msg}")
                await asyncio.sleep(1.5)
    if unresolved:
        print(f"{unresolved} pick(s) unresolved")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
