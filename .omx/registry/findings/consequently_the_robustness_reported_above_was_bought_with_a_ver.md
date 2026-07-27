---
title: "Consequently the robustness reported above was bought with a very small fault ex"
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

# Consequently the robustness reported above was bought with a very small fault ex

Consequently the robustness reported above was bought with a very small fault exposure — under 6% of envs carried any degraded thruster even at the end of training.

[EVIDENCE: effective per-thruster fail probability = `u * thruster_fail_prob` = 0.0771 x 0.10 =]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

Consequently the robustness reported above was bought with a very small fault exposure — under 6% of envs carried any degraded thruster even at the end of training.

[EVIDENCE: effective per-thruster fail probability = `u * thruster_fail_prob` = 0.0771 x 0.10 = 0.00771 (Arm A) and 0.00959 (Arm B), so P(at least 1 of 6 faulted) = 4.54% / 5.62% and E[faulted per env] = 0.046 / 0.058; `thruster_fail_prob = 0.1` and `thruster_health_range = (0.0, 0.5)` from `params/env.yaml:503-505`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

Consequently the robustness reported above was bought with a very small fault exposure — under 6% of envs carried any degraded thruster even at the end of training.

[EVIDENCE: effective per-thruster fail probability = `u * thruster_fail_prob` = 0.0771 x 0.10 = 0.00771 (Arm A) and 0.00959 (Arm B), so P(at least 1 of 6 faulted) = 4.54% / 5.62% and E[faulted per env] = 0.046 / 0.058; `thruster_fail_prob = 0.1` and `thruster_health_range = (0.0, 0.5)` from `params/env.yaml:503-505`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
