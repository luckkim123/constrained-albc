# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Privileged obs union layout (2026-07-12 consolidation, option (c)): p_t stays 27D but its
  content changed -- REMOVED Ixx and linear-damping-roll (priv-obs-slim Stage-1 validated
  removals; quad_damp + measured lin_vel RETAINED, pending their own A/B), ADDED buoy_volume
  and buoy_body_mass (DR-backed, decorrelated from the main-body scales; new DORAEMON dims
  buoy_volume_scale / buoy_body_mass_scale, NDIMS 18 -> 20). Buoy dims sit at p_t[22:24] (end
  of the DR-backed block); measured lin_vel stays last at [24:27]. Both DORAEMON sampling and
  the eval-time uniform fallback key the buoy volume off buoy_volume_scale (events
  `volume_key`); `randomize_body_mass` overwrites the buoy mass row with the independent
  scale. Analysis sweep dispatch fingerprints union-27D checkpoints by bounds content (idx22
  lower > 0, buoy volume) so pre-union 27D checkpoints keep their previous dispatch behavior.
  Supersedes the unmerged exp/priv-obs-slim (21D) and exp/dr-offset-prune-buoy (25D) branches;
  slim's contested removals (quad_damp, lin_vel) and buoy's Exp-A xy-offset prune remain in
  the experiment queue. Verification: per-dim bounds pins in test_priv_obs_bounds (27 dims),
  buoy volume/mass wiring + collapse guards in test_buoy_dr, DORAEMON registration order
  assert; full suite 353 passed (pre-existing deploy-engine failure unrelated).

- Deploy artifacts now live under `deploy/<group>/<label>_<YYMMDD_HHMMSS>/`
  (mirrors the logs tree group layer, label-before-date, timestamp =
  `analysis.paths.RUN_TS_FORMAT`) instead of ad-hoc repo-root dirs. The CLI
  derives this path when `--out` is omitted (new `--run-group`/`--tag` args);
  explicit `--out` still wins. `.gitignore` ignores the whole `deploy/` tree
  (replaces the stale `deploy_export_5000/*.npz` line). Existing artifacts
  relocated with payload hashes unchanged:
  `deploy_pack_5000iter_260611/` -> `deploy/attitude_only_campaign/pack_5000iter_260611_183252/`,
  `deploy_export_5000/` -> `deploy/attitude_only_campaign/export_5000_260611_175116/`.

### Added

- DORAEMON obs-noise curriculum: `obs_noise_scale` DR dimension (NDIMS 17 -> 18), a global
  [0,1] scale on the per-tree observation-noise std (69D main / 87D full_dof), applied as an
  extra white-noise layer in `_get_observations`. nominal=0 (byte-identical to today), widening
  to +1x std. std only; per-episode bias unchanged. Not in privileged obs (pure robustness;
  state_space unchanged: 27 main / 24 full_dof). Off by default (byte-identical when DORAEMON disabled). Both env trees
  (main + full_dof); full_dof gained a byte-identical port of `mdp/faults.py`
  (`apply_sensor_noise`) from main, since full_dof previously had no fault layer.

### Verification

- `test_faults` (stacked layer composition), `test_doraemon` (NDIMS 18, `obs_noise_scale`
  nominal 0), `test_dr_config` (eval sweep 0 -> 1). NDIMS ripple audit clean. 18-dim scheduler
  smoke.

### Notes

- Plan A continuity: scale=1 is sqrt(2)x today's std (curriculum expands BEYOND today, not
  around it). The original plan's "scale=1 == today" clause was dropped -- it contradicts
  off-byte-identical + nominal-0-clean given the two-stage noise pipeline. Robustness benefit
  is a HYPOTHESIS to verify via the comparison run, not a given. NDIMS 17 -> 18 dilutes the
  DORAEMON entropy/KL budget across one more dimension. TRAINING LAUNCH is a separate,
  user-gated step after a fault-free baseline is established.

