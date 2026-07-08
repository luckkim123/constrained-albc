# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Pure attitude control ALBC environment with TRPO + IPO + Encoder.

Tracks roll/pitch attitude + yaw rate only (no linear velocity tracking).
Uses 8D action space (2D arm + 6D thruster) with constrained RL.

69D observation: 20D current proprio + 46D temporal history + 3D integral error.
28D privileged obs for asymmetric encoder (static min-max normalization).

Registered task (this is the default ALBC task; the legacy full-DOF env lives in
`constrained_albc.envs.full_dof` under `Isaac-ConstrainedALBC-Full-*` ids):
    Isaac-ConstrainedALBC-TRPO-v0: TRPO + IPO + Asymmetric Encoder (production)
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
