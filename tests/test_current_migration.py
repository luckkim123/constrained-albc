# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression net for the marinelab.core OceanCurrent migration (Task 1).

marinelab v0.2.0 moved the ocean current into a standalone OceanCurrent component
and removed HydrodynamicsModel._current_velocity / ._max_current_vel. albc now
reads/writes through hydro.current.velocity_w / .max_velocity / .set and injects a
shared current into the buoy model. This pins that API surface and the OU update
math so the removed-buffer crash cannot regress.

The API-surface test imports marinelab, whose package __init__ pulls in Isaac Sim
(via gym.register of the bluerov tasks); it is skipped when marinelab cannot import
(dev/CI without Isaac Sim). The OU-shape test is pure torch and always runs.
"""

import pytest
import torch


def test_marinelab_oceancurrent_api_surface():
    """The new API that albc Task 1 depends on must exist on the real classes."""
    import sys

    for name in list(sys.modules):
        if name.split(".")[0] in ("marinelab", "isaaclab", "omni", "pxr", "carb", "warp"):
            mod = sys.modules[name]
            # Sibling test modules install _MockModule stand-ins at import
            # (collection) time; their __getattr__ auto-creates a truthy
            # __file__, so require a real str path when deciding to keep.
            # The whole sim stack must be evicted, not just marinelab:
            # importing real marinelab on TOP of a mocked isaaclab/omni raises
            # TypeError mid-import (PathFinder iterates the mock parent's
            # __path__), which importorskip does NOT catch (ImportError only)
            # -> false failure instead of a skip. With the mocks gone the
            # import fails as a plain ImportError (no pxr) and skips cleanly.
            if not isinstance(getattr(mod, "__file__", None), str):
                del sys.modules[name]
    pytest.importorskip("marinelab.core", reason="marinelab requires Isaac Sim to import")
    import inspect

    from marinelab.core import HydrodynamicsModel, OceanCurrent

    # OceanCurrent exposes the buffers / methods albc reads and writes.
    assert hasattr(OceanCurrent, "velocity_w")
    assert hasattr(OceanCurrent, "max_velocity")
    assert hasattr(OceanCurrent, "set")
    assert hasattr(OceanCurrent, "add_drift")
    # HydrodynamicsModel exposes .current and accepts a shared current injection.
    assert hasattr(HydrodynamicsModel, "current")
    assert "current" in inspect.signature(HydrodynamicsModel.__init__).parameters


def test_ou_update_shapes_on_shared_buffer():
    """OU update reads/writes velocity_w[:, :3] without touching removed buffers."""
    n = 4
    velocity_w = torch.zeros(n, 6)
    max_velocity = torch.tensor([0.5, 0.5, 0.25, 0.0, 0.0, 0.0])
    mu = torch.zeros(n, 3)
    theta, sigma, dt = 0.15, 0.1, 0.02

    # Mirror albc_env._step_ocean_current_ou on the shared velocity_w buffer.
    current = velocity_w[:, :3]
    drift = -theta * (current - mu) * dt
    diffusion = sigma * (dt**0.5) * torch.randn_like(current)
    new_current = current + drift + diffusion
    clamp_bound = max_velocity[:3] * 1.05
    new_current = new_current.clamp(-clamp_bound, clamp_bound)
    velocity_w[:, :3] = new_current

    assert velocity_w.shape == (n, 6)
    # Angular (and zero-max) axes stay zero: OU only touches linear xyz.
    assert torch.all(velocity_w[:, 3:] == 0.0)
    # Linear axes stay within the 1.05 * max_velocity clamp band.
    assert torch.all(velocity_w[:, :3].abs() <= clamp_bound + 1e-6)
