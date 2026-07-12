---
title: "Next from-scratch retrain manifest: what rides on the post-TAM baseline retrain (sim fixes + learning-dynamics experiments)"
tags: ["albc", "envs-main", "retrain-campaign", "sim-to-real-audit", "baseline-retrain", "manifest", "index", "experiment-roster", "from-scratch", "constraint-trpo", "velocity-limit", "reward-weight-tuning", "two-phase"]
created: 2026-07-05T08:06:16.009224
updated: 2026-07-12T13:45:17.487104
sources: []
links: ["experiment_result_recording_location_experiments_tree_is_ssot_no.md", "tam_columns_must_match_robot_firmware_esc_channel_order_reorder_.md", "encoder_priv_obs_normalization_bounds_must_be_dr_derived_not_har.md", "thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban.md", "leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r.md", "encoder_latent_z_dim_ablation_coupling_points_constraints_for_a_.md", "action_bounding_is_justified_raw_gaussian_external_clamp_tanh_ru.md", "arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt.md", "real_robot_deployment_vibration_differential_diagnosis_by_sim_to.md", "next_experiment_workflow_pick_a_baseline_train_once_then_re_tune.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Next from-scratch retrain manifest: what rides on the post-TAM baseline retrain (sim fixes + learning-dynamics experiments)

# Next from-scratch retrain manifest

**Purpose**: single index of everything that must ride on the NEXT baseline retrain, so the roster is not scattered
across many `docs/plans/` files. This card is the roster; each item links to its own detail doc/card. When the retrain
group directory is created (`train.py --run_group <campaign>`), migrate this roster into that group's `DESIGN.md`
(experiments-tree is the SSOT for a launched campaign; this card is the pre-group holding place -- see
[[experiment_result_recording_location_experiments_tree_is_ssot_no]]).

**Why one retrain, not piecemeal**: all fixes below change env physics or learning dynamics and invalidate old
checkpoints. Holding them together avoids confounded baselines but means several variables change at once -- so each
item records *why* it is a fix and *what code proves it*, for post-hoc debugging if the retrained baseline looks wrong.
Umbrella plan: `docs/plans/2026-06-29-sim-to-real-audit-before-baseline-retrain.md`.

**HARD invalidation gate**: every pre-TAM-reorder checkpoint is physically invalid on current code -- TAM column
reorder (`238932c`) changed the action->thruster mapping. Confirmed 2026-07-05 when an Arm B checkpoint eval'd at
survival 14% (vs 100% at train time) purely from this. See [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]].
So the retrain is FROM SCRATCH; no resume from any existing model.

2026-07-05 B1 실측으로 TAM은 열 순열뿐 아니라 **행(Fz/My/Mz) 재작성**도 필요 판명 -- 순열 전제(238932c)만으론 불충분.

## Roster (status as of 2026-07-05)

### Group A/B/C/D -- sim-to-real audit fixes (apply together, then retrain)
Detail: `docs/plans/2026-06-29-sim-to-real-audit-before-baseline-retrain.md`.

| Item | Status | Detail |
|:---|:---|:---|
| A -- control-timing dt alignment (arm 50->10 Hz, IMU hold) | code-verified; A2 non-integer-phase choice OPEN | audit doc Group A |
| B1 -- encoder priv-obs norm bounds: hardcoded -> DR-derived | IMPLEMENTED (`exp/dr-derived-norm-bounds 87b80b0`, UNPUSHED; 34 tests pass) | `docs/plans/2026-06-30-dr-derived-priv-obs-normalization-bounds.md`; [[encoder_priv_obs_normalization_bounds_must_be_dr_derived_not_har]] |
| TAM column reorder -> firmware ESC order | IMPLEMENTED + PUSHED (`238932c`) | [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]] |
| TAM 수평 3행+순열 재작성 (회전실측 기하 완결) | 수평 확정(m4 유추), 수직행·m4실측 대기 | [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]] |
| Thruster nonlinear curve (deadband + signed-square) | IMPLEMENTED off-by-default (marinelab `exp/thruster-curve d34debc`, UNPUSHED) | [[thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban]] |
| TAM moment-arm + max_thrust DR bands (currently NONE) | audit candidate (Group D verdict) | audit doc Group D |
| C -- constraint over-spec sweep (joint1_pos 720-slack) | TBD, not yet audited | audit doc Group C |

### Learning-dynamics experiments (ride ON the retrained baseline, toggle A/B)
These are NOT sim fixes -- they change learning/obs dynamics, so each needs its own A/B on the retrained baseline
(toggle off = the audit baseline itself; toggle on = the probe). Do not fold into the sim-fix batch (would confound).

