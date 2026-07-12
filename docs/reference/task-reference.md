# Task Reference

> **Scope**: Every `Isaac-ConstrainedALBC-*` task ID registered by this repo — one
> row each, with the owning env package, observation/privileged/action dims, and a
> typical launch command. This is the **single place task IDs are enumerated**;
> other docs (`README.md`, `docs/architecture.md`, `docs/installation.md`) should
> link here rather than repeat the list. Verified against
> `constrained_albc/envs/__init__.py` and each env package's `__init__.py` /
> `config.py` (2026-07-12).
>
> For the full breakdown of the default task's 69D/28D dims (per-field indices,
> noise model, encoder consumption), see
> [`observation-space.md`](observation-space.md) — this page only gives the
> top-level numbers.

## Registered tasks (7)

| Task ID | Env package | Obs dim (policy / privileged / action) | Purpose / status | Typical entry command |
|---|---|---|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | `envs/main` | 69D / 28D / 8D | **Default.** Attitude-only ALBC (roll/pitch attitude + yaw-rate, no lin_vel tracking). ConstraintTRPO + IPO + asymmetric encoder. | `python scripts/train.py --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 4096 --max_iterations 5000 --logger wandb --log_project_name albc_trpo` |
| `Isaac-ConstrainedALBC-Full-TRPO-v0` | `envs/full_dof` | 87D / 24D / 8D | Legacy. Full 6-DOF (velocity + attitude) tracking, same algorithm as the default (production reference for full-DOF experiments). | `python scripts/train.py --task Isaac-ConstrainedALBC-Full-TRPO-v0 --num_envs 4096 --max_iterations 5000 --logger wandb --log_project_name albc_trpo` |
| `Isaac-ConstrainedALBC-Full-NoEncoder-v0` | `envs/full_dof` | 87D / 24D / 8D | Legacy ablation baseline 1 — TRPO + IPO, encoder removed (DR/reward/constraints unchanged). | `python scripts/train.py --task Isaac-ConstrainedALBC-Full-NoEncoder-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-Full-PPO-v0` | `envs/full_dof` | 87D / 24D / 8D | Legacy ablation baseline 2 — standard PPO + asymmetric critic, no encoder, no IPO constraint. | `python scripts/train.py --task Isaac-ConstrainedALBC-Full-PPO-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-Full-TRPO-NoIPO-v0` | `envs/full_dof` | 87D / 24D / 8D | Legacy ablation variant 3 — encoder + TRPO with the IPO barrier disabled (empty constraint list). | `python scripts/train.py --task Isaac-ConstrainedALBC-Full-TRPO-NoIPO-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-Full-PPO-Enc-v0` | `envs/full_dof` | 87D / 24D / 8D | Legacy ablation variant 4 — encoder + standard PPO, no IPO. | `python scripts/train.py --task Isaac-ConstrainedALBC-Full-PPO-Enc-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-TDC-v0` | `envs/tdc` | 87D / 24D / 8D (action ignored) | TDC + thruster-PD classical-control baseline — **no RL training**; same env/DR/reward as `Full-TRPO-v0` for a directly comparable evaluation. | `python constrained_albc/analysis/eval.py static --task Isaac-ConstrainedALBC-TDC-v0 --num_envs 64 --headless` |

Notes:
- All `python` invocations above run through the workspace's Isaac Sim `python`
  wrapper (or `./isaaclab.sh -p` from `/workspace/isaaclab`) — see
  [`installation.md`](../installation.md).
- `Isaac-ConstrainedALBC-TDC-v0`'s 8D action space is kept only so observation
  history and downstream scripts stay compatible with the RL variants; the env
  overwrites the action with the classical controller's output
  (`envs/tdc/config.py`).
- `Full-TRPO-NoIPO-v0` and `Full-PPO-Enc-v0` register through
  `config_noconstraint.ALBCNoConstraintEnvCfg`, which inherits `full_dof`'s
  `ALBCEnvCfg` verbatim except for an emptied constraint list — obs/privileged
  dims are identical to the other `full_dof` tasks.
