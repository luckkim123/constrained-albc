---
title: "On yaw TRANSIENT — not steady state — Arm A beats Arm B at all four DR levels by"
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

# On yaw TRANSIENT — not steady state — Arm A beats Arm B at all four DR levels by

On yaw TRANSIENT — not steady state — Arm A beats Arm B at all four DR levels by a margin that matters, which is the cleanest single-axis result in the whole A/B.

[EVIDENCE: paired delta of yaw `os_env_mean` (pp of step), m4-dead minus healthy, via `compare.py paired` — anchor +21.98 / +15.02 / +19.67 / +19.64 (REAL at 4/4); Arm A +11.90 / +9.84 / +10.69 / +11.07; Arm B +14.02 / +12.91 / +13.63 / +12.96; Arm A below Arm B at 4/4 levels]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md
