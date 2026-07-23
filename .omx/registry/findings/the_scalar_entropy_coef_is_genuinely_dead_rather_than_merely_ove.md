---
title: "The scalar `entropy_coef` is genuinely dead rather than merely overridden in spi"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The scalar `entropy_coef` is genuinely dead rather than merely overridden in spi

The scalar `entropy_coef` is genuinely dead rather than merely overridden in spirit: an all-zero 8-tuple is still a non-empty tuple, so the truthiness test at `constraint_trpo.py:107` takes the per-dim branch and the bonus term evaluates to exactly zero.

[EVIDENCE: `constraint_trpo.py:107` `if entropy_coef_per_dim:`; `:490` `if self._entropy_coef_per_dim is not None:`; `:497` `entropy_bonus = -(self._entropy_coef_per_dim * per_dim_ent).sum(dim=-1).mean()`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
