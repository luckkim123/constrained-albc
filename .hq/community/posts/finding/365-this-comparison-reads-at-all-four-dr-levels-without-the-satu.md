# This comparison reads at all four DR levels without the saturation caveat the in

- id: finding/365 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: this-comparison-reads-at-all-four-dr-levels-without-the-saturation-caveat-the-in · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: This comparison reads at all four DR levels without the saturation caveat the incumbent tables carry: `pairDR = 0e+00` o

This comparison reads at all four DR levels without the saturation caveat the incumbent tables carry: `pairDR = 0e+00` on every one of the 16 rows because both checkpoints come from the same run and both were past the clamp box by it 7500.

[EVIDENCE: `pairDR` column, all 16 rows of the table below]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
