---
title: "bias_ema obs is deployment-safe: computed from command minus measured attitude, no privileged state"
tags: ["bias_ema", "sim2real", "observation", "p-b1"]
created: 2026-07-20T04:40:39.671033
updated: 2026-07-20T04:40:39.671033
sources: []
links: ["leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r.md", "bias_ema_observability_69_72d_improves_absolute_attitude_trackin.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# bias_ema obs is deployment-safe: computed from command minus measured attitude, no privileged state

The 3 extra obs dims added by `use_bias_ema_obs` (69->72D, ON by default since P-B1 2026-07-16) are computable ONBOARD on the real robot — they are NOT a teacher-only / privileged channel, so there is no need to distill them away for deployment.

MECHANISM (code, envs/main/albc_env.py): `_bias_ema = a*_bias_ema + (1-a)*err3` with `a = reward.bias_ema_alpha = 0.99` (~100 steps = 2 s at 50 Hz), where `err3 = [_att_rp_err[:,0], _att_rp_err[:,1], _yaw_rate_err]` (:1196-1207). Those errors come from `_compute_ang_errors` (:1155-1160): `_ang_cmd[:, :2] - [roll, pitch]` (command minus the attitude ESTIMATE) and `_ang_cmd[:,2] - root_ang_vel_b[:,2]` (command minus the gyro z rate). Every input is either the commanded setpoint (known to the controller) or a standard IMU/AHRS output. The buffer is a POLICY-INTERNAL FILTER STATE the controller integrates itself, exactly like the already-shipped `_error_integral` (`use_integral_obs`, Hwangbo-2017 pattern) — nothing is read out of the simulator.

WHY IT EXISTED BEFORE THE OBS CHANGE: `reward.k_bias` already penalized this buffer (`bias_ema_penalty`, mdp/rewards.py), so pre-P-B1 the policy was punished for a quantity it could not observe (non-Markov; theory-review R1 called it the #1 flaw). `apply_bias_ema_obs` hard-fails if `k_bias == 0` because the buffer is not updated then.

DEPLOYMENT CAVEATS (both real, neither blocking):
1. The 3 dims get obs-noise std 0 in sim (`_OBS_NOISE_STD` padded with zeros — computed, not sensor-noised, same treatment as the integral dims). On hardware the noise/drift enters UPSTREAM through the attitude estimate, and with a 2 s EMA window a slow AHRS bias integrates straight into this channel. The sim analogue of that error path is whatever DR is applied to the attitude estimate, not a noise term on these 3 dims.
2. The buffer is NOT zeroed on mid-episode command resample (only on episode reset, :1633) — see [[leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r]] for the designed-but-unlaunched A/B.

STATUS: adopted (config.py:405 `use_bias_ema_obs: bool = True`). Fair shared-anchor eval (`--doraemon-dr-from`) has P-B1 winning every ss_error cell, none/roll -67.7%; the surviving loss is hard-level transient `n_gt20` 8.667 vs 6.667. See [[bias_ema_observability_69_72d_improves_absolute_attitude_trackin]].
