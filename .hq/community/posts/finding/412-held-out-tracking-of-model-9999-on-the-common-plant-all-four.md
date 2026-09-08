# Held-out tracking of `model_9999` on the common plant, all four DR levels and al

- id: finding/412 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: held-out-tracking-of-model_9999-on-the-common-plant-all-four-dr-levels-and-al · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Held-out tracking of `model_9999` on the common plant, all four DR levels and all seven cells: attitude `ss_error` is 6–

Held-out tracking of `model_9999` on the common plant, all four DR levels and all seven cells: attitude `ss_error` is 6–9 deg without lag, 11–14 deg at 1–2 steps of lag and 18–24 deg at 8 steps; CV = `ss_error_std`/`ss_error` is 0.8–1.0 on the no-lag cells (a few envs carry the mean, the median is lower) and drops to 0.4–0.7 under lag where every env is bad. Survival is 100 % in all 28 rows. `none` is *worse* than `medium` on every no-lag cell (8.07 vs 5.96 on `healthy`) — the policy is tuned to the DR mean rather than to the nominal plant.

[EVIDENCE: `exam_table.py` → `/root/p5_report_scratch/exam_table.csv`, rows tag=`p5_10000`, fields `att_norm.ss_error`, `att_norm.ss_error_std`, `roll.ss_error`, `pitch.ss_error`, `yaw.ss_error` (rad/s), `survival_pct`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
