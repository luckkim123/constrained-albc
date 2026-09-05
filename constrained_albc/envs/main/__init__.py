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
