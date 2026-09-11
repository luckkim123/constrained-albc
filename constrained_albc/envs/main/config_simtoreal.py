# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Env cfg for the retrain-simtoreal-2026-09 section-5 plant.

Freezes the seven Hydra overrides that Phase 3b was launched with (see
`g0c_runner/p3b_resume.sh`) into a named variant, so a retrain selects them with
one task id instead of seven command-line strings that are silently dropped when
forgotten. `finding/352` filed this as blocking: every one of the seven differs
from the ALBCEnvCfg default, so a launch that omits the block reverts to exactly
the configuration `finding/315` measured stalling (curriculum never opened,
DORAEMON mode -2, fault_severity 0.0045).

    thrusters.thrust_coefficient            40.0     -> 13.0     (R-1 measured band)
    randomization.thrust_coefficient_scale  (0.7,1.3)-> (0.5,2.0)
    randomization.control_delay_steps       (0,0)    -> (0,3)    (finding/264; 152 ms)
    fault.enable                            False    -> True
    fault.thruster_fail_prob                0.10     -> 0.30
    fault.thruster_dead_frac                0.0      -> 0.5
    doraemon.performance_lb                 250.0    -> 200.0    (finding/315)

Base-class defaults are untouched, so every other task and experiment in the repo
is unaffected. Equivalence to the override block is not asserted here -- it is
checked by `test_simtoreal_cfg.py`, which resolves both and diffs them.
"""

from __future__ import annotations

from isaaclab.utils import configclass

from .config import (
    ALBCEnvCfg,
    ALBCThrusterCfg,
    DomainRandomizationCfg,
    DoraemonCfg,
    FaultInjectionCfg,
)
from .mdp.constraints import ALBCConstraintCfg


@configclass
class ALBCSimToRealEnvCfg(ALBCEnvCfg):
    """Section-5 delta plant; everything else inherited from ALBCEnvCfg."""

    thrusters: ALBCThrusterCfg | None = ALBCThrusterCfg(thrust_coefficient=13.0)
    randomization: DomainRandomizationCfg = DomainRandomizationCfg(
        thrust_coefficient_scale=(0.5, 2.0),
        control_delay_steps=(0, 3),
    )
    fault: FaultInjectionCfg = FaultInjectionCfg(
        enable=True,
        thruster_fail_prob=0.30,
        thruster_dead_frac=0.5,
    )
    # The base sets four DoraemonCfg args at config.py:612; only performance_lb moves,
    # so the other three are repeated here rather than inherited (a bare
    # DoraemonCfg(performance_lb=200.0) would silently reset enable/kl_ub/step_interval).
    doraemon: DoraemonCfg = DoraemonCfg(
        enable=True, kl_ub=0.12, performance_lb=200.0, step_interval=250
    )


@configclass
class ALBCSimToRealNoDoraemonEnvCfg(ALBCSimToRealEnvCfg):
    """N6a No-DORAEMON: fixed section-5 DR sampled uniformly at full static ranges.

    With the scheduler disabled, ``ALBCEnv`` has no ``_doraemon`` and its reset
    fallbacks draw every DORAEMON-managed dimension uniformly over the inherited
    section-5 static ranges. The plant, faults, action delay, and observation noise
    task conditions otherwise remain those of ``ALBCSimToRealEnvCfg``.
    """

    doraemon: DoraemonCfg = DoraemonCfg(
        enable=False, kl_ub=0.12, performance_lb=200.0, step_interval=250
    )


@configclass
class ALBCSimToRealNoDREnvCfg(ALBCSimToRealNoDoraemonEnvCfg):
    """N6b No-DR: every physics DR range collapsed to its nominal point, DORAEMON off.

    The points are the eval ``none`` level (``analysis/dr_config._TRUE_NOMINAL_PHYSICS``)
    plus ``buoy_volume_scale``/``buoy_body_mass_scale`` at 1.0 -- those two are missing
    from dr_config's interpolation list, so eval ``none`` still draws them over
    (0.75, 1.25); N6b fixes them (operator decision 2026-09-11). ``enable`` stays True
    on purpose: ``enable=False`` returns from ``_reset_physics`` before the thruster
    fault draw and also skips the initial joint-position draw, which would remove
    faults along with DR. Task conditions kept equal to N6a: action delay (0, 3),
    ``fault_severity_range`` (0, 1), initial joint randomization.
    """

    randomization: DomainRandomizationCfg = DomainRandomizationCfg(
        added_mass_scale=(1.0, 1.0),
        linear_damping_scale=(1.0, 1.0),
        quadratic_damping_scale=(1.0, 1.0),
        volume_scale=(1.0, 1.0),
        cob_offset_x=(0.0, 0.0),
        cob_offset_y=(0.0, 0.0),
        cob_offset_z=(0.0, 0.0),
        cog_offset_x=(0.0, 0.0),
        cog_offset_y=(0.0, 0.0),
        cog_offset_z=(0.0, 0.0),
        inertia_scale=(1.0, 1.0),
        body_mass_scale=(1.0, 1.0),
        water_density_range=(1000.0, 1000.0),
        buoy_volume_scale=(1.0, 1.0),
        buoy_body_mass_scale=(1.0, 1.0),
        joint_stiffness_range=(100.0, 100.0),
        joint_damping_range=(3.0, 3.0),
        yaw_damping_scale=(1.0, 1.0),
        joint_effort_limit_range=(1.0, 1.0),
        joint_static_friction_range=(0.0, 0.0),
        joint_viscous_friction_range=(0.0, 0.0),
        payload_mass_range=(0.0, 0.0),
        payload_cog_offset_xy_radius=0.0,
        payload_cog_offset_xy_u_range=(0.0, 0.0),
        payload_cog_offset_z=(0.0, 0.0),
        thrust_coefficient_scale=(1.0, 1.0),
        time_constant_scale=(1.0, 1.0),
        max_thrust_scale=(1.0, 1.0),
        control_delay_steps=(0, 3),
        ocean_current_strength_range=(0.0, 0.0),
        obs_noise_scale_range=(0.0, 0.0),
    )
    priv_obs_bounds_randomization: DomainRandomizationCfg = DomainRandomizationCfg(
        thrust_coefficient_scale=(0.5, 2.0),
        control_delay_steps=(0, 3),
    )
    """Encoder min-max bounds come from the section-5 ranges (the parent's), not the
    collapsed ones above: zero-width bounds divide by zero in the encoder
    (`constraint_encoder_runner.py`), and matching the reference arm keeps the network's
    input scaling identical so only the training plant differs."""


@configclass
class ALBCSimToRealNoConstraintEnvCfg(ALBCSimToRealEnvCfg):
    """Section-5 delta plant WITH an empty constraint list.

    The paper-ablation-5000 comparison suite needs both halves of a 2x2: the plant
    (old / section-5) crossed with the constraint list (K=10 / empty). Three of the
    seven training arms sit in the empty-constraint cell -- TRPO-NoIPO, no-both, and
    PPO-Enc -- and on anchor (B) all of them train on the section-5 plant, so they
    need a cfg that is `ALBCSimToRealEnvCfg` and `ALBCNoConstraintEnvCfg` at once.

    Composed by inheritance rather than by adding a third variant of the seven-field
    block: the plant values live in exactly one place (the parent), so an arm cannot
    drift onto a half-applied plant, which is what `finding/352` asked for. The
    emptying is the same one line `ALBCNoConstraintEnvCfg` applies to `ALBCEnvCfg`,
    and it means the same thing here -- ConstraintEncoderRunner's auto-sync sees
    num_constraints=0 and no-ops the IPO barrier and the cost critic.
    """

    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=[])
