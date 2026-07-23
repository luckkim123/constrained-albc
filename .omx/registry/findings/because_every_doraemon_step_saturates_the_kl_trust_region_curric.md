---
title: "Because every DORAEMON step saturates the KL trust region, curriculum expansion "
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

# Because every DORAEMON step saturates the KL trust region, curriculum expansion 

Because every DORAEMON step saturates the KL trust region, curriculum expansion in this config is SCHEDULE-bound, not success-bound — the 7.2% lower success rate in A3 changed nothing about the DR box it trained in. This makes the A3-vs-anchor eval comparison fair, and it also means "DORAEMON health" cannot discriminate runs in this campaign.

[EVIDENCE: kl_step == 0.1200 at all 18 updates in both runs despite success_rate 0.8138 vs 0.8773; terminal Beta identical]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
