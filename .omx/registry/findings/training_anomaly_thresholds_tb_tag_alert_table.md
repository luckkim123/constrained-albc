---
title: "training anomaly thresholds (TB tag alert table)"
tags: ["anomaly", "thresholds", "encoder", "trpo", "thruster"]
created: 2026-06-02T08:28:02.568518
updated: 2026-06-02T08:28:02.568518
sources: ["train-analyze SKILL.md (distilled before skill removal 2026-06-02)"]
links: ["training_diagnosis_decision_tree.md"]
category: reference
confidence: high
schemaVersion: 1
---

# training anomaly thresholds (TB tag alert table)

Per-TB-tag alert thresholds for ConstraintTRPO+encoder+thruster runs. Source: train-analyze/analyze_training.py ANOMALY_RULES (engine at .omx/profile/analyze_training.py). Each row = metric / alert / meaning:
- entropy < 0 -> COLLAPSED (exploration dead)
- noise_std < 0.25 -> LOW (action diversity insufficient); noise_std >= 0.95 -> CEILING (entropy bonus dominates constraints)
- z_min < -0.95 or z_max > 0.95 -> SAT (encoder latent saturated); z_std < 0.1 -> LOW (encoder output near-constant); grad_norm < 1e-4 -> DEAD (encoder not learning)
- line_search_success < 0.5 -> FAIL (TRPO updates mostly rejected)
- barrier_penalty > 0.1 -> SPIKE (barrier gradient overwhelming reward)
- mean_reward < 0 -> NEG (penalty-dominated)
- roll_deg > 20 -> HIGH; pitch_deg > 25 -> HIGH (attitude error above bound)
- action_rate_mean > 1.0 -> HIGH (jerky control); joint_vel_abs_max > 3.0 -> HIGH (joint vel dangerous)
- too_fast_ang > 0.5 / too_fast_lin > 0.5 -> HIGH (velocity over threshold frequently)
- thruster_util_max > 0.95 -> HIGH (thruster near saturation)
These are the alert bounds the analysis engine flags; pair with the diagnosis decision tree (see [[training-diagnosis-decision-tree]]) to map an alert to a likely cause and config knob.
