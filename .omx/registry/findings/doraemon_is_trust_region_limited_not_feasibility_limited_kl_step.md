---
title: "DORAEMON is trust-region-limited not feasibility-limited: kl_step is pinned AT kl_ub every update, so kl_ub x n_updates is one expansion budget"
tags: ["doraemon", "kl_ub", "curriculum", "expansion-budget", "p-a9", "dgx", "correction", "dwell-time", "step_interval"]
created: 2026-07-16T05:49:54.801488
updated: 2026-07-16T05:57:44.772031
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

---

## Update (2026-07-16T05:57:44.772031)

# CORRECTION 2026-07-16 (same day): "separable knobs, one effect" is WRONG — kl_ub and max_iterations are NOT interchangeable

The section above concluded that because expansion scales with `n_updates x kl_ub`, the two knobs
"multiply into one quantity" and therefore a kl_ub sweep at fixed budget "re-explores the axis P-A8
already moved with the other knob". **That inference is refuted by evidence already in this wiki**,
which the session that wrote it failed to consult. Correcting rather than deleting, per append-merge.

[FINDING] The product model correctly describes WHERE the distribution goes, but NOT whether the
policy keeps up — and the policy is what the metrics measure. The dr_harder orthogonal factorial:
E1 (kl_ub 0.06->0.12) and E2 (ocean nominal 0.0->0.3) reached the SAME final ocean coverage (0.421
vs 0.409) but OPPOSITE attitude outcomes — E1 roll/pitch hard +34%/+69% WORSE, E2 +8%/-17%
(attitude kept). A deterministic E4 control made this causal, not seed. So the same reached
difficulty, bought two different ways, gives opposite results: expansion bought with SPEED (kl_ub)
is not the same good as expansion bought with TIME (max_iterations).
[EVIDENCE: wiki kl_ub_up_and_per_difficulty_learning_are_antagonistic_the_dr_har.md (decision, high) + dr_harder_campaign_synthesis_speed_kills_attitude_center_shift_o.md]
[CONFIDENCE: HIGH]

[FINDING] The mechanism is the missing third term the product model drops: `step_interval` owns
dwell-time INDEPENDENTLY of kl_ub. Raising kl_ub makes each expansion a bigger jump within the SAME
unchanged dwell window, so the policy is under-trained relative to the harder distribution. The
invariant that matters is therefore expansion PER DWELL, not total expansion. Corollary with teeth:
there is NO cheap way to buy more expansion inside a fixed iteration budget — raising kl_ub or
shrinking step_interval both cut dwell per unit of difficulty. A large expansion budget genuinely
requires a large iteration budget.
[EVIDENCE: doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step_.md (code-verified 3-lever breakdown); config.py:544 step_interval=250]
[CONFIDENCE: HIGH]

[FINDING] Second-order consequence for any endpoint measurement: `current_success_rate` (Ghat) is
estimated from real rollout returns (doraemon.py:427) and compared to alpha (doraemon.py:430). An
under-trained policy therefore reports DEPRESSED success — so a kl_ub-up probe would bias itself
toward a false "the feasibility floor binds" reading. kl_ub-up does not just cost attitude; it
corrupts the instrument that would measure the cost.
[EVIDENCE: doraemon.py:427/430; E1 under-training mechanism above]
[CONFIDENCE: MED]

# What survives, and what the archive says to do instead

SURVIVES (unchanged, directly measured): kl_step IS pinned at kl_ub on every update of all 4 runs;
updates ARE rare (~18 per 5000 iters at step_interval=250); P-B1 DID stop at success 0.8825 far above
the alpha=0.5 floor, so it ran out of expansion steps rather than hitting the gate — lb never bound.
Measured expansion budgets, corrected to MEASURED update counts (the original section used nominal
max_iterations/step_interval, which overstates): P-B1 = 18 x 0.12 = 2.16; P-A8 = 25 x 0.12 + 1 x
0.0766 = 3.08 (not 3.12/3.84).

RETRACTED: "a kl_ub sweep is not novel because P-A8 already moved that axis". The wiki treats the two
levers as non-interchangeable, so they are different axes. The kl_ub lead is closed for a STRONGER
reason instead: raising kl_ub at a fixed budget is known-bad (E1), not redundant.

THE NAMED UNTESTED CELL (quoting kl_ub_up_and_per_difficulty_learning_are_antagonistic...): "raise the
difficulty target (performance_lb, or DORAEMON variance from nominal=0) and/or extend max_iter, while
keeping kl_ub LOW so per-difficulty dwell-time stays high. That combination was never run." That is
also the direction the user committed to on 2026-07-16 (larger max_iterations + num_envs on an NVIDIA
DGX). Proposed as next-20260716-145510 (pending approval), which supersedes the refuted
next-20260716-144338.

# Process lesson

The refuted design queried the wiki by SYMPTOM (hard-level confound, DR width) and never by LEVER
NAME (kl_ub). The contradicting page was category `decision`, confidence `high`, and titled with the
lever — one `omx wiki query "kl_ub"` would have surfaced it before a GPU proposal was written. Query
the wiki for the KNOB you intend to turn, not only for the symptom you intend to fix.

