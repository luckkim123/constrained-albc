# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Byte-identity + decouple guard for the R1 integral-obs gate threshold.

Sim-free (AST + source), mirroring tests/test_bias_ema_obs.py check (1): booting a
real ALBCEnv would need Isaac Sim, so the static contract is asserted instead.

R1 (reward_sigma wiki review): the integral-obs settling-band gate historically COPIED
reward.att_rp.sigma (roll, pitch) and reward.yaw_vel.sigma (yaw_rate) at env init
(albc_env.py) -- one scalar aliased two orthogonal knobs (reward-kernel width AND the
gate threshold), so a reward-kernel ablation silently retuned the gate. R1 adds an
independent cfg field `integral_gate_threshold` that the gate reads instead.

Two guarantees:
  (1) BYTE-IDENTITY at the decouple: the default MUST equal the historical shared-sigma
      value (att_rp.sigma = yaw_vel.sigma = 0.10 -> gate = (0.10, 0.10, 0.10)), so
      today's behavior is unchanged.
  (2) DECOUPLE: the env's gate build must read `integral_gate_threshold`, NOT
      `reward.*.sigma` -- otherwise the aliasing survives. Note this test deliberately
      does NOT tie the default to the *live* reward sigma: after R1 they are independent,
      so a future reward-sigma retune must not break this test.
"""

from __future__ import annotations

import ast
from pathlib import Path

CONFIG_PY = Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "config.py"
ALBC_ENV_PY = Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "albc_env.py"

# Historical pre-R1 gate values [roll, pitch, yaw_rate], copied from reward.att_rp.sigma
# (roll, pitch) and reward.yaw_vel.sigma (yaw_rate), both 0.10 (config yaw_vel sigma=0.10;
# att_rp sigma=0.10 in ALBCRewardCfg; wiki reward_sigma review, code-verified 2026-07-24).
HISTORICAL_GATE = (0.10, 0.10, 0.10)


def _default_of(source: str, name: str):
    """Return the literal default assigned to top-level class attr `name` (AnnAssign/Assign)."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target == name and node.value is not None:
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} default not found in source")


def test_default_threshold_is_byte_identical_to_historical_gate():
    """integral_gate_threshold default must reproduce the pre-R1 (0.10, 0.10, 0.10) gate."""
    val = _default_of(CONFIG_PY.read_text(), "integral_gate_threshold")
    assert tuple(val) == HISTORICAL_GATE, (
        f"integral_gate_threshold default {val} != historical gate {HISTORICAL_GATE} "
        "-- the R1 decouple is no longer byte-identical at default"
    )


def test_env_gate_reads_threshold_not_reward_sigma():
    """The env's _integral_gate_sigmas build must use integral_gate_threshold, not reward.*.sigma."""
    src = ALBC_ENV_PY.read_text()
    i = src.index("self._integral_gate_sigmas = torch.tensor")
    # inspect the assignment statement (up to the closing of torch.tensor(...))
    build = src[i : src.index(")", i) + 1]
    assert "integral_gate_threshold" in build, "gate build does not read integral_gate_threshold"
    assert "reward.att_rp.sigma" not in build and "reward.yaw_vel.sigma" not in build, (
        "gate build still references reward.*.sigma -- the shared-sigma aliasing was not removed"
    )
