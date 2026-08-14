---
title: "The training-log diagnostic engine cannot diagnose this run type, reproducing th"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-05T09:49:50.734092
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The training-log diagnostic engine cannot diagnose this run type, reproducing th

The training-log diagnostic engine cannot diagnose this run type, reproducing the recorded gap exactly.

[EVIDENCE: `/isaac-sim/python.sh .omx/profile/analyze_training.py <run> --tier 3 --deep` returns `STATUS: HEALTHY / iters=0 / last_step=0` on a run with 1000 logged samples per tag, emitting no DIAGNOSIS, changepoint, plateau or regime line — it cannot resolve the iteration axis under the `student/` namespace]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

The training-log diagnostic engine cannot diagnose this run type, reproducing the recorded gap exactly.

[EVIDENCE: `/isaac-sim/python.sh .omx/profile/analyze_training.py <run> --tier 3 --deep` returns `STATUS: HEALTHY / iters=0 / last_step=0` on a run with 1000 logged samples per tag, emitting no DIAGNOSIS, changepoint, plateau or regime line — it cannot resolve the iteration axis under the `student/` namespace]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T07:04:05.217247)

The training-log diagnostic engine cannot diagnose this run type, reproducing the recorded gap exactly.

[EVIDENCE: `/isaac-sim/python.sh .omx/profile/analyze_training.py <run> --tier 3 --deep` returns `TIER 1 / STATUS: HEALTHY / iters=0 / last_step=0` on a run with 1000 logged samples per tag, emits no DIAGNOSIS, changepoint, plateau or regime line, and falls back to CUSUM because ruptures and hmmlearn are unavailable — it cannot resolve the iteration axis under the `student/` namespace]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

The training-log diagnostic engine cannot diagnose this run type, reproducing the recorded gap exactly.

[EVIDENCE: `/isaac-sim/python.sh .omx/profile/analyze_training.py <run> --tier 3 --deep` returns `TIER 1 / STATUS: HEALTHY / iters=0 / last_step=0` on a run with 1000 logged samples per tag, emits no DIAGNOSIS, changepoint, plateau or regime line, and falls back to CUSUM because ruptures and hmmlearn are unavailable — it cannot resolve the iteration axis under the `student/` namespace]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
