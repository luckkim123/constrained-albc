# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression net for the marinelab.core OceanCurrent migration (Task 1).

marinelab v0.2.0 moved the ocean current into a standalone OceanCurrent component
and removed HydrodynamicsModel._current_velocity / ._max_current_vel. albc now
reads/writes through hydro.current.velocity_w / .max_velocity / .set and injects a
shared current into the buoy model. This pins that API surface so the removed-buffer
crash cannot regress.

The test imports marinelab, whose package __init__ pulls in Isaac Sim (via gym.register
of the bluerov tasks); it is skipped when marinelab cannot import (dev/CI without Isaac
Sim).

A companion `test_ou_update_shapes_on_shared_buffer` was deleted in the 2026-09 cleanup.
It reimplemented the OU update inline and asserted on its own arithmetic, so it could not
fail whatever production did -- and WP3 (04ef330) then removed the thing it claimed to
mirror (`albc_env._step_ocean_current_ou`, `_ou_base_current`, `ou_enable/theta/sigma`),
leaving it a check with no counterpart at all. Do not re-add it without a real call into
production code.
"""

import pytest


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
