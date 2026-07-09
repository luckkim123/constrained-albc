# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for tracking reward functions (no Isaac Sim required).

Pins the sign conventions and the roll-weighting so a refactor cannot silently
invert a reward (which would let training run while optimizing the wrong way):

  - tracking rewards (lin/att/yaw): max at zero error (exp=1), monotonically
    decreasing as |err| grows.
  - penalty terms (torque/thruster/smoothness): always >= 0 magnitude; the
    negative weight lives in cfg (k_tau/k_thr/k_s), not in the function.
  - bias_ema_penalty: reads the preallocated env._reward_manager._bias_w
    (regression net for the P0-5 per-step-alloc removal).

Loaded via importlib to bypass constrained_albc.__init__ (which pulls in
isaaclab.sim). rewards.py only needs the configclass decorator.
"""

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

# ---------------------------------------------------------------------------
# Mock the one isaaclab dependency, then load rewards.py directly.
# ---------------------------------------------------------------------------
import dataclasses


def _mock_configclass(cls):
    """Stand-in for isaaclab.utils.configclass.

    rewards.py instantiates configclass types at module load (ALBCRewardCfg has
    nested TrackingTermCfg / tuple defaults), so the mock must build a kwargs
    __init__ like the real (dataclass-based) configclass. Plain @dataclass
    rejects mutable defaults; real configclass wraps them in default_factory, so
    we do the same before delegating to dataclass.
    """
    annotations = getattr(cls, "__annotations__", {})
    for name, value in list(vars(cls).items()):
        if name not in annotations:
            continue
        is_mutable = isinstance(value, (list, dict, set)) or hasattr(value, "__dict__")
        if is_mutable:
            setattr(cls, name, dataclasses.field(default_factory=lambda v=value: v))
    return dataclasses.dataclass(cls)


for _pkg in ("isaaclab", "isaaclab.utils"):
    if _pkg not in sys.modules:
        sys.modules[_pkg] = types.ModuleType(_pkg)
sys.modules["isaaclab.utils"].configclass = _mock_configclass

_REWARDS_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc/envs/main/mdp/rewards.py"
)
_spec = importlib.util.spec_from_file_location("_albc_rewards_under_test", _REWARDS_PATH)
R = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = R
_spec.loader.exec_module(R)

JOINT_IDS = [0, 1]


def _track_term(**kw):
    """A TrackingTermCfg-like object (sigma/quad/lin/saturating fields)."""
    base = dict(k=1.0, sigma=0.10, quad_ratio=1.0, lin_ratio=0.0,
                tanh_coef=0.0, tanh_eps=0.10, arctan_coef=0.0, arctan_eps=0.10)
    base.update(kw)
    return SimpleNamespace(**base)


def _reward_cfg(**kw):
    cfg = SimpleNamespace(
        att_rp=_track_term(), att_roll_weight=1.5,
        lin_vel=_track_term(), yaw_vel=_track_term(),
    )
    for k, v in kw.items():
        setattr(cfg, k, v)
    return cfg


def _env(*, lin_err=None, att_err=None, yaw_err=None, actions=None,
         prev=None, prev_prev=None, bias_ema=None, bias_w=None, reward_cfg=None,
         joint_pos=None):
    rm = SimpleNamespace(_bias_w=bias_w) if bias_w is not None else None
    robot = (
        SimpleNamespace(data=SimpleNamespace(joint_pos=joint_pos))
        if joint_pos is not None else None
    )
    return SimpleNamespace(
        _lin_vel_err=lin_err, _att_rp_err=att_err, _yaw_rate_err=yaw_err,
        _actions=actions, _prev_actions=prev, _prev_prev_actions=prev_prev,
        _bias_ema=bias_ema, _reward_manager=rm, _albc_joint_ids=JOINT_IDS,
        _robot=robot,
        cfg=SimpleNamespace(reward=reward_cfg or _reward_cfg()),
    )


# ---------------------------------------------------------------------------
# Tracking rewards: max at zero error, decreasing with |err|
# ---------------------------------------------------------------------------


def test_yaw_vel_tracking_peaks_at_zero():
    assert R.yaw_vel_tracking(_env(yaw_err=torch.zeros(1))).item() == pytest.approx(1.0)
    near = R.yaw_vel_tracking(_env(yaw_err=torch.tensor([0.05]))).item()
    far = R.yaw_vel_tracking(_env(yaw_err=torch.tensor([0.5]))).item()
    assert near > far


def test_att_rp_roll_weighted_more_than_pitch():
    """Same-magnitude error costs more on roll than pitch (att_roll_weight=1.5)."""
    roll_only = _env(att_err=torch.tensor([[0.2, 0.0]]))
    pitch_only = _env(att_err=torch.tensor([[0.0, 0.2]]))
    # roll error is up-weighted -> lower reward than the same pitch error
    assert R.att_rp_tracking(roll_only).item() < R.att_rp_tracking(pitch_only).item()


def test_att_rp_peaks_at_zero():
    assert R.att_rp_tracking(_env(att_err=torch.zeros(1, 2))).item() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Penalty terms: non-negative magnitude (sign lives in cfg weights)
# ---------------------------------------------------------------------------


def test_joint_torque_nonneg_mean_square():
    robot = SimpleNamespace(data=SimpleNamespace(applied_torque=torch.tensor([[3.0, 4.0]])))
    # mean(3^2, 4^2) = mean(9,16) = 12.5
    assert R.joint_torque(robot, _env()).item() == pytest.approx(12.5)


def test_thruster_energy_uses_thruster_action_slice():
    # actions: [arm0, arm1, thr0..thr5]; only thr slice (idx 2:) counts
    actions = torch.tensor([[9.0, 9.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    # mean of [1,0,0,0,0,0]^2 = 1/6
    assert R.thruster_energy(_env(actions=actions)).item() == pytest.approx(1.0 / 6.0)


def test_action_smoothness_zero_when_constant():
    a = torch.tensor([[0.3, -0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0]])
    env = _env(actions=a, prev=a.clone(), prev_prev=a.clone())
    assert R.action_smoothness(env).item() == pytest.approx(0.0)
    # a moving action -> positive
    env2 = _env(actions=a, prev=torch.zeros_like(a), prev_prev=torch.zeros_like(a))
    assert R.action_smoothness(env2).item() > 0.0


# ---------------------------------------------------------------------------
# bias_ema_penalty: regression net for P0-5 preallocated _bias_w
# ---------------------------------------------------------------------------


def test_bias_ema_uses_preallocated_weights():
    bias_w = torch.tensor([1.5, 1.0, 1.0, 1.0, 1.0, 1.0])
    bias_ema = torch.tensor([[2.0, 0.0, 0.0, 0.0, 0.0, 0.0]])  # roll offset only
    env = _env(bias_ema=bias_ema, bias_w=bias_w)
    # sum(w_i * ema_i^2) = 1.5 * 2^2 = 6.0
    assert R.bias_ema_penalty(env).item() == pytest.approx(6.0)


def test_bias_ema_zero_when_no_offset():
    env = _env(bias_ema=torch.zeros(1, 6), bias_w=torch.ones(6))
    assert R.bias_ema_penalty(env).item() == pytest.approx(0.0)


def test_reward_manager_preallocates_bias_w():
    """RewardManager.__init__ must create _bias_w (the P0-5 change)."""
    cfg = _reward_cfg(bias_weights=(1.5, 1.0, 1.0, 1.0, 1.0, 1.0))
    rm = R.RewardManager(cfg, num_envs=4, device="cpu")
    assert hasattr(rm, "_bias_w")
    assert torch.allclose(rm._bias_w, torch.tensor([1.5, 1.0, 1.0, 1.0, 1.0, 1.0]))
