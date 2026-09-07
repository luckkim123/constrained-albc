# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Frozen surface of ALBCEnvCfg's observation toggles and their materializers.

Read by AST, never imported: ``constrained_albc.envs.main.config`` needs pxr, so an
import-based test SKIPS in a container without Isaac Sim and therefore guards nothing
there (``test_actuation_noise_cfg.py`` is exactly that case, and an earlier draft of
this test was placed in it and silently skipped). Parsing the source runs everywhere.

Why a frozen set rather than a "these names are gone" assertion: the observation width
is assembled by a chain of materializers (config.apply_*_obs) that ALBCEnv calls in a
fixed order before ``super().__init__()``, and each one both bumps ``observation_space``
and pads the noise/bias tuples. Adding or removing a link silently changes the obs
contract that every checkpoint, deploy pack and student distillation is pinned to, so
the surface is frozen here and a change has to be deliberate.

Removed Koopman keys: isaaclab applies Hydra overrides through ``update_class_from_dict``,
which raises KeyError on ``not hasattr(obj, key)``, so a key absent from this surface is a
key an override cannot set.
"""

from __future__ import annotations

import ast
import os

_CFG = os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "envs", "main", "config.py")

# Every cfg field a materializer reads to widen the observation, and the functions that
# consume them. WP1 (2026-09-07) removed the Koopman pair from both columns.
EXPECTED_OBS_TOGGLES = {
    "use_integral_obs",
    "use_bias_ema_obs",
    "use_extra_policy_obs",
    "use_privileged_fault_obs",
}
EXPECTED_MATERIALIZERS = {
    "apply_bias_ema_obs",
    "apply_extra_policy_obs",
    "apply_privileged_fault_obs",
}
REMOVED_BY_WP1 = {"use_marine_feature_obs", "koopman_module_path"}


def _tree() -> ast.Module:
    with open(_CFG, encoding="utf-8") as fh:
        return ast.parse(fh.read())


def _albc_env_cfg_fields() -> set[str]:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ClassDef) and node.name == "ALBCEnvCfg":
            return {s.target.id for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
    raise AssertionError("ALBCEnvCfg not found in config.py")


def test_obs_toggle_surface_is_frozen():
    fields = _albc_env_cfg_fields()
    assert fields >= EXPECTED_OBS_TOGGLES, EXPECTED_OBS_TOGGLES - fields
    assert not (REMOVED_BY_WP1 & fields), "a WP1-removed Koopman key is back on ALBCEnvCfg"


def test_obs_materializer_surface_is_frozen():
    found = {
        n.name
        for n in _tree().body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("apply_") and n.name.endswith("_obs")
    }
    assert found == EXPECTED_MATERIALIZERS, f"materializer set changed: {found}"
