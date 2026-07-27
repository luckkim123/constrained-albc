---
title: "Fault-DR training reduces m4-dead attitude degradation by 5-12x versus the ancho"
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-27T05:49:10.587769
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Fault-DR training reduces m4-dead attitude degradation by 5-12x versus the ancho

Fault-DR training reduces m4-dead attitude degradation by 5-12x versus the anchor, at every DR level, and eliminates the fault-induced terminations entirely.

[EVIDENCE: summary.json paired healthy/dead]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

Fault-DR training reduces m4-dead attitude degradation by 5-12x versus the anchor and eliminates the fault-induced terminations entirely, with `soft` the one level where the anchor was already benign so the improvement there is only 1.2-2.5x.

[EVIDENCE: summary.json paired healthy/dead — att_norm delta anchor 1.805 / 0.282 / 1.818 / 3.472 vs Arm A 0.285 / 0.241 / 0.251 / 0.432 and Arm B 0.148 / 0.113 / 0.149 / 0.669 (none/soft/medium/hard); yaw `ss_error` delta anchor 0.092-0.168 rad/s (18-34% of the 0.5 rad/s command) vs both arms 0.019-0.030 rad/s (4-6%); survival anchor -6.25 / 0.00 / -4.69 / -7.81 pp vs both arms 0.00 pp at all four levels]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
