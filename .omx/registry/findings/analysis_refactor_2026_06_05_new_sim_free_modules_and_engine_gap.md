---
title: "analysis refactor 2026-06-05 — new sim-free modules and engine-gap status"
tags: ["engine", "engine-gap", "analysis", "refactor", "sim-free", "omx-callable"]
created: 2026-06-05T06:43:49.886174
updated: 2026-06-05T06:43:49.886174
sources: ["exp/analysis-refactor", "tasks-1-10", "2026-06-05"]
links: ["analysis_engine_map_what_is_grow_able_vs_off_limits.md"]
category: reference
confidence: high
schemaVersion: 1
---

# analysis refactor 2026-06-05 — new sim-free modules and engine-gap status

Branch exp/analysis-refactor (tasks 1-6,8-10 done 2026-06-05; task 7 deferred, needs GPU) extracted sim-free code from eval.py and recompute.py into importable plain-python3 modules. eval.py shrank 3414 -> 1885 lines (-45%). This page updates [[analysis-engine-map-what-is-grow-able-vs-off-limits]] with the new module inventory.

## New GROW-ABLE modules (sim-free, omx exp-analyze callable)

All importable with `python3 -c "import sys; sys.path.insert(0,'constrained_albc/analysis'); import <module>"` — no Isaac Sim required.

- eval_plots.py : ALL plotting functions extracted from eval.py (1204 lines, 24 plot funcs). Mirrors _eval_dr/ pattern. omx can regenerate plots from existing npz without running eval.py. (_plot_dr_distributions stays in eval.py: it instantiates HardDomainRandomizationCfg -> sim-bound.)
- eval_serialize.py : npz/.mat serialization (write_eval_npz writes data_<level>.npz; _build_mat_meta + _MAT_VAR_DESC build the .mat metadata struct for scipy.io.savemat). NOT summary.json. Extracted from eval.py. omx can re-export results to .npz/.mat.
- dr_config.py : DR level interpolation helpers (build_dr_config, get_hard_dr_config, load_doraemon_dr, _collapse_dr_to_midpoint). NOT directly omx-callable (DomainRandomizationCfg transitively imports carb), but structurally isolated from the rollout path.
- _analyze/recompute_metrics.py : pure-numpy metric core (was inside recompute.py god-file). Functions: _per_env_ss_stats, _per_env_rise_time, _per_env_peak_metrics, _compute_enhanced_metrics, _process_run. DIRECTLY omx-callable — no Isaac Sim, no matplotlib.
- _analyze/recompute_plots.py : matplotlib summary plots for recompute subcommand. Separated from metric core.
- _encoder/_shared.py : now exports load_encoder_from_state_dict(state_dict, arch) — single correct loader detecting pre-softsign LayerNorm. Both debug.py and sweep.py delegate to it. Previously debug.py silently dropped LayerNorm (latent correctness bug fixed).
- _pathsetup.py : idempotent sys.path shim; inserts analysis/ dir. Import at start of any sub-package module that needs `from common import`.

## eval.py status after refactor

eval.py is now ~1885 lines (was 3414). Still OFF-LIMITS (boots Isaac Sim at top-level import). Remaining content: rollout loop, env setup, runner/policy load, student wrapper — all result-PRODUCING code. The sim-free plotting/serialization/DR-config is now in eval_plots.py / eval_serialize.py / dr_config.py.

## DR_LEVELS single-source

DR_LEVELS and DR_SCALE are now single-sourced in common.py. Previously copied in recompute_metrics.py, student_latent.py, and eval.py. All copies replaced with `from common import DR_LEVELS`.

## omx adapter connection points (next step: eval_adapter.py)

omx exp-analyze can now call these without booting sim:
- recompute pipeline: `from _analyze.recompute_metrics import _process_run` -> run on existing data_*.npz -> emit summary.json
- plot regeneration: `from eval_plots import <plot_fn>` -> regenerate PNGs from saved npz
- result re-export: `from eval_serialize import ...` -> convert to .mat / CSV
- encoder inspection: `from _encoder._shared import load_encoder_from_state_dict` -> load checkpoint, run sweep

For adapter implementation: add `sources: [eval, encoder]` to .omx/profile/metrics.yaml and write eval_adapter.py that reads summary.json + calls _process_run. This is the [ENGINE-GAP] for eval/encoder analysis.

[ENGINE-GAP] eval_adapter.py not yet implemented. [WHERE] .omx/profile/eval_adapter.py. [SPEC] read summary.json + data_*.npz via recompute_metrics._process_run; expose per-env SS error/jitter/rise_time/overshoot per axis per DR level to omx exp-analyze. [STATUS] proposed.
