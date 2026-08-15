---
title: "The pre-registered per-env paired comparison cannot be executed: _per_env_ss_stats hides its vector and a docstring-faithful reimplementation misses the published scalar by up to 3.6x the floor"
tags: ["engine-gap", "per-env", "pre-registered-rule", "m3", "instrument", "recompute-metrics"]
created: 2026-08-15T04:17:20.590696
updated: 2026-08-15T04:17:20.590696
sources: ["diagnose-20260814-235911"]
links: ["where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu.md", "eval_py_static_ood_appends_a_fifth_dr_level_and_unpairs_every_cr.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "The same engine-gap M3 is blocked on: expose the per-env vector from _per_env_ss_stats (recompute_metrics.py:234) instead of returning four aggregate scalars. Until then any protocol clause requiring per-env paired differences is unexecutable."
---

# The pre-registered per-env paired comparison cannot be executed: _per_env_ss_stats hides its vector and a docstring-faithful reimplementation misses the published scalar by up to 3.6x the floor

teacher-final-replicate's pre-registered rule requires "per-env paired differences, not group means".
That clause cannot be honoured with the shipped instrument, and this page records the attempt so the
next session does not repeat it.

WHY IT IS BLOCKED. `_per_env_ss_stats` (`constrained_albc/analysis/_analyze/recompute_metrics.py:234`)
computes the per-env steady-state array internally and returns only four aggregates -- ss_err_mean,
ss_err_std, ss_jit_mean, ss_jit_std, each already reduced across envs. Nothing downstream can recover
the vector. This is one of the two engine-gaps
[[where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu]] is blocked on.

WHY REIMPLEMENTING FROM THE DOCSTRING DOES NOT RESCUE IT, measured rather than assumed. The docstring
is explicit -- "SS error per env: mean |actual - target| over last 50% of segment" -- so a
reimplementation looks safe. It is not. Segmenting on target changes, masking with `terminated`,
taking the last 50% of each segment and averaging across segments reproduces the published `ss_error`
to nowhere near tolerance at `hard`:

| run | axis | reimplementation | published `ss_error` | error |
|:--|:--|--:|--:|--:|
| incumbent | roll | 0.3069 | 0.6718 | -0.3648 |
| incumbent | pitch | 0.1911 | 0.3376 | -0.1465 |
| R30 | roll | 0.5436 | 0.8577 | -0.3140 |
| R31 | roll | 0.4963 | 0.7022 | -0.2059 |

The gap runs from 0.5x to 3.6x the 0.10 deg decision floor, so a per-env analysis built on it would
have produced confident, floor-scale, wrong deltas. The validation that caught it is the cheap one and
should be mandatory for any reimplementation: **reproduce the published aggregate from your own per-env
vector before using the vector for anything.**

WHAT TO DO INSTEAD, until the gap is closed: state group means with the pairing gate confirmed
(elementwise-identical `dr_*`) and declare the per-env clause unmet, rather than substituting an
unvalidated per-env metric. Related instrument lesson:
[[eval_py_static_ood_appends_a_fifth_dr_level_and_unpairs_every_cr]].

