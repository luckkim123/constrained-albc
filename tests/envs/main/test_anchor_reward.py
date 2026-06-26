import torch
from constrained_albc.envs.main.mdp.rewards import ee_anchor, ALBCRewardCfg, RewardManager


class _FakeLayer:
    def __init__(self, ee):
        self.ee_target = ee


class _FakeEnv:
    def __init__(self, ee, nom, num_envs=1, device="cpu"):
        self._ee_layer = _FakeLayer(ee) if ee is not None else None
        self.num_envs = num_envs
        self.device = device
        cfg = ALBCRewardCfg(nom_ee=nom)
        self.cfg = type("C", (), {"reward": cfg})()
        self._reward_manager = RewardManager(cfg, num_envs, device)


def test_anchor_zero_at_nominal():
    env = _FakeEnv(torch.tensor([[0.233, 0.233]]), (0.233, 0.233))
    assert torch.allclose(ee_anchor(env), torch.zeros(1), atol=1e-6)


def test_anchor_is_squared_distance():
    env = _FakeEnv(torch.tensor([[0.333, 0.233]]), (0.233, 0.233))
    # |(0.1, 0)|^2 = 0.01
    assert torch.allclose(ee_anchor(env), torch.tensor([0.01]), atol=1e-6)


def test_anchor_returns_zeros_when_ee_layer_none():
    # Baseline (ee_action_enable=False) sets env._ee_layer = None.
    # ee_anchor is still called eagerly every step by RewardManager.compute();
    # it must return zeros without crashing.
    env = _FakeEnv(None, (0.233, 0.233), num_envs=4, device="cpu")
    out = ee_anchor(env)
    assert out.shape == (4,)
    assert torch.allclose(out, torch.zeros(4))
