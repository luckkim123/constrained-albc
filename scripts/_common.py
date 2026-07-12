#!/usr/bin/env python3
# Copyright (c) 2026.
"""Shared overlay-launch boilerplate for scripts/train.py and scripts/play.py.

Both entry points need: (1) upstream cli_args importable via ISAACLAB_PATH, and
(2) a one-shot import hook that registers constrained_albc's gym envs the moment
isaaclab_tasks is imported (after AppLauncher boots SimulationApp, so pxr exists).
Kept as a plain sibling module (not a package) since it must be importable before
AppLauncher runs, same constraint as `cli_args` itself.
"""

import builtins
import os
import sys

from isaaclab.app import AppLauncher


def install_overlay_import_hook():
    """Make upstream cli_args importable and install the isaaclab_tasks import hook.

    Returns the upstream `cli_args` module.
    """
    isaaclab_path = os.environ.get("ISAACLAB_PATH", "/workspace/isaaclab")
    upstream_rl_dir = os.path.join(isaaclab_path, "scripts", "reinforcement_learning", "rsl_rl")
    if upstream_rl_dir not in sys.path:
        sys.path.insert(0, upstream_rl_dir)

    import cli_args  # isort: skip

    real_import = builtins.__import__
    overlay_loaded = False

    def _import_with_overlay(name, *args, **kwargs):
        module = real_import(name, *args, **kwargs)
        nonlocal overlay_loaded
        if not overlay_loaded and name == "isaaclab_tasks":
            overlay_loaded = True
            import constrained_albc  # noqa: F401  triggers gym.register()
        return module

    builtins.__import__ = _import_with_overlay
    return cli_args


def launch_app(parser):
    """Append AppLauncher cli args, parse, and launch the Isaac Sim app.

    Returns (args_cli, hydra_args, app_launcher, simulation_app).
    """
    AppLauncher.add_app_launcher_args(parser)
    args_cli, hydra_args = parser.parse_known_args()
    if args_cli.video:
        args_cli.enable_cameras = True
    sys.argv = [sys.argv[0]] + hydra_args
    app_launcher = AppLauncher(args_cli)
    simulation_app = app_launcher.app
    return args_cli, hydra_args, app_launcher, simulation_app
