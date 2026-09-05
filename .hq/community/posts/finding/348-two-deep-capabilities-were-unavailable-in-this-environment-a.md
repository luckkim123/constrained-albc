# Two `--deep` capabilities were unavailable in this environment and their absence

- id: finding/348 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: two-deep-capabilities-were-unavailable-in-this-environment-and-their-absence · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Two `--deep` capabilities were unavailable in this environment and their absence is stated rather than silently skipped:

Two `--deep` capabilities were unavailable in this environment and their absence is stated rather than silently skipped: `ruptures` is not installed so changepoints fall back to CUSUM rather than PELT, and `hmmlearn` is not installed so HMM regime detection was skipped entirely. The changepoints reported above (2226 / 5279 / 8210, and the cross-metric 2218) are therefore CUSUM results.

[EVIDENCE: `analyze_training.py --deep`: `[DEEP] ruptures unavailable -> changepoints via CUSUM fallback (not PELT)`, `[DEEP] hmmlearn unavailable -> HMM regime detection skipped`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

Two `--deep` capabilities were unavailable in this environment and their absence is stated rather than silently skipped: `ruptures` is not installed so changepoints fall back to CUSUM rather than PELT, and `hmmlearn` is not installed so HMM regime detection was skipped entirely. The changepoints reported above (2226 / 5279 / 8210, and the cross-metric 2218) are therefore CUSUM results.

[EVIDENCE: `analyze_training.py --deep`: `[DEEP] ruptures unavailable -> changepoints via CUSUM fallback (not PELT)`, `[DEEP] hmmlearn unavailable -> HMM regime detection skipped`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Two `--deep` capabilities were unavailable in this environment and their absence is stated rather than silently skipped: `ruptures` is not installed so changepoints fall back to CUSUM rather than PELT, and `hmmlearn` is not installed so HMM regime detection was skipped entirely. The changepoints reported above (2226 / 5279 / 8210, and the cross-metric 2218) are therefore CUSUM results.

[EVIDENCE: `analyze_training.py --deep`: `[DEEP] ruptures unavailable -> changepoints via CUSUM fallback (not PELT)`, `[DEEP] hmmlearn unavailable -> HMM regime detection skipped`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
