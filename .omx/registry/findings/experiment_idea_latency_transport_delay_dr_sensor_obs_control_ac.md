---
title: "experiment idea: latency/transport-delay DR (sensor-obs + control-action lag) -- infra exists (isaaclab DelayBuffer) but unused; DelayedPD failed before"
tags: ["latency", "delay", "domain-randomization", "sim2real", "experiment-idea", "control_delay", "delay-buffer", "sim-to-real", "doraemon", "eval-instrument", "e1", "user-decision"]
created: 2026-07-08T02:50:39.246807
updated: 2026-08-04T17:50:19.276763
sources: ["trpo_e1_latdr_260713_124923", "diagnose-20260713-184751", "next-20260713-122215", "next-20260713-142602", "dr_config.py", "eval.py", "next-20260724-033157", "static_260724_083142", "static_260724_085559"]
links: ["real_robot_deployment_vibration_differential_diagnosis_by_sim_to.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md", "an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_.md", "baseline_open_experiment_leads_backlog_beyond_heavy_tail_triage_.md", "xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e.md", "cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov.md", "real_albc_deployment_state_estimation_rates_measured_from_code_a.md", "obs4_student_extra_observation_interface_4_deployable_channels_r.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
blocked-on: "BLOCKER 1 (eval instrument) RESOLVED; BLOCKER 2 (delay is off-DORAEMON, needs _PARAM_DEFS dim or MEASURED performance_lb recalibration) remains for the training side. As of 2026-08-03 this lead is no longer speculative margin -- the real bus rate is MEASURED and the deployed system already carries observation staleness of the same order the Z4 sweep priced; priority argument strengthened, blocker unchanged"
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
[[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum__]]: delay is absent from
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
([[baseline_open_experiment_leads_backlog_beyond_heavy_tail_triage__]]).

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

---

## Update (2026-07-24T00:05:54.075973)

[FINDING] E2/Z4-sweep (proposal next-20260724-033157) RESOLVES the benefit/cost question:
H2 CONFIRMED overwhelmingly -- the delay-naive anchor policy has ZERO free delay tolerance.
BLOCKER 1 CLEARED: the delay-sweep eval instrument now EXISTS (eval.py --control-delay <N>,
commits 99de708 + fix 790b0c8 on branch exp/latency-eval-instrument; d=0 byte-identical stock,
gate passed: d0 att_norm 0.630 vs anchor 0.586 within eval noise). none-level delay response on
anchor s30 model_4999 (config-clean -- max_thrust forced 1.0 at none), att_norm ss_error / roll
ss_jitter vs delay:

| d | delay | att_norm ss_error | roll ss_jitter |
|---|---|---|---|
| 0 | 0 ms  | 0.630 deg (base)  | 0.338 deg (1.0x) |
| 1 | 20 ms | 1.477 deg (+134%) | 0.745 deg (2.2x) |
| 2 | 40 ms | 3.246 deg (+415%) | 1.623 deg (4.8x) |
| 3 | 60 ms | 5.608 deg (+790%) | 2.879 deg (8.5x) |

Even a SINGLE 20 ms step of un-trained dead-time roughly doubles attitude error and jitter;
60 ms drives ~8x jitter / ~9x error (policy oscillates). hard-level is the same shape
(d=3 att_norm +1143%). Pre-registered H2 (d=3/none >=+30% att OR >=2x jitter) is cleared at
EVERY d>=1.

[EVIDENCE: sweep2 eval/static_260724_{083142,083940,084749,085559} on anchor model_4999,
64 env cuda:0, code-exec 2026-07-24; thresholds from proposal next-20260724-033157. The FIRST
sweep (static_260724_{075630..082030}) is INVALID -- a buffer-allocation bug made the delay a
no-op, caught by byte-identical d=0..3, fixed in 790b0c8.]
[CONFIDENCE: HIGH]

STATUS: needs-experiment (the TRAINING follow-up remains). The eval/measurement half is DONE
(H2 -- delay needs training exposure, quantifying the user's 2026-07-20 "latency in final config"
decision). The remaining experiment is a delay-ON training run (control_delay_steps (0,3)), still
gated on BLOCKER 2: delay is off-DORAEMON and stalls the curriculum -- needs either a _PARAM_DEFS
dim or a MEASURED performance_lb recalibration to the delay-ON nominal return. Write it as a
SEPARATE proposal (human-gated launch) and grade it on THIS sweep, not delay-free axes. The e1
run (trpo_e1_latdr) already showed a naive delay-ON run stalls -- do not repeat that design.

---

## Update (2026-07-24T07:18:33.943973)

[MEASURED 2026-07-24] Z4 delay eval sweep DONE -> BLOCKER 1 (no delay-sweep instrument) RESOLVED. Built `--control-delay N` on exp/latency-eval-instrument (99de708 + 790b0c8 DelayBuffer-at-env-init); d=0 reproduces the clean anchor byte-for-byte (roll ss_error none 0.539) = instrument is a clean no-op at d=0, so the delay effect is REAL not artifact. Anchor s30, none+hard, d in {0,1,2,3} (1 step = 20 ms @ 50 Hz). att_norm ss_error vs d0: none d1=+134% (0.63->1.47), d2=+414%, d3=+790% (5.60); hard d1=1.7x, d2=8.4x, d3=12.8x (10.68 deg); roll ss_jitter blows up 2.2x/4.8x/8.5x (none) and 2.8x/7.6x/11.6x (hard); hard survival drops 100->92%. VERDICT: H2 (delay-naive policy degrades MATERIALLY) CONFIRMED strongly -- the H1 "delay is free" tolerance (att_norm within +10%, jitter <2x) breaks already at d=1 (20 ms). Control latency is NOT free; large sim-to-real risk. CONSEQUENCE: a delay-ON training probe is justified (benefit-half now measured). CAVEAT: the magnitude is large enough that the delay-ON training proposal should FIRST re-confirm the DelayBuffer semantics in code (rule 03 "verify implementation not name"). BLOCKER 2 (off-DORAEMON, performance_lb recalibration) still gates the training side. Data: experiments/.../trpo_buoyanchor_s30_260722_134743/sweeps/z4_delay/d*/summary.json.

---

## Update (2026-08-03T09:07:52.061131)


## 2026-08-03 -- the measured bus rate reclassifies this lead from hypothetical margin to current deployment condition

[FINDING] The real sensor rates are now measured from firmware, not assumed
([[real_albc_deployment_state_estimation_rates_measured_from_code_a]]): `/hero_agent/sensors`
(attitude + gyro + depth) publishes at <= ~25 Hz while the policy ticks at 50 Hz, and joints arrive at
10 Hz. The deployed system therefore ALREADY runs on observations aged roughly 0-40 ms on the attitude
channel and up to 100 ms on the joint channel. The Z4 sweep on this page priced 20 ms of loop
dead-time at +134% attitude error and 2.2x roll jitter, and 40 ms at +415% / 4.8x. The staleness the
robot actually has sits inside that measured band.

[EVIDENCE: rate page (agent.ino 4-phase loop, delay(9) per phase, publish only in the last phase ->
period >= 36 ms, exact value = loop_speed/4 self-telemetered in the sensors DEPTH field; Dynamixel
LOOP_HZ = 10.0; control_hz = 50 / CONTROL_DT = 0.02) against the Z4 table already on this page
(experiments/.../trpo_buoyanchor_s30_260722_134743/sweeps/z4_delay/d*/summary.json).]
[CONFIDENCE: HIGH]

DO NOT read the Z4 d-numbers as a spec for the sensor side. Z4 delayed the ACTION with a fixed
DelayBuffer; what the rate measurement describes is OBSERVATION staleness whose age VARIES between
ticks because a slower publisher is being zero-order held. Both add dead-time to the same loop, so the
order of magnitude carries; the exact penalty does not, and asserting it would be the "verify
implementation, not name" trap. The training probe should model the sensor side explicitly rather than
reuse a control-side buffer and call it equivalent.

SCOPE BOUNDARY, so this does not get silently absorbed by another arm: the obs4 work
([[obs4_student_extra_observation_interface_4_deployable_channels_r]]) zero-order holds ITS OWN four
new channels at the real bus rate, but the pre-existing 72D observation vector is still trained fresh
at 50 Hz. Closing the staleness gap on the MAIN observation vector belongs to this lead, not to the
B2 arm. B2 must not be graded as if it addressed it.

CONSEQUENCE: BLOCKER 2 is unchanged -- delay is still off-DORAEMON and still needs either a
_PARAM_DEFS dim or a measured performance_lb recalibration, and the naive delay-ON run (trpo_e1_latdr)
already showed what skipping that costs. What changed is the justification: this is no longer a
robustness margin someone might want, it is a condition the hardware imposes today.

---

## Update (2026-08-04T17:50:19.276763)

## VERDICT 2026-08-05 -- CLOSED-OUT-OF-SCOPE for gen-1, carried as a gen-2 engine requirement

Recorded by the backlog-closeout program (`.omx/programs/backlog-closeout/PLAN.md`). The eval half of
this lead is now measured on the FINAL gen-1 teacher rather than on the superseded anchor, and the
training half is deliberately not run. Both parts are justified below.

### 1. The measurement, on the model that would actually deploy

`trpo_eint_s30_rs2350_260727_195102` / `model_4999.pt`, `--control-delay 1|2|3` (20/40/60 ms at
50 Hz), 64 env, all four DR levels, anchored to E-int's own DORAEMON, GPU1, single seed.
d0 = `eval/static_260804_203719`; d1/d2/d3 = `eval/static_260805_{021830,022832,023838}`, each
carrying its own `eval.log` with the four per-level injection markers. Survival is **100 % at every
level and every delay point**, so nothing here is survivorship-contaminated.

PAIRED `none` response (0 % DR -- the only level where d0 pairs with d>=1, see section 3):

| d | delay | att_norm ss_error | vs d0 | roll ss_jitter | vs d0 |
|--:|--:|--:|--:|--:|--:|
| 0 | 0 ms | 0.4997 deg | 1.00x | 0.1331 deg | 1.00x |
| 1 | 20 ms | 1.2746 deg | 2.55x | 0.6448 deg | 4.84x |
| 2 | 40 ms | 3.2286 deg | 6.46x | 1.5355 deg | 11.54x |
| 3 | 60 ms | 6.1165 deg | 12.24x | 2.7349 deg | 20.55x |

The slope BETWEEN delay points is paired at all four levels (d1/d2/d3 are mutually paired
everywhere). At `hard` the same progression reads 2.3937 -> 4.8417 -> 9.3941 deg.

**Deployment reading.** The measured bus gives the attitude channel 0-40 ms of staleness, which
brackets d1-d2. At d2 this teacher's nominal attitude error is **3.23 deg against 0.50 deg clean** --
a 6.5x degradation inside the band the hardware already imposes. The 2026-07-20 user decision that
latency belongs in the final training config is therefore confirmed by measurement on the actual
final teacher, not only on the anchor.

**Scope limit, repeating this page's own 2026-08-03 warning rather than quietly ignoring it**: this
sweep delays the CONTROL ACTION with a fixed per-env DelayBuffer. The rate measurement describes
OBSERVATION staleness whose age VARIES between ticks because a slower publisher is zero-order held.
Both add dead time to the same loop so the order of magnitude carries; these numbers are NOT a
sensor-side spec. The sensor/observation delay path remains entirely unimplemented.

### 2. Why the training half is not run, and what would unblock it

BLOCKER 2 is unchanged: `control_delay_steps` is not a DORAEMON `_PARAM_DEFS` dim, so the curriculum
cannot ease it, and the return tax pins mean return under `performance_lb` -- which is exactly how
`trpo_e1_latdr` stalled at mode -2 for its whole run. Neither of the two admissible fixes was
available inside this program:

- **Adding a `_PARAM_DEFS` dim** is an engine change to the curriculum. Made mid-program it voids
  E-int as the comparison baseline for the DGX flagship, and its importance-sampling behaviour could
  not be validated before the deadline -- so a run using it would confound the mechanism with its
  implementation, which is the same reason this program declined the DORAEMON nominal-corner floor.
- **Recalibrating `performance_lb` to the MEASURED delay-ON nominal return** needs a pilot run to
  learn the new return ceiling, then the real run. That is two GPU0 slots. GPU0 had three, all
  committed: Run A (iteration-budget, closes the curriculum lead and corrects DGX Gate A) and Runs
  B/C (the R6 integral-gate sweep).

A naive delay-ON run without either fix reproduces e1 exactly and answers nothing. Running it to
have "run something" would have been the worse choice.

**Carried forward as a gen-2 requirement, not dropped.** The user's 2026-07-20 decision stands. The
recipe is fully specified: resolve BLOCKER 2 by ONE of the two routes above, train with
`control_delay_steps (0,3)`, and grade on THIS sweep rather than on delay-free axes. Because the
`none` column is now measured on the final teacher, a delay-ON run has a proper benefit bar to clear
instead of the unreadable design e1 had.

### 3. CORRECTION to the 2026-07-24 Z4 numbers on this page -- the hard column is UNPAIRED

Found while re-running the sweep. `_draw_control_delay` (`albc_env.py:66-85`) returns early at
`hi <= 0` and **skips its `torch.randint`**, so a d=0 run and a d>=1 run consume different amounts of
RNG and every DR draw after the first reset diverges. `none` looks clean only because at 0 % DR there
is nothing to shift.

Measured on the Z4 artifacts themselves: d0-vs-d1 shows **0 of 23** `dr_`/`fault_` keys differing at
`none` and **23 of 23** at soft, medium and hard. Among the d>=1 points, d2 and d3 pair at all four
levels (both 92.19 % survival at hard) while d1 breaks against them at medium and hard (98.44 %) --
a different death count means a different number of resets means a different number of draws.

Consequence:
- Z4's **`none` column stands** as a valid paired measurement (d1 +134 %, d2 +415 %, d3 +790 %).
- Z4's **`hard` column** (d1 1.7x, d2 8.4x, d3 12.8x, survival 100->92 %) compares delay against a
  DIFFERENT DR sample. The ALBC decision floors declare themselves "paired same-machine" and do not
  apply to it. The effect sizes are far too large to be sampling noise, so the qualitative claim
  survives -- but the multipliers must not be quoted as precise, and no floor-based verdict may rest
  on them.

The RNG consumption is deliberately NOT fixed: that is an env-code change that would alter the plant
and void the current baseline. It is recorded here so the next person budgets for it rather than
rediscovering it.

[EVIDENCE: pairing matrix computed elementwise over `dr_*`/`fault_*` npz keys for all 6 delay-point
pairs x 4 levels on the E-int sweep, and for d0-vs-d{1,2,3} and d{1,2,3} inter-pairs on the Z4
artifacts under `trpo_buoyanchor_s30_260722_134743/sweeps/z4_delay/`; `albc_env.py:66-85` read at
HEAD. Response table from the four `summary.json` files named in section 1. Index and decoder written
to `<E-int run>/eval/README.md`. Code-exec 2026-08-05.]
[CONFIDENCE: HIGH]

### 4. A second instrument trap, for whoever runs the delay-ON probe

Do NOT reach past `--control-delay` to the Hydra path `env.randomization.control_delay_steps`. It is
accepted, exits 0, and injects nothing: `apply_dr_config()` rebuilds the randomization config before
env creation and at every DR level, and the field is not a `_DR_TUPLE_FIELDS` dim, so it reverts to
`(0, 0)` each time. Detected only by a byte-identical comparison against the stock baseline. Full
write-up on `eval_py_rebuilds_env_cfg_from_hydra_defaults_so_obs_widening_fla.md`.

