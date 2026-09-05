# The only cross-metric changepoint the engine found in the whole run couples the 

- id: finding/342 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-only-cross-metric-changepoint-the-engine-found-in-the-whole-run-couples-the · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The only cross-metric changepoint the engine found in the whole run couples the encoder to the return: at iteration 2218

The only cross-metric changepoint the engine found in the whole run couples the encoder to the return: at iteration 2218, `z_std` steps down while `mean_reward` steps up — i.e. the latent tightened as the policy improved, right at the resume boundary (2050).

[EVIDENCE: `analyze_training.py --deep` `[CHANGEPOINTS] cross-metric`: `iter 2218: [2 metrics]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

The only cross-metric changepoint the engine found in the whole run couples the encoder to the return: at iteration 2218, `z_std` steps down while `mean_reward` steps up — i.e. the latent tightened as the policy improved, right at the resume boundary (2050).

[EVIDENCE: `analyze_training.py --deep` `[CHANGEPOINTS] cross-metric`: `iter 2218: [2 metrics]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

The only cross-metric changepoint the engine found in the whole run couples the encoder to the return: at iteration 2218, `z_std` steps down while `mean_reward` steps up — i.e. the latent tightened as the policy improved, right at the resume boundary (2050).

[EVIDENCE: `analyze_training.py --deep` `[CHANGEPOINTS] cross-metric`: `iter 2218: [2 metrics]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
