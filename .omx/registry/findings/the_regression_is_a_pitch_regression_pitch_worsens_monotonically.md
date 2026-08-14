---
title: "The regression is a PITCH regression: pitch worsens monotonically with DR at all"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The regression is a PITCH regression: pitch worsens monotonically with DR at all

The regression is a PITCH regression: pitch worsens monotonically with DR at all four levels (+0.0391 / +0.0922 / +0.1052 / +0.3062 deg) while roll improves at three of four, so `att_norm`'s hard failure is carried almost entirely by pitch.

[EVIDENCE: `summary.json` per-axis `ss_error` for both evals, table above; hard pitch delta +0.3062 against the hard att_norm delta +0.3012]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
