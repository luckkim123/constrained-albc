---
title: "The only floor-crossing cell in the whole delta matrix is pitch ss_error at `har"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T06:42:48.885806
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The only floor-crossing cell in the whole delta matrix is pitch ss_error at `har

The only floor-crossing cell in the whole delta matrix is pitch ss_error at `hard` (+0.101 deg, REAL by DECISION_FLOORS) — but soft/medium/hard cross-run deltas are exam-confounded: eval.py static grades each run on its OWN learned DORAEMON box, so only the `none` level is a fair cross-run exam and the campaign's standing gate reads verdicts at `none` only.

[EVIDENCE: compare.py paired delta ss_error pitch hard = +0.101 REAL; wiki eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr; PLAN.md section 1 standing gate]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
