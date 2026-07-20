---
title: "The load-bearing regression is roll TRANSIENT OVERSHOOT, and it lands on the FAI"
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:34:26.111024
updated: 2026-07-20T03:34:26.111024
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The load-bearing regression is roll TRANSIENT OVERSHOOT, and it lands on the FAI

The load-bearing regression is roll TRANSIENT OVERSHOOT, and it lands on the FAIR point: at `none` mean roll overshoot rose 17.02% → 26.99% (+59%) while roll steady-state FELL 21% — floor down, spike up, on the same fixed nominal physics. (The DR-scaled rows move the same way but are exam-confounded; the nominal row alone carries the verdict.)

[EVIDENCE: summary.json roll/os_env_mean (overshoot, % of target step) — 8k static_260717_005643 vs 5000 static_260715_192701; `none` = fixed nominal physics, the only fair cross-run level]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md
