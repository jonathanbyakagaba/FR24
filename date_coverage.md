# Which dates are in the export — and which are unfinished

The archive now runs **01 Sep – 30 Sep** — 30 consecutive days, 802 tracks, 610 logged flights. Every day is present; the question is which days are *complete*.

**The download ends at 23:31 local on 03 Oct** (2026-10-03 20:31:52Z UTC) — the last fix in the archive. Whatever flew after that is not in this export yet, which is past the end of 30 Sep, the last logged day, so that day runs to its normal end, and a rotation still in the air at the cut is marked *pending* instead of missing.

Three kinds of evidence, kept apart because they mean different things:

* **app-confirmed missing** — a per-tail app page shows the leg for that date and the
  export has no track for it. Independent evidence: the export is short a flight.
* **rotation hole** — a triangle rotation left Entebbe and came back, but a leg in between
  is not in the export. The chain is what proves it, so it is a hole in a rotation rather
  than a flight confirmed to have flown.

* **tracked, but not logged** — the export holds the track and the log has no leg for it,
  because the callsign it was transmitted under fails the log's gate. Nothing needs
  fetching; it is a question for the log. **6 legs
  this month** sit in that category, all of them the Hoima runs, confirmed by the
  operator on 2 Oct 2026 as the `UR523` service, flown under the `AF523` callsign.

---

## Every date at a glance

| date | day | tracks | flights | rotation holes | app-confirmed missing | pending at cut | verdict |
|---|---|---|---|---|---|---|---|
| 01 Sep | Tue | 17 | 17 | — | — | — | **complete** |
| 02 Sep | Wed | 24 | 22 | — | — | — | **complete** |
| 03 Sep | Thu | 15 | 14 | — | — | — | **complete** |
| 04 Sep | Fri | 25 | 26 | 1 | — | — | **partial** |
| 05 Sep | Sat | 21 | 19 | — | — | — | **complete** |
| 06 Sep | Sun | 26 | 28 | 1 | — | — | **partial** |
| 07 Sep | Mon | 23 | 23 | — | — | — | **complete** |
| 08 Sep | Tue | 19 | 21 | — | — | — | **complete** |
| 09 Sep | Wed | 21 | 19 | 1 | — | — | **partial** |
| 10 Sep | Thu | 15 | 15 | — | — | — | **complete** |
| 11 Sep | Fri | 26 | 26 | — | — | — | **complete** |
| 12 Sep | Sat | 22 | 18 | — | — | — | **complete** |
| 13 Sep | Sun | 27 | 30 | — | — | — | **complete** |
| 14 Sep | Mon | 16 | 18 | — | — | — | **complete** |
| 15 Sep | Tue | 18 | 18 | — | 1 | — | **partial** |
| 16 Sep | Wed | 18 | 16 | 1 | 3 | — | **partial** |
| 17 Sep | Thu | 13 | 13 | — | 1 | — | **partial** |
| 18 Sep | Fri | 23 | 22 | 2 | 2 | — | **partial** |
| 19 Sep | Sat | 17 | 15 | 1 | — | — | **partial** |
| 20 Sep | Sun | 19 | 21 | 1 | 3 | — | **partial** |
| 21 Sep | Mon | 19 | 19 | 1 | 1 | — | **partial** |
| 22 Sep | Tue | 17 | 19 | 1 | — | — | **partial** |
| 23 Sep | Wed | 23 | 21 | — | — | — | **complete** |
| 24 Sep | Thu | 16 | 15 | — | — | — | **complete** |
| 25 Sep | Fri | 29 | 28 | — | — | — | **complete** |
| 26 Sep | Sat | 21 | 18 | — | — | — | **complete** |
| 27 Sep | Sun | 26 | 24 | 2 | 1 | — | **partial** |
| 28 Sep | Mon | 22 | 23 | 1 | — | — | **partial** |
| 29 Sep | Tue | 22 | 22 | — | 1 | — | **partial** |
| 30 Sep | Wed | 25 | 20 | — | — | — | **complete** |

**16 of 30 days are complete.** The other 14 are set out below with exactly what each is short, along with any rotation that was still in the air at the cut. No date is missing and every complete day runs to the normal end of that weekday's evening bank.

---

## The unfinished dates, and what each is missing

