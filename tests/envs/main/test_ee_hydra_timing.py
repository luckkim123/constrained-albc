"""Regression guard for the hydra-override timing bug.

When train.py launches with env.ee_action_enable=true, isaaclab hydra:
  1. Builds ALBCEnvCfg() -- __post_init__ runs with ee_action_enable=False -> 69D.
  2. Merges the CLI override via from_dict(), which assigns ee_action_enable=True
     directly WITHOUT re-running __post_init__ -> observation_space stays 69D.
  3. ALBCEnv.__init__ is called with the stale 69D cfg.

Before the fix: super().__init__() consumed the stale 69D cfg, then compute_policy_obs
emitted 71D, crashing the per-step assert at albc_env.py:976.

After the fix: apply_ee_obs_space(cfg) runs at the top of ALBCEnv.__init__, BEFORE
super().__init__(), so cfg.observation_space is corrected to 71D in time.

This test reproduces the hydra round-trip WITHOUT Isaac Sim (sim-free) by directly
field-flipping ee_action_enable AFTER construction, mimicking from_dict behaviour.
"""

from constrained_albc.envs.main.config import ALBCEnvCfg, apply_ee_obs_space


# ---------------------------------------------------------------------------
# Hydra timing: field-flip after __post_init__ (the bug reproduction path)
# ---------------------------------------------------------------------------

def test_field_flip_after_post_init_corrected_by_apply_ee_obs_space():
    """Simulate the hydra round-trip: build cfg (ee off -> 69D), then flip field,
    then call apply_ee_obs_space -- as ALBCEnv.__init__ now does before super().
    observation_space must become 71 and noise model must be 71D.
    """
    cfg = ALBCEnvCfg()
    # Confirm __post_init__ locked at 69D (ee off at construction time).
    assert cfg.observation_space == 69, "baseline post_init should be 69D"

    # Simulate hydra from_dict: assign field directly, no __post_init__ re-run.
    cfg.ee_action_enable = True
    # Without the fix, observation_space is still 69 here -- the stale value.
    assert cfg.observation_space == 69, "stale hydra state should still be 69D before apply"

    # The fix: ALBCEnv.__init__ calls apply_ee_obs_space before super().__init__().
    apply_ee_obs_space(cfg)

    # Now cfg must be 71D.
    assert cfg.observation_space == 71, "apply_ee_obs_space must correct to 71D"

    # Noise model must also be 71D.
    noise_std = cfg.observation_noise_model.noise_cfg.std
    assert len(noise_std) == 71, f"noise std must be 71D, got {len(noise_std)}"
    bias_min = cfg.observation_noise_model.bias_noise_cfg.n_min
    assert len(bias_min) == 71, f"bias n_min must be 71D, got {len(bias_min)}"
    bias_max = cfg.observation_noise_model.bias_noise_cfg.n_max
    assert len(bias_max) == 71, f"bias n_max must be 71D, got {len(bias_max)}"


# ---------------------------------------------------------------------------
# Toggle-off: baseline path must remain byte-identical (ee_action_enable=False)
# ---------------------------------------------------------------------------

def test_apply_ee_obs_space_off_keeps_69d():
    """When ee_action_enable=False, apply_ee_obs_space must leave observation_space=69
    and must NOT replace the noise model (toggle-off byte-identical guarantee).
    """
    cfg = ALBCEnvCfg()
    original_noise_model = cfg.observation_noise_model

    apply_ee_obs_space(cfg)

    assert cfg.observation_space == 69
    # Noise model object must not have been replaced.
    assert cfg.observation_noise_model is original_noise_model


def test_apply_ee_obs_space_idempotent_on_path():
    """Calling apply_ee_obs_space twice when ee on must be idempotent (same values)."""
    cfg = ALBCEnvCfg()
    cfg.ee_action_enable = True
    apply_ee_obs_space(cfg)
    assert cfg.observation_space == 71

    noise_std_first = cfg.observation_noise_model.noise_cfg.std

    apply_ee_obs_space(cfg)
    assert cfg.observation_space == 71
    assert cfg.observation_noise_model.noise_cfg.std == noise_std_first
