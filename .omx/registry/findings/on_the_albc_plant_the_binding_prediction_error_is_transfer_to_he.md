---
title: "On the ALBC plant the binding prediction error is transfer to held-out plants, not model class, so lifting does not touch the dominant term"
tags: ["koopman", "generalization", "domain-randomization", "exchange-rate", "decision"]
created: 2026-08-05T10:17:27.747458
updated: 2026-08-05T10:17:27.747458
sources: [".omx/programs/koopman-lifting/PLAN.md#12.8", ".omx/programs/koopman-lifting/step2_fit/fit_hard.json"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# On the ALBC plant the binding prediction error is transfer to held-out plants, not model class, so lifting does not touch the dominant term

SOURCE: .omx/programs/koopman-lifting/step2_fit/fit_hard.json, 2026-08-05, PLAN 12.8. Fitting lifted linear models with an env-wise 48/16 split at DR hard (so the test envs are held-out PLANTS), the train/test gap is +0.58 to +0.62 against a test error of 0.85 to 0.90 -- roughly two thirds of the test error is failure to transfer. That gap is nearly identical for every model class including no lift at all. The entire model family spans about 6 pct while the gap spans about 65 pct. A model with more capacity does not help: the nested nonlinear variant has the LARGEST gap at hard, so its extra capacity partly buys train accuracy that does not transfer. Consequence for pricing any lifting intervention on this stack: in the realistic full-length protocol at hard, a learned lift beats a random expansion by only 1.6 pct RMSE, whereas the X1 tail-split already measured that a 6.69 pct RMSE improvement in latent quality produced a sub-floor (zero) control change. The offline signal in the realistic condition is therefore about 4x smaller than one already demonstrated to move nothing. In transient-rich protocols the same comparison reaches 9.5 to 17.6 pct, so any single number quoted without its command protocol is misleading.
