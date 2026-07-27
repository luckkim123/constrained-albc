---
title: "The same ordering holds on the yaw heavy-tail count, and there Arm A stays under"
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-27T05:49:10.587769
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The same ordering holds on the yaw heavy-tail count, and there Arm A stays under

The same ordering holds on the yaw heavy-tail count, and there Arm A stays under the pre-registered floor at every level while Arm B crosses it — so the fault-critical axis favours the SIMPLER arm, independently of the attitude sign-flip.

[EVIDENCE: paired delta of yaw `n_gt20` (envs of 64) — anchor +27.5 / +22.5 / +22.0 / +20.5 (REAL at 4/4); Arm A +9.0 / +9.5 / +9.5 / +9.5 (BELOW-FLOOR at 4/4); Arm B +15.0 (REAL) / +13.5 / +13.5 / +14.5]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md
