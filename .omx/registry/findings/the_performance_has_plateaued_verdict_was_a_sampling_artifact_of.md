---
title: "The \"performance has plateaued\" verdict was a sampling artifact of a 4-point eva"
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

# The "performance has plateaued" verdict was a sampling artifact of a 4-point eva

The "performance has plateaued" verdict was a sampling artifact of a 4-point eval schedule. The seven-point curve is a regression at 9000 followed by monotone recovery, not an oscillation around a flat level; the run was stopped mid-recovery.

[EVIDENCE: `eval/static_260808_153741` (9000), `static_260808_154936` (11000), `static_260808_160132` (13400) added to the four pre-approved points; paired per-env series below]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
