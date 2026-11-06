#!/usr/bin/env python3
"""Turn Flightradar24 track exports into the monthly AeroRoutes-style flight log.

A month lives in ``archive/YYYY-MM/`` and holds:

    tracks/*.csv            the raw Flightradar24 exports, one file per flight
    tracks/manifest.csv     one row per track file: flight id, number, route,
                            registration, aircraft, actual times, SHA-256
    flights_YYYY-MM.csv     one row per flight leg, normalised (written here)
    rotations_YYYY-MM.csv   one row per airframe rotation, its airport chain and
                            any sector the record is missing (written here)
    aeroroutes_YYYY-MM.md   the log in AeroRoutes notation (written here)
    sources.json            what was read, and its checksums (written here)

Build a month once its tracks are in place:

    python3 work/fr24_tracks.py --month 2026-06

Everything else comes from ``reference/``: ``airports.csv`` (coordinates,
elevation, city, IATA), ``airport_timezones.csv`` (local clock), ``fleet.csv``
(registration -> type) and ``route_distances.csv`` (great-circle distance).

The export format handled is Flightradar24's playback export:

    Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction[,Airport,OnGround...]

with ``Position`` as "lat,lon" or separate Latitude/Longitude columns. Column
names are matched loosely, so exports from the API, the playback page and the
mobile app all read in.

The AeroRoutes conventions reproduced here, per aeroroutes.com listings:

    **Entebbe – Johannesburg**          route heading, city pairs, en dash
    *eff 01JUN26* 5 weekly A330-800     effective date, weekly frequency, equipment
    UR713 EBB0900 – 1125JNB A338 135    flight no, dep time+code, arr time+code,
                                        type, days of week (1=Mon ... 7=Sun, x=except)

Times are the times the aircraft actually got airborne and touched down, in
local time at each end, to the minute.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import re
import statistics
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "reference"

# A track export is cut into legs wherever one callsign goes quiet for this long.
LEG_GAP = timedelta(minutes=60)
MIN_POINTS = 4
MIN_KM = 20.0
AIRPORT_RADIUS_KM = 25.0

MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
               "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# Marketing names used in the frequency line, keyed by ICAO type designator.
TYPE_NAMES = {
    "A338": "A330-800",
    "A339": "A330-900",
    "A332": "A330-200",
    "A333": "A330-300",
    "A20N": "A320neo",
    "B738": "737-800",
    "B38M": "737 MAX 8",
    "B739": "737-900",
    "CRJ9": "CRJ900",
    "CRJ2": "CRJ200",
    "DH8D": "Dash 8-400",
    "AT76": "ATR 72-600",
    "E190": "E190",
}

# header aliases -> canonical name. Everything is normalised to lower snake case
# first, so "Vertical Rate", "vertical_rate" and "verticalrate" all collapse.
ALIASES = {
    "timestamp": {"timestamp", "ts", "epoch", "time", "unixtime"},
    "utc": {"utc", "datetime", "datetime_utc", "date_time_utc", "time_utc",
            "date", "date_time"},
    "callsign": {"callsign", "call_sign", "flight", "flight_number", "flightno",
                 "flight_id", "ident"},
    "registration": {"registration", "reg", "tail", "tail_number",
                     "aircraft_registration", "ac_reg"},
    "type": {"type", "aircraft", "aircraft_type", "type_code", "icao_type",
             "equipment", "ac_type", "model"},
    "position": {"position", "pos", "latlon", "location"},
    "latitude": {"latitude", "lat", "y"},
    "longitude": {"longitude", "lon", "lng", "long", "x"},
    "altitude": {"altitude", "alt", "altitude_ft", "height"},
    "speed": {"speed", "gs", "ground_speed", "spd"},
    "heading": {"direction", "heading", "track", "hdg"},
    "vertical_rate": {"verticalrate", "vertical_rate", "vs", "climb"},
    "squawk": {"squawk", "squawk_code"},
    "onground": {"onground", "on_ground", "ground", "is_ground"},
    "airport": {"airport", "near_airport", "airport_code", "nearest_airport"},
    "origin": {"origin", "from", "departure", "dep", "origin_iata", "from_airport"},
    "destination": {"destination", "to", "arrival", "arr", "destination_iata",
                    "to_airport"},
}
CANONICAL = {alias: key for key, aliases in ALIASES.items() for alias in aliases}


# --------------------------------------------------------------------------- #
# reference data
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Airport:
    ident: str
    iata: str
    city: str
    lat: float
    lon: float
    elevation_ft: float
    tz: ZoneInfo

    @property
    def code(self) -> str:
        return self.iata or self.ident

    @property
    def label(self) -> str:
        return self.city or self.iata or self.ident


def load_airports(reference: Path = REFERENCE) -> list[Airport]:
    tz_rows = {}
    tz_path = reference / "airport_timezones.csv"
    if tz_path.exists():
        with tz_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                tz_rows[row["ident"]] = row
    airports = []
    with (reference / "airports.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ident = row["ident"]
            extra = tz_rows.get(ident, {})
            tz_name = extra.get("timezone") or "UTC"
            airports.append(Airport(
                ident=ident,
                iata=(row.get("iata_code") or "").upper(),
                # the airport table carries the display name AeroRoutes would use
                # ("London Gatwick", "Kilimanjaro") where it differs from the town
                city=(extra.get("city") or row.get("municipality") or "").strip(),
                lat=float(row["latitude_deg"]),
                lon=float(row["longitude_deg"]),
                elevation_ft=float(row["elevation_ft"] or 0),
                tz=ZoneInfo(tz_name),
            ))
    return airports


def load_fleet(reference: Path = REFERENCE) -> dict[str, str]:
    path = reference / "fleet.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {(row["registration"] or "").upper(): (row["icao_type"] or "").upper()
                for row in csv.DictReader(fh)}


def load_gc_distances(reference: Path = REFERENCE) -> dict[str, int]:
    path = reference / "route_distances.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["route"]: int(row["gc_km"]) for row in csv.DictReader(fh)}


def great_circle_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_airport(airports, lat, lon, radius_km=AIRPORT_RADIUS_KM):
    best, best_km = None, radius_km
    for ap in airports:
        km = great_circle_km(lat, lon, ap.lat, ap.lon)
        if km < best_km:
            best, best_km = ap, km
    return best


# --------------------------------------------------------------------------- #
# reading the export
# --------------------------------------------------------------------------- #

@dataclass
class Point:
    ts: datetime
    lat: float
    lon: float
    altitude: float | None = None
    speed: float | None = None
    onground: bool | None = None
    callsign: str = ""
    registration: str = ""
    type: str = ""
    airport: str = ""


def _norm_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")


def _parse_bool(value: str) -> bool | None:
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in {"true", "1", "yes", "y", "ground", "g"}:
        return True
    if v in {"false", "0", "no", "n", "air", "a"}:
        return False
    return None


def _parse_time(row: dict, cols: dict) -> datetime | None:
    raw = row.get(cols.get("timestamp", ""), "") if cols.get("timestamp") else ""
    text = row.get(cols.get("utc", ""), "") if cols.get("utc") else ""
    # "2025-06-01 04:12:33" (with or without UTC suffix)
    for candidate in (text, raw):
        if not candidate:
            continue
        candidate = str(candidate).strip().replace("Z", "").replace(" UTC", "")
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M:%S",
                    "%Y-%m-%d"):
            try:
                return datetime.strptime(candidate, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    for candidate in (raw, text):
        if not candidate:
            continue
        try:
            value = float(str(candidate).strip())
        except ValueError:
            continue
        if value > 1e11:          # milliseconds
            value /= 1000.0
        if value > 1e9:
            return datetime.fromtimestamp(value, tz=timezone.utc)
    return None


def read_export(path: Path) -> list[Point]:
    points: list[Point] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {}
        for name in reader.fieldnames or []:
            key = CANONICAL.get(_norm_header(name))
            if key and key not in cols:
                cols[key] = name
        if "latitude" not in cols and "position" not in cols:
            raise SystemExit(f"{path}: no latitude/longitude or Position column found "
                             f"(headers: {reader.fieldnames})")
        for row in reader:
            ts = _parse_time(row, cols)
            if ts is None:
                continue
            lat = lon = None
            if "latitude" in cols and "longitude" in cols:
                try:
                    lat = float(row[cols["latitude"]])
                    lon = float(row[cols["longitude"]])
                except (TypeError, ValueError):
                    lat = lon = None
            if lat is None and "position" in cols:
                pos = str(row[cols["position"]] or "")
                m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*[,; ]\s*(-?\d+(?:\.\d+)?)", pos)
                if m:
                    lat, lon = float(m.group(1)), float(m.group(2))
            if lat is None or lon is None:
                continue
            speed = None
            if "speed" in cols:
                try:
                    speed = float(str(row[cols["speed"]]).replace(",", ""))
                except (TypeError, ValueError):
                    speed = None
            altitude = None
            if "altitude" in cols:
                try:
                    altitude = float(str(row[cols["altitude"]]).replace(",", ""))
                except (TypeError, ValueError):
                    altitude = None
            points.append(Point(
                ts=ts, lat=lat, lon=lon, altitude=altitude, speed=speed,
                onground=_parse_bool(row.get(cols["onground"])) if "onground" in cols else None,
                callsign=(row.get(cols["callsign"], "") if "callsign" in cols else "").strip().upper(),
                registration=(row.get(cols["registration"], "") if "registration" in cols else "").strip().upper(),
                type=(row.get(cols["type"], "") if "type" in cols else "").strip().upper(),
                airport=(row.get(cols["airport"], "") if "airport" in cols else "").strip().upper(),
            ))
    points.sort(key=lambda p: p.ts)
    return points


def load_manifest(path: Path) -> dict[str, dict]:
    """Track file name -> metadata row, for exports that ship one file per flight."""
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {(row.get("file") or ""): row for row in csv.DictReader(fh)}


# --------------------------------------------------------------------------- #
# legs
# --------------------------------------------------------------------------- #

@dataclass
class Leg:
    callsign: str
    registration: str
    type: str
    origin: Airport | None
    destination: Airport | None
    takeoff: datetime
    landing: datetime
    points: int
    distance_km: float
    max_altitude_ft: float | None
    source: str = ""
    flight_id: str = ""
    # how far the track stops short of an airport it never reached, in km
    gap_km: float = 0.0
    # "track" when the off/on times are read out of the track, "record" when the
    # track was too short and the movement board's actual times were used instead
    time_source: str = "track"
    # true when the track starts and ends on the ground at an airport
    track_complete: bool = True
    # anything worth saying about this leg: a truncated track, or a track that
    # contradicts the flight record it was filed under
    note: str = ""

    @property
    def minutes(self) -> int:
        return round((self.landing - self.takeoff).total_seconds() / 60)

    @property
    def route(self) -> str:
        return f"{self.origin.code if self.origin else 'ZZZZ'}-" \
               f"{self.destination.code if self.destination else 'ZZZZ'}"

    @property
    def local_departure(self) -> datetime | None:
        return self.takeoff.astimezone(self.origin.tz) if self.origin else None

    @property
    def local_arrival(self) -> datetime | None:
        return self.landing.astimezone(self.destination.tz) if self.destination else None


def _airborne_window(points: list[Point], origin: Airport | None, destination: Airport | None):
    """Off/on times: prefer the OnGround flag, fall back to altitude above field."""
    start = end = None
    for p in points:
        if p.onground is False:
            start = p.ts
            break
    for p in reversed(points):
        if p.onground is False:
            end = p.ts
            break
    if start is None or end is None:
        floor = max((origin.elevation_ft if origin else 0),
                    (destination.elevation_ft if destination else 0)) + 1000
        air = [p for p in points if p.altitude is not None and p.altitude > floor]
        if air:
            start, end = air[0].ts, air[-1].ts
    if start is None:
        start = points[0].ts
    if end is None:
        end = points[-1].ts
    return start, end


def _on_the_ground(airports, point: Point) -> Airport | None:
    """The airport an endpoint sits on, if the aircraft is actually down there.

    A nearest-airport lookup on its own is not enough: a track cut off in the
    cruise will still find some airport a few kilometres below it. Requiring the
    endpoint to be low and slow keeps overflights out of the log.
    """
    airport = nearest_airport(airports, point.lat, point.lon)
    if airport is None:
        return None
    if point.onground:
        return airport
    # low over the field is enough: a track that ends on the landing roll is
    # still on 130 knots and a few hundred feet up when the export stops
    low = point.altitude is not None and point.altitude <= airport.elevation_ft + 2000
    return airport if low else None


def _parse_iso(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _airport_by_code(airports, code: str) -> Airport | None:
    code = (code or "").strip().upper()
    if not code:
        return None
    for ap in airports:
        if ap.iata == code or ap.ident == code:
            return ap
    return None


def build_legs(points: list[Point], airports, fleet: dict[str, str],
               meta: dict | None = None, source: str = "") -> list[Leg]:
    """Cut one export into legs. ``meta`` is an optional manifest row for the file."""
    meta = meta or {}
    by_callsign: dict[str, list[Point]] = defaultdict(list)
    for p in points:
        by_callsign[p.callsign or "UNKNOWN"].append(p)

    legs: list[Leg] = []
    for callsign, track in by_callsign.items():
        track.sort(key=lambda p: p.ts)
        segments, current = [], [track[0]]
        for previous, point in zip(track, track[1:]):
            if point.ts - previous.ts > LEG_GAP:
                segments.append(current)
                current = [point]
            else:
                current.append(point)
        segments.append(current)

        # A gap in coverage is not a stop. Only re-open the flight where the
        # aircraft is on the ground at an airport on both sides of the gap;
        # otherwise the pieces are one flight with a hole in the middle.
        joined = [segments[0]]
        for segment in segments[1:]:
            before = _on_the_ground(airports, joined[-1][-1])
            after = _on_the_ground(airports, segment[0])
            if before and after and before.ident == after.ident:
                joined.append(segment)
            else:
                joined[-1] = joined[-1] + segment
        segments = joined

        for segment in segments:
            if len(segment) < MIN_POINTS:
                continue
            distance = sum(great_circle_km(a.lat, a.lon, b.lat, b.lon)
                           for a, b in zip(segment, segment[1:]))
            if distance < MIN_KM:
                continue

            # Where did the aircraft actually start and stop?
            #
            # An endpoint that is on the ground at an airport wins over the
            # flight record, because that is how a sector flown under a through
            # flight number (Entebbe-Zanzibar-JRO) shows up. Where the track
            # never reaches the ground, the record is the better evidence and
            # the track is only a partial record of the flight.
            grounded_origin = _on_the_ground(airports, segment[0])
            grounded_destination = _on_the_ground(airports, segment[-1])
            recorded_origin = _airport_by_code(airports, meta.get("from", ""))
            recorded_destination = _airport_by_code(airports, meta.get("to", ""))
            origin = grounded_origin or recorded_origin \
                or nearest_airport(airports, segment[0].lat, segment[0].lon)
            destination = grounded_destination or recorded_destination \
                or nearest_airport(airports, segment[-1].lat, segment[-1].lon)
            if origin is None or destination is None:
                continue
            if origin.ident == destination.ident:
                # both ends over the same field: a track cut off after departure
                # or before landing, so fall back on the record for the far end
                origin = recorded_origin or origin
                destination = recorded_destination or destination
                if origin.ident == destination.ident:
                    continue

            endpoints_grounded = bool(grounded_origin and grounded_destination)
            # a flight whose track jumps en route is not measured end to end
            hole = any((b.ts - a.ts) > LEG_GAP for a, b in zip(segment, segment[1:]))
            track_complete = endpoints_grounded and not hole
            recorded_takeoff = _parse_iso(meta.get("atd_utc", ""))
            recorded_landing = _parse_iso(meta.get("ata_utc", ""))
            takeoff, landing = _airborne_window(segment, origin, destination)
            time_source = "track"
            if not endpoints_grounded:
                # the board's actual times are block times, a few minutes either
                # side of airborne, but far closer than a truncated track
                if recorded_takeoff and recorded_landing:
                    takeoff, landing = recorded_takeoff, recorded_landing
                    time_source = "record"
                else:
                    scheduled_takeoff = _parse_iso(meta.get("std_utc", ""))
                    scheduled_landing = _parse_iso(meta.get("sta_utc", ""))
                    if scheduled_takeoff and scheduled_landing:
                        takeoff, landing = scheduled_takeoff, scheduled_landing
                        time_source = "schedule"
            registration = (meta.get("registration") or "").strip().upper()
            if not registration:
                found = Counter(p.registration for p in segment if p.registration).most_common(1)
                registration = found[0][0] if found else ""
            type_code = (meta.get("aircraft") or "").strip().upper()
            if not type_code:
                found = Counter(p.type for p in segment if p.type).most_common(1)
                type_code = found[0][0] if found else ""
            if not type_code:
                type_code = fleet.get(registration, "")
            number = (meta.get("number") or "").strip().upper() or callsign

            # where the track stops short of an airport, or contradicts the record
            notes, gap = [], 0.0
            if not endpoints_grounded:
                start_gap = great_circle_km(segment[0].lat, segment[0].lon,
                                            origin.lat, origin.lon)
                end_gap = great_circle_km(segment[-1].lat, segment[-1].lon,
                                          destination.lat, destination.lon)
                gap = max(start_gap, end_gap)
                if start_gap > AIRPORT_RADIUS_KM:
                    notes.append(f"track picks the flight up {start_gap:.0f} km out")
                if end_gap > AIRPORT_RADIUS_KM:
                    notes.append(f"track stops {end_gap:.0f} km short")
            elif hole:
                missing = max((b.ts - a.ts) for a, b in zip(segment, segment[1:]))
                notes.append(f"track has a {round(missing.total_seconds() / 60)} minute hole en route")
            recorded = ""
            if recorded_origin and recorded_destination:
                recorded = f"{recorded_origin.code}-{recorded_destination.code}"
            if recorded and recorded != f"{origin.code}-{destination.code}":
                notes.append(f"filed as {recorded}, track {origin.code}-{destination.code}")
            altitudes = [p.altitude for p in segment if p.altitude is not None]
            legs.append(Leg(
                callsign=number, registration=registration, type=type_code,
                origin=origin, destination=destination,
                takeoff=takeoff, landing=landing, points=len(segment),
                distance_km=round(distance, 1),
                max_altitude_ft=round(max(altitudes)) if altitudes else None,
                source=source or Path(meta.get("file", "")).name,
                flight_id=(meta.get("flight_id_hex") or "").strip(),
                gap_km=round(gap, 1) if gap > AIRPORT_RADIUS_KM else 0.0,
                time_source=time_source,
                track_complete=track_complete,
                note="; ".join(notes),
            ))
    return legs


# --------------------------------------------------------------------------- #
# rotations
# --------------------------------------------------------------------------- #
#
# The movement board lists point-to-point sectors, so a rotation with a tag stop
# it never recorded — Entebbe–Harare, then Lusaka–Entebbe with the same airframe
# in between — reads as two unrelated flights. Chaining an airframe's legs keeps
# the missing sector visible as an *untracked hop*, so the rotation still runs
# start to finish instead of falling apart into orphan sectors.

# a rotation is one airframe's day of flying: its legs, grouped by the local
# date they departed. The fleet turns in two or three hours around the clock, so
# a ground-time cut-off alone would chain a week of flying into one rotation.
# A hop the record is missing has to fit inside this gap to count as a tag sector.
MAX_HOP_GAP = timedelta(hours=8)
# an untracked hop longer than this is a repositioning, not a tag sector
MAX_HOP_KM = 3000.0
# used to test whether a tag sector fits inside the hole in the record
HOP_SPEED_KMH = 600.0
MIN_HOP_KM = 50.0

# the operator's base: rotations are grouped and timed on Entebbe's clock
BASE_TZ = ZoneInfo("Africa/Kampala")
# the flying day turns over at 04:00 local, so a night rotation that puts down
# after midnight still belongs to the day it left on
SERVICE_DAY_SHIFT = timedelta(hours=4)


def _code(airport: Airport | None) -> str:
    return airport.code if airport else "ZZZZ"


@dataclass(frozen=True)
class UntrackedHop:
    """A sector an airframe must have flown between two legs, with no track."""

    origin: str
    destination: str
    after: datetime   # wheels down of the leg before the hop
    before: datetime  # wheels up of the leg after it
    # index (in the rotation's legs) of the leg that follows the hop
    index: int = 0
    # false when the hole is too small to hold the sector the airframe must
    # have flown — a track that overlaps its neighbour, not a missing flight
    plausible: bool = True

    @property
    def route(self) -> str:
        return f"{self.origin}-{self.destination}"


@dataclass
class Rotation:
    """One airframe's run of legs, with any sector missing from the record."""

    key: str                        # registration, or callsign if unregistered
    legs: list[Leg]
    hops: list[UntrackedHop] = field(default_factory=list)

    day: date = None  # local date the rotation flew (set by build_rotations)

    @property
    def id(self) -> str:
        day = self.day or self.legs[0].takeoff.date()
        return f"{self.key}-{day:%Y%m%d}"

    @property
    def start(self) -> datetime:
        return self.legs[0].takeoff

    @property
    def end(self) -> datetime:
        return self.legs[-1].landing

    @property
    def type(self) -> str:
        return self.legs[0].type

    @property
    def complete(self) -> bool:
        return not self.hops

    @property
    def sectors(self) -> int:
        return len(self.legs) + len(self.hops)

    def _tokens(self, mark_hops: bool) -> list[str]:
        """Airport sequence the airframe flew, with each hop where it fell."""
        hops = {hop.index: hop for hop in self.hops}
        tokens = [_code(self.legs[0].origin)]
        for i, leg in enumerate(self.legs):
            hop = hops.get(i)
            if hop is not None:
                if hop.origin != tokens[-1]:
                    tokens.append(hop.origin)
                label = hop.destination if hop.plausible else f"{hop.destination}?"
                tokens.append(f"[{label}]" if mark_hops else label)
            elif _code(leg.origin) != tokens[-1]:
                tokens.append(_code(leg.origin))
            tokens.append(_code(leg.destination))
        return tokens

    @property
    def chain(self) -> str:
        """Airport sequence the airframe flew, every sector a plain code."""
        return "–".join(self._tokens(mark_hops=False))

    @property
    def marked_chain(self) -> str:
        """The same chain with the airports only reached through a hop bracketed."""
        return "–".join(self._tokens(mark_hops=True))

    @property
    def flight_numbers(self) -> str:
        return " ".join(dict.fromkeys(leg.callsign for leg in self.legs))


