# FR data (1).zip — which dates have no flights, checked against FTA

Checked 19 Oct 2026. Source A: `FR data (1).zip` (1,100 CSV track files).
Source B: Uganda Airlines FTA "Utilization Plans by Date" —
https://fta.ugandairlines.com/utilization-plans (pages 1–5 read in full, older pages spot-checked).

## Answer in one paragraph

Inside the period the FR export is actually collecting day by day
(**30 Aug – 16 Oct 2026**), **no date is completely empty except in effect
Saturday 10 Oct 2026**: that day has a single late-night inbound track and
none of the 20 legs the airline planned for it. The export ends on
**16 Oct**, so **17, 18 and 19 Oct have no FR flights at all** even though
FTA published plans for all three (20 Oct is also planned, but had not yet
flown when checked). Just before the run starts, **27 and 28 Aug 2026 are
completely empty**, and 30–31 Aug are only partial. Everything earlier in
the zip is stray one-off downloads, not a daily archive — FTA had a plan
for essentially every one of those days too.

## How the counting was done

- Every CSV in the zip was read; a flight's date is the **local (EAT,
  UTC+3) date of its first fix**, the same convention used elsewhere in
  this repo. Overnight inbounds can therefore sit on the evening before
  their FTA plan date — this matters for 10 Oct, below.
- 35 of the 1,100 files are **byte-identical duplicates** (`_1`, `-1`,
  ` (1)` suffixes etc.). After removing them: **1,065 unique tracks,
  1,016 of them Uganda Airlines (UR)**; the other 49 are foreign carriers
  (ET, QR, KL, TK…) downloaded incidentally and ignored for this check,
  since FTA only covers Uganda Airlines.
- FTA lists a utilization plan for **every single day from 23 Aug to
  20 Oct 2026** (verified page by page), plus one future plan for
  5 Dec 2026. Spot checks of older pages (Jul 2026, Mar 2026, Nov 2025,
  Aug 2025, Jun–Jul 2025) show the same daily pattern going back well
  beyond the FR data. So a date with an FTA plan but no FR track is a gap
  in the FR download, not a day the airline didn't fly. (FTA is a *plan*:
  individual legs can be marked CANCELLED — noted where relevant.)

## The dates with no (or effectively no) flights

| Date | Day | FTA plan | Unique UR tracks in FR (1) | What it means |
|---|---|---|---|---|
| 23 Aug 2026 | Sun | PUBLISHED | 0 | No flights. Before the export's daily run. |
| 24 Aug 2026 | Mon | AMENDED | 0 | No flights. |
| 25 Aug 2026 | Tue | AMENDED | 0 | No flights. |
| 26 Aug 2026 | Wed | PUBLISHED | 1 | Single stray track (UR361, 17:55) only. |
| **27 Aug 2026** | Thu | PUBLISHED | **0** | **No flights — airline planned a full day.** |
| **28 Aug 2026** | Fri | AMENDED | **0** | **No flights — airline planned a full day.** |
| 29 Aug 2026 | Sat | AMENDED | 1 | Single stray track (UR431, 22:38) only. |
| 30 Aug 2026 | Sun | AMENDED | 13 | **Partial** — FTA lists 29 legs (3 cancelled, so 26 operating); FR holds about half a day. First day of the run. |
| 31 Aug 2026 | Mon | AMENDED | 5 | **Mostly missing** — only evening tracks from 20:45 on (UR322, UR720, UR206, UR712, UR323). FTA lists 23 legs (UR200/UR201 cancelled, so 21 operating); the whole daytime bank is absent. |
| **10 Oct 2026** | Sat | AMENDED | **1** | **Effectively no flights** — see below. |
| **17 Oct 2026** | Sat | PUBLISHED | **0** | **No flights** — export has ended; FTA lists 21 legs (UR520/UR521 cancelled, 19 operating). |
| **18 Oct 2026** | Sun | PUBLISHED | **0** | **No flights** — after end of export. |
| **19 Oct 2026** | Mon | AMENDED | **0** | **No flights** — after end of export (day still in progress when checked). |
| 20 Oct 2026 | Tue | PUBLISHED | 0 | Planned but had not yet flown when checked — not yet a gap. |

The full day-by-day table for 23 Aug – 20 Oct 2026 is in
[`fr_data_1_date_coverage.csv`](fr_data_1_date_coverage.csv).

### 10 Oct 2026 in detail — the one real hole inside the run

FR holds exactly one track touching that date: **UR431 BOM–EBB**
(`UR431-4210f981.csv`), first fix over Mumbai 22:40 EAT on 10 Oct, landing
Entebbe 05:23 on 11 Oct. It is the return of 10 Oct's outbound UR430, so
it belongs to the day operationally — but **none of the 20 legs FTA
planned for 10 Oct itself was captured**:

