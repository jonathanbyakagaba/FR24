# SIDs and STARs — are they published, and can this dataset use them?

*Researched and written 2026-10-20. `procedures.csv` (same folder) is
the seed inventory built from what is publicly verifiable today.*

## Short answer

**Yes, they are published — but not in one place, and not in a form we
can simply download into this repository.** Every airport in the
network has SIDs/STARs in its **national AIP, section AD 2.24** (charts)
with the coding tables alongside. What does *not* exist publicly is a
free, redistributable, machine-readable (ARINC 424) procedure database
for our airports. The one fully open coded dataset — the FAA's CIFP —
is US-only (public domain, but no use here). The global coded databases
(Jeppesen NavData, Navigraph) are commercial products whose licences
**prohibit redistribution**, so they cannot be committed to this repo.

## What publication/access actually looks like at our stations
*(each source below was checked on 2026-10-20)*

| Station | Published? | Public access | How we know |
|---|---|---|---|
| **EBB / HUEN** | Yes — RNAV (GNSS) SID/STAR set for RWY 17/35 | **Subscription.** UCAA eAIP portal (aim.caa.co.ug/eAIP) returns 401; UCAA sells the AIP annually | Uganda National Aviation Safety Plan 2022-25 ("Several SIDs and STARs were developed for the GNSS/RNAV departures/arrivals for Entebbe"); NOTAM A0194/26 cites AD 2-HUEN-2-1 |
| **NBO / HKJK, MBA / HKMO** | Yes | **Purchase/subscription** portal (eaip.kcaa.or.ke); "Valid NOTAM Lists free", eAIP paid | KCAA AIM pages |
| **LGW / EGKK** | Yes, full set | **Free** — UK NATS AIS eAIP, current, no account | NATS AIS |
| **BOM / VABB** | Yes — RNAV-1 (GNSS) SIDs & STARs effective **1 Oct 2026** | **Free** — India AAI eAIP | NOTAM 804/26 (AIP SUP 121/2026) |
| **JNB / FAOR** | Yes — named RNAV SIDs/STARs | AIP via SA CAA/ATNS subscription channels | NOTAMs name them: SIDs EGMEN 1C/1D, APDAK 1D, GEROX 1C; STARs AVAGO/NIBEX/OKPIT/UNPOM (see `procedures.csv`) |
| **DAR, ZNZ, JRO** | Yes (ZNZ IAP charts amended WEF 29 Oct 2026) | TCAA AIS, subscription/EAD channels | NOTAM 209/26 names HTZA RNP 18/36, ILS Y/Z 18 |
| **LOS, MGQ, JUB, HRE, LUN, BJM** | Yes, in their national AIPs | Mostly subscription/national-AIS only; no free current portal found. | ICAO Annex 15 obligation; NOTAM series active for LOS/MGQ |

Two important consequences:

1. **The NOTAMs already leak the procedure structure.** Suspensions and
   amendments name procedures, runways and entry/exit fixes — that's
   how `procedures.csv` got seeded (19 rows) without touching a paywall.
   JNB currently *requires* radar vectoring off its STARs (NOTAMs
   3896-3900/26) and has suspended its RNAV SIDs (3686/26) — any
   track-vs-procedure analysis at JNB must use these as ground truth
   for Sep 29 onwards.
2. **Procedures are AIRAC-versioned** (28-day cycles). A SID encoded
   from the December AIP must not be scored against September tracks;
   `procedures.csv` therefore carries a status/effective column, and
   BOM's set literally changed on 1 Oct 2026 mid-dataset.

## The realistic route to using them here

**Through the airline's own AIP access (recommended).** As the operator
you already hold (or can hold) the UCAA/KCAA/etc. AIP subscriptions and
the Jeppesen/Navigraph company navdata. Facts from a chart — procedure
name, runway, transition fixes, waypoint sequence, altitude/speed
constraints — can be transcribed into `procedures.csv` (facts aren't
redistributable *data products*, and this stays an internal dataset).
Encode **EBB first** (both runway ends, both directions), then NBO and
JNB. Roughly an hour per airport from the AD 2.24 charts.

Once encoded, the tracks support analyses nothing else in this repo
can do:

* **Which SID/STAR was actually flown** — match each track's first/last
  fixes to procedure waypoint sequences (the FR24 tracks carry the
  positions; Entebbe's terminal fixes like EL001/EL005/EL007 are in
  open waypoint lists, so clustering works even before transcription).
* **Vectoring & shortcut detection** — track miles vs procedure miles
  per departure/arrival; where ATC habitually cuts the corner (JNB is
  *instructed* to right now), and what that's worth in minutes/fuel.
* **Profile conformance** — climb/descent vs published constraints:
  continuous-climb/descent rates, level-offs, and where they cost fuel.
* **Procedure-change before/after** — e.g. BOM's new RNAV-1 set from
  1 Oct 2026: did UR430/431 track shapes and block times actually
  change on 1 October?

**Open-data-only fallback:** for EGKK and VABB the free eAIPs let us
encode today with clean provenance. For the rest, unofficial chart
mirrors (ChartFox, VATSIM, aip.aero) are fine to *read* but their
terms don't allow republishing scans in git — link, don't copy.

## Bottom line

Published: yes, everywhere. Free and downloadable: only the UK and
India sets. Usable in this dataset: yes — starting with the seeded
`procedures.csv`, and properly once the EBB/NBO/JNB procedure paths are
transcribed from the AIP copies the airline is entitled to. That
transcription is the single unlock; I've left the schema ready for it.
