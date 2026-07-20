---
title: "step_interval 250->400 probe: separate DR-WIDTH from OPTIMISATION-STEPS as the cause of extend8k's nominal roll transient regression (pending approval, not launched)"
tags: ["doraemon", "step_interval", "dr-width", "transient-overshoot", "thruster-util", "probe", "teacher_baseline_posttam", "pending-approval", "correction", "result", "h1-refuted"]
created: 2026-07-20T04:17:04.272956
updated: 2026-07-20T17:14:00.313630
sources: ["diagnose-20260720-124259", "next-20260720-131526", "marinelab/marinelab/algorithms/doraemon.py", "diagnose-20260721-020253", "static_260721_014808"]
links: ["extend8k_saturated_the_dr_config_box_at_iter_7000_all_20_params_.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "PENDING HUMAN APPROVAL -- reviewer-approved 2026-07-20; user deferred launching to batch-plan accumulated leads later; nothing else blocks it"
---

# step_interval 250->400 probe: separate DR-WIDTH from OPTIMISATION-STEPS as the cause of extend8k's nominal roll transient regression (pending approval, not launched)

# Context

extend8k (8000 iters) regressed the NOMINAL roll transient while improving roll
steady-state. Two mechanisms are confounded in that run pair, because raising
`max_iterations` raises BOTH: (a) the achieved DR width (DORAEMON's expansion clock is
iterations), and (b) the number of optimisation steps taken against an already-binding
constraint. This page records the designed probe that separates them, so a later planning
pass can pick it up alongside the other open leads.

[FINDING] The two candidate drivers of the extend8k nominal transient regression are
separable by holding the DR width ENDPOINT fixed while leaving the iteration budget
varied. The single-variable change is `envs/main/config.py:544`
`doraemon.step_interval` 250 -> 400 at `max_iterations=8000`: 20 scheduled expansion
attempts, the same SCHEDULED count as the 5000-run's 20, which delivered 18 achieved
expansions and ended at `entropy_before` = -22.702.
[EVIDENCE: proposal next-20260720-131526 (pending approval) in run trpo_biasema_extend8k_260716_162849; report diagnose-20260720-124259]
[CONFIDENCE: HIGH]

[FINDING] Expansion ATTEMPTS are not achieved expansions, measured on both runs: the
5000-run delivered 18 of 20 scheduled (90%), extend8k 26 of 32 (81%). Any future probe
that reasons about DR width from the SCHEDULE alone is unanchored -- width is an achieved
quantity that must be read from `DORAEMON/kl_step` nonzero counts.
[EVIDENCE: direct TB read 2026-07-20 -- DORAEMON/kl_step nonzero 18 (sum 2.160, final entropy_before -22.702) for trpo_biasema_260715_142543; 26 (sum 3.109, final -18.201) for trpo_biasema_extend8k_260716_162849]
[CONFIDENCE: HIGH]

[FINDING] Saturation does NOT block this probe. Reaching the Beta(1,1) config ceiling took
~26 achieved expansions; 20 scheduled (~18 achieved) lands ~4.5 nats short of it. Step SIZE
is capped at `kl_ub` on every update, so a longer `step_interval` cannot make a single
widening step wider -- only rarer. The terminal width therefore separates from extend8k's.
[EVIDENCE: doraemon.py:631, :713 (kl_ub cap in _optimize_entropy); entropy trajectory -22.702 (it5000) -> -18.201 (it7000, pinned); independent proposal-reviewer verification 2026-07-20]
[CONFIDENCE: HIGH]

# Predictions (what the probe would settle)

- H1 (DR width is the driver): roll `os_env_mean` at `none` returns to ~17.0%,
  thruster_util J_C/d_k falls back toward ~0.85, and roll steady-state gives back most of
  its gain.
- H2 (optimisation pressure is the driver): roll `os_env_mean` at `none` still ~25-27%,
  thruster_util still ~0.93.
- Intermediate (~21-23%, ~0.89) = both contribute; partition with a width sweep.

# MANIPULATION CHECK is a precondition, not a formality

Three rows must hold JOINTLY before H1/H2 may be read: final `DORAEMON/entropy_before`
within +/-0.5 of -22.70; the 3 deployment params' terminal Beta b >= ~5; achieved nonzero
`kl_step` count 17-20 of 20 scheduled (>= 24 means it widened like extend8k). FAIL means
the manipulation leaked -- the run does NOT discriminate and must NOT be reported as
evidence for H2. The fallback is to hold the width PATH directly via `--replay_curriculum`
(`doraemon.py:817`, `albc_env.py:491`).

# Known residual

The probe matches the width ENDPOINT, not the width-vs-iteration PATH: at any intermediate
iteration its DR is narrower than the 5000-run's. H1/H2 are read on terminal metrics so the
discrimination holds, but an intermediate-looking outcome could partly reflect the slower
widening schedule. `--replay_curriculum` is the strictly stronger, more expensive control.

# Phase context (do not misread the budget)

The short `max_iterations` across this campaign is a DELIBERATE settings-search choice --
many cheap runs to settle the configuration -- not a defect. The real training run comes
later on an NVIDIA DGX with much larger `max_iterations` AND `num_envs`. So "extending did
not help" is a finding about this plant's response at a fixed config, NOT an argument that
the budget is wrong. What carries to the DGX is the saturation guard recorded in
[[extend8k_saturated_the_dr_config_box_at_iter_7000_all_20_params__]]: bounds first, then
scale.

# Status

Proposal is PENDING HUMAN APPROVAL -- not launched. The user elected (2026-07-20) to defer
launching and to batch-plan the accumulated leads later, so this page exists to make the
probe visible in that planning pass.

---

## Update (2026-07-20T04:19:54.445544)

# CORRECTION + review outcome (2026-07-20, appended after independent re-review)

The proposal `next-20260720-131526` was APPROVED by an independent `proposal-reviewer`
pass, which reproduced every number in it from TB / summary.json / source lines. Four
minor items remain OPEN in the proposal text and are recorded here so the later planning
pass sees them:

[FINDING] CORRECTION to the attrition figure stated above and in the proposal: extend8k's
per-attempt expansion success is NOT 26/32 (81%). Its last nonzero `kl_step` is at iter
6750 and the config box saturated at iter 7000, so the 5 scheduled attempts from 7000
onward could not widen BY CONSTRUCTION (ceiling-forced zeros, not feasibility failures).
True per-attempt success is 26/27 (~96%). The 5000-run's 18/20 (90%) is unaffected -- it
never reached the ceiling. Consequence: real feasibility attrition is much smaller than the
proposal's band rationale assumes, so a step_interval=400 run should be EXPECTED to achieve
close to its full 20 scheduled expansions. The PASS band 17-20 still covers that, and the
+/-0.5 entropy gate (row 1, the primary gate) is unaffected -- but do not cite "19%
attrition" as a fact.
[EVIDENCE: independent proposal-reviewer TB verification 2026-07-20 -- DORAEMON/kl_step last nonzero at iter 6750; saturation at iter 7000 per doraemon_state.pt]
[CONFIDENCE: HIGH]

Remaining minor items in `next-20260720-131526` (none blocks a launch):
- Manipulation-check row 3 FAIL clause ">= 24" is unreachable dead text: the probe
  schedules only 20 attempts, so the achieved count cannot exceed 20. Read the row as
  "PASS 17-20, FAIL materially fewer".
- Lane 1 quotes a cross-run `barrier_penalty` -0.124 -> -0.113 in untagged prose; only the
  8k value (-0.1129) is in the source report. The 5000-run value carries no citation.
- The measured "+8 achieved expansions" supersedes the source report's TL;DR "+12
  curriculum expansions" (which is the SCHEDULED delta, 3000/250). The proposal's number is
  the accurate one; a reader cross-checking the report will hit that conflict.

---

## Update (2026-07-20T08:43:43.909618)

Literature + code check (2026-07-20 pass-2): neither DORAEMON (Tiboni et al., ICLR 2024) nor ADR/AutoDR treats the update interval as an independent tunable -- both GATE distribution updates on measured performance (DORAEMON: train_until_performance_lb; ADR: buffered success threshold). No published ablation varies a fixed clock interval at constant budget, so this probe has no literature precedent to confirm or refute. Code verification: our doraemon.py:416 fires updates on a pure clock (step_count % step_interval); the performance guard lives INSIDE the update as the hard_performance_constraint inversion (mode -2), not as an update gate -- a deliberate approximation of the reference's train-until-converged cadence (comment at doraemon.py:43). FRAMING RULE for the probe write-up: the result characterizes THIS repo's clock-based approximation, not a literature-known sensitivity; do not cite the papers as predicting a direction.

---

## Update (2026-07-20T17:14:00.313630)

# RESULT 2026-07-21 -- probe RAN, H1 REFUTED

Run `trpo_stepint400_260720_180208` (8000 iters, step_interval 400, branch
exp/step-interval-400 @ 81d7c61). Full report: analysis `diagnose-20260721-020253`.

[FINDING] H1 is REFUTED and H2 is not confirmed either -- the run landed OUTSIDE both
pre-registered poles. Holding the achieved DR width at the 5k endpoint while running 8000
iterations gave roll `os_env_mean` 30.5% at `none`, WORSE than extend8k's 27.0%, where H1
predicted a return to ~17.0%. Narrowing the width did not recover the transient; it
degraded it further.
[EVIDENCE: eval/static_260721_014808/summary.json none/roll/os_env_mean = 30.546 vs ref5k static_260716_160156 = 17.022 vs extend8k static_260717_005643 = 26.991]
[CONFIDENCE: HIGH]

[FINDING] Decomposition over the 3 populated cells of the (iterations x width) 2x2 --
the 4th cell (5000 iters x saturated width) was never run: iterations 5k->8k at
held-narrow width costs +13.52 pts of overshoot, while width narrow->saturated at held-8k
BUYS BACK -3.56 pts. The wider DR box is therefore a weak PROTECTIVE factor, the opposite
sign to the hypothesis under test. Both signs are robust; the magnitudes are single-seed
point estimates and the iteration edge carries the residual row-1 leak.
[EVIDENCE: same three summary.json none/roll/os_env_mean values; 17.022 -> 30.546 = +13.524, 30.546 -> 26.991 = -3.555]
[CONFIDENCE: MED]

[FINDING] `step_interval` 400 is NOT adoptable: A1 is worse than extend8k on BOTH axes of
the trade-off extend8k established -- it pays the transient AND gives back the
steady-state gain (roll ss_error 0.261 vs extend8k 0.171, and even worse than ref5k's
0.215).
[EVIDENCE: summary.json none/roll/ss_error -- A1 0.261, ref5k 0.215, extend8k 0.171]
[CONFIDENCE: HIGH]

[FINDING] REUSABLE WARNING -- the two pre-registered readouts DECOUPLED, so
`thruster_util` J_C/d_k must NOT be used as a proxy for transient quality. It tracked the
DR width (A1 0.843 ~ ref5k 0.846, extend8k 0.932) while the roll transient tracked the
iteration budget. Any future probe that pre-registers an actuator-constraint margin and a
transient metric as if they co-move is mis-specified.
[EVIDENCE: engine [TIER 2] Constraints binding row across the three runs -- thruster_util J_C/d_k 0.843 (A1) / 0.846 (ref5k) / 0.932 (extend8k); margin m= 6.28 / 6.14 / 2.74]
[CONFIDENCE: HIGH]

[FINDING] Manipulation-check outcome for the record: 2 of 3 rows passed. Row 2 (Beta b
5.635/5.401/5.502 >= ~5) and row 3 (19 achieved expansions, in 17-20) PASSED; row 1
FAILED marginally -- terminal `entropy_before` -22.043 vs the -22.70 +/- 0.5 band, over by
0.157 nats. The leak is ~15% of the 4.5-nat H1/H2 separation and the outcome landed
outside both poles, so it does not carry the verdict, but any re-use of this run as a
width-held control must carry that caveat.
[EVIDENCE: TB DORAEMON/entropy_before final -22.043 (A1) / -22.702 (ref5k) / -18.201 (extend8k); DORAEMON/kl_step nonzero 19 / 18 / 26]
[CONFIDENCE: HIGH]

[FINDING] Downstream consequence for the curriculum-replay arm: the demotion condition
recorded on the cross-run comparability page ("revisit only if the roll transient peak
becomes binding AND the step_interval probe fails to separate DR-width from
optimisation-steps") is NOT triggered. The probe DID separate them -- it produced a clean
directional answer (iterations dominate, width protects), so `--replay_curriculum` stays
demoted rather than being escalated as the fallback.
[EVIDENCE: this page's decomposition finding; cross_run_dr_comparability page's demotion condition]
[CONFIDENCE: MED]
