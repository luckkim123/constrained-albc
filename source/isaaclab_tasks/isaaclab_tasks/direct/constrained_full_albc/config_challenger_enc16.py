# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Env cfg for Phase 0.6 baseline challenger.

Reconstructs the EXACT env configuration used for the r13a_hist5_act3 run
(trained 2026-04-21 15:13 in a now-deleted worktree) and changes only
`encoder_latent_dim` from 9 to 16 in the paired runner cfg.

Main `ALBCEnvCfg` has drifted via r14 (OU drift enabled + doubled sigma,
HardDR ranges widened 1.5-3x, action_latency added, doraemon.step_interval
doubled). To test the encoder bottleneck hypothesis cleanly, every field
that differs between hist5_act3's saved env.yaml and current main must be
overridden here to the r13-era value.

Reference: `/workspace/isaaclab/logs/rsl_rl/fulldof_albc/2026-04-21_15-13-15_r13a_hist5_act3/params/env.yaml`
"""

from __future__ import annotations

from isaaclab.utils import configclass
from isaaclab.utils.noise import GaussianNoiseCfg, NoiseModelWithAdditiveBiasCfg, UniformNoiseCfg

from .config import ALBCEnvCfg, DomainRandomizationCfg
from .doraemon import DoraemonCfg

# =============================================================================
# Observation noise / bias (121D layout, matching hist5_act3 exactly)
# =============================================================================
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
    + [0.0]            # manipulability
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
    [0] * 3            # vel_cmd_lin
    + [0] * 3          # ang_cmd
    + [0.02] * 3       # euler
    + [0.03] * 3       # ang_vel
    + [0.02] * 3       # lin_vel
    + [0.02] * 2       # joint_pos
    + [0.03] * 2       # joint_vel
    + [0]              # manipulability
    + [0.01] * 6       # thruster
    + ([0.02] * 2 + [0.03] * 2) * _HIST_LEN
    + ([0.02] * 3 + [0.04] * 3 + [0.02] * 3) * _HIST_LEN
    + [0] * (8 * _HIST_ACTION_LEN)
    + [0] * 6
)

_OBS_BIAS_MIN_121 = tuple(-x for x in _OBS_BIAS_MAG_121)
_OBS_BIAS_MAX_121 = _OBS_BIAS_MAG_121

assert len(_OBS_NOISE_STD_121) == 121, f"noise std length {len(_OBS_NOISE_STD_121)} != 121"
assert len(_OBS_BIAS_MAG_121) == 121, f"bias mag length {len(_OBS_BIAS_MAG_121)} != 121"


# =============================================================================
# HardDomainRandomization — r13-era values (exact copy of hist5_act3 randomization)
# =============================================================================


@configclass
class ChallengerHardDomainRandomizationCfg(DomainRandomizationCfg):
    """r13-era HardDR, pre-r14 widening. Values copied from hist5_act3 env.yaml."""

    enable: bool = True
    # Hydrodynamics (r13 values)
    added_mass_scale: tuple[float, float] = (0.5, 1.5)
    linear_damping_scale: tuple[float, float] = (0.4, 1.7)
    quadratic_damping_scale: tuple[float, float] = (0.4, 1.7)
    volume_scale: tuple[float, float] = (0.75, 1.25)
    # COB / COG (unchanged between r13 and r14)
    cob_offset_x: tuple[float, float] = (-0.02, 0.02)
    cob_offset_y: tuple[float, float] = (-0.02, 0.02)
    cob_offset_z: tuple[float, float] = (-0.04, 0.04)
    cog_offset_x: tuple[float, float] = (-0.02, 0.02)
    cog_offset_y: tuple[float, float] = (-0.02, 0.02)
    cog_offset_z: tuple[float, float] = (-0.04, 0.04)
    # Inertia / Mass (r13 values)
    inertia_scale: tuple[float, float] = (0.4, 2.0)
    body_mass_scale: tuple[float, float] = (0.75, 1.25)
    water_density_range: tuple[float, float] = (995.0, 1025.0)
    # Payload (r13 values)
    payload_mass_range: tuple[float, float] = (0.0, 3.0)
    payload_cog_offset_xy_radius: float = 0.08
    payload_cog_offset_z: tuple[float, float] = (-0.05, 0.0)
    buoy_moment_arm: float = 0.18
    # Joint Actuator (r13 values)
    joint_stiffness_range: tuple[float, float] = (30.0, 150.0)
    joint_damping_range: tuple[float, float] = (0.3, 7.0)
    yaw_damping_scale: tuple[float, float] = (0.5, 1.5)
    joint_effort_limit_range: tuple[float, float] = (0.7, 1.0)
    joint_static_friction_range: tuple[float, float] = (0.0, 0.03)
    joint_viscous_friction_range: tuple[float, float] = (0.0, 0.2)
    # Thruster (r13 values)
    thrust_coefficient_scale: tuple[float, float] = (0.7, 1.3)
    time_constant_scale: tuple[float, float] = (0.7, 1.3)
    # Ocean current (r13 values)
    ocean_current_strength_range: tuple[float, float] = (0.0, 1.0)
    # Action latency (r13 had no such field -> default (0, 0) from parent DomainRandomizationCfg)
    # Explicitly set to (0, 0) to avoid any future-default change.
    action_latency_range: tuple[int, int] = (0, 0)


# =============================================================================
# ALBCChallengerEnc16EnvCfg — hist5_act3 env + observation dim 121
# =============================================================================


@configclass
class ALBCChallengerEnc16EnvCfg(ALBCEnvCfg):
    """Exact reconstruction of hist5_act3 training env.

    The ONLY intended behavioral difference vs the original hist5_act3 run is
    `encoder_latent_dim` (9 -> 16), which is set in the paired runner cfg, not
    here. All env-side fields match hist5_act3's saved env.yaml.
    """

    # Observation shape (hist5_act3)
    observation_space: int = 121
    hist_len: int = 5
    hist_action_len: int = 3

    # Obs noise / bias resized to 121D
    observation_noise_model: NoiseModelWithAdditiveBiasCfg = NoiseModelWithAdditiveBiasCfg(
        noise_cfg=GaussianNoiseCfg(mean=0.0, std=_OBS_NOISE_STD_121),
        bias_noise_cfg=UniformNoiseCfg(n_min=_OBS_BIAS_MIN_121, n_max=_OBS_BIAS_MAX_121),
    )

    # Ocean current OU drift — hist5_act3 had OU disabled, sigma=0.05
    ou_enable: bool = False
    ou_sigma: float = 0.05

    # Domain randomization — r13-era values
    randomization: ChallengerHardDomainRandomizationCfg = ChallengerHardDomainRandomizationCfg()

    # Doraemon — hist5_act3 used step_interval=250 (main is now 500)
    doraemon: DoraemonCfg = DoraemonCfg(
        enable=True,
        kl_ub=0.06,
        performance_lb=90.0,
        step_interval=250,
    )
