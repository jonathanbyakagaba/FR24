# Departure punctuality — September 2026

`punctuality.csv` is unchanged from the frozen build: the FR24 app status
dot is available for **603 of the 610** flights the frozen log carried, and
delays are measured against each service's own usual time (no September
timetable was available to the original build, and none was transcribed in
this rebuild — see `schedule_delays.md`).

The rebuilt `flights.csv` carries 640 rows: the same 610 (609 reproduced
from the same tracks, plus the reattributed sector files), the AF523
Hoima/test tracks the frozen log excluded, 16 tracks recovered from
FR24 playback on 2026-10-23 and 2 more from the same day's fresh
`FR data.zip` export (see `data_gaps.md`). Those extra tracks have
no app scoring and do not appear in `punctuality.csv`.

Read with the usual warning: a usual-time baseline cannot see a habit — a
service that always leaves 40 minutes late scores zero here. The
timetable-basis measurement for September now exists separately:
`schedule_delays.csv` (FTA plan STD, 624 matched legs — see
`schedule_delays.md`). This file was left app-based deliberately, so the
two scorings can be compared rather than one overwriting the other.