| Experiment | Status | Detail |
|:---|:---|:---|
| carry-off: reset `_error_integral`/`_bias_ema` at resample | DESIGN ONLY (this session) | `docs/plans/2026-07-05-carry-over-reset-ab-experiment-design.md`; [[leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r]] |
| encoder latent z_dim ablation (9D vs sweep) | DESIGN ONLY | [[encoder_latent_z_dim_ablation_coupling_points_constraints_for_a_]] |
| entropy-collapse <-> IPO-barrier causal isolation | DEFERRED (hypothesis only, no code) | `docs/plans/2026-06-30-entropy-collapse-ipo-barrier-experiment.md` |
| joint1 graduated-rotation constraint (arm B) | design under discussion (not exp-design'd) | `docs/plans/2026-06-29-joint1-graduated-rotation-constraint-design.md` |
| action clip_fraction logging (highest-priority, no gate) | lead recorded, not implemented | [[action_bounding_is_justified_raw_gaussian_external_clamp_tanh_ru]] |

## Coverage-gap follow-up (eval tooling, checkpoint-independent)
Separate from the retrain: `eval.py static` probes only the inner half of the train command box
(`trajectory.py:14` ATT_AMP_DEG=15 vs `config.py:410` +-30). Fix = raise the amplitude constants to the config
boundary or make them CLI/env-var configurable, so eval covers the full train box. Independent of any checkpoint or
retrain. Detail: `docs/plans/2026-07-05-command-sampling-resampling-review.md` section 4-1.

## Migration note
When the retrain group is created, this roster's content -> `experiments/rsl_rl/<exp>/<group>/DESIGN.md`; this card
then becomes a pointer to that DESIGN.md. Until then this card is the roster SSOT and the `docs/plans/` files are the
per-item details.

---

## Update (2026-07-06T07:33:45.325955)

## Roster addition 2026-07-06 -- arm velocity_limit_sim (Group A/B sim-to-real fix)

Add to the "sim-to-real audit fixes" roster (motivated by onboard 2026-07-06 measurement, user agrees in principle, applied at retrain not now):

| Item | Status | Detail |
|:---|:---|:---|
| arm velocity_limit_sim 6.28 -> ~3.1 rad/s (measured plateau) + soft velocity_limit_cost 4.189 -> inside 3.1 (MUST, else dead constraint) | measured + ripple-analyzed, NOT applied (rides retrain) | [[arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt]] |

Why it is a PAIR not one line: lowering only velocity_limit_sim inverts 4.189 (soft) vs 3.1 (hard) and silently kills the `velocity_limit_cost` constraint (always 0, zero gradient). Also review delta_scale=0.10 vs 3.1 reachability (target-runaway risk; resolve via delta sysid). Full ripple + checklist in the linked card.

---

## Update (2026-07-09T02:44:56.236446)

## Related: real-robot vibration symptom -> this roster

2026-07-09: a deployment-vibration differential-diagnosis card was added that maps the "real robot shakes" symptom to
the sim-to-real channels (obs-noise OOD / latency / clamp-saturation blind spot / control-rate) and back to the
interventions in THIS roster. Enter from that card when a batch experiment plan starts from a real-robot symptom rather
than from a code audit item. See [[real_robot_deployment_vibration_differential_diagnosis_by_sim_to]].

---

## Update (2026-07-11T06:41:42.683852)

## Two-phase reward-weight retune (added 2026-07-11, user-directed)

Added to the learning-dynamics roster: the next campaign runs a deliberate TWO-PHASE reward-weight schedule —
(1) pick a baseline, (2) train ONCE on the shipped weights, (3) re-tune per-term reward weights from that
run's evidence (per-term Reward/* decomposition, per-axis SS error, heavy-tail vs DC-bias), (4) retrain and
compare. Weight tuning is evidence-driven POST-run, not a priori. Phase-1 baseline must be the POST-fix
from-scratch retrained baseline (pre-TAM-reorder checkpoints are physically invalid). Full plan + coupling
gotchas (ratio-only invariance, k_bias two-file toggle, sigma/integral-gate coupling, performance_lb
recalibration): [[next_experiment_workflow_pick_a_baseline_train_once_then_re_tune]].

---

## Update (2026-07-12T13:45:17.487104)

## P4 sim-fix batch APPLIED on consolidated main (2026-07-12)

Landed via merge "P4 sim-fix batch" (constrained-albc cd192b7, marinelab 02c1007), pre-baseline. Roster status changes:

| Item | New status |
|:---|:---|
| Thruster first-order lag dt bug (NEW item, found by 2026-07-12 audit): apply_dynamics received physics_dt from _pre_physics_step (once per env step) -> lag advanced at 1/4 speed (ALBC, decimation=4) / 1/2 (BlueROV); effective T200 taus were 4x/2x configured | FIXED (step_dt at all 3 sites: main, full_dof, bluerov) |
| arm velocity_limit_sim 6.28 -> 3.1 + soft velocity_limit_cost pair | APPLIED (3.1 hard / 2.8 soft; ripple card checklist items 1-2 done; delta_scale review still OPEN) |
| action clip_fraction logging (Lead 1) | IMPLEMENTED (`Policy/clip_fraction` = |a|>=1 rate of the raw pre-clamp rollout sample, ConstraintTRPO.update(); Lead 2 now gated only on data) |
| M1 (NEW, 2026-07-12 audit): critic_uses_z=True gave the encoder NO critic learning signal -- value MSE backprops through z but TRPO reads grads via autograd.grad, so no optimizer applied the critic-side encoder grads | FIXED (encoder params now also owned by the value Adam optimizer; regression test tests/test_value_optimizer_groups.py) |
| Thruster nonlinear curve (deadband + signed-square) | merged to main OFF-by-default (P2); STAYS OFF for the baseline per the curve card's 2026-07-02 keep-off addendum (unmeasured plant model). The consolidation plan's "recommend ON" missed that addendum -- addendum wins. |

All of these change nominal dynamics or learning dynamics -> the from-scratch retrain requirement is unchanged. Record the full delta list in the campaign DESIGN.md at group creation per the migration note.
