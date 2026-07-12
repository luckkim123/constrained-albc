<div align="center">

# constrained-albc

**Constraint-aware reinforcement learning for an underwater vehicle-manipulator system on NVIDIA Isaac Lab.**

![python](https://img.shields.io/badge/python-3.10%2B-blue)
![isaac-sim](https://img.shields.io/badge/Isaac%20Sim-5.1.0-76b900)
![status](https://img.shields.io/badge/status-private%20research-red)

[Documentation](docs/README.md) | [Getting Started](#getting-started) | [Architecture](docs/architecture.md)

</div>

> Private, unpublished research code. Not licensed for distribution or use. See [LICENSE](LICENSE).

## Overview

`constrained-albc` is the top layer of a three-repo research stack for 6-DOF underwater
vehicle-manipulator (UUV) reinforcement learning. It trains an attitude-only arm-linked
buoyancy control (ALBC) teacher policy with ConstraintTRPO (TRPO + IPO interior-point
constraints), an asymmetric critic, and a privileged-observation encoder, then distills
the teacher into a deployable TCN/GRU student.

```
isaaclab   (GPU sim core — pristine upstream fork)
   └── marinelab   (public: marine physics + UUV assets + BlueROV tasks)
          └── constrained-albc   (this repo — private research overlay)
```

## Key Features

- **ConstraintTRPO + IPO**: constrained policy optimization with interior-point barriers, on stock `rsl-rl-lib` (no fork — `ConstraintTRPO` is a standalone algorithm).
- **Asymmetric privileged encoder**: 69D actor observation, 28D privileged observation encoded to a 9D latent for the critic path.
- **DORAEMON domain randomization**: entropy-scheduled DR curriculum over hydrodynamics, thruster, latency, and observation-noise dimensions.
- **Teacher-student distillation**: TCN/GRU students recover the privileged latent from onboard history for deployment.
- **Evaluation and analysis suite**: `eval.py` static/periodic/segmented modes with per-env heavy-tail and CV diagnostics, PNG reports.

## Getting Started

### Prerequisites

- Isaac Sim 5.1.0 with Isaac Lab installed (the project Docker image provides both)
- [marinelab](../marinelab) installed into the Isaac Lab environment
- NVIDIA GPU, Python 3.10+ (the Isaac Sim interpreter)

### Installation

Three-layer install order is strict — `isaaclab -> marinelab -> constrained-albc`.
See [docs/installation.md](docs/installation.md) for the full sequence.

```bash
cd /workspace/isaaclab
./isaaclab.sh -p -m pip install -e /workspace/marinelab
./isaaclab.sh -p -m pip install -e /workspace/constrained-albc
```

> Every script must run through the Isaac Sim interpreter (`./isaaclab.sh -p`, or the
> container's `python` wrapper). Plain system Python cannot find Isaac Sim modules.

### Quick Start

Train the main task with the overlay-owned entry point (`isaaclab` stays a pristine
fork; env registration and the `ConstraintEncoderRunner` dispatch live here):

```bash
cd /workspace/isaaclab
./isaaclab.sh -p /workspace/constrained-albc/scripts/train.py \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --num_envs 4096 --max_iterations 5000 \
    --logger wandb --log_project_name albc_trpo
```

Evaluate (produces PNG plots; other modes: `periodic`, `segmented`):

```bash
./isaaclab.sh -p /workspace/constrained-albc/constrained_albc/analysis/eval.py static \
    --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless
```

New here? Follow the end-to-end walkthrough in
[docs/tutorials/getting-started.md](docs/tutorials/getting-started.md).

<details>
<summary><strong>Student distillation and student evaluation</strong></summary>

Student distillation has its own overlay entry point. Run TCN then GRU;
`--teacher_run_dir` points at the teacher's run through the
`experiments/.../train` symlink so the student manifest links to the teacher.
Hyperparameters are CLI flags — pass only what differs from the defaults.

```bash
cd /workspace/isaaclab
CUDA_VISIBLE_DEVICES=1 ./isaaclab.sh -p /workspace/constrained-albc/scripts/train_student.py \
    --encoder_type tcn \
    --teacher_run_dir /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/<run_id>/train \
    --num_envs 2048 --wandb_project constrained_albc_student --headless
```

A distilled student is evaluated through the same `static` path
(teacher-comparable, plus the l_hat/l_true encoder diagnostic):

```bash
./isaaclab.sh -p /workspace/constrained-albc/constrained_albc/analysis/eval.py static \
    --teacher_ckpt experiments/rsl_rl/albc_trpo_teacher/<run_id>/train/model_4999.pt \
    --student_ckpt experiments/rsl_rl/albc_trpo_student/<run_id>/train/models/student_999.pt \
    --encoder_type tcn --num_envs 64 --headless
```

</details>

## Registered Tasks

The default task is `Isaac-ConstrainedALBC-TRPO-v0` (attitude-only, `envs/main`).
The full list of 7 task IDs, their env packages, and status is maintained in
[docs/reference/task-reference.md](docs/reference/task-reference.md).

<details>
<summary><strong>Task table</strong></summary>

| Task ID | Description |
|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | **Main** — attitude-only ALBC (`envs/main`), ConstraintTRPO + IPO + asymmetric encoder, DORAEMON DR |
| `Isaac-ConstrainedALBC-Full-TRPO-v0` | Legacy full-DOF (`envs/full_dof`) — velocity + attitude |
| `Isaac-ConstrainedALBC-Full-NoEncoder-v0` | Full-DOF TRPO + IPO, no encoder (ablation) |
| `Isaac-ConstrainedALBC-Full-PPO-v0` | Full-DOF unconstrained PPO baseline |
| `Isaac-ConstrainedALBC-Full-TRPO-NoIPO-v0` | Full-DOF TRPO without IPO barrier (ablation) |
| `Isaac-ConstrainedALBC-Full-PPO-Enc-v0` | Full-DOF PPO with asymmetric encoder |
| `Isaac-ConstrainedALBC-TDC-v0` | TDC controller variant (`envs/tdc`) |

</details>

## Project Structure

```
constrained-albc/
├── constrained_albc/
│   ├── envs/          # main (default), full_dof (legacy), tdc — env + algorithm variants
│   └── analysis/      # eval.py, analyze.py, encoder tools, plotting
├── scripts/           # overlay-owned entry points: train.py, play.py, train_student.py
├── docs/              # tutorials / how-to / reference / explanation (Diátaxis)
├── experiments/       # run index tree (results SSOT; heavy data lives in logs/)
└── tests/             # no-Isaac unit tests
```

## Documentation

Start at the [documentation index](docs/README.md). Reference pages are the single
source of truth for dimensions, task IDs, and config values; the network architecture
is documented in
[docs/reference/main-network-architecture.md](docs/reference/main-network-architecture.md).

## License

Private research — all rights reserved. See [LICENSE](LICENSE). Not for distribution.
