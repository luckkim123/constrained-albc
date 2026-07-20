---
title: "P-B1 (same lb=250 as the reference) did NOT hit the reference's feasibility stal"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-16T07:19:42.517477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# P-B1 (same lb=250 as the reference) did NOT hit the reference's feasibility stal

P-B1 (same lb=250 as the reference) did NOT hit the reference's feasibility stall: `mode` -2 (stall, reference) vs 0 (P-B1); doraemon_success_rate 0.40 (reference) vs 0.88 (P-B1); DORAEMON/ess_ratio 0.41 (reference) vs 0.76 (P-B1). This is the SAME stall signature the perflb200 probe (lb 250->200) targeted via a different single variable — here bias_ema observability alone cleared it on the unchanged lb=250. DORAEMON/entropy_before and DORAEMON/kl_step are not broken out as separate scalars in the engine's tier-3 summary line for either run (only the aggregate success/ess/mode triple is printed) — genuinely absent from the printed output for both runs.

[EVIDENCE: engine deep output "success=doraemon_success_rate ess_ratio=DORAEMON/ess_ratio mode=..." line, both runs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md

---

## Update (2026-07-16T07:19:42.517477)

P-B1 (same lb=250 as the reference) did NOT hit the reference's feasibility stall: `mode` -2 (stall, reference) vs 0 (P-B1); doraemon_success_rate 0.40 (reference) vs 0.88 (P-B1); DORAEMON/ess_ratio 0.41 (reference) vs 0.76 (P-B1). This is the SAME stall signature the perflb200 probe (lb 250->200) targeted via a different single variable — here bias_ema observability alone cleared it on the unchanged lb=250. DORAEMON/entropy_before and DORAEMON/kl_step are not broken out as separate scalars in the engine's tier-3 summary line for either run (only the aggregate success/ess/mode triple is printed) — genuinely absent from the printed output for both runs.

[EVIDENCE: engine deep output "success=doraemon_success_rate ess_ratio=DORAEMON/ess_ratio mode=..." line, both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
