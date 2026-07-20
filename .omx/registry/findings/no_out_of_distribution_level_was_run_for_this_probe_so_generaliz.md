---
title: "No out-of-distribution level was run for this probe, so generalization is read f"
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

# No out-of-distribution level was run for this probe, so generalization is read f

No out-of-distribution level was run for this probe, so generalization is read from the in-curriculum DR ladder only; that is sufficient here because H1/H2 are both pre-registered on the `none` level and the OOD arm belongs to the plant-refresh campaign, not to a curriculum-pace probe.

[EVIDENCE: `eval/static_260721_014808/` contains `data_{none,soft,medium,hard}.npz` and no `data_ood*`; `eval.py static` was invoked without `--ood`/`--ood-preset`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
