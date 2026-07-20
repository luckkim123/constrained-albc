---
title: "The expansion did NOT continue to the end of training — it SATURATED the config "
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:53:52.371991
updated: 2026-07-20T03:58:45.859914
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The expansion did NOT continue to the end of training — it SATURATED the config 

The expansion did NOT continue to the end of training — it SATURATED the config box at iter 7000 and then froze for the final 1000 iterations. All 20 DORAEMON parameters ended at Beta(a=1.0, b=1.0), i.e. exactly uniform over their full configured ranges. DORAEMON is entropy-maximizing, so uniform-over-the-box is its terminal state, not a stall. (This SUPERSEDES the prior plot-based reading that the ±1σ bands were "still widening at 8000" — that mistook an asymptote for growth; the terminal-state file settles it.)

[EVIDENCE: train/doraemon_state.pt (step_count=8000) dist_a == dist_b == 1.0000 for all 20 params; TB DORAEMON/entropy_before + DORAEMON/mean|std ocean_current_strength]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md

---

## Update (2026-07-20T03:58:45.859914)

The expansion did NOT continue to the end of training — it SATURATED the config box at iter 7000 and then froze for the final 1000 iterations. All 20 DORAEMON parameters ended at Beta(a=1.0, b=1.0), i.e. exactly uniform over their full configured ranges. DORAEMON is entropy-maximizing, so uniform-over-the-box is its terminal state, not a stall. (This SUPERSEDES the prior plot-based reading that the ±1σ bands were "still widening at 8000" — that mistook an asymptote for growth; the terminal-state file settles it.)

[EVIDENCE: train/doraemon_state.pt (step_count=8000) dist_a == dist_b == 1.0000 for all 20 params; TB DORAEMON/entropy_before + DORAEMON/mean|std ocean_current_strength]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md
