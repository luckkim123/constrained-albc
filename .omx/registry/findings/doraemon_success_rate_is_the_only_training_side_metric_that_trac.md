---
title: "`DORAEMON/success_rate` is the only training-side metric that tracks the eval ex"
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

# `DORAEMON/success_rate` is the only training-side metric that tracks the eval ex

`DORAEMON/success_rate` is the only training-side metric that tracks the eval excursion — it bottoms at 0.5743 in the 9.25-10k window and recovers to ~0.60 by the end, mirroring the exam curve. The amplitude is ~3% against a 34% eval swing, so it is a weak correlate, not a usable detector.

[EVIDENCE: window table in the reward section; success_rate 0.6207 / 0.5933 / 0.5966 / 0.5877 / **0.5743** / 0.5794 / 0.6018 / 0.5963]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
