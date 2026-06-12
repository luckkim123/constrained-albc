# Copyright (c) 2026.
"""constrained-albc: ALBC research environments and algorithms.

Default task is attitude-only (`envs.main`, `Isaac-ConstrainedALBC-TRPO-v0`); the
legacy full-DOF env (`envs.full_dof`) registers `Isaac-ConstrainedALBC-Full-*`.
"""
from .envs import full_dof  # noqa: F401  triggers gym.register() for Full-* tasks
from .envs import main  # noqa: F401  triggers gym.register() for the default task
from .envs import tdc  # noqa: F401
