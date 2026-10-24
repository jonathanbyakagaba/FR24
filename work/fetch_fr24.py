#!/usr/bin/env python3
"""Enumerate FR24 flight history for one aircraft registration.

Phase A (history-horizon test): page backwards through the flight list
for a tail until reaching --since, save the combined list to CSV and
print the covered date range. Tells us how far back the account's
history reaches (the September/October gap-recovery question).

Auth: reads subscription_key from the local fr24.conf (Windows:
%LOCALAPPDATA%\\fr24\\fr24\\fr24.conf) and passes it directly, so the
library's JWT parsing is never involved and no secret is printed.

Run in the (fr24env) venv on the user's Windows machine:
    pip install "fr24[curl,polars]==0.4.0" tzdata
    python fetch_fr24.py --reg 5X-KOB --since 2026-09-01

(tzdata is required on Windows: Python there has no system timezone
database and polars/zoneinfo fails with ZoneInfoNotFoundError without it.)
"""

from __future__ import annotations

import argparse
import asyncio
import configparser
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from fr24.authentication import login
from fr24.clients.curl import CurlAsyncClient
from fr24.json import FlightListParams, flight_list, flight_list_df, get_json_headers


def read_subscription_key() -> str:
    cfg_path = (
        Path(os.environ["LOCALAPPDATA"]) / "fr24" / "fr24" / "fr24.conf"
    )
    cfg = configparser.ConfigParser()
    if not cfg.read(cfg_path):
        sys.exit(f"config not found: {cfg_path}")
    key = cfg.get("global", "subscription_key", fallback="").strip()
    if not key:
        sys.exit(f"subscription_key is empty in {cfg_path}")
    return key


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reg", required=True, help="aircraft registration, e.g. 5X-KOB")
    ap.add_argument("--since", default="2026-09-01", help="stop paging at this UTC date")
    ap.add_argument("--out", default="", help="output CSV (default flightlist_<reg>.csv)")
    ap.add_argument("--max-pages", type=int, default=50, help="safety cap on pages")
    args = ap.parse_args()

    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    headers = get_json_headers()
    frames: list[pl.DataFrame] = []

    async with CurlAsyncClient() as client:
        auth = await login(
            client,
            creds={"subscriptionKey": read_subscription_key(), "token": None},
        )
        print("auth:", auth.get("message"))
        page = 1
        timestamp: datetime | str = "now"
        while True:
            resp = await flight_list(
                client,
                FlightListParams(
                    reg=args.reg, page=page, limit=100, timestamp=timestamp
                ),
                headers=headers,
                auth=auth,
            )
            resp.raise_for_status()
            raw = resp.json()
            response_obj = raw.get("result", {}).get("response", {})
            if not response_obj.get("data"):
                print(f"page {page}: no more data")
                break
            df = flight_list_df(raw)
            print(f"page {page}: {df.height} flights")
            frames.append(df)

            oldest = df["ATOD"].min()
            if oldest is not None and oldest < since:
                break
            if not response_obj.get("page", {}).get("more"):
                break
            # FR24 paging quirk (per the library's own fetch-all): the
            # next request needs page+1 AND timestamp re-anchored to the
            # earliest scheduled departure of the batch just received.
            stod_min = df["STOD"].min()
            if stod_min is not None:
                timestamp = stod_min
            page += 1
            if page > args.max_pages:
                print(f"stopping at --max-pages={args.max_pages}")
                break
            await asyncio.sleep(1)  # stay gentle with FR24

    if not frames:
        print("no flights returned")
        return
    allf = pl.concat(frames)
    n_raw = allf.height
    with_id = allf.filter(pl.col("flight_id").is_not_null())
    no_id = allf.filter(pl.col("flight_id").is_null())
    allf = pl.concat(
        [with_id.unique(subset=["flight_id"], keep="first"), no_id]
    )
    if allf.height != n_raw:
        print(f"deduped {n_raw} -> {allf.height} flights (page overlaps)")
    out = args.out or f"flightlist_{args.reg}.csv"
    allf.write_csv(out)
    print(f"total {allf.height} flights -> {out}")
    print("ATOD range:", allf["ATOD"].min(), "to", allf["ATOD"].max())


if __name__ == "__main__":
    asyncio.run(main())
