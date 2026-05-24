# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Full 6-DOF ALBC environment with TRPO + IPO + Encoder.

Forked from constrained_albc. Uses 8D action space (2D arm + 6D thruster)
for full position + attitude tracking with constrained RL.

87D observation: 26D current proprio + 55D temporal history + 6D integral error.
24D privileged obs for asymmetric encoder (static min-max normalization).
Error-gated 6D integral observation (Hwangbo 2017 pattern, validated R7/R8).

Registered tasks:
    Isaac-FullDOF-TRPO-v0:          TRPO + IPO + Asymmetric Encoder (production)
    Isaac-FullDOF-NoEncoder-v0:     TRPO + IPO without encoder (ablation baseline 1)
    Isaac-FullDOF-PPO-v0:           Standard PPO + asymmetric critic (ablation baseline 2)
"""

import gymnasium as gym

from .albc_env import ALBCEnv
from .config import (
    ALBCEnvCfg,
    DomainRandomizationCfg,
    HardDomainRandomizationCfg,
)

##
# Register Gym environments.
##

gym.register(
    id="Isaac-FullDOF-TRPO-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFTRPORunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-NoEncoder-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFNoEncoderRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-PPO-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFPPORunnerCfg",
    },
)

# Variant #3: Encoder + TRPO without IPO (empty constraint list)
gym.register(
    id="Isaac-FullDOF-TRPO-NoIPO-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_noconstraint:ALBCNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:FullDOFTRPONoIPORunnerCfg",
    },
)

# Variant #4: Encoder + PPO (no IPO)
gym.register(
    id="Isaac-FullDOF-PPO-Enc-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config_noconstraint:ALBCNoConstraintEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.ablation_cfgs:FullDOFPPOEncRunnerCfg",
    },
)
