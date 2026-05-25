# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Env cfg with empty constraints list (used by TRPO-NoIPO and PPO-Enc ablations).

Inherits ALBCEnvCfg verbatim except constraints.terms is emptied. The
ConstraintEncoderRunner auto-sync then sets num_constraints=0 in the policy
and algorithm cfgs, fully disabling the IPO barrier and cost critic.

Reward, DR, DORAEMON, action space, observation space, obs noise — all
unchanged so these variants differ from the main method by exactly one
controlled variable (constraint / algorithm, depending on the runner cfg).
"""

from __future__ import annotations

from isaaclab.utils import configclass

from .config import ALBCEnvCfg
from .mdp.constraints import ALBCConstraintCfg


@configclass
class ALBCNoConstraintEnvCfg(ALBCEnvCfg):
    """Empty constraint list; everything else inherited from ALBCEnvCfg."""

    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=[])