def _tag_fits(after: Airport | None, before: Airport | None,
              gap: timedelta) -> bool:
    """Could the airframe have flown ``after`` -> ``before`` inside ``gap``?"""
    if after is None or before is None:
        return False
    km = great_circle_km(after.lat, after.lon, before.lat, before.lon)
    if not MIN_HOP_KM <= km <= MAX_HOP_KM:
        return False
    needed = timedelta(hours=km / HOP_SPEED_KMH) + timedelta(minutes=30)
    return needed <= gap <= MAX_HOP_GAP


def service_day(leg: Leg) -> date:
    """The flying day a leg belongs to, on the base's clock."""
    return (leg.takeoff.astimezone(BASE_TZ) - SERVICE_DAY_SHIFT).date()


def build_rotations(legs: list[Leg]) -> list[Rotation]:
    """Chain each airframe's legs, day by day, keeping the sectors it must have
    flown without a track of their own."""
    groups: dict[tuple[str, date], list[Leg]] = defaultdict(list)
    for leg in legs:
        key = leg.registration or leg.callsign
        if not key:
            continue
        groups[(key, service_day(leg))].append(leg)

    rotations: list[Rotation] = []
    for (key, day) in sorted(groups, key=lambda k: (k[1], k[0])):
        group = sorted(groups[(key, day)], key=lambda leg: leg.takeoff)
        hops: list[UntrackedHop] = []
        for i, (previous, leg) in enumerate(zip(group, group[1:]), start=1):
            if _code(previous.destination) == _code(leg.origin):
                continue
            gap = leg.takeoff - previous.landing
            hops.append(UntrackedHop(
                _code(previous.destination), _code(leg.origin),
                previous.landing, leg.takeoff,
                index=i,
                plausible=_tag_fits(previous.destination, leg.origin, gap)))
        rotations.append(Rotation(key, group, hops, day=day))

    rotations.sort(key=lambda rotation: (rotation.start, rotation.key))
    return rotations


