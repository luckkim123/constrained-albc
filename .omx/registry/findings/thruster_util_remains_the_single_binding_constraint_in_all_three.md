---
title: "`thruster_util` remains the single binding constraint in all three runs — this i"
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

# `thruster_util` remains the single binding constraint in all three runs — this i

`thruster_util` remains the single binding constraint in all three runs — this is now 8 of 8 runs on this workspace — and fault-DR TIGHTENS it on the fault-agnostic arm specifically.

[EVIDENCE: engine `-> binding (max JC/dk): thruster_util` for all three; JC/dk 0.805 (anchor) ->]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

`thruster_util` remains the single binding constraint in all three runs — now 8 of 8 runs on this workspace — and fault-DR TIGHTENS it on the fault-agnostic arm specifically.

[EVIDENCE: engine reports `-> binding (max JC/dk): thruster_util` for all three; JC/dk 0.805 (anchor) -> **0.902** (Arm A) -> 0.798 (Arm B), against a next-highest `rp_vel_settling` at 0.514-0.576]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

`thruster_util` remains the single binding constraint in all three runs — now 8 of 8 runs on this workspace — and fault-DR TIGHTENS it on the fault-agnostic arm specifically.

[EVIDENCE: engine reports `-> binding (max JC/dk): thruster_util` for all three; JC/dk 0.805 (anchor) -> **0.902** (Arm A) -> 0.798 (Arm B), against a next-highest `rp_vel_settling` at 0.514-0.576]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
