---
title: "DORAEMON becomes feasibility-limited at the ceiling: the kl_ub 0.06 arm reached 98.6 percent of full DR then contracted because mean_reward sits below performance_lb"
tags: ["albc", "doraemon", "curriculum", "performance_lb", "feasibility", "kl_ub", "saturation", "teacher", "arm-w", "performance-lb", "kl-ub", "limit-cycle", "closed"]
created: 2026-08-09T18:10:10.947879
updated: 2026-08-14T07:44:36.077029
sources: ["wiki-backlog-20260814"]
links: ["doraemon_is_trust_region_limited_not_feasibility_limited_kl_step.md", "sigma_decay_under_an_expanding_dr_curriculum_literature_verdict.md", "where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
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

---

## Update (2026-08-14T07:44:36.077029)

CLOSED 2026-08-14 on the COMPLETED run. This lead was written at iteration 11,294 with two readings
left open and an explicit instruction ("report at 14,750 / 17,000, do not kill"). The run finished at
model_19999 on 2026-08-10 and the data settles it: READING 2 IS REFUTED, READING 1 SURVIVES.

Reading 2 was "Arm W has simply had ~500 iterations near full width against the incumbent's 2,250, and
its remaining ~8,700 iterations may lift the return over the floor and re-lock the box." It got all
8,700 of them. Neither half happened.

THE RETURN NEVER CROSSES THE FLOOR. `Train/mean_reward` per 1000-iteration bucket:

| iters | mean_reward | | iters | mean_reward |
|:--|--:|:--|:--|--:|
| 7000-7999  | 253.18 | | 14000-14999 | 243.02 |
| 8000-8999  | 248.71 | | 15000-15999 | 242.81 |
| 9000-9999  | 244.69 | | 16000-16999 | 242.61 |
| 10000-10999 | 239.92 | | 17000-17999 | 242.27 |
| 11000-11999 | 241.65 | | 18000-18999 | 242.04 |
| 12000-12999 | 241.53 | | 19000-19999 | **242.34** |
| 13000-13999 | 241.13 | | `performance_lb` | 250.0 |

It last cleared 250.0 in the 7000-7999 bucket and has been flat at 241-243 for the final 9,000
iterations. This is a PLATEAU, not a slow climb: the slope over 11k->19k is +8.65e-05 reward/iter, so
closing the 7.66-point gap would take **88,470 further iterations -- 4.4x the entire 20k run already
spent**. By this repo's slope rule (>5x current training time = structurally hopeless) it is not
merely unlikely, it is off the schedule entirely.

THE CURRICULUM NEVER RE-LOCKS. Summed per-dim KL to uniform, computed from
`curriculum_trajectory.json` (the five rows in the table above reproduce EXACTLY -- 0.8238 / 0.5888 /
0.4245 / 0.5236 / 0.6481 with sat 0/0/2/1/1 -- so the instrument is validated before the new reading):
after the turnaround it enters a BOUNDED OSCILLATION in the 0.20-0.73 band for 8,700 iterations. Best
approach is 0.1958 at 17,750 (closer than the 0.4245 that triggered this page) and saturated dims peak
at 5/21 at 15,750, never approaching the incumbent's 21/21. The run ENDS CONTRACTING: 0.2958 at 18,000
-> 0.7314 at 19,750.

THE GATE IS THE RETURN FLOOR, CONFIRMED OVER THE FULL RUN. `DORAEMON/success_rate` is flat at
0.462-0.484 across every bucket from 10,000 to the end while the curriculum oscillates, so the success
gate is not what moves. This page's original units argument now has 9,000 iterations of support.

WHAT THIS IS, THEN. Not a failure to converge -- a stable limit cycle at the feasibility edge, which
is DESIGNED behaviour: see [[sigma_decay_under_an_expanding_dr_curriculum_literature_verdict_]] on the
DORAEMON authors' Eq. 6 backup optimisation, where widen-violate-contract at the ceiling is the
intended dynamics. Arm W is not stuck mid-transient; it is parked in the cycle permanently.

THE PLANNING CONSEQUENCE STANDS AND HARDENS. "Iterations to saturation" cannot be budgeted from
`kl_ub` alone. A low-`kl_ub` arm may never saturate at all, and this run is the existence proof --
20,000 iterations, 98.6% of the way, and it ended further out than its own best.

WHAT THIS DOES NOT CLOSE. WHERE the 8 points of return are lost is still open and still the right next
probe -- see [[where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu]], whose premise
(241.69 against 250.0) is confirmed here at 241.63 final-200 / 242.34 final-1000.

EVIDENCE: `.omx/scratch/wiki-backlog-20260814/py/tb_traj.py` over the run's single event file, 1000-iter
buckets; cross-checked on a different code path with `.omx/profile/tb_final.py --window 200`
(mean_reward 241.632, success_rate 0.445). Curriculum from `curriculum_trajectory.json`, 80 entries,
KL(Beta(a,b)||Beta(1,1)) with a pure-math digamma (system scipy is broken by numpy 2.5.1 here).

