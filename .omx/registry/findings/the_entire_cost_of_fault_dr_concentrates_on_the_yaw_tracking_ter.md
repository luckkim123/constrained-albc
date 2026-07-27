---
title: "The entire cost of fault-DR concentrates on the YAW tracking term, not on attitu"
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

# The entire cost of fault-DR concentrates on the YAW tracking term, not on attitu

The entire cost of fault-DR concentrates on the YAW tracking term, not on attitude tracking or on the penalty terms — the same axis the TAM authority analysis identified as the one m4 loss attacks.

[EVIDENCE: `Reward/yaw_vel` 2.102 (anchor) -> 1.970 (Arm B) -> 1.665 (Arm A); `Reward/att_rp`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

The entire cost of fault-DR concentrates on the YAW tracking term, not on attitude tracking or on the penalty terms — the same axis the TAM authority analysis identified as the one m4 loss attacks.

[EVIDENCE: `Reward/yaw_vel` 2.102 (anchor) -> 1.970 (Arm B) -> 1.665 (Arm A); `Reward/att_rp` moves only -0.047 to -0.080; every penalty term (`bias`, `smoothness`, `thruster`, `torque`) moves by <= 0.015]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

The entire cost of fault-DR concentrates on the YAW tracking term, not on attitude tracking or on the penalty terms — the same axis the TAM authority analysis identified as the one m4 loss attacks.

[EVIDENCE: `Reward/yaw_vel` 2.102 (anchor) -> 1.970 (Arm B) -> 1.665 (Arm A); `Reward/att_rp` moves only -0.047 to -0.080; every penalty term (`bias`, `smoothness`, `thruster`, `torque`) moves by <= 0.015]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
