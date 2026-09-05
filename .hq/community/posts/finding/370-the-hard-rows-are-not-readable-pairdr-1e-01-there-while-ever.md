# The `hard` rows are NOT readable. `pairDR = 1e-01` there while every CORE row of

- id: finding/370 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-hard-rows-are-not-readable-pairdr-1e-01-there-while-every-core-row-of · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The `hard` rows are NOT readable. `pairDR = 1e-01` there while every CORE row of the same arm pair is `0e+00`, so on thi

The `hard` rows are NOT readable. `pairDR = 1e-01` there while every CORE row of the same arm pair is `0e+00`, so on this config the two arms did not draw the same plant at `hard` and the delta mixes policy with exam. The mechanism is not established here and is not guessed at; the row is reported and excluded.

[EVIDENCE: `pairDR` column, `pair34_d2` at `hard` (1.09e-01) vs the 16 CORE rows at `0e+00`. The per-env sign count and the paired survival delta are confounded by the same plant mismatch, so all three columns are blanked, not just the delta]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
