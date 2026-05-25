# System Overview

> **Status**: 2026-05-25 | **Source**: `constrained_full_albc/{albc_env,config}.py`,
> `mdp/observations.py`, [`experiments-index.json`](../reference/experiments-index.json)

Conceptual overview of the constrained full-DOF ALBC system. For package layout and the
RSL-RL dependency (stock, no fork) see [`../architecture.md`](../architecture.md); for
registered task IDs see the [README](../README.md).

## The robot

An underwater vehicle (UUV) that controls attitude with a **buoyancy-actuated arm**: two
revolute joints reposition a buoyant link, whose buoyancy generates restoring torque to
stabilize roll/pitch. Thrusters provide the remaining wrench.

```
[Main Body] -- joint1 -- [Link1] -- joint2 -- [Link2 / Buoy]
 (9.18 kg)              (L1=0.233m)          (L2=0.233m, F_buoy~=26.2N)
```

System net buoyancy is slightly positive → weak passive stability.

## Control problem

The policy tracks a mixed command:

| Channel | Command | Reward shape |
|---|---|---|
| Roll / Pitch | attitude (±30°) | exponential kernel |
| Yaw | rate (±0.5 rad/s) | quadratic penalty |
| Linear (x/y/z) | velocity (±0.5 m/s) | quadratic penalty |

## Action / observation spaces (verified against code)

| Space | Dim | Composition |
|---|---|---|
| **Action** | **8D** | 2D arm (delta joint targets) + 6D thruster wrench |
| **Observation** | **87D** | 26D current proprio + 55D temporal history + 6D integral |
| **Privileged** | **24D** | hydro (7) + dynamic response (5) + payload (4) + actuator (4) + env (4) |

- **26D current proprio** = command (6) + body state (9) + arm state (5) + thruster (6).
- **55D history** = joint (12) + body (27) + action (16) ring-buffer.
- **6D integral** = error-gated leaky integrator on [roll, pitch, vx, vy, vz, yaw_rate]
  (Hwangbo 2017 pattern; introduced R7, error-gated in R8 — see
  [experiments-archive](../reference/experiments-archive.md)).

> The code's prose docstring still reads "81D" in one place, but
> `observation_space = 87` and the itemized breakdown both sum to 87 — **87 is
> authoritative**. Privileged is **24D** (`state_space = 24`).

## Algorithm

**ConstraintTRPO + IPO** with an **asymmetric encoder/critic**:

- **Encoder**: privileged `p_t` (24D) → static min-max norm → MLP[256,128,64] →
  LayerNorm → softsign → latent `z` (9D).
- **Actor**: MLP[256,128,64], reads `[o_t, z]`. `log_std` decoupled from the TRPO natural
  gradient into a separate Adam optimizer.
- **Critic / Cost**: asymmetric MLP[512,256,128], reads `[o_t, z, p_t]` (privileged).
- **Constraints**: 10 terms (5 probabilistic + 5 average), per-constraint cost-advantage
  standardization (NORBC Sec IV-B), IPO log-barrier.
- **DR curriculum**: DORAEMON adaptive Beta (`kl_ub=0.04`, `performance_lb=90`,
  `step_interval=250`). Ocean current enabled.

## Deployment constraint: the encoder latent z

The teacher actor reads `[o_t, z]`, where `z` is the encoder latent computed from
the **privileged** observation `p_t` (24D). Real hardware has no `p_t`, so the
teacher policy cannot run on-robot as-is. Deployment requires either:

- a distilled **student** network (TCN/GRU) that reconstructs `z` from the
  observation history (`student/` package), or
- an ablation variant that does not depend on the encoder.

See [`../how-to/deploy.md`](../how-to/deploy.md) for the export pipeline.

## Package layout

```
constrained_full_albc/
├── albc_env.py              # env: 8D action, 87D obs, 24D privileged
├── config.py                # ALBCEnvCfg + DR / HardDR cfgs
├── doraemon.py              # DORAEMON DR curriculum
├── agents/                  # rsl_rl_ppo_cfg.py, ablation_cfgs.py
├── algorithms/              # constraint_trpo.py (ConstraintTRPO + IPO)
├── encoder/                 # actor_critic_encoder.py, actor_critic_asym_constrained.py
├── runners/                 # constraint_encoder_runner.py, on_policy_doraemon_runner.py
├── student/                 # TCN / GRU distillation
├── mdp/                     # constraints.py, rewards.py, observations.py, events.py
└── utils/
```

The TDC controller variant lives in the sibling `constrained_full_albc_tdc/` package
(`Isaac-FullDOF-TDC-v0`); its control law is in
[`tdc-control-law.md`](tdc-control-law.md).

## Registered tasks

Six task IDs are registered — `Isaac-FullDOF-TRPO-v0` (main) plus NoEncoder / PPO /
TRPO-NoIPO / PPO-Enc ablations and the TDC variant. Full table in the
[README](../README.md).

> **Deprecated, not registered:** the 2-DOF `hero_agent` envs (`Isaac-HeroAgent-*`,
> 13D obs) and the HORA/RMA two-phase Encoder-Base/Adapt-Base pipeline. Do not treat
> those as current — they were removed in the repo split.