### 04 Sep (Fri) — 26 flights, 25 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).

### 06 Sep (Sun) — 28 flights, 26 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).

### 09 Sep (Wed) — 19 flights, 21 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD722** — missing HRE–LUN (the export holds EBB–HRE, LUN–EBB).

### 15 Sep (Tue) — 18 flights, 18 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR209 | 5X-KOB | NBO–EBB | green | 03 Sep, 04 Sep, 06 Sep, 07 Sep… |

### 16 Sep (Wed) — 16 flights, 18 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR322 | 5X-EQU | EBB–DAR | red | 02 Sep, 03 Sep, 04 Sep, 05 Sep… |
| UR334 | 5X-KOB | ZNZ–JRO | green | 02 Sep, 04 Sep, 06 Sep, 09 Sep… |
| UR711 | 5X-KDP | JNB–EBB | red | 02 Sep, 04 Sep, 05 Sep, 07 Sep… |

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD334** — missing ZNZ–JRO (the export holds EBB–ZNZ, JRO–EBB).

### 17 Sep (Thu) — 13 flights, 13 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR720 | ET-APL | LUN–HRE | amber | 05 Sep, 07 Sep, 11 Sep, 13 Sep… |

### 18 Sep (Fri) — 22 flights, 23 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR334 | 5X-KDP | ZNZ–JRO | green | 02 Sep, 04 Sep, 06 Sep, 09 Sep… |
| UR720 | 5X-KDP | LUN–HRE | green | 05 Sep, 07 Sep, 11 Sep, 13 Sep… |

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD334** — missing ZNZ–JRO (the export holds EBB–ZNZ, JRO–EBB).
* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).

### 19 Sep (Sat) — 15 flights, 17 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing HRE–EBB (the export holds EBB–LUN, LUN–HRE).

### 20 Sep (Sun) — 21 flights, 19 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR121 | 5X-KDP | JUB–EBB | grey | 02 Sep, 03 Sep, 04 Sep, 05 Sep… |
| UR334 | 5X-KOB | ZNZ–JRO | red | 02 Sep, 04 Sep, 06 Sep, 09 Sep… |
| UR334 | 5X-KOB | EBB–ZNZ | red | 02 Sep, 04 Sep, 06 Sep, 09 Sep… |

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).

### 21 Sep (Mon) — 19 flights, 19 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR720 | 5X-KOB | LUN–HRE | green | 05 Sep, 07 Sep, 11 Sep, 13 Sep… |

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).

### 22 Sep (Tue) — 19 flights, 17 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD722** — missing HRE–LUN (the export holds EBB–HRE, LUN–EBB).

### 27 Sep (Sun) — 24 flights, 26 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR334 | 5X-KDP | ZNZ–JRO | green | 02 Sep, 04 Sep, 06 Sep, 09 Sep… |

**Tracked, but not in the log** — the export holds these tracks; they are absent from the log because the callsign they were transmitted under fails the gate, so the day is not short of a flight:

| flight | tail | sector | app status | transmitted as |
|---|---|---|---|---|
| UR523 | 5X-EQU | UG-0013–EBB | grey | AF523 |
| UR523 | 5X-EQU | EBB–EBB | grey | AF523 |
| UR523 | 5X-EQU | EBB–UG-0013 | grey | AF523 |

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD334** — missing ZNZ–JRO (the export holds EBB–ZNZ, JRO–EBB).
* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).

### 28 Sep (Mon) — 23 flights, 22 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing HRE–EBB (the export holds EBB–LUN, LUN–HRE).

### 29 Sep (Tue) — 22 flights, 22 tracks

**Missing, app-confirmed** (the app lists the leg, the export has no track):

| flight | tail | sector | app status | also flown on |
|---|---|---|---|---|
| UR209 | 5X-EQU | NBO–EBB | green | 03 Sep, 04 Sep, 06 Sep, 07 Sep… |

**Tracked, but not in the log** — the export holds these tracks; they are absent from the log because the callsign they were transmitted under fails the gate, so the day is not short of a flight:

| flight | tail | sector | app status | transmitted as |
|---|---|---|---|---|
| UR523 | 5X-KDP | EBB–UG-0013 | grey | AF523 |

