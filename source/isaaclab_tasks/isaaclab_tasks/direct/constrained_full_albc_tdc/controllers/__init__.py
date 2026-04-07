# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Classical controllers for the Full-DOF ALBC TDC baseline."""

from .thruster_pd import ThrusterPDCfg, ThrusterPDController

__all__ = ["ThrusterPDCfg", "ThrusterPDController"]
