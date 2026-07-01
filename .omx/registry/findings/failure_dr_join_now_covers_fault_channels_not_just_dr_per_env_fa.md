---
title: "failure_dr join now covers fault_ channels, not just dr_ (per-env failure<->FAULT correlation enabled)"
tags: ["fault-injection", "failure-dr", "eval-analysis", "heavy-tail", "ftc", "eval-adapter", "omx-report", "prefix-generalization"]
created: 2026-06-14T06:38:50.635559
updated: 2026-06-14T06:38:50.635559
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
---

# failure_dr join now covers fault_ channels, not just dr_ (per-env failure<->FAULT correlation enabled)

# failure_dr join now covers fault_ channels, not just dr_ (per-env failure<->FAULT correlation enabled)

The per-env worst-env<->value join in `_analyze/failure_dr.py` was generalized so it
analyzes injected `fault_<name>[N]` channels alongside the `dr_<name>[N]` domain-
randomization channels. Code-changed 2026-06-14 on branch `exp/fault-injection`
(commit `105818e`); this is the analysis half of the fault-injection infrastructure
(the injection half records fault tensors into the eval npz). Until this change the
fault data was present in the npz but invisible to analysis -- the join hardcoded the
`dr_` prefix in three places.

WHAT WAS BLIND (the gap): `failure_dr.py:113` hardcoded `key.startswith("dr_")`, the
plot label strip used `replace("dr_","")`, and the `eval_dr.py` skip-guard used
`startswith("dr_")`. So even when `eval.py --fault` wrote `fault_thruster_{0..5}`,
`fault_sensor_noise`, `fault_joint` into `data_<level>.npz`, the per-env heavy-tail /
failure-correlation analysis never looked at them. Per-env heavy-tail analysis along
the FAULT axis -- the premise of the fault-tolerant-control study -- was impossible.

WHAT CHANGED:
- `join_failure_dr(data, axis, k, prefixes=("dr_","fault_"))`: prefix is now a
  parameter. Each prefix is ranked into a SEPARATE list keyed `<prefix sans _>_ranking`
  -> the result carries both `dr_ranking` AND `fault_ranking`. Separation is deliberate:
  a fault correlation must not be out-ranked and hidden by a dr channel when they share
  one sorted list. Extracted a prefix-agnostic `_rank_by_prefix()` helper.
- `plot_failure_dr`: renders rows = DR levels x cols = (DR, FAULT); an empty column is
  dropped, so a dr-only run renders identically to before. Label strip generalized to
  `_strip_value_prefix()` (handles dr_ and fault_).
- `eval_dr.py` (`_ed_run_failure_dr`): skip-guard is now `startswith(("dr_","fault_"))`
  and the console report prints a "binding FAULT" section beside "binding DR".
- `.omx/profile/eval_adapter.py`: new `analyze_failure_dr()` (PURE delegation to the
  engine's `analyze_failure_dr_levels`, no metric math in the adapter -- the same drift-
  prevention invariant as `analyze_eval`/`analyze_segmented`) + a `failure-dr` CLI
  subcommand emitting JSON, so omx report can fold the fault ranking.

HOW TO USE (omx report fault ranking):
`python3 .omx/profile/eval_adapter.py failure-dr <eval_dir> --levels none soft medium hard --axis roll`
-> JSON `{levels: {<lvl>: {dr_ranking:[...], fault_ranking:[...]}}}`. A dead thruster
shows up as the top `fault_ranking` entry with a NEGATIVE correlation (low health <->
worst tracking).

BACKWARD-COMPAT INVARIANT (important when reasoning about old dr-only runs): for an npz
with no `fault_` keys the `dr_ranking` output is byte-identical to before -- same
records, same `axis/k/n_failing` scalars, only an empty `fault_ranking: []` is added.
The OLD dr loop body is preserved verbatim inside `_rank_by_prefix`. So any prior
failure_dr analysis on a dr-only eval is unaffected; do not re-run old runs expecting a
different dr ranking.

VERIFICATION: 31 sim-free tests (19 `tests/test_failure_dr.py` + 12
`tests/test_eval_adapter.py`); independent code review confirmed dr byte-identity via
git-show diff. The single requirement to surface a fault ranking is that the eval was
run with `--fault` (else `fault_ranking` is empty -- not an error, just no fault data).

