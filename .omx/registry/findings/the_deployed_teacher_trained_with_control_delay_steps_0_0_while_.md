---
title: "The deployed teacher trained with control_delay_steps (0,0) while the robot serves observations 1.2 to 4.7 control steps stale, and DORAEMON has no dim to cover it"
tags: ["albc", "deployment", "latency", "staleness", "control-delay", "doraemon", "retrain", "sim2real"]
created: 2026-08-14T05:32:58.452008
updated: 2026-08-14T05:32:58.452008
sources: ["trpo_iterbudget_s30_260805_012813"]
links: ["an_off_doraemon_channel_that_costs_return_stalls_the_curriculum.md", "experiment_idea_latency_transport_delay_dr_sensor_obs_control_ac.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-apply-before-retrain
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

