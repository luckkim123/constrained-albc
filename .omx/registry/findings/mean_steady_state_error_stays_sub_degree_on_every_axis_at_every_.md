---
title: "Mean steady-state error stays sub-degree on every axis at every DR level; the su"
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

# Mean steady-state error stays sub-degree on every axis at every DR level; the su

Mean steady-state error stays sub-degree on every axis at every DR level; the summary.json per-env CV rises from ~0.2–0.3 (none) to ~2.0–2.4 (hard), flagging a dispersion that grows with DR (roll worst, then pitch; yaw-rate ~0). CV alone is only a flag — the heavy tail is confirmed on raw data below.

[EVIDENCE: summary.json — att_norm ss_error 0.53°/CV0.23 (none) -> 0.72°/CV2.13 (hard); roll hard CV 2.42; pitch hard CV 1.99]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

Mean steady-state error stays sub-degree on every axis at every DR level; the summary.json per-env CV rises from ~0.2–0.3 (none) to ~2.0–2.4 (hard), flagging a dispersion that grows with DR (roll worst, then pitch; yaw-rate ~0). CV alone is only a flag — the heavy tail is confirmed on raw data below.

[EVIDENCE: summary.json — att_norm ss_error 0.53°/CV0.23 (none) -> 0.72°/CV2.13 (hard); roll hard CV 2.42; pitch hard CV 1.99]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
