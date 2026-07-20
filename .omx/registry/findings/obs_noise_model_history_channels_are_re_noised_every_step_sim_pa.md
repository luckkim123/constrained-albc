---
title: "Obs-noise model: history channels are re-noised every step (sim past is not frozen like hardware)"
tags: ["obs-noise", "sim2real", "observation", "history"]
created: 2026-07-20T04:56:02.446084
updated: 2026-07-20T04:56:02.446084
sources: []
links: ["bias_ema_obs_is_deployment_safe_computed_from_command_minus_meas.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Obs-noise model: history channels are re-noised every step (sim past is not frozen like hardware)

The 46D history block of the policy obs gets a FRESH noise draw every step, so the SAME past measurement carries a DIFFERENT noise realization each step it remains in the observation window. On hardware a past sample is recorded once and stays fixed. This is a structural sim-to-real mismatch in the obs-noise model, mild but real.

MECHANISM (verified 2026-07-20): `_hist_buf` stores CLEAN state — `albc_env.py:631-632` shifts and writes `new_entry` built from raw robot state, with no noise applied. The noise model runs LAST, on the fully assembled obs vector: `direct_rl_env.py:415` `self.obs_buf['policy'] = self._observation_noise_model(self.obs_buf['policy'])`. So current-proprio and history slots are noised together, per step, independently.

DIRECTION OF THE BIAS: independent re-draws are EASIER to average out than a frozen repeated value, so sim is mildly OPTIMISTIC on history-channel noise. The additive-bias component does NOT have this issue — it is drawn per env at reset and applied uniformly, so it stays consistent across the window as a real calibration offset would.

RELATED GAPS in the same model (all verified in config.py:271-310 / albc_env.py:1131-1145): noise is white Gaussian + episode-CONSTANT bias only — there is no random-walk DRIFT, no spikes/outliers, no quantization, no band-limited colored noise. The frozen bias matters for `_bias_ema` specifically: with a 2 s EMA window a constant sim bias converges cleanly, while a drifting real AHRS bias would be chased. cf [[bias_ema_obs_is_deployment_safe_computed_from_command_minus_meas]].

Three additive obs-noise layers exist, each with an independent randn: (1) always-on `NoiseModelWithAdditiveBiasCfg`, (2) per-env sensor FAULT scale U(0,2) (off by default), (3) DORAEMON `obs_noise_scale` u in [0,1] scaling `_OBS_NOISE_STD` (active; std only, bias untouched; u=1 gives sqrt(2)x total std).
