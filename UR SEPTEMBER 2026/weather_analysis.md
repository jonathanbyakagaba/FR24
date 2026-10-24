# Weather analysis — September 2026 (rebuilt 2026-10-20)

Source: Iowa State IEM ASOS extract for **HUEN (Entebbe)**, routine reports,
1–30 Sep 2026 UTC, archived in `metar/HUEN_202609_part0–4.csv` and joined to
each flight's takeoff/landing by `work/build_conditions.py` (nearest report
within ±75 min). Per-flight values are in `flight_conditions.csv`.

METAR was retrieved for Entebbe only in this rebuild (see SUPPORTING.md for
how to add the outstations). Every flight with an Entebbe end — 594 of 640
September flights — has real conditions at that end; the outstation
end is blank in `flight_conditions.csv`. The frozen build's weather file was
based on its own, now-lost METAR archive, so figures are not comparable
row-by-row.

## What September looked like at Entebbe

- **Thunderstorms were a regular afternoon/overnight feature.** 20 flights
  had TS/TSRA reported at their Entebbe end (10 TSRA, 7 TS, 3 −TSRA report
  ends), with further rain-only reports (RA/−RA/DZ at 12 flight-ends). The
  wettest spells in the archive: early hours of 8, 14, 17, 27 and 29 Sep
  (TSRA with visibility down to 1.24 mi / ~2 km at 04:00Z on 29 Sep).
- **Winds were light.** The prevailing daytime flow is southerly (160–190°,
  8–16 kt) off Lake Victoria, veering northerly and calm overnight. The
  strongest routine report in the month is 18 kt (several afternoons); one
  25 kt gust (11 Sep 05:00Z, TSRA) and one 30 kt gust (in October's series).
- **Runway wind favour:** at the Entebbe end, the wind favoured the runway
  in use (headwind component ≥ −2 kt) in 482 of 596 scored ends (81%); 114
  ends (19%) had a >2 kt tailwind component on the runway used — almost all
  light-wind cases where either direction is workable.
- Visibility was ≥6.21 mi (10 km) in the great majority of reports; sub-5 mi
  visibility occurs almost exclusively inside TSRA cells.

## Caveats

- Conditions are the *nearest routine report*, not a SPECI; fast-moving cells
  can sit between reports.
- One archived report (26 Sep 20:00Z) carries a 34 °C temperature that is
  inconsistent with its neighbours (22–24 °C) — left as retrieved from IEM.
- Outstation weather (NBO, DAR, JNB, LUN, HRE…) is not in this rebuild;
  `work/build_conditions.py` picks up any additional station extract dropped
  into `metar/`.
