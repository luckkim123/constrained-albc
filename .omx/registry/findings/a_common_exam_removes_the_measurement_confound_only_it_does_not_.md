---
title: "A common exam removes the MEASUREMENT confound only. It does not make these two "
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# A common exam removes the MEASUREMENT confound only. It does not make these two 

A common exam removes the MEASUREMENT confound only. It does not make these two policies a same-config/different-budget pair: they are optima of DIFFERENT training distributions, and no eval-time flag can remove that. So "the transient trade is real" means precisely *it survives a fair exam* — it does NOT attribute the trade to the observation change.

[EVIDENCE: workspace convention `cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov` SCOPE LIMIT section; quantified here by the 20/20-parameter DR width table above (mean variance ratio 2.23x) — P-B1 trained against a materially wider distribution than the reference]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

A common exam removes the MEASUREMENT confound only. It does not make these two policies a same-config/different-budget pair: they are optima of DIFFERENT training distributions, and no eval-time flag can remove that. So "the transient trade is real" means precisely *it survives a fair exam* — it does NOT attribute the trade to the observation change.

[EVIDENCE: workspace convention `cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov` SCOPE LIMIT section; quantified here by the 20/20-parameter DR width table above (mean variance ratio 2.23x) — P-B1 trained against a materially wider distribution than the reference]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
