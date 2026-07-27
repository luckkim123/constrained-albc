---
title: "Arm B's curriculum ran ~24% further than Arm A's, which confounds the arm compar"
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

# Arm B's curriculum ran ~24% further than Arm A's, which confounds the arm compar

Arm B's curriculum ran ~24% further than Arm A's, which confounds the arm comparison at the margin: Arm B saw a slightly harder fault distribution AND had the privileged channel.

[EVIDENCE: final `fault_severity` mean 0.0959 (B) vs 0.0771 (A), a 1.24x ratio; `success_rate`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

Arm B's curriculum ran ~24% further than Arm A's, which confounds the arm comparison at the margin: Arm B saw a slightly harder fault distribution AND had the privileged channel.

[EVIDENCE: final `DORAEMON/mean/fault_severity` 0.0959 (B) vs 0.0771 (A), a 1.24x ratio; the mechanism is `doraemon_success_rate` 0.753 (B) vs 0.579 (A), since DORAEMON expands faster when the policy copes]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

Arm B's curriculum ran ~24% further than Arm A's, which confounds the arm comparison at the margin: Arm B saw a slightly harder fault distribution AND had the privileged channel.

[EVIDENCE: final `DORAEMON/mean/fault_severity` 0.0959 (B) vs 0.0771 (A), a 1.24x ratio; the mechanism is `doraemon_success_rate` 0.753 (B) vs 0.579 (A), since DORAEMON expands faster when the policy copes]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
