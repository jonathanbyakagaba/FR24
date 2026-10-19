# UR-only split — 19 Oct 2026

`FR data (1).zip` has been **deleted** (it was byte-identical to
`FR data.zip` after the cleanup in `ZIP_UPDATE.md`), and the remaining
archive has been separated by airline so Uganda Airlines data can be
analysed on its own.

## The UR-only dataset (use this for UR analysis)

| Archive | Tracks | Months covered |
|---|---|---|
| `FR data.zip` (top level, now **UR only**) | 1,017 | 2026-10: 317 · 2026-09: 622 · 2026-08: 20 · 2026-03: 43 · 2026-02: 5 · 2026-01: 3 · 2025-12: 1 · 2025-07: 5 · 2025-05: 1 |
| `UR SEPTEMBER 2026/september_tracks.zip` | 622 | Sep 2026 only |
| `UR OCTOBER 2026/october_tracks.zip` | 317 | Oct 2026 only (unchanged — it was already all UR) |

A track counts as UR if its filename flight number starts with `UR`,
**or** it transmitted under a UGD callsign. That adds one file the
filename rule alone would miss: `41e29857.csv` (UGD720X, NBO–EBB,
29 Sep 2026 — see `UR SEPTEMBER 2026/no_code_tracks.md`). The
AF523-transmitting Hoima tracks are already `UR523`-named and are
included as before.

Internal layout of every zip is unchanged (`FR data/FR data/*.csv`),
and no track was renamed or altered — only moved between archives.
`FR data.zip` sha256 is now
`541ea737d44b3257dec58358a84aabfc0ff70272b78e8f3dbc75ea172b3e1f50`.

## The other airlines (kept, but separate)

| Archive | Tracks |
|---|---|
| `other_airlines_tracks.zip` (+ `other_airlines_tracks_manifest.csv`) | 48 |
| `UR SEPTEMBER 2026/september_other_airlines_tracks.zip` (+ manifest) | 4 of those 48, split out by month as well |

Contents: Ethiopian ET332/333/338/339/506/3810/3859/3873/3917/3926/8337
(×13), Qatar Airways QR1383/1384 (×6), Turkish TK612 (×4), Garuda
GA7840/7850 (×4), flynas XY345/346/1233/1234 (×4), RwandAir
WB422/423/464 (×4), KLM KL535/537 (×3), Brussels SN455/465/467 (×4),
EgyptAir MS835 (×2), flydubai FZ619 (×1), Kenya Airways KQ418 (×1),
plus one unidentified track (`3e02c7e0.csv`, 22 Jan 2026, no callsign,
EBB–KGL — it cannot be attributed to any airline, so it is filed here
rather than silently counted as UR; see `no_code_tracks.md`).

By month the other-airline tracks are: Mar 2026 ×37, Sep 2026 ×4,
Jan 2026 ×3, Apr 2026 ×2, Jul 2026 ×2.

## Notes for analysis

- Anything computed before this split from the combined 1,065-track
  archive will differ by exactly these 48 tracks. Reports in this
  repo written before the split (`missing_dates_fr_data_1.md` etc.)
  counted UR by filename only (1,016); the UR-only archive has 1,017
  because of the UGD720X file above.
- The month manifests in `UR SEPTEMBER 2026/` and
  `UR OCTOBER 2026/` were regenerated to match the UR-only zips.
- If you'd rather have a single `UR data.zip` filename at top level
  instead of the UR-only `FR data.zip`, that's a pure rename — say
  the word.
