---
title: "The asymmetric critic absorbed the fault dimension without degrading: the value "
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

# The asymmetric critic absorbed the fault dimension without degrading: the value 

The asymmetric critic absorbed the fault dimension without degrading: the value loss rises modestly (harder value prediction under a wider env distribution) while the CONSTRAINT value loss actually falls on both arms.

[EVIDENCE: `Loss/value_function` +0.076 (A) / +0.034 (B) vs anchor; `Loss/cost_value`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

The asymmetric critic absorbed the fault dimension without degrading: the value loss rises modestly under a wider env distribution while the CONSTRAINT value loss actually falls on both arms.

[EVIDENCE: `Loss/value_function` +0.076 (A) / +0.034 (B) vs the anchor's 0.4731; `Loss/cost_value` -0.095 (A) / -0.151 (B) vs the anchor's 0.7620]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

The asymmetric critic absorbed the fault dimension without degrading: the value loss rises modestly under a wider env distribution while the CONSTRAINT value loss actually falls on both arms.

[EVIDENCE: `Loss/value_function` +0.076 (A) / +0.034 (B) vs the anchor's 0.4731; `Loss/cost_value` -0.095 (A) / -0.151 (B) vs the anchor's 0.7620]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
