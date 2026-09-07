# Domain Rules — constrained-albc (UUV RL, experiment project)

6-DOF underwater vehicle-manipulator RL on Isaac Lab. Default task is attitude-only
`Isaac-ConstrainedALBC-TRPO-v0` (`envs/main`); the classical-control baselines are
`Isaac-ConstrainedALBC-Main-{TDC,PID,ATDC}-v0` (`envs/tdc_main`). The legacy full-DOF
family (`envs/full_dof`, `envs/tdc`, `Isaac-ConstrainedALBC-Full-*`, `-TDC-v0`) was
removed in the 2026-09 cleanup — do NOT launch those ids; they are at tag
`legacy-full-dof-final`. The training machinery (ConstraintTRPO, encoder, runners,
student distillation) lives in `constrained_albc/algorithms/` -- promoted out of
`envs/_core/` in the same cleanup, and the four `envs/main/` import shims
(`algorithms`, `encoder`, `runners`, `student`) deleted. Every `__init__` there is
docstring-only, so import the module directly:
`from constrained_albc.algorithms.constraint_trpo import ConstraintTRPO`.

## Execution

Scripts run through the Isaac Sim interpreter (a PATH `python` wrapper execs
`/isaac-sim/python.sh`). Plain system `python` cannot find Isaac Sim modules.
Entry points are overlay-owned: `scripts/train.py`, `scripts/play.py`.

## Evaluation

"Evaluate" means running the eval script and showing PNG plots. A text metric summary
is not an evaluation.

- Main task: `constrained_albc/analysis/eval.py static` is mandatory.
- **Do not pass `--output_dir`.** When the checkpoint sits inside the run-id tree,
  eval.py routes output to `experiments/<run_id>/eval/<mode>_<ts>/` on its own; an
  explicit `--output_dir` overrides that and scatters the artifacts.
- **Give the checkpoint through the `train` symlink path**
  (`experiments/rsl_rl/<exp>/<run_id>/train/model_4999.pt`), not the `logs/` path.
  The run-id tree is detected by the `train` path segment; without it the output
  silently falls back to the legacy `eval_dr/` directory.

## Analysis discipline

- Report env-to-env variance, not just the mean. Compute CV (`ss_error_std/ss_error`);
  compare all four DR levels (none/soft/medium/hard) and every axis.
- Heavy-tail and sample-mean divergence are independent failure modes. Do not call a
  large std "heavy-tail" -- that verdict needs `analyze.py eval_dr`.
- Read the code before reading the metric. A constraint or reward function's name is
  not evidence of what it computes.
- Predict recovery by slope, not by hope: `(target - current) / slope` over the last
  ~200 iters. "Wait longer" without that number is a guess.
- Never add an auxiliary loss to the encoder (reconstruction, z_bounds, contrastive).
  Reconstruction was measured to collapse z.

## Experiments

- `run_id` is always `make_run_id` output (`<task_short>[_<tag>]_<ts>`); the tag is
  mandatory.
- The `<group>` folder name, the wandb project name, and the experiment PURPOSE are one
  self-documenting string: launch with the same value for `--run_group` and
  `--log_project_name`.
- Results SSOT is the `experiments/` tree (`report.md`), never a loose markdown file.
- Never launch training autonomously. Queue it (`omx queue-launch`) -- a human gate
  approves the launch.
- A comparison experiment branches from a baseline tag onto `exp/<topic>`; `main` stays
  the verified original.

## Settled -- do not re-open

Ocean current is enabled. Encoder is elu hidden + LayerNorm + softsign output,
`encoder_latent_dim=9`. Algorithm is ConstraintTRPO + IPO with an asymmetric critic.
