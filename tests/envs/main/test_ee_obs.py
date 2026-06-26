"""Tests for EE-position observation toggle (Task 5: 69D -> 71D)."""
from constrained_albc.envs.main.config import ALBCEnvCfg


def test_obs_space_71_when_ee_enabled():
    cfg = ALBCEnvCfg()
    cfg.ee_action_enable = True
    cfg.__post_init__() if hasattr(cfg, "__post_init__") else None
    # observation_space must reflect the +2D EE term when enabled
    from constrained_albc.envs.main.config import resolve_observation_space

    assert resolve_observation_space(cfg) == 71


def test_obs_space_69_when_ee_disabled():
    from constrained_albc.envs.main.config import resolve_observation_space

    cfg = ALBCEnvCfg()
    assert resolve_observation_space(cfg) == 69


def test_noise_model_71d_when_ee_enabled():
    cfg = ALBCEnvCfg()
    cfg.ee_action_enable = True
    cfg.__post_init__()
    assert len(cfg.observation_noise_model.noise_cfg.std) == 71
    assert len(cfg.observation_noise_model.bias_noise_cfg.n_min) == 71
    assert len(cfg.observation_noise_model.bias_noise_cfg.n_max) == 71


def test_noise_model_69d_when_ee_disabled():
    cfg = ALBCEnvCfg()
    assert len(cfg.observation_noise_model.noise_cfg.std) == 69
