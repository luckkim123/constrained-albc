# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Root pytest configuration for the no-Isaac test suite.

Import tensordict (and transitively torch._dynamo) BEFORE any test module is
collected: several test modules install _MockModule stubs (omni/pxr/carb/warp)
into sys.modules at module level, and torch._dynamo's trace_rules walks
sys.modules doing path operations on each module's __file__ -- a _MockModule
there raises TypeError during collection of any later module that imports
tensordict. Importing here runs the walk while sys.modules is still clean.
"""

import tensordict  # noqa: F401
