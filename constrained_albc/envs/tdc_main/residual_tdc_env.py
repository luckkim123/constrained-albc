# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Residual RL over classical TDC — arm N4 of program `paper-ablation-5000`.

The classical controller keeps full authority and the policy only adds a correction
torque on top of it. This is the strongest control group for a model-based /
model-free integration claim, and the seam it needs already existed and had zero
callers: `TDCController.compute()` has taken a `residual_tau` argument since the
controller was written (`tdc.py` Step 5b, `tau_desired = tau_desired + residual_tau`).
This class is what finally calls it (PLAN.md §3-2 N4, §4-4).

What the policy controls, and what it does not
----------------------------------------------
The 8D action vector is unchanged -- it has to be, because `main.ALBCEnv` packs the
action history into the observation, so narrowing the action space would change the
observation dimension and put this arm on a different scale from every other arm in
the table. Dimensions 0:2 become the roll/pitch residual torque; 2:8 are ignored, the
same way `ALBCTDCEnv` ignores all eight. That asymmetry is deliberate and is the open
design question on this arm: a residual on the six thruster channels as well would use
the whole action vector and is arguably the more complete formulation, but PLAN.md
§4-4 specifies the arm torque seam only, and widening it is a scope decision rather
than an implementation detail. Recorded here rather than taken.

Where the constraints act
-------------------------
On the composite torque, which is what makes this arm comparable to the RL arms, and
it holds automatically: `compute_all_costs` reads robot state, never the action
(`albc_env.py:1411-1412`), so the K=10 costs see the vehicle produced by TDC-plus-
residual without any wiring. PLAN.md §4-4 reasons the same way.

Plant
-----
This arm trains, so under anchor (B) it must sit on the section-5 plant. Its config
therefore descends from `ALBCSimToRealEnvCfg` and re-declares the two classical
controller fields, rather than descending from `ALBCTDCEnvCfg` and re-declaring the
seven plant fields. Duplicating the plant block is exactly the failure `finding/352`
is filed against; duplicating two controller defaults is not.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from .tdc_env import ALBCTDCEnv

if TYPE_CHECKING:
    from .config import ALBCResidualTDCEnvCfg


class ALBCResidualTDCEnv(ALBCTDCEnv):
    """TDC with an additive policy residual on the arm torque (trains)."""

    cfg: ALBCResidualTDCEnvCfg

    def __init__(self, cfg: ALBCResidualTDCEnvCfg, render_mode: str | None = None, **kwargs) -> None:
        super().__init__(cfg, render_mode, **kwargs)
        # Zero until the first action arrives. `_compute_classical_actions` is reachable
        # from reset paths that run before any `_pre_physics_step`, and a residual of
        # zero there is exactly the plain TDC law rather than a stale or absent buffer.
        self._residual_buf = torch.zeros(self.num_envs, 2, device=self.device)

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        """Keep the policy action as a residual, then run the classical pipeline.

        Read before delegating, because the parent discards the action -- that is its
        contract as a classical arm and it is not changed here.
        """
        self._residual_buf = actions[:, :2].clamp(-1.0, 1.0) * self.cfg.residual_tau_scale
        super()._pre_physics_step(actions)

    def _residual_tau(self) -> torch.Tensor:
        return self._residual_buf
