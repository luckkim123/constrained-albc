---
title: "Constraint/margin is in per-constraint discounted-budget units (d_k = D_k/(1-gamma)) -- rank by J_C/d_k, never by raw margin; the baseline report's 'binding trio' is exactly inverted"
tags: ["constraint", "margin", "ipo", "normalization", "budget", "report-error", "metric-reading", "envs-main"]
created: 2026-07-20T03:27:11.701599
updated: 2026-07-20T03:27:11.701599
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Constraint/margin is in per-constraint discounted-budget units (d_k = D_k/(1-gamma)) -- rank by J_C/d_k, never by raw margin; the baseline report's 'binding trio' is exactly inverted

`Constraint/margin/*` is NOT normalized and NOT comparable across constraints. Reading the raw margins
side by side inverts the ranking, and the baseline report did exactly that.

## What margin actually is (code-verified, constraint_trpo.py)

- `:148` budgets are discounted: `d_k = D_k / (1 - cost_gamma)`, and `cost_gamma = 0.99`, so `d_k = D_k * 100`.
- `:322` adaptive threshold `d_k^adaptive = max(d_k, J_C + alpha * d_k)`, `barrier_alpha = 0.05`.
- `:463` `Constraint/margin/k = d_k^adaptive - J_C`; `:461` `Constraint/viol/k = J_C - d_k`, so `J_C = viol + d_k`.

So each constraint's margin is expressed in ITS OWN budget scale. `attitude` has D_k=0.01 -> d_k=1.0,
`thruster_util` has D_k=0.40 -> d_k=40.0. Their margins differ by 40x before any policy behaviour enters.

**Use the normalized utilization `J_C/d_k = 1 - margin/d_k`.** Binding threshold: utilization > 1-alpha =
95%, the point where the adaptive threshold re-anchors and the margin pins at `alpha*d_k`.

## The correction (baseline trpo_baseline_260713_031325, final-200)

| constraint | D_k | d_k | margin | J_C | J_C/d_k |
|---|---|---|---|---|---|
| thruster_util | 0.40 | 40.0 | 7.79 | 32.21 | **80.5%** |
| rp_vel_settling | 0.20 | 20.0 | 9.64 | 10.36 | **51.8%** |
| rp_rate | 0.10 | 10.0 | 6.29 | 3.71 | **37.1%** |
| arm_torque | 0.08 | 8.0 | 7.29 | 0.71 | 8.9% |
| manipulability | 0.05 | 5.0 | 4.64 | 0.36 | 7.2% |
| yaw_rate | 0.10 | 10.0 | 9.44 | 0.56 | 5.6% |
| arm_joint_vel | 0.02 | 2.0 | 1.98 | 0.02 | 1.0% |
| attitude | 0.01 | 1.0 | 0.994 | 0.006 | **0.6%** |
| joint1_pos | 0.01 | 1.0 | 0.997 | 0.003 | **0.3%** |
| cumul_yaw | 0.01 | 1.0 | 1.000 | 0.000 | **0.0%** |

## REPORT ERROR being corrected

`trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md` section 6 states: "all 10
constraints satisfied (all NORMALIZED margins > 0); attitude / joint1_pos / cumul_yaw are the binding
trio (margin ~1.0), the rest have large slack." BOTH halves are wrong. The margins are not normalized,
and those three are the LEAST binding of the ten (0.0-0.6% utilization) -- their margin sits near 1.0
only because their d_k IS 1.0 and their cost is ~zero. The actual near-binding constraint is
thruster_util, which the report filed under "large slack". Any downstream reasoning of the form
"the attitude constraint is squeezing the policy" traces to this misreading and needs re-checking.

## The gradient-weight nuance (does not rescue the wrong reading)

The barrier is `-sum log(margin_k) / barrier_t` (`:484`, `barrier_t=100`), so the gradient coefficient on
constraint k's cost surrogate is `1/(margin_k * barrier_t)` -- and cost advantages ARE standardized
per-constraint (`:451-453`), so those coefficients are comparable. That makes attitude/joint1_pos/cumul_yaw
the HIGHEST-weighted constraints per unit of cost change (0.0101 vs thruster_util's 0.00128, ~8x). But
they are binary-indicator constraints whose cost-advantage std is near zero, and `ca_std.clamp(min=1.0)`
(`:451`) deliberately blocks the amplification -- so there is no signal for the large coefficient to
multiply. High sensitivity, no excitation. This is a second reason the raw-margin reading misleads.

GENERAL RULE: when a logged "margin"/"slack" is a difference against a per-item budget, never rank items
by the raw difference. Divide by the budget first, and state the threshold at which the metric changes
regime.

