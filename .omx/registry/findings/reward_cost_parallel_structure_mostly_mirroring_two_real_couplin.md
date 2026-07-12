---
title: "reward/cost parallel structure: mostly mirroring, two real couplings (value grad-clip over the union throttles reward critic; feasibility J_C uses GAE-return so constraint level inherits lambda_c + cost-critic bias)"
tags: ["constraint", "constraint_trpo", "cost_critic", "reward_cost_parallel", "ipo", "grad_clip", "feasibility"]
created: 2026-07-12T08:06:08.383201
updated: 2026-07-12T08:06:08.383201
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# reward/cost parallel structure: mostly mirroring, two real couplings (value grad-clip over the union throttles reward critic; feasibility J_C uses GAE-return so constraint level inherits lambda_c + cost-critic bias)

ConstraintTRPO mirrors the reward pipeline onto K cost channels (cost GAE, timeout
bootstrap, a multi-head cost critic, a combined surrogate). Code-reading during the
2026-07-12 constraint deep-dive settled whether that parallelism is sound and where
"parallel" is actually "shared".

## Verdict: the parallelism is theoretically justified, not lazy reuse

reward-return and cost-return are the SAME object E[sum gamma^t signal] <= budget, so
running cost-GAE identical to reward-GAE is the standard CPO/PCPO/IPO reduction. The code
correctly SEPARATES what must differ and only MIRRORS what is genuinely symmetric:
- gamma/lambda are independent (`cost_gamma=0.99`, `cost_lam=0.95` vs reward `gamma`/`lam`).
  Right, because gamma_c is a SAFETY HORIZON, a different semantic than the reward discount.
- critic params are disjoint: `self.critic` (out=1) and `self.cost_critic` (out=K) are two
  independent MLPs, NO shared backbone (`encoder/_policy_base.py:86,91`). The `value_backbone.`
  entry in `value_prefixes` is a classification catch, not a real shared trunk in
  `ALBCActorCriticEncoder`.
- advantage standardization diverges on purpose: reward uses the `1e-8` guard, cost uses the
  `min=1.0` floor (`constraint_trpo.py:437` vs `:424`) because binary-indicator cost columns
  have near-zero std and would 1e8-amplify.

## Two places where "parallel" is a REAL coupling (both code-verified, neither a bug)

1. [CODE] Value grad-clip is over the UNION of both critics. The value update does
   `total = L_V + L_VC; total.backward(); clip_grad_norm_(self._value_params, max_grad_norm=1.0);
   value_optimizer.step()` (`constraint_trpo.py:601-605`). `self._value_params` is reward-critic
   + cost-critic together. Params are disjoint so backward() does not cross-couple, BUT the single
   union grad-clip does: cost_critic (K=10 heads, rare-event targets) can dominate the combined
   norm, and when the union norm > 1.0 the clip scales BOTH critics by the same factor -> a noisy
   cost critic can throttle the reward critic's effective step. Flagged, not proven harmful;
   confirm with a runtime value-group grad-norm split (is the norm cost-critic-dominated? does the
   clip bite most steps?). Minimal fix IF confirmed: clip each param-group independently, or raise
   max_grad_norm.

2. [CODE] Feasibility level Ĵ_C is a GAE-return estimator, not the true MC cost return.
   `cost_returns = cost_advantage + cost_value` (`constraint_trpo.py:291`), and its mean
   `mean_cost_returns` drives `barrier_base`, `violations`, and the adaptive threshold
   (`:443,447,454`). So the constraint-satisfaction judgment inherits the `cost_lam=0.95` bias
   AND the cost critic's estimation error. On the reward side a biased value only costs
   policy-gradient efficiency; on the COST side an under-estimating cost critic makes the barrier
   read feasible when the true cost return already exceeds the budget -> an estimator-driven
   VIOLATION risk. Inherent to critic-based constrained RL, not a defect. Minimal fix IF a run
   shows systematic under-estimation: use a raw MC discounted cost sum for the feasibility LEVEL
   while keeping GAE for the gradient direction.

## prob/avg "no distinction" claim, refined

The optimizer has zero prob-vs-avg branches, and that is CORRECT (a probabilistic constraint is
just an average constraint on a {0,1} indicator cost; the expectation is smooth in theta). But
"no distinction" is true only at the OPTIMIZER-LOGIC level: (a) the `min=1.0` std floor is
implicitly binary-aware, (b) indicator costs are gradient-DARK in deep slack (zero signal once
never-violated), which is part of why the §9 experimental finding shows attitude/cumul_yaw
"fully inert" (J_C/d_k = 0.003 / 0.000). A continuous cost would keep a small shaping gradient;
binary gives exactly zero. This is by design (a safety constraint should only bound violation
frequency, not shape the interior), so it is correct, but docs saying "completely
distinction-free" slightly over-claim.

Work order with the confirm-then-fix steps for couplings 1 and 2:
`.sp/plans/PROMPT_constraint_reward_cost_parallel_coupling_triage.md`.

