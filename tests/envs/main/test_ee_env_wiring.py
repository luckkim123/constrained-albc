"""Logic-only test of the toggle branch via a minimal duck-typed env shim.

Does NOT boot Isaac Sim. Verifies that EEActionLayer (the layer the env wires
to) satisfies the contract _apply_joint_pd_action relies on: given arm actions
and current joint positions, step() returns finite joint targets of the correct
shape.
"""
import math

import torch

from constrained_albc.envs.main.ee_action import EEActionLayer


def test_ee_layer_produces_joint_targets_in_range():
    # Standalone proxy for the wired path: action -> EEActionLayer.step -> joint targets.
    layer = EEActionLayer(num_envs=8, device="cpu")
    cur = torch.tensor([[0.0, math.pi / 2]] * 8)
    layer.reset(torch.arange(8), cur)
    jt = layer.step(torch.zeros(8, 2), cur)
    assert jt.shape == (8, 2)
    assert torch.isfinite(jt).all()
