---
title: "Both critic losses order the runs by exam difficulty, not by iteration budget: A"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-20T17:13:19.523263
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Both critic losses order the runs by exam difficulty, not by iteration budget: A

Both critic losses order the runs by exam difficulty, not by iteration budget: A1 (8000 iters, narrow box) sits at the 5k reference's level while extend8k (8000 iters, saturated box) is ~19% higher on `Loss/value_function` and ~15% higher on `Loss/cost_value`. The critics therefore corroborate the width manipulation independently of the DORAEMON rows.

[EVIDENCE: `Loss/value_function` A1 0.38312 vs ref5k 0.38568 (-0.7%) vs extend8k 0.45641 (+19.1% over A1); `Loss/cost_value` A1 0.77106 vs ref5k 0.79675 vs extend8k 0.91446 (+18.6% over A1)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
