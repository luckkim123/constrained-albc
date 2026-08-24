# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Attitude-only ALBC environment driven by classical PD + thruster P controller.

TDC (Time Delay Control) = TDE (Time Delay Estimation) compensation + a PD
inner loop (`tdc.py` module docstring: `tau = M_hat * u_pd + U_hat + delta_T_b`).
Dropping the TDE term (`U_hat + delta_T_b`) leaves pure PD attitude control --
this class is that arm, glued the same way as `ALBCTDCEnv` but with TDE
disabled at every step, for a TDC-vs-PD ablation baseline.

`tdc.py` is NOT modified to get this: `TDCController.compute()` already
contains the exact pure-PD code path this class needs
(`tau_desired = torch.where(init_mask, tau_full, m_hat_u_pd)`,
`tdc.py:301-303`) -- it is what every environment runs on its very first
control step, before `_is_initialized` flips permanently True at the end of
`compute()` (`tdc.py:491`). This class simply flips that flag back to False
after every step, so the "not yet initialized" branch -- pure
`m_hat_u_pd` (kd*e_dot + kp*e, `_compute_pd_torque`, `tdc.py:408-431`,
confirmed stateless: no dependence on TDE history) -- runs forever instead
of only once. Every other TDC internal (Lambda/T_b/nu_dot history, EE
position feedback) keeps updating normally each step; only the final
TDE-vs-PD selector is pinned. Same gains, same IK, same thruster PD as the
TDC arm -- only this switch differs.
"""

from __future__ import annotations

import torch

from .tdc_env import ALBCTDCEnv


class ALBCPIDEnv(ALBCTDCEnv):
    """Attitude-only ALBC environment driven by PD-only classical control (no TDE, no RL).

    Uses the identical `ALBCTDCEnvCfg` as the TDC arm (no new config fields --
    the TDE/PD selector is a code-path choice, not a tunable).
    """

    def _compute_classical_actions(self) -> torch.Tensor:
        actions = super()._compute_classical_actions()
        # Pin the TDC controller to its pure-PD branch for the next step too
        # (tdc.py:491 just set this True at the end of the compute() call
        # inside the super() above). Reused unmodified: forcing this flag is
        # the documented "not yet initialized" path, not a new control law.
        self._tdc._is_initialized[:] = False
        return actions
