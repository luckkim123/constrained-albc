---
title: "Real-robot deployment vibration: differential diagnosis by sim-to-real gap channel (which DR/noise probe to reach for)"
tags: ["albc", "envs-main", "sim-to-real", "deployment", "vibration", "jitter", "ood", "domain-randomization", "obs-noise", "latency", "action-clamp", "differential-diagnosis", "smoothness-reward", "experiment-plan-substrate"]
created: 2026-07-09T02:44:18.250138
updated: 2026-07-09T02:44:18.250138
sources: []
links: ["next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md", "action_pipeline_behavior_walk_through_two_clamps_raw_gaussian_vs.md"]
category: reference
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Real-robot deployment vibration: differential diagnosis by sim-to-real gap channel (which DR/noise probe to reach for)

# Real-robot deployment vibration: differential diagnosis by sim-to-real gap channel (which DR/noise probe to reach for)

**Symptom (2026-07-09, user report)**: the deployed policy "shakes a lot" (엄청 흔들림) on the real robot, while
sim playback is quiet. Question raised: is this OOD from sim!=real, and should we add training noise / widen DR?

**Answer in one line**: the `action_smoothness` reward term is NOT at fault (it is textbook velocity+jerk
regularization, `rewards.py:157-161`). Real-robot shake is almost always a vibration the smoothness term *cannot see*
being amplified across the sim-to-real gap. "OOD" is partly right but too vague to act on -- the useful question is
WHICH channel is OOD, because that picks the probe. This card is the symptom->channel->existing-intervention map so a
later batch experiment plan can be built from it. cf [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]] (the retrain roster this feeds).

## Why the reward term can't fix it (mechanism)

`action_smoothness` penalizes `mean((a_t - a_{t-1})^2) + mean((a_t - 2a_{t-1} + a_{t-2})^2)` over all 8 action dims
(2D arm + 6D thruster). It penalizes the action-difference the policy PRODUCES INSIDE SIM. If the real robot shakes, it
is because the policy is REACTING to inputs (or a plant) it never saw in sim -- no reward weight on the sim-side action
difference can suppress an out-of-distribution real-side phenomenon. The fix is input-distribution alignment (DR /
noise), not a heavier reward term. One structural exception (channel C below) is a reward BLIND SPOT, not an OOD issue,
so DR does not fix it either.

## Four hypotheses (differential diagnosis, NOT yet confirmed -- needs real logs)

Per `.claude/rules/03` (no premature assertion): this is a diagnosis STRUCTURE, do not declare a winner without data.

### Channel A -- observation-noise OOD  (leading suspect, code-grounded)
Smoothness only sees action diffs; for the policy to emit smooth actions its INPUT (obs) must be smooth. If sim
IMU/attitude obs noise is smaller than real, or the *structure* differs (sim=Gaussian, real=drift+spike+quantization),
the policy chases the real obs high-frequency content and jitters the action. This is exactly OOD.
**Key fact**: the obs-noise DORAEMON curriculum (`obs-noise-dr`) is IMPLEMENTED but NOT yet trained/deployed
(memory `project-obs-noise-doraemon-260708`), so the currently deployed policy was likely under-trained for obs noise.
=> intervention already exists, just unshipped. This is suspect #1.

### Channel B -- actuator / latency dynamics gap  (leading suspect, in-progress branch)
Sim thruster models only a 1st-order lag (`time_constant_scale`); there is NO send/receive latency DR (confirmed this
session's Explore sweep; the `exp/latency-dr` branch is adding exactly that). Real hardware has comms+controller delay,
so a policy's action for "current attitude" applies tens of ms late. A delayed plant + a policy trained delay-free is a
CLASSIC limit-cycle/vibration cause (delay eats phase margin). If the THRUSTER shakes, this is prime.

### Channel C -- clamp-saturation vibration  (smoothness BLIND SPOT, not OOD)
`_actions` is stored AFTER `clamp(-1,1)` (`albc_env.py:509`). If the policy oscillates OUTSIDE the +-1 boundary, sim
squashes both to +-1 so `da~=0` and smoothness thinks it is quiet. In reality that oscillation leaks straight to the
real actuator. If the training clamp-saturation rate was high, this is a hidden cause -- and DR does NOT fix it because
it is a reward design blind spot, not a distribution shift. cf [[action_pipeline_behavior_walk_through_two_clamps_raw_gaussian_vs]] (two-clamp pipeline).

### Channel D -- control-rate / decimation mismatch
Sim is fixed 50 Hz (step_dt=0.02). If the real control loop is not exactly 50 Hz or has jitter, the timescale over
which `da` was penalized diverges from the real applied timescale, breaking the smoothness assumption. Partly overlaps
the audit's Group A control-timing item ([[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]]).

## Diagnosis protocol (evidence, not guessing) -- classify the shake in ~3 minutes

| Check | How | What it discriminates |
|:---|:---|:---|
| vibration frequency | FFT of real thruster command time series | high-freq (>10 Hz)=obs-noise/latency; low-freq limit cycle=latency/control |
| sim clamp-saturation rate | training log `\|action\|>0.99` fraction | high => channel C (blind spot) |
| inject real-level obs noise in sim | add real-scale noise to obs at play, does it shake | shakes => channel A confirmed |
| inject latency in sim | turn on delay via `exp/latency-dr` at play | shakes => channel B confirmed |

**First triage question**: is the ARM (2D, slow dynamics) shaking or the THRUSTER (6D, delay/noise sensitive)? This
alone narrows the candidate set sharply before any FFT.

## Sim-to-real reduction options this maps to (for the batch plan)

The user's instinct ("add training noise / widen DR") is right for channels A/B, wrong for C:
- **Channel A** => ship the obs-noise DORAEMON curriculum (already built) + widen obs-noise DR range.
- **Channel B** => finish + train the latency DR (`exp/latency-dr`), add comms-delay band.
- **Channel C** => NOT a DR fix. Either widen action clamp headroom, add a saturation-margin penalty, or re-check why
  the policy sits on the +-1 boundary (over-aggressive gains). Widening DR here would waste budget on the wrong lever.
- **Channel D** => control-timing alignment (audit Group A), not a noise/DR knob.

So "widen DR / add noise" is 2 of the 4 real levers -- the card exists so the batch plan does not reflexively answer
every sim-to-real symptom with "more DR" when a reward blind spot (C) or a timing fix (D) is the actual cause.

## Status / unverified
- All four are HYPOTHESES; none confirmed against real logs (none available this session).
- Which channel to probe FIRST is an exp-design decision (deferred by user: "실험 설계까지는 괜찮고"). This card is
  the knowledge substrate for that later batch plan, not the plan itself.
- Companion intervention cards already exist for A (obs-noise-dr, memory), B (`exp/latency-dr`), C (action-pipeline
  clamp card), D (audit Group A). This card is the INDEX that ties the real-shake symptom to them.

