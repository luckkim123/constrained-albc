# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Section-5 SimToReal plant with closed-loop depth and open-loop XY force."""

from __future__ import annotations

from isaaclab.utils import configclass

from .config import DepthXYCfg
from .config_simtoreal import ALBCSimToRealEnvCfg


@configclass
class ALBCSimToRealDepthXYEnvCfg(ALBCSimToRealEnvCfg):
    """Enable only gen-2 observations and the depth/XY task extension."""

    use_extra_policy_obs: bool = True
    depth_xy: DepthXYCfg = DepthXYCfg(enable=True)