**App rows that are not missing flights** — the aircraft's movement that day is already in the export, as two logged hops under a suffixed callsign, so the app row is a through-label rather than a flight to fetch:

| flight | tail | sector as the app labels it | the export holds |
|---|---|---|---|
| UR720 | 5X-KOB | HRE–EBB | HRE→NBO + NBO→EBB |

---

## The triangle route flights

Three rotations run through the month — `UGD720` Entebbe→Lusaka→Harare→Entebbe, `UGD722` Entebbe→Harare→Lusaka→Entebbe and `UGD334` Entebbe→Zanzibar→Kilimanjaro→Entebbe. The export carries the Entebbe legs almost every time they fly; the **middle sector, the hop between the two outstations, is the recurring gap** — 11 of the 48 rotations found are missing it, and that is the single largest hole in the archive.

| rotation | chain | rotations | complete | no middle sector | no return leg |
|---|---|---|---|---|---|
| UGD720 | `EBB → LUN → HRE → EBB` | 17 | 7 | 6 | 2 |
| UGD722 | `EBB → HRE → LUN → EBB` | 18 | 14 | 2 | 0 |
| UGD334 | `EBB → ZNZ → JRO → EBB` | 13 | 9 | 3 | 0 |

### The rotation leaving Entebbe each day

| date | day | UGD720 | UGD722 | UGD334 |
|---|---|---|---|---|
| 01 Sep | Tue | only HRE–EBB | complete | — |
| 02 Sep | Wed | — | complete | complete |
| 03 Sep | Thu | — | complete | — |
| 04 Sep | Fri | **missing LUN–HRE** | — | complete |
| 05 Sep | Sat | complete | complete | — |
| 06 Sep | Sun | **missing LUN–HRE** | — | complete |
| 07 Sep | Mon | complete | — | — |
| 08 Sep | Tue | — | complete | — |
| 09 Sep | Wed | — | **missing HRE–LUN** | complete |
| 10 Sep | Thu | — | complete | — |
| 11 Sep | Fri | complete | — | complete |
| 12 Sep | Sat | complete | complete | — |
| 13 Sep | Sun | complete | — | complete |
| 14 Sep | Mon | — | — | — |
| 15 Sep | Tue | — | only LUN–EBB | — |
| 16 Sep | Wed | — | complete | **missing ZNZ–JRO** |
| 17 Sep | Thu | — | complete | — |
| 18 Sep | Fri | **missing LUN–HRE** | — | **missing ZNZ–JRO** |
| 19 Sep | Sat | **missing HRE–EBB** | — | — |
| 20 Sep | Sun | **missing LUN–HRE** | — | only JRO–EBB |
| 21 Sep | Mon | **missing LUN–HRE** | — | — |
| 22 Sep | Tue | — | **missing HRE–LUN** | — |
| 23 Sep | Wed | — | complete | complete |
| 24 Sep | Thu | — | complete | — |
| 25 Sep | Fri | complete | — | complete |
| 26 Sep | Sat | complete | complete | — |
| 27 Sep | Sun | **missing LUN–HRE** | — | **missing ZNZ–JRO** |
| 28 Sep | Mon | **missing HRE–EBB** | — | — |
| 29 Sep | Tue | only HRE–NBO | complete | — |
| 30 Sep | Wed | — | complete | complete |

A dash means no rotation of that flight left Entebbe that day — the 720 and 722 alternate rather than running daily, and `UGD334` flies a few days a week. Rows marked `only …` are single legs whose partners fall outside the month or are themselves missing.

---

## What to ask for

1. **11 missing middle sectors** — the outstation-to-outstation hop, in rotations whose other legs are all in the export.
2. **2 missing return legs** — a rotation left Entebbe and the leg home is absent.
3. **The 13 legs the app confirms but the export does not hold**, listed date by date above.
   (Also not counted: **1 app row(s)** whose sector the app labels as one leg while the export holds the same aircraft's two hops that day, listed above as "not missing flights".)
   (Not counted there: **6 legs** the app lists which the export *does* hold, under a callsign the log does not accept. They are filed above as "tracked, but not logged" — a question for the log, not a fetch request.)
4. **App pages from 01 Oct on**, so the days after the capture can be checked against a record as well as against the rotation pattern. The pages currently stop at 30 Sep.
