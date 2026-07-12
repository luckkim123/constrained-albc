# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""full_dof student config -- overrides the attitude-only defaults from _core."""
from __future__ import annotations

from dataclasses import dataclass

from constrained_albc.envs._core.student.config import StudentCfg as _CoreStudentCfg


@dataclass
class StudentCfg(_CoreStudentCfg):
    """Legacy full-DOF student dims (r13_A-era teacher)."""

    policy_obs_dim: int = 87
    privileged_dim: int = 24
    latent_dim: int = 9             # must match r13_A teacher
    variant_module: str = "constrained_albc.envs.full_dof"
