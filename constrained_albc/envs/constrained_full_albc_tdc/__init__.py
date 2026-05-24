# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Full-DOF ALBC TDC + thruster PD baseline (no RL).

Classical control variant of `Isaac-FullDOF-TRPO-v0` used as a comparison
baseline. Arm 2D is controlled by the Time Delay Controller, thruster 6D by a
stateless P controller with thruster allocation. DR, reward, command sampling
and DORAEMON are identical to the RL environment so evaluations are directly
comparable.

Registered tasks:
    Isaac-FullDOF-TDC-v0: FullDOFTDCEnv (no RL training required)
"""

import gymnasium as gym

from .config import FullDOFTDCEnvCfg
from .tdc_env import FullDOFTDCEnv

##
# Register Gym environments.
##

gym.register(
    id="Isaac-FullDOF-TDC-v0",
    entry_point="constrained_albc.envs.constrained_full_albc_tdc:FullDOFTDCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:FullDOFTDCEnvCfg",
        # Play/eval scripts require an rsl_rl cfg. The classical baseline does
        # not train, so reuse the RL runner cfg purely for script compatibility.
        "rsl_rl_cfg_entry_point": (
            "constrained_albc.envs.constrained_full_albc.agents.rsl_rl_ppo_cfg:FullDOFTRPORunnerCfg"
        ),
    },
)
