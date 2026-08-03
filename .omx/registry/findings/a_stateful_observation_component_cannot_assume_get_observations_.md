---
title: "A stateful observation component cannot assume _get_observations runs once per step: the teacher runner calls it an extra time per iteration"
tags: []
created: 2026-08-03T14:34:01.257153
updated: 2026-08-03T14:34:01.257153
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# A stateful observation component cannot assume _get_observations runs once per step: the teacher runner calls it an extra time per iteration

## What bit us

`compute_student_extra_obs` (the obs4 4-channel sensor model) advances a differentiator,
a first-order LPF and the zero-order-hold tick on EVERY call. Its docstring encoded the
assumption that made that safe:

> CALL EXACTLY ONCE PER ENV STEP -- the only call site is ALBCEnv._get_observations,
> which DirectRLEnv invokes once per step and once per reset.

That assumption is FALSE during teacher training. `ConstraintEncoderRunner.log` ->
`log_encoder_metrics` calls `env.get_observations()` an extra time per iteration to sample
latent health, and that lands in the same `_get_observations`. So the sensor model ran at
roughly twice its intended rate — in a channel set whose entire reason for the 25 Hz ZOH
is that rate fidelity matters.

## The symptom is loud but it is not the problem

It surfaced as `RuntimeError: Inplace update to inference tensor outside InferenceMode`
on the `env._depth_meas_prev[pending] = ...` write, because rsl_rl's logging path runs
outside the `inference_mode` the rollout wrote those buffers under. That crash is a gift:
the silent version of the same bug is a sensor model running at the wrong rate, which no
test would have caught.

## Where the guard belongs

In `ALBCEnv._get_observations`, not in the observation function:

```python
if self._extra_last_step == self.common_step_counter:
    extra_obs = self._student_extra_held.clone()
else:
    self._extra_last_step = self.common_step_counter
    extra_obs = compute_student_extra_obs(self, self._robot)
```

The env owns the step counter, so the env is what can de-duplicate. Pushing the guard
into `compute_student_extra_obs` would have broken its unit tests, which drive it with a
bare fake env where one call legitimately means one step — and would have forced those
fakes to grow a `common_step_counter` they have no business owning.

## The generalizable rule

`_get_observations` is an ACCESSOR and callers treat it as one. Any component in it that
mutates persistent state (integrator, filter, hold, counter, RNG draw) must be idempotent
within a step. Before adding such a component, grep for every `get_observations()` call
site, not just the DirectRLEnv step path. Today that set includes
`constraint_encoder_runner.log_encoder_metrics`.

Note which existing components were already safe: the integral and bias-EMA buffers are
updated in `_get_rewards`, not in `_get_observations`, so they never had this exposure.
The obs4 channels were the first stateful thing computed inside the observation path.

