# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Event functions for ALBC domain randomization (Isaac Lab EventTerm pattern)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import torch

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from isaaclab_tasks.models import HydrodynamicsModel

    from ..albc_env import ALBCEnv
    from ..config import DomainRandomizationCfg


# --- Helper Functions (Private) ---


def _ensure_env_ids(env: ALBCEnv, env_ids: torch.Tensor | None) -> torch.Tensor:
    """Ensure env_ids is a valid tensor, defaulting to all environments if None."""
    if env_ids is None:
        return torch.arange(env.num_envs, device=env.device)
    return env_ids


def _rand_uniform_range(
    shape: tuple | int,
    range_tuple: tuple[float, float],
    device: str | torch.device,
) -> torch.Tensor:
    """Generate uniform random values in [low, high] from a (low, high) tuple."""
    if isinstance(shape, int):
        shape = (shape,)
    lo, hi = range_tuple
    return torch.rand(shape, device=device) * (hi - lo) + lo


def _sample_or_uniform(
    key: str,
    sampled: dict[str, torch.Tensor] | None,
    shape: tuple | int,
    range_tuple: tuple[float, float],
    device: str | torch.device,
    broadcast_dim: int | None = None,
) -> torch.Tensor:
    """Return DORAEMON-sampled value if available, otherwise uniform random."""
    if sampled and key in sampled:
        val = sampled[key]
        if broadcast_dim is not None:
            val = val.unsqueeze(-1).expand(-1, broadcast_dim)
        return val
    return _rand_uniform_range(shape, range_tuple, device)


def _apply_xyz_offset_with_doraemon(
    target: torch.Tensor,
    env_ids: torch.Tensor,
    base: torch.Tensor,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    z_range: tuple[float, float],
    sampled: dict[str, torch.Tensor] | None,
    device: str | torch.device,
    x_key: str | None = None,
    y_key: str | None = None,
    z_key: str | None = None,
) -> None:
    """Apply XYZ offsets; each axis uses DORAEMON-sampled value if key provided."""
    num = len(env_ids)
    for axis, (key, rng) in enumerate([(x_key, x_range), (y_key, y_range), (z_key, z_range)]):
        if key and sampled and key in sampled:
            target[env_ids, axis] = base[axis] + sampled[key]
        else:
            target[env_ids, axis] = base[axis] + _rand_uniform_range(num, rng, device)


# --- DRSampler ---


def _clamp_payload_cog_stability(
    attachment_offset: torch.Tensor,
    cog_offset: torch.Tensor,
    buoyancy_force: torch.Tensor,
    moment_arm: float,
    mass: torch.Tensor,
    gravity: float,
) -> torch.Tensor:
    """Clamp payload CoG offset for static stability: m*g*|r_eff_xy| <= F_bu * h.

    Args:
        attachment_offset: Payload attachment offset in body frame. Shape: (N, 3).
        cog_offset: Payload CoG offset (relative to attachment). Shape: (N, 3).
        buoyancy_force: Buoy buoyancy force. Shape: (N,).
        moment_arm: Buoy moment arm (scalar, meters).
        mass: Payload mass. Shape: (N,).
        gravity: Gravitational acceleration (m/s^2).

    Returns:
        Clamped cog_offset tensor. Shape: (N, 3).
    """
    effective = attachment_offset + cog_offset
    current_norm = effective[:, :2].norm(dim=-1)
    max_norm = torch.where(
        mass > 1e-6,
        (buoyancy_force * moment_arm) / (mass * gravity),
        torch.full_like(mass, float("inf")),
    )
    scale = torch.clamp(max_norm / current_norm.clamp(min=1e-8), max=1.0)
    clamped = effective * scale.unsqueeze(-1)
    return clamped - attachment_offset


class DRSampler:
    """Bundles DR config + num_envs + device for domain randomization sampling."""

    def __init__(
        self,
        cfg: DomainRandomizationCfg,
        num_envs: int,
        device: str | torch.device,
    ) -> None:
        self.cfg = cfg
        self.num_envs = num_envs
        self.device = device

    def get(self, range_tuple: tuple[float, float], shape: tuple | int | None = None) -> torch.Tensor:
        """Sample uniform random values. Defaults shape to num_envs."""
        if shape is None:
            shape = self.num_envs
        return _rand_uniform_range(shape, range_tuple, self.device)


