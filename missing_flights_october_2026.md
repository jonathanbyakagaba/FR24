# Which flights are missing in October 2026

FR `FR data (1).zip` (unique tracks, dated by first fix, EAT) vs Uganda
Airlines FTA utilization plans, 1–20 Oct 2026 — every FTA day plan read
in full and matched leg by leg (flight number + routing + time, allowing
overnight legs to fall on the neighbouring date). Legs FTA marked
CANCELLED are not counted as missing.

## Summary

October is mostly good — until it isn't. **1, 2, 4, 6, 7 and 14 Oct are
complete**, and most other days are short only one or two legs, usually
the outstation middle sector of a triangle. Then **10 Oct is missing its
entire day (20 legs)**, and **17–19 Oct are missing everything** because
the FR export ends on 16 Oct.

| Date | Missing flights |
|---|---|
| Thu 01 Oct | — none — |
| Fri 02 Oct | — none — |
| Sat 03 Oct | UR722 HRE–LUN · UR720 LUN–HRE |
| Sun 04 Oct | — none — |
| Mon 05 Oct | UR720 LUN–HRE |
| Tue 06 Oct | — none — |
| Wed 07 Oct | — none — |
| Thu 08 Oct | UR343 MBA–EBB |
| Fri 09 Oct | UR334 ZNZ–JRO · UR720 LUN–HRE · UR111 LGW–EBB |
| **Sat 10 Oct** | **all 20 planned legs — see below** |
| Sun 11 Oct | UR334 ZNZ–JRO · UR720 LUN–HRE · UR343 MBA–EBB · UR111 LGW–EBB |
| Mon 12 Oct | UR111 LGW–EBB |
| Tue 13 Oct | UR323 DAR–EBB (23:50 departure) |
| Wed 14 Oct | — none — |
| Thu 15 Oct | UR722 HRE–LUN · UR343 MBA–EBB |
| Fri 16 Oct | UR720 LUN–HRE · UR111 LGW–EBB |
| **Sat 17 Oct** | **all 19 operating legs (export ended)** |
| **Sun 18 Oct** | **all 29 legs (export ended)** |
| **Mon 19 Oct** | **all 20 legs (export ended)** |
| Tue 20 Oct | all 21 legs planned, but had not yet flown when checked |

That is 37 missing legs on 1–16 Oct (20 of them on 10 Oct alone), plus
68 more on 17–19 Oct that simply haven't been downloaded yet.

## The recurring pattern (1–9 and 11–16 Oct, excluding 10 Oct)

Almost every gap is one of three things:

1. **The middle sector of a triangle** — the outstation-to-outstation
   hop that this archive keeps losing (the same hole documented for
   September in `UR SEPTEMBER 2026/`):
   - UR722 **HRE–LUN** on 03 and 15 Oct
   - UR720 **LUN–HRE** on 03, 05, 09, 11 and 16 Oct
   - UR334 **ZNZ–JRO** on 09 and 11 Oct
   
   In every case FR holds the two Entebbe legs either side of the
   missing hop (e.g. 11 Oct: UR334 EBB–ZNZ 09:48 and JRO–EBB 14:25 are
   present, ZNZ–JRO between them is not), so the flight certainly
   operated — the track just wasn't downloaded.

2. **UR343 MBA–EBB**, the late Mombasa return, on 08, 11 and 15 Oct —
   the outbound UR342 EBB–MBA is present each time.

3. **UR111 LGW–EBB** on 09, 11, 12 and 16 Oct (the 16 Oct one arrives
   that morning; a further UR111 departing London on the evening of
   16 Oct is also absent). The UR110 outbound to London is present on
   each of those days; the overnight return is not in the zip. Note FTA
   lists the UR111 on the *arrival* day's plan, so it is counted here
   on that day even though it departs London the previous evening.

Single one-off: **UR323 DAR–EBB** (23:50) on 13 Oct.

Two things that look like gaps but aren't: the split tracks on 11 Oct
(UR323 DAR–EBB, filed as DAR–NBO + NBO–EBB — FTA shows it as the delayed
UR323D via Nairobi) and 13 Oct (UR121 JUB–EBB via NBO) are present,
just recorded in two files; and several legs FTA lists on two
consecutive day plans (overnight inbounds) have only been counted once.

## Sat 10 Oct — the whole day (20 legs)

The only FR track touching the date is UR431 BOM–EBB, first fix over
Mumbai 22:40 EAT, landing Entebbe 05:23 on 11 Oct — the return of the
previous rotation. None of the day's own planned legs was captured:

