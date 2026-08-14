---
title: "DORAEMON becomes feasibility-limited at the ceiling: the kl_ub 0.06 arm reached 98.6 percent of full DR then contracted because mean_reward sits below performance_lb"
tags: ["albc", "doraemon", "curriculum", "performance_lb", "feasibility", "kl_ub", "saturation", "teacher", "arm-w"]
created: 2026-08-09T18:10:10.947879
updated: 2026-08-09T18:10:10.947879
sources: []
links: ["doraemon_is_trust_region_limited_not_feasibility_limited_kl_step.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
---

# DORAEMON becomes feasibility-limited at the ceiling: the kl_ub 0.06 arm reached 98.6 percent of full DR then contracted because mean_reward sits below performance_lb

`trpo_rampw_kl006_s30_260809_161913` (`kl_ub` 0.06) did **not** saturate. It approached the ceiling,
touched 2/21 dims at Beta(1,1), and then **turned around and began contracting** -- because the
policy's return fell below `performance_lb`. The wiki's standing claim that DORAEMON is
trust-region-limited and "not being held back by the feasibility gate"
([[doraemon_is_trust_region_limited_not_feasibility_limited_kl_step]]) was measured on runs whose
return stayed above the floor. **Which constraint binds is not a property of DORAEMON; it is a
property of whether the policy can still earn `performance_lb` at the current box width.**

## The turnaround, measured

| iteration | summed per-dim KL to uniform | saturated dims | delta |
|---:|---:|---:|---:|
| 10250 | 0.8238 | 0/21 | -0.3476 |
| 10500 | 0.5888 | 0/21 | -0.2350 |
| **10750** | **0.4245** | **2/21** | -0.1643 |
| 11000 | 0.5236 | 1/21 | **+0.0991** |
| 11250 | 0.6481 | 1/21 | **+0.1245** |

Closest approach is 0.4245 of an initial 31.2855 -- about 98.6% of the way to full DR -- then back out.

## The mechanism, measured

`performance_lb` = 250.0 on both runs. `Train/mean_reward` decides it:

| | `trpo_iterbudget_s30` (`kl_ub` 0.12) | `trpo_rampw_kl006_s30` (`kl_ub` 0.06) |
|:--|:--|:--|
| reward near the ceiling | 262.6 (6500-6750) -> 254.6 -> 254.1 -> **252.9** (9750-9998) | **239.5** (10500-10750) -> **242.3** (11150-11290) |
| vs `performance_lb` 250.0 | always ABOVE | always BELOW |
| `DORAEMON/success_rate` | 0.78 -> 0.65 | 0.49 |
| `DORAEMON/entropy_before` at ceiling | -18.2007, frozen from 8000 on | -18.67 best, drifting |
| outcome | **locked 21/21 from iteration 7748** | oscillates at the boundary |

The incumbent cleared the floor by 2.9-12.6 points and kept its box; Arm W misses it by 8-10 and gets
pulled back. `success_rate` is stable (~0.49) across the turnaround, so the gate driving this is the
RETURN floor, not the success gate -- the units confirm it (`performance_lb` 250.0 is on the reward
scale, not the 0-1 success scale).

## Do not read this as "the kl_ub 0.06 arm failed"

Two readings survive the data and cannot be separated at iteration 11,294:
1. The slower curriculum yields a genuinely weaker policy at matched DR width.
2. Arm W has simply had ~500 iterations near full width against the incumbent's 2,250, and its
   remaining ~8,700 iterations may lift the return over the floor and re-lock the box.

Reading 2 is live and cheap to settle -- watch whether `Train/mean_reward` crosses 250.0 and the
curriculum resumes closing. The run gate stands: report at 14,750 / 17,000, **do not kill**.

## Consequence for planning

At this plant, full DR sits *right at* the feasibility edge for a seed-30 policy: the run that made
it cleared the floor by ~3 points at the end. Any arm can therefore stall at the boundary, and
"iterations to saturation" is not a schedule you can budget from `kl_ub` alone -- it depends on a
reward that is not under the curriculum's control. Budgeting a low-`kl_ub` arm as "2x the
iterations" assumes a saturation that may never arrive.

## Supersedes

This page replaces an earlier page of mine that reported "halving kl_ub cost 1.42x iterations to
saturation". That number was computed from a PROJECTED Arm W saturation at ~11,000 which did not
happen. The projection was extrapolated from a decelerating tail; the tail reversed instead.
