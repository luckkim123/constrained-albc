---
title: "The critic pair is the largest training-side delta: Loss/value_function 0.44 -> "
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T10:30:03.859588
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The critic pair is the largest training-side delta: Loss/value_function 0.44 -> 

The critic pair is the largest training-side delta: Loss/value_function 0.44 -> 0.52 (+18%) and Loss/cost_value 0.77 -> 0.96 (+25%) — consistent with the new per-env parameter (max_thrust_scale) being INVISIBLE to the asymmetric critic: the 28D privileged obs was deliberately left unchanged (one-variable rule), so ceiling variation is irreducible env-conditioned noise to both critics.

[EVIDENCE: engine TIER 3 Losses — anchor value=0.44 cost_val=0.77 vs B0c value=0.52 cost_val=0.96]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

The critic pair is the largest training-side delta: Loss/value_function 0.44 -> 0.52 (+18%) and Loss/cost_value 0.77 -> 0.96 (+25%) — consistent with the new per-env parameter (max_thrust_scale) being INVISIBLE to the asymmetric critic: the 28D privileged obs was deliberately left unchanged (one-variable rule), so ceiling variation is irreducible env-conditioned noise to both critics.

[EVIDENCE: engine TIER 3 Losses — anchor value=0.44 cost_val=0.77 vs B0c value=0.52 cost_val=0.96]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
