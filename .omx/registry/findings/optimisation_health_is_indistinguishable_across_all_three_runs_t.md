---
title: "Optimisation health is indistinguishable across all three runs; the engine's `en"
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

# Optimisation health is indistinguishable across all three runs; the engine's `en

Optimisation health is indistinguishable across all three runs; the engine's `entropy COLLAPSED` + `noise_std LOW` anomaly is the workspace's standing baseline condition, not something fault-DR introduced.

[EVIDENCE: engine `[TIER 1] Core Health` reports `STATUS: 2 ANOMALIES` with the same two flags]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

Optimisation health is indistinguishable across all three runs; the engine's `entropy COLLAPSED` + `noise_std LOW` anomaly is the workspace's standing baseline condition, not something fault-DR introduced.

[EVIDENCE: engine `[TIER 1] Core Health` reports `STATUS: 2 ANOMALIES` with the same two flags for the anchor as for both arms; `kl` pinned at the 0.005 `max_kl` cap (0.00496 / 0.00499 / 0.00501) and `line_search_success` = 1.000 in all three]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

Optimisation health is indistinguishable across all three runs; the engine's `entropy COLLAPSED` + `noise_std LOW` anomaly is the workspace's standing baseline condition, not something fault-DR introduced.

[EVIDENCE: engine `[TIER 1] Core Health` reports `STATUS: 2 ANOMALIES` with the same two flags for the anchor as for both arms; `kl` pinned at the 0.005 `max_kl` cap (0.00496 / 0.00499 / 0.00501) and `line_search_success` = 1.000 in all three]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
