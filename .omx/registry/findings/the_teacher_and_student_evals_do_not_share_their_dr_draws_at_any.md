---
title: "The teacher and student evals do not share their DR draws at any level except `n"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T04:31:12.085504
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The teacher and student evals do not share their DR draws at any level except `n

The teacher and student evals do not share their DR draws at any level except `none`, so the pre-registered decision floors cannot adjudicate this pair.

[EVIDENCE: data_<level>.npz `dr_*` arrays compared elementwise, teacher static_260804_092723 vs student static_260804_130704 — 0/24 keys differ at none, 23/24 at soft, medium and hard]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
