---
title: "experiment idea: latency/transport-delay DR (sensor-obs + control-action lag) -- infra exists (isaaclab DelayBuffer) but unused; DelayedPD failed before"
tags: ["latency", "delay", "domain-randomization", "sim2real", "experiment-idea", "control_delay", "delay-buffer", "sim-to-real", "doraemon", "eval-instrument", "e1", "user-decision"]
created: 2026-07-08T02:50:39.246807
updated: 2026-07-20T05:14:39.045842
sources: ["trpo_e1_latdr_260713_124923", "diagnose-20260713-184751", "next-20260713-122215", "next-20260713-142602", "dr_config.py", "eval.py"]
links: ["real_robot_deployment_vibration_differential_diagnosis_by_sim_to.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md", "an_off_doraemon_channel_that_costs_return_stalls_the_curriculum.md", "baseline_open_experiment_leads_backlog_beyond_heavy_tail_triage.md", "xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e.md", "cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "BLOCKER 1: delay-sweep eval instrument (proposal next-20260713-142602) does not exist -- dr_config.py/eval.py have zero control_delay at HEAD 2026-07-20, so the benefit half is unmeasurable. BLOCKER 2: delay is off-DORAEMON and stalls the curriculum -- needs either _PARAM_DEFS dim or a MEASURED performance_lb recalibration. Also parked under the 2026-07-20 batch-pass decision."
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

---

## Update (2026-07-20T05:14:39.045842)

## UPDATE 2026-07-20 (B): e1 ALREADY RAN THIS — result, and why it answered nothing

The 2026-07-08 body and the 2026-07-20 (A) status correction both describe this as an
untried idea. It is not: probe **e1 latdr** (`trpo_e1_latdr_260713_124923`, campaign p7_tail,
proposal `next-20260713-122215`, analysis `diagnose-20260713-184751`) trained a full 5000-iter
run with `control_delay_steps (0,0) -> (0,3)` (0-60 ms @ 50 Hz) as its single variable.
Any latency redo MUST start from e1's outcome, not from a blank page.

### e1's verdict: BOTH bands UNMEASURABLE — a design failure, not a result

- The proposal's H1 (delay trains in for free) and H2 (delay costs jitter >=2x or ss_error
  >+20%) were BOTH defined at the `hard` eval level — the one level that is per-run
  non-comparable ([[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]]).
  Neither band could be read.
- The only fair level (`none`, fixed nominal physics) showed e1 markedly WORSE:
  att_norm ss_error 1.903 vs baseline 0.532 deg (3.6x); att_norm ss_jitter 0.950 vs 0.200
  deg (4.75x); roll none 1.647 vs 0.436.
- **That 3.6x is NOT a clean latency price and must never be quoted as one.** e1's DORAEMON
  curriculum stalled infeasible for the entire run (mode -2, success 0.09, inertia_scale
  Beta-std CONTRACTED to 0.111 vs baseline's 0.268), so e1's policy trained under a NARROWER
  DR than baseline. The number is delay + a broken curriculum, inseparably.
- One adverse tail signal survives the confound: at ood, #env with peak |error_roll| > 20 deg
  rose 1 (baseline) -> 5 (e1), i.e. MORE extreme-outlier envs despite e1's milder exam.
  [CONFIDENCE: MED — 64 env, single seed.]

### BLOCKER 1 (instrument): eval cannot inject delay, so the BENEFIT half is unmeasurable

`constrained_albc/analysis/dr_config.py` contains **zero** occurrences of `control_delay`
(`_DR_TUPLE_FIELDS`, `_TRUE_NOMINAL_PHYSICS`), and so does `eval.py` — re-verified at HEAD
**2026-07-20**, still zero, unchanged since the 2026-07-13 observation. No eval level applies
any delay.

Consequence, and this is the structural reason e1 is a discard rather than a finding: e1 was
trained WITH delay and graded on delay-FREE axes. That setup can only ever show the COST of
delay exposure, never the BENEFIT (delay tolerance) the probe existed to buy. e1's own
proposal admits this in a parenthetical inside [H1-PREDICTS]; the companion proposal
`next-20260713-142602` was written specifically to build the missing delay-sweep eval
instrument (fixed `control_delay_steps = d`, d in {0,1,2,3}, as a SEPARATE sweep at base
levels none+hard, leaving `_DR_TUPLE_FIELDS` untouched so existing levels stay
byte-comparable) — **and it was never built.**

**Do not re-run a latency training probe before this instrument exists.** Rerunning without it
reproduces e1's unanswerable design exactly.

### BLOCKER 2 (curriculum): delay is an off-DORAEMON channel that stalls the curriculum

Mechanism and treatment are already recorded in
[[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_]]: delay is absent from
DORAEMON `_PARAM_DEFS` (20 dims) so the curriculum cannot ease it; the ~10% return tax pins
mean return (~197) below `performance_lb` (config.py = 250, with baseline ~247 sitting just
under it), so `doraemon_success_rate` never reaches alpha=0.5 and DORAEMON sits at mode -2 all
run, contracting instead of widening.

Either fix is required before a redo, and they are alternatives, not both:
1. make `control_delay_steps` a DORAEMON `_PARAM_DEFS` dim (curriculum can then ease it when
   infeasible), or
2. recalibrate `performance_lb` to the delay-ON nominal return — **MEASURED, not guessed**.

### USER DECISION 2026-07-20: latency IS wanted in the final training config

[DECISION] User: run a latency experiment later, and include latency DR in the FINAL model
training — the real robot has transport delay, so a sim without it is a sim-to-real gap.
[CONFIDENCE: HIGH — user domain judgment, same authority as the 2026-07-16 e4 rejection.]

This settles the DIRECTION and flips this page from "idea" to "endorsed, gated". It does NOT
authorise a launch: both blockers above stand, and per the 2026-07-20 parking decision every
open lead is planned and executed in ONE later batch pass
([[baseline_open_experiment_leads_backlog_beyond_heavy_tail_triage_]]).

Note the principle is the same one that KILLED the e4 xy-offset prune
([[xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e]]): a physically-real
property of the hardware belongs in the sim. There it forbade removing a real disturbance;
here it argues for adding one. e1's negative result is evidence about a broken probe design,
NOT evidence that the robot has no delay.

### Ordered plan for the redo (design input for exp-design; not a proposal)

1. Build the delay-sweep eval instrument (proposal `next-20260713-142602`, zero-GPU code +
   user-gated eval runs). Sweep the EXISTING baseline checkpoint first — this alone yields
   the never-measured error-vs-delay response curve and may show the delay tolerance is
   already there for free (that proposal's Lane 1).
2. Only if step 1 shows a real deficit: resolve BLOCKER 2 by one of the two fixes, then train
   with delay ON, and grade on the delay sweep — not on the delay-free axes that made e1
   unreadable.
3. Cross-run comparison anchors to `none` or to a shared reference DR via
   `--doraemon-dr-from` ([[cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov]]).

Sensor/observation delay remains entirely unimplemented (2026-07-20 (A) correction) and is a
separate channel from the control-action delay e1 exercised.

