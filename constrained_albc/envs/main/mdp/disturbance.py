# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Pure (Isaac-Sim-free) exogenous-disturbance helpers for the ALBC env.

Same split as ``faults.py``, and for the same reason: the NUMERICAL core lives here as
pure torch functions so it is unit-testable on plain torch (no sim, no GPU), and the env
(``albc_env.py``) only decides WHEN to call them and WHERE the buffers live.

One disturbance so far -- the exogenous heave force (see ``config.FzDisturbanceCfg``).
Once ``fault.thruster_always_dead=(0, 3)`` takes the verticals out of the policy's
actuator set, the deployed depth PID still drives the one surviving vertical channel, so
its Fz reaches the hull as an EXOGENOUS wrench the policy cannot command -- together with
the pitch moment the vertical geometry couples to it (decision/159 결정 2, PLAN §4
item 11). Random in magnitude AND in timing: piecewise-constant, re-drawn per env when a
random hold expires.

Toggle-off contract: the env calls neither function unless ``cfg.disturbance.enable``, so
a disturbance-disabled env draws no RNG and stays byte-identical to the pre-item-11 env.
"""
from __future__ import annotations

import torch


def sample_fz_and_hold(
    strength: torch.Tensor,
    fz_max: float,
    hold_s: tuple[float, float],
    generator: torch.Generator | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Draw ``Fz = U(-1, 1) * strength * fz_max`` and a hold ``U(hold_s)``, per env.

    ``strength`` [n] is the per-env DORAEMON knob in [0, 1]; it scales the MAGNITUDE
    only, so ``|Fz| <= strength * fz_max`` holds elementwise and ``strength == 0`` gives
    exactly 0.0 (an env at the curriculum nominal feels nothing). The sign is drawn
    independently of the strength -- the depth PID pushes both ways.

    Returns ``(fz [n], hold [n])`` in newtons and seconds.
    """
    n = strength.shape[0]
    device = strength.device
    u = torch.rand(n, device=device, generator=generator) * 2.0 - 1.0
    fz = u * strength * fz_max
    lo, hi = hold_s
    hold = torch.rand(n, device=device, generator=generator) * (hi - lo) + lo
    return fz, hold


def write_fz_wrench(
    forces: torch.Tensor,
    torques: torch.Tensor,
    fz: torch.Tensor,
    my_per_fz: float,
) -> None:
    """Write the heave force and its coupled pitch moment into pre-allocated buffers.

    ``forces`` / ``torques`` are (N, B, 3) body-frame buffers for
    ``permanent_wrench_composer.add_forces_and_torques``; only the z force column and the
    y torque column are ever touched, so every other component keeps whatever the caller
    allocated (zeros). The moment is ``My = my_per_fz * Fz`` exactly -- a single realised
    ratio measured on the robot (``deployed_tam.json`` My/Fz = -0.1458, finding/155), NOT
    re-derived from the sim TAM columns.
    """
    col = fz.unsqueeze(-1)
    forces[:, :, 2] = col
    torques[:, :, 1] = my_per_fz * col
