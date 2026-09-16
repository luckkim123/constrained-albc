"""Sim-free contracts for the optional closed-loop-depth/open-loop-XY task."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch


_ROOT = Path(__file__).resolve().parent.parent
_MAIN = _ROOT / "constrained_albc" / "envs" / "main"
_CONFIG_PATH = _MAIN / "config.py"
_ENV_PATH = _MAIN / "albc_env.py"
_OBS_PATH = _MAIN / "mdp" / "observations.py"
_TASK_CFG_PATH = _MAIN / "config_simtoreal_depthxy.py"
_REGISTER_PATH = _MAIN / "__init__.py"


def _function(path: Path, name: str, namespace: dict | None = None):
    tree = ast.parse(path.read_text())
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = {"ALBCEnv": object, "Articulation": object}
    if namespace is not None:
        scope.update(namespace)
    exec(compile(ast.unparse(node), f"<{name}>", "exec"), scope)
    return scope[name]


class _RewardTermCfg(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


def _materializer():
    return _function(
        _CONFIG_PATH,
        "apply_depth_xy_obs",
        {
            "RewardTermCfg": _RewardTermCfg,
            "depth_tracking": lambda *_args, **_kwargs: None,
            "xy_force_tracking": lambda *_args, **_kwargs: None,
        },
    )


def _depth_cfg(enable: bool) -> SimpleNamespace:
    return SimpleNamespace(
        enable=enable,
        depth_offset_range=(-0.5, 0.5),
        depth_error_clip=1.0,
        xy_force_scale=8.0,
        depth_reward_weight=3.0,
        depth_reward_sigma=0.10,
        xy_reward_weight=2.0,
        xy_reward_sigma=2.0,
        doraemon_return_excludes_new_terms=True,
    )


def _materializer_cfg(*, enable: bool, use_extra_policy_obs: bool, obs_dim: int) -> SimpleNamespace:
    return SimpleNamespace(
        depth_xy=_depth_cfg(enable),
        use_extra_policy_obs=use_extra_policy_obs,
        observation_space=obs_dim,
        state_space=28,
        observation_noise_model=SimpleNamespace(
            noise_cfg=SimpleNamespace(std=(0.01,) * obs_dim),
            bias_noise_cfg=SimpleNamespace(n_min=(-0.01,) * obs_dim, n_max=(0.01,) * obs_dim),
        ),
        reward=SimpleNamespace(extra_terms=[]),
    )


def test_depth_xy_defaults_off_and_materializer_is_identity():
    tree = ast.parse(_CONFIG_PATH.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DepthXYCfg")
    enable = next(
        n for n in cls.body if isinstance(n, ast.AnnAssign) and n.target.id == "enable"
    )
    assert ast.literal_eval(enable.value) is False

    cfg = _materializer_cfg(enable=False, use_extra_policy_obs=False, obs_dim=72)
    noise_model = cfg.observation_noise_model
    rewards = cfg.reward.extra_terms
    _materializer()(cfg)
    assert cfg.observation_space == 72
    assert cfg.state_space == 28
    assert cfg.observation_noise_model is noise_model
    assert cfg.reward.extra_terms is rewards


def test_depth_xy_materializer_builds_80d_policy_and_29d_privileged_obs():
    cfg = _materializer_cfg(enable=True, use_extra_policy_obs=True, obs_dim=76)
    _materializer()(cfg)
    assert cfg.observation_space == 80
    assert cfg.state_space == 29
    assert cfg.observation_noise_model.noise_cfg.std[-4:] == (0.0,) * 4
    assert cfg.observation_noise_model.bias_noise_cfg.n_min[-4:] == (0.0,) * 4
    assert cfg.observation_noise_model.bias_noise_cfg.n_max[-4:] == (0.0,) * 4
    assert [(term.name, term.weight, term.params) for term in cfg.reward.extra_terms] == [
        ("depth_tracking", 3.0, {"sigma": 0.10}),
        ("xy_force_tracking", 2.0, {"sigma": 2.0}),
    ]


def test_depth_xy_requires_gen2_extra_policy_obs():
    cfg = _materializer_cfg(enable=True, use_extra_policy_obs=False, obs_dim=72)
    with pytest.raises(ValueError, match="use_extra_policy_obs"):
        _materializer()(cfg)


def test_depth_xy_materializer_supports_eval_without_generic_noise_model():
    cfg = _materializer_cfg(enable=True, use_extra_policy_obs=True, obs_dim=76)
    cfg.observation_noise_model = None
    _materializer()(cfg)
    assert (cfg.observation_space, cfg.state_space) == (80, 29)
    assert cfg.observation_noise_model is None


def test_depth_xy_materializer_rejects_double_apply():
    cfg = _materializer_cfg(enable=True, use_extra_policy_obs=True, obs_dim=80)
    with pytest.raises(ValueError, match="observation_space"):
        _materializer()(cfg)


def _sampler_env(*, enable: bool, zero_prob: float = 0.1, current_depth: float = 0.6):
    n = 16
    return SimpleNamespace(
        cfg=SimpleNamespace(
            play_mode=False,
            att_cmd_rp_range=(-0.5, 0.5),
            yaw_rate_cmd_range=(-0.5, 0.5),
            vel_cmd_zero_prob=zero_prob,
            depth_xy=_depth_cfg(enable),
        ),
        device="cpu",
        _ang_cmd=torch.zeros(n, 3),
        _cmd_att_scale=torch.ones(n),
        _cmd_yaw_scale=torch.ones(n),
        _vel_cmd_step_counter=torch.zeros(n, dtype=torch.long),
        _episode_start_depth=torch.full((n,), 0.5),
        _depth_target=torch.zeros(n),
        _xy_cmd=torch.zeros(n, 2),
        _robot=SimpleNamespace(
            data=SimpleNamespace(
                root_pos_w=torch.tensor([[0.0, 0.0, -current_depth]]).repeat(n, 1)
            )
        ),
    )


def _anchor_sample_velocity_command(self, env_ids: torch.Tensor) -> None:
    if self.cfg.play_mode:
        self._ang_cmd[env_ids] = 0.0
        self._vel_cmd_step_counter[env_ids] = 0
        return
    n = len(env_ids)
    att_max = abs(self.cfg.att_cmd_rp_range[1])
    yaw_max = abs(self.cfg.yaw_rate_cmd_range[1])
    att_s = self._cmd_att_scale[env_ids].unsqueeze(1)
    yaw_s = self._cmd_yaw_scale[env_ids]
    self._ang_cmd[env_ids, :2] = torch.empty(n, 2, device=self.device).uniform_(-1, 1) * (att_max * att_s)
    self._ang_cmd[env_ids, 2] = torch.empty(n, device=self.device).uniform_(-1, 1) * (yaw_max * yaw_s)
    zero_mask = torch.rand(n, device=self.device) < self.cfg.vel_cmd_zero_prob
    if zero_mask.any():
        self._ang_cmd[env_ids[zero_mask]] = 0.0
    self._vel_cmd_step_counter[env_ids] = 0


def test_off_sampler_matches_anchor_and_consumes_no_rng():
    sample = _function(_ENV_PATH, "_sample_velocity_command", {"torch": torch})
    env_ids = torch.arange(16)

    reference = _sampler_env(enable=False)
    torch.manual_seed(418)
    _anchor_sample_velocity_command(reference, env_ids)
    reference_next = torch.rand(8)

    actual = _sampler_env(enable=False)
    torch.manual_seed(418)
    sample(actual, env_ids)
    actual_next = torch.rand(8)

    assert torch.equal(actual._ang_cmd, reference._ang_cmd)
    assert torch.equal(actual_next, reference_next)


def test_on_sampler_ranges_and_hover_draw():
    sample = _function(_ENV_PATH, "_sample_velocity_command", {"torch": torch})
    env_ids = torch.arange(16)

    moving = _sampler_env(enable=True, zero_prob=0.0)
    torch.manual_seed(7)
    sample(moving, env_ids)
    assert torch.all((moving._depth_target - moving._episode_start_depth).abs() <= 0.5)
    assert torch.all(moving._xy_cmd.abs() <= 1.0)

    hover = _sampler_env(enable=True, zero_prob=1.0, current_depth=0.73)
    torch.manual_seed(8)
    sample(hover, env_ids)
    assert torch.equal(hover._ang_cmd, torch.zeros_like(hover._ang_cmd))
    assert torch.equal(hover._depth_target, torch.full_like(hover._depth_target, 0.73))
    assert torch.equal(hover._xy_cmd, torch.zeros_like(hover._xy_cmd))


def test_policy_channel_order_and_clipping():
    compute = _function(_OBS_PATH, "compute_depth_xy_policy_obs", {"torch": torch})
    env = SimpleNamespace(
        cfg=SimpleNamespace(depth_xy=SimpleNamespace(depth_error_clip=1.0)),
        _depth_meas_held=torch.tensor([2.0, 0.4]),
        _depth_target=torch.tensor([0.5, 0.5]),
        _depth_error_integral=torch.tensor([0.25, -0.25]),
        _xy_cmd=torch.tensor([[0.2, -0.3], [-0.4, 0.5]]),
    )
    assert torch.allclose(
        compute(env),
        torch.tensor([[1.0, 0.25, 0.2, -0.3], [-0.1, -0.25, -0.4, 0.5]]),
    )


def test_privileged_depth_error_is_noise_free_and_appended_last():
    node = next(
        n
        for n in ast.walk(ast.parse(_OBS_PATH.read_text()))
        if isinstance(n, ast.FunctionDef) and n.name == "compute_privileged_obs"
    )
    body = ast.unparse(node)
    fault_append = body.index("p_t = torch.cat([p_t, health]")
    depth_append = body.index("p_t = torch.cat([p_t, true_error.unsqueeze(-1)]")
    assert depth_append > fault_append
    assert "depth = -env._robot.data.root_pos_w[:, 2]" in body


def test_new_task_cfg_and_registration_are_pinned():
    cfg_tree = ast.parse(_TASK_CFG_PATH.read_text())
    cls = next(
        n
        for n in cfg_tree.body
        if isinstance(n, ast.ClassDef) and n.name == "ALBCSimToRealDepthXYEnvCfg"
    )
    assert [ast.unparse(base) for base in cls.bases] == ["ALBCSimToRealEnvCfg"]
    assigns = {
        node.target.id: ast.unparse(node.value)
        for node in cls.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert set(assigns) == {"use_extra_policy_obs", "depth_xy"}
    assert assigns["use_extra_policy_obs"] == "True"
    assert assigns["depth_xy"] == "DepthXYCfg(enable=True)"

    reg_tree = ast.parse(_REGISTER_PATH.read_text())
    registrations = []
    for call in (n for n in ast.walk(reg_tree) if isinstance(n, ast.Call)):
        if not (isinstance(call.func, ast.Attribute) and call.func.attr == "register"):
            continue
        kwargs = {kw.arg: kw.value for kw in call.keywords}
        if "id" in kwargs and ast.literal_eval(kwargs["id"]) == (
            "Isaac-ConstrainedALBC-TRPO-SimToReal-DepthXY-v0"
        ):
            registrations.append(kwargs)
    assert len(registrations) == 1
    registered = ast.unparse(registrations[0]["kwargs"])
    assert "config_simtoreal_depthxy:ALBCSimToRealDepthXYEnvCfg" in registered
    assert "agents.rsl_rl_ppo_cfg:ALBCTRPORunnerCfg" in registered


def test_doraemon_exclusion_flag_is_wired_to_reward_manager_and_accumulator():
    tree = ast.parse(_ENV_PATH.read_text())
    init_rewards = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_init_task_and_rewards"
    )
    get_rewards = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_get_rewards"
    )
    assert "doraemon_return_excludes_new_terms" in ast.unparse(init_rewards)
    reward_body = ast.unparse(get_rewards)
    assert "doraemon_return_excludes_new_terms" in reward_body
    assert "doraemon_step_reward" in reward_body


def test_depth_integral_uses_shared_leak_clamp_and_resets():
    tree = ast.parse(_ENV_PATH.read_text())
    get_rewards = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_get_rewards"
    )
    reset = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_reset_task_and_state"
    )
    reward_body = ast.unparse(get_rewards)
    assert "self._depth_error_integral.mul_(self.cfg.integral_leak)" in reward_body
    assert "self.cfg.integral_clamp" in reward_body
    assert "self._depth_error_integral[env_ids] = 0.0" in ast.unparse(reset)


def test_encoder_bounds_append_depth_error_after_optional_fault_health():
    runner_path = (
        _ROOT
        / "constrained_albc"
        / "envs"
        / "_core"
        / "runners"
        / "constraint_encoder_runner.py"
    )
    src = runner_path.read_text()
    fault = src.index("lower = lower + [0.0] * 6")
    depth = src.index("lower = lower + [-env_cfg.depth_xy.depth_error_clip]")
    assert depth > fault
