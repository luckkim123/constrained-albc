---
title: "Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger "
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-16T06:36:01.268339
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger 

Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger AC fraction (ss_jitter up to ~0.6-0.7x ss_error). ss_jitter grew in absolute terms post-TAM (roll hard 0.181 -> 0.270 +49%, pitch hard 0.097 -> 0.163 +68%) but stays a minority fraction of ss_error, so there is no oscillatory blow-up.

[EVIDENCE: summary.json MATCHED hard roll ss_error 0.571 vs ss_jitter 0.270 (0.47x); MATCHED pitch none ss_jitter 0.146/ss_error 0.207=0.71, hard 0.163/0.295=0.55; void hard ss_jitter roll 0.181 -> 0.270, pitch 0.097 -> 0.163]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md

---

## Update (2026-07-16T06:36:01.268339)

Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger AC fraction (ss_jitter up to ~0.6-0.7x ss_error). ss_jitter grew in absolute terms post-TAM (roll hard 0.181 -> 0.270 +49%, pitch hard 0.097 -> 0.163 +68%) but stays a minority fraction of ss_error, so there is no oscillatory blow-up.

[EVIDENCE: summary.json MATCHED hard roll ss_error 0.571 vs ss_jitter 0.270 (0.47x); MATCHED pitch none ss_jitter 0.146/ss_error 0.207=0.71, hard 0.163/0.295=0.55; void hard ss_jitter roll 0.181 -> 0.270, pitch 0.097 -> 0.163]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
