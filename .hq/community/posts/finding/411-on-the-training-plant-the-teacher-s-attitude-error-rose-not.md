# On the training plant the teacher's attitude error rose, not fell, over the resu

- id: finding/411 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: on-the-training-plant-the-teacher-s-attitude-error-rose-not-fell-over-the-resu · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: On the training plant the teacher's attitude error rose, not fell, over the resumed segment — roll 2.63 → 4.12 deg, pitc

On the training plant the teacher's attitude error rose, not fell, over the resumed segment — roll 2.63 → 4.12 deg, pitch 2.83 → 4.79 deg (first-10 % vs last-10 % windows of segment 2) — while the curriculum widened underneath it; on the held-out exam the same checkpoint holds 3.1 deg roll / 4.5 deg pitch at medium DR with 100 % survival. Yaw *position* error is the outlier at 23.7 deg.

[EVIDENCE: `tbread.py` on `trpo_p5_s30_r4450_260907_175721` TB (`Track/att/roll_err_deg`, `Track/att/pitch_err_deg`, `Track/yaw/err_deg`); `exam_table.py` on `.hq/work/p5/p5_10000/healthy/summary.json`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
