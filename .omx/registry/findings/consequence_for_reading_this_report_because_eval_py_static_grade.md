---
title: "CONSEQUENCE for reading this report: because `eval.py static` grades each run on"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# CONSEQUENCE for reading this report: because `eval.py static` grades each run on

CONSEQUENCE for reading this report: because `eval.py static` grades each run on its own learned DR box, A4's soft/medium/hard columns are a HARDER exam than the anchor's, so those magnitudes are inflated. The `none` level applies no DR at eval time and so carries no EVAL-TIME confound — and the band was written on `none` precisely for this reason. A training-time curriculum difference could in principle still colour nominal behaviour, so `none` is confound-REDUCED, not confound-free; with the measured deltas 15-40x outside the band, that residual cannot account for the result. The verdict does not rest on the confounded columns.

[EVIDENCE: DR box difference above; workspace rule that eval.py static uses each run's own learned box]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
