# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free unit tests for the Koopman arm-B marine-feature lift.

Two things can silently void the arm, and each gets a test here:

1. ``compute_marine_features`` emitting the wrong columns -- the report would compare a
   dictionary nobody designed.
2. ``MARINE_SRC_IDX`` drifting out of sync with ``compute_policy_obs``'s channel order --
   the features would be built from the wrong signals (joint angles instead of body rates,
   say) and the run would look like a clean null instead of a broken instrument.

Loads observations.py standalone (bypasses constrained_albc/__init__ -> isaaclab.sim ->
pxr), the same pattern tests/test_student_extra_obs.py uses.
"""

import importlib.util
import types
from pathlib import Path

import torch

_OBS_PATH = Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "mdp" / "observations.py"


def _load_observations():
    spec = importlib.util.spec_from_file_location("albc_observations_marine", _OBS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_marine_features_are_the_seven_designed_columns():
    """Values and order, against hand-computed truth."""
    obs = _load_observations()
    src = torch.tensor([[0.3, -0.7, 2.0, -3.0, 0.5]])
    out = obs.compute_marine_features(src)

    assert out.shape == (1, 7), out.shape
    expected = torch.tensor([
        [
            torch.sin(torch.tensor(0.3)),
            torch.cos(torch.tensor(0.3)),
            torch.sin(torch.tensor(-0.7)),
            torch.cos(torch.tensor(-0.7)),
            4.0,    # p|p| =  2.0 * 2.0
            -9.0,   # q|q| = -3.0 * 3.0  -- signed, NOT squared
            0.25,   # r|r| =  0.5 * 0.5
        ]
    ])
    assert torch.allclose(out, expected, atol=1e-6), f"{out} != {expected}"


def test_signed_quadratic_rates_keep_their_sign():
    """A plain square would pass the shape check and destroy the drag direction."""
    obs = _load_observations()
    pos = obs.compute_marine_features(torch.tensor([[0.0, 0.0, 1.5, 1.5, 1.5]]))
    neg = obs.compute_marine_features(torch.tensor([[0.0, 0.0, -1.5, -1.5, -1.5]]))
    assert torch.all(pos[:, 4:] > 0) and torch.all(neg[:, 4:] < 0)
    assert torch.allclose(pos[:, 4:], -neg[:, 4:])


def test_marine_src_idx_points_at_roll_pitch_and_body_rates():
    """Guards the index mapping against a reordering of compute_policy_obs.

    Fails if anyone inserts or moves a channel in the 20D proprio block without updating
    MARINE_SRC_IDX -- the failure mode that would leave the arm training on the wrong
    signals while every width assert still passes.
    """
    obs = _load_observations()
    n, dev = 2, "cpu"
    roll = torch.tensor([0.11, 0.12])
    pitch = torch.tensor([0.21, 0.22])
    yaw = torch.tensor([0.31, 0.32])
    ang_vel = torch.tensor([[0.41, 0.51, 0.61], [0.42, 0.52, 0.62]])

    env = types.SimpleNamespace(
        _euler_cache=(roll, pitch, yaw),
        _ang_cmd=torch.full((n, 3), -1.0),
        _albc_joint_ids=[0, 1],
        _manipulability=torch.full((n,), -2.0),
        _thruster=None,
        num_envs=n,
        device=dev,
    )
    robot = types.SimpleNamespace(
        data=types.SimpleNamespace(
            joint_pos=torch.full((n, 2), -3.0),
            joint_vel=torch.full((n, 2), -4.0),
            root_ang_vel_b=ang_vel,
        )
    )

    proprio = obs.compute_policy_obs(env, robot)
    assert proprio.shape == (n, 20), proprio.shape

    picked = proprio[:, obs.MARINE_SRC_IDX]
    want = torch.stack([roll, pitch, ang_vel[:, 0], ang_vel[:, 1], ang_vel[:, 2]], dim=-1)
    assert torch.allclose(picked, want), f"MARINE_SRC_IDX picked {picked}, expected {want}"

    # The sentinels above are all negative; a correct pick contains none of them.
    assert torch.all(picked > 0), "MARINE_SRC_IDX is reading a command/arm/thruster channel"


if __name__ == "__main__":
    test_marine_features_are_the_seven_designed_columns()
    test_signed_quadratic_rates_keep_their_sign()
    test_marine_src_idx_points_at_roll_pitch_and_body_rates()
    print("marine-feature obs: 3/3 checks passed")
