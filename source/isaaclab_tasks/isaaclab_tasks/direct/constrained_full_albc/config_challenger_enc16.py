# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Env cfg for Phase 0.6 baseline challenger.

Mirrors hist5_act3 obs config (hist_len=5, hist_action_len=3, observation_space=121)
and is paired with encoder_latent_dim=16 in the runner cfg, testing whether the
encoder bottleneck (latent=9 in prior hist-series runs) was masking the marginal
value of extra history information.

Reward / DR / DORAEMON / ocean current / constraints inherited verbatim from
ALBCEnvCfg. Only obs-shape-dependent fields differ:
    - observation_space: 87 -> 121
    - hist_len: 3 -> 5
    - hist_action_len: 2 -> 3
    - _OBS_NOISE_STD / _OBS_BIAS_MAG resized to 121D
"""

from __future__ import annotations

from isaaclab.utils import configclass
from isaaclab.utils.noise import GaussianNoiseCfg, NoiseModelWithAdditiveBiasCfg, UniformNoiseCfg

from .config import ALBCEnvCfg

# =============================================================================
# Observation noise / bias (121D layout)
# =============================================================================
# Layout (mirrors hist5_act3):
#   Current Proprio (26D)      [unchanged from parent]
#   Joint tracking hist (20D)  = 4D x hist_len(5)
#   Body tracking hist (45D)   = 9D x hist_len(5)
#   Action hist (24D)          = 8D x hist_action_len(3)
#   Integral error (6D)        [unchanged]
_HIST_LEN = 5
_HIST_ACTION_LEN = 3

_OBS_NOISE_STD_121 = tuple(
    # --- Current Proprioception (26D) ---
    [0.0] * 3          # vel_cmd_lin
    + [0.0] * 3        # ang_cmd
    + [0.02] * 3       # euler
    + [0.04] * 3       # ang_vel
    + [0.04] * 3       # lin_vel
    + [0.02] * 2       # joint_pos
    + [0.04] * 2       # joint_vel
    + [0.0]            # manipulability (computed)
    + [0.02] * 6       # thruster_state
    # --- Joint Tracking History (4D x hist_len) ---
    + ([0.02] * 2 + [0.04] * 2) * _HIST_LEN
    # --- Body Tracking History (9D x hist_len) ---
    + ([0.04] * 3 + [0.04] * 3 + [0.02] * 3) * _HIST_LEN
    # --- Action History (8D x hist_action_len) ---
    + [0.0] * (8 * _HIST_ACTION_LEN)
    # --- Integral Error (6D) ---
    + [0.0] * 6
)

_OBS_BIAS_MAG_121 = tuple(
    # --- Current Proprioception (26D) ---
    [0] * 3            # vel_cmd_lin
    + [0] * 3          # ang_cmd
    + [0.02] * 3       # euler
    + [0.03] * 3       # ang_vel
    + [0.02] * 3       # lin_vel
    + [0.02] * 2       # joint_pos
    + [0.03] * 2       # joint_vel
    + [0]              # manipulability
    + [0.01] * 6       # thruster
    # --- Joint Tracking History (4D x hist_len) ---
    + ([0.02] * 2 + [0.03] * 2) * _HIST_LEN
    # --- Body Tracking History (9D x hist_len) ---
    + ([0.02] * 3 + [0.04] * 3 + [0.02] * 3) * _HIST_LEN
    # --- Action History (8D x hist_action_len) ---
    + [0] * (8 * _HIST_ACTION_LEN)
    # --- Integral Error (6D) ---
    + [0] * 6
)

_OBS_BIAS_MIN_121 = tuple(-x for x in _OBS_BIAS_MAG_121)
_OBS_BIAS_MAX_121 = _OBS_BIAS_MAG_121

assert len(_OBS_NOISE_STD_121) == 121, f"noise std length {len(_OBS_NOISE_STD_121)} != 121"
assert len(_OBS_BIAS_MAG_121) == 121, f"bias mag length {len(_OBS_BIAS_MAG_121)} != 121"


@configclass
class ALBCChallengerEnc16EnvCfg(ALBCEnvCfg):
    """hist5_act3 obs config for Phase 0.6 baseline challenger."""

    observation_space: int = 121
    hist_len: int = 5
    hist_action_len: int = 3

    observation_noise_model: NoiseModelWithAdditiveBiasCfg = NoiseModelWithAdditiveBiasCfg(
        noise_cfg=GaussianNoiseCfg(mean=0.0, std=_OBS_NOISE_STD_121),
        bias_noise_cfg=UniformNoiseCfg(n_min=_OBS_BIAS_MIN_121, n_max=_OBS_BIAS_MAX_121),
    )
