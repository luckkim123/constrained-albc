---
title: "Halving kl_ub cost 1.42x iterations to saturation, not the 2x the trust-region model predicts -- and trajectory retention blocks closing the confound"
tags: ["albc", "doraemon", "kl_ub", "curriculum", "saturation", "expansion-budget", "teacher", "data-retention", "superseded"]
created: 2026-08-09T16:57:23.834949
updated: 2026-08-09T18:10:47.542700
sources: []
links: ["doraemon_is_trust_region_limited_not_feasibility_limited_kl_step.md", "doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_.md"]
category: debugging
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# Halving kl_ub cost 1.42x iterations to saturation, not the 2x the trust-region model predicts -- and trajectory retention blocks closing the confound

The wiki records DR expansion as trust-region-limited, with reach ~ `n_updates x kl_ub`
([[doraemon_is_trust_region_limited_not_feasibility_limited_kl_step]], confidence high). That model
predicts halving `kl_ub` doubles the iterations to saturation. The first run to actually vary
`kl_ub` alone is coming in at **1.42x, not 2x** -- close enough to matter, not yet a refutation.

## The measurement

| run | `kl_ub` | `step_interval` | `performance_lb` | saturated at |
|:--|:--|:--|:--|:--|
| `trpo_iterbudget_s30_260805_012813` | 0.12 | 250 | 250.0 | iteration **7748** (21/21 dims) |
| `trpo_rampw_kl006_s30_260809_161913` | 0.06 | 250 | 250.0 | **~11,000 projected** |

7748 = 31 update slots; ~11,000 = ~44. Ratio 1.42. Under `n_updates x kl_ub` it should be ~62 slots.

## Three reasons this is not yet a test

1. **The 11,000 is extrapolated, not observed.** At iteration 10,000 Arm W has 1.1715 KL left and is
   decelerating (-0.4402/step); the incumbent covered its last 1.1552 in 4 steps. Replace this with
   the measured number once Arm W saturates.
2. **Arm W wasted update slots the incumbent may not have.** Of its 41 records, 4 moved BACKWARD
   (the box contracts while `success_rate` is under `performance_lb`, iterations ~500-1250) and 3 were
   flat (one of them the `Singular matrix` rejection at 2000). Seven slots of 41 did not advance.
   Whether the incumbent had a comparable early-contraction phase is **unknowable**: see below.
3. **Two different KL scales are in play.** `kl_ub` is DORAEMON's per-step trust region (0.12); the
   distance measured from `curriculum_trajectory.json` is the summed per-dim KL to uniform (31.2855
   at run start). They differ by roughly 8x and are not interchangeable. The ITERATION ratio above is
   metric-independent and safe; any budget arithmetic mixing the two is not.

## Blocking data-hygiene problem: trajectory retention is inconsistent

`curriculum_trajectory.json` does not retain the same slice across runs, which silently caps exactly
this comparison:

| run | records | iterations covered |
|:--|:--|:--|
| `trpo_rampw_kl006_s30` | 41 | 0..10000 (complete) |
| `trpo_iterbudget_s30` | 20 | 5248..9998 (early history GONE) |
| `trpo_eint_s30_260727_160913` | 10 | 0..2250 (stops early despite a 5000-iteration run) |

So the incumbent's early contraction cannot be counted, and confound 2 cannot be closed from
existing artifacts.

## What would settle it

Arm W's measured saturation iteration (free, ~1 h away), plus one `kl_ub` 0.12 run whose FULL
trajectory is retained, so forward/backward/flat slots can be counted on both sides. Until then,
treat "halving `kl_ub` doubles time-to-saturation" as an upper bound rather than an estimate --
budgeting a low-`kl_ub` arm at 2x may over-provision by ~40%.

---

## Update (2026-08-09T18:10:47.542700)

**SUPERSEDED AND WRONG. Do not use the number in this title.**

Read [[doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_]] instead.

The "1.42x" was computed from a PROJECTED saturation of `trpo_rampw_kl006_s30_260809_161913` at
iteration ~11,000, extrapolated from a decelerating tail. **That saturation never happened.** The
run reached its closest approach at iteration 10,750 (0.4245 summed KL to uniform, 2/21 dims at
Beta(1,1)) and then reversed, contracting at +0.0991 and +0.1245 over the next two updates, because
`Train/mean_reward` (239.5-242.3) sits below `performance_lb` (250.0).

So there is no measured "iterations to saturation" for the `kl_ub` 0.06 arm, and no ratio against
the incumbent's 7748. The comparison this page proposed cannot be made from these two runs.

The one piece worth keeping is the data-hygiene note: `curriculum_trajectory.json` retention is
inconsistent across runs -- `trpo_rampw_kl006_s30` kept all 41 records (iterations 0..10000),
`trpo_iterbudget_s30` only 20 (5248..9998), `trpo_eint_s30_260727_160913` only 10 (0..2250) despite
running 5000 iterations. Any cross-run curriculum comparison is silently capped by whichever slice
each run happened to keep.

This page is left in place only because deletion is human-gated (`omx wiki gc`). It is a candidate
for the next gc pass.
