# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Pure attitude control ALBC environment with TRPO + IPO + Encoder.

Tracks roll/pitch attitude + yaw rate only (no linear velocity tracking).
Uses 8D action space (2D arm + 6D thruster) with constrained RL.

69D observation: 20D current proprio + 46D temporal history + 3D integral error.
28D privileged obs for asymmetric encoder (static min-max normalization).

Registered tasks (these are the default ALBC tasks; the legacy full-DOF envs live in
`constrained_albc.envs.full_dof` under `Isaac-ConstrainedALBC-Full-*` ids):
    Isaac-ConstrainedALBC-TRPO-v0:       TRPO + IPO + Asymmetric Encoder (production)
    Isaac-ConstrainedALBC-NoEncoder-v0:  TRPO + IPO without encoder (ablation baseline 1)
    Isaac-ConstrainedALBC-PPO-v0:        Standard PPO + asymmetric critic (ablation baseline 2)
    Isaac-ConstrainedALBC-TRPO-NoIPO-v0: Encoder + TRPO without IPO (ablation 3)
    Isaac-ConstrainedALBC-PPO-Enc-v0:    Encoder + PPO, no IPO (ablation 4)
    Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-v0: TRPO, no IPO, no encoder (ablation 5, "no-both")
    Isaac-ConstrainedALBC-TRPO-SimToReal-v0: production TRPO on the section-5 plant

Section-5 plant variants of the ablation arms (program `paper-ablation-5000`, anchor (B)):
    Isaac-ConstrainedALBC-NoEncoder-SimToReal-v0
    Isaac-ConstrainedALBC-PPO-SimToReal-v0
    Isaac-ConstrainedALBC-TRPO-NoIPO-SimToReal-v0
    Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-SimToReal-v0
    Isaac-ConstrainedALBC-PPO-Enc-SimToReal-v0
    Isaac-ConstrainedALBC-TRPO-Lagrangian-SimToReal-v0 (arm N1, new mechanism)
"""

import gymnasium as gym

from .albc_env import ALBCEnv
from .config import (
    ALBCEnvCfg,
    DomainRandomizationCfg,
)

##
# Register Gym environments.
##

gym.register(
    id="Isaac-ConstrainedALBC-TRPO-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:ALBCTRPORunnerCfg",
    },
)

# Variant #1: TRPO + IPO without the encoder
gym.register(
    id="Isaac-ConstrainedALBC-NoEncoder-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:ALBCNoEncoderRunnerCfg",
    },
)

# Variant #2: standard PPO + asymmetric critic
gym.register(
    id="Isaac-ConstrainedALBC-PPO-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:ALBCPPORunnerCfg",
    },
)

# Variant #3: Encoder + TRPO without IPO (empty constraint list)
gym.register(
    id="Isaac-ConstrainedALBC-TRPO-NoIPO-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_noconstraint:ALBCNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:ALBCTRPONoIPORunnerCfg",
    },
)

# Variant #4: Encoder + PPO (no IPO)
gym.register(
    id="Isaac-ConstrainedALBC-PPO-Enc-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_noconstraint:ALBCNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:ALBCPPOEncRunnerCfg",
    },
)

# Variant #5: TRPO without IPO, without encoder ("no-both")
gym.register(
    id="Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_noconstraint:ALBCNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:ALBCTRPONoIPONoEncoderRunnerCfg",
    },
)

# Variant #6: production TRPO on the retrain-simtoreal-2026-09 section-5 plant.
# Same runner cfg as Isaac-ConstrainedALBC-TRPO-v0; only the env cfg differs, and it
# carries the seven overrides Phase 3b was fired with (finding/352). Launch a retrain
# with this task id instead of repeating the override block.
gym.register(
    id="Isaac-ConstrainedALBC-TRPO-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:ALBCTRPORunnerCfg",
    },
)

# =============================================================================
# Section-5 plant variants of the ablation arms — program `paper-ablation-5000`
# =============================================================================
#
# Anchor (B) (PLAN.md §8-R): every arm of the comparison table trains on the
# retrain-simtoreal-2026-09 section-5 plant, so each arm needs a task id that
# carries the seven overrides. `finding/352` is explicit that the seven are
# launch-override-only and that a launch which omits the block silently reverts
# to the old plant -- PLAN.md §4-5 chose path (a), a cfg subclass per arm task
# id, precisely to remove the way to forget it.
#
# The runner cfg of each pair is byte-identical to its old-plant twin above; only
# `env_cfg_entry_point` moves. That is the whole point: the arm's algorithm is the
# controlled variable and the plant is not, so a diff between the two registrations
# should show exactly one changed line.
#
# Constraint-list axis: arms whose old-plant twin uses `config_noconstraint` take
# `ALBCSimToRealNoConstraintEnvCfg`, the rest take `ALBCSimToRealEnvCfg`.
#
# Not registered here: the reference arm on this plant. `-TRPO-SimToReal-v0` above
# already is it; whether it is retrained from scratch at 5000 iterations is
# `[DECISION-REQUIRED: reference-arm]` (PLAN.md §8-R-7) and is the user's call.

# A2 on the section-5 plant: TRPO + IPO without the encoder
gym.register(
    id="Isaac-ConstrainedALBC-NoEncoder-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:ALBCNoEncoderRunnerCfg",
    },
)

# A3 on the section-5 plant: standard PPO + asymmetric critic
gym.register(
    id="Isaac-ConstrainedALBC-PPO-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:ALBCPPORunnerCfg",
    },
)

# A4 on the section-5 plant: encoder + TRPO without IPO
gym.register(
    id="Isaac-ConstrainedALBC-TRPO-NoIPO-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:ALBCTRPONoIPORunnerCfg",
    },
)

# A5 on the section-5 plant: "no-both"
gym.register(
    id="Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": (
            f"{__name__}.agents.ablation_cfgs:ALBCTRPONoIPONoEncoderRunnerCfg"
        ),
    },
)

# A6 on the section-5 plant: encoder + PPO. Registered but never trained on either
# plant -- PLAN.md §8-R-2 makes it launch order 1 as the pipeline canary, because it
# is the cheapest arm that exercises the whole path. It is only a canary if the
# as-run params of its run directory are diffed against the seven fields (§4-5); a
# run that silently reverted to the old plant otherwise looks like a success
# (`finding/318`).
gym.register(
    id="Isaac-ConstrainedALBC-PPO-Enc-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:ALBCPPOEncRunnerCfg",
    },
)

# Arm N1 (paper-ablation-5000 §3-2, §4-1): same constraints, different mechanism.
# Note the env cfg is the constraint-CARRYING one -- unlike A4/A5/A6 above, this arm
# must see the full K=10 list, because what it ablates is how the budget is enforced
# (Lagrangian multipliers instead of the IPO barrier), not whether there is one.
gym.register(
    id="Isaac-ConstrainedALBC-TRPO-Lagrangian-SimToReal-v0",
    entry_point="constrained_albc.envs.main:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_simtoreal:ALBCSimToRealEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:ALBCTRPOLagrangianRunnerCfg",
    },
)
