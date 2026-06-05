---
title: "analysis refactor 2026-06-05 — new sim-free modules and engine-gap status"
tags: ["engine", "engine-gap", "analysis", "refactor", "sim-free", "omx-callable"]
created: 2026-06-05T06:43:49.886174
updated: 2026-06-05T18:00:00.000000
sources: ["exp/analysis-refactor", "tasks-1-10", "exp/omx-eval-adapter", "2026-06-05"]
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

## omx import pattern for the sim-free modules (verified 2026-06-05)

The correct and SUFFICIENT way for omx (eval_adapter / omx_paths) to import the
metric core, plotting, and serialization without booting Isaac Sim is: put the
`analysis/` dir on sys.path (one line), then import the packages by name:

    import sys, os
    sys.path.insert(0, "<repo>/constrained_albc/analysis")
    from _analyze import recompute_metrics    # _analyze/ is a real package (__init__.py)
    from eval_plots import generate_plots
    from eval_serialize import write_eval_npz

That single sys.path line is enough — `_analyze` is a proper package so its
internal relative imports (`from ._shared import ...`) and sibling imports
(`from common import ...`) all resolve. The sub-package modules do NOT each need
their own `import _pathsetup`: only `_analyze/student_latent.py` wires it, and
adding it to the others changes nothing about omx's ability to import them (it is
pure redundant defense). Conversely the 3 entrypoints (eval.py / analyze.py /
encoder_tools.py) keep their raw `sys.path.insert(self_dir)` BY DESIGN — they are
the ones that establish the path, so they cannot `import _pathsetup` (chicken-egg).
Net: the "_pathsetup wiring scope-gap" is CLOSED with no work owed.

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

[ENGINE-GAP] eval basic stats (mean/std/CV) — RESOLVED by the omx core, not by an
adapter. `omx reduce summarize --path <summary.json> --format eval_summary --cv-field
<metric>` already emits per-axis mean/std/CV for all 4 DR levels (verified EXIT 0 on
the teacher run, 2026-06-05; 28 rows = 4 levels x 7 axes). No adapter was built for
basic stats — that would duplicate the core (DRY). [STATUS] resolved-by-core.

[ENGINE-GAP] eval heavy-tail / sample-mean divergence / cross-axis corr — the core
CANNOT do this (`omx reduce summarize --cv-field n_gt20` returns an empty cv list; the
core only CVs fields with a `_std` sibling). Required by repo rule 03-analysis-quality.md
("절대 하지 말 것: mean+std로 heavy-tail 판정"). [WHERE] .omx/profile/eval_adapter.py
`analyze_eval`, a PURE pass-through to sim-free `_analyze/eval_dr.py` `_ed_analyze_run`
(it computes nothing itself, so it cannot drift — guarded by test_adapter_matches_engine_directly,
`out == ref`). [SPEC] per-DR-level per-axis heavy_tail (_HeavyTail: ss_mean/ss_std/ss_max/
peak_mean/peak_max/pct_peak_gt_thresh/pct_ss_gt_hthresh/n_env) + divergence (sample_rank_pct
etc.) + cross-axis corr, from data_*.npz, no Isaac Sim. CLI `eval_adapter.py heavy-tail
<eval_dir>` emits JSON for exp-analyze's code-exec path. Also: `eval` added to the profile
sources vocab so exp-analyze routes eval questions. [STATUS] implemented (branch
exp/omx-eval-adapter, 2026-06-05).

[ENGINE-GAP] encoder z-sweep — no omx path reads encoder latent sensitivity. [WHERE] new
.omx/profile/encoder_adapter.py, delegating to sim-free `_encoder/_shared.py`
`load_encoder_from_state_dict` + `_encoder/sweep.py`. [SPEC] load checkpoint state_dict,
run per-dim z sensitivity sweep, emit JSON. NOTE: the sweep itself runs a torch forward
(GPU), so this adapter is NOT fully sim-free — defer to a GPU-capable session. [STATUS] proposed.
