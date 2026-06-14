---
title: "Reward absolute scale is invariant to the ConstraintTRPO actor; only term ratios matter (3 un-normalized leak paths)"
tags: ["reward", "scale", "advantage-normalization", "trpo", "doraemon", "entropy-coef", "tuning"]
created: 2026-06-14T07:38:12.045031
updated: 2026-06-14T07:38:12.045031
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# Reward absolute scale is invariant to the ConstraintTRPO actor; only term ratios matter (3 un-normalized leak paths)

ConstraintTRPO actor learning is invariant to the ABSOLUTE scale of the reward; only term-to-term RATIOS matter. The recurring "scale = importance" tuning intuition is half-wrong for this codebase.
WHY (code-verified `envs/main/algorithms/constraint_trpo.py`, 2026-06-14):
- The actor surrogate `:461` `reward_surr = -(adv * ratio).mean()` consumes advantages that are STANDARDIZED to mean 0 / std 1 at `:423-426` (`advantages = (advantages - mean) / adv_std`). Multiply EVERY `Reward/*` by 10 -> returns x10 -> advantages x10 -> but `adv_std` x10 too -> the division cancels exactly. 0.1x cancels the same way.
- TRPO's natural-gradient step is renormalized to the `max_kl=0.005` trust region (`:539` `shs = 0.5 * nat_grad.dot(g)`), so even gradient MAGNITUDE cannot set step length. The actor is doubly scale-invariant.
- Therefore "make the whole reward bigger to learn harder/faster" does NOT hold in this algorithm. Uniform scaling of all terms is ~a no-op on the actor.
THE THREE UN-NORMALIZED LEAK PATHS (where absolute scale DOES change something):
1. Critic MSE `(returns - V).pow(2).mean()` (`:591`, value_loss_coef=1.0 `:601`) scales QUADRATICALLY (x100 for a x10 reward). Affects critic warmup/convergence speed, separate optimizer -> only indirect on actor.
2. Entropy bonus `-entropy_coef * mean_entropy` (`:479`) is added in REWARD UNITS (un-normalized, different unit than the standardized advantage). Bigger reward -> entropy term relatively smaller -> less exploration. BUT this baseline runs `entropy_coef=0.0` (default `:69`) so it is currently INERT. Becomes live only if entropy_coef is set nonzero.
3. DORAEMON success `episode_return >= performance_lb` (doraemon.py:306) compares RAW episode return, never normalized. A x10 reward clears the success bar trivially -> curriculum expands DR faster. This is the largest practical side-effect and the subtlest confound.
WHAT ACTUALLY SHAPES POLICY BEHAVIOR: the RATIO between terms (`k_att=9 : k_yaw=3.5 : k_thr=-0.35 : k_bias=-2.0`). Scaling att_rp ALONE (not all terms) survives normalization and re-weights the gradient direction. So "scale = importance" is TRUE read as relative ratio, FALSE read as absolute magnitude.
ACTION RULE for any reward-scale experiment: prefer changing term RATIOS, not the global magnitude. If absolute scale is ever changed, rescale `performance_lb` by the same factor or reward-scale and curriculum-difficulty confound (rule02 minimum-change-revert). Uniform global scaling alone is mostly an actor no-op + a DR-curriculum confound -- not a learning-strength lever.
GENERAL DEBUGGING HEURISTIC: in PPO/TRPO, the way scale leaks is through every term added in reward units OUTSIDE the advantage normalization (entropy bonus, critic MSE, any raw-return threshold). To predict whether a scale change matters, find the un-normalized terms.
