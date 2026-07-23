---
title: "`arm1` is the sharpest single result: it reaches its 0.10 floor by iter 1000 and"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `arm1` is the sharpest single result: it reaches its 0.10 floor by iter 1000 and

`arm1` is the sharpest single result: it reaches its 0.10 floor by iter 1000 and stays pinned, which happens in no other run of this lineage — with the bonus removed, 6 of 8 action dims end the run on a floor instead of 5.

[EVIDENCE: final `exp(log_std)` — A2 (arm0 0.10000, arm1 0.10000, thr0 0.10358, thr1 0.05, thr2 0.05, thr3 0.10799, thr4 0.05, thr5 0.05) vs anchor (arm0 0.10000, arm1 0.13034, thr0 0.12714, thr1 0.05, thr2 0.05, thr3 0.13062, thr4 0.05, thr5 0.05)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
