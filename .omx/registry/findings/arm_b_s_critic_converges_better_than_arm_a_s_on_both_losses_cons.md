---
title: "Arm B's critic converges better than Arm A's on both losses, consistent with the"
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

# Arm B's critic converges better than Arm A's on both losses, consistent with the

Arm B's critic converges better than Arm A's on both losses, consistent with the +6D true-health input reducing the aliasing the critic would otherwise face between "this env is hard" and "this env has a dead thruster".

[EVIDENCE: value 0.5071 (B) < 0.5492 (A); cost_value 0.6110 (B) < 0.6670 (A)]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

Arm B's critic converges better than Arm A's on both losses, consistent with the +6D true-health input reducing the aliasing the critic would otherwise face between "this env is hard" and "this env has a dead thruster".

[EVIDENCE: `Loss/value_function` 0.5071 (B) < 0.5492 (A); `Loss/cost_value` 0.6110 (B) < 0.6670 (A)]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

Arm B's critic converges better than Arm A's on both losses, consistent with the +6D true-health input reducing the aliasing the critic would otherwise face between "this env is hard" and "this env has a dead thruster".

[EVIDENCE: `Loss/value_function` 0.5071 (B) < 0.5492 (A); `Loss/cost_value` 0.6110 (B) < 0.6670 (A)]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
