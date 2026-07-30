# P1 Isaac-side raw CSVs (2026-07-29)

15 runs = 5 profiles {S5, S2, S1ff, S3, S4} x 3 reps, produced by
`scripts/isaac_p1_replay.py` (see its docstring for the plant and settle schedule).
Each file is a 20 s window at the 50 Hz control rate = 1001 rows including the header.
Columns are byte-identical to the Stonefish-side runner's 24.

Aggregate with `P1_STENCIL=3`. The default 5-sample derivative stencil spans 40 ms at
Stonefish's 100 Hz but 80 ms here, which would smooth the Isaac peaks harder than the
Stonefish ones and break the like-for-like comparison.

With DR and faults off Isaac is deterministic: the 3-rep standard deviation is exactly 0
on every metric. One rep suffices; sd=0 is not an anomaly.
