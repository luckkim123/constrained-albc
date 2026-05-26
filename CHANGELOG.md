# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Eval pipeline, three independent issues surfaced during an end-to-end
  teacher -> student -> eval run:
  - `run_student_evals.sh` aborted after the first eval stage. The `run()` helper
    ended with `[ $rc -ne 0 ] && {...}`; under `set -e`, when a stage succeeds
    (rc==0) that test is false, making the function's exit status 1, which `set -e`
    treats as failure and kills the script. Replaced with an explicit
    `if [ "$rc" -ne 0 ]; then ...; fi` so successful stages return 0 and the next
    stage runs.
  - Enhanced-summary regeneration looked for `<run_dir>/eval_dr/data_*.npz` while
    the run-id-tree static eval writes data to `<run_dir>/eval/static_<ts>/`, so
    `summary.json` + per-env `summary_*.png` were silently skipped. `_analyze.recompute`
    now takes a `data_subdir` argument (default `"eval_dr"` preserves the legacy
    `analyze.py recompute` layout); `eval_dr.run_static` passes the actual data
    folder name so enhanced summaries land beside the `.npz` files.
  - `run_student_evals.sh` now resolves `TEACHER`/`TCN_CKPT`/`GRU_CKPT` to absolute
    paths (via `realpath -m`) before its `cd /workspace/isaaclab`, and asserts each
    file exists. Previously a relative `experiments/...` path given from the
    constrained-albc dir was not found post-cd (FileNotFoundError).
- Ocean current migrated to the marinelab.core `OceanCurrent` API. marinelab v0.2.0
  removed `HydrodynamicsModel._current_velocity` / `._max_current_vel` (the current
  moved into a standalone component); albc accessed the removed buffers in 8+ sites
  and crashed on env reset / OU step. Reads and writes now route through
  `hydro.current.velocity_w` / `.max_velocity` / `.set`, and the buoy model shares
  the main model's `OceanCurrent` via constructor injection (the manual per-step
  sync is removed). OU math unchanged.
- `test_update_buoyancy_force_subset` (pre-existing failure): the test passed a
  full-batch `F_bu` with a subset `env_ids`, but `_set_param` (and the sole real
  caller, `tdc_env._reset_idx`) expect `F_bu` pre-sliced to `env_ids`. Fixed the
  test to pass subset-shaped values.

### Added

- Runtime obs-shape assert in `_get_observations()` (complements the existing
  construction-time check at `albc_env.py:138`).
- Isaac-Sim-free tests: `test_current_migration.py` (OceanCurrent API regression
  net) and `test_config_equivalence.py` (config de-dup `to_dict()` equality).
- `experiment-plots/` (gitignored): 962 eval/training PNG plots migrated from the
  old `isaaclab/logs` tree, original per-run directory structure preserved, plus
  `_final_models/` holding `r13_A`/`r13_B` `model_4999.pt` + their env/agent configs.
  See `experiment-plots/README.md`; `experiments-archive.md` now links to it.

### Changed

- FullDOF runner cfgs de-duplicated via `_BaseFullDOFRunnerCfg` (shared seed /
  num_steps_per_env / max_iterations / save_interval). No field value changes;
  `FullDOFPPOEncRunnerCfg` keeps its intentional `save_interval=100` override.
  Guarded by `test_config_equivalence.py`.

### Removed

- Unused `compute_M_bb` (`tdc.py`): exported but had zero call sites.
- `isaaclab/logs` (11G) + `isaaclab/wandb` (6.9G) + `isaaclab/outputs` (24M) raw
  experiment artifacts deleted (~17.9G reclaimed). Checkpoints are unusable post
  repo-3split / fork-removal / OceanCurrent migration (runtime environment that
  produced them no longer exists) and no successful run exists; numeric results
  live in `docs/reference/experiments-archive.md` + `experiments-index.json` (49
  experiments). Only PNG plots and `r13_A`/`r13_B` finals were kept (see Added).

### Notes

- DIAGNOSIS Phase C (added-mass clamp on DR'd inertia, barrier log floor, cost
  surrogate `1/(1-gamma)` scale, OU 5% over-clamp) remains diagnosis-only; these
  change learning behavior and need approval plus before/after data. See
  `DIAGNOSIS.md` section 9.

### Verification

- `pytest tests/` — 32 passed, 2 skipped (the 2 skips are the marinelab API-surface
  check, which importorskips without Isaac Sim).
- `ast.parse` over the package — OK.
- grep confirms zero `_current_velocity` / `_max_current_vel` / `compute_M_bb`
  references remain.

## [0.1.0] - 2026-05-25

### Added

- Initial extraction from the isaaclab monorepo with full git history (`git filter-repo`).
- `constrained_full_albc` environment: ConstraintTRPO + IPO + asymmetric encoder,
  DORAEMON adaptive DR curriculum, 6-DOF full-DOF ALBC for underwater vehicles.
- `constrained_full_albc_tdc` environment: TDC (Time-Delay Controller) variant with
  kinematics, TDC, and thruster-PD controllers.
- Student distillation pipeline (TCN / GRU) under `envs/constrained_full_albc/student/`:
  collector, runner, models, teacher, eval.
- Analysis tooling under `constrained_albc/analysis/`: `eval_dr` (4 DR modes: static,
  periodic, segmented, sudden), `eval_student`, `analyze`, `compare`, `monitor`,
  `encoder_tools`.
- Launcher scripts under `scripts/`: `launch_student_tcn.sh`, `launch_student_gru.sh`,
  `launch_students_sequential.sh`, `run_student_evals.sh`, `train_student.py`.
- Six registered Isaac Lab task IDs: `Isaac-FullDOF-TRPO-v0` (main),
  `Isaac-FullDOF-NoEncoder-v0`, `Isaac-FullDOF-PPO-v0`, `Isaac-FullDOF-TRPO-NoIPO-v0`,
  `Isaac-FullDOF-PPO-Enc-v0`, `Isaac-FullDOF-TDC-v0`.
- Depends on `marinelab` for shared marine physics and UUV assets (Hero Agent).