# --- Hydrodynamics Randomization ---


class _HydroBaseCache:
    """Cached base tensors from a HydrodynamicsModel config for DR scaling."""

    __slots__ = (
        "added_mass",
        "linear_damping",
        "quadratic_damping",
        "volume",
        "cob",
        "cog",
        "inertia",
        "water_density",
    )

    def __init__(self, hydro: HydrodynamicsModel) -> None:
        kw = {"dtype": torch.float32, "device": hydro.device}
        self.added_mass = torch.tensor(hydro.cfg.added_mass, **kw)
        self.linear_damping = torch.tensor(hydro.cfg.linear_damping, **kw)
        self.quadratic_damping = torch.tensor(hydro.cfg.quadratic_damping, **kw)
        self.volume: float = hydro.cfg.volume if hydro.cfg.volume is not None else hydro.volume[0].item()
        self.cob = torch.tensor(hydro.cfg.center_of_buoyancy, **kw)
        self.cog = torch.tensor(hydro.cfg.center_of_gravity, **kw)
        if hydro.cfg.rigid_body_inertia is not None:
            self.inertia = torch.tensor(hydro.cfg.rigid_body_inertia, **kw)
        else:
            logger.warning(
                "rigid_body_inertia not set for %s; falling back to 0.5 * added_mass[3:6]. "
                "This heuristic may not match the actual rigid body inertia.",
                type(hydro.cfg).__name__,
            )
            self.inertia = torch.tensor(hydro.cfg.added_mass[3:6], **kw) * 0.5
        self.water_density: float = hydro.cfg.water_density


def _get_hydro_base(hydro: HydrodynamicsModel) -> _HydroBaseCache:
    """Get or create cached base tensors for a hydrodynamics model."""
    if not hasattr(hydro, "_dr_base_cache"):
        hydro._dr_base_cache = _HydroBaseCache(hydro)  # type: ignore[attr-defined]
    return hydro._dr_base_cache  # type: ignore[attr-defined]


