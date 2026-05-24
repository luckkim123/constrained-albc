# constrained-albc

**Private research: constrained full-DOF ALBC for underwater vehicles. Not for distribution.**

This is the top layer of a three-repo research stack:

```
isaaclab  (GPU sim core, clean fork)
    └── marinelab  (public: BlueROV2 + UUV assets, marine physics)
            └── constrained-albc  (this repo, private)
```

`constrained-albc` adds the research-specific stack on top of `marinelab`:
- Constrained full-DOF ALBC (TRPO + IPO + asymmetric encoder)
- TDC-augmented variant
- Student distillation (TCN / GRU)
- Analysis and evaluation tooling

## Registered environments

| Task ID | Description |
|---|---|
| `Isaac-FullDOF-TRPO-v0` | **Main** — ConstraintTRPO + IPO + asymmetric encoder, DORAEMON DR |
| `Isaac-FullDOF-NoEncoder-v0` | TRPO + IPO, no encoder (ablation) |
| `Isaac-FullDOF-PPO-v0` | Unconstrained PPO baseline |
| `Isaac-FullDOF-TRPO-NoIPO-v0` | TRPO without IPO barrier (ablation) |
| `Isaac-FullDOF-PPO-Enc-v0` | PPO with asymmetric encoder |
| `Isaac-FullDOF-TDC-v0` | TDC controller variant |

## Install

Three-layer install order — see [`docs/installation.md`](docs/installation.md) for the full sequence.

Short form:

```bash
# 1. isaaclab (GPU sim base — already installed in Docker)
# 2. marinelab
cd /workspace/isaaclab && ./isaaclab.sh -p -m pip install -e /workspace/marinelab
# 3. this repo
cd /workspace/isaaclab && ./isaaclab.sh -p -m pip install -e /workspace/constrained-albc
```

> **RSL-RL fork required.** This repo needs a forked `rsl_rl` and forked `isaaclab_rl`
> (custom ctor kwargs + encoder-LR param groups). A stock `rsl-rl-lib` from PyPI will fail.
> See [`docs/architecture.md`](docs/architecture.md) for the exact fields and why they matter.

## Quickstart: training

Training uses Isaac Lab's shared `train.py` entry point:

```bash
cd /workspace/isaaclab
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --task Isaac-FullDOF-TRPO-v0 \
    --num_envs 4096 --max_iterations 5000 \
    --logger wandb --log_project_name full_dof_trpo
```

Student distillation has its own entry point:

```bash
cd /workspace/constrained-albc
/workspace/isaaclab/isaaclab.sh -p scripts/train_student.py --help
# or use the launcher scripts:
bash scripts/launch_student_tcn.sh
bash scripts/launch_student_gru.sh
```

## Quickstart: evaluation

Full-DOF evaluation **must** use `eval_dr.py static` and produces PNG plots:

```bash
cd /workspace/isaaclab
./isaaclab.sh -p /workspace/constrained-albc/constrained_albc/analysis/eval_dr.py static \
    --task Isaac-FullDOF-TRPO-v0 --num_envs 64 --headless
```

Other DR modes: `periodic`, `segmented`, `sudden`.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for:
- Package layout (envs / analysis / scripts / tests)
- RSL-RL fork dependency details
