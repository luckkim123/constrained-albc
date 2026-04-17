# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Full 6-DOF ALBC environment with TRPO + IPO + Encoder.

Forked from constrained_albc. Uses 8D action space (2D arm + 6D thruster)
for full position + attitude tracking with constrained RL.

Registered tasks:
    Isaac-FullDOF-TRPO-v0:          TRPO + IPO + Asymmetric Encoder (production)
    Isaac-FullDOF-NoEncoder-v0:     TRPO + IPO without encoder (ablation baseline 1)
    Isaac-FullDOF-PPO-v0:           Standard PPO + asymmetric critic (ablation baseline 2)
    Isaac-FullDOF-PerDimEnt-v0:     per-dim entropy_coef (arm=0.01, thr=0.001)
    Isaac-FullDOF-ArmOnly-v0:       arm-only entropy boost (thr=baseline)
    Isaac-FullDOF-Exp-L1-v0:        L1 penalty for SS error (lin_ratio=0.15, yaw_ratio=0.15)
    Isaac-FullDOF-Exp-Settling-v0:  Settling constraints for overshoot (lin_vel + yaw)
    Isaac-FullDOF-Exp-Tanh-v0:      Saturating tanh penalty (coef=1.0, eps=0.10) -- Round 4
    Isaac-FullDOF-Exp-Arctan-v0:    Saturating arctan penalty (coef=1.0, eps=0.10) -- Round 4
    Isaac-FullDOF-MaxStd1-v0:       max_std=1.0 (cap thr noise divergence)
    Isaac-FullDOF-R5-RpVel-v0:      Round 5 GPU1: rp_vel_settling budget 0.20->0.08 (attitude SS)
    Isaac-FullDOF-R5-VelSettling-v0: Round 5 GPU2: activate lin_vel+yaw settling (threshold=sigma)
    Isaac-FullDOF-R6-AttArctan-v0:  Round 6 GPU1: att_rp Arctan coef=0.3 (attitude SS via shape)
    Isaac-FullDOF-R6-VelTanh-v0:    Round 6 GPU2: lin+yaw_vel Tanh coef=0.3 (velocity SS via shape)
    Isaac-FullDOF-R7-EpsSmooth-v0:  Round 7 GPU1: wider eps(0.20) + k_s=-0.2 (roll fix + OS reduce)
    Isaac-FullDOF-R7-Integral-v0:   Round 7 GPU2: integral-error obs (Hwangbo 2017, 84D obs)
"""

import gymnasium as gym

from .albc_env import ALBCEnv
from .config import (
    ALBCEnvArctanCfg,
    ALBCEnvCfg,
    ALBCEnvL1Cfg,
    ALBCEnvR5RpVelSettlingCfg,
    ALBCEnvR5VelSettlingCfg,
    ALBCEnvR6AttArctanCfg,
    ALBCEnvR6VelTanhCfg,
    ALBCEnvR7EpsSmoothCfg,
    ALBCEnvR7IntegralCfg,
    ALBCEnvSettlingCfg,
    ALBCEnvTanhCfg,
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
    id="Isaac-FullDOF-Exp-L1-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvL1Cfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFExpL1RunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-Exp-Settling-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvSettlingCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFExpSettlingRunnerCfg",
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

gym.register(
    id="Isaac-FullDOF-Exp-Tanh-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvTanhCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFExpTanhRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-Exp-Arctan-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvArctanCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFExpArctanRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-R5-RpVel-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvR5RpVelSettlingCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFR5RpVelRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-R5-VelSettling-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvR5VelSettlingCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFR5VelSettlingRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-R6-AttArctan-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvR6AttArctanCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFR6AttArctanRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-R6-VelTanh-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvR6VelTanhCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFR6VelTanhRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-R7-EpsSmooth-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvR7EpsSmoothCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFR7EpsSmoothRunnerCfg",
    },
)

gym.register(
    id="Isaac-FullDOF-R7-Integral-v0",
    entry_point="isaaclab_tasks.direct.constrained_full_albc:ALBCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCEnvR7IntegralCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agents.rsl_rl_ppo_cfg:FullDOFR7IntegralRunnerCfg",
    },
)
