# Both retrained checkpoints are additive; the interaction removal belongs to the 

- id: finding/373 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: both-retrained-checkpoints-are-additive-the-interaction-removal-belongs-to-the · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Both retrained checkpoints are additive; the interaction removal belongs to the retrain, not to the final 2500 iteration

Both retrained checkpoints are additive; the interaction removal belongs to the retrain, not to the final 2500 iterations. `model_7500` overshoots its prediction by 0.018 deg and `model_9999` by 0.000, against the incumbent's 7.232.

[EVIDENCE: `d2_read.py` additivity table, `none` level, three arms]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
