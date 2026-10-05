# Which dates are in the export — and which are unfinished

The archive now runs **01 Oct – 05 Oct** — 5 consecutive days, 826 tracks, 82 logged flights. Every day is present; the question is which days are *complete*.

**The download ends at 05:23 local on 05 Oct** (2026-10-05 02:23:07Z UTC) — the last fix in the archive. Whatever flew after that is not in this export yet, so the final day is a stub rather than a finished day, and a rotation still in the air at the cut is marked *pending* instead of missing.

Three kinds of evidence, kept apart because they mean different things:

* **app-confirmed missing** — a per-tail app page shows the leg for that date and the
  export has no track for it. Independent evidence: the export is short a flight.
* **rotation hole** — a triangle rotation left Entebbe and came back, but a leg in between
  is not in the export. The chain is what proves it, so it is a hole in a rotation rather
  than a flight confirmed to have flown.

* **tracked, but not logged** — the export holds the track and the log has no leg for it,
  because the callsign it was transmitted under fails the log's gate. Nothing needs
  fetching; it is a question for the log. **0 legs
  this month** sit in that category, all of them the Hoima runs, confirmed by the
  operator on 2 Oct 2026 as the `UR523` service, flown under the `AF523` callsign.

---

## Every date at a glance

| date | day | tracks | flights | rotation holes | app-confirmed missing | pending at cut | verdict |
|---|---|---|---|---|---|---|---|
| 01 Oct | Thu | 16 | 16 | — | — | — | **complete** |
| 02 Oct | Fri | 27 | 27 | — | — | — | **complete** |
| 03 Oct | Sat | 19 | 17 | 2 | — | — | **partial** |
| 04 Oct | Sun | 17 | 21 | — | — | — | **complete** |
| 05 Oct | Mon | 1 | 1 | — | — | — | **cut-off** |

**3 of 5 days are complete.** The other 1 are set out below with exactly what each is short, along with any rotation that was still in the air at the cut. No date is missing and every complete day runs to the normal end of that weekday's evening bank.

---

## The unfinished dates, and what each is missing

### 03 Oct (Sat) — 17 flights, 19 tracks

**Rotation holes** — the rotation left Entebbe and returned; this leg is not in the export:

* **UGD720** — missing LUN–HRE (the export holds EBB–LUN, HRE–EBB).
* **UGD722** — missing HRE–LUN (the export holds EBB–HRE, LUN–EBB).

---

## The triangle route flights

Three rotations run through the month — `UGD720` Entebbe→Lusaka→Harare→Entebbe, `UGD722` Entebbe→Harare→Lusaka→Entebbe and `UGD334` Entebbe→Zanzibar→Kilimanjaro→Entebbe. The export carries the Entebbe legs almost every time they fly; the **middle sector, the hop between the two outstations, is the recurring gap** — 2 of the 7 rotations found are missing it, and that is the single largest hole in the archive.

| rotation | chain | rotations | complete | no middle sector | no return leg |
|---|---|---|---|---|---|
| UGD720 | `EBB → LUN → HRE → EBB` | 3 | 1 | 1 | 0 |
| UGD722 | `EBB → HRE → LUN → EBB` | 2 | 1 | 1 | 0 |
| UGD334 | `EBB → ZNZ → JRO → EBB` | 2 | 2 | 0 | 0 |

### The rotation leaving Entebbe each day

| date | day | UGD720 | UGD722 | UGD334 |
|---|---|---|---|---|
| 01 Oct | Thu | — | complete | — |
| 02 Oct | Fri | complete | — | complete |
| 03 Oct | Sat | **missing LUN–HRE** | **missing HRE–LUN** | — |
| 04 Oct | Sun | — | — | complete |
| 05 Oct | Mon | only LUN–HRE | — | — |

A dash means no rotation of that flight left Entebbe that day — the 720 and 722 alternate rather than running daily, and `UGD334` flies a few days a week. Rows marked `only …` are single legs whose partners fall outside the month or are themselves missing.

---

## What to ask for

1. **2 missing middle sectors** — the outstation-to-outstation hop, in rotations whose other legs are all in the export.
2. **0 missing return legs** — a rotation left Entebbe and the leg home is absent.
3. **The 0 legs the app confirms but the export does not hold**, listed date by date above.
4. **App pages from 01 Oct on**, so the days after the capture can be checked against a record as well as against the rotation pattern. The pages currently stop at 30 Sep.