def _randomize_hydro_model(
    hydro: HydrodynamicsModel,
    env_ids: torch.Tensor,
    dr: DRSampler,
    sampled: dict[str, torch.Tensor] | None = None,
) -> None:
    """Apply domain randomization to a hydrodynamics model."""
    n = dr.num_envs
    cfg = dr.cfg
    base = _get_hydro_base(hydro)
    device = dr.device

    # Added mass (6 DOF, DORAEMON: single scale broadcast to 6)
    am_scales = _sample_or_uniform("added_mass_scale", sampled, (n, 6), cfg.added_mass_scale, device, broadcast_dim=6)
    hydro.added_mass_matrix[env_ids] = torch.diag_embed(base.added_mass.unsqueeze(0) * am_scales)

    # Linear damping (6 DOF, DORAEMON: single scale broadcast to 6)
    ld_scales = _sample_or_uniform(
        "linear_damping_scale", sampled, (n, 6), cfg.linear_damping_scale, device, broadcast_dim=6
    )
    hydro.linear_damping[env_ids] = base.linear_damping.unsqueeze(0) * ld_scales

    # Quadratic damping (6 DOF, DORAEMON: single scale broadcast to 6)
    qd_scales = _sample_or_uniform(
        "quadratic_damping_scale", sampled, (n, 6), cfg.quadratic_damping_scale, device, broadcast_dim=6
    )
    hydro.quadratic_damping[env_ids] = base.quadratic_damping.unsqueeze(0) * qd_scales

    # Yaw-specific quadratic damping override (index 5)
    yaw_scales = dr.get(cfg.yaw_damping_scale)
    hydro.quadratic_damping[env_ids, 5] = base.quadratic_damping[5] * yaw_scales

    # Volume (DORAEMON if available)
    vol_scales = _sample_or_uniform("volume_scale", sampled, n, cfg.volume_scale, device)
    hydro.volume[env_ids] = base.volume * vol_scales

    # Water density (DORAEMON: absolute value, not scale)
    hydro.water_density[env_ids] = _sample_or_uniform("water_density", sampled, n, cfg.water_density_range, device)

    hydro.update_buoyancy_force(env_ids)

    # Center of Buoyancy (DORAEMON for all axes)
    _apply_xyz_offset_with_doraemon(
        hydro.center_of_buoyancy,
        env_ids,
        base.cob,
        cfg.cob_offset_x,
        cfg.cob_offset_y,
        cfg.cob_offset_z,
        sampled,
        device,
        x_key="cob_offset_x",
        y_key="cob_offset_y",
        z_key="cob_offset_z",
    )

    # Center of Gravity (DORAEMON for all axes)
    _apply_xyz_offset_with_doraemon(
        hydro.center_of_gravity,
        env_ids,
        base.cog,
        cfg.cog_offset_x,
        cfg.cog_offset_y,
        cfg.cog_offset_z,
        sampled,
        device,
        x_key="cog_offset_x",
        y_key="cog_offset_y",
        z_key="cog_offset_z",
    )

    # Rigid body inertia (DORAEMON if available)
    inertia_scales = _sample_or_uniform("inertia_scale", sampled, (n, 3), cfg.inertia_scale, device, broadcast_dim=3)
    hydro.rigid_body_inertia[env_ids] = base.inertia.unsqueeze(0) * inertia_scales

    # Added mass stability: clamp M_a[i] < 0.95 * I_rigid[i] (forward Euler stability)
    if hydro.cfg.apply_added_mass_force and hydro.body_mass is not None:
        threshold = 0.95
        am_diag = torch.diagonal(hydro.added_mass_matrix[env_ids], dim1=-2, dim2=-1)  # (N, 6)
        body_mass = hydro.body_mass[env_ids]  # (N,)
        rot_inertia = hydro.rigid_body_inertia[env_ids]  # (N, 3)
        gen_inertia = torch.cat([body_mass.unsqueeze(-1).expand(-1, 3), rot_inertia], dim=-1)  # (N, 6)
        max_am = threshold * gen_inertia
        exceeded = am_diag > max_am
        if exceeded.any():
            clamped = torch.where(exceeded, max_am, am_diag)
            hydro.added_mass_matrix[env_ids] = torch.diag_embed(clamped)


def randomize_hydrodynamics(
    env: ALBCEnv,
    env_ids: torch.Tensor | None,
    dr: DRSampler,
    sampled: dict[str, torch.Tensor] | None = None,
) -> None:
    """Randomize hydrodynamic parameters for main body and buoy."""
    env_ids = _ensure_env_ids(env, env_ids)
    _randomize_hydro_model(env._hydro, env_ids, dr, sampled)
    _randomize_hydro_model(env._buoy_hydro, env_ids, dr, sampled)


def randomize_ocean_current(
    env: ALBCEnv,
    env_ids: torch.Tensor | None,
) -> None:
    """Randomize ocean current (same velocity for main body and buoy)."""
    env_ids = _ensure_env_ids(env, env_ids)
    env._hydro.set_ocean_current(env_ids)

    # Share current with buoy (same water volume)
    if env._buoy_hydro is not None:
        env._buoy_hydro.set_ocean_current(env_ids, velocity=env._hydro._current_velocity[env_ids])


# --- Robot Pose Reset ---


def reset_robot_pose_default(
    env: ALBCEnv,
    env_ids: torch.Tensor | None,
) -> None:
    """Reset robot to default pose: env_origin, upright, zero velocity."""
    env_ids = _ensure_env_ids(env, env_ids)

    default_root_state = env._robot.data.default_root_state[env_ids].clone()
    # Position = env_origin (no offset)
    default_root_state[:, :3] = env.scene.env_origins[env_ids]
    # Orientation = identity (upright)
    default_root_state[:, 3:7] = torch.tensor([1.0, 0.0, 0.0, 0.0], device=env.device)
    # Velocity = zero
    default_root_state[:, 7:] = 0.0

    env._robot.write_root_pose_to_sim(default_root_state[:, :7], env_ids)
    env._robot.write_root_velocity_to_sim(default_root_state[:, 7:], env_ids)


