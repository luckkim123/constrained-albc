---
title: "training diagnosis decision tree"
tags: ["diagnosis", "anomaly", "encoder", "trpo", "thruster", "procedure"]
created: 2026-06-02T08:28:21.342549
updated: 2026-06-02T08:28:21.342549
sources: ["train-analyze SKILL.md (distilled before skill removal 2026-06-02)"]
links: ["training_anomaly_thresholds_tb_tag_alert_table.md"]
category: debugging
confidence: high
schemaVersion: 1
---

# training diagnosis decision tree

Maps an anomaly pattern (see [[training-anomaly-thresholds-tb-tag-alert-table]]) to a likely cause and the config knob to check. Source: train-analyze/analyze_training.py DIAGNOSIS block (engine at .omx/profile/analyze_training.py). Diagnosis always runs (not only when tier-1 anomalies fire); it checks anomaly patterns AND data-derived patterns (plateau, divergence).
- entropy COLLAPSED + noise LOW -> noise floor too low, check min_std config
- z SAT + grad DEAD -> encoder saturated, check weight_decay/activation/z_bounds_coef
- ls_success FAIL -> barrier_t too low (cost gradient dominates) OR too many constraints active simultaneously
- arm frozen (jnt_vel < 0.5, act_size < 0.15) -> arm constraints suppress movement, check constraint budgets / singularity budget
- reward plateau -> constraint pressure preventing improvement OR curriculum needs adjustment
- reward declining all 4 quarters -> training diverged, fundamental issue
- reward early convergence (Q1-Q2 up, Q3-Q4 flat) -> curriculum exhausted or constraint ceiling reached
- mode CYCLING (switch rate > 0.2) -> constraint budget too tight (cost oscillates around d_k); barrier excluded during recovery creates gradient discontinuity; raise budget or keep barrier active in recovery
- barrier_penalty SPIKE (max > 0.1) -> barrier gradient overwhelms reward at small margins; raise margin_min clamp or reduce beta
- too_fast_ang HIGH (> 50%) -> TAM yaw coupling causes spin-out at high init_noise_std; lower init_noise_std or remove velocity termination (use soft constraints)
- thruster saturation (util_max > 0.95) -> wrench commands too aggressive or init_noise_std too high
- gradient misalignment (enc_cos_vanilla_natgrad < -0.3) -> encoder gradient opposes natural gradient; trust region distorts encoder updates; check cg_damping and encoder_lr
- death spiral (terminated > 50% + too_fast_ang > 80%) -> all-negative rewards make early death optimal; remove velocity termination or lower init_noise_std
