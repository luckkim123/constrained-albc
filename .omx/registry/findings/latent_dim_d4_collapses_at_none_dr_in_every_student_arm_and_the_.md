---
title: "Latent dim d4 collapses at none-DR in every student arm and the blanket none-exclusion hides it"
tags: ["encoder", "latent", "observability", "student", "distillation", "albc", "none-dr", "metric-correction", "r2"]
created: 2026-07-29T07:26:10.998573
updated: 2026-07-29T08:30:12.380402
sources: ["diagnose-20260729-161459", "diagnose-20260729-172500"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Latent dim d4 collapses at none-DR in every student arm and the blanket none-exclusion hides it

The A0 and A0g reports mark the `none` DR level '(excluded)' in the per-dim latent collapse count, on the grounds that its aggregate l_true env-variance (~0.009) is an order of magnitude below hard's (~0.068) and so the ratio denominator is untrustworthy. That aggregate caveat is real but it is applied too broadly.

Per-dim check (analysis diagnose-20260729-161459, computed from latent_none.npz reproducing eval.py:982-1000 `_summarize_latent`, env-variance = var over axis 1 averaged over time):
- at `none`, d4 carries the LARGEST teacher env-variance of all nine dims: 5.85e-2 (A0), 5.93e-2 (A0g), 6.04e-2 (B4b) -- it is the best-conditioned dimension there, not a near-zero denominator.
- yet its ratio l_hat/l_true at that level is 0.0721 (A0), 0.0740 (A0g), 0.0380 (B4b): under the 0.1 collapse threshold in ALL THREE arms, across two encoder architectures and two dagger_beta settings.

So the d4 collapse at `none` is a genuine under-dispersion, not an artifact, and the wholesale exclusion has been hiding it since A0. The dimension spread does justify caution about the AGGREGATE none ratio (l_true env-variance spans 122x across dims at none vs 64x at hard) -- the fix is to exclude the aggregate, not the per-dim count.

This is a narrower and more actionable form of the parked observability lead (closed_loop_latent_collapse_suspicion_legacy_student_measured_11): rather than 'is there an observability floor', the question is 'why is the single most env-discriminative latent dimension the one the student cannot reproduce when DR is off'. Resolvable from existing evals first (per-dim ratio across the campaign's stored latent_*.npz) before any new arm.

---

## Update (2026-07-29T08:30:12.380402)

CORRECTION 2026-07-29 (B1b, analysis diagnose-20260729-172500) -- THIS PAGE'S ORIGINAL CLAIM IS REVERSED.

The d4 "collapse" at `none` is not under-dispersion. It is the correct, calibrated behaviour of a weak
predictor, and d4 is in fact the ANCHOR'S SINGLE BEST-TRACKED DIMENSION at that level.

The error was reading the ratio against a target of 1. The law of total variance fixes the correct target:
for an MSE-optimal predictor `l_hat = E[l_true | obs]`,

    Var(l_hat) = Var(l_true) - E[Var(l_true|obs)]   and   MSE = E[Var(l_true|obs)]
    => Var(l_hat) / Var(l_true) = 1 - MSE / Var(l_true) = R2

So the P1 ratio and R2 are THE SAME QUANTITY for a calibrated predictor. The ratio's healthy target is
R2, not 1 -- a genuinely weak-but-honest predictor is REQUIRED to have a low ratio.

Measured at `none`, anchor A0 (lambda 1), from latent_none.npz:

| dim | ratio | R2 = 1 - MSE/Var_total(l_true) | Var_total(l_true) |
|:--|--:|--:|--:|
| d4 | 0.0721 | +0.0830 | 0.05886 |
| every other dim | 0.20 - 5.60 | -0.16 to -16.11 | 0.00068 - 0.00724 |

d4's ratio and R2 agree to 0.011 -- textbook calibration -- and d4 is the ONLY dim of nine with positive
R2 at `none`, while carrying 8x the total variance of the next-largest dim. The campaign was calling its
best-tracked dimension collapsed.

The lambda bracket confirms the mechanism (d4 at `none`, lambda 0 / 1 / 4 = B1a / A0 / B1b):

| quantity | lambda 0 | lambda 1 | lambda 4 |
|:--|--:|--:|--:|
| ratio | 0.1166 | 0.0721 | 0.0416 |
| R2 | -0.0634 | +0.0830 | +0.0247 |
| in-loop MSE | 0.0621 | 0.0540 | 0.0582 |
| Var(l_true) | 0.0584 | 0.0589 | 0.0597 |

The ratio falls monotonically with lambda while MSE is flat -- MSE regression shrinking toward the
conditional mean on a weakly-identifiable target. Pushing harder on the matching loss buys shrinkage,
not fidelity. That is a property of the estimator, not a pathology of d4.

WHAT SURVIVES from the original page: the aggregate `none` ratio is still untrustworthy (dimension spread
122x), and per-dim inspection is still the right granularity. WHAT DOES NOT SURVIVE: "the d4 collapse at
`none` is a genuine under-dispersion", and the framing "why is the single most env-discriminative latent
dimension the one the student cannot reproduce when DR is off" -- it reproduces it better than any other
dimension there.

THE REAL FINDING, which is larger: in-loop the student latent is WORSE THAN A CONSTANT-MEAN PREDICTOR on
8 of 9 dims at `none` and 5 of 9 at `hard`, identically for lambda 0, 1 and 4. Only d0/d1/d5/d8 have
positive R2 at hard, in every arm. That is covariate shift -- the campaign's already-identified binding
constraint -- and no loss reweighting reaches it. The actionable successor is the observability retrain
(velocity channel and/or longer history), because R2 names exactly which dimensions are unidentifiable
and the lambda bracket proves reweighting cannot fix them.

PROTOCOL CHANGE for every future arm: report per-dim R2 beside the ratio. Agreement means calibrated;
ratio >> R2 means over-dispersion (B1a d5 at none: ratio 11.122, R2 -94.199); ratio << R2 would mean
under-dispersion. The divergence is the diagnostic, not the ratio's distance from 1.

