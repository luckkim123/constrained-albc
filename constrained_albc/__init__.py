# Copyright (c) 2026.
"""constrained-albc: ALBC research environments and algorithms.

Default task is attitude-only (`envs.main`, `Isaac-ConstrainedALBC-TRPO-v0`). The
legacy full-DOF family (`envs.full_dof`, `envs.tdc`) was removed in the 2026-09
cleanup; recover it from tag `legacy-full-dof-final`.
"""
from .envs import (
    main,  # noqa: F401  triggers gym.register() for the default task
    tdc_main,  # noqa: F401  triggers gym.register() for the classical baselines
)
