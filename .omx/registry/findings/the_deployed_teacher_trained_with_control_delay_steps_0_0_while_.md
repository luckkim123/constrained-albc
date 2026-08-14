---
title: "The deployed teacher trained with control_delay_steps (0,0) while the robot serves observations 1.2 to 4.7 control steps stale, and DORAEMON has no dim to cover it"
tags: ["albc", "deployment", "latency", "staleness", "control-delay", "doraemon", "retrain", "sim2real", "delaybuffer", "decision", "range", "z4", "feasibility-gate", "board-side", "performance-lb"]
created: 2026-08-14T05:32:58.452008
updated: 2026-08-14T10:25:49.391040
sources: ["trpo_iterbudget_s30_260805_012813", "wiki-backlog-20260814", "diagnose-20260814-172325"]
links: ["an_off_doraemon_channel_that_costs_return_stalls_the_curriculum.md", "experiment_idea_latency_transport_delay_dr_sensor_obs_control_ac.md", "uniform_only_dr_full_roster_9_params_doraemon_bypassing_payload.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-apply-before-retrain
blocked-on: "RANGE DECIDED 2026-08-14: (0,1) for the next FROM-SCRATCH teacher round, behind a ~500-iteration feasibility gate. No longer blocked on a user decision. Blocked on that round existing -- R30/R31 already launched 2026-08-10 at (0,0) and must not be changed. The larger half of the fix is board-side and needs no training at all."
---

# The deployed teacher trained with control_delay_steps (0,0) while the robot serves observations 1.2 to 4.7 control steps stale, and DORAEMON has no dim to cover it

[FIELD-MEASURED 2026-08-12, desk audit of the deployed teacher] The deployed policy was trained
with ZERO observation delay, and the real robot feeds it observations that are 1.2 to 4.7 control
steps old. This is outside the training distribution and no DR axis covers it.

WHAT THE TRAINING RUN SAYS. The deployment pack's MANIFEST.json pins the teacher to
`logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813`, and that
run's `params/env.yaml` carries:

    control_delay_steps: !!python/tuple
    - 0
    - 0

An earlier finding recorded this as "unverified, training run directory not found in the
container". That was wrong -- the path is in the manifest and the run is present on
marinelab-isaaclab. The item is now closed, unfavourably.

WHAT THE ROBOT DOES. Measured on agent-jetson 2026-08-12: IMU publishes at 20.3 Hz, joint states
at 10.0 Hz, and the policy runs at 50 Hz (`CONTROL_DT = 0.02`). Zero-order hold therefore serves
the policy joint observations up to 94 ms old (4.7 control steps) and attitude about 1.2 steps
old. A later board session measured the IMU faster (22.6 Hz) but the joint rate unchanged.

WHY DR DOES NOT COVER IT. `control_delay_steps` is not among DORAEMON's `_PARAM_DEFS` dims, so the
curriculum cannot widen or ease it -- see
[[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_]]. The isaaclab DelayBuffer
infrastructure exists but is unused on this line
([[experiment_idea_latency_transport_delay_dr_sensor_obs_control_ac]]), and the one prior attempt
(DelayedPD) failed. So this is not "a knob left at its default"; it is an axis the trained policy
has never seen at all.

WHY IT IS APPLY-BEFORE-RETRAIN AND NOT AN EXPERIMENT. Nothing here needs measuring first -- both
sides are known numbers. The action is to turn the delay on in the next teacher run's config so
the trained distribution contains the staleness the robot actually delivers. Doing it as a
separate probe would spend a training run to re-derive two numbers already in hand.

WHAT NOT TO CONCLUDE. This does not say staleness caused the 2026-08-13 watertank instability.
That session's own paired comparison (50 Hz vs 10 Hz control with per-second joint gain matched)
pointed at delay rather than gain but recorded confidence MEDIUM, because integrator rise time and
GRU history real-time span also differ between those two conditions. Staleness is a training-side
gap to close, not an established root cause.

SOURCE: vault `0_Project/in_progress/albc/.omx/programs/simtoreal-thrusters-live/PLAN.md` section
0i-1 (desk audit) and the backlog table row "deployed teacher control_delay_steps = (0, 0)".
[CONFIDENCE: HIGH for both measured sides; the causal claim is explicitly NOT made]

---

## Update (2026-08-14T07:50:51.283885)

COST CORRECTION 2026-08-14, read against the code. One load-bearing claim on this page is WRONG, and
correcting it makes this blocking item much cheaper to clear than the page implies.

WHAT THE PAGE SAYS: "the isaaclab DelayBuffer infrastructure exists but is unused on this line ... So
this is not 'a knob left at its default'; it is an axis the trained policy has never seen at all."

WHAT THE CODE SAYS: the DelayBuffer is fully wired on this line. In `envs/main/albc_env.py`:
- `_draw_control_delay` (:69-88) allocates `DelayBuffer(history_length=hi, batch_size=num_envs)` and
  draws a PER-ENV integer lag with `torch.randint(low=lo, high=hi+1, ...)`, then `buf.set_time_lag(lag)`.
- It is called during setup at :386-387 from `self.cfg.randomization.control_delay_steps`.
- `_apply_control_delay` (:91-95) applies it on the action path.
- Per-env lags are REDRAWN at reset (:1688-1692), so it behaves like any other per-env randomised axis.
- `control_delay_steps: tuple[int, int] = (0, 0)` (`envs/main/config.py:263`) short-circuits the whole
  pass: `if hi <= 0: return lag, None`.

So the second half of the page's sentence is right (the trained policy has never seen delay) and the
first half is wrong about WHY. It is exactly a knob left at its default. Turning it on is a config
edit, not an implementation project, and the page's own conclusion -- apply it in the next teacher
run's config rather than spending a probe -- stands and gets cheaper.

THREE THINGS TO CARRY WHEN IT IS TURNED ON.

1. IT DELAYS THE ACTION, NOT THE OBSERVATION. For total closed-loop latency the two are equivalent, so
   this is the right knob for the 1.2-4.7 step figure. It cannot represent PER-CHANNEL staleness: the
   robot's attitude is ~1.2 steps stale while joints are ~4.7, and a single scalar action lag collapses
   that to one number. If the per-channel split turns out to matter, this knob is not the instrument.

2. IT SHIFTS THE RNG STREAM. `torch.randint` at :86 is consumed ONLY when `hi > 0`. A run with delay on
   therefore does not share env draws with a `(0, 0)` run, which is the unpairing hazard already on
   record for the eval-side delay injector. Any comparison against an existing `(0, 0)` baseline is
   DISTRIBUTION-LEVEL, not paired -- check `dr_*` array identity before applying paired decision floors.

3. THERE IS A KOOPMAN INTERLOCK. `albc_env.py:446` warns when `koopman_module_path` is set together
   with a nonzero `control_delay_steps`. Read that branch before combining the two.

WHAT REMAINS A DECISION, NOT A FACT. The RANGE to train against. The measured staleness is 1.2 steps
(attitude) to 4.7 steps (joints) at 50 Hz; whether to train `(0, 5)`, `(1, 5)`, a narrower band, or to
put it under DORAEMON at all is a plant choice that forces a retrain and is the owner's call. This page
does not make it. What it now establishes is that the choice is the only remaining work -- no
infrastructure, no probe.

STATUS KEPT at needs-apply-before-retrain: the fact still invalidates any dependent run that claims
deployment realism, and the gate should keep refusing until the range is chosen.

---

## Update (2026-08-14T10:25:49.391040)

## RANGE DECIDED 2026-08-14 (user-approved): (0,1) on the next from-scratch round, gated

### This is not a fresh range question -- (0,3) was already trained and it failed structurally

E1-latdr (`trpo_e1_latdr_260713_124923`, 2026-07-13) ran `control_delay_steps (0,0) -> (0,3)`.
Mean return fell to ~197 against `performance_lb` 250, `doraemon_success_rate` 0.09 against alpha
0.5, DORAEMON sat at mode -2 for the ENTIRE run, `kl_step ~ 0`, and the curriculum CONTRACTED its
own dims (inertia_scale Beta-std 0.111 against the baseline's widened 0.268) while policy entropy
collapsed. Full mechanism:
[[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_]].

### There is no margin to absorb that cost today

Measured on the deployed teacher `trpo_iterbudget_s30_260805_012813`:
`Train/mean_reward` final-50 = 253.35 against `performance_lb` 250.0 (config.py:608), a margin of
1.3%; `DORAEMON/success_rate` final-50 = 0.65 against alpha 0.5. Every DORAEMON dim is already at
Beta(1,1) (std 0.289), i.e. the curriculum is saturated with no easing left to give.

### The Z4 instrument exists and it sizes the per-step cost

`teacher-final-closeout` records "Z4 instrument does not exist" -- that is STALE. `eval.py` carries
`--control_delay` and the sweep was run on the buoyanchor teacher
(`trpo_buoyanchor_s30_260722_134743/sweeps/z4_delay/d{0,1,2,3}`). att_norm ss_error at `none`,
delay-free-trained policy:

| injected delay | 0 | 1 | 2 | 3 |
|:--|--:|--:|--:|--:|
| att ss_error (deg) | 0.630 | 1.474 | 3.239 | 5.604 |
| vs d=0 | -- | 2.3x | 5.1x | 8.9x |

At `hard`, d=2 and d=3 also drop survival to 92.19%. The cost is steeply superlinear in the step
count, which is why the range choice is not a matter of taste. Caveat: the injector draws RNG, so
d>0 does not share env draws with d=0 at soft/medium/hard; `none` is unaffected because its dr_*
are constant.

### The decision

1. **R30/R31 stay (0,0).** They launched 2026-08-10 14:04 and the round's ONLY purpose is config
   identity with the incumbent (user: run it with the same settings as the incumbent, two seeds).
   There was never a retrain this could ride along with -- the one scheduled round left with the
   delay deliberately off.
2. **Next FROM-SCRATCH teacher round: (0,1)**, i.e. 0-20 ms, behind a ~500-iteration feasibility
   gate reading `Train/mean_reward` and `DORAEMON/success_rate`. Proceed to the full run only if
   success stays at or above alpha 0.5 and mean reward at or above 250; otherwise drop the axis.
   Roughly 30 minutes to answer, against 9.6 h (workstation) / 15.3 h (DGX) for the full run.

REJECTED, with reasons: (0,3) and (0,5) -- (0,3) is directly measured to stall and (0,5) is
strictly worse. Adding `control_delay_steps` to DORAEMON `_PARAM_DEFS` -- nine DR params already
bypass DORAEMON as uniform-only
([[uniform_only_dr_full_roster_9_params_doraemon_bypassing_payload_]]), so bypassing IS the
established pattern here; an integer delay also does not fit the Beta-continuous sampler, and a
new dim dilutes the others. Lowering `performance_lb` -- the user's own round design already
rejects it: "a curriculum gate, not a quality dial. Changing it makes this round incomparable to
the incumbent".

### The larger half of the fix is board-side and costs no training at all

This knob delays the ACTION. The measured problem is OBSERVATION staleness, and it is asymmetric:
attitude 1.2 control steps, joints 4.7. One scalar cannot represent that split, and the obs-path
DelayBuffer is still unwired, so **the 4.7-step joint staleness is out of this knob's reach
entirely**. Its actual cause is a board defect -- joint states publish at 10.0 Hz against a 50 Hz
control loop. Raising that publish rate removes the dominant term at zero training cost, and the
user has confirmed the board code is freely modifiable. Do that FIRST; (0,1) then covers what is
left, which is the 1.2-step attitude path, and the sizing matches by construction.

### What would change the range

A feasibility gate at (0,1) that clears comfortably (success well above 0.5) argues for widening to
(0,2) on the round after. A board fix that puts joints at 50 Hz leaves only the 1.2-step attitude
path, which is exactly what (0,1) spans -- in that case (0,1) is not a compromise, it is the right
number.

### Koopman interaction

Not affected today: `koopman_module_path` defaults to `""` (config.py:708), so the guard cannot
fire. Note the guard at `albc_env.py:446` is a `ValueError`, not a warning -- a run carrying both a
Koopman module path and a nonzero delay DIES at construction, by design, because the frozen
operator was fitted on the undelayed action. The Koopman line reopened 2026-08-05 under a paper
objective, so the two must be scheduled separately.

