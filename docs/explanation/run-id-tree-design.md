# run_id Single Tree Design (Unifying Training, Evaluation, and Config)

> Status: **Implemented (minimal-touch)** (2026-05-25). All 6 modification points (section 4) and
> all 3 Open Questions (section 6) are done. The minimal-touch approach was chosen: training/eval
> output stays in `logs/`, and `experiments/<run_id>/` is added as a tracing entry point
> (manifest.json + copied config + a `train` symlink). Physical relocation of tb/checkpoints under
> `experiments/` (the literal "path replacement" of #1) was intentionally deferred -- it is a separate,
> higher-risk change (resume compatibility) and not needed for the unified-tracing goal.
> Commits: c903f12 (#4 paths.py) · fce9685 (#6 Hydra) · 6eac3d6 (Open Q) · d0d4588 (#1 train.py) ·
> 1a5d591 (#2 eval_dr) · d074fad (#3 student) · df64cf8 (#5 common). Verified GPU-free via 39 unit
> tests in tests/test_paths.py; end-to-end manifest emission still wants one real smoke run to confirm.

## 1. Problem — The Same Run Is Scattered Across 4 Places

Currently the outputs of a single policy are scattered across different trees. To trace "from which training config
this eval PNG's policy came", one must visually cross-reference timestamps.

| Output | Current path | Generation location (verified) |
|:---|:---|:---|
| Training (model/tb/doraemon/params/git) | `logs/rsl_rl/<exp>/<ts>_<run>/` | `scripts/train.py:193-200` |
| static eval | `logs/eval_dr/<folder>/<ts>/` | `eval_dr.py:2288` |
| periodic eval | `logs/eval_dr_robustness/<folder>/<ts>/` | `eval_dr.py:2982` |
| sudden eval | `<ckpt_dir>/eval_single_switch/` | `eval_dr.py:4004` |
| student training | `logs/rsl_rl/student_policy/` | `student/config.py:59` |
| Hydra config | `outputs/<date>/<time>/.hydra/` | `@hydra_task_config` (automatic) |

Key point: training is grouped by `experiment_name` (= fixed per task), and eval branches off into a
**separate top-level tree** called `eval_dr/`. The only thing connecting the two is the timestamp.

## 2. Solution — run_id as a Single Key

### 2-A. run_id Convention

```
run_id = <YYMMDD_HHMMSS>_<task_short>[_<tag>]
  e.g.: 260525_160248_trpo
        260525_170012_ppo-enc_ablation
```

- The timestamp format is `%y%m%d_%H%M%S` (`paths.RUN_TS_FORMAT`, train.py:196) — **shortened
  2026-05-26** from the original `%Y-%m-%d_%H-%M-%S` (19→13 chars) because the full run_id was too
  long; `task_short` is kept. `_timestamp_from_log_dir` parses BOTH the short and the legacy long
  format, so older training folders still resolve.
- `task_short`: extracted from the task ID. `Isaac-ConstrainedALBC-TRPO-v0`→`trpo`, `-PPO-Enc-`→`ppo-enc`,
  `-NoEncoder-`→`noenc`, `-TRPO-NoIPO-`→`trpo-noipo`, `-PPO-`→`ppo`, `-TDC-`→`tdc`.
  → task_short resolves the problem where the current 4 ablations are mixed into one folder under
     `experiment_name="full_dof_ablation"` (rsl_rl_ppo_cfg.py:298/381 + ablation_cfgs.py:40/79).
- `tag`: reuses the existing `run_name` (train.py:199) as is.
- Collision policy: run_id uniqueness (via the testname/tag) is the caller's responsibility; an
  existing run dir is not overwritten.
- **The training log folder leaf == the run_id (2026-05-26).** train.py / train_student.py build
  the `logs/rsl_rl/<experiment_name>/` leaf via `make_run_id` (the same builder
  `emit_run_manifest` uses), so `logs/rsl_rl/<exp>/<run_id>/` and
  `experiments/rsl_rl/<exp>/<run_id>/` share one identical name -- the logs leaf now includes
  `task_short` too (previously it was `<ts>_<run_name>` with no task_short, which drifted from
  the experiments run_id).

### 2-B. Directory Layout (grouped by experiment_name, sibling to legacy)

Runs are grouped under `experiments/rsl_rl/<experiment_name>/<run_id>/` (**2026-05-26**), mirroring
the `logs/rsl_rl/<experiment_name>/` layout so teacher (`albc_trpo_teacher`) and student
(`albc_trpo_student`) cluster together. Detection of a run tree (eval output routing, student->teacher
linkage) is via the `train` symlink ancestor (`paths._run_root_from_path`), so it is independent of the
grouping depth — a flat `experiments/<run_id>/` still resolves too.

```
experiments/                              # .gitignore'd (large outputs)
├── legacy/                               # past frozen outputs (already moved 2026-05-25)
│   ├── plots/  final_models/  README.md
└── rsl_rl/<experiment_name>/<run_id>/    # NEW: active run single tree, grouped by experiment_name
    ├── manifest.json                     # ★ run meta — entry point for all tracing (§3)
    ├── config/
    │   ├── env.yaml                      # existing params/env.yaml (train.py already dumps it)
    │   ├── agent.yaml                    # existing params/agent.yaml
    │   ├── hydra_config.yaml             # moved from outputs/.hydra/config.yaml
    │   └── git_state.txt                 # existing git/ (runner.add_git_repo_to_log)
    ├── train/
    │   ├── tb/                           # events.out.tfevents.*
    │   ├── checkpoints/                  # model_*.pt (numeric sort — feedback_model_trim_disaster)
    │   └── doraemon_state.pt
    └── eval/
        └── <mode>_<eval_ts>/             # static / periodic / segmented (only 3 modes exist)
            ├── raw/                      # data_<level>.npz (+ .mat option, INFRA §2-D)
            ├── figures/                  # diagnostic PNG (traj_*/summary_*)
            └── summary.json              # output of analyze.py recompute
```

Key point: **the training folder name (run_id) and the eval folder (eval/<mode>_<ts>/) share the same parent** →
training, evaluation, and config are all reachable with a single run_id. No timestamp cross-referencing needed.

### 2-C. student Linkage

The student is a child of the teacher. Instead of a separate top-level (`logs/rsl_rl/student_policy/`):
- Option A (nested): `experiments/<teacher_run_id>/student/<student_run_id>/`
- Option B (sibling + reference): `experiments/<student_run_id>/` + linked via the manifest's `parent_run_id`.
  → **B recommended** (teacher/student can run independently, replacing the hardcoded teacher_run_dir at student/config.py:17).

## 3. manifest.json — Entry Point for Tracing

```json
{
  "run_id": "2026-05-25_16-02-48_trpo",
  "kind": "teacher | student",
  "parent_run_id": "<teacher run_id>",        // only when student
  "task": "Isaac-ConstrainedALBC-TRPO-v0",
  "created": "2026-05-25T16:02:48",
  "git": {"sha": "...", "branch": "...", "dirty": false},
  "config": {"num_envs": 4096, "max_iterations": 2500, "seed": 30,
             "algorithm": "ConstraintTRPO+IPO", "encoder_latent_dim": 9},
  "wandb": {"project": "constrained-albc", "run_path": ".../runs/<id>", "url": "..."},
  "paths": {"tb": "train/tb", "checkpoints": "train/checkpoints",
            "evals": ["eval/static_2026-05-25_18-00-00", ...]},
  "status": "running | completed | failed",
  "repro": {"seed": 30, "rng_seeded": false, "dr_distribution_source": "tb",
            "value_norm_persisted": false},   // INFRA §14 self-records the reproducibility grade
  "final_metrics": {"att_ss_error_hard_deg": 8.2, ...}
}
```

Instead of grepping timestamp directories, post-hoc tools (analyze/compare) read the manifest to
resolve paths. Knowing only the run_id, training, evaluation, config, and wandb URL are all reachable.

## 4. Modification Points at Implementation Time (On Hold — After Approval)

| # | file:line | Change | Risk |
|:--|:---|:---|:---|
| 1 | `train.py` (after params dump) | **DONE** (commit d0d4588, minimal-touch): training output stays in `logs/rsl_rl/<exp>/<ts>/`; `experiments/<run_id>/` added as a tracing entry (manifest + config copy + `train` symlink). Physical path replacement (moving tb/ckpt under experiments) deferred. | Done (training-neutral) |
| 2 | `eval_dr.py` (4 modes) | **DONE** (commit 1a5d591): `eval_dir_for_checkpoint()` routes eval into `experiments/<run_id>/eval/<mode>_<ts>/` when the checkpoint is in a run_id tree; legacy checkpoints + explicit `--output_dir` unchanged. | Done |
| 3 | `train_student.py` (after StudentRunner) | **DONE** (commit d074fad): `emit_run_manifest(kind="student", parent_run_id=...)`; teacher resolved via `run_id_from_path(cfg.teacher_run_dir)`, omitted if legacy. Section 2-C Option B. | Done |
| 4 | `analysis/paths.py` (NEW) | `resolve_run(run_id)`/`resolve_eval()` — manifest-based | **DONE** (commit c903f12, training-neutral; imported by nothing yet) |
| 5 | `common.py` | **DONE** (commit df64cf8): `resolve_run_path` delegates to `paths.resolve_run`, returning `tb_dir` so monitor/encoder-debug work for both run_id-tree and legacy runs. | Done |
| 6 | `train.py` (overlay, NOT isaaclab) | Inject `hydra.run.dir=experiments/<run_id>/config` into `hydra_args` | **Verified possible** (see section 6 #1) |

## 5. Migration

- Past runs: already frozen into `experiments/legacy/` (move completed). The run_id tree applies from new runs onward.
- legacy has no manifest — paths.py scans directories for legacy and prioritizes the manifest for active.

## 6. Open Questions (User Confirmation Before Starting Implementation)

1. **RESOLVED (2026-05-25): Hydra `run.dir` override is possible — no copy-after needed, isaaclab stays pristine.**
   - `hydra_task_config` (isaaclab `isaaclab_tasks/utils/hydra.py:83`) uses a standard
     `@hydra.main(config_path=None, config_name=..., version_base="1.3")`. train.py forwards
     `hydra_args` to it via `sys.argv = [argv0] + hydra_args` (train.py:91), so the standard
     Hydra override `hydra.run.dir=<path>` reaches the run as a normal CLI arg.
   - Verified empirically (Hydra 1.3.2): reproducing the exact decorator pattern with
     `sys.argv=[argv0, "hydra.run.dir=<TARGET>"]` makes `HydraConfig.get().run.dir == TARGET`
     and writes `<TARGET>/.hydra/{config,hydra,overrides}.yaml`.
   - Implication: at implementation time, train.py (the overlay, NOT isaaclab) injects
     `hydra.run.dir=experiments/<run_id>/config` into `hydra_args` before calling the decorated
     main. No edit to isaaclab `hydra.py` (`feedback_isaaclab_pristine` preserved).
     `HydraConfig.get().run.dir` is also readable inside the run for a copy-after fallback if ever needed.
2. **RESOLVED (2026-05-25): Apply from new runs onward; past runs not migrated.**
   The 5 past `logs/rsl_rl/` runs were all same-day smoke/debug runs (max iteration 0-1,
   31M total) with no training value, and were deleted. The run_id tree applies to new
   training only; paths.py still resolves any future legacy dir via its fallback (section 5).
3. **RESOLVED (2026-05-25): Do NOT include git_sha in run_id.**
   `run_id = <ts>_<task_short>` (e.g. `2026-05-25_16-02-48_trpo`, ~24 chars). Timestamp +
   task_short suffice: observed same-second collisions = 0, and parallel ablations differ by
   task_short (trpo/ppo/noenc/...). The commit SHA is still recorded in manifest.git.sha
   (section 3) for provenance, just not in the directory name.
