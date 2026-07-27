---
title: "But the curriculum also never SATURATED: `fault_severity` reached only 7.7% (Arm"
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

# But the curriculum also never SATURATED: `fault_severity` reached only 7.7% (Arm

But the curriculum also never SATURATED: `fault_severity` reached only 7.7% (Arm A) / 9.6% (Arm B) of its `[0, 1]` range and was still rising monotonically at the last sample. The trajectory is convex and still accelerating — this is an UNDER-EXPANDED dimension, a different diagnosis from a stall.

[EVIDENCE: `curriculum_trajectory.json` per-dim Beta(a,b) converted against `param_bounds`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

But the curriculum also never SATURATED: `fault_severity` reached only 7.7% (Arm A) / 9.6% (Arm B) of its `[0, 1]` range and was still rising monotonically at the last sample, which is an UNDER-EXPANDED dimension rather than a stall.

[EVIDENCE: `curriculum_trajectory.json` per-dim Beta(a,b) converted against `param_bounds` [0.0, 1.0], cross-checked against TB `DORAEMON/mean/fault_severity` with an exact match at 0.0771 (A) / 0.0959 (B); the trajectory is convex and still accelerating at iter 4750]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

But the curriculum also never SATURATED: `fault_severity` reached only 7.7% (Arm A) / 9.6% (Arm B) of its `[0, 1]` range and was still rising monotonically at the last sample, which is an UNDER-EXPANDED dimension rather than a stall.

[EVIDENCE: `curriculum_trajectory.json` per-dim Beta(a,b) converted against `param_bounds` [0.0, 1.0], cross-checked against TB `DORAEMON/mean/fault_severity` with an exact match at 0.0771 (A) / 0.0959 (B); the trajectory is convex and still accelerating at iter 4750]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
