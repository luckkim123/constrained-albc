# Scored directly against each other rather than through the incumbent, `model_750

- id: finding/364 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: scored-directly-against-each-other-rather-than-through-the-incumbent-model_750 · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Scored directly against each other rather than through the incumbent, `model_7500` beats `model_9999` on 15 of 16 CORE r

Scored directly against each other rather than through the incumbent, `model_7500` beats `model_9999` on 15 of 16 CORE rows; 12 of those clear the 0.10 deg floor, 3 are ties, and `model_9999` wins exactly one row. The final 2500 iterations were a net regression, not a trade of accuracy for robustness.

[EVIDENCE: `g0c_runner/ckpt_read.py` over `.hq/work/p4/p3b_7500` and `.hq/work/p4/p3b_final`, `p4_score` loaders]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
