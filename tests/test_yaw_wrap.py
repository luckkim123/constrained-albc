# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Shortest-path property of the wrapped yaw error. Pure torch, no Isaac imports.

The yaw command is a world-frame heading TARGET, so the tracking error is
    yaw_err = atan2(sin(cmd - yaw), cos(cmd - yaw))   in (-pi, pi]
which is exactly the idiom albc_env._compute_ang_errors uses. Its sign is the
short turn direction: a +3.0 target from a -3.0 heading is a 0.283 rad turn
clockwise, not a 6.0 rad turn the other way.

Run: python3 test_yaw_wrap.py
"""

from __future__ import annotations

import math

import torch


def wrap_to_pi(x: torch.Tensor) -> torch.Tensor:
    """Wrap an angle (rad) into (-pi, pi] via the atan2 identity."""
    return torch.atan2(torch.sin(x), torch.cos(x))


def yaw_err(cmd: torch.Tensor, yaw: torch.Tensor) -> torch.Tensor:
    """Wrapped heading error, shortest path."""
    return wrap_to_pi(cmd - yaw)


def test_short_way_across_the_branch_cut() -> None:
    """cmd=+3.0, yaw=-3.0: the short way is -0.283 rad, NOT +6.0."""
    e = yaw_err(torch.tensor([3.0]), torch.tensor([-3.0])).item()
    expected = 2 * math.pi - 6.0  # 0.28318...
    assert abs(e - (-expected)) < 1e-5, f"expected {-expected:.6f}, got {e:.6f}"
    assert abs(e + 0.283) < 1e-3, f"expected about -0.283, got {e:.6f}"
    assert e < 0.0, "sign must point the short (clockwise) way"


def test_zero_command_zero_yaw() -> None:
    """cmd=0, yaw=0 -> exactly 0."""
    e = yaw_err(torch.zeros(1), torch.zeros(1)).item()
    assert e == 0.0, f"expected 0.0, got {e}"


def test_random_batch_is_bounded_by_pi() -> None:
    """|err| <= pi for any command/heading pair, including far outside (-pi, pi]."""
    g = torch.Generator().manual_seed(0)
    cmd = (torch.rand(4096, generator=g) * 4 - 2) * math.pi  # (-2pi, 2pi)
    yaw = (torch.rand(4096, generator=g) * 4 - 2) * math.pi
    e = yaw_err(cmd, yaw)
    assert torch.isfinite(e).all(), "wrapped error must be finite"
    assert e.abs().max().item() <= math.pi + 1e-6, f"max |err| = {e.abs().max().item()}"


def test_error_is_equivalent_modulo_two_pi() -> None:
    """Adding 2*pi to either side leaves the error unchanged."""
    g = torch.Generator().manual_seed(1)
    cmd = torch.rand(512, generator=g) * 2 * math.pi - math.pi
    yaw = torch.rand(512, generator=g) * 2 * math.pi - math.pi
    base = yaw_err(cmd, yaw)
    shifted = yaw_err(cmd + 2 * math.pi, yaw - 2 * math.pi)
    assert torch.allclose(base, shifted, atol=1e-5), "error must be 2*pi-periodic"


def test_settling_gate_threshold_is_five_degrees() -> None:
    """yaw_settling_cost gates on |yaw_err| <= 0.087 rad; that is 5 deg."""
    assert abs(math.degrees(0.087) - 5.0) < 0.02, math.degrees(0.087)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all yaw-wrap checks passed")
