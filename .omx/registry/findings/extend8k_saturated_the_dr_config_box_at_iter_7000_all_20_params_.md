---
title: "extend8k SATURATED the DR config box at iter 7000 (all 20 params Beta(1,1) = uniform): performance_lb/kl_ub were never the limit, so its `hard` exam IS absolute -- but the 5000-run's is not"
tags: ["doraemon", "dr-difficulty", "extend8k", "curriculum-saturation", "eval-fairness"]
created: 2026-07-20T03:37:29.562304
updated: 2026-07-20T06:27:47.261385
sources: ["diagnose-20260720-124259"]
links: ["doraemon_is_trust_region_limited_not_feasibility_limited_kl_step.md", "doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step.md", "decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema.md", "step_interval_250_400_probe_separate_dr_width_from_optimisation.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-experiment
---

# extend8k SATURATED the DR config box at iter 7000 (all 20 params Beta(1,1) = uniform): performance_lb/kl_ub were never the limit, so its `hard` exam IS absolute -- but the 5000-run's is not

# Context

User question (2026-07-20) on the extend8k results: "the numbers look good, but is the policy
actually good, or did DORAEMON stay easy because performance_lb / kl_ub are too small?" This page
answers it with the terminal DORAEMON state, and corrects two claims in the extend8k report.

[FINDING] extend8k SATURATED the DR config box. At iter 7000 every one of the 20 DORAEMON
parameters reached Beta(a=1.0, b=1.0) -- exactly uniform over its full configured range -- and the
curriculum then froze for the last 1000 iterations. This is the entropy-max terminal state, not a
stall: DORAEMON is entropy-maximizing, so uniform-over-the-box IS the ceiling.
[EVIDENCE: train/doraemon_state.pt step_count=8000, dist_a==dist_b==1.0000 for all 20 params;
TB DORAEMON/entropy_before -45.881(it0) -> -22.702(it5000) -> -19.527(it6000) -> -18.201(it7000)
-> -18.201(it7999, pinned); DORAEMON/mean|std ocean_current_strength = 0.500 | 0.2887 at it7000,
which is exactly Beta(1,1) mean/std]
[CONFIDENCE: HIGH]

[FINDING] Therefore performance_lb=250 and kl_ub=0.12 did NOT hold the curriculum back on this
config. The run was time-limited only up to iter 7000 and ceiling-limited after; success_rate ended
0.789, far above alpha=0.5, so the feasibility gate was never the binding constraint either.
Raising kl_ub or lowering performance_lb cannot make this configuration harder -- the box is
exhausted.
[EVIDENCE: train/params/env.yaml performance_lb 250.0, alpha 0.5, kl_ub 0.12, step_interval 250;
TB DORAEMON/success_rate 0.915(it2000) -> 0.848(it6000) -> 0.789(it7999), never below alpha]
[CONFIDENCE: HIGH]

[FINDING] Consequence for reading the eval: the extend8k `hard` level is the FULL configured DR box
(ocean_current xi uniform over its whole range, obs_noise full span, payload CoG full disk, every
hydro/mass param full span). So the good `hard` numbers are NOT an easy-exam artifact -- they are
the hardest exam this config can produce. The exam is still run-relative (`eval.py static` defaults
`--doraemon-dr` True, so soft/medium/hard = the run's own learned DR scaled 0.3/0.6/1.0), but for
extend8k specifically "its own learned DR" happens to equal the config ceiling, so hard is absolute
here. This is NOT true of the 5000-run, whose 3 deployment params ended at Beta(1, ~6.2-6.6)
(mean ~0.135, i.e. ~14% of range) -- its `hard` is much softer, so the cross-run soft/medium/hard
rows remain non-comparable.
[EVIDENCE: eval.py:235 `--doraemon-dr` BooleanOptionalAction default=True; eval.py:1110 "use it as
the hard-DR anchor"; analysis/common.py:36 DR_SCALE none 0.0 / soft 0.3 / medium 0.6 / hard 1.0;
5000-run doraemon_state.pt payload_cog_offset_xy_u Beta(1.000,6.400), ocean_current_strength
Beta(1.000,6.177), obs_noise_scale Beta(1.000,6.585); its other 17 params Beta(~1.7,~1.7)]
[CONFIDENCE: HIGH]

[FINDING] CORRECTION to the extend8k report: the [CONFIDENCE: MED] finding "the DR expansion
continues to the very end of training (iter 8000) -- every DR param's +-1 sigma band still widening
at 8000" is REFUTED. Expansion stopped at iter 7000. The plot-based read mistook an asymptote for
continued growth; the terminal-state file settles it.
[EVIDENCE: report.md (diagnose-20260720-123142) doraemon section vs doraemon_state.pt +
TB entropy_before flat -18.201 from it7000]
[CONFIDENCE: HIGH]

[FINDING] The heavy tail at `hard` is real and is NOT a small-scale ratio artifact. Roll ss_error
CV rises 25.3% (none) -> 246.2% (hard), and at hard the absolute numbers are large too: overshoot
median 18.4% vs q90 33.0%, 4 envs above 40% overshoot, ss_error_std 2.04 on a mean of 0.83. At
`none` the "small scale inflates the ratio" reading IS correct (ss_error 0.171, CV only 25%) -- but
that reading cannot be carried to hard, where the scale is not small.
[EVIDENCE: eval/static_260717_005643/summary.json roll: none ss_error 0.1706 std 0.0432; hard
ss_error 0.8282 std 2.0393, os_env_median 18.398, os_env_q90 33.028, n_gt40 4.0]
[CONFIDENCE: HIGH]

# Decision / next experiment (lead)

The lever for more robustness on this plant is NOT iters, NOT kl_ub, and NOT performance_lb -- all
three are exhausted or non-binding at the box ceiling. It is (a) widening the config DR bounds
themselves (the P-A6 physical-span review: only justified where MEASURED hardware variation exceeds
the current bounds), or (b) plant fidelity. This also sharpens the e3 verdict: the last 1000 of the
8000 iterations trained on a frozen distribution, so "extend past 5000" was partly "train longer on
a fixed max-width DR" -- and it still did not raise reward (-2.6%).

Open guard for any DGX scale-up: with the box already saturated at 7000 iters on 4096 envs, a
larger iteration budget alone will add only frozen-DR iterations unless the config bounds are
widened first.

---

## Update (2026-07-20T04:00:52.022048)

# UPDATE 2026-07-20: the report itself has been corrected

The refuted "DR expansion continues to iter 8000" finding is no longer only flagged here -- the
experiments-tree report (the results SSOT) has been corrected through the exp-analyze RE-analysis
path. Current analysis: `diagnose-20260720-124259` (supersedes 123142 / 122425 / 115818).

[FINDING] The correction is landed and gated, not just recorded in the wiki. The new report replaces
the single MED-confidence plot-based finding with three HIGH-confidence code-verified ones
(saturation at iter 7000; performance_lb/kl_ub non-binding; exam absolute-for-extend8k vs
relative-for-the-5000-run), plus a tracking-section finding that the hard-level heavy tail is not a
small-scale ratio artifact.
[EVIDENCE: analysis/diagnose-20260720-124259 -- `omx report-coverage --min-coverage 0.5 --baseline
auto --cross-run-refs` returned ok:true with no depth regression (words 2526 -> 3302, findings
17 -> 20, tables 70 -> 87) and cross_run_refs ok (20 cells re-verified against the 5000-run's
summary.json); `omx report-review` approve; independent report-reviewer agent approve after one
revise cycle]
[CONFIDENCE: HIGH]

[FINDING] Two review-driven corrections worth carrying forward as habits. First, the heavy-tail
claim originally cited transient-overshoot columns (os_env_median / os_env_q90 / n_gt40) as support
for a STEADY-STATE ss_error tail -- exactly the conflation rule 03 forbids; the table now carries
ss_error / ss_error_std / CV only. Second, "DR ocean_current (end) = 0.22" and "ocean_current mean =
0.500" are NOT contradictory: the first is the physical magnitude (`DR/ocean_current_mag_mean`), the
second the normalized Beta-xi mean (`DORAEMON/mean/ocean_current_strength`). The report now carries
a unit note saying so.
[EVIDENCE: report-reviewer verdict on diagnose-20260720-124259 (revise -> both applied -> approve);
manifest.json `corrections` list]
[CONFIDENCE: HIGH]

[FINDING] Saturation timing must NOT be attributed to `num_envs`. The verdict originally said "at
4096 envs the box saturates by iter 7000"; the expansion clock is `step_interval`, measured in
iterations, and no evidence in this campaign ties saturation timing to env count. The DGX scale-up
guard is therefore "widen the config bounds first", stated without an env-count claim.
[EVIDENCE: train/params/env.yaml step_interval=250 (iterations); reviewer finding 4 on
diagnose-20260720-124259]
[CONFIDENCE: HIGH]

---

## Update (2026-07-20T06:27:47.261385)

## SCOPE QUALIFIER (2026-07-20): "performance_lb/kl_ub were never the limit" holds ONLY while the box is the ceiling

This page is routinely read as "the config box is the only remaining lever" (the
`teacher_baseline_posttam` README states exactly that: "the only road to a harder exam is widening
the DR bounds themselves"). That is true of the SATURATED state and false of the state immediately
after you widen the box. The moment the bounds move, all three knobs become live again:

1. **kl_ub x n_updates is the reachable distance, and it is the ACTIVE binding constraint.**
   `DORAEMON/kl_step` sits exactly at `kl_ub` on essentially every update (17/17, 18/18, 19/19,
   25/26 across the four posttam runs) -- DORAEMON always takes the largest move permitted, so the
   trust region, not feasibility, paces expansion
   ([[doraemon_is_trust_region_limited_not_feasibility_limited_kl_step]]). Expansion budget ~=
   `(max_iterations / step_interval) x kl_ub`. Measured: P-B1 = 18 x 0.12 = 2.16 did NOT saturate;
   extend8k = 26 x 0.12 = 3.12 DID. A wider box raises the entropy ceiling but does not buy any
   extra distance -- widen the box at a fixed budget and the run simply stops short of the new
   bound, i.e. you get the same exam you already had, later.
2. **performance_lb must be re-checked, not left alone.** It is an ABSOLUTE return threshold
   (doraemon.py:39), so a wider box lowers achievable return at fixed lb, pushing success down
   toward alpha and handing the binding role BACK to the feasibility gate. The tuning criterion is
   not the absolute value but "does `success_rate` settle at `alpha`=0.5 at convergence"
   ([[doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step_]]). Both failure directions
   are already on record here: too low -> success ~0.99, feasibility inert, self-pacing gone (the
   lb=200 + bias_ema case, [[decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema]]);
   too high -> early stall at mode -2 (the posttam baseline).
3. **step_interval trades reach for thoroughness at fixed budget.** Raising it lowers n_updates and
   therefore LOWERS final difficulty. The approved-but-unlaunched 250->400 probe is precisely the
   instrument for separating DR-width from optimisation-steps
   ([[step_interval_250_400_probe_separate_dr_width_from_optimisation_]]).

DESIGN TENSION to carry into the batch pass (this is the hard part, not a footnote): widening the
box while holding the budget under-uses the new box; widening the box AND the budget re-runs the
axis extend8k already measured, whose verdict was an axis TRADE, not a win (fair-none roll ss -21%
but pitch +52%, roll overshoot +59%). So "widen the DR bounds" is a NECESSARY, not sufficient,
condition, and it cannot be executed as a clean single-variable probe without deciding in advance
which of the three knobs is held fixed and why. State that choice in the DESIGN.md before launch.

