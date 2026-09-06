# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Attitude-only ALBC classical-control baselines (TDC and PD; no RL).

Classical control variants of `Isaac-ConstrainedALBC-TRPO-v0` (the paper's
default attitude-only task, `envs/main`) used as comparison baselines. Arm 2D
is controlled by the Time Delay Controller (TDC arm) or its PD-only
sub-mechanism (PID/PD arm, TDE compensation disabled -- see `pid_env.py`),
thruster 6D by a stateless P controller with thruster allocation. DR, reward,
command sampling and DORAEMON are identical to the RL environment so
evaluations are directly comparable. Controller bodies (`tdc.py`,
`kinematics.py`, `thruster_pd.py`) are reused unmodified from
`.controllers` -- this package also supplies the `main`-specific glue
(`tdc_env.py`, `pid_env.py`) and config/registration. Both arms share the
identical `ALBCTDCEnvCfg` (the TDE/PD selector is a code-path choice on the
env class, not a config field).

Registered tasks:
    Isaac-ConstrainedALBC-Main-TDC-v0: ALBCTDCEnv (TDC = TDE + PD, no RL training required)
    Isaac-ConstrainedALBC-Main-PID-v0: ALBCPIDEnv (PD only, no TDE, no RL training required)
    Isaac-ConstrainedALBC-Main-ATDC-v0: ALBCTDCEnv + online design-inertia adaptation
        (paper-ablation-5000 arm N2; no RL training required)
    Isaac-ConstrainedALBC-Main-ResidualTDC-SimToReal-v0: TDC + learned residual torque
        (paper-ablation-5000 arm N4; this one DOES train, on the section-5 plant)
"""

import gymnasium as gym

from .config import ALBCATDCEnvCfg, ALBCResidualTDCEnvCfg, ALBCTDCEnvCfg
from .pid_env import ALBCPIDEnv
from .residual_tdc_env import ALBCResidualTDCEnv
from .tdc_env import ALBCTDCEnv

##
# Register Gym environments.
##

gym.register(
    id="Isaac-ConstrainedALBC-Main-TDC-v0",
    entry_point="constrained_albc.envs.tdc_main:ALBCTDCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCTDCEnvCfg",
        # Play/eval scripts require an rsl_rl cfg. The classical baseline does
        # not train, so reuse the RL runner cfg purely for script compatibility.
        "rsl_rl_cfg_entry_point": (
            "constrained_albc.envs.main.agents.rsl_rl_ppo_cfg:ALBCTRPORunnerCfg"
        ),
    },
)

gym.register(
    id="Isaac-ConstrainedALBC-Main-PID-v0",
    entry_point="constrained_albc.envs.tdc_main:ALBCPIDEnv",
    disable_env_checker=True,
    kwargs={
        # Same config as the TDC arm -- see module docstring: no new fields,
        # the TDE-vs-PD selector lives on the env class, not the config.
        "env_cfg_entry_point": f"{__name__}.config:ALBCTDCEnvCfg",
        "rsl_rl_cfg_entry_point": (
            "constrained_albc.envs.main.agents.rsl_rl_ppo_cfg:ALBCTRPORunnerCfg"
        ),
    },
)

# Arm N2 (paper-ablation-5000 §3-2, §4-2): ATDC = the same TDC law with the design
# inertia adapted online instead of fixed. Same env class and same cfg as the TDC
# arm except `tdc_controller.adaptive_m_hat`, so a TDC-vs-ATDC comparison isolates
# the adaptation law. Evaluation-only, like its two siblings above.
gym.register(
    id="Isaac-ConstrainedALBC-Main-ATDC-v0",
    entry_point="constrained_albc.envs.tdc_main:ALBCTDCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCATDCEnvCfg",
        "rsl_rl_cfg_entry_point": (
            "constrained_albc.envs.main.agents.rsl_rl_ppo_cfg:ALBCTRPORunnerCfg"
        ),
    },
)

# Arm N4 (paper-ablation-5000 §3-2, §4-4): the only task in this package that trains.
# TDC keeps authority and the policy adds a correction torque; the id carries the
# SimToReal suffix because, unlike its evaluation-only siblings above, this arm has a
# plant baked into its cfg and anchor (B) requires that to be the section-5 one.
gym.register(
    id="Isaac-ConstrainedALBC-Main-ResidualTDC-SimToReal-v0",
    entry_point="constrained_albc.envs.tdc_main:ALBCResidualTDCEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.config:ALBCResidualTDCEnvCfg",
        "rsl_rl_cfg_entry_point": (
            "constrained_albc.envs.main.agents.ablation_cfgs:ALBCResidualTDCRunnerCfg"
        ),
    },
)