UR720 HRE–EBB · UR722 EBB–HRE · UR722 HRE–LUN · UR722 LUN–EBB ·
UR520 EBB–MGQ · UR521 MGQ–EBB · UR120 EBB–JUB · UR121 JUB–EBB ·
UR322 EBB–DAR · UR323 DAR–EBB · UR200 EBB–NBO · UR201 NBO–EBB ·
UR208 EBB–NBO · UR111 LGW–EBB · UR430 EBB–BOM · UR903 LOS–EBB ·
UR710 EBB–JNB · UR711 JNB–EBB · UR720 EBB–LUN · UR720 LUN–HRE

(all SCHEDULED in FTA, none cancelled). This day needs a complete
re-download from Flightradar24.

## 17–19 Oct — everything (export ended)

The last departing track in the zip is UR902 on 16 Oct (22:37 EAT);
the last fix is 03:17 on 17 Oct from that flight. FTA plans exist for
all three days, so every leg below is missing from FR — currently
"not yet downloaded" rather than lost, provided the next pull reaches
back for them.

**Sat 17 Oct — 19 operating legs** (UR520/UR521 were CANCELLED):
UR720 HRE–EBB · UR722 EBB–HRE · UR722 HRE–LUN · UR722 LUN–EBB ·
UR323 DAR–EBB · UR208 EBB–NBO · UR200 EBB–NBO · UR201 NBO–EBB ·
UR120 EBB–JUB · UR121 JUB–EBB · UR322 EBB–DAR · UR111 LGW–EBB ·
UR430 EBB–BOM · UR431 BOM–EBB · UR903 LOS–EBB · UR710 EBB–JNB ·
UR711 JNB–EBB · UR720 EBB–LUN · UR720 LUN–HRE
(plus UR720 LUN–HRE's onward UR720 HRE–EBB, and the UR720 LUN–HRE of
16 Oct above, whose return falls in this window)

**Sun 18 Oct — 29 legs:**
UR200 EBB–NBO · UR201 NBO–EBB · UR120 EBB–JUB · UR121 JUB–EBB ·
UR342 EBB–MBA · UR343 MBA–EBB · UR209 NBO–EBB · UR520 EBB–MGQ ·
UR521 MGQ–EBB · UR320 EBB–DAR · UR321 DAR–EBB · UR206 EBB–NBO ·
UR207 NBO–EBB · UR208 EBB–NBO · UR323 DAR–EBB · UR334 EBB–ZNZ ·
UR334 ZNZ–JRO · UR334 JRO–EBB · UR360 EBB–BJM · UR361 BJM–EBB ·
UR720 EBB–LUN · UR720 LUN–HRE · UR720 HRE–EBB · UR431 BOM–EBB ·
UR110 EBB–LGW · UR111 LGW–EBB · UR900 EBB–LOS · UR901 LOS–EBB ·
UR712 EBB–JNB

**Mon 19 Oct — 20 legs:**
UR122 EBB–JUB · UR123 JUB–EBB · UR360 EBB–BJM · UR361 BJM–EBB ·
UR208 EBB–NBO · UR209 NBO–EBB · UR200 EBB–NBO · UR201 NBO–EBB ·
UR320 EBB–DAR · UR321 DAR–EBB · UR720 HRE–EBB · UR710 EBB–JNB ·
UR711 JNB–EBB · UR720 EBB–LUN · UR720 LUN–HRE · UR111 LGW–EBB ·
UR713 JNB–EBB · UR900 EBB–LOS · UR901 LOS–EBB · UR712 EBB–JNB

**Tue 20 Oct — 21 legs planned** (UR209, UR320/321, UR206/207,
UR520/521, UR360/361, UR720 HRE–EBB, UR200/201, UR120/121, UR110/111,
UR713, UR722 ×3, UR712): not yet flown when checked on 19 Oct, so not
counted as missing yet — but FR will need a pull after the fact to get it.

## What to re-download, in priority order

1. **10 Oct 2026, whole day** — 20 legs, the only true hole inside
   the downloaded period.
2. **17 Oct onwards** — 68 legs across 17–19 Oct and counting.
3. **The triangle middle sectors**: UR720 LUN–HRE (03, 05, 09, 11,
   16 Oct), UR722 HRE–LUN (03, 15 Oct), UR334 ZNZ–JRO (09, 11 Oct).
4. **UR343 MBA–EBB** (08, 11, 15 Oct), **UR111 LGW–EBB**
   (09, 11, 12, 16 Oct) and **UR323 DAR–EBB** (13 Oct).

*Method: all 1,100 FR CSVs parsed and deduplicated (1,065 unique
tracks); each track's route inferred from first/last fix; FTA day plans
for 1–20 Oct 2026 read in full from
fta.ugandairlines.com/utilization-plans and matched by flight, routing
and scheduled time within a ±1 day window for overnight legs.*
