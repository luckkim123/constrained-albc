---
title: "performance_lb recon needs ZERO new rollouts: doraemon_state.pt already carries buffer_returns (the 260608 p25 method)"
tags: ["p-a2", "doraemon", "performance_lb", "recon", "episode-return", "method"]
created: 2026-07-16T05:49:26.443412
updated: 2026-07-16T05:49:26.443412
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# performance_lb recon needs ZERO new rollouts: doraemon_state.pt already carries buffer_returns (the 260608 p25 method)

# performance_lb recon needs ZERO new rollouts: doraemon_state.pt already carries buffer_returns

The P-A2 lead was parked as "eval.py has no episode-return distribution -> needs new analysis code"
(session log 2026-07-15, wiki no-op query commit b176d8f). That conclusion was correct ABOUT eval.py
and wrong about the workspace: the data was already on disk the whole time.

[FINDING] DORAEMON's EpisodeBuffer is checkpointed into every run's `doraemon_state.pt`. Top-level
keys: dist_a, dist_b, step_count, total_episodes, buffer_xi (2000,20), `buffer_returns` (2000,),
`buffer_success` (2000,), buffer_log_probs, buffer_write_idx. `buffer_returns` holds the last 2000
COMPLETED TRAINING episodes' returns -- 30s episodes with mid-episode command resample -- which is
exactly the quantity `success = episode_return >= performance_lb` gates on (doraemon.py:306). So the
260608-style recon (lb = the buffer's p25) is a torch.load + np.percentile, not a new rollout harness.
[EVIDENCE: torch.load on experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/*/train/doraemon_state.pt, all 4 posttam runs, 2026-07-16]
[CONFIDENCE: HIGH]

[FINDING] The read is self-validating: stored `buffer_success` equals `(buffer_returns >= lb_used)`
at 100% agreement on all four posttam runs, and the recomputed success rate reproduces each run's
reported `doraemon_success_rate` exactly (reference 0.3955 ~ the reported 0.40; P-B1 0.8825 ~ 0.88).
That agreement is also what pins down which lb each run actually trained with, without trusting a
launch record.
[EVIDENCE: same torch.load, buffer_success vs (buffer_returns >= lb) elementwise, 4 runs]
[CONFIDENCE: HIGH]

Measured distributions (n=2000 each, end of training):

| run | min | p5 | p25 | median | p95 | lb used | success |
|:---|---:|---:|---:|---:|---:|---:|---:|
| trpo_baseline_260714_192020 (bias_ema OFF) | -28.8 | 91.7 | 212.0 | 241.2 | 282.0 | 250 | 0.3955 |
| trpo_biasema_260715_142543 (bias_ema ON) | 29.6 | 237.1 | 261.8 | 274.9 | 302.6 | 250 | 0.8825 |
| trpo_perflb200_260715_023744 | -64.0 | 66.9 | 189.5 | 229.5 | 276.4 | 200 | 0.7055 |
| trpo_perflb200-moreiters_260715_195227 (8000it) | -52.0 | 21.8 | 134.8 | 199.2 | 264.3 | 200 | 0.4955 |

# Scope / what this does NOT settle

This is the 260608-style recon (buffer p25), NOT the paper's App A.1 rule (J_LB ~= 80% of a **no-DR
nominal** return). The buffer is recorded under whatever DR the run had REACHED, so it is not a no-DR
measurement. App A.1 remains never-done (see `doraemon_alpha_is_a_feasibility_floor...` item 5).
Doing it properly still needs a no-DR rollout with the TRAINING episode structure -- and `eval.py`
cannot supply that: it forces play_mode=True, vel_cmd_resample_steps=0, and overrides
episode_length_s from the trajectory schedule (eval.py:962-963, 978, 1595-1596, 1980-1981), so an
eval-none return is a different quantity from the training return lb gates on.

Reusable script pattern (no repo tool exists; system python3 has no torch, use /isaac-sim/python.sh):
load doraemon_state.pt -> d["buffer_returns"].numpy() -> np.percentile(r, [5,25,50,95]).

