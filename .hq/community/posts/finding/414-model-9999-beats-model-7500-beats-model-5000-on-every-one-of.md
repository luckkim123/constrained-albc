# `model_9999` beats `model_7500` beats `model_5000` on every one of the five rank

- id: finding/414 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: model_9999-beats-model_7500-beats-model_5000-on-every-one-of-the-five-rank · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: `model_9999` beats `model_7500` beats `model_5000` on every one of the five ranked cells and on the two d8 cells, on the

`model_9999` beats `model_7500` beats `model_5000` on every one of the five ranked cells and on the two d8 cells, on the common final sidecar; `p5_pick.py` selected `model_9999.pt` (medium paired att 9.33 vs 13.76 vs 18.41; hard median 8.11 vs 12.06 vs 14.78; survival 100 % all). This reverses the p3b finding (`finding/362`, "the last checkpoint regressed") for this run — the r4450 segment was still improving at 9999 because its curriculum was still opening.

[EVIDENCE: `/workspace/g0c_runner/p5_pick.log` (table reproduced), `p5_pick.py` ranking key (medium mean, hard median, earlier iteration)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
