# Weather analysis — 1–22 October 2026 (rebuilt 2026-10-23)

Source: Iowa State IEM ASOS extract for **HUEN (Entebbe)**, routine reports,
1–22 Oct 2026 UTC, archived in `metar/HUEN_202610_part0–4.csv` and joined to
each flight's takeoff/landing by `work/build_conditions.py` (nearest report
within ±75 min). Per-flight values are in `flight_conditions.csv`.

METAR was retrieved for Entebbe only in this rebuild (see SUPPORTING.md for
how to add the outstations). 436 of 473 October flights have an Entebbe end
with a matched report; the outstation end is blank in
`flight_conditions.csv`. The frozen build's weather file used its own,
now-lost METAR archive, so figures are not comparable row-by-row.

## What 1–22 October looked like at Entebbe

- **A wet, thundery fortnight.** TS/TSRA appears at 15 flight-ends and rain
  codes at 24 more; the archive shows TSRA episodes on 3, 5, 10–12 and
  16–20 Oct, including a 30 kt gust at 19:00Z on 6 Oct and visibility
  down to 3.11 mi in the 16 Oct 23:00Z and 20 Oct 02:00Z TSRA cells;
  thunder returned early on 22 Oct.
- **Runway wind favour:** headwind component ≥ −2 kt on the runway used in
  343 of 436 scored Entebbe ends (79%); 93 ends (21%) had a >2 kt tailwind
  component, predominantly in light-and-variable overnight conditions.
- Daytime southerlies (160–190°, 8–16 kt) remain the pattern, with northerly
  drainage flow overnight — the same regime as September.

## Caveats

- Conditions are the *nearest routine report*, not a SPECI; fast-moving
  cells can sit between reports.
- Outstation weather is not in this rebuild; `work/build_conditions.py`
  picks up any additional station extract dropped into `metar/`.
