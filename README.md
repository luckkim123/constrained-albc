<div align="center">

# constrained-albc

**Training and evaluation code for "Underwater Mini-ROV Manipulation via Active Link Buoyancy
Control with Sim-to-Real Reinforcement Learning".**

![python](https://img.shields.io/badge/python-3.10%2B-blue)
![isaac-sim](https://img.shields.io/badge/Isaac%20Sim-5.1.0-76b900)
![license](https://img.shields.io/badge/license-MIT-green)

[Documentation](docs/README.md) | [Reproducing the paper](#reproducing-the-paper) | [Architecture](docs/architecture.md)

</div>

## Overview

A mini-ROV carries a two-joint arm whose buoyant element, repositioned by the arm, holds roll
and pitch against an unknown payload moment. This repository trains the attitude controller
for that vehicle in NVIDIA Isaac Lab and exports it for the onboard runtime.

- **Teacher.** ConstraintTRPO (TRPO with an interior-point log-barrier on ten cost budgets)
  with an asymmetric critic and a privileged encoder: a 72D observation and 28 privileged
  inputs compressed to a 9D latent; the action is 8D (two arm joints, six thrusters).
  Domain randomization follows the DORAEMON curriculum.
- **Student.** A GRU encoder distilled to predict the latent from the observation history
  alone, deployed with the teacher's policy at 50 Hz.
- **Deploy.** A torch-free pack (numpy weights, CPU goldens, parity self-check, sha256
  manifest) for the board runtime.

```
isaaclab   (GPU sim core — upstream)
   └── marinelab   (marine physics, UUV assets)
          └── constrained-albc   (this repo — ALBC tasks, training, evaluation, export)
```

## Getting Started

### Prerequisites

- Isaac Sim 5.1.0 with Isaac Lab
- [marinelab](https://github.com/luckkim123/marinelab) installed into the Isaac Lab environment
- NVIDIA GPU, Python 3.10+ (the Isaac Sim interpreter)

### Installation

The install order is `isaaclab -> marinelab -> constrained-albc`; see
[docs/installation.md](docs/installation.md).

```bash
cd /workspace/isaaclab
./isaaclab.sh -p -m pip install -e /workspace/marinelab
./isaaclab.sh -p -m pip install -e /workspace/constrained-albc
```

Every script runs through the Isaac Sim interpreter (`isaaclab.sh -p`).

## Reproducing the paper

The paper's controller is trained on the section-5 plant task
`Isaac-ConstrainedALBC-TRPO-SimToReal-v0`. Run every command below from the repository root,
with `ISAACLAB_SH` pointing at Isaac Lab's launcher:

```bash
cd /path/to/constrained-albc
export ISAACLAB_SH=/path/to/isaaclab/isaaclab.sh
```

**1. Teacher.**

```bash
"$ISAACLAB_SH" -p scripts/train.py --task Isaac-ConstrainedALBC-TRPO-SimToReal-v0 \
    --num_envs 4096 --headless --seed 30 --run_group <campaign>
```

The paper teacher (`trpo_rr_FTP_s30_260927_182609`, `model_7200`) was trained with, among other
overrides, `env.reward.k_sstv=-5.0 env.reward.sstv_start_step=125`,
`env.randomization.obs_delay_steps=[0,5]` and `env.randomization.control_delay_steps=[7,13]`.
Its full resolved configuration is the run's `params/env.yaml`
(`experiments/paper/ckpt/proposed_teacher_s30_7200/params/env.yaml` in the project data
tree). The training randomization ranges live in code: `constrained_albc/envs/main/config.py`
(`DomainRandomizationCfg`), `config_simtoreal.py`, and the DORAEMON dimension table
`constrained_albc/envs/main/doraemon.py`.

`scripts/paper/train_teacher.sh` is the paper teacher's training run with its complete set of
overrides. It is a fine-tune: it resumes from a starting teacher checkpoint (`model_6400` with
its `doraemon_state.pt`) for 801 iterations and is run as
`RESUME_CKPT=<model_6400.pt> OUT_DIR=<dir> ARMED=1 scripts/paper/train_teacher.sh`.
That starting checkpoint and the training chain that produced it are not released.

**2. Student (GRU).**

`scripts/paper/train_student.sh` is the paper student's distillation run with its complete set
of arguments, including the DAgger schedule (teacher-action probability annealed 1 -> 0 over
600 iterations, `--dagger_mix select`):

```bash
TEACHER_CKPT=<teacher run>/model_7200.pt OUT_DIR=<dir> ARMED=1 scripts/paper/train_student.sh
```

**3. Evaluate.**

```bash
"$ISAACLAB_SH" -p constrained_albc/analysis/eval.py static \
    --task Isaac-ConstrainedALBC-TRPO-SimToReal-v0 --num_envs 64 --headless \
    --teacher_ckpt <teacher .pt> --student_ckpt <student .pt> --encoder_type gru
```

**4. Export the deploy pack.**

```bash
"$ISAACLAB_SH" -p scripts/export_deploy_pack.py --batch attitude_only_5000 \
    --student-ckpt <student .pt> --teacher-ckpt <teacher .pt> \
    --run-group <campaign> --tag pack_<label> --device cpu --golden --report
```

The paper's pack is `pack_rr_ft_ftp7200_s30_gru_260927_193819`; see
[docs/how-to/deploy.md](docs/how-to/deploy.md) and
[docs/how-to/deploy-pack-export.md](docs/how-to/deploy-pack-export.md).

**Ablations and figures.** `tools/compare_arms.py` builds the ablation comparison from a
manifest of arms; `tools/paper_figures.py` renders tables and figures from evaluation
outputs.

## Registered Tasks

| Task ID | Description |
|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | ConstraintTRPO + IPO + asymmetric encoder, DORAEMON DR (`envs/main`) |
| `Isaac-ConstrainedALBC-{NoEncoder,PPO,TRPO-NoIPO,PPO-Enc}-v0` | Ablation arms of the above |
| `Isaac-ConstrainedALBC-*-SimToReal-v0` | The same arms on the section-5 plant (`envs/main/config_simtoreal.py`); `TRPO-NoIPO-NoEncoder` exists only here |
| `Isaac-ConstrainedALBC-Main-{TDC,PID}-v0` | Classical-control baselines, no RL training (`envs/tdc_main`) |

Details: [docs/reference/task-reference.md](docs/reference/task-reference.md).

## Project Structure

```
constrained-albc/
├── constrained_albc/
│   ├── algorithms/    # ConstraintTRPO, encoder actor-critic, runners, student distillation
│   ├── envs/          # main (RL tasks), tdc_main (TDC / PID baselines)
│   ├── analysis/      # eval.py and sim-free metric/plot helpers
│   └── deploy/        # torch -> numpy export, goldens, pack
├── scripts/           # train.py, train_student.py, play.py, export_deploy_pack.py
├── tools/             # compare_arms.py, paper_figures.py
├── docs/              # tutorials / how-to / reference / explanation
└── tests/             # unit tests that run without Isaac Sim
```

## Tests

The unit tests need no simulator and no GPU; run them from the repo root with the Isaac Sim
interpreter:

```bash
CUDA_VISIBLE_DEVICES= "$ISAACLAB_SH" -p -m pytest -q tests --ignore=tests/test_simtoreal_cfg.py
```

- `tests/test_simtoreal_cfg.py` boots Kit through `AppLauncher` and needs a GPU; run it on its
  own (`"$ISAACLAB_SH" -p tests/test_simtoreal_cfg.py`).
- `tests/test_eval_adapter.py` and `tests/test_encoder_adapter.py` exercise a local analysis
  profile that is not part of this repository, so they are skipped in a fresh clone.
- Known failures: `tests/test_doraemon.py` (collection error) and two tests in
  `tests/test_fault_dr.py` import `marinelab.algorithms.doraemon`, which the current marinelab
  release does not provide. They are not fixed here.

## License

MIT, see [LICENSE](LICENSE). Files carrying the Isaac Lab Project Developers copyright header
remain under Isaac Lab's BSD-3-Clause license, reproduced in the same file.
