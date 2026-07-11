---
title: "experiment idea: latency/transport-delay DR (sensor-obs + control-action lag) -- infra exists (isaaclab DelayBuffer) but unused; DelayedPD failed before"
tags: ["latency", "delay", "domain-randomization", "sim2real", "experiment-idea"]
created: 2026-07-08T02:50:39.246807
updated: 2026-07-08T02:50:39.246807
sources: []
links: []
category: convention
confidence: medium
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

