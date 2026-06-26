import torch
from constrained_albc.envs.main.mdp.rewards import ee_anchor, ALBCRewardCfg


class _FakeLayer:
    def __init__(self, ee):
        self.ee_target = ee


class _FakeEnv:
    def __init__(self, ee, nom):
        self._ee_layer = _FakeLayer(ee)
        self.cfg = type("C", (), {"reward": ALBCRewardCfg(nom_ee=nom)})()


def test_anchor_zero_at_nominal():
    env = _FakeEnv(torch.tensor([[0.233, 0.233]]), (0.233, 0.233))
    assert torch.allclose(ee_anchor(env), torch.zeros(1), atol=1e-6)


def test_anchor_is_squared_distance():
    env = _FakeEnv(torch.tensor([[0.333, 0.233]]), (0.233, 0.233))
    # |(0.1, 0)|^2 = 0.01
    assert torch.allclose(ee_anchor(env), torch.tensor([0.01]), atol=1e-6)
