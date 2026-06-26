import math
import torch
from constrained_albc.envs.main.ee_action import EEActionLayer

NOM = (0.233, 0.233)

def _layer(n=4, **kw):
    return EEActionLayer(num_envs=n, device="cpu", **kw)

def test_reset_sets_ee_target_to_fk_of_current_joints():
    layer = _layer()
    cur = torch.tensor([[0.0, math.pi / 2]] * 4)
    layer.reset(torch.arange(4), cur)
    # FK(0, pi/2) = (0.233, 0.233)
    assert torch.allclose(layer.ee_target, torch.tensor([NOM] * 4), atol=1e-5)

def test_zero_action_with_leak_holds_near_nominal():
    layer = _layer(ee_leak=0.02)
    cur = torch.tensor([[0.0, math.pi / 2]] * 4)
    layer.reset(torch.arange(4), cur)
    for _ in range(50):
        cur = layer.step(torch.zeros(4, 2), cur)
    # zero action + leak pulling to nominal: EE target stays at nominal
    assert torch.allclose(layer.ee_target, torch.tensor([NOM] * 4), atol=1e-4)

def test_biased_action_reaches_finite_equilibrium_not_boundary():
    layer = _layer(ee_delta_scale=0.02, ee_leak=0.05)
    cur = torch.tensor([[0.0, math.pi / 2]] * 1)
    layer.reset(torch.arange(1), cur)
    a = torch.tensor([[1.0, 0.0]])  # saturated +x bias
    for _ in range(300):
        cur = layer.step(a, cur)
    r = layer.ee_target.norm(dim=-1)
    # leak bounds drift: must NOT pin to workspace boundary 0.466
    assert (r < 0.466 - 1e-3).all(), f"drifted to boundary: r={r}"

def test_output_is_finite_for_out_of_reach_action():
    layer = _layer(ee_delta_scale=10.0)  # huge step -> immediately out of reach
    cur = torch.tensor([[0.1, 0.5]] * 4)
    layer.reset(torch.arange(4), cur)
    out = layer.step(torch.ones(4, 2), cur)
    assert torch.isfinite(out).all()

def test_step_is_differentiable_wrt_action():
    layer = _layer()
    cur = torch.tensor([[0.1, 0.5]] * 4)
    layer.reset(torch.arange(4), cur)
    a = torch.zeros(4, 2, requires_grad=True)
    out = layer.step(a, cur)
    out.sum().backward()
    assert a.grad is not None and torch.isfinite(a.grad).all()
