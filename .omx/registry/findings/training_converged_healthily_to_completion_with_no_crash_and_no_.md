---
title: "Training converged healthily to completion with no crash and no termination path"
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

# Training converged healthily to completion with no crash and no termination path

Training converged healthily to completion with no crash and no termination pathology, and attitude tracking improved over the pre-crash state.

[EVIDENCE: launch.log final block iteration 4990 — Mean reward 269.95, `Track/att/roll_err_deg` 0.6567, `Track/att/pitch_err_deg` 0.5293, Term/terminated 0.0000, `Dynamics/thr/util_mean` 0.1604; the same fields at pre-crash iteration 2391 — the last iteration logged before the crash — read 259.86 / 0.7821 / 0.6781 (iteration 2390 read 0.8556 / 0.6914); the log contains zero assertion/abort/traceback lines and reached iteration 4999/5000 writing model_4999.pt]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
