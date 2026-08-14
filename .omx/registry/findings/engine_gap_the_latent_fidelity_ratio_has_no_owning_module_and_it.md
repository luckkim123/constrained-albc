---
title: "engine-gap: the latent fidelity ratio has no owning module, and it must be reported against per-dim R2 because their divergence is the diagnostic"
tags: ["engine-gap", "latent", "student", "distillation", "metric-definition", "r2", "ratio", "albc"]
created: 2026-08-14T06:41:27.965059
updated: 2026-08-14T06:41:27.965059
sources: ["diagnose-20260729-172500", "wiki-curation-2026-08-14"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: the latent fidelity ratio has no owning module, and it must be reported against per-dim R2 because their divergence is the diagnostic

[ENGINE-GAP] The student latent-fidelity "ratio" (P1 in the student pre-registrations) is defined in
pre-registration prose and recomputed ad hoc in each analysis; no module owns it. That is why its
definition could drift, and why it kept being read as a fidelity score when it is not one.

[WHERE] Nowhere, which is the gap. Verified 2026-08-14: no `ratio` metric exists in
constrained_albc/analysis/eval.py, none in constrained_albc/analysis/_encoder/ (_shared, sweep, train,
debug), and none in .omx/profile/eval_adapter.py or encoder_adapter.py. It should live beside the other
latent statistics in the analysis package, so every student report computes the identical quantity.

[SPEC] Two parts.
1. Give the metric an owning function that returns BOTH the aggregate env-variance ratio and per-dim
   R2 from the same arrays, so they cannot diverge by construction of the caller.
2. Report them TOGETHER, always. For a calibrated predictor the two are the same quantity; their
   DIVERGENCE is the actual diagnostic, and it separates three regimes cleanly:
   - calibrated          -- A0 d4 at none:  ratio 0.072  vs R2  0.083
   - over-dispersed      -- B1a d5 at none: ratio 11.122 vs R2 -94.199
   - under-dispersed-but-honest -- B1b d4 at none: ratio 0.042 vs R2 0.025
   A ratio alone cannot tell regime 2 from regime 3; the pair can.

[EVIDENCE] The three regime rows above are from analysis diagnose-20260729-172500 (run
trpo_sdeint_b1_lam4_s30_260729_170008). Corroborated from a second direction in the same analysis: the
aggregate ratio moved +13.6% at none (0.5974 -> 0.6787) while in-loop MSE moved +34.9% in the WORSE
direction (0.032975 -> 0.044489) over the same run pair -- the ratio does not track fidelity. The
mechanism behind that decoupling is the shrinkage signature: d4's ratio falls monotonically with
lambda (0.1166 -> 0.0721 -> 0.0416 across lambda 0/1/4) while its in-loop MSE is flat (0.0621 / 0.0540
/ 0.0582) against an essentially unchanged target variance of ~0.059. That is MSE regression shrinking
toward the conditional mean on a weakly-identifiable target -- pushing harder on the matching loss
buys shrinkage, not fidelity.

[CONSEQUENCE] Never adopt or reject a latent intervention on the ratio alone. An improving ratio with
a flat or worsening MSE is shrinkage, and reads as progress only if the pair is not shown.

[STATUS] proposed

RELATED: an R2 delta between two runs mixes error change with denominator change; latent dim d4
collapses at none-DR in every student arm; Lambda_latent is bracketed and CLOSED.

