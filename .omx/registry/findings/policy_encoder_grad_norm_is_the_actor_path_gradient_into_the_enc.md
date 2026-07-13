---
title: "`Policy/encoder_grad_norm` is the ACTOR-path gradient into the encoder (TRPO sur"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `Policy/encoder_grad_norm` is the ACTOR-path gradient into the encoder (TRPO sur

`Policy/encoder_grad_norm` is the ACTOR-path gradient into the encoder (TRPO surrogate; constraint_trpo.py:541-548 in `_trpo_step`), not the value/critic gradient — its rise shows the encoder trains via the actor path but is NOT by itself evidence of the P4 M1 fix (encoder params in the value optimizer). The M1 fix is present in the code path; this run's TB exposes no critic-side encoder-grad metric, so its effect is not separately confirmable from this run.

[EVIDENCE: code constraint_trpo.py:541-548 (enc_slice of the surrogate grad g); no value-side encoder-grad tag among the 136 TB scalars]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

`Policy/encoder_grad_norm` is the ACTOR-path gradient into the encoder (TRPO surrogate; constraint_trpo.py:541-548 in `_trpo_step`), not the value/critic gradient — its rise shows the encoder trains via the actor path but is NOT by itself evidence of the P4 M1 fix (encoder params in the value optimizer). The M1 fix is present in the code path; this run's TB exposes no critic-side encoder-grad metric, so its effect is not separately confirmable from this run.

[EVIDENCE: code constraint_trpo.py:541-548 (enc_slice of the surrogate grad g); no value-side encoder-grad tag among the 136 TB scalars]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
