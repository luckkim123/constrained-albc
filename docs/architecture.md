# constrained-albc Architecture

## Overview

### Three-layer dependency

```
isaaclab          (GPU sim core: Isaac Sim 5.1.0, stock RSL-RL, stock isaaclab_rl)
    |
    v
marinelab         (public overlay: BlueROV2/ALBC assets, marine physics)
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
| `constrained_albc/envs/` | RL environments: `main` (attitude-only ALBC, TRPO+IPO+encoder — the default), `full_dof` (legacy full-DOF variants), and `tdc` (TDC controller variant) |
| `constrained_albc/analysis/` | Evaluation and training-analysis tooling: `eval.py` (live evaluator entry point, ~2100 lines, 3 sub-modes: `static` / `periodic` / `segmented`; `static` is the required mode for `Isaac-ConstrainedALBC-TRPO-v0`, and accepts `--student_ckpt`/`--teacher_ckpt`/`--encoder_type` to evaluate a distilled student through the same path, also emitting the l_hat/l_true encoder-fidelity diagnostic), backed by the pure-numpy, Isaac-Sim-free `_eval_dr/` package (trajectory + metrics); post-hoc tooling `analyze.py`, `compare.py`, `monitor.py`, `encoder_tools.py` (thin CLIs backed by the `_analyze/` and `_encoder/` packages), shared `common` and `cli_args` |
| `scripts/` | Entry points: `train.py` (teacher), `train_student.py` (distillation), `play.py` (policy playback), `export_deploy.py` (packaged teacher+student deploy export). Run directly via `isaaclab.sh -p` — no wrapper shell scripts |
| `tests/` | Unit tests spanning dimension contracts, DR/DORAEMON, constraints, encoder/priv-obs bounds, eval metrics, TDC controller, and deploy-pack export (`tests/deploy/`); most run sim-free, a subset mocks `omni`/`pxr`/`carb`/`warp` directly |

### Registered task IDs

| Task ID | Env dir | Description |
|---|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | `envs/main` | **Main** — attitude-only ALBC, ConstraintTRPO + IPO + asymmetric encoder, DORAEMON DR. 69D obs / 28D privileged / 8D action |
| `Isaac-ConstrainedALBC-Full-TRPO-v0` | `envs/full_dof` | Legacy full-DOF (velocity + attitude, 87D obs); kept for future full-DOF experiments |
| `Isaac-ConstrainedALBC-Full-NoEncoder-v0` | `envs/full_dof` | Full-DOF TRPO + IPO, no encoder (ablation) |
| `Isaac-ConstrainedALBC-Full-PPO-v0` | `envs/full_dof` | Full-DOF unconstrained PPO baseline |
| `Isaac-ConstrainedALBC-Full-TRPO-NoIPO-v0` | `envs/full_dof` | Full-DOF TRPO without IPO barrier (ablation) |
| `Isaac-ConstrainedALBC-Full-PPO-Enc-v0` | `envs/full_dof` | Full-DOF PPO with asymmetric encoder |
| `Isaac-ConstrainedALBC-TDC-v0` | `envs/tdc` | TDC controller variant (inherits full_dof) |

The network architecture of the default `Isaac-ConstrainedALBC-TRPO-v0` is
documented in [`docs/reference/main-network-architecture.md`](reference/main-network-architecture.md).

---

## RSL-RL dependency (stock, no fork)

constrained-albc runs on **stock `rsl-rl-lib==3.1.2`** and **stock `isaaclab_rl`**.
There are no forks: a fresh-machine install is `pip install rsl-rl-lib==3.1.2` plus
the clean isaaclab fork-point checkout.

The main pipeline does not subclass stock rsl_rl. `Isaac-ConstrainedALBC-TRPO-v0` uses:
- `ConstraintTRPO` — a standalone algorithm (own `optim.Adam`), NOT an `rsl_rl.PPO`
  subclass. Injected into `rsl_rl.runners.on_policy_runner`'s namespace by the overlay
  runner so `OnPolicyRunner`'s `eval(class_name)` resolves it.
- `ActorCriticEncoder(PolicyBase)` — a custom policy base, NOT `rsl_rl.ActorCritic`.

The PPO ablations (`Isaac-ConstrainedALBC-Full-PPO-v0`,
`Isaac-ConstrainedALBC-Full-PPO-Enc-v0`) use stock `rsl_rl.PPO` with
`class_name="PPO"`; they set only stock algorithm fields.

Notes on fields that previously looked fork-specific:
- `state_dependent_std` is a STOCK `RslRlPpoActorCriticCfg` field (present upstream at
  the fork point). The main `envs/main` policy cfg (`_ALBCPolicyCfg`) does not define
  it at all — its std is a single global `log_std` parameter (see the network
  reference). A per-state std head exists only in the unmerged `exp/attitude-only-state-std`
  experiment branch.
- `weight_decay` was a former local addition to `RslRlPpoAlgorithmCfg`; it has been
  removed. The PPO ablation never set it, so stock PPO (which lacks the kwarg) is
  fully compatible.
