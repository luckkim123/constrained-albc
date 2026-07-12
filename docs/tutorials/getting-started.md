# Getting Started

A first walkthrough: confirm the stack is installed, run a short smoke-train,
find the output, evaluate the checkpoint, and read the resulting plots. This
is learning-oriented (Diátaxis "tutorial") — for flag/task lookup use the
linked `reference/` and `how-to/` pages instead of repeating them here.

## Prerequisites

- This workspace runs inside a Docker container that already provides Isaac
  Sim 5.1.0 and the Isaac Lab editable install.
- Install order is strict: `isaaclab` -> `marinelab` -> `constrained-albc`
  (each overlay depends on the layer below it). Follow
  [`../installation.md`](../installation.md) end to end before continuing —
  it covers the `pip install -e` steps and the task-registration check.

Confirm the stack is ready (registers the default task):

```bash
cd /workspace/isaaclab && ./isaaclab.sh -p -c "
import constrained_albc  # noqa: F401  triggers gym.register()
import gymnasium as gym
print('Isaac-ConstrainedALBC-TRPO-v0' in gym.envs.registry)
"
```

Expected output: `True`.

## 1. Smoke-train (100 iterations)

Run a short training job to confirm the stack works end to end. `--num_envs
256` and `--max_iterations 100` keep it to a few minutes on a single GPU:

```bash
cd /workspace/constrained-albc && python scripts/train.py \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --num_envs 256 --max_iterations 100 --headless
```

`--task`, `--num_envs`, `--max_iterations`, `--headless` are all real flags
(verified against `scripts/train.py`'s argparse; `--headless` comes from
Isaac Lab's `AppLauncher`). The default agent config (`ALBCTRPORunnerCfg`)
sets `logger = "wandb"` — if WandB is not configured yet, add `--logger
tensorboard` to this first run to skip the login prompt.

## 2. Where the run lands

Paths are resolved relative to the directory you ran the command from
(`/workspace/constrained-albc`), not the Isaac Sim interpreter's location.
Two trees are written:

- **Training output** (checkpoints, TensorBoard events):
  `logs/rsl_rl/albc_trpo_teacher/<run_id>/`
- **Tracing entry point** (auto-created by `train.py`, mirrors the above):
  `experiments/rsl_rl/albc_trpo_teacher/<run_id>/`, containing
  `manifest.json`, a copied `config/`, and a `train` symlink back to the
  `logs/` directory above.

`<run_id>` defaults to `trpo_<timestamp>` (`make_run_id()`; pass
`--run_name <tag>` to `train.py` to label it). List the run to get its exact
name and find your checkpoints:

```bash
ls /workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/
ls /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/<run_id>/train/
```

Checkpoints are named `model_<iteration>.pt`, saved every 50 iterations plus
one final save — pick the highest-numbered file. See
[`../explanation/run-id-tree-design.md`](../explanation/run-id-tree-design.md)
for why the two trees exist, and the `run_id / group / campaign` entry in the
[glossary](../reference/glossary.md) for the naming scheme.

## 3. Evaluate the checkpoint

The required evaluator is `eval.py static` — a text metric summary is not a
substitute. Point `--checkpoint` at the checkpoint through the
`experiments/.../train/` symlink (not the raw `logs/` path) and **do not
pass `--output_dir`** — both are load-bearing for where the output lands:

```bash
cd /workspace/constrained-albc && python constrained_albc/analysis/eval.py static \
    --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless \
    --checkpoint experiments/rsl_rl/albc_trpo_teacher/<run_id>/train/model_<N>.pt
```

Output lands at
`experiments/rsl_rl/albc_trpo_teacher/<run_id>/eval/static_<eval_ts>/`.
Passing `--output_dir` explicitly, or pointing `--checkpoint` at the raw
`logs/` path, both skip this auto-resolution and scatter the output
elsewhere — see `.claude/rules/03-analysis-quality.md` for the two pitfalls
in detail.

## 4. Reading the output plots

`eval.py static` sweeps 4 fixed DR levels — `none` / `soft` / `medium` /
`hard` (see the "DR" entry in the [glossary](../reference/glossary.md)) —
and writes one PNG per plot, one row per level:

| File | Content |
|---|---|
| `traj_attitude.png` | roll/pitch tracking trajectory |
| `traj_yaw.png` | yaw-rate tracking trajectory |
| `traj_error.png` | tracking error over time |
| `summary_attitude.png`, `summary_yaw.png` | per-level steady-state metric bars |
| `summary_failuretime.png` | time-to-failure summary |

The default task is attitude-only, so `traj_linvel.png` /
`summary_linvel.png` are **not** produced for it — those only appear when
evaluating a linear-velocity-tracking task (e.g. the legacy
`Isaac-ConstrainedALBC-Full-*` tasks).

Each trajectory plot draws two lines per level: the across-env **mean**, and
a dashed **sample** line for one representative env (the median-attitude-error
env, picked once and reused across every panel). A sample line that tracks
the mean closely means the policy's axes are correlated; a diverging sample
line means that env does much better or worse on one axis than the others.
See `.claude/rules/03-analysis-quality.md` ("Sample Env Plot Divergence
Explained") for the full diagnostic reading.

View a plot with the Read tool, or open the PNG directly — evaluation in
this repository requires visually inspecting the plots, not just the summary
numbers.
