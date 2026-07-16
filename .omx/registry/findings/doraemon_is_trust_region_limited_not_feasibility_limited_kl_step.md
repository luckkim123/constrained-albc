---
title: "DORAEMON is trust-region-limited not feasibility-limited: kl_step is pinned AT kl_ub every update, so kl_ub x n_updates is one expansion budget"
tags: ["doraemon", "kl_ub", "curriculum", "expansion-budget", "p-a9", "dgx"]
created: 2026-07-16T05:49:54.801488
updated: 2026-07-16T05:49:54.801488
sources: []
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# DORAEMON is trust-region-limited not feasibility-limited: kl_step is pinned AT kl_ub every update, so kl_ub x n_updates is one expansion budget

# DORAEMON is trust-region-limited, not feasibility-limited: kl_step is pinned AT kl_ub on every update

[FINDING] `DORAEMON/kl_step` sits at exactly the configured `kl_ub` (0.12) on essentially every
optimization step of all four posttam runs: reference 17/17 updates at the cap (mean 0.1200), P-B1
18/18 (0.1200), perflb200 19/19 (0.1200), P-A8 25/26 (mean 0.1183, 96.2% at cap). The KL trust
region is therefore the ACTIVE binding constraint on DR expansion rate -- DORAEMON takes the largest
move it is permitted, every single time. It is not being held back by the feasibility gate.
[EVIDENCE: TB scalar DORAEMON/kl_step, 4 posttam runs, filtered to update steps (kl_step>0 -- it is 0 on non-update iterations by construction, doraemon.py:418), 2026-07-16]
[CONFIDENCE: HIGH]

[FINDING] Updates are RARE: `step_interval=250` (config.py:544) gives only ~20 optimization steps per
5000 iterations (measured 17-19; P-A8's 8000 iters gave 26). Combined with the pinning above, the DR
expansion reached by run-end scales with `n_updates x kl_ub` = `(max_iterations / step_interval) x
kl_ub`. Approximate -- KL is not additive along a path -- but every step is at the cap, so the
ordering is exact. Measured expansion budgets: P-B1 = 18 x 0.12 = 2.16; P-A8 = 26 x 0.12 = 3.12, and
P-A8 is the run that reached the FULL config ceiling Beta(1.00,1.00) on all 20 params.
[EVIDENCE: same TB read; config.py:544; report diagnose-20260716-035505 doraemon_state.pt all 20 dims]
[CONFIDENCE: HIGH]

# Consequence: kl_ub and max_iterations are separable as KNOBS but not as EFFECTS

The wiki records them as 3 separable levers (`doraemon_difficulty_has_3_separable_levers...`:
kl_ub = step size, step_interval = dwell, max_iterations = #expansions). That is true of the knobs,
but on the ENDPOINT they multiply into one quantity: total expansion budget. Two consequences:

1. A "kl_ub sweep at a fixed budget" is NOT an independent axis -- it re-explores the same axis
   `max_iterations` already moved. P-A8 (3.12) vs P-B1 (2.16) is already a point on it, and it
   already measured that axis's trade-off (fair-none roll +31% / pitch +61%, n_gt20 -56%).
2. It also explains the recorded "kl_ub optimum is BUDGET-conditional"
   (`kl_ub_up_and_per_difficulty_learning_are_antagonistic...`) mechanically rather than empirically:
   the optimum is conditional because the two knobs are two ways of buying the same thing.

# Why P-B1's DR was "narrow" -- it was not lb

P-B1 ended at success 0.8825, far ABOVE the alpha=0.5 feasibility floor. It did not stop expanding
because performance_lb constrained it; it stopped because it ran out of expansion steps (18 x 0.12).
The feasibility endpoint has never been observed for the bias_ema-ON config. At a large budget (the
planned NVIDIA DGX run, much larger max_iterations AND num_envs) the DR necessarily runs to its
endpoint -- min(config ceiling, success->alpha) -- and which of the two binds decides the next lever:
widening the HardDR config bounds (P-A6) vs tuning lb.

Usable corollary: because expansion scales with n_updates x kl_ub, raising kl_ub at a fixed iteration
count is a CHEAP PROXY for a much larger budget (20 x 0.24 = 4.8 exceeds the 3.12 that saturated the
bias_ema-OFF config), so the endpoint question can be answered in one 5000-iter run before spending
DGX time. Proposed as next-20260716-144338 (pending approval).

