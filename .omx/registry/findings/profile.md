---
title: "Workspace profile (auto-synced)"
tags: ["profile", "auto-synced"]
created: 2026-07-13T23:34:22.396946
updated: 2026-07-13T23:34:22.396946
sources: []
links: []
category: environment
confidence: high
schemaVersion: 1
---

# Workspace profile (auto-synced)

Regenerated from `.omx/profile/` at 2026-07-13T23:34:22.396946. Do not edit; run `omx wiki sync-profile` after profile changes.

## metrics.yaml

```yaml
# OMX profile - metrics vocabulary + output root.
# Consumed by omx_paths.Profile (vocabulary tier) and exp-analyze (#4).
# Set pending_approval to false (or delete the key) on approval.
aggs:
- by_axis
- mean_std
keep_policy: pass_only
metrics:
# --- tracking error (primary objective) ---
# Default task is attitude-only (roll/pitch + yaw-rate); it tracks no linear velocity,
# so lin_err_x/y/z are intentionally absent (the legacy full-DOF env logs them).
- reward_total
- att_roll_err_deg
- att_pitch_err_deg
- yaw_rate_err
# --- reward decomposition (7 attitude-only terms: which axis drives plateau vs which penalizes) ---
# tracking terms (should rise): att_rp, yaw_vel. penalty terms (negative drag):
# bias, smoothness, thruster, torque. (full-DOF additionally has lin_vel.) total plateau
# is diagnosed by decomposition, not
# Reward/total alone (rule 03 differential diagnosis). reward_total/Reward/total are
# PER-STEP (same unit as the 8 terms below). Train/mean_reward is the EPISODE-cumulative
# return (~29x larger, verified step-wise) -- it is what DORAEMON compares to
# performance_lb(=90) for success, so keep it for the curriculum analysis.
- Train/mean_reward
- Reward/att_rp
- Reward/yaw_vel
- Reward/bias
- Reward/smoothness
- Reward/thruster
- Reward/torque
# --- learning dynamics (TRPO) ---
# surrogate_loss = policy improvement signal (should rise); value_function/cost_value
# = critic losses (should fall). cost_value is ConstraintTRPO-specific: if it does not
# converge, constraint advantages are noise and IPO misbehaves. Loss/kl, Loss/learning_rate,
# Noise/std_min, and the Policy/* duplicates (entropy/noise/line_search) are omitted as
# redundant -- the same signal is already covered under its primary name.
- entropy
- noise_std
- line_search_success
- kl
- Policy/surrogate_loss
- Loss/value_function
- Loss/cost_value
- Grad/actor_step
- Grad/sigma_step
# --- encoder health: z saturation/collapse + gradient liveness ---
# z_std<0.1 LOW (near-constant); z_min<-0.95 or z_max>0.95 SAT (softsign clipped);
# encoder_grad_norm<1e-4 DEAD (not learning). NOTE: TB tells "update applied", NOT
# "meaningful learning" -- confirm with encoder_tools.py sweep (rule 03-analysis-quality).
- Encoder/z_std
- Encoder/z_min
- Encoder/z_max
- Encoder/z_mean
- Policy/encoder_grad_norm
- Grad/enc_step
# --- constraint health: IPO barrier + ALL 10 constraints (margin>0 = satisfied) ---
# Expanded 4->10 (2026-06-14): the 2026-06-02 "4 core + on-demand" choice hid the 2nd
# binding constraint (rp_vel_settling, J_C/d_k=0.504) and every early-satisfy candidate
# the user flagged for the constraint-rebalance/removal direction. Full-set tracking is
# the prerequisite for that next experiment (need before/after viol+margin per constraint).
# viol = J_C - d_k (starts at -d_k, rises toward 0 = healthy); margin ~= -viol in slack regime.
# budgets (config.py:57-69): thruster_util 0.40, rp_vel_settling 0.20, rp_rate/yaw_rate 0.10,
# arm_torque 0.08, manipulability 0.05, arm_joint_vel 0.02, attitude/joint1_pos/cumul_yaw 0.01.
- barrier_penalty
- Constraint/margin/attitude
- Constraint/margin/arm_torque
- Constraint/margin/arm_joint_vel
- Constraint/margin/joint1_pos
- Constraint/margin/cumul_yaw
- Constraint/margin/thruster_util
- Constraint/margin/rp_rate
- Constraint/margin/yaw_rate
- Constraint/margin/rp_vel_settling
- Constraint/margin/manipulability
- Constraint/viol/attitude
- Constraint/viol/arm_torque
- Constraint/viol/arm_joint_vel
- Constraint/viol/joint1_pos
- Constraint/viol/cumul_yaw
- Constraint/viol/thruster_util
- Constraint/viol/rp_rate
- Constraint/viol/yaw_rate
- Constraint/viol/rp_vel_settling
- Constraint/viol/manipulability
# --- DR curriculum (DORAEMON): is the env still too easy at the end? ---
# success_rate vs alpha(0.5): if success stays HIGH while entropy/std plateau, there is
# headroom DORAEMON is not using (env ended too easy). entropy_before = cumulative
# difficulty (flattening iter = expansion stalled). kl_step = trust-region cap hit?
# ess_ratio = IS estimate reliability (low -> updates rejected). std/* = per-param
# difficulty WIDTH; mean/* = difficulty DIRECTION. 4 physics-dominant params chosen;
# the other 13 (cob/cog offsets, water_density, volume...) added on demand.
- doraemon_success_rate
- DORAEMON/entropy_before
- DORAEMON/kl_step
- DORAEMON/ess_ratio
- DORAEMON/std/ocean_current_strength
- DORAEMON/std/payload_mass
- DORAEMON/std/added_mass_scale
- DORAEMON/std/linear_damping_scale
- DORAEMON/mean/ocean_current_strength
- DORAEMON/mean/payload_mass
- DORAEMON/mean/added_mass_scale
- DORAEMON/mean/linear_damping_scale
output_root: experiments
# --- diagnostic groups for the exp-analyze completeness lint (omx report-coverage) ---
# Each group must have >=1 metric referenced in a report; otherwise the lint loud-fails.
# Mirrors the "# --- ... ---" comment headers above, promoted to machine-readable form
# so a report cannot silently skip a whole diagnostic family (GAP 4 / dr-harder incident).
groups:
  # tracking error is discussed by AXIS name + ss_error in reports (not the raw TB
  # tag att_roll_err_deg), so the lint tokens are the report-facing vocabulary.
  tracking: [ss_error, roll, pitch, yaw]
  reward_decomp: [Reward/att_rp, Reward/yaw_vel, Reward/bias, Reward/smoothness, Reward/thruster, Reward/torque]
  trpo: [entropy, noise_std, line_search_success, kl, Policy/surrogate_loss, Grad/actor_step, Grad/sigma_step]
  critic: [Loss/value_function, Loss/cost_value]
  encoder: [Encoder/z_std, Encoder/z_min, Encoder/z_max, Policy/encoder_grad_norm, Grad/enc_step]
  constraint: [barrier_penalty, Constraint/margin/attitude, Constraint/margin/arm_torque, Constraint/margin/arm_joint_vel, Constraint/margin/joint1_pos, Constraint/margin/cumul_yaw, Constraint/margin/thruster_util, Constraint/margin/rp_rate, Constraint/margin/yaw_rate, Constraint/margin/rp_vel_settling, Constraint/margin/manipulability, Constraint/viol/attitude, Constraint/viol/arm_torque, Constraint/viol/arm_joint_vel, Constraint/viol/joint1_pos, Constraint/viol/cumul_yaw, Constraint/viol/thruster_util, Constraint/viol/rp_rate, Constraint/viol/yaw_rate, Constraint/viol/rp_vel_settling, Constraint/viol/manipulability]
  doraemon: [doraemon_success_rate, DORAEMON/entropy_before, DORAEMON/kl_step, DORAEMON/ess_ratio]
# Markers proving the report was grounded in the training-log engine (analyze_training.py)
# rather than hand-extracted final scalars. >=1 must appear or the lint loud-fails.
engine_markers: [DIAGNOSIS, TIER 1, TIER 2, TIER 3, TREND, changepoint, plateau, regime, phase]
# --- required report SECTIONS (markdown headings), dr_harder 2026-06-08 incident ---
# The token-group lint above checks metric COVERAGE but cannot see a whole section
# being deleted when it maps to no metric group. The 2026-06-08 re-analysis dropped
# the `## generalization (in-dist hard vs OOD)` section entirely (OOD was the PHASE B
# deliverable) and still passed the lint. These tokens MUST each appear inside a
# markdown heading or `omx report-coverage` loud-fails. generalization is the one the
# incident lost; the rest are the spine every dr_harder report carries.
required_sections: [tracking, generalization, reward, trpo, critic, encoder, constraint, doraemon, verdict]
pending_approval: false
run_id_regex: null
score_formula: null
sources:
- tensorboard
- wandb_offline
- eval
- encoder
views:
- trajectory
- per_axis_bar
- overlay
```

## rules.md

# Analysis discipline (consumed as guidance by exp-analyze)

## Always
- (e.g.) Report CV = std/mean for every metric; mean alone is half the picture.

## Never
- (e.g.) Assert "heavy-tail" without per-env peak counting.

## Notes
- (free form)


## tree schema

(no tree.yaml)

## evaluator seal

status: absent (sealed_at: None)
