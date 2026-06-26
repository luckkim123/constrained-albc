from constrained_albc.envs.main.config import ALBCEnvCfg
from constrained_albc.envs.main.mdp.rewards import ALBCRewardCfg


def test_ee_cfg_defaults_are_off():
    cfg = ALBCEnvCfg()
    assert cfg.ee_action_enable is False
    assert cfg.ee_delta_scale == 0.02
    assert cfg.ee_leak == 0.02
    assert cfg.nom_ee == (0.233, 0.233)


def test_anchor_reward_default_zero():
    r = ALBCRewardCfg()
    assert r.k_anchor == 0.0
    assert r.nom_ee == (0.233, 0.233)


def test_observation_space_stays_69_when_ee_off():
    cfg = ALBCEnvCfg()
    assert cfg.observation_space == 69
