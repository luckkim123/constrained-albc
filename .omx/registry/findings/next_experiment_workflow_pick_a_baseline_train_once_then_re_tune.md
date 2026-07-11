---
title: "Next experiment workflow: pick a baseline, train once, then re-tune reward weights and retrain (two-phase)"
tags: ["reward-weight-tuning", "two-phase", "baseline", "retrain", "experiment-plan", "envs-main", "evidence-driven"]
created: 2026-07-11T06:41:04.657766
updated: 2026-07-11T06:41:04.657766
sources: []
links: ["reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o.md", "reward_penalty_terms_thruster_smoothness_bias_block_3_temporal_b.md", "analysis_engine_map_what_is_grow_able_vs_off_limits.md", "next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Next experiment workflow: pick a baseline, train once, then re-tune reward weights and retrain (two-phase)

Next experiment workflow: pick a baseline, train ONCE, then re-tune reward weights and retrain (two-phase).

User-directed plan recorded 2026-07-11. The next experiment campaign follows a deliberate TWO-PHASE
schedule rather than launching a fully-tuned reward config from the start.

## The plan (as instructed)

1. **Select a baseline** first. Fix the env/reward/constraint config that will serve as the reference point
   (the "canonical baseline" a later comparison narrative leans on). This is the config from which all
   weight-retune deltas are measured.
2. **Train ONCE** on that baseline — a first full training run to observe how the shipped reward weights
   actually behave (per-term `Reward/*` decomposition, which term dominates / saturates / sits near zero,
   heavy-tail vs DC-bias, per-axis SS error).
3. **Re-tune reward weights** based on that first run's evidence (NOT a priori). Adjust the per-term `k`
   values (e.g. `att_rp` k=9, `yaw_vel` k=3.5, penalties `k_thr=-0.35`, `k_s=-0.1`, `k_bias=-2.0`,
   `att_roll_weight=1.5`) where the run shows a term is mis-balanced.
4. **Retrain** with the re-tuned weights and compare against the phase-1 baseline.

## Why two-phase (rationale)

Reward-weight tuning is an EVIDENCE-driven step, not a guess. The correct balance between tracking terms and
penalties (and among the penalties themselves) is only observable AFTER a run — you need the per-term reward
decomposition and the per-axis/per-DR-level SS-error + heavy-tail behavior to see which term is starving,
saturating, or dominating. Tuning weights before that first run would be the "generic ML pattern without
evidence" anti-pattern the project rules forbid (`.claude/rules/03`). So: baseline first, measure, then tune.

## Coupling / gotchas to respect when re-tuning

- **Only term RATIOS matter to the ConstraintTRPO actor, not absolute reward scale.** Scaling ALL terms by a
  constant is invisible to the policy; only the RELATIVE weights (`k_att : k_yaw : k_thr : k_bias : ...`) change
  behavior. So a weight re-tune must change ratios, and scaling one term alone (e.g. att_rp) is the meaningful
  move. See [[reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o]].
- **`k_bias` is a two-file coupled toggle**: `if k_bias != 0` gates BOTH the reward term weight (rewards.py)
  AND the EMA-buffer update loop (albc_env.py:1133). Setting `k_bias=0` freezes `_bias_ema` at 0, not just
  the penalty. See [[reward_penalty_terms_thruster_smoothness_bias_block_3_temporal_b]].
- **Reward `sigma` is NOT just a reward knob**: `att_rp.sigma` / `yaw_vel.sigma` also set the integral-observation
  gate threshold (`_integral_gate_sigmas`, albc_env.py). Retuning sigma silently retunes the obs integral gating.
- **DORAEMON `performance_lb=250.0` is calibrated to the current reward's episode-return scale.** If a weight
  re-tune materially changes the achievable episode return, `performance_lb` may need recalibration or the
  DR-curriculum success signal drifts (all-success or all-fail → curriculum inert).
- Which files are experiment-determining source (changing them = a new baseline, invalidates old checkpoints):
  `envs/main/**` reward/config. See [[analysis_engine_map_what_is_grow_able_vs_off_limits]].

## Relation to the retrain manifest

This two-phase weight-retune rides on the from-scratch baseline retrain, not before it. All the sim-to-real
fixes in [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]] change env physics and invalidate
old checkpoints, so the phase-1 baseline here should be the POST-fix retrained baseline (not a pre-TAM-reorder
model, which is physically invalid on current code). Register the phase-1 run_id and the retuned phase-2 run_id
in the campaign group's DESIGN.md (experiments tree = SSOT) when the group is created via `train.py --run_group`.

