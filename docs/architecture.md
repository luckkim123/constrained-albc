# constrained-albc Architecture

## Overview

### Three-layer dependency

```
isaaclab          (GPU sim core: Isaac Sim 5.1.0, RSL-RL fork, forked isaaclab_rl)
    |
    v
marinelab         (public overlay: BlueROV2/Hero Agent assets, marine physics)
    |
    v
constrained-albc  (this repo, private: constrained RL envs, student distillation, analysis)
```

Each layer is installed as an editable package into Isaac Lab's bundled Python via
`./isaaclab.sh -p -m pip install -e <path>`. See `docs/installation.md` for the full
sequence.

### Package layout

| Subdirectory | Contents |
|---|---|
| `constrained_albc/envs/` | RL environments: `constrained_full_albc` (TRPO+IPO+encoder, main) and `constrained_full_albc_tdc` (TDC controller variant) |
| `constrained_albc/analysis/` | Evaluation and training-analysis tooling: `eval_dr` (4 DR modes), `eval_student`, `analyze`, `compare`, `monitor`, `encoder_tools`, shared `common` and `cli_args` |
| `scripts/` | Student-distillation entry point (`train_student.py`) and launcher shell scripts |
| `tests/` | Unit tests (TDC controller; Isaac Sim not required) |

### Registered task IDs

| Task ID | Description |
|---|---|
| `Isaac-FullDOF-TRPO-v0` | **Main** — ConstraintTRPO + IPO + asymmetric encoder, DORAEMON DR |
| `Isaac-FullDOF-NoEncoder-v0` | TRPO + IPO, no encoder (ablation) |
| `Isaac-FullDOF-PPO-v0` | Unconstrained PPO baseline |
| `Isaac-FullDOF-TRPO-NoIPO-v0` | TRPO without IPO barrier (ablation) |
| `Isaac-FullDOF-PPO-Enc-v0` | PPO with asymmetric encoder |
| `Isaac-FullDOF-TDC-v0` | TDC controller variant |

---

## RSL-RL cfg dependency

constrained-albc depends on a **forked RSL-RL stack** that ships with Isaac Lab in
this workspace. A fresh-machine install must provide **both** of the following forks;
the upstream/PyPI `rsl-rl-lib` and stock `isaaclab_rl` are insufficient.

### 1. The `isaaclab_rl` fork's cfg fields

The agent config classes in `constrained_albc/.../agents/` set fields that exist only
in the forked `isaaclab_rl` wrapper cfgs:

- `state_dependent_std` in `RslRlPpoActorCriticCfg`
  (`source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py:34`, default `False`).
- `weight_decay` in `RslRlPpoAlgorithmCfg`
  (`source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py:125`, default `0.0`).

Constructing the runner cfg against a stock `isaaclab_rl` raises `TypeError` on these
unknown kwargs.

### 2. The forked `rsl_rl` package itself

Beyond the cfg fields, the runtime depends on a forked `rsl_rl` package with custom
constructor kwargs and encoder-aware learning-rate logic:

- `actor_critic.py` accepts a `state_dependent_std` ctor kwarg and branches on it
  (e.g. `modules/actor_critic.py:32,52,55,81,125`).
- `ppo.py` accepts `encoder_grad_scale` and `use_encoder_update` ctor kwargs
  (`algorithms/ppo.py:43-44`) and builds **separate optimizer param groups for
  encoder vs actor/critic** params (`algorithms/ppo.py:109-123`). This encoder-LR
  separation is required by the asymmetric-encoder training; stock `rsl_rl` puts all
  params in one group and will not honor the encoder learning-rate logic.

### Implication for a fresh install

A clean environment must install both forks (the in-repo `isaaclab_rl` and the forked
`rsl_rl` that ships under Isaac Lab's bundled Python). Installing constrained-albc plus
upstream RSL-RL is **not** enough — the cfg construction and the actor-critic / PPO
constructors will fail or silently lose the encoder-LR behavior.
