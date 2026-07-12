---
title: "reward/cost parallel structure: mostly mirroring, two real couplings (value grad-clip over the union throttles reward critic; feasibility J_C uses GAE-return so constraint level inherits lambda_c + cost-critic bias)"
tags: ["constraint", "constraint_trpo", "cost_critic", "reward_cost_parallel", "ipo", "grad_clip", "feasibility", "triage"]
created: 2026-07-12T08:06:08.383201
updated: 2026-07-12T08:32:10.674326
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

---

## Update (2026-07-12T08:32:10.674326)

## 2026-07-12 runtime triage — all couplings classified (C), NO code change

A follow-up session re-verified the couplings above with RUNTIME evidence (not just
code-reading) and classified each: (A) real defect / (B) stale docs / (C) intended-or-
intrinsic. An adversarial verifier (Opus) confirmed the disposition and surfaced a THIRD
instance of the same pattern. Result under the rule "only (A) proven by runtime evidence
gets touched": all (C), NO code change.

Runs analyzed: `logs/rsl_rl/albc_trpo_teacher/joint1_constraint/{trpo_avg_constraint_d05_260628_040906, trpo_cumul_constraint_260627_231709}` (main-task ConstraintTRPO+IPO, 5000 iters each; confirmed by `Constraint/*` + `Constraint/barrier_penalty` + attitude-only `Track/*` tags, no lin_vel-tracking tags).

### Coupling (1) — value grad-clip over the union (`constraint_trpo.py:601-605`) -> (C)
- Mechanism (verified): `value_prefixes` (`:160`) catches both `critic.` and `cost_critic.`
  -> `_value_params` (`:185`) is the UNION; single `total.backward()` then one
  `clip_grad_norm_(_value_params, 1.0)` (`:604`) couples the two critics' norms.
- (A) hypothesis (cost critic's larger rare-event gradient dominates the union norm and
  throttles reward-critic value learning) is REFUTED by outcome: reward `Loss/value_function`
  converges healthily 68 -> 1.13 (it1000) -> last50 mean 1.20/1.18 (std 0.14/0.06), no high
  plateau; cost `Loss/cost_value` last50 0.94/1.06, comparable magnitude, not dominating at
  convergence. [EVIDENCE: TB re-extracted, both runs]
- Two mechanistic reasons the coupling is structurally benign (beyond the outcome):
  (a) `clip_grad_norm_` multiplies the whole union by ONE scalar -> preserves the reward:cost
  gradient RATIO; it scales both equally and cannot differentially throttle the reward critic.
  (b) the value optimizer is Adam (`:186`), ~invariant to a uniform gradient rescale, so the
  per-parameter reward-critic step is barely perturbed.
- Ceiling (known): the discriminating measurement — reward vs cost critic grad-norm SPLIT —
  is NOT logged (only policy-side `Grad/*` + `Policy/encoder_grad_norm` exist), needs
  instrumentation + a training run (gated). But (A) requires BOTH norm-domination AND actual
  reward-value impairment; the latter is refuted, so the missing split cannot upgrade to (A).
  -> (C), no change. Optional upgrade: independent per-critic clips IF a run ever shows a
  reward-value throttle.

### Coupling (2) — feasibility judged from GAE-return (`:291,443,447,454,306-308`) -> (C)
- Mechanism (verified): `cost_returns` is GAE(cost_lam=0.95) return (`:291`); `violations`,
  `barrier_base`, adaptive thresholds all derive from `mean_cost_returns` (`:443/447/454/
  306-308`), so the constraint LEVEL inherits lambda_c bias + cost-critic estimation error.
  (Gradient direction `cost_surr` is separate; only the level is affected.)
- Intrinsic to any critic-based constrained-RL feasibility estimate — not a code defect;
  already documented in `docs/reference/constraints.md` §4.3.
- Feared active symptom (cost critic UNDER-estimates -> a truly-infeasible constraint reads
  barrier-feasible) — bounded by a NON-GATED physical cross-check: thruster_util is an
  Average constraint, budget 0.40 on peak thruster utilization (`mdp/constraints.py:188-203`).
  Raw physical `Dynamics/thr/util_mean` = 0.153, `Dynamics/thr/util_max` = 0.439 (last50).
  GAE margin 5.3 reconstructs to J_C ~= 34.7 vs d_k = 40 -> averaged peak ~= 0.35 vs budget
  0.40 (J_C/d_k ~= 0.87, near-boundary but feasible). For the barrier to hide a real
  violation the critic would need >13% systematic underestimation, and the modest raw
  utilization argues against a large hidden violation. Also lambda_c=0.95 is high, so the GAE
  cost return is dominated by OBSERVED costs -> structurally bounds the critic-bias term.
  [EVIDENCE: TB + constraints.py]
- Ceiling (known): the EXACT per-constraint MC-vs-GAE gap still needs a rollout with per-step
  cost + cost-value dump (gated Isaac Sim); that precise check is HELD. The non-gated proxy
  corroborates feasibility but is not the exact measurement. -> (C), no change.
- Note: `Dynamics/thr/util_max` 0.439 briefly exceeds budget 0.40, but the constraint is
  Average-type (discounted mean peak ~= 0.35), so an instantaneous worst-case peak above
  budget is not a violation.

### Coupling (3) (NEW, verifier-surfaced) — policy-side combined-surrogate union clip (`:521-533`) -> (C)
- Same pattern as (1) but on the ACTOR side: `loss = surrogate()` = reward_surr + barrier
  (cost) + entropy_bonus (`:480`); `g = flat_grad(loss, _policy_params)` (`:523`); then
  `g = g * (max_grad_norm/g_norm)` when `g_norm > 1.0` (`:531-533`) clips the union of
  reward+barrier+entropy gradients as one vector BEFORE conjugate gradient.
- In-frame per the "combined surrogate" listed in the parallel structure. Almost certainly
  (C): the TRPO step renormalizes via `step_dir = -sqrt(max_kl/shs)*nat_grad` (`:544`) under
  the KL trust region, so the pre-CG clip mainly CONDITIONS the CG direction rather than
  setting the final step magnitude (the trust region does). No runtime evidence of harm.
  -> (C), no change.

### (B) stale-docs — NOT triggered
`docs/reference/constraints.md` already documents both original couplings in the same
language: §4.3 (feasibility / under-estimating cost critic reads feasible) and §4.6 (union
`clip_grad_norm_` throttle). No doc update needed for (1)/(2). Coupling (3) is newly named
here; docs mention is optional, not required (it is (C)).

### Bottom line
(A): none. (B): none. (C): couplings (1), (2), (3). No code touched. The parallel structure's
residual couplings are either benign-by-construction ((1): ratio-preserving clip + Adam;
(3): trust-region renorm) or intrinsic to estimator-based constrained RL ((2): bounded
non-gated by physical utilization, exact gap gated). Adversarial verifier (Opus) verdict:
ACCEPT — safe to finalize, no change. Minor: cost critic actually has K=11 heads
(prompt/§1.2 said 10); immaterial (point is K>1).

