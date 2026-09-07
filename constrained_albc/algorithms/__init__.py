# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Variant-independent training machinery for the ALBC envs.

Holds the algorithms (ConstraintTRPO, ConstraintLagrangian) plus the encoder,
runners, student distillation and logging utilities. Env/task logic (albc_env,
config, mdp) stays per-variant under ``constrained_albc.envs``.

Promoted here from ``constrained_albc/envs/_core/`` in the 2026-09 cleanup: none
of this is an environment, so it no longer lives under ``envs/``.

Keep every __init__ in this package import-light (docstring only, no re-exports):
the deploy isolation path (constrained_albc/deploy/_isolation.py) loads modules
under stubbed parent packages on export hosts without Isaac Sim, so a package
init that imported torch or rsl_rl would drag the sim stack onto an export host.
Importers therefore spell the module out, e.g.
``from constrained_albc.algorithms.constraint_trpo import ConstraintTRPO``.
"""
