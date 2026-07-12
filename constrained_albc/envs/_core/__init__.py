# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Algorithm core shared by the main and full_dof env variants.

Holds the variant-independent training machinery (algorithms, encoder, runners,
student distillation, logging utilities). Env/task logic (albc_env, config, mdp)
stays per-variant -- that divergence is genuine (69D vs 87D task spaces).

Keep every __init__ in this package import-light (docstring only): the deploy
isolation path (constrained_albc/deploy/_isolation.py) loads modules under
stubbed parent packages on export hosts without Isaac Sim, so package inits
here must not pull in isaaclab.
"""