# --- Joint Randomization ---


def randomize_joint_positions(
    env: ALBCEnv,
    env_ids: torch.Tensor | None,
    joint_pos_range: tuple[float, float] = (-6.0, 6.0),
) -> None:
    """Randomize ALBC joint positions, clamp to limits, sync target buffer."""
    env_ids = _ensure_env_ids(env, env_ids)
    num_reset = len(env_ids)
    device = env.device

    default_joint_pos = env._robot.data.default_joint_pos[env_ids].clone()
    default_joint_vel = torch.zeros_like(default_joint_pos)

    random_pos = _rand_uniform_range((num_reset, len(env._albc_joint_ids)), joint_pos_range, device)

    default_joint_pos[:, env._albc_joint_ids] = random_pos
    env._joint_pos_targets[env_ids] = random_pos

    env._robot.write_joint_state_to_sim(default_joint_pos, default_joint_vel, env_ids=env_ids)


def reset_joint_positions_default(
    env: ALBCEnv,
    env_ids: torch.Tensor | None,
) -> None:
    """Reset joints to default positions (no randomization)."""
    env_ids = _ensure_env_ids(env, env_ids)

    default_joint_pos = env._robot.data.default_joint_pos[env_ids].clone()
    default_joint_vel = torch.zeros_like(default_joint_pos)

    env._joint_pos_targets[env_ids] = 0.0

    env._robot.write_joint_state_to_sim(default_joint_pos, default_joint_vel, env_ids=env_ids)


# --- Payload Randomization ---


def randomize_payload(
    env: ALBCEnv,
    env_ids: torch.Tensor | None,
    dr: DRSampler,
    sampled: dict[str, torch.Tensor] | None = None,
) -> None:
    """Randomize payload mass, attachment offset, and CoG offset (gripper frame)."""
    env_ids = _ensure_env_ids(env, env_ids)

    if env._payload_mass is None or env._payload_attachment_offset is None:
        return

    num_reset = len(env_ids)
    device = env.device
    cfg = dr.cfg

    # Mass (DORAEMON target)
    env._payload_mass[env_ids] = _sample_or_uniform("payload_mass", sampled, num_reset, cfg.payload_mass_range, device)

    # Reset attachment offset to fixed default
    base_offset = torch.tensor(env.cfg.payload_attachment_offset, device=device, dtype=torch.float32)
    env._payload_attachment_offset[env_ids] = base_offset.unsqueeze(0)

    # CoG offset: XY in disk, Z uniform
    if env._payload_cog_offset is not None:
        r_max = cfg.payload_cog_offset_xy_radius
        if r_max > 0:
            angle = torch.rand(num_reset, device=device) * 2.0 * torch.pi
            radius = r_max * torch.sqrt(torch.rand(num_reset, device=device))
            env._payload_cog_offset[env_ids, 0] = radius * torch.cos(angle)
            env._payload_cog_offset[env_ids, 1] = radius * torch.sin(angle)
        else:
            env._payload_cog_offset[env_ids, 0] = 0.0
            env._payload_cog_offset[env_ids, 1] = 0.0
        env._payload_cog_offset[env_ids, 2] = _sample_or_uniform(
            "payload_cog_offset_z", sampled, num_reset, cfg.payload_cog_offset_z, device
        )

        # Clamp effective xy offset: m*g*|r_eff_xy| <= F_bu * h
        env._payload_cog_offset[env_ids] = _clamp_payload_cog_stability(
            attachment_offset=env._payload_attachment_offset[env_ids],
            cog_offset=env._payload_cog_offset[env_ids],
            buoyancy_force=env._buoy_hydro.buoyancy_force[env_ids],
            moment_arm=cfg.buoy_moment_arm,
            mass=env._payload_mass[env_ids],
            gravity=env._gravity_magnitude.item(),
        )


# --- Joint Actuator Gain Randomization ---


