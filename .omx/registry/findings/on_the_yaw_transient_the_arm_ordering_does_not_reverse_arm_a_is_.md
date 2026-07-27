---
title: "On the yaw TRANSIENT the arm ordering does NOT reverse — Arm A is ahead at all f"
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-27T05:49:10.587769
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# On the yaw TRANSIENT the arm ordering does NOT reverse — Arm A is ahead at all f

On the yaw TRANSIENT the arm ordering does NOT reverse — Arm A is ahead at all four DR levels on both transient metrics — but the Arm A minus Arm B gap is BELOW the pre-registered floor at every level, so this is directionally consistent evidence, not a decisive win.

[EVIDENCE: paired delta of yaw `os_env_mean` (pp of step), m4-dead minus healthy, via `compare.py paired` — anchor +21.98 / +15.02 / +19.67 / +19.64; Arm A +11.90 / +9.84 / +10.69 / +11.07; Arm B +14.02 / +12.91 / +13.63 / +12.96; the A-B gap is -2.12 / -3.08 / -2.94 / -1.89 pp against a 10 pp floor, i.e. BELOW-FLOOR at 4/4]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
