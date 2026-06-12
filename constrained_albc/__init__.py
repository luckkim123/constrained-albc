# Copyright (c) 2026.
"""constrained-albc: full-DOF ALBC research environments and algorithms."""
from .envs import main  # noqa: F401  triggers gym.register()
from .envs import attitude_only  # noqa: F401  triggers gym.register()
from .envs import tdc  # noqa: F401