### Fixed

- `npforward.py` was not Python 2.7-loadable: three `@` matmul sites (PEP 465,
  py3.5+) raised SyntaxError at `import` on the agent-jetson board, whose ROS
  (lunar rospy) pins the inference node to py2.7. Every parity check had run
  under python3 (test_npforward.py), which can never catch a py2 syntax break.
  Replaced `@` with `np.dot` (bit-identical: regenerated-pack parity unchanged,
  teacher 0.0/1.9e-6, TCN 1.6e-7) and added a permanent sim-free AST gate
  (`tests/deploy/test_npforward_compat.py`: no matmul / f-strings / annotations /
  keyword-only args). Stale dim docstrings (87 -> 69) fixed in the same hash
  change. New npforward sha256 `8eff0046...0741`; the old `4b708314...b10e2` is
  py2.7-broken and the 260611 pack carrying it was superseded by the regenerated
  `pack_5000iter_260612_135619` (weights/goldens byte-identical).

### Added

- `--golden` pack assembly (`constrained_albc/deploy/pack.py` + CLI flag): one
  command now produces a complete self-verifying deploy pack -- golden vectors
  (CPU-forced), `npforward.py` copy, parity self-close (loud-fail), and
  `MANIFEST.json` with payload-derived dims and per-file sha256. Verified by
  regeneration: the CLI-produced pack's weights + goldens are byte-identical to
  the hand-assembled 2026-06-11 pack. Tested sim-free end-to-end with tiny
  same-structure torch models (`tests/deploy/test_pack.py`).

- Deploy export package (`constrained_albc/deploy/`). Exports torch `.pt`
  checkpoints to numpy `.npz` matching a hardcoded board-runtime key contract,
  via an `ExportSpec` registry (one spec per architecture = key contract + model
  build + state_dict rename), a round-trip `verify_npz` stop-gate, and a CLI
  (`--list-specs` / `--spec` / `--batch attitude_only_5000`). Two specs:
  `StudentTCNSpec` (14-key identity map -> `weights_tcn.npz`) and
  `TeacherActorSpec` (43-key ActorCriticEncoder filtered to 10 actor+normalizer
  keys, `actor_obs_normalizer.*` renamed to `normalizer.*` -> `weights_teacher.npz`).
  Verified dims for the attitude-only 5000-iter run: policy obs 69, action 8,
  latent 9, teacher actor input 78 (= obs69 + latent9). All exports fp32 and
  byte-identical to the source checkpoints (max|delta| = 0).
  - **Import isolation** (`deploy/_isolation.py` + `scripts/export_deploy.py`):
    export runs on hosts without the Isaac Sim USD runtime (no `pxr`). The launcher
    injects lightweight `sys.modules` stubs for the three sim-pulling import roots
    (`constrained_albc`, `constrained_albc.envs.main`, `isaaclab.utils`) before the
    package `__init__` (gym register -> `albc_env` -> `isaaclab.sim` -> `pxr`) can
    fire, so the sim-free student/teacher build code loads against unmodified source.
    Training code and the pristine isaaclab fork are never modified, only shadowed
    in `sys.modules` during export.
  - **Teacher build** derives architecture dims and encoder-obs bounds from the
    checkpoint tensors (`_infer_teacher_dims`), not hardcoded config, so it serves
    any teacher variant (main full-DOF 87/24 or attitude-only 69/27) and cannot
    silently export a mis-shaped model. Load uses the encoder's own
    `load_state_dict` override (robust to omitted non-exported heads) plus a
    pre-load presence check on the export-required actor/normalizer keys and a
    post-load byte-identity integrity gate.
  - **Golden e2e: skipped** on the container -- the 69D observation assembly lives
    in `albc_env.py` (the sim env), not in student code, so it cannot be lifted
    byte-identically on an export host. The `.npz` payloads are complete and
    independently value-verified; generate `golden_e2e_tcn.npz` on the Mac/ksm-nas
    path during board integration. The `.npz` artifacts are gitignored (large
    binary build outputs; kept on disk for docker-cp).