ROTATION_COLUMNS = [
    "rotation_id", "registration", "aircraft_type", "first_takeoff_utc",
    "last_landing_utc", "chain", "sectors", "tracked_sectors",
    "untracked_sectors", "untracked_hops", "complete", "flight_numbers",
]


def write_rotations(path: Path, rotations: list[Rotation]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(ROTATION_COLUMNS)
        for rotation in rotations:
            writer.writerow([
                rotation.id, rotation.key, rotation.type,
                rotation.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                rotation.end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                rotation.chain, rotation.sectors, len(rotation.legs),
                len(rotation.hops),
                " ".join(hop.route if hop.plausible else f"{hop.route}?"
                         for hop in rotation.hops),
                "yes" if rotation.complete else "no", rotation.flight_numbers,
            ])


def _hop_label(hop: UntrackedHop) -> str:
    return hop.route if hop.plausible else f"{hop.route} (unconfirmed)"


def render_rotations(rotations: list[Rotation]) -> list[str]:
    """The rotations section of the month's log: only the chains with a hole."""
    broken = [rotation for rotation in rotations if rotation.hops]
    if not broken:
        return []
    hops = [hop for rotation in broken for hop in rotation.hops]
    doubtful = [hop for hop in hops if not hop.plausible]
    complete = len(rotations) - len(broken)

    intro = (
        "A rotation is one airframe's day of flying, its legs chained in order: "
        f"{len(rotations)} this month, {complete} with every sector of the chain in "
        f"the record. In the {len(broken)} below, the aircraft puts down at one "
        "airport and is next heard from at another, so it must have flown a sector "
        f"the movement board does not hold — {len(hops) - len(doubtful)} such hops. "
        "They are kept in place rather than dropped, so a rotation reads from its "
        "first departure to its last arrival instead of breaking into orphan "
        "sectors. The airport that is only reachable through a hop is bracketed in "
        "the chain, and work/fetch_fr24_tracks.py goes and fetches the sector "
        "itself where Flightradar24 credentials allow, after which the brackets "
        "come off on the next rebuild."
    )
    lines = ["## Rotations", ""] + textwrap.wrap(intro, width=78)
    lines += [
        "",
        "```",
        "EBB–HRE  UR720  →  HRE–[LUN]  →  LUN–EBB  UR721      one rotation",
        "```",
    ]
    if doubtful:
        lines += [""] + textwrap.wrap(
            "A hop carrying a question mark is where the record contradicts itself — "
            "the next leg is already under way while this aircraft should still be "
            "on the ground — so the airport is shown and the sector is not claimed.",
            width=78)
    lines += [
        "",
        "| rotation | aircraft | chain | legs | first off – last on (EBB) |",
        "|---|---|---|---|---|",
    ]
    base = BASE_TZ
    for rotation in sorted(broken, key=lambda r: r.start):
        first = rotation.start.astimezone(base)
        last = rotation.end.astimezone(base)
        window = f"{first:%d}{MONTH_NAMES[first.month - 1]}{first:%y} {first:%H:%M}"
        window += (f" – {last:%H:%M}" if last.date() == first.date()
                   else f" – {last:%d}{MONTH_NAMES[last.month - 1]} {last:%H:%M}")
        lines.append(
            f"| {rotation.id} | {rotation.key} {rotation.type or '—'} | "
            f"{rotation.marked_chain} | {len(rotation.legs)} | {window} |")
    lines.append("")
    return lines


# --------------------------------------------------------------------------- #
# AeroRoutes notation
# --------------------------------------------------------------------------- #

def hhmm(value: datetime, tz: ZoneInfo) -> str:
    return value.astimezone(tz).strftime("%H%M")


def day_marker(departure: datetime, arrival: datetime, origin_tz, dest_tz) -> str:
    delta = arrival.astimezone(dest_tz).date() - departure.astimezone(origin_tz).date()
    return f"(+{delta.days})" if delta.days > 0 else ""


def compress_days(days: list[int]) -> str:
    if not days:
        return ""
    days = sorted(set(days))
    if len(days) == 7:
        return "1234567"
    return "".join(str(d) for d in days)


def frequency_text(days: list[int]) -> str:
    n = len(set(days))
    if n == 7:
        return "1 daily"
    return f"{n} weekly"


def type_name(code: str) -> str:
    return TYPE_NAMES.get(code, code or "—")


def render_log(month: str, legs: list[Leg], gc_km: dict[str, int],
               sources: list[dict] | None = None,
               rotations: list[Rotation] | None = None) -> str:
    year, month_no = (int(x) for x in month.split("-"))
    month_label = f"{datetime(year, month_no, 1):%B %Y}"
    start = datetime(year, month_no, 1)
    end = datetime(year + month_no // 12, month_no % 12 + 1, 1) - timedelta(days=1)
    # a month still in progress is dated by what it covers, not by the calendar
    first_flight = min(leg.local_departure for leg in legs).date()
    last_flight = max(leg.local_departure for leg in legs).date()
    covered = first_flight == start.date() and last_flight == end.date()
    if covered:
        period = (f"{start:%d}{MONTH_NAMES[start.month - 1]}{start:%y} – "
                  f"{end:%d}{MONTH_NAMES[end.month - 1]}{end:%y}")
    else:
        period = (f"{first_flight:%d}{MONTH_NAMES[first_flight.month - 1]}{first_flight:%y} – "
                  f"{last_flight:%d}{MONTH_NAMES[last_flight.month - 1]}{last_flight:%y}"
                  f" (part month, {len({leg.local_departure.date() for leg in legs})} days)")

    directions: dict[tuple[str, str], list[Leg]] = defaultdict(list)
    for leg in legs:
        directions[(leg.origin.code, leg.destination.code)].append(leg)

    city = {}
    for leg in legs:
        city[leg.origin.code] = leg.origin.label
        city[leg.destination.code] = leg.destination.label

    total_minutes = sum(leg.minutes for leg in legs)
    airframes = sorted({leg.registration for leg in legs if leg.registration})
    types = sorted({leg.type for leg in legs if leg.type})
    partial = [leg for leg in legs if not leg.track_complete]
    discrepancies = [leg for leg in legs if "filed as" in leg.note]
    from_record = [leg for leg in legs if leg.time_source == "record"]
    from_schedule = [leg for leg in legs if leg.time_source == "schedule"]
    flown_km = sum(leg.distance_km for leg in legs if leg.track_complete)
    sources = sources or []
    rotations = rotations if rotations is not None else build_rotations(legs)
    complete_rotations = [rotation for rotation in rotations if rotation.complete]

    lines = [
        f"# Uganda Airlines — {month_label}",
        "",
        "Flight log in [AeroRoutes](https://www.aeroroutes.com/) notation, rebuilt from the",
        f"month's Flightradar24 track exports (`archive/{month}/tracks/`, "
        f"{len(sources):,} files).",
        "",
        "| field | value |",
        "|---|---|",
        "| operator | Uganda Airlines (UR / UGD) |",
        f"| period | {period} |",
        f"| flights | {len(legs):,} |",
        f"| airborne | {total_minutes // 60:,} h {total_minutes % 60:02d} min |",
        f"| distance flown | {flown_km:,.0f} km (complete tracks only) |",
        f"| track coverage | {len(legs) - len(partial)} of {len(legs)} flights end to end |",
        f"| city pairs | {len(directions)} directional / "
        f"{len({frozenset(k) for k in directions})} undirected |",
        f"| rotations | {len(rotations)}"
        + (f" ({len(rotations) - len(complete_rotations)} with an untracked hop)"
           if complete_rotations is not None and len(complete_rotations) < len(rotations)
           else "")
        + " |",
        f"| airframes | {', '.join(airframes) if airframes else '—'} |",
        f"| types | {', '.join(types) if types else '—'} |",
        "",
        "**How to read a line.** Route heading in bold, then the effective date, weekly",
        "frequency and equipment, then one line per flight number:",
        "",
        "```",
        "UR713 EBB0900 – 1125JNB A338 135",
        "  |    |         |      |   |   +-- days of week flown (1 = Monday ... 7 = Sunday)",
        "  |    |         |      |   +------ ICAO type designator",
        "  |    |         |      +---------- arrival airport (IATA)",
        "  |    |         +----------------- arrival time, local, HHMM",
        "  |    +--------------------------- departure time, local, HHMM",
        "  +-------------------------------- flight number",
        "```",
        "",
        "Times are the actual off/on times recorded in the track data, converted to",
        "local time at each end; `(+1)` marks an arrival on the following day. A flight",
        "is logged under the date it departed, local time.",
        "",
        "## Log",
        "",
    ]

    for (dep, arr) in sorted(directions, key=lambda k: (city.get(k[0], k[0]), city.get(k[1], k[1]))):
        route_legs = directions[(dep, arr)]
        route_legs.sort(key=lambda leg: (leg.callsign, leg.local_departure))
        by_flight: dict[str, list[Leg]] = defaultdict(list)
        for leg in route_legs:
            by_flight[leg.callsign].append(leg)

        first_date = min(leg.local_departure for leg in route_legs).date()
        days = [leg.local_departure.isoweekday() for leg in route_legs]
        type_codes = Counter(leg.type for leg in route_legs if leg.type).most_common()
        equipment = " / ".join(type_name(code) for code, _ in type_codes) or "—"

        lines.append(f"**{city.get(dep, dep)} – {city.get(arr, arr)}**  ")
        lines.append(f"*eff {first_date:%d}{MONTH_NAMES[first_date.month - 1]}{first_date:%y}* "
                     f"{frequency_text(days)} {equipment}  ")
        for flight_no in sorted(by_flight):
            flight_legs = by_flight[flight_no]
            flight_days = compress_days([leg.local_departure.isoweekday() for leg in flight_legs])
            dep_airport, arr_airport = flight_legs[0].origin, flight_legs[0].destination
            # the most-flown slot for this flight number: the habitual timing,
            # not one odd day
            dep_time, arr_time = Counter(
                (hhmm(leg.takeoff, leg.origin.tz), hhmm(leg.landing, leg.destination.tz))
                for leg in flight_legs
            ).most_common(1)[0][0]
            carry = day_marker(flight_legs[0].takeoff, flight_legs[0].landing,
                               dep_airport.tz, arr_airport.tz)
            code = (Counter(leg.type for leg in flight_legs if leg.type).most_common(1)
                    or [("", 0)])[0][0]
            name = flight_no if flight_no != "UNKNOWN" else "—"
            # a 3-letter code runs straight on from the time, as AeroRoutes writes
            # it; anything longer (an airport with no IATA code) gets a space so
            # the code and the clock cannot be read as one number
            dep_field = f"{dep}{dep_time}" if len(dep) == 3 else f"{dep} {dep_time}"
            arr_field = f"{arr_time}{carry}{arr}" if len(arr) == 3 else f"{arr_time}{carry} {arr}"
            lines.append(f"{name} {dep_field} – {arr_field} "
                         f"{code or '—'} {flight_days}")
        lines.append("")

    lines += [
        "## Route summary",
        "",
        "| route | flights | weekly | equipment | great-circle km | median air min |",
        "|---|---|---|---|---|---|",
    ]
    for (dep, arr) in sorted(directions, key=lambda k: -len(directions[k])):
        route_legs = directions[(dep, arr)]
        days = {leg.local_departure.isoweekday() for leg in route_legs}
        equipment = " / ".join(type_name(code) for code, _ in
                               Counter(leg.type for leg in route_legs if leg.type).most_common()) or "—"
        route_airports = route_legs[0]
        gc = gc_km.get(f"{dep}-{arr}") or round(great_circle_km(
            route_airports.origin.lat, route_airports.origin.lon,
            route_airports.destination.lat, route_airports.destination.lon))
        lines.append(
            f"| {dep}-{arr} | {len(route_legs)} | {len(days)} | {equipment} | {gc} | "
            f"{round(statistics.median(leg.minutes for leg in route_legs))} |"
        )
    lines.append("")

    lines += render_rotations(rotations)

    if partial:
        lines += [
            "## Track coverage",
            "",
            f"{len(partial)} of the {len(legs)} flights have a track that covers only part of",
            "the flight: the export starts after take-off, stops in the cruise, or both.",
            "They are still logged — the flight happened and its days are not in doubt.",
            "The route comes from the flight record; the times come from "
            + " and ".join(filter(None, [
                f"the movement board's actual times ({len(from_record)} flights)" if from_record else "",
                f"the board's scheduled times ({len(from_schedule)} flights)" if from_schedule else "",
                f"the partial track itself ({len(partial) - len(from_record) - len(from_schedule)} flights)"
                if len(partial) - len(from_record) - len(from_schedule) else "",
            ])) + ".",
            "",
            "| flight | date | logged as | times from | what the track covers |",
            "|---|---|---|---|---|",
        ]
        for leg in sorted(partial, key=lambda l: l.local_departure):
            note = leg.note or "track incomplete"
            note = note.replace("; filed as ", "; flight record says ")
            source = {"record": "board, actual", "schedule": "board, scheduled",
                      "track": "the track"}.get(leg.time_source, leg.time_source)
            lines.append(f"| {leg.callsign} | {leg.local_departure:%Y-%m-%d} | "
                         f"{leg.route} | {source} | {note} |")
        lines.append("")

    if discrepancies:
        lines += [
            "## Route discrepancies",
            "",
            "Sectors the aircraft flew under a through flight number, where the track",
            "shows a landing the flight record does not name. The log follows the track.",
            "",
            "| flight | date | logged as | flight record |",
            "|---|---|---|---|",
        ]
        for leg in sorted(discrepancies, key=lambda l: l.local_departure):
            filed = leg.note.split("filed as ")[-1].split(",")[0]
            lines.append(f"| {leg.callsign} | {leg.local_departure:%Y-%m-%d} | "
                         f"{leg.route} | {filed} |")
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

FLIGHT_COLUMNS = [
    "flight_date", "flight_no", "callsign", "registration", "aircraft_type",
    "origin", "destination", "takeoff_utc", "landing_utc",
    "takeoff_local", "landing_local", "airborne_min", "distance_km",
    "max_altitude_ft", "track_points", "track_gap_km", "track_complete",
    "time_source", "flight_id_hex", "track_file",
]


def write_flights(path: Path, legs: list[Leg]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(FLIGHT_COLUMNS)
        for leg in legs:
            writer.writerow([
                f"{leg.local_departure:%Y-%m-%d}",
                leg.callsign, leg.callsign, leg.registration, leg.type,
                leg.origin.code, leg.destination.code,
                leg.takeoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
                leg.landing.strftime("%Y-%m-%dT%H:%M:%SZ"),
                f"{leg.local_departure:%Y-%m-%dT%H:%M}",
                f"{leg.local_arrival:%Y-%m-%dT%H:%M}",
                leg.minutes, f"{leg.distance_km:.1f}",
                leg.max_altitude_ft if leg.max_altitude_ft is not None else "",
                leg.points, leg.gap_km or "",
                "yes" if leg.track_complete else "no", leg.time_source,
                leg.flight_id, leg.source,
            ])


def collect_tracks(outdir: Path, month: str, explicit: list[str]) -> list[Path]:
    if explicit:
        files: list[Path] = []
        for item in explicit:
            path = Path(item)
            if path.is_dir():
                files.extend(sorted(path.glob("*.csv")))
            elif any(ch in item for ch in "*?["):
                files.extend(sorted(Path(p) for p in glob.glob(item)))
            else:
                files.append(path)
        return files
    tracks_dir = outdir / "tracks"
    if tracks_dir.is_dir():
        return sorted(p for p in tracks_dir.glob("*.csv") if p.name != "manifest.csv")
    return sorted(Path(p) for p in glob.glob(str(outdir / f"fr24_tracks_{month}*.csv")))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--month", required=True, help="YYYY-MM, e.g. 2026-06")
    parser.add_argument("--track", action="append", default=[],
                        help="export file, folder or glob; defaults to archive/<month>/tracks/")
    parser.add_argument("--outdir", default=None, help="defaults to archive/<month>")
    parser.add_argument("--manifest", default=None,
                        help="defaults to archive/<month>/tracks/manifest.csv when present")
    args = parser.parse_args(argv)

    month = args.month
    datetime.strptime(month, "%Y-%m")  # validate
    outdir = Path(args.outdir) if args.outdir else ROOT / "archive" / month
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest) if args.manifest else outdir / "tracks" / "manifest.csv"

    files = collect_tracks(outdir, month, args.track)
    files = [f for f in files if f.exists()]
    if not files:
        print(f"no track export found in {outdir} (expected tracks/*.csv) — nothing to do",
              file=sys.stderr)
        return 1

    airports = load_airports()
    fleet = load_fleet()
    manifest = load_manifest(manifest_path)

    legs: list[Leg] = []
    sources: list[dict] = []
    empty: list[str] = []
    other_month = 0
    for path in files:
        meta = manifest.get(path.name, {})
        points = read_export(path)
        if not points:
            print(f"{path.name}: no usable track points", file=sys.stderr)
            continue
        file_legs = build_legs(points, airports, fleet, meta=meta, source=path.name)
        kept = [leg for leg in file_legs
                if leg.local_departure and f"{leg.local_departure:%Y-%m}" == month]
        other_month += len(file_legs) - len(kept)
        if not file_legs:
            empty.append(path.name)
        legs.extend(kept)
        sources.append({
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "track_points": len(points),
            "flight_id_hex": (meta.get("flight_id_hex") or "").strip(),
            "legs_in_month": len(kept),
        })

    if not legs:
        print("no flight legs could be rebuilt for this month", file=sys.stderr)
        return 1
    legs.sort(key=lambda leg: leg.takeoff)

    flights_path = outdir / f"flights_{month}.csv"
    rotations_path = outdir / f"rotations_{month}.csv"
    log_path = outdir / f"aeroroutes_{month}.md"
    sources_path = outdir / "sources.json"
    rotations = build_rotations(legs)
    write_flights(flights_path, legs)
    write_rotations(rotations_path, rotations)
    log_path.write_text(render_log(month, legs, load_gc_distances(), sources, rotations),
                        encoding="utf-8")
    sources_path.write_text(json.dumps({
        "month": month,
        "generator": "work/fr24_tracks.py",
        "flights_logged": len(legs),
        "legs_dropped_outside_month": other_month,
        # exports that held no leg: ground-only, or too little to place
        "exports_without_a_leg": empty,
        "sources": sources,
    }, indent=2) + "\n", encoding="utf-8")

    def show(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    print(f"{len(legs):,} flights, "
          f"{len({(l.origin.code, l.destination.code) for l in legs})} directional city pairs, "
          f"{sum(l.minutes for l in legs) / 60:,.1f} airborne hours")
    if other_month:
        print(f"{other_month} legs fell outside {month} and were left out")
    if empty:
        print(f"{len(empty)} exports held no usable leg: {', '.join(empty[:6])}"
              f"{' ...' if len(empty) > 6 else ''}")
    partial = [leg for leg in legs if not leg.track_complete]
    if partial:
        counts = Counter(leg.time_source for leg in partial)
        detail = ", ".join(f"{value} {source}" for source, value in counts.most_common())
        print(f"{len(partial)} flights have a partial track (times from: {detail})")
    broken = [rotation for rotation in rotations if not rotation.complete]
    if broken:
        hops = Counter(hop.route for rotation in broken for hop in rotation.hops)
        detail = ", ".join(f"{route} {n}" for route, n in hops.most_common(4))
        print(f"{len(broken)} of {len(rotations)} rotations have an untracked hop "
              f"({sum(hops.values())} hops: {detail})")
    else:
        print(f"all {len(rotations)} rotations are fully tracked")
    print(f"wrote {show(flights_path)}, {show(rotations_path)}, {show(log_path)} "
          f"and {show(sources_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
