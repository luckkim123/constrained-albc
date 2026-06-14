# constrained-albc

**Private research: constrained ALBC for underwater vehicles. Not for distribution.**

This is the top layer of a three-repo research stack:

```
isaaclab  (GPU sim core, clean fork)
    └── marinelab  (public: BlueROV2 + UUV assets, marine physics)
            └── constrained-albc  (this repo, private)
```

`constrained-albc` adds the research-specific stack on top of `marinelab`:
- Constrained ALBC (TRPO + IPO + asymmetric encoder) — attitude-only main task, plus legacy full-DOF variants
- TDC-augmented variant
- Student distillation (TCN / GRU)
- Analysis and evaluation tooling

## Registered environments

| Task ID | Description |
|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | **Main** — attitude-only ALBC (`envs/main`), ConstraintTRPO + IPO + asymmetric encoder, DORAEMON DR |
| `Isaac-ConstrainedALBC-Full-TRPO-v0` | Legacy full-DOF (`envs/full_dof`) — velocity + attitude |
| `Isaac-ConstrainedALBC-Full-NoEncoder-v0` | Full-DOF TRPO + IPO, no encoder (ablation) |
| `Isaac-ConstrainedALBC-Full-PPO-v0` | Full-DOF unconstrained PPO baseline |
| `Isaac-ConstrainedALBC-Full-TRPO-NoIPO-v0` | Full-DOF TRPO without IPO barrier (ablation) |
| `Isaac-ConstrainedALBC-Full-PPO-Enc-v0` | Full-DOF PPO with asymmetric encoder |
| `Isaac-ConstrainedALBC-TDC-v0` | TDC controller variant (`envs/tdc`) |

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

> **Stock RSL-RL, no fork.** This repo runs on stock `rsl-rl-lib==3.1.2` and stock
> `isaaclab_rl`. `ConstraintTRPO` is a standalone algorithm (it does not subclass
> `rsl_rl.PPO`), so no forked `rsl_rl` is needed.
> See [`docs/architecture.md`](docs/architecture.md) for why.

## Quickstart: training

Training uses the **overlay-owned** entry point. `isaaclab` stays a pristine
upstream fork, so its stock `train.py` does not know the `Isaac-ConstrainedALBC-*`
tasks — the overlay entry owns env registration (`import constrained_albc`) and the
custom runner dispatch (`ConstraintEncoderRunner`):

```bash
cd /workspace/isaaclab
./isaaclab.sh -p /workspace/constrained-albc/scripts/train.py \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --num_envs 4096 --max_iterations 5000 \
    --logger wandb --log_project_name albc_trpo
```

Student distillation has its own overlay entry point. Run it directly (TCN then GRU);
`--teacher_run_dir` points at the teacher's run (use the `experiments/.../train` symlink
so the student manifest links to the teacher). Hyperparameters are CLI flags — pass only
what differs from the defaults (`--help` lists them):

```bash
cd /workspace/isaaclab
CUDA_VISIBLE_DEVICES=1 ./isaaclab.sh -p /workspace/constrained-albc/scripts/train_student.py \
    --encoder_type tcn \
    --teacher_run_dir /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/<run_id>/train \
    --num_envs 2048 --wandb_project constrained_albc_student --headless
# then repeat with --encoder_type gru
```

## Quickstart: evaluation

Evaluation of the main task **must** use `eval.py static` and produces PNG plots:

```bash
cd /workspace/isaaclab
./isaaclab.sh -p /workspace/constrained-albc/constrained_albc/analysis/eval.py static \
    --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless
```

A distilled student is evaluated through the same `static` path (teacher-comparable,
+ the l_hat/l_true encoder diagnostic) by adding student flags:

```bash
./isaaclab.sh -p /workspace/constrained-albc/constrained_albc/analysis/eval.py static \
    --teacher_ckpt experiments/rsl_rl/albc_trpo_teacher/<run_id>/train/model_4999.pt \
    --student_ckpt experiments/rsl_rl/albc_trpo_student/<run_id>/train/models/student_999.pt \
    --encoder_type tcn --num_envs 64 --headless
```

Other DR modes: `periodic`, `segmented`, `sudden`.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for:
- Package layout (envs / analysis / scripts / tests)
- RSL-RL fork dependency details

The main task's network architecture (encoder / actor / asymmetric critic /
ConstraintTRPO) is documented in
[`docs/reference/main-network-architecture.md`](docs/reference/main-network-architecture.md).
