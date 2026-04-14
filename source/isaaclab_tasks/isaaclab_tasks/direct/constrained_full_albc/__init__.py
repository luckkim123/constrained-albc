# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Full 6-DOF ALBC environment with TRPO + IPO + Encoder.

Forked from constrained_albc. Uses 8D action space (2D arm + 6D thruster)
for full position + attitude tracking with constrained RL.

Registered tasks:
    Isaac-FullDOF-TRPO-v0:       TRPO + IPO + Asymmetric Encoder (production)
    Isaac-FullDOF-NoEncoder-v0:  TRPO + IPO without encoder (ablation baseline 1)
    Isaac-FullDOF-PPO-v0:        Standard PPO + asymmetric critic (ablation baseline 2)
    Isaac-FullDOF-PerDimEnt-v0:  Exp 1: per-dim entropy_coef (arm=0.01, thr=0.001)
    Isaac-FullDOF-MaxStd1-v0:    Exp 2: max_std=1.0 (cap thr noise divergence)
"""

import gymnasium as gym

from .albc_env import ALBCEnv
from .config import ALBCEnvCfg, DomainRandomizationCfg, HardDomainRandomizationCfg

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

gym.register(
    id="Isaac-FullDOF-PerDimEnt-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFPerDimEntRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-ArmOnly-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFArmOnlyRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-MaxStd1-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFMaxStd1RunnerCfg",
    },
)
