# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""DR-derived privileged-obs normalization bounds.

The encoder min-max-normalizes the 27D privileged observation before its MLP.
Historically those bounds lived as hardcoded literals
(``_PRIV_OBS_LOWER`` / ``_PRIV_OBS_UPPER`` in ``agents/rsl_rl_ppo_cfg.py``).
Those literals drifted away from the DR ranges the env actually samples, and two
dimensions drifted into outright bugs that break normalization:

* idx12 payload_mass: hardcoded ``[-0.1, 2.2]`` but DR samples ``[0.0, 3.0]`` ->
  a 3 kg payload normalizes to ``1.35 > 1`` (encoder sees an input range it was
  never trained on) and the lower margin is a physically impossible negative mass.
* idx13/14 payload_cog xy: hardcoded ``+/-0.17`` (stale 0.15 m radius) but DR
  radius was reduced to 0.08 m on 2026-04-19 -> encoder uses only half its
  normalized input span.

This module replaces the hardcoded literals: ``derive_priv_obs_bounds_from_dr``
computes the 27D bounds from the base physical values (asset cfg, the single
source of truth) combined with the DR ranges (the DR cfg instance). The derived
bounds equal the DR sampling range EXACTLY (margin 0), so DR config and
normalization bounds can no longer drift apart. A runtime assertion at the end
catches any future DR-range change that forgets to flow through here.

