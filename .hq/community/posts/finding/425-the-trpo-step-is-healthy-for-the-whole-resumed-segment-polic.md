# The TRPO step is healthy for the whole resumed segment: `Policy/line_search_succ

- id: finding/425 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-trpo-step-is-healthy-for-the-whole-resumed-segment-policy-line_search_succ · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The TRPO step is healthy for the whole resumed segment: `Policy/line_search_success` 1.00 on every iteration, `Loss/kl` 

The TRPO step is healthy for the whole resumed segment: `Policy/line_search_success` 1.00 on every iteration, `Loss/kl` 0.0047 against `max_kl` 0.005 (the trust region is used, not hit), `Policy/surrogate_loss` −0.158, `Policy/clip_fraction` 0.0006, actor step norm `Grad/actor_step` 0.071, `Grad/sigma_step` 0.0067, learning rate constant at 1e-3. The engine's `[TIER 1]` flags `entropy −1.52 COLLAPSED` and `noise_std 0.20 LOW`; `Policy/mean_noise_std` is 0.203 against a `min_std` floor of 0.05, so the policy is not on the floor, and the same two flags appeared on the p3b teacher that beat the incumbent. `Policy/entropy` fell −0.78 → −1.43 over the segment, with the cross-metric changepoint at 5596 (entropy and noise up together) and 8545 (both down) bracketing the phase where the curriculum widened fastest.

[EVIDENCE: `tbread.py` seg 2 windows; `analyze_training.py` `[TIER 1] Core Health` (seg 2: `ls_success 1.00`, `noise_std 0.20 LOW`, `entropy −1.52 COLLAPSED`), `[CONFIG]` `max_kl=0.005, entropy_coef=0.003, min_std=0.05`; `[CHANGEPOINTS]` 5596, 8545]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
