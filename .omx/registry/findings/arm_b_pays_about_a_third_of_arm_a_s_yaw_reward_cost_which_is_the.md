---
title: "Arm B pays about a third of Arm A's yaw-reward cost, which is the one place the "
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-27T05:49:10.587769
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Arm B pays about a third of Arm A's yaw-reward cost, which is the one place the 

Arm B pays about a third of Arm A's yaw-reward cost, which is the one place the privileged fault channel shows a coherent training-side benefit.

[EVIDENCE: yaw_vel deficit -0.132 (B) vs -0.437 (A); episode return 260.65 (B) vs 250.63 (A)]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

Arm B pays about a third of Arm A's yaw-reward cost, which is the one place the privileged fault channel shows a coherent training-side benefit.

[EVIDENCE: `Reward/yaw_vel` deficit -0.132 (B) vs -0.437 (A); `Train/mean_reward` 260.65 (B) vs 250.63 (A) against the anchor's 266.01]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

Arm B pays about a third of Arm A's yaw-reward cost, which is the one place the privileged fault channel shows a coherent training-side benefit.

[EVIDENCE: `Reward/yaw_vel` deficit -0.132 (B) vs -0.437 (A); `Train/mean_reward` 260.65 (B) vs 250.63 (A) against the anchor's 266.01]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
