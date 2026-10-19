# September / October separation — 19 Oct 2026

The cleaned top-level archive (`FR data.zip` = `FR data (1).zip`,
1,065 unique tracks) has been split by month into the two existing
month folders:

| Folder | File | Tracks | Contents |
|---|---|---|---|
| `UR SEPTEMBER 2026/` | `september_tracks.zip` | 626 (621 UR + 5 other carriers) | every track starting in Sep 2026 |
| `UR SEPTEMBER 2026/` | `september_tracks_manifest.csv` | 626 rows | file, flight, callsign, first/last fix (EAT), fix count |
| `UR OCTOBER 2026/` | `october_tracks.zip` | 317 (all UR) | every track starting in Oct 2026 |
| `UR OCTOBER 2026/` | `october_tracks_manifest.csv` | 317 rows | same columns |

## Rule used

A track belongs to the month of its **first fix, local time (EAT,
UTC+3)** — the convention already stated in the month folders'
READMEs. A track is never split: the two September tracks that land
after midnight (`UR430-41e8fb3a.csv`, 30 Sep 21:04 → 1 Oct 03:30, and
`UR343-41e94875.csv`, 30 Sep 22:36 → 1 Oct 00:01) are stored whole in
the September zip. Inside each zip the layout matches the source
archive: `FR data/FR data/*.csv`.

## Notes

- **October now runs to 16 Oct.** The `october_tracks.zip` added here
  comes from the newest download, so it supersedes — for track-data
  purposes — the older `FR data.zip` (882 tracks, to ~5 Oct) already
  in that folder. That older zip and the folders' frozen analysis
  tables were left untouched, as the folders are frozen snapshots.
- **122 tracks belong to neither month** and exist only in the
  top-level zips: Aug 2026 ×20 (the 26–31 Aug run-in), Mar 2026 ×80,
  and strays from 2025-05, 2025-07, 2025-12, 2026-01, 2026-02,
  2026-04 and 2026-07. If August is ever wanted as its own month, its
  20 tracks can be split out the same way.
- The separation inherits the gaps documented in
  `missing_flights_october_2026.md` (notably 10 Oct) — splitting the
  data does not fill them.
