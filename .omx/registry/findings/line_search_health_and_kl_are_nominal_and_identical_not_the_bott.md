---
title: "line-search health and KL are nominal and identical (not the bottleneck); the TR"
tags: ["auto-captured", "trpo_perflb200_260715_023744"]
created: 2026-07-15T04:54:53.987453
updated: 2026-07-15T04:54:53.987453
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# line-search health and KL are nominal and identical (not the bottleneck); the TR

line-search health and KL are nominal and identical (not the bottleneck); the TRPO step lands cleanly, so the collapse is not a failed-update artifact.

[EVIDENCE: engine TIER1 `Policy/line_search_success`=1.00 both; TIER3 `kl=0.00` (perflb) / `0.01` (baseline); `Policy/surrogate_loss`/`Grad/actor_step`/`Grad/sigma_step` show no run-to-run divergence and no engine anomaly flag]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md
