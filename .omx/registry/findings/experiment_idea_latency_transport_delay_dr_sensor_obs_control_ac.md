---
title: "experiment idea: latency/transport-delay DR (sensor-obs + control-action lag) -- infra exists (isaaclab DelayBuffer) but unused; DelayedPD failed before"
tags: ["latency", "delay", "domain-randomization", "sim2real", "experiment-idea"]
created: 2026-07-08T02:50:39.246807
updated: 2026-07-20T04:55:48.094568
sources: []
links: ["real_robot_deployment_vibration_differential_diagnosis_by_sim_to.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# experiment idea: latency/transport-delay DR (sensor-obs + control-action lag) -- infra exists (isaaclab DelayBuffer) but unused; DelayedPD failed before

EXPERIMENT IDEA (proposed 2026-07-08, prompt written, NOT designed/run): add latency / transport-delay domain randomization (sensor-obs delay and/or control-action delay) to model real-robot communication lag.

## Current state (verified 2026-07-08)
NO transport/comm-delay DR exists. Confirmed absent: no delay/latency/lag field in DomainRandomizationCfg (config.py:133-222) or _PARAM_DEFS (doraemon.py:41-72); no obs-delay or action-delay buffer in the env (_hist_buf albc_env.py:288-302 is policy-input HISTORY not lag; obs reads live robot.data, action applies same step albc_env.py:587-592); fault channels (faults.py) are magnitude/noise only.

What DOES exist but is DIFFERENT: (a) thruster first-order lag tau_up=0.1/tau_down=0.05 s, DR'd via time_constant_scale=(0.7,1.3) (thruster.py:188-217, config.py:209, p_t[19]) -- a CONTINUOUS response lag, not a discrete N-step transport delay, and NOT on DORAEMON curriculum; (b) fixed 20 ms one-step decimation delay (decimation=4, config.py:358), not DR.

## Infrastructure already on the shelf (Isaac Lab, UNUSED here)
- isaaclab/.../utils/buffers/delay_buffer.py `DelayBuffer` -- generic per-env ring buffer with settable integer time_lag. The reusable primitive for any delayed signal.
- isaaclab/.../actuators/actuator_pd.py:329 `DelayedPDActuator` -- three DelayBuffers, per-env randint(min_delay,max_delay+1) on reset (:335-352). Cfg min_delay/max_delay int=0 (units=control steps).
- Neither is referenced in constrained-albc/ or marinelab/ (grep-confirmed). Available, not wired.

## Two DISTINCT latency types (design must separate)
1. Sensor/obs delay: measurements reach policy N steps late -> phase-lagged feedback -> over-control/oscillation. Wiring: DelayBuffer on OBS path (compute_policy_obs / albc_env). DelayedPDActuator does NOT cover this.
2. Control/action delay: action reaches actuator N steps late -> dead-time instability. Wiring: DelayBuffer on self._actions before physics apply (albc_env.py:587-592), or DelayedPDActuator for the arm (but see FAILED note).

## CRITICAL prior failure to reconcile
Session memory records "DelayedPD FAILED" (arm now uses ImplicitActuatorCfg albc.py:196, not DelayedPDActuatorCfg). A prior attempt to use delayed-PD on the ARM failed -- likely an implicit-vs-explicit actuator incompatibility or a delay-buffer warmup/reset interaction. Any actuator-delay design MUST recover why it failed first; the manual-action-DelayBuffer route (works for thruster too) likely avoids the implicit-actuator issue. The sensor-delay path is independent of that failure.

## Recommended minimal first cut (rules/03: smallest discriminating design)
Start with ONE delay type (sensor-obs OR control-action), integer step units (each=20ms), small max (1-5 steps=20-100ms, ground in a real comm-lag number if available), STATIC uniform DR first (mirrors how time_constant_scale is handled) rather than DORAEMON (a discrete integer delay is awkward for Beta-continuous curriculum -- would need sample-then-round). Zero-delay must be byte-identical to baseline (pass-through DelayBuffer, regression test). If made a DR param, add to p_t[+1] per the one-scalar-per-DR-param invariant (priv_obs_bounds re-index). Prompt: PROMPT_latency_dr.md. Provenance: session project-obs-space-doc-qa-260708.

---

## Update (2026-07-20T04:55:48.094568)

## STATUS CORRECTION 2026-07-20 (supersedes the 2026-07-08 'NO delay DR exists' state above)

CONTROL-ACTION delay is now IMPLEMENTED (commit `eb3ce35`, 'feat(latency-dr): wire DelayBuffer on applied action, off-default byte-identical' — the `exp/latency-dr` branch landed). Verified in code 2026-07-20:

- `DomainRandomizationCfg.control_delay_steps: tuple[int, int] = (0, 0)` (config.py:239) — integer control steps, 1 step = 20 ms @ 50 Hz. Comment records the experiment value as (0, 3).
- `_draw_control_delay` (albc_env.py:52-72): `hi <= 0` returns `(zeros, None)` = skip the pass entirely; otherwise an isaaclab `DelayBuffer(history_length=hi)` with per-env `randint(lo, hi+1)` lag.
- Applied at `albc_env.py:655` on `self._actions`; re-drawn per env on reset (`:1497-1501`).
- The per-env lag IS exposed to the critic: `observations.py:178-179` normalizes it by `control_delay_steps[1]` into the 28D privileged vector (the ALBCEnvCfg docstring now reads '28D privileged (incl. measured lin_vel + control-action delay)').
- As designed in the original card: STATIC uniform DR, NOT on the DORAEMON curriculum (integer delay does not fit the Beta-continuous sampler). It is not in `_PARAM_DEFS` (20 params, none of them delay).

WHAT IS STILL TRUE FROM THE ORIGINAL CARD:
- **SENSOR/OBS delay remains ABSENT.** `_get_observations` reads live `robot.data`; no DelayBuffer on the obs path. Latency type 1 of the two the card separates is still unwired.
- **The default is OFF and no teacher run has ever trained with it.** `control_delay_steps=(0,0)` on every posttam run, so the deployed/analyzed policies are all delay-free-trained. Channel B of [[real_robot_deployment_vibration_differential_diagnosis_by_sim_to]] is therefore still an open, untested sim-to-real gap — the infra question is closed, the EXPERIMENT question is not.
- Thruster `time_constant_scale (0.7,1.3)` on tau_up=0.1/tau_down=0.05 s is a CONTINUOUS response lag, not transport dead-time; the fixed 20 ms decimation is structural and has no jitter DR.
