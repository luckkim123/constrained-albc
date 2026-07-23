---
title: "A5 took 19 DORAEMON expansions vs the anchor's 18 -- the SAME extra-expansion pa"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-23T02:21:27.244561
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# A5 took 19 DORAEMON expansions vs the anchor's 18 -- the SAME extra-expansion pa

A5 took 19 DORAEMON expansions vs the anchor's 18 -- the SAME extra-expansion pattern as A4: the gate fired at iter 250 where the anchor's first was 500, every step at the 0.12 KL cap. A5 therefore trained on, and is examined on, a slightly WIDER DR box, so its soft/medium/hard columns are a marginally harder exam than the anchor's; the `none` column carries no eval-time DR and is the clean comparison.

[EVIDENCE: TB DORAEMON/kl_step nonzero steps -- A5 at 250..4750 (19 values, all 0.12) vs anchor 500..4750 (18)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

A5 took 19 DORAEMON expansions vs the anchor's 18 -- the SAME extra-expansion pattern as A4: the gate fired at iter 250 where the anchor's first was 500, every step at the 0.12 KL cap. A5 therefore trained on, and is examined on, a slightly WIDER DR box, so its soft/medium/hard columns are a marginally harder exam than the anchor's; the `none` column carries no eval-time DR and is the clean comparison.

[EVIDENCE: TB DORAEMON/kl_step nonzero steps -- A5 at 250..4750 (19 values, all 0.12) vs anchor 500..4750 (18)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