def randomize_joint_gains(
    env: ALBCEnv,
    env_ids: torch.Tensor,
    dr: DRSampler,
) -> None:
    """Randomize ALBC joint stiffness and damping (same value for both joints per env)."""
    cfg = dr.cfg

    stiffness = dr.get(cfg.joint_stiffness_range)
    damping = dr.get(cfg.joint_damping_range)

    env._robot.write_joint_stiffness_to_sim(stiffness.unsqueeze(-1), joint_ids=env._albc_joint_ids, env_ids=env_ids)
    env._robot.write_joint_damping_to_sim(damping.unsqueeze(-1), joint_ids=env._albc_joint_ids, env_ids=env_ids)


# --- Joint Effort Limit Randomization ---


def randomize_joint_effort_limit(
    env: ALBCEnv,
    env_ids: torch.Tensor,
    dr: DRSampler,
) -> None:
    """Randomize ALBC joint effort limits (scale applied to asset default)."""
    scale = dr.get(dr.cfg.joint_effort_limit_range)

    num_joints = len(env._albc_joint_ids)
    effort = (env._default_effort_limit * scale).unsqueeze(-1).expand(-1, num_joints)

    env._robot.write_joint_effort_limit_to_sim(effort, joint_ids=env._albc_joint_ids, env_ids=env_ids)

    # Sync actuator internal buffers (Isaac Lab #128 workaround)
    albc_ids_t = torch.tensor(env._albc_joint_ids, device=env.device)
    for actuator in env._robot.actuators.values():
        jids = actuator.joint_indices
        if isinstance(jids, torch.Tensor):
            mask = torch.isin(jids, albc_ids_t)
            if mask.any():
                local_ids = mask.nonzero(as_tuple=True)[0]
                actuator.effort_limit[env_ids[:, None], local_ids] = effort[..., : local_ids.shape[0]]
                actuator.effort_limit_sim[env_ids[:, None], local_ids] = effort[..., : local_ids.shape[0]]
        elif jids == slice(None):
            actuator.effort_limit[env_ids[:, None], albc_ids_t] = effort
            actuator.effort_limit_sim[env_ids[:, None], albc_ids_t] = effort


# --- Body Mass Randomization ---


def randomize_body_mass(
    env: ALBCEnv,
    env_ids: torch.Tensor,
    dr: DRSampler,
    sampled: dict[str, torch.Tensor] | None = None,
) -> None:
    """Randomize rigid body masses (single scale per env, broadcast to all bodies)."""
    env_ids_cpu = env_ids.cpu()

    masses = env._robot.root_physx_view.get_masses()
    masses[env_ids_cpu] = env._robot.data.default_mass[env_ids_cpu].clone()

    scales = _sample_or_uniform("body_mass_scale", sampled, dr.num_envs, dr.cfg.body_mass_scale, dr.device).cpu()
    masses[env_ids_cpu] *= scales.unsqueeze(-1)
    masses = torch.clamp(masses, min=1e-6)

    env._robot.root_physx_view.set_masses(masses, env_ids_cpu)

    # Sync hydrodynamics body_mass tensors with PhysX (for privileged obs)
    body_idx = env._body_id[0]
    buoy_idx = env._buoy_body_id[0]
    device = env.device
    if env._hydro.body_mass is not None:
        env._hydro.body_mass[env_ids] = masses[env_ids_cpu, body_idx].to(device)
    if env._buoy_hydro.body_mass is not None:
        env._buoy_hydro.body_mass[env_ids] = masses[env_ids_cpu, buoy_idx].to(device)


# --- Joint Friction Randomization ---


def randomize_joint_friction(
    env: ALBCEnv,
    env_ids: torch.Tensor,
    dr: DRSampler,
) -> None:
    """Randomize ALBC joint static and viscous friction (same for both joints per env)."""
    cfg = dr.cfg

    static = dr.get(cfg.joint_static_friction_range)
    viscous = dr.get(cfg.joint_viscous_friction_range)

    env._robot.write_joint_friction_coefficient_to_sim(
        joint_friction_coeff=static.unsqueeze(-1),
        joint_viscous_friction_coeff=viscous.unsqueeze(-1),
        joint_ids=env._albc_joint_ids,
        env_ids=env_ids,
    )