Design spec: docs/plans/2026-06-30-dr-derived-priv-obs-normalization-bounds.md
"""

from __future__ import annotations

# Index ordering MUST mirror compute_privileged_obs (mdp/observations.py:135-160):
#   hydro(7) = volume, CoG(x,y,z), CoB(x,y,z)
#   dynamics(5) = Ixx, lin_damp_roll, quad_damp_roll, body_mass, added_mass_surge
#   payload(4) = mass, cog_offset(x,y,z)
#   actuator(4) = joint_Kp, joint_Kd, thrust_coeff, time_const_up
#   env(4) = water_density, ocean_current(x,y,z)
#   measured(3) = body lin_vel u, v, w
PRIV_OBS_DIM = 27


def derive_priv_obs_bounds_from_dr(
    dr_cfg,
    ocean_max_velocity,
    thruster_cfg,
    hydro_cfg=None,
) -> tuple[list[float], list[float]]:
    """Derive the 27D privileged-obs normalization bounds from the DR config.

    Bounds equal the DR sampling range exactly (margin 0). The base physical
    values are read from the asset hydrodynamics cfg and the thruster cfg (the
    SSOT) rather than re-hardcoded, so ``base`` cannot become a second drift
    source.

    Args:
        dr_cfg: DR config INSTANCE (e.g. ``DomainRandomizationCfg()``, the hard config).
            Fields are read via ``getattr`` so inherited fields
            (``water_density_range``, ``ocean_current_strength_range``) resolve
            through Python inheritance even though Hard does not redeclare them.
        ocean_max_velocity: Ocean current max velocity, e.g.
            ``(0.5, 0.5, 0.25, 0, 0, 0)``; only ``[:3]`` is used. This is the
            ``base`` for the ocean-current dims (idx21-23).
        thruster_cfg: Thruster config providing ``thrust_coefficient`` (base for
            idx18) and ``time_constant_up`` (base for idx19).
        hydro_cfg: Hydrodynamics config providing the base physical values. If
            ``None``, the default ``ALBCHydrodynamicsCfg`` is imported and
            instantiated.

    Returns:
        ``(lower, upper)`` -- each a 27-element list of floats, exactly matching
        the spec section 3 derived column.
    """
    if hydro_cfg is None:
        # Imported lazily so the pure derivation can be unit-tested with a
        # stand-in hydro_cfg without pulling in Isaac Sim / marinelab.
        from marinelab.assets.albc.albc import ALBCHydrodynamicsCfg

        hydro_cfg = ALBCHydrodynamicsCfg()

    # -- Base physical values (read from the asset cfg SSOT, never re-hardcoded) --
    volume = hydro_cfg.volume  # idx0 base
    cog = hydro_cfg.center_of_gravity  # idx1-3 base (z = -0.05, NOT 0)
    cob = hydro_cfg.center_of_buoyancy  # idx4-6 base
    ixx = hydro_cfg.rigid_body_inertia[0]  # idx7 base
    lin_damp_roll = hydro_cfg.linear_damping[3]  # idx8 base (roll = index 3)
    quad_damp_roll = hydro_cfg.quadratic_damping[3]  # idx9 base (roll = index 3)
    body_mass = hydro_cfg.body_mass  # idx10 base
    added_mass_surge = hydro_cfg.added_mass[0]  # idx11 base (surge = index 0)
    thrust_coeff = thruster_cfg.thrust_coefficient  # idx18 base
    time_const_up = thruster_cfg.time_constant_up  # idx19 base

    # -- DR ranges (getattr resolves inherited fields on the instance) --
    volume_scale = getattr(dr_cfg, "volume_scale")
    cog_off_x = getattr(dr_cfg, "cog_offset_x")
    cog_off_y = getattr(dr_cfg, "cog_offset_y")
    cog_off_z = getattr(dr_cfg, "cog_offset_z")
    cob_off_x = getattr(dr_cfg, "cob_offset_x")
    cob_off_y = getattr(dr_cfg, "cob_offset_y")
    cob_off_z = getattr(dr_cfg, "cob_offset_z")
    inertia_scale = getattr(dr_cfg, "inertia_scale")
    lin_damp_scale = getattr(dr_cfg, "linear_damping_scale")
    quad_damp_scale = getattr(dr_cfg, "quadratic_damping_scale")
    body_mass_scale = getattr(dr_cfg, "body_mass_scale")
    added_mass_scale = getattr(dr_cfg, "added_mass_scale")
    payload_mass_range = getattr(dr_cfg, "payload_mass_range")
    payload_cog_xy_radius = getattr(dr_cfg, "payload_cog_offset_xy_radius")
    payload_cog_z = getattr(dr_cfg, "payload_cog_offset_z")
    joint_stiffness_range = getattr(dr_cfg, "joint_stiffness_range")
    joint_damping_range = getattr(dr_cfg, "joint_damping_range")
    thrust_coeff_scale = getattr(dr_cfg, "thrust_coefficient_scale")
    time_const_scale = getattr(dr_cfg, "time_constant_scale")
    water_density_range = getattr(dr_cfg, "water_density_range")  # inherited
    ocean_strength_range = getattr(dr_cfg, "ocean_current_strength_range")  # inherited

    def scale(base, rng):
        """form=scale: [base * scale_lo, base * scale_hi]."""
        return base * rng[0], base * rng[1]

    def offset(base, rng):
        """form=offset: [base + off_lo, base + off_hi] -- base may be nonzero."""
        return base + rng[0], base + rng[1]

    # ocean strength upper multiplies max_velocity (strength in [0, s_hi]).
    s_hi = ocean_strength_range[1]
    ocean_max = ocean_max_velocity[:3]

    pairs: list[tuple[float, float]] = [
        # -- Hydrodynamics (7D) --
        scale(volume, volume_scale),  # 0 main body volume
        offset(cog[0], cog_off_x),  # 1 CoG x (base 0)
        offset(cog[1], cog_off_y),  # 2 CoG y (base 0)
        offset(cog[2], cog_off_z),  # 3 CoG z (base -0.05) -> [-0.09, -0.01]
        offset(cob[0], cob_off_x),  # 4 CoB x (base 0)
        offset(cob[1], cob_off_y),  # 5 CoB y (base 0)
        offset(cob[2], cob_off_z),  # 6 CoB z (base 0)
        # -- Dynamic Response (5D) --
        scale(ixx, inertia_scale),  # 7 main body Ixx
        scale(lin_damp_roll, lin_damp_scale),  # 8 linear damping roll
        scale(quad_damp_roll, quad_damp_scale),  # 9 quadratic damping roll
        scale(body_mass, body_mass_scale),  # 10 body mass
        scale(added_mass_surge, added_mass_scale),  # 11 added mass surge (raw DR 12.0)
        # -- Payload (4D) --
        (payload_mass_range[0], payload_mass_range[1]),  # 12 DIRECT [0, 3] (base 0)
        (-payload_cog_xy_radius, payload_cog_xy_radius),  # 13 radius -> [-r, r]
        (-payload_cog_xy_radius, payload_cog_xy_radius),  # 14 radius -> [-r, r]
        (payload_cog_z[0], payload_cog_z[1]),  # 15 DIRECT [-0.05, 0]
        # -- Actuator (4D) --
        (joint_stiffness_range[0], joint_stiffness_range[1]),  # 16 Kp DIRECT (overwrite)
        (joint_damping_range[0], joint_damping_range[1]),  # 17 Kd DIRECT (overwrite)
        scale(thrust_coeff, thrust_coeff_scale),  # 18 thrust coefficient
        scale(time_const_up, time_const_scale),  # 19 time constant up
        # -- Environment (4D) --
        (water_density_range[0], water_density_range[1]),  # 20 DIRECT absolute (no *998)
        (-ocean_max[0] * s_hi, ocean_max[0] * s_hi),  # 21 ocean current x symmetric
        (-ocean_max[1] * s_hi, ocean_max[1] * s_hi),  # 22 ocean current y symmetric
        (-ocean_max[2] * s_hi, ocean_max[2] * s_hi),  # 23 ocean current z symmetric
        # -- Measured velocity (3D): not DR-backed, fixed normalization range --
        (-1.0, 1.0),  # 24 body lin_vel u
        (-1.0, 1.0),  # 25 body lin_vel v
        (-1.0, 1.0),  # 26 body lin_vel w
    ]

    assert len(pairs) == PRIV_OBS_DIM, f"expected {PRIV_OBS_DIM} dims, got {len(pairs)}"

    lower = [float(lo) for lo, _ in pairs]
    upper = [float(hi) for _, hi in pairs]

    # Runtime assertion: ordering + lower <= upper everywhere, and (margin-0
    # policy) each DR-backed bound equals the DR range it came from. This is the
    # re-drift guard: a future DR-range edit that forgets to flow through this
    # function trips here immediately.
    _assert_bounds_match_dr(
        lower,
        upper,
        scale_pairs={
            0: (volume, volume_scale),
            7: (ixx, inertia_scale),
            8: (lin_damp_roll, lin_damp_scale),
            9: (quad_damp_roll, quad_damp_scale),
            10: (body_mass, body_mass_scale),
            11: (added_mass_surge, added_mass_scale),
            18: (thrust_coeff, thrust_coeff_scale),
            19: (time_const_up, time_const_scale),
        },
        offset_pairs={
            1: (cog[0], cog_off_x),
            2: (cog[1], cog_off_y),
            3: (cog[2], cog_off_z),
            4: (cob[0], cob_off_x),
            5: (cob[1], cob_off_y),
            6: (cob[2], cob_off_z),
        },
        direct_pairs={
            12: payload_mass_range,
            15: payload_cog_z,
            16: joint_stiffness_range,
            17: joint_damping_range,
            20: water_density_range,
        },
        radius_pairs={13: payload_cog_xy_radius, 14: payload_cog_xy_radius},
        symmetric_pairs={
            21: ocean_max[0] * s_hi,
            22: ocean_max[1] * s_hi,
            23: ocean_max[2] * s_hi,
        },
    )

    return lower, upper


def _assert_bounds_match_dr(
    lower,
    upper,
    *,
    scale_pairs,
    offset_pairs,
    direct_pairs,
    radius_pairs,
    symmetric_pairs,
    tol=1e-9,
):
    """Assert each DR-backed dim equals the DR range it derives from (margin 0).

    Measured dims (24-26) are skipped: they have no DR field.
    """

    def _close(a, b):
        return abs(a - b) <= tol + tol * max(abs(a), abs(b))

    for idx in range(PRIV_OBS_DIM):
        assert lower[idx] <= upper[idx] + tol, f"idx{idx}: lower {lower[idx]} > upper {upper[idx]}"

    for idx, (base, rng) in scale_pairs.items():
        exp_lo, exp_hi = base * rng[0], base * rng[1]
        # scale can invert sign if base < 0; normalize to lo <= hi for comparison.
        exp_lo, exp_hi = min(exp_lo, exp_hi), max(exp_lo, exp_hi)
        assert _close(lower[idx], exp_lo) and _close(upper[idx], exp_hi), (
            f"idx{idx} scale mismatch: derived [{lower[idx]}, {upper[idx]}] != DR [{exp_lo}, {exp_hi}]"
        )

    for idx, (base, rng) in offset_pairs.items():
        exp_lo, exp_hi = base + rng[0], base + rng[1]
        assert _close(lower[idx], exp_lo) and _close(upper[idx], exp_hi), (
            f"idx{idx} offset mismatch: derived [{lower[idx]}, {upper[idx]}] != DR [{exp_lo}, {exp_hi}]"
        )

    for idx, rng in direct_pairs.items():
        assert _close(lower[idx], rng[0]) and _close(upper[idx], rng[1]), (
            f"idx{idx} direct mismatch: derived [{lower[idx]}, {upper[idx]}] != DR [{rng[0]}, {rng[1]}]"
        )

    for idx, r in radius_pairs.items():
        assert _close(lower[idx], -r) and _close(upper[idx], r), (
            f"idx{idx} radius mismatch: derived [{lower[idx]}, {upper[idx]}] != [{-r}, {r}]"
        )

    for idx, m in symmetric_pairs.items():
        assert _close(lower[idx], -m) and _close(upper[idx], m), (
            f"idx{idx} symmetric mismatch: derived [{lower[idx]}, {upper[idx]}] != [{-m}, {m}]"
        )
