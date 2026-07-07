# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for the ActuationNoiseCfg subcfg (the 3rd actuation channel).

Skipped if importing the env config boots Isaac Sim (structural-only test).
"""

from __future__ import annotations

import pytest

config = pytest.importorskip("constrained_albc.envs.main.config")


def test_actuation_noise_cfg_defaults_off():
    c = config.ActuationNoiseCfg()
    assert c.enable is False
    assert c.thruster_noise_std == pytest.approx(0.05)
    assert c.joint_noise_std == pytest.approx(0.05)


def test_env_cfg_has_actuation_noise_sibling_of_fault():
    env = config.ALBCEnvCfg()
    # Sibling of fault / randomization, independently toggleable.
    assert isinstance(env.actuation_noise, config.ActuationNoiseCfg)
    assert env.actuation_noise.enable is False
    # The other two channels are untouched (still their own defaults).
    assert env.fault.enable is False
    assert env.randomization.enable is False
