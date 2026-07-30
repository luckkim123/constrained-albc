---
title: "The curriculum runs the same but reaches further on fault exposure: DORAEMON/suc"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The curriculum runs the same but reaches further on fault exposure: DORAEMON/suc

The curriculum runs the same but reaches further on fault exposure: DORAEMON/success_rate 0.809 vs 0.815, DORAEMON/ess_ratio 0.752 vs 0.773, DORAEMON/entropy_before -25.81 vs -27.01, DORAEMON/kl_step final 0.0000 vs 0.0006; fault_severity mean ends at 10.8% of range vs 7.7% (E-int and ArmA both ~7.7%) — the plant swap changed curriculum dynamics (+3.1 pp fault reach). All 21 dims are still EXPANDING at the final iteration (engine verdict), the family-wide under-converged-curriculum trait.

[EVIDENCE: tb_final.py final-window means, tags DORAEMON/success_rate ess_ratio entropy_before kl_step and DORAEMON/mean/fault_severity, both runs; analyze_training.py DORAEMON table verdict column EXPANDING on all dims]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

The curriculum runs the same but reaches further on fault exposure: doraemon_success_rate (TB tag DORAEMON/success_rate) 0.809 vs 0.815, DORAEMON/ess_ratio 0.752 vs 0.773, DORAEMON/entropy_before -25.81 vs -27.01, DORAEMON/kl_step final 0.0000 vs 0.0006; fault_severity mean ends at 10.8% of range vs 7.7% (E-int and ArmA both ~7.7%) — the plant swap changed curriculum dynamics (+3.1 pp fault reach). All 21 dims are still EXPANDING at the final iteration (engine verdict), the family-wide under-converged-curriculum trait.

[EVIDENCE: tb_final.py final-window means, tags DORAEMON/success_rate ess_ratio entropy_before kl_step and DORAEMON/mean/fault_severity, both runs; analyze_training.py DORAEMON table verdict column EXPANDING on all dims]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

The curriculum runs the same but reaches further on fault exposure: doraemon_success_rate (TB tag DORAEMON/success_rate) 0.809 vs 0.815, DORAEMON/ess_ratio 0.752 vs 0.773, DORAEMON/entropy_before -25.81 vs -27.01, DORAEMON/kl_step final 0.0000 vs 0.0006; fault_severity mean ends at 10.8% of range vs 7.7% (E-int and ArmA both ~7.7%) — the plant swap changed curriculum dynamics (+3.1 pp fault reach). All 21 dims are still EXPANDING at the final iteration (engine verdict), the family-wide under-converged-curriculum trait.

[EVIDENCE: tb_final.py final-window means, tags DORAEMON/success_rate ess_ratio entropy_before kl_step and DORAEMON/mean/fault_severity, both runs; analyze_training.py DORAEMON table verdict column EXPANDING on all dims]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