- DORAEMON curriculum replay wiring. The runner flushes
  `curriculum_trajectory.json` into the run dir per checkpoint and passes the RL
  iteration into `_doraemon.step(iteration=...)`. `_init_doraemon` constructs a
  `CurriculumReplayer` (frozen replay) when `replay_curriculum_path` (config) or
  `--replay_curriculum` (CLI, wins) is set, otherwise the live `DoraemonScheduler`.
  Lets MDP / no-encoder baselines replay the cmdp run's exact DR curriculum so the
  only controlled difference is the algorithm. Engine lives in marinelab.

### Changed

- `paths.find_runs` now ignores alias symlinks and `_`-prefixed / `legacy` subtrees during run
  enumeration, and tolerates an extra purpose-grouping layer
  (`experiments/rsl_rl/<exp>/<group>/<run_id>/`, e.g. `dr_harder/`). Previously a `baseline -> run`
  alias symlink was double-listed as a separate run (`run_id="baseline"`) and a `_pre_reanalysis_
  backup/.../` subtree surfaced its non-underscore leaf as a phantom run, because `rglob` is a flat
  iterator (pruning a parent does not stop descent). The skip now tests EVERY path segment relative
  to the scan root, so aliases/backups at any depth are excluded while real runs at any grouping
  depth are still found. Guarded by 3 new tests in `test_paths.py` (purpose-group layer; alias +
  backup ignored). Lets runs be classified by experiment purpose (a `dr_harder/` group with its own
  `baseline` pointer) without corrupting `find_runs` / eval routing.
- `paths.resolve_eval` now stamps eval folders with `RUN_TS_FORMAT` (`%y%m%d_%H%M%S`) instead of
  the hardcoded `%Y-%m-%d_%H-%M-%S`. The eval folder date now matches the run_id by construction
  (`static_260606_054825` under `..._260606_004205`), making `RUN_TS_FORMAT` the single source of
  truth for every output timestamp (run_id / eval / encoder). Prevents the run_id-vs-eval date-
  format split. `_timestamp_from_log_dir` already dual-accepts both formats, so old eval folders
  still resolve. See `docs/results/2026-06-06-output-naming-cleanup.md`.
- run_id shortened: `%Y-%m-%d_%H-%M-%S` -> `%y%m%d_%H%M%S` (`paths.RUN_TS_FORMAT`), so a
  run_id goes from `2026-05-25_16-02-48_trpo` (24 chars) to `260525_160248_trpo` (18).
  task_short is kept. `_timestamp_from_log_dir` parses both the short and the legacy long
  format, so older training folders still resolve.
- experiments/ trees are now grouped by experiment_name:
  `experiments/rsl_rl/<experiment_name>/<run_id>/` (was flat `experiments/<run_id>/`),
  mirroring `logs/rsl_rl/<experiment_name>/`. Run-tree detection (eval output routing,
  student->teacher linkage) switched from "the dir right under experiments/" to the `train`
  symlink ancestor (`paths._run_root_from_path`), so it is grouping-depth-independent and a
  flat layout still resolves.
- Training log folder leaf now equals the run_id. train.py / train_student.py build the
  `logs/rsl_rl/<experiment_name>/` leaf via `make_run_id` (the builder `emit_run_manifest` already
  used), so `logs/rsl_rl/<exp>/<run_id>/` and `experiments/rsl_rl/<exp>/<run_id>/` share one
  identical name. Previously the logs leaf was `<ts>_<run_name>` (no task_short) while the
  experiments run_id was `<ts>_<task_short>_<run_name>` -- the two drifted. The `latest` symlink,
  `_timestamp_from_log_dir`, and resume (`load_run`) are unaffected (they read the timestamp prefix
  or the whole leaf, not task_short specifically).
