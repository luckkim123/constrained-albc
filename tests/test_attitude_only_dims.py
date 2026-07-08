"""Sim-free dimension-consistency checks for the attitude_only experiment group.

Mirrors the env's dimension-contract guard (albc_env.py:141) without importing Isaac Sim:
    observation_space == PROPRIO_DIM + 13_or_10*hist_len + 8*hist_action_len + integral_dims
For attitude_only, the body history feature drops lin_vel_err (3D), so body 9 -> 6, making
the per-(joint+body) history slice 13 -> 10.
"""

# Expected attitude_only dimensions (the design contract):
PROPRIO_DIM = 20          # was 26: dropped vel_cmd_lin(3) + measured lin_vel(3)
HIST_LEN = 3
HIST_ACTION_LEN = 2
JOINT_BODY_PER_STEP = 10  # was 13: joint(4) + body(6); body dropped lin_vel_err(3)
ACTION_PER_STEP = 8
INTEGRAL_DIMS = 3         # was 6: [roll, pitch, yaw_rate]; dropped vx,vy,vz
STATE_SPACE = 28          # was 27: appended control-action delay (1) to p_t tail


def _expected_obs_dim():
    return (
        PROPRIO_DIM
        + JOINT_BODY_PER_STEP * HIST_LEN
        + ACTION_PER_STEP * HIST_ACTION_LEN
        + INTEGRAL_DIMS
    )


def test_expected_observation_space():
    # 20 + 10*3 + 8*2 + 3 = 20 + 30 + 16 + 3 = 69
    assert _expected_obs_dim() == 69


def test_config_matches_expected_dims():
    """The config module's declared dims must match the design contract.

    Imports ONLY the config dataclass defaults via ast, never instantiating the env.
    """
    import ast
    import pathlib

    cfg_path = pathlib.Path(__file__).parents[1] / "constrained_albc" / "envs" / "main" / "config.py"
    tree = ast.parse(cfg_path.read_text())
    assigns = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant):
                assigns[node.target.id] = node.value.value
    assert assigns.get("observation_space") == _expected_obs_dim()
    assert assigns.get("state_space") == STATE_SPACE
    assert assigns.get("integral_dims") == INTEGRAL_DIMS
    assert assigns.get("hist_feature_dim") == JOINT_BODY_PER_STEP + ACTION_PER_STEP  # 18
