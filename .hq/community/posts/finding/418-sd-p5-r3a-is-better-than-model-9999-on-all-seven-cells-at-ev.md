# `sd_p5_r3a` is better than `model_9999` on all seven cells at every DR level; th

- id: finding/418 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: sd_p5_r3a-is-better-than-model_9999-on-all-seven-cells-at-every-dr-level-th · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: `sd_p5_r3a` is better than `model_9999` on all seven cells at every DR level; the smallest medium margin is 0.5 deg (`pa

`sd_p5_r3a` is better than `model_9999` on all seven cells at every DR level; the smallest medium margin is 0.5 deg (`pair34`) and the largest 5.9 deg (`healthy_d1`, `healthy_d2`). Under 1–2 steps of lag the student does not degrade at all (5.34–6.01 vs 5.34–5.78 without lag) while the teacher doubles (11.2–12.0). Under 8 steps both degrade, the student less (17.0/15.6 vs 19.9/20.1).

[EVIDENCE: `exam_table.csv` rows tag ∈ {`sd_p5_r3a`, `p5_10000`}, all levels; `.hq/work/p5/sd_p5_r3a/*/summary.json` and `.hq/work/p5/p5_10000/*/summary.json`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
