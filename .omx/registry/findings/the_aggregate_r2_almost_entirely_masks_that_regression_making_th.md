---
title: "The aggregate `R2` almost entirely masks that regression, making this the fifth "
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

> # SUPERSEDED 2026-08-14 -- same run, same report, and this page's campaign claim was retracted.
>
> `the_aggregate_r2_almost_entirely_masks_that_regression_and_it_ma.md` (16 minutes later,
> 2026-08-03T15:16, and updated again on 08-04) covers the **identical** measurement: same run
> `trpo_sdeint_b2wide_gru256_s30_260803_231320`, same source report `diagnose-20260803-235022`,
> same numbers (-0.0164 / -0.1020 / +0.1440 / +0.2460 / 0.6626 -> 0.7362).
>
> The difference is the claim this page makes and that one withdraws. Here: **"the fifth
> denominator artifact in this campaign"**. There: the direction claim is explicitly *bounded to
> the instances actually on record* -- the Phase C d3 finding and its aggregate finding, both in
> `diagnose-20260803-223517` -- with **"no exhaustive campaign tally is asserted"**.
>
> So "fifth in this campaign" is an unbacked count. Read the later page. This one is a duplicate
> whose only unique content is the overclaim.


# The aggregate `R2` almost entirely masks that regression, making this the fifth 

The aggregate `R2` almost entirely masks that regression, making this the fifth denominator artifact in this campaign and the first where the artifact hides a LOSS rather than manufacturing a gain: the raw delta of -0.0164 reads as "no change" while the error-only delta is -0.1020.

[EVIDENCE: the decomposition table above; `1 - sum(mse_WIDE)/sum(var_B2)` = +0.1440 against B2's own +0.2460, with `sum(Var)` 0.6626 -> 0.7362]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
