# flight paths

One CSV per flight, as Flightradar24 recorded it: `Timestamp,UTC,Callsign,Position,Altitude,Speed,Direction`, positions as `lat,lon`, altitudes and speeds in feet and knots, times in UTC. Names are `<flight>-<fr24 track id>.csv` (a bare `<id>.csv` is a capture whose flight number the listing did not carry).

`INDEX.csv` is the table of contents: 1108 files, 33,821,135 bytes, newest observation last in each row. The build writes these files from `FR data.zip` and from each night's capture — `python3 tools/publish_paths.py` — and the archive stays the input to the analysis, which reads it through `work/repo_layout.py`.
