---
title: "analysis engine map — what is grow-able vs off-limits"
tags: ["engine", "analysis", "adapter", "engine-gap", "eval", "refactor", "sim-free", "omx-callable"]
created: 2026-06-02T08:39:53.980927
updated: 2026-07-12T14:11:29.031769
sources: ["constrained_albc/analysis/ tree survey 2026-06-02", "exp/analysis-refactor", "tasks-1-10", "exp/omx-eval-adapter", "exp/omx-encoder-adapter", "2026-06-05"]
links: ["training_log_analysis_engine_reference_adapter.md", "analysis_engine_map_what_is_grow_able_vs_off_limits.md"]
category: reference
confidence: high
schemaVersion: 1
---

# analysis engine map — what is grow-able vs off-limits

The workspace owns analysis code in TWO homes; engine-gap specs may grow the GROW-ABLE ones (code that READS results), never the off-limits ones (code that PRODUCES results / launches runs).

GROW-ABLE (pure post-processing, reads saved *.npz/summary.json, no Isaac Sim) — engine-gap specs target these:
- constrained_albc/analysis/analyze.py -> _analyze/ : subcommands eval_dr (heavy-tail + sample-mean divergence + axis decorrelation, the key diagnostic), recompute (per-env summary), switching (segmented DR metrics), table (Table 1), student_latent. Run: python3 constrained_albc/analysis/analyze.py eval_dr <run_dir>.
- constrained_albc/analysis/_eval_dr/metrics.py (646 lines, per-env metric math incl _pick_sample_env = median-attitude env) + trajectory.py.
- constrained_albc/analysis/compare.py : multi-run side-by-side plot (subcommands dr, tdc_rl).
- constrained_albc/analysis/monitor.py : TB dashboard / wandb report (subcommands plot, compare, wandb).
- constrained_albc/analysis/common.py (numpy only: DR_LEVELS/DR_SCALE) + paths.py (stdlib only): shared helpers, safe to extend.
- .omx/profile/analyze_training.py + tslib.py : the TB/wandb training-log adapter (see [[training_log_analysis_engine_reference_adapter]]).

OFF-LIMITS (do NOT edit during analyze/design — alters results or launches runs):
- constrained_albc/analysis/eval.py (3379 lines): imports isaaclab + constrained_albc.envs.main.* (ConstraintTRPO, ActorCriticEncoder, runners). It LOADS a policy and rolls out in Isaac Sim — an eval RUNNER, run via ./isaaclab.sh -p, NOT a post-processor. If a spec needs a pure-postproc tweak that happens to live in eval.py, extract only that part; never touch the rollout/launch path.
- cli_args.py (Isaac Sim AppLauncher args), student_policy.py (env/teacher deps).
- constrained_albc/envs/main/** (model/reward/training/env): experiment-determining source. Changing these is what the next-experiment PROBE proposes, never an analysis-time edit.

This map is the [WHERE] reference for engine-gap specs: a missing diagnostic in analyze.py = grow-able; a wrong reward = off-limits (propose a probe instead).

---

## Merged from analysis_refactor_2026_06_05_new_sim_free_modules_and_engine_gap.md (2026-07-12T14:11:29.031769)

# analysis refactor 2026-06-05 — new sim-free modules and engine-gap status

Branch exp/analysis-refactor (tasks 1-6,8-10 done 2026-06-05; task 7 deferred, needs GPU) extracted sim-free code from eval.py and recompute.py into importable plain-python3 modules. eval.py shrank 3414 -> 1885 lines (-45%). This page updates analysis-engine-map-what-is-grow-able-vs-off-limits with the new module inventory.

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

[ENGINE-GAP] encoder z-sweep — no omx core path reads encoder latent sensitivity.
[WHERE] .omx/profile/encoder_adapter.py `sweep_sensitivity`, ASSEMBLING the sim-free
engine functions `_encoder/sweep.py` `_load_encoder_for_sweep` + `_sweep_parameter`
and `common.build_sweep_params_from_checkpoint`; it computes only z_range = z.max-z.min
(guarded by test_matches_engine_z_ranges, byte-equal to sweep.py:282). [SPEC] per-DR-param
per-dim z-range sensitivity matrix + active_dims, plus optional heatmap/per-param PNG
delegation to `_plot_*` (CLI `sweep <ckpt> [--num-points N] [--plots <dir>]`; engine [INFO]
prints are redirected off stdout so the JSON contract stays clean). CORRECTION to the
earlier note: the sweep runs a torch forward but on CPU (map_location='cpu', tiny MLP) —
it is sim-free AND GPU-free, so it is unit-tested CPU-only with a 192 KB mini-checkpoint
fixture (no GPU session needed). `encoder` added to the profile sources vocab so exp-analyze
routes encoder questions. [STATUS] implemented (branch exp/omx-encoder-adapter, 2026-06-05).
