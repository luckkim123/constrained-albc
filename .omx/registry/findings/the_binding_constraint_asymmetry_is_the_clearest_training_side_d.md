---
title: "The binding-constraint asymmetry is the clearest training-side difference betwee"
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

# The binding-constraint asymmetry is the clearest training-side difference betwee

The binding-constraint asymmetry is the clearest training-side difference between the arms and it points the same way as the yaw-reward deficit: Arm A must over-drive the surviving thrusters blindly, spending 90% of its utilisation budget, while Arm B — which can see which thruster is degraded — stays at the anchor's level.

[EVIDENCE: `thruster_util` JC/dk 0.902 (A) vs 0.798 (B) vs 0.805 (anchor); margin 3.90 (A) vs]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

The binding-constraint asymmetry is the clearest training-side difference between the arms and points the same way as the yaw-reward deficit: Arm A must over-drive the surviving thrusters blindly while Arm B, which can see which thruster is degraded, stays at the anchor's level.

[EVIDENCE: `Constraint/margin/thruster_util` JC/dk 0.902 (A) vs 0.798 (B) vs 0.805 (anchor); margin 3.90 (A) vs 8.09 (B) vs 7.80 (anchor) — Arm A's margin is halved]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

The binding-constraint asymmetry is the clearest training-side difference between the arms and points the same way as the yaw-reward deficit: Arm A must over-drive the surviving thrusters blindly while Arm B, which can see which thruster is degraded, stays at the anchor's level.

[EVIDENCE: `Constraint/margin/thruster_util` JC/dk 0.902 (A) vs 0.798 (B) vs 0.805 (anchor); margin 3.90 (A) vs 8.09 (B) vs 7.80 (anchor) — Arm A's margin is halved]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
