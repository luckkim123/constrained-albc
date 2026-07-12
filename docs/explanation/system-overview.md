# System Overview

> **Status**: 2026-07-12 | **Source**: `constrained_albc/envs/main/{albc_env,config}.py`,
> `constrained_albc/envs/__init__.py`, `envs/main/agents/rsl_rl_ppo_cfg.py`, root `README.md`
> (verified against disk; the env code + config are the SSOT for every number below).

Conceptual overview of the default task, `Isaac-ConstrainedALBC-TRPO-v0`
(`constrained_albc/envs/main/`) — attitude-only ALBC. For package layout and the
RSL-RL dependency (stock, no fork) see [`../architecture.md`](../architecture.md);
for the full registered-task table see the [README](../../README.md). The legacy
full-DOF variants (`envs/full_dof/`, 87D obs) and the TDC variant (`envs/tdc/`) are
out of scope here — see the README's task table for those.

## The robot

A UUV that controls attitude with a **buoyancy-actuated arm**: two continuous-rotation
joints reposition a buoyant end link, whose buoyancy generates a restoring torque to
stabilize roll/pitch. Six thrusters (BlueROV T200 parameters, BlueROV2-Heavy-derived
allocation) provide the remaining wrench for surge/sway/heave/yaw and assist attitude.

```
[Main Body] -- joint1 -- [Link1] -- joint2 -- [Link2 / Buoy]
 (9.18 kg, F_buoy~=88N)  (L=0.233m)          (L=0.233m, F_buoy~=26.2N)
```

Main body + buoy buoyancy together slightly exceed total weight — a weak, passive
net-positive stability (`marinelab/assets/albc/albc.py`).

## Env stack

```
Isaac Sim 5.1.0 (Omniverse)
    -> isaaclab            GPU sim core, pristine fork
        -> marinelab       marine physics + UUV/BlueROV assets (public overlay)
            -> constrained-albc   this task: ConstraintTRPO + IPO + encoder (private overlay)
```

Hydrodynamics, the thruster model, and the ALBC/BlueROV asset configs live in
`marinelab.core` / `marinelab.assets`; `constrained-albc` owns the env, reward,
constraints, algorithm, and training/eval entry points. Install order and commands:
root `README.md`.

## Control problem

The policy tracks an **attitude-only** command — no linear-velocity tracking (no
DVL on the real robot):

| Channel | Command | Reward shape |
|---|---|---|
| Roll / Pitch | attitude (±30°) | exponential kernel |
| Yaw | rate (±0.5 rad/s) | quadratic penalty |

Full command-sampling, resampling, and error-integral details:
[`reference/command-and-task.md`](../reference/command-and-task.md).

## Observation, action, privileged observation

The env emits `{"policy": o_t, "privileged": p_t}` per step:

| Tensor | Dim | Composition (high level) |
|---|---:|---|
| Action `a_t` | 8D | 2D arm joint delta + 6D thruster command |
| Observation `o_t` | 69D | 20D current proprioception + 46D strided temporal history + 3D leaky error integral — no measured linear velocity |
| Privileged `p_t` | 28D | one scalar per independent DR parameter (25D: hydro/dynamics/payload/actuator/env/buoy/latency) + measured body linear velocity (3D, critic-only) |

`o_t` is everything the real robot can measure; `p_t` is sim-only ground truth fed
to the encoder and critic, never to the actor — the DVL-free asymmetry that motivates
the teacher/student split below. Full per-dimension tables, code line references, and
the asymmetric actor/critic routing: [`reference/observation-space.md`](../reference/observation-space.md)
(observation axis) and [`reference/action-pipeline.md`](../reference/action-pipeline.md)
(action axis).

## Algorithm

**ConstraintTRPO + IPO** with an asymmetric encoder/critic:

- **Encoder**: `p_t` (28D) -> static min-max norm -> MLP[256,128,64] elu -> LayerNorm
  -> softsign -> latent `z` (9D).
- **Actor**: MLP[256,128,64] elu, reads `[o_t, z]` (78D), never raw `p_t`. A single
  global `log_std` (not state-dependent) is updated through the TRPO natural gradient.
- **Critic / cost critic**: asymmetric MLP[512,256,128] elu, reads `[o_t, z, p_t]`
  (106D). The cost critic is multi-head, one head per constraint.
- **Constraints**: 10 IPO terms (5 probabilistic + 5 average), each with a
  per-constraint cost-advantage standardization and log-barrier margin.

Full network layer sizes, the ConstraintTRPO/IPO update equations, and hyperparameters:
[`reference/main-network-architecture.md`](../reference/main-network-architecture.md).
Constraint definitions and budgets: [`reference/constraints.md`](../reference/constraints.md).
Reward shaping: [`reference/reward.md`](../reference/reward.md).

## Domain randomization and DORAEMON

Physics (hydrodynamics, payload, actuator gains, ocean current, control-latency) is
domain-randomized every reset; the range for each parameter is scheduled online by
DORAEMON, an entropy-maximizing adaptive-Beta curriculum shared with `marinelab`
(`marinelab.algorithms.doraemon`) that widens each parameter's distribution as the
policy's binary success rate on that distribution stays above a target. Ocean current
is enabled by default. Full parameter list, the two DR surfaces, and the
scheduler mechanics: [`reference/domain-randomization-and-doraemon.md`](../reference/domain-randomization-and-doraemon.md).

## Teacher -> student deployment

The teacher actor reads `[o_t, z]`, and `z` is computed from the **privileged**
`p_t`, which the real robot cannot observe (no DVL, no direct hydrodynamic-parameter
sensing). So the teacher cannot run on-robot as trained. Deployment distills a
**student** network (TCN or GRU, `envs/main/student/`) that reconstructs `z` from the
observation history alone, replacing the encoder at inference time while the actor
weights are reused unchanged. The packaged export (teacher + student, golden-value
self-check) is produced by `scripts/export_deploy.py`; see
[`how-to/deploy-pack-export.md`](../how-to/deploy-pack-export.md) and
[`how-to/sim-to-real.md`](../how-to/sim-to-real.md).

## Package layout

```
constrained_albc/envs/main/
├── albc_env.py       # env: 8D action, 69D obs, 28D privileged
├── config.py         # ALBCEnvCfg + DomainRandomizationCfg + constraint terms
├── doraemon.py        # ALBC-specific DORAEMON param defs (engine lives in marinelab)
├── agents/            # rsl_rl_ppo_cfg.py (policy / algorithm / runner cfgs)
├── algorithms/         # constraint_trpo.py (ConstraintTRPO + IPO)
├── encoder/            # actor_critic_encoder.py, actor_critic_asym_constrained.py
├── runners/            # constraint_encoder_runner.py
├── student/            # TCN / GRU distillation (collector, models, runner, teacher)
├── mdp/                # constraints.py, rewards.py, observations.py, events.py, faults.py
└── utils/
```

Registered task IDs (7 total: main + legacy full-DOF ablations + TDC): see the
[README](../../README.md#registered-environments). Package/entry-point layout across
`envs/analysis/scripts/tests`: [`../architecture.md`](../architecture.md).
