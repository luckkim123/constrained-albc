---
title: "The DORAEMON curriculum state was genuinely restored across the process restart "
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The DORAEMON curriculum state was genuinely restored across the process restart 

The DORAEMON curriculum state was genuinely restored across the process restart rather than silently reset, which is the precondition for the pre-registered fault_severity check to carry meaning.

[EVIDENCE: `DORAEMON/mean/fault_severity` first logged value on the resumed run is 0.0178 at step 2350 — a mid-curriculum value, not the 0.0 nominal start; loader path ALBCConstraintEncoderRunner.load restores doraemon_state.pt via _load_aux_state (constraint_encoder_runner.py:309-313)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
