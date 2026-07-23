---
title: "The intervention separates cleanly into a DC win and an AC/transient loss: `ss_e"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The intervention separates cleanly into a DC win and an AC/transient loss: `ss_e

The intervention separates cleanly into a DC win and an AC/transient loss: `ss_error` improves on roll and pitch at every DR level while `os_env_mean` on roll and `ss_jitter` on pitch degrade at every DR level.

[EVIDENCE: summary.json all four levels — roll ss_error -6/-14/-5/-2%, pitch ss_error -47/-43/-27/+0%; roll os_env_mean +26/+13/+8/+4%; pitch ss_jitter +9/+8/+27/+50%]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
