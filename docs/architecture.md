# constrained-albc Architecture

## Overview

### Three-layer dependency

```
isaaclab          (GPU sim core: Isaac Sim 5.1.0, stock RSL-RL, stock isaaclab_rl)
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
| `constrained_albc/analysis/` | Evaluation and training-analysis tooling: `eval_dr` (single ~4000-line module, 4 sub-modes: `static` / `periodic` / `segmented` / `sudden`; `static` is the required mode for `Isaac-FullDOF-TRPO-v0`), `eval_student`, `analyze`, `compare`, `monitor`, `encoder_tools`, shared `common` and `cli_args` |
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

## RSL-RL dependency (stock, no fork)

constrained-albc runs on **stock `rsl-rl-lib==3.1.2`** and **stock `isaaclab_rl`**.
There are no forks: a fresh-machine install is `pip install rsl-rl-lib==3.1.2` plus
the clean isaaclab fork-point checkout.

The main pipeline does not subclass stock rsl_rl. `Isaac-FullDOF-TRPO-v0` uses:
- `ConstraintTRPO` — a standalone algorithm (own `optim.Adam`), NOT an `rsl_rl.PPO`
  subclass. Injected into `rsl_rl.runners.on_policy_runner`'s namespace by the overlay
  runner so `OnPolicyRunner`'s `eval(class_name)` resolves it.
- `ActorCriticEncoder(PolicyBase)` — a custom policy base, NOT `rsl_rl.ActorCritic`.

The PPO ablations (`Isaac-FullDOF-PPO-v0`, `Isaac-FullDOF-PPO-Enc-v0`) use stock
`rsl_rl.PPO` with `class_name="PPO"`; they set only stock algorithm fields.

Notes on fields that previously looked fork-specific:
- `state_dependent_std` is a STOCK `RslRlPpoActorCriticCfg` field (present upstream at
  the fork point); our cfgs do not set it.
- `weight_decay` was a former local addition to `RslRlPpoAlgorithmCfg`; it has been
  removed. The PPO ablation never set it, so stock PPO (which lacks the kwarg) is
  fully compatible.
