# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Pure-torch test of the joint delta-noise formula used in _apply_joint_pd_action.

The env class cannot boot under pytest (Isaac Sim), so this mirrors the exact
delta-noise expression and asserts: off = byte-identical, on = perturbs + resamples.
The env-level toggle wiring is covered by the runtime check in the plan's Task 6.
"""

from __future__ import annotations

import torch


def _apply_delta_noise(delta: torch.Tensor, std):
    """Exact mirror of the noise branch in _apply_joint_pd_action."""
    if std is not None and std > 0.0:
        noise = torch.randn_like(delta) * std
        delta = delta * (1.0 + noise)
    return delta


def test_joint_noise_off_is_identity():
    delta = torch.full((4, 2), 0.05)
    out = _apply_delta_noise(delta.clone(), None)
    assert torch.equal(out, delta)  # None -> no RNG, exact identity


def test_joint_noise_zero_std_is_identity():
    delta = torch.full((4, 2), 0.05)
    out = _apply_delta_noise(delta.clone(), 0.0)
    assert torch.equal(out, delta)  # std<=0 -> branch skipped


def test_joint_noise_on_perturbs_and_resamples():
    delta = torch.full((4, 2), 0.05)
    torch.manual_seed(0)
    o1 = _apply_delta_noise(delta.clone(), 0.1)
    torch.manual_seed(1)
    o2 = _apply_delta_noise(delta.clone(), 0.1)
    assert not torch.allclose(o1, delta)   # perturbed
    assert not torch.allclose(o1, o2)      # independent per-step draws


def test_joint_noise_shape_is_per_actuator():
    delta = torch.full((8, 2), 0.05)
    torch.manual_seed(0)
    out = _apply_delta_noise(delta.clone(), 0.1)
    assert out.shape == (8, 2)  # [N, 2] per-joint independent
