---
title: "WIDE is the best arm in the set at `none` on the mean (0.4948, below B2's 0.5137"
tags: ["auto-captured", "trpo_sdeint_b2wide_gru256_s30_260803_231320"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:16:03.279468
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# WIDE is the best arm in the set at `none` on the mean (0.4948, below B2's 0.5137

WIDE is the best arm in the set at `none` on the mean (0.4948, below B2's 0.5137 and C3's 0.5469) while being the worst at `hard`, so it reproduces and extends the opposite-directions shape Phase C flagged as this campaign's most decision-relevant pattern.

[EVIDENCE: the `tracking` table above; `configure_env_for_student` disables DORAEMON and installs a static hard DR box for distillation, which is what makes `none` the off-distribution end for every student here]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-03T15:16:03.279468)

WIDE is the best arm in the set at `none` on the mean (0.4948, below B2's 0.5137 and C3's 0.5469) while being the worst at `hard`, so it reproduces and extends the opposite-directions shape Phase C flagged as this campaign's most decision-relevant pattern.

[EVIDENCE: the `tracking` table above; `configure_env_for_student` disables DORAEMON and installs a static hard DR box for distillation, which is what makes `none` the off-distribution end for every student here]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
