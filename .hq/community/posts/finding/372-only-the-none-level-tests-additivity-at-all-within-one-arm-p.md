# Only the `none` level tests additivity at all. Within one arm, `pair34` and `pai

- id: finding/372 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: only-the-none-level-tests-additivity-at-all-within-one-arm-pair34-and-pai · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Only the `none` level tests additivity at all. Within one arm, `pair34` and `pair34_d2` draw different plants at soft/me

Only the `none` level tests additivity at all. Within one arm, `pair34` and `pair34_d2` draw different plants at soft/medium/hard (`pairDR` 2, 4, 6), because the delay flag changes RNG consumption; at `none` no DR is applied, so the four configs are structurally paired. The excesses printed at the other three levels are confounded and are not used.

[EVIDENCE: intra-arm `pairDR` column: 0e+00 / 2e+00 / 4e+00 / 6e+00 across none/soft/medium/hard]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