- experiment_name renamed for teacher/student clustering: teacher `albc_trpo` ->
  `albc_trpo_teacher` (rsl_rl_ppo_cfg.py), student `student_policy` -> `albc_trpo_student`
  (student/config.py). The WandB project (`--log_project_name` / `--wandb_project`) is a
  separate axis and is unchanged.
- Student training output no longer leaks into the isaaclab repo. `StudentCfg.log_dir_root`
  is now an ABSOLUTE constrained-albc path (anchored to the repo root) and train_student.py
  derives `experiments_root` from it, instead of relative paths that resolved against the
  isaaclab cwd train_student.py runs from. Teacher and student output share one source-of-truth
  tree under constrained-albc.

### Added

- `eval_dr.py static` accepts `--student_ckpt`/`--teacher_ckpt`/`--encoder_type` (mirrors
  `segmented`), so a distilled student is evaluated through the same static path as the teacher
  (4 DR levels + `.mat` + full PNG set) for a 1:1 teacher/student comparison. Reuses
  `student.eval.build_student_policy_fn`; the eval loop is policy-agnostic so only the policy
  loader differs. DORAEMON DR / agent params resolve from the teacher dir in student mode.
- Student evaluation is now symmetric across TCN and GRU: each is evaluated with the SAME two
  modes, `static` (teacher-comparable) + `segmented` (switching), as plain `eval.py` invocations.
  Previously the (now-removed) launcher ran only `segmented` for TCN while GRU also ran
  `eval_student dr`; the asymmetric `eval_student dr` was dropped (`static` supersedes it).
- Encoder-fidelity latent diagnostic integrated into `eval_dr.py static`: when a student is
  evaluated, the same pass also logs (l_hat = student-predicted latent, l_true = teacher
  privileged latent) per DR level, writing `latent_{level}.npz` + `summary_latent.json` (overall
  / per-dim MSE, env-variance and time-variance collapse checks, per-env RMSE). Moved from
  `eval_student.py latent`; one static pass now yields both performance and the encoder
  diagnostic, so it is run for every student eval (rule 03: encoder verification needs more than
  aggregate z_std). The wrapper's action is identical to the wrapped policy, so performance
  metrics are unaffected.

### Fixed

- Enhanced-summary regeneration looked for `<run_dir>/eval_dr/data_*.npz` while
  the run-id-tree static eval writes data to `<run_dir>/eval/static_<ts>/`, so
  `summary.json` + per-env `summary_*.png` were silently skipped. `_analyze.recompute`
  now takes a `data_subdir` argument (default `"eval_dr"` preserves the legacy
  `analyze.py recompute` layout); `eval.run_static` passes the actual data
  folder name so enhanced summaries land beside the `.npz` files. (Surfaced during an
  end-to-end teacher -> student -> eval run.)
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

- All four shell launchers under `scripts/` (`launch_student_tcn.sh`, `launch_student_gru.sh`,
  `launch_students_sequential.sh`, `run_student_evals.sh`). They only wrapped a single
  `train_student.py` / `eval.py` invocation with a `cd`, a `CUDA_VISIBLE_DEVICES` flag, and
  sequential ordering — the teacher already runs without any such wrapper, so the student side
  is now symmetric: invoke `train_student.py` / `eval.py` directly (see README). Their baked-in
  hyperparameters were either `train_student.py` defaults or two CLI-overridable values
  (`--num_envs 2048`, `--wandb_project constrained_albc_student`); nothing reproducible is lost.
- `constrained_albc/analysis/eval_student.py`: both its modes are now redundant. `dr`
  (DR-level performance) is superseded by `eval.py static --student_ckpt` (teacher-comparable,
  with .mat); `latent` (l_hat/l_true encoder diagnostic) moved into the same static student pass.
  Nothing referenced it once the student eval moved to direct `eval.py` invocations. The shared
  `StudentInLoopPolicy` it used lives in `analysis/student_policy.py` (kept).
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
