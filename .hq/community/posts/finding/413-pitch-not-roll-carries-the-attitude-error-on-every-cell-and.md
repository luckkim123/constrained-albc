# Pitch, not roll, carries the attitude error on every cell and level (pitch/roll 

- id: finding/413 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: pitch-not-roll-carries-the-attitude-error-on-every-cell-and-level-pitch-roll · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Pitch, not roll, carries the attitude error on every cell and level (pitch/roll = 1.4–1.8 without lag, 1.5–1.9 at 1–2 st

Pitch, not roll, carries the attitude error on every cell and level (pitch/roll = 1.4–1.8 without lag, 1.5–1.9 at 1–2 steps of lag), and under 8-step lag both axes and yaw-rate blow up together (yaw-rate `ss_error` 0.44 → 1.29–1.49 rad/s on `healthy_d8`). The m3+m4 fault itself costs only +0.3 deg at medium (`pair34` 6.27 vs `healthy` 5.96) — the fault axis is solved, the delay axis is not.

[EVIDENCE: same `exam_table.csv` rows; `pair34`−`healthy` medium delta 0.31 deg, below the 0.10 deg floor only for roll (3.13 vs 3.09)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
