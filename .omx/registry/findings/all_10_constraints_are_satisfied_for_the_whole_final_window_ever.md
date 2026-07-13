---
title: "All 10 constraints are satisfied for the whole final window (every normalized ma"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# All 10 constraints are satisfied for the whole final window (every normalized ma

All 10 constraints are satisfied for the whole final window (every normalized margin > 0); attitude / joint1_pos / cumul_yaw are the binding trio (margin ~1.0), the rest carry large slack.

[EVIDENCE: TB Constraint/margin/* final-200 all >0 — attitude 0.994, joint1_pos 0.997, cumul_yaw 1.000 tightest; others 1.98–9.64; Constraint/viol/* all negative]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

All 10 constraints are satisfied for the whole final window (every normalized margin > 0); attitude / joint1_pos / cumul_yaw are the binding trio (margin ~1.0), the rest carry large slack.

[EVIDENCE: TB Constraint/margin/* final-200 all >0 — attitude 0.994, joint1_pos 0.997, cumul_yaw 1.000 tightest; others 1.98–9.64; Constraint/viol/* all negative]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
