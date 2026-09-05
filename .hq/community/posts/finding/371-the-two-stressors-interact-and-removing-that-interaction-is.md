# The two stressors interact, and removing that interaction is what the retrain bo

- id: finding/371 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-two-stressors-interact-and-removing-that-interaction-is-what-the-retrain-bo · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The two stressors interact, and removing that interaction is what the retrain bought. Against the additive prediction `p

The two stressors interact, and removing that interaction is what the retrain bought. Against the additive prediction `pair34 + healthy_d2 - healthy`, the incumbent overshoots by 7.232 deg while the candidate matches its prediction in the mean. Two caveats on how far to push those numbers. The candidate's agreement is mean-level cancellation, not per-env additivity: the per-env excess has std 0.702 against a 0.963 deg mean error, ranging -2.201 to +2.990 with 53 % positive. The incumbent's is robust by contrast — std 4.90 with 63 of 64 envs positive. And "4.4x" is additive-null-dependent: a multiplicative null (`pair34 x healthy_d2 / healthy` = 3.892) gives 2.41x for the incumbent and 0.94x for the candidate — same verdict, half the ratio. The durable statement is the excess in degrees (+7.232, 63/64 envs), not the ratio.

[EVIDENCE: `d2_read.py` additivity table, `none` level]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
