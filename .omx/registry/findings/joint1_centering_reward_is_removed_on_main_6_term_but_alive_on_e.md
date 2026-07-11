---
title: "joint1_centering reward is REMOVED on main (6-term) but ALIVE on exp/latency-dr (7-term); reward.md doc is main-stale"
tags: ["joint1", "reward", "branch-divergence", "reward-md-stale", "line-cite-drift", "latency-dr", "envs-main"]
created: 2026-07-11T06:40:33.149894
updated: 2026-07-11T06:40:33.149894
sources: []
links: ["joint1_anti_drift_constrain_the_command_cumulative_arm_b_not_the.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# joint1_centering reward is REMOVED on main (6-term) but ALIVE on exp/latency-dr (7-term); reward.md doc is main-stale

joint1_centering reward is REMOVED on main (6-term) but ALIVE on exp/latency-dr (7-term); reward.md doc is main-stale.

Code-verified 2026-07-11 (session on branch exp/latency-dr). The reward-side `joint1_centering_penalty`
term has DIVERGED between branches — do not trust reward.md's term count without checking the branch you are on.

## The divergence (verified)

| Branch | `joint1_centering_penalty` reward term | `_NAMES` (rewards.py) |
|:---|:---|:---|
| `main` | REMOVED | `["att_rp", "yaw_vel", "torque", "thruster", "smoothness", "bias"]` (6 terms) |
| `exp/latency-dr` | STILL PRESENT | `[..., "bias", "joint1_center"]` (7 terms) |

- `exp/latency-dr` is 5 commits BEHIND main / 8 ahead (`git rev-list --left-right --count main...exp/latency-dr` = `5  8`),
  and does not contain the removal commit. So the term is live here purely because this branch predates the main merge.
- The removal on main was this project's "reward/constraint joint1 정리" work (task 4 = drop reward-side
  `joint1_centering_penalty`, RewardManager 7→6 terms; task 5 = also drop constraint arm A, leaving only
  arm B `joint1_cumulative_cost` as the joint1 anti-drift lever). Merged to main, unpushed as of 2026-07-09.

## reward.md is stale against main

`constrained-albc/docs/reference/reward.md` is written for the 7-term (pre-removal) reward and still
documents `joint1_center` as term #7 (§3, §5.5). It matches `exp/latency-dr` but is STALE vs main (6-term).
Anyone reading reward.md on/for main must mentally drop the joint1_center term.

## reward.md line-cite drift (independent trap, verified 2026-07-11)

Beyond the term-count staleness, reward.md's LINE numbers no longer match the code (the file shifted after
the doc was written). Confirmed mismatches while answering the bias-reward question:
- bias `k_bias=-2.0` override: doc says `config.py:429`, ACTUAL `config.py:453`.
- bias-EMA buffer update block: doc says `albc_env.py:1042-1052`, ACTUAL `albc_env.py:1133-1143`.
- `_get_rewards` entry: doc's §1 flow cites `albc_env.py:1009`, ACTUAL `def _get_rewards` at `albc_env.py:1100`.
The MECHANISM prose in reward.md is accurate; only the line anchors are stale. Re-verify any line cite before
using it, and fix these anchors if/when reward.md is next revised.

## What joint1_centering reward WAS (the removed term, for reference)

`r_jc = wrap(theta1)^2`, `wrap = atan2(sin theta1, cos theta1)` (rewards.py:184-199 on exp/latency-dr).
Reads only joint1 (`_albc_joint_ids[0]`). Joint1 is a continuous-rotation motor with no PhysX position limit,
driven by a pure delta-integrator — nothing pulls it to nominal, so sim-to-real micro-bias would drift it
monotonically. This term supplied the missing restoring gradient. wrap() so a full revolution (2*pi ~ 0) is
NOT penalized as a large error. OFF by default (`k_joint1_center=0.0`) and never overridden, yet the
atan2/sin/cos EXECUTED every step and logged `Reward/joint1_center = 0.0` (reads as measured-zero, not disabled).
Removed on main because joint1 anti-drift was consolidated onto the constraint-side lever
(`joint1_constraint_arm`, cost-critic channel), see [[joint1_anti_drift_constrain_the_command_cumulative_arm_b_not_the]].

## Practical warning

If work on `exp/latency-dr` (latency DR investigation) is later merged to main, expect a joint1-related merge
conflict or regression: this branch still carries the 7-term reward + `k_joint1_center` field that main deleted.
Rebase/merge carefully so the term is not silently re-introduced.

