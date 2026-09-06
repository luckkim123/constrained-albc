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

## Registered tasks

> The registry holds **17** ids: 13 from `constrained_albc/envs/main/__init__.py`
> (each RL variant below plus its `-SimToReal-v0` arm, and `TRPO-NoIPO-NoEncoder`) and 4 from
> `constrained_albc/envs/tdc_main/__init__.py` (`Main-TDC`, `Main-PID`, `Main-ATDC`,
> `Main-ResidualTDC-SimToReal`). The table lists the RL teacher variants; enumerate the live set
> with the snippet in [`installation.md`](../installation.md).

`envs/main` obs is **72D**, not the 69D its cfg source declares: `use_bias_ema_obs` has been
ON since 2026-07-16 and appends the 3D bias-EMA at cfg-construction time. Runners resolve
this through `sync_policy_obs_dim`; a hardcoded 69 in an agent cfg aborts the run.

| Task ID | Env package | Obs dim (policy / privileged / action) | Purpose / status | Typical entry command |
|---|---|---|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | `envs/main` | 72D / 28D / 8D | **Default.** Attitude-only ALBC (roll/pitch attitude + yaw-rate, no lin_vel tracking). ConstraintTRPO + IPO + asymmetric encoder. | `python scripts/train.py --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 4096 --max_iterations 5000 --logger wandb --log_project_name albc_trpo` |
| `Isaac-ConstrainedALBC-NoEncoder-v0` | `envs/main` | 72D / 28D / 8D | Ablation baseline 1 — TRPO + IPO, encoder removed (DR/reward/constraints unchanged). | `python scripts/train.py --task Isaac-ConstrainedALBC-NoEncoder-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-PPO-v0` | `envs/main` | 72D / 28D / 8D | Ablation baseline 2 — standard PPO + asymmetric critic, no encoder, no IPO constraint. | `python scripts/train.py --task Isaac-ConstrainedALBC-PPO-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-TRPO-NoIPO-v0` | `envs/main` | 72D / 28D / 8D | Ablation variant 3 — encoder + TRPO with the IPO barrier disabled (empty constraint list). | `python scripts/train.py --task Isaac-ConstrainedALBC-TRPO-NoIPO-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |
| `Isaac-ConstrainedALBC-PPO-Enc-v0` | `envs/main` | 72D / 28D / 8D | Ablation variant 4 — encoder + standard PPO, no IPO. | `python scripts/train.py --task Isaac-ConstrainedALBC-PPO-Enc-v0 --num_envs 4096 --logger wandb --log_project_name albc_ablation` |

Notes:
- All `python` invocations above run through the workspace's Isaac Sim `python`
  wrapper (or `./isaaclab.sh -p` from `/workspace/isaaclab`) — see
  [`installation.md`](../installation.md).
- The classical-control baselines (`Isaac-ConstrainedALBC-Main-{TDC,PID,ATDC}-v0`,
  `-Main-ResidualTDC-SimToReal-v0`) live in `envs/tdc_main` and keep the 8D action
  space only so observation history and downstream scripts stay compatible with the
  RL variants; the env overwrites the action with the controller's output.
- Every RL id above also has a `-SimToReal-v0` arm, and `TRPO-Lagrangian` and
  `TRPO-NoIPO-NoEncoder` exist as SimToReal-only arms. The `-SimToReal-v0` arms use the section-5 plant
  (`envs/main/config_simtoreal.py`); the plain ids keep the pre-2026-09 plant.
- The legacy full-DOF family (`envs/full_dof`, `envs/tdc`, `Isaac-ConstrainedALBC-Full-*` and `-TDC-v0`) was removed in the 2026-09 cleanup; recover it from tag `legacy-full-dof-final`.
