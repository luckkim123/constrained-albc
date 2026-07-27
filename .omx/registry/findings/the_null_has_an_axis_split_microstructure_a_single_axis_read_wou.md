---
title: "The null has an axis-split microstructure a single-axis read would miss: roll ss"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T06:42:48.885806
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The null has an axis-split microstructure a single-axis read would miss: roll ss

The null has an axis-split microstructure a single-axis read would miss: roll ss_error improves at all 4 levels while pitch worsens at all 4 — sign-opposite axes, so the band buys no coherent tracking change, and per protocol the sub-floor deltas are NULL, never "better" or "worse". | level | roll d ss_error (deg) | pitch d ss_error (deg) | yaw d ss_error (rad/s) | |---|---|---|---| | none | -0.027 | +0.044 | +0.000 | | soft | -0.031 | +0.031 | +0.000 | | medium | -0.034 | +0.047 | -0.000 | | hard | -0.047 | +0.101 | -0.001 |

[EVIDENCE: compare.py paired, delta ss_error tables, all 4 DR levels]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
