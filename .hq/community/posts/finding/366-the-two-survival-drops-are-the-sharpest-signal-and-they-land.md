# The two survival drops are the sharpest signal and they land on the delay config

- id: finding/366 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-two-survival-drops-are-the-sharpest-signal-and-they-land-on-the-delay-config · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The two survival drops are the sharpest signal and they land on the delay configs: -3.1 pp at `hard` on both `healthy_d1

The two survival drops are the sharpest signal and they land on the delay configs: -3.1 pp at `hard` on both `healthy_d1` and `healthy_d2`, i.e. two of 64 envs that finish the episode under `model_7500` and terminate under `model_9999`. Both exceed the 1.6 pp floor.

[EVIDENCE: `survD` column, `healthy_d1 hard` and `healthy_d2 hard`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
