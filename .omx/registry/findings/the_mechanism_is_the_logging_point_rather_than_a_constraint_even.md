---
title: "The mechanism is the logging point rather than a constraint event: `_last_barrie"
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

# The mechanism is the logging point rather than a constraint event: `_last_barrie

The mechanism is the logging point rather than a constraint event: `_last_barrier_penalty` is assigned inside `surrogate()`, which the line search calls once per candidate, so the scalar written to TB is the LAST evaluated candidate — including a rejected backtracking step whose ratio far from 1 can momentarily drive a margin small. The documented `clamp(min=1e-8)` caps the resulting barrier at 0.184, and the observed 0.140 sits under that ceiling. Attributing this to a rejected candidate is the reading most consistent with the evidence, but the candidate itself is not logged, so it is not directly observed.

[EVIDENCE: `constraint_trpo.py:470-476` `margin = barrier_base - cost_surrs`, `barrier = -torch.log(margin.clamp(min=1e-8)).sum() / self._barrier_t`, `self._last_barrier_penalty = barrier.item()` inside the `surrogate()` closure]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
