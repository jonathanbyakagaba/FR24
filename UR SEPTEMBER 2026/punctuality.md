# Departure punctuality — September 2026

`punctuality.csv` is unchanged from the frozen build: the FR24 app status
dot is available for **603 of the 610** flights the frozen log carried, and
delays are measured against each service's own usual time (no September
timetable was available to the original build, and none was transcribed in
this rebuild — see `schedule_delays.md`).

The rebuilt `flights.csv` carries 622 rows: the same 610 (609 reproduced
from the same tracks, plus the reattributed sector files) plus the AF523
Hoima/test tracks the frozen log excluded. Those extra tracks have no app
scoring and do not appear in `punctuality.csv`.

Read with the usual warning: a usual-time baseline cannot see a habit — a
service that always leaves 40 minutes late scores zero here. For a
timetable-basis measurement, October's rebuilt files (FTA plan STD) are
the worked example.