UR720 HRE–EBB · UR722 EBB–HRE · UR722 HRE–LUN · UR722 LUN–EBB ·
UR520 EBB–MGQ · UR521 MGQ–EBB · UR120 EBB–JUB · UR121 JUB–EBB ·
UR322 EBB–DAR · UR323 DAR–EBB · UR200 EBB–NBO · UR201 NBO–EBB ·
UR208 EBB–NBO · UR111 LGW–EBB · UR430 EBB–BOM · UR903 LOS–EBB ·
UR710 EBB–JNB · UR711 JNB–EBB · UR720 EBB–LUN · UR720 LUN–HRE

(all shown SCHEDULED, none cancelled). Neighbouring days are normal —
24 tracks on 9 Oct, 25 on 11 Oct — so this is a one-day download hole,
not the airline standing down. **This whole day needs re-downloading
from Flightradar24.**

### Where the export ends

The last departing track is UR902 on 16 Oct (22:37 EAT); the last fix in
the whole zip is 03:17 EAT on 17 Oct, from that same flight. By departure
date, **17 Oct onwards has nothing**. 17–19 Oct are therefore "not yet
downloaded", not lost — but they will become a hole like 10 Oct if the
next FR pull doesn't reach back for them.

### Dates that are fine

Every date **1 Sep – 9 Oct and 11 – 16 Oct 2026** has flights
(13–28 unique UR tracks per day). No date in September is missing —
this agrees with the frozen September analysis in `UR SEPTEMBER 2026/`,
and the new zip additionally fills October up to the 16th.

## Everything before 23 Aug 2026 is stray downloads

The zip is cumulative and reaches back to a single track on 5 May 2025,
but before late August 2026 it was never a daily collection. Only these
dates have any UR tracks at all; **every other date in between has no
flights**, despite FTA publishing daily plans throughout:

2025: 5 May · 14, 27, 28 Jul · 31 Dec —
2026: 1 Jan · 30 Jan · 18, 19, 28 Feb · 1, 4, 7, 8, 12–16, 18–22 Mar

Compressed, the zero-flight ranges between the first (5 May 2025) and
last (16 Oct 2026) FR tracks are:

| Zero-flight range | Length |
|---|---|
| 6 May – 13 Jul 2025 | 69 days |
| 15 – 26 Jul 2025 | 12 days |
| 29 Jul – 30 Dec 2025 | 155 days |
| 2 – 29 Jan 2026 | 28 days |
| 31 Jan – 17 Feb 2026 | 18 days |
| 20 – 27 Feb 2026 | 8 days |
| 2 – 3 Mar 2026 | 2 days |
| 5 – 6 Mar 2026 | 2 days |
| 9 – 11 Mar 2026 | 3 days |
| 17 Mar 2026 | 1 day |
| 23 Mar – 25 Aug 2026 | 156 days |
| 27 – 28 Aug 2026 | 2 days |

456 of the 530 calendar days spanned by the zip have no UR flights.
These shouldn't be read as missing data to chase — nothing suggests a
daily download was ever attempted for them. They only become "gaps" if
the aim is a complete FTA-vs-FR history back to 2025, in which case
effectively the whole period before 30 Aug 2026 needs downloading.

## What to re-download from Flightradar24, in priority order

1. **Sat 10 Oct 2026 — the whole day** (20 planned legs, only the
   late BOM–EBB inbound captured).
2. **17 Oct 2026 onwards** — planned by FTA, nothing in FR yet.
3. **Mon 31 Aug 2026 daytime** (only 20:45-onwards captured) and
   **Sun 30 Aug 2026** (about half the operating legs captured).
4. **27–28 Aug 2026** — if coverage is wanted from before the daily run
   started; both days fully planned, both empty in FR.

## Caveats

- FTA is the airline's *plan*, published/amended in advance; a planned
  leg is strong evidence of intent, and the statuses above note the
  cancellations FTA itself declares, but FTA alone doesn't prove a leg
  operated. For 10 Oct, the surrounding days' FR tracks (aircraft
  rotations continuing normally on 11 Oct) corroborate that flying
  happened.
- Counts here are **tracks starting that EAT date**. A track is one
  Flightradar24 flight recording; a handful of flights transmit under
  non-UR callsigns (e.g. the AF523 Hoima runs) but are filed under UR
  flight numbers in the zip, and are counted here.
- `FR data (1).zip` supersedes the plain `FR data.zip` in this repo
  (63 tracks newer, extending coverage from 14 Oct to 16 Oct), which is
  why this check was run against `(1)`.

*Method: parsed all 1,100 CSVs, deduplicated byte-identical files,
dated each unique track by first fix in EAT, tallied UR tracks per date,
and compared against the FTA utilization-plan index (pages 1–5 =
23 Aug–20 Oct 2026, all dates present) and individual FTA day plans for
30 Aug, 31 Aug, 10 Oct and 17 Oct 2026.*
