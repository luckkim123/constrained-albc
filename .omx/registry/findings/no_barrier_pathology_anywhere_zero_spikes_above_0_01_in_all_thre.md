---
title: "No barrier pathology anywhere: zero spikes above 0.01 in all three runs and the "
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

# No barrier pathology anywhere: zero spikes above 0.01 in all three runs and the 

No barrier pathology anywhere: zero spikes above 0.01 in all three runs and the safety rails (`attitude`, `cumul_yaw`, `joint1_pos`) stay at ~0 budget consumption.

[EVIDENCE: `barrier_penalty spikes(>0.01)=0` for all three; the three rail constraints report]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

No barrier pathology anywhere: zero spikes above 0.01 in all three runs and the safety rails stay at ~0 budget consumption.

[EVIDENCE: `barrier_penalty spikes(>0.01)=0` for all three (max -0.043 / -0.044 / -0.008); `Constraint/viol/attitude`, `Constraint/viol/cumul_yaw` and `Constraint/viol/joint1_pos` report JC/dk = -0.000 except Arm B's `attitude` at 0.033]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

No barrier pathology anywhere: zero spikes above 0.01 in all three runs and the safety rails stay at ~0 budget consumption.

[EVIDENCE: `barrier_penalty spikes(>0.01)=0` for all three (max -0.043 / -0.044 / -0.008); `Constraint/viol/attitude`, `Constraint/viol/cumul_yaw` and `Constraint/viol/joint1_pos` report JC/dk = -0.000 except Arm B's `attitude` at 0.033]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
