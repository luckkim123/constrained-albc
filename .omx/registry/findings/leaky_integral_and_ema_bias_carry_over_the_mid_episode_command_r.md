---
title: "Leaky-integral and EMA-bias carry over the mid-episode command resample (unexamined side-effect, harm unproven, A/B design ready)"
tags: ["albc", "envs-main", "command-resample", "leaky-integral", "bias-ema", "carry-over", "observation", "experiment-lead", "sim-to-real-retrain", "constraint-trpo"]
created: 2026-07-05T08:05:40.008780
updated: 2026-07-05T08:05:40.008780
sources: []
links: ["tam_columns_must_match_robot_firmware_esc_channel_order_reorder_.md", "next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md"]
category: reference
confidence: medium
schemaVersion: 1
---

# Leaky-integral and EMA-bias carry over the mid-episode command resample (unexamined side-effect, harm unproven, A/B design ready)

# Leaky-integral & EMA-bias carry over the mid-episode command resample

**Scope**: `envs/main` (Isaac-ConstrainedALBC-TRPO-v0). Verified 2026-07-05 in the command-sampling/resampling review
(`docs/plans/2026-07-05-command-sampling-resampling-review.md` section 2-3).

## The mechanism (VERIFIED-CODE)

At each mid-episode command resample (`albc_env.py:526-534`, fires when `_vel_cmd_step_counter >= vel_cmd_resample_steps`
= 250 steps = 5 s @ 50 Hz), `_sample_velocity_command(resample_ids)` draws a NEW command but does NOT reset two
persistent error-accumulation buffers:

- `_error_integral` (`albc_env.py:312`, 3D roll/pitch/yaw-rate): leaky `mul_(0.99)` + error-gated add (`:1020,1033`),
  clamp 2.0 (`:1038`). Leak half-life ~= 69 steps.
- `_bias_ema` (`albc_env.py:316`, 3D, ungated): EMA `alpha=0.99` updated EVERY step (`:982`).

Both are reset ONLY at episode reset (`:1446-1447`), NOT at resample. So for ~100 steps after a resample the integral
obs and the sustained-offset penalty carry state referenced to the OLD command while the policy tracks the NEW one.

## Verdict: unexamined side-effect, NOT a known bug and NOT documented intent

- **Harm evidence**: NONE. Full search of DIAGNOSIS.md, experiments-archive, wiki, git returned nothing; DIAGNOSIS.md
  flags in-place integral accumulation only as `[unverified-LOW]`.
- **Intent evidence**: the integral obs ITSELF has intent + literature (Hwangbo 2017 leaky-integrator pattern,
  `config.py:342`) and R7/R8 experiment validation. But the specific choice of NOT resetting across resample has NO
  documented intent anywhere. Whether R7/R8 validated under a resampling regime is unknown (git blame lost under rename).
- Self-correcting: leaky+gated buffers converge within ~100 steps (<40% of the 250-step segment), so the contamination
  is easy to miss and the policy trained WITH this behavior may tolerate/exploit it. Reasoning alone cannot settle it --
  needs an A/B.

## A/B experiment (designed, NOT launched)

Design doc: `docs/plans/2026-07-05-carry-over-reset-ab-experiment-design.md`. Single variable
`reset_error_state_on_resample` (off = shipped). B zeros `_error_integral`/`_bias_ema` rows at resample.

- **Placement pitfall (VERIFIED)**: `_sample_velocity_command` is called from TWO sites -- mid-episode resample
  (`:534`, resample_ids) AND episode reset (`:1436`, env_ids, inside `_reset_framework`). Put the reset at the
  mid-episode CALL SITE (`:534` branch), NOT inside the function -- else it fires on episode reset too (already zeroed
  at `:1446-1447`) and couples the toggle to episode-start state, breaking single-variable isolation.
- Metrics: `ss_error`/CV/`ss_jitter`/`n_gt20`, measured at the POST-RESAMPLE transient window (not just aggregate).
  3-way verdict: B-better -> adopt; B-worse -> carry-over is load-bearing, keep + document; no-diff -> neutral, record null.
- **Hard precondition**: requires a post-TAM-reorder (`238932c`) from-scratch checkpoint. Fold into the sim-to-real
  audit retrain batch (run that retrain twice: toggle off = audit baseline, toggle on = this probe). See
  [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]] for why pre-TAM checkpoints are invalid.
  Roster: [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]].

