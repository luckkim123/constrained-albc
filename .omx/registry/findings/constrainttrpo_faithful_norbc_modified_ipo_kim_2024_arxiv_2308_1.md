---
title: "ConstraintTRPO = faithful NORBC Modified-IPO (Kim 2024, arXiv:2308.12517); standardized-vs-raw barrier + soft feasibility are NORBC design not bugs; only the 1e-8 barrier clamp is code-level (no functional fix)"
tags: ["constraint_trpo", "NORBC", "IPO", "barrier", "provenance", "feasibility"]
created: 2026-07-12T09:14:05.788615
updated: 2026-07-12T09:14:05.788615
sources: ["arXiv:2308.12517v4", "arXiv:1910.09615", "CPO-Achiam-2017"]
links: ["reward_cost_parallel_structure_mostly_mirroring_two_real_couplin.md", "constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# ConstraintTRPO = faithful NORBC Modified-IPO (Kim 2024, arXiv:2308.12517); standardized-vs-raw barrier + soft feasibility are NORBC design not bugs; only the 1e-8 barrier clamp is code-level (no functional fix)

The `ConstraintTRPO` optimizer (`constrained_albc/envs/main/algorithms/constraint_trpo.py`) is
a FAITHFUL implementation of NORBC's "Modified IPO", not a bespoke or bolted-together algorithm.
Source (in the file's own docstring, L16-18): Kim, Oh, Lee, Choi, Ji, Jung, Youm, Hwangbo,
"Not Only Rewards But Also Constraints: Applications on Legged Robot Locomotion", arXiv:2308.12517v4,
2024 (KAIST Hwangbo lab). Local copy: `/workspace/references/NORBC - Not Only Rewards But Also Constraints/`.
Established during the 2026-07-12 constraint deep-dive after an independent critic flagged two
theoretical "soft spots"; consulting the NORBC paper resolved both as design, not code defects.

## Code <-> NORBC equation correspondence (all verified against disk)

| Code | NORBC (Sec IV-B) | match |
|:---|:---|:---|
| `d_k = D_k/(1-cost_gamma)` (`:147`) | Eq. (8) discounted budget | yes |
| `barrier_base = adaptive_d_k - mean_cost_returns` (raw, `:454`) + `cost_surrs = (1/(1-gamma)) * mean(ratio * A_C_standardized)` (`:462`) | Eq. (10): `log(d_k - (J_C(pi_i) + (1/(1-gamma)) E[A_C]))/t` | yes |
| `adaptive_d_k = max(d_k, J_C + alpha*d_k)` (`:308`) | Eq. (11) adaptive thresholding | yes |
| `cost_critic = MLP(obs, num_constraints, ...)` (`_policy_base.py:91`), reward critic separate (`:86`) | multi-head cost value + separate V | yes |
| Fisher = pure KL Hessian, CG, line search (`:357,536,564`) | TRPO step (NORBC uses TRPO, not IPO's PPO) | yes |

## The two flagged "soft spots" are NORBC's deliberate design, NOT bugs

**(a) Barrier margin mixes a RAW level with a STANDARDIZED delta -- this is NORBC Eq. (10) verbatim.**
`barrier_base` uses raw `J_C(pi_i)` (Eq. 11 defines it as `E[C_k]/(1-gamma)`, a physical cost return);
the correction term uses the STANDARDIZED cost advantage (NORBC Sec IV-B, "each advantage function
undergoes standardization and zero-mean normalization before the policy gradient"). So the raw-vs-
standardized asymmetry is the paper's formulation, not a faithfulness bug. NORBC justifies it: the
zero-mean normalization makes `E[A_C] ~ 0` at ratio=1, so the barrier argument ~ `d_k^i - J_C >= alpha*d_k > 0`
=> the problem is ALWAYS feasible at the start of every iteration (NORBC's "always feasible" claim).
The standardization (divide by std) is NORBC's gradient-conditioning trick to stack 10+ constraints
stably (their scalability goal). Consequence still holds -- for a constraint whose cost-advantage
std>1 the effective boundary is inflated (more permissive) -- but that is a property of the published
method, dormant unless a constraint's runtime cost-adv std actually exceeds 1. Supersedes the earlier
"possible faithfulness bug vs NORBC" worry: RETRACTED, the code is faithful.
See [[reward_cost_parallel_structure_mostly_mirroring_two_real_couplin]], [[constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli]].

**(b) Soft (non-CPO) feasibility is NORBC's acknowledged trade-off.** The constraint is a soft
log-barrier inside the surrogate + a TRPO natural-gradient step; the line search (`:406`) only checks
`(old_loss-new_loss)>0 and KL<=delta` over the full surrogate, never a separate constraint check.
This is weaker than CPO's per-update QP feasibility -- but NORBC never claims CPO's guarantee. NORBC
claims only "near-constraint satisfaction" (from the discounted rescale, Eq. 8), and deliberately picks
TRPO over CPO for "stable improvement + feasibility CHECKING" (not enforcement). So (b) is accurate but
it is the method's designed behavior, not a defect.

## The ONLY genuine code-level item: the barrier clamp (min=1e-8), which is NOT in NORBC's equations

`barrier = -torch.log(margin.clamp(min=1e-8)).sum() / barrier_t` (`:464`). NORBC Eq. (9)/(10) have no
clamp. It is a numerical guard so a line-search candidate with ratio!=1 that momentarily pushes
`margin <= 0` does not produce `log(<=0) = NaN`. Side effect (found by the independent critic): the
barrier SATURATES at `-log(1e-8)/barrier_t = 18.42/100 ~ 0.184` per constraint -- it does NOT diverge
to +inf. So the strict interior-point "cannot cross the boundary" property is broken: a step whose
reward-surrogate gain exceeds ~0.184 walks through the boundary. This is CONSISTENT with NORBC's soft
"near-satisfaction" nature (NORBC gives no hard per-step bound anyway) and is self-correcting because
the adaptive threshold re-anchors on raw `mean_cost_returns` every iteration. VERDICT: not a functional
bug, no fix required; at most a one-line code comment documenting intent (clamp caps the barrier, and
that is acceptable given the method is soft-by-design). This CORRECTS an earlier verbal claim in this
campaign that "margin->0 makes the barrier diverge to +inf and auto-rejects the step" -- WRONG, it is capped.

## Corrections logged this session
- "NORBC is an unverifiable / possibly-fabricated citation" -> RETRACTED. It is Kim et al., IROS/arXiv
  2024, named in the file docstring; only web-indexing was poor.
- "IPO barrier diverges to +inf at the boundary in this code" -> WRONG. The `min=1e-8` clamp caps it at ~0.184/constraint.

## Net answer to "did we attach a different theory / is there a bug?"
No. The code implements ONE published, coherent method (NORBC Modified IPO = IPO barrier + TRPO step +
adaptive threshold + multi-head cost value). The name "ConstraintTRPO" abbreviates exactly that. The
theoretical soft-spots are NORBC's design and acknowledged trade-offs; the only code-original element is
the 1e-8 barrier clamp, a numerical guard needing at most a comment. Open research-level question (a
critique of NORBC itself, not this code): whether advantage standardization strictly voids the
near-satisfaction guarantee -- out of scope for a code fix.

