---
title: "The pre-registered per-env paired comparison cannot be executed: _per_env_ss_stats hides its vector and a docstring-faithful reimplementation misses the published scalar by up to 3.6x the floor"
tags: ["engine-gap", "per-env", "pre-registered-rule", "m3", "instrument", "recompute-metrics", "resolved", "engine-gap-closed"]
created: 2026-08-15T04:17:20.590696
updated: 2026-08-15T12:14:10.239304
sources: ["diagnose-20260814-235911"]
links: ["where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu.md", "eval_py_static_ood_appends_a_fifth_dr_level_and_unpairs_every_cr.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "CLOSED 2026-08-15: the vector is exposed. _per_env_ss_vectors extracted, _per_env_ss_stats delegates to it, _compute_enhanced_metrics gained with_per_env=False (summary.json byte-identical by default). Half of M3's blocker set is therefore gone; M3's other gap (no per-env episode-return channel in eval.py) is untouched."
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

---

## Update (2026-08-15T12:14:10.239304)

## RESOLVED 2026-08-15 — the vector is exposed, and the clause has been executed

The block described above is closed. What changed, in `_analyze/recompute_metrics.py`:

- `_per_env_ss_vectors(actual, alive, cur_tgt)` extracted, returning the two UNREDUCED (n_env,)
  arrays.
- `_per_env_ss_stats` now delegates to it instead of computing its own copy, so the scalar and the
  vector cannot drift. The attitude-norm block, which had its own inline duplicate of the same
  masking/window logic, was pointed at the shared helper too.
- `_compute_enhanced_metrics(..., with_per_env=False)` — off by default so `summary.json` stays
  byte-identical for every existing caller; on, it adds a top-level `per_env` dict of per-axis
  (n_env,) lists, averaged across segments exactly as the scalar is.

VALIDATED, and this is the check that makes the vector safe to use: on the three real teacher evals
the across-env mean of the exposed vector reproduces the published `ss_error` to machine epsilon
(0.00e+00 to 1.11e-16, on `att_norm` and `roll`, at `none` and `hard`). Tests added in
`tests/test_recompute_metrics.py`: one asserting the scalars are exactly the reduction of the
vectors, one asserting `mean(per_env[ax]) == out[ax]["ss_error"]` on a fixture with a distinct
offset per env, one asserting the default output has no `per_env` key. The reproduce-the-scalar test
was mutation-checked -- flipping the aggregation axis makes it fail.

WHY THE REIMPLEMENTATION MISSED, now that the real code is visible. Three things the docstring does
not say: segments come from `_find_segments`, not from a naive diff on the target;
`_classify_segment` and `_is_target_zero` DROP several segments that a hand version keeps; and the
last-50% window is taken per segment with the cross-segment average applied afterwards, not over a
concatenation. Each is individually enough to move the answer by more than the decision floor.

## What the executed clause immediately showed

Running the comparison the round actually asked for changed how much weight its `hard` cells can
carry. Per-env paired differences on `att_norm ss_error`, 64 envs:

| level | comparison | paired mean (deg) | SE | mean/SE | envs better |
|:--|:--|--:|--:|--:|:--|
| hard | R30 - incumbent | +0.1757 | 0.0933 | 1.9 | 16/64 |
| hard | R31 - incumbent | +0.0442 | 0.1088 | 0.4 | 37/64 |
| none | R30 - incumbent | +0.1448 | 0.0104 | 13.9 | 4/64 |
| none | R31 - R30 | -0.1708 | 0.0048 | 35.3 | 64/64 |

The fixed 0.10 deg floor calls R30 - incumbent decision-grade at BOTH levels because the deltas are
nearly the same size. The paired test says they are not the same result at all: 13.9 standard errors
at `none` against 1.9 at `hard`, because per-env spread at `hard` is NINE TIMES larger (SE 0.0933
against 0.0104). **A fixed floor cannot see heteroscedasticity across DR levels; the paired
difference can.** That is the concrete argument for the pre-registered clause, and it is now cheap
to honour. Detail: analysis diagnose-20260814-235911.

