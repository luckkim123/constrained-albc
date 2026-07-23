---
title: "Exploration is dead in A1 exactly as in both references, so entropy collapse is "
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Exploration is dead in A1 exactly as in both references, so entropy collapse is 

Exploration is dead in A1 exactly as in both references, so entropy collapse is a lineage property and NOT caused by the `step_interval` change — which is why the A2 probe (entropy bonus off) is the right next isolation and not a follow-up to A1.

[EVIDENCE: engine `[TIER 1]` — entropy -9.21 COLLAPSED / noise_std 0.08 LOW (A1); -9.07 / 0.09 (ref5k); -9.21 / 0.08 (extend8k); `[DIAGNOSIS]` item 1 fires on all three]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md

---

## Update (2026-07-21T10:26:11.609658)

Exploration is dead in A1 exactly as in both references, so entropy collapse is a lineage property and NOT caused by the `step_interval` change — which is why the A2 probe (entropy bonus off) is the right next isolation and not a follow-up to A1.

[EVIDENCE: engine `[TIER 1]` — entropy -9.21 COLLAPSED / noise_std 0.08 LOW (A1); -9.07 / 0.09 (ref5k); -9.21 / 0.08 (extend8k); `[DIAGNOSIS]` item 1 fires on all three]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
