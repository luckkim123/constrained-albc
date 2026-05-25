# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Pure (Isaac-Sim-free) helpers extracted from eval_dr.py.

These modules hold the trajectory builder and the metric computations, which
operate only on plain numpy/dict data and have no dependency on a booted
simulation_app, env objects, or the DR-config/SIM globals in eval_dr.py. The
eval_dr.py orchestrator imports them back; keeping them here lets them be
unit-tested with synthetic data dicts on plain python3.
"""
