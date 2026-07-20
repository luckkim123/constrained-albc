---
title: "Curriculum recalibration protocol: widening the DR box requires re-tuning budget (kl_ub x n_updates) AND performance_lb together -- not a single-variable probe"
tags: ["doraemon", "curriculum", "kl_ub", "performance_lb", "step_interval", "max_iterations", "dr-box", "protocol", "experiment-design", "batch-planning"]
created: 2026-07-20T06:29:51.844146
updated: 2026-07-20T06:29:51.844146
sources: ["doraemon.py:38-49", "doraemon.py:416", "trpo_biasema_extend8k_260716_162849", "diagnose-20260716-035505"]
links: ["doraemon_is_trust_region_limited_not_feasibility_limited_kl_step.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "kl_ub_up_and_per_difficulty_learning_are_antagonistic_the_dr_har.md", "decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema.md", "cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov.md", "eval_command_box_was_half_the_trained_envelope_from_2026_04_06_t.md", "step_interval_250_400_probe_separate_dr_width_from_optimisation.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "Step 1 (new bounds must come from a MEASURED physical span review) is blocked on hydro/TAM measurement -- no load cell. Step 0 (state check on existing TB) is zero-GPU and unblocked. Whole lead parked under the 2026-07-20 batch-pass decision."
---

# Curriculum recalibration protocol: widening the DR box requires re-tuning budget (kl_ub x n_updates) AND performance_lb together -- not a single-variable probe

Widening the DR bounds is a NECESSARY but NOT SUFFICIENT condition for a harder exam, and it cannot
be run as an ordinary single-variable probe. This page is the protocol for doing it correctly, and
it is registered as an open lead so the batch pass plans it rather than improvising it.

## Why the normal single-variable rule breaks here

The three curriculum knobs are separable as KNOBS but multiply into ONE quantity at the endpoint:

    expansion budget ~= n_updates x kl_ub = (max_iterations / step_interval) x kl_ub

and `DORAEMON/kl_step` is pinned AT `kl_ub` on essentially every update (17/17, 18/18, 19/19, 25/26
across the four posttam runs) -- the trust region, not feasibility, is the active pacing constraint
([[doraemon_is_trust_region_limited_not_feasibility_limited_kl_step]]). Measured: 18 x 0.12 = 2.16
did not saturate the box; 26 x 0.12 = 3.12 did (extend8k, at iter 7000).

Consequence: widening the box raises the entropy CEILING but buys no extra DISTANCE. Widen the box
at a fixed budget and the run stops short of the new bound -- the same exam as before, arrived at
later. So the variable that must be declared and controlled is the BUDGET, not each knob separately.

## Protocol

**Step 0 -- state check (zero GPU, on the current reference run).** Confirm the three preconditions
before changing anything, from TB scalars of the run you are branching from:
- `DORAEMON/kl_step` at the `kl_ub` cap on ~all updates -> trust-region-limited (expected).
- `DORAEMON/success_rate` vs `alpha` (0.5). If success >> alpha the feasibility gate is INERT and
  `performance_lb` is already mis-set -- fix that first, it is a confound, not a co-variable.
- iteration at which `doraemon_state.pt` reaches Beta(1,1) on all params. If the box never saturated,
  the box is NOT yet the ceiling and widening it is premature.

**Step 1 -- source the new bounds, do not invent them.** New DR ranges must come from measured
hardware variation, not from a round-number multiplier. This is currently BLOCKED: the hydro nominal
is analytical rather than measured and there is no load cell for a TAM moment-arm / max_thrust band
([[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]]). Widening bounds without a
physical span review produces a harder exam that means nothing physically.

**Step 2 -- buy the distance with `max_iterations`, hold `kl_ub` fixed.** Of the two ways to raise
the budget, only one is side-effect free:
- `max_iterations` UP -> more expansions, no curriculum side-effect, wall-clock cost only.
- `kl_ub` UP -> a bigger distribution jump inside an UNCHANGED dwell window, so each difficulty is
  under-trained relative to the jump; E1 measured this as attitude collapse
  ([[kl_ub_up_and_per_difficulty_learning_are_antagonistic_the_dr_har]]).
Therefore the default is: keep `kl_ub` at its current value, raise `max_iterations` until
`n_updates x kl_ub` covers the KL distance to the NEW bound. A `kl_ub` sweep at fixed budget is NOT
an independent axis -- it re-explores the axis `max_iterations` already moved, and extend8k vs the
5000-run are already two measured points on it.

**Step 3 -- recalibrate `performance_lb` against the NEW return ceiling.** `performance_lb` is an
ABSOLUTE return threshold (doraemon.py:39), so a wider box lowers achievable return and hands the
binding role back to the feasibility gate. Tune by the criterion, never by the absolute number:
**does `success_rate` settle at `alpha` = 0.5 at convergence?** Both failure directions are on
record -- too low gives success ~0.99 and self-pacing disappears (lb=200 + bias_ema,
[[decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema]]); too high stalls early at
`mode` = -2 (the posttam baseline). This step needs a short pilot to learn the new return ceiling
before the full run; do not guess lb from the old ceiling.

**Step 4 -- manipulation checks (state them in DESIGN.md BEFORE launch).** The run is only
interpretable if these hold:
- `kl_step` still at cap (confirms the budget calculation applies),
- `mode` >= 0 (curriculum not stalled),
- `success_rate` -> alpha (lb correctly re-set),
- box saturation iteration < `max_iterations` (budget actually sufficed),
- `entropy_after` rising across updates (the distribution really is widening).
If saturation is NOT reached, the run answers nothing about the new box -- it only re-measures the
budget axis.

**Step 5 -- fair evaluation.** Grade with a shared anchor, not each run's own learned DR:
`eval.py static --doraemon-dr-from <reference run>`, plus the `none` level, at the FULL +-30 command
box. Never read cross-run soft/medium/hard from a run-relative DORAEMON eval
([[cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov]]), and never compare against a
pre-2026-07-15 number without noting it was measured on the half command box
([[eval_command_box_was_half_the_trained_envelope_from_2026_04_06_t]]).

## The design tension to resolve explicitly, in writing

Widening the box at a fixed budget under-uses the new box. Widening the box AND the budget re-runs
the axis extend8k already measured, whose verdict was an axis TRADE and not a win (fair-none roll ss
-21% but pitch +52%, roll overshoot +59%). There is no configuration of this experiment that avoids
both. The DESIGN.md must therefore state which quantity is being held fixed and why, and what result
would count as distinguishing "the wider box helped" from "the larger budget traded axes again" --
otherwise the run reproduces a known trade under a new name.

`step_interval` is the third knob and moves in the opposite direction: raising it at fixed
`max_iterations` LOWERS final difficulty (fewer expansions) in exchange for more training per
difficulty. The approved-but-unlaunched 250->400 probe is the instrument for separating DR-width from
optimisation-steps and should be read before this campaign is designed
([[step_interval_250_400_probe_separate_dr_width_from_optimisation_]]).

## Status

Open lead. Blocked on the Step-1 physical span review (measured hardware variation for the new
bounds), and parked under the 2026-07-20 batch-pass decision like every other lead. Step 0 is
zero-GPU and can be executed at any time on existing TB data.

