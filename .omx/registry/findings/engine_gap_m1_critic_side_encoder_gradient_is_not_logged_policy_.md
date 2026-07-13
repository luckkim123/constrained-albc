---
title: "engine-gap: M1 critic-side encoder gradient is not logged (Policy/encoder_grad_norm is actor-path only)"
tags: ["engine-gap", "encoder", "M1", "constraint_trpo", "proposed"]
created: 2026-07-12T23:46:27.232691
updated: 2026-07-12T23:46:27.232691
sources: ["diagnose-20260713-081707"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: M1 critic-side encoder gradient is not logged (Policy/encoder_grad_norm is actor-path only)

[ENGINE-GAP] Policy/encoder_grad_norm logs ONLY the actor-path gradient into the encoder: it is the enc_slice of g=_flat_grad(surrogate_fn(), self._policy_params) computed in _trpo_step (constraint_trpo.py:541-548). The M1 fix (critic_uses_z adds encoder params to the Adam value_params group, constraint_trpo.py:186-192) means the encoder ALSO receives a value/critic gradient, but _update_values logs no encoder-grad tag, so the M1 critic-side contribution is unobservable in TB. Consequence: a report CANNOT confirm the M1 fix worked from this run's TB (only that the encoder trains via the actor path). [WHERE] constraint_trpo.py _update_values + constraint_encoder_runner.py metrics dict (~L337). [SPEC] log the encoder slice of the value-loss gradient (e.g. Encoder/value_grad_norm or Grad/enc_value_step) so future baselines can quantify the M1 effect. [EVIDENCE] analysis diagnose-20260713-081707, run trpo_baseline_260713_031325: encoder_grad_norm rose 0.030->0.113 but that is actor-side; no value-side encoder-grad among the run's TB scalars. [STATUS] proposed.
