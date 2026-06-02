---
title: "analysis engine map — what is grow-able vs off-limits"
tags: ["engine", "analysis", "adapter", "engine-gap", "eval"]
created: 2026-06-02T08:39:53.980927
updated: 2026-06-02T08:39:53.980927
sources: ["constrained_albc/analysis/ tree survey 2026-06-02"]
links: ["training_log_analysis_engine_reference_adapter.md"]
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
- .omx/profile/analyze_training.py + tslib.py : the TB/wandb training-log adapter (see [[training-log-analysis-engine-reference-adapter]]).

OFF-LIMITS (do NOT edit during analyze/design — alters results or launches runs):
- constrained_albc/analysis/eval.py (3379 lines): imports isaaclab + constrained_albc.envs.main.* (ConstraintTRPO, ActorCriticEncoder, runners). It LOADS a policy and rolls out in Isaac Sim — an eval RUNNER, run via ./isaaclab.sh -p, NOT a post-processor. If a spec needs a pure-postproc tweak that happens to live in eval.py, extract only that part; never touch the rollout/launch path.
- cli_args.py (Isaac Sim AppLauncher args), student_policy.py (env/teacher deps).
- constrained_albc/envs/main/** (model/reward/training/env): experiment-determining source. Changing these is what the next-experiment PROBE proposes, never an analysis-time edit.

This map is the [WHERE] reference for engine-gap specs: a missing diagnostic in analyze.py = grow-able; a wrong reward = off-limits (propose a probe instead).
