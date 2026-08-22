---
title: "OOD does not invert the in-distribution ranking, it dissolves it. `model_7500` b"
tags: ["auto-captured"]
created: 2026-08-14T08:13:07.299190
updated: 2026-08-14T08:13:07.299190
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# OOD does not invert the in-distribution ranking, it dissolves it. `model_7500` b

OOD does not invert the in-distribution ranking, it dissolves it. `model_7500` beats `model_13400` decisively at `none` (t = +7.53, 6/64) but the two are statistically indistinguishable at `hard` (t = +0.63) and at `ood` (t = +1.59). The later checkpoint's deficit is confined to nominal physics, which is the least deployment-relevant condition.

[EVIDENCE: `~/paired_ood.py` over `data_ood.npz` / `data_hard.npz` in `static_260808_1620..1704`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
