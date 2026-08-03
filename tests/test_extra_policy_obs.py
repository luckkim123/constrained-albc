"""Gen-2 extra-policy-obs (obs4 Phase D): fold the 4 deployable channels into policy_obs.

Gen-1 published the 4 channels (IMU specific force 3D + pressure-derived heave rate 1D) as a
side key that only the student encoder read, leaving the teacher's frozen actor blind to them.
Phase C could not separate that blindness from capacity crowding, so gen-2 folds the same 4
channels into policy_obs itself (72 -> 76) and retrains the teacher.

The materializer is exercised the same way test_bias_ema_obs.py exercises apply_bias_ema_obs:
extracted via AST and exec'd standalone, so the whole file runs without Isaac Sim. The env-side
width tracking cannot be exercised that way (ALBCEnv needs Isaac), so it is checked at source
level instead -- each of the three width-tracking sites must mention the flag by name, which is
what actually breaks if a future edit adds a fourth site and forgets this one.

Each test names the production change that makes it fail:
  - off_is_noop            -> deleting the `if not cfg.use_extra_policy_obs: return` guard
  - bumps_and_extends      -> bumping by 3 instead of 4, or padding non-zero noise
  - mutually_exclusive     -> deleting the gen-1/gen-2 exclusivity precondition
  - rejects_double_apply   -> deleting the pre-bump width check
  - noise_model_none       -> dropping the `is not None` guard (AttributeError on eval path)
  - composes_with_bias_ema -> hardcoding a 72-only pre-bump width
  - env_width_sites        -> adding the +4 to only some of the three env-side sites
  - shared_extra_tensor    -> calling compute_student_extra_obs twice per step
  - step_guard             -> dropping the _extra_last_step de-duplication
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

_MAIN = Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main"
_CONFIG_PATH = _MAIN / "config.py"
_ENV_PATH = _MAIN / "albc_env.py"


def _load_apply_extra_policy_obs():
    """Extract apply_extra_policy_obs's source via AST and exec it standalone.

    Body has zero external references (builtins + attribute access on the passed cfg).
    """
    tree = ast.parse(_CONFIG_PATH.read_text())
    func_node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "apply_extra_policy_obs"
    )
    namespace: dict = {}
    exec(compile(ast.unparse(func_node), "<apply_extra_policy_obs>", "exec"), namespace)
    return namespace["apply_extra_policy_obs"]


def _make_fake_cfg(*, use_extra_policy_obs: bool, use_student_extra_obs: bool, observation_space: int):
    width = observation_space
    return SimpleNamespace(
        use_extra_policy_obs=use_extra_policy_obs,
        use_student_extra_obs=use_student_extra_obs,
        observation_space=observation_space,
        observation_noise_model=SimpleNamespace(
            noise_cfg=SimpleNamespace(std=tuple(0.01 for _ in range(width))),
            bias_noise_cfg=SimpleNamespace(
                n_min=tuple(-0.01 for _ in range(width)),
                n_max=tuple(0.01 for _ in range(width)),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# (1) Static config contract
# ---------------------------------------------------------------------------


def test_gen2_toggle_is_off_by_default():
    """Gen-2 must default OFF: every teacher trained so far is 72D, and flipping this
    default would silently change the width of every existing recipe."""
    assigns = {}
    for node in ast.walk(ast.parse(_CONFIG_PATH.read_text())):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant):
                assigns[node.target.id] = node.value.value
    assert assigns.get("use_extra_policy_obs") is False


# ---------------------------------------------------------------------------
# (2) apply_extra_policy_obs()
# ---------------------------------------------------------------------------


def test_off_is_noop():
    apply = _load_apply_extra_policy_obs()
    cfg = _make_fake_cfg(use_extra_policy_obs=False, use_student_extra_obs=False, observation_space=72)
    apply(cfg)
    assert cfg.observation_space == 72
    assert len(cfg.observation_noise_model.noise_cfg.std) == 72


def test_bumps_and_extends_vectors_with_four_zeros():
    apply = _load_apply_extra_policy_obs()
    cfg = _make_fake_cfg(use_extra_policy_obs=True, use_student_extra_obs=False, observation_space=72)
    apply(cfg)
    assert cfg.observation_space == 76
    std = cfg.observation_noise_model.noise_cfg.std
    n_min = cfg.observation_noise_model.bias_noise_cfg.n_min
    n_max = cfg.observation_noise_model.bias_noise_cfg.n_max
    assert len(std) == len(n_min) == len(n_max) == 76
    # Zero, not the ambient 0.01: these channels carry their own sensor model, so the
    # generic obs-noise layer must be identity on them or they get double-noised.
    assert std[-4:] == (0.0, 0.0, 0.0, 0.0)
    assert n_min[-4:] == (0.0, 0.0, 0.0, 0.0)
    assert n_max[-4:] == (0.0, 0.0, 0.0, 0.0)


def test_mutually_exclusive_with_gen1_side_channel():
    """Both flags on would hand the student the same signal twice, and would force the
    student to extra_obs_dim>0 -- which train_student.py's consistency check rejects for a
    76D-obs student. A gen-2 student runs extra_obs_dim=0 with the gen-1 flag off."""
    apply = _load_apply_extra_policy_obs()
    cfg = _make_fake_cfg(use_extra_policy_obs=True, use_student_extra_obs=True, observation_space=72)
    with pytest.raises(ValueError, match="mutually exclusive"):
        apply(cfg)


def test_rejects_double_apply():
    apply = _load_apply_extra_policy_obs()
    cfg = _make_fake_cfg(use_extra_policy_obs=True, use_student_extra_obs=False, observation_space=76)
    with pytest.raises(ValueError, match="observation_space"):
        apply(cfg)


def test_bumps_space_when_noise_model_none_eval_path():
    """eval.py nulls observation_noise_model; the 76D policy still needs the space bump."""
    apply = _load_apply_extra_policy_obs()
    cfg = _make_fake_cfg(use_extra_policy_obs=True, use_student_extra_obs=False, observation_space=72)
    cfg.observation_noise_model = None
    apply(cfg)
    assert cfg.observation_space == 76
    assert cfg.observation_noise_model is None


def test_composes_with_bias_ema_off():
    """bias_ema off leaves 69, so gen-2 must accept that pre-bump width too (69 -> 73)."""
    apply = _load_apply_extra_policy_obs()
    cfg = _make_fake_cfg(use_extra_policy_obs=True, use_student_extra_obs=False, observation_space=69)
    apply(cfg)
    assert cfg.observation_space == 73


# ---------------------------------------------------------------------------
# (3) Env-side width tracking, checked at source level (ALBCEnv needs Isaac Sim)
# ---------------------------------------------------------------------------


def test_every_env_width_site_tracks_the_flag():
    """The three env-side sites that must widen together.

    A gen-2 env whose obs-width guard was updated but whose _obs_noise_base_std was not
    would build fine and then feed a 76D obs through a 72D noise std -- a shape error deep
    in the step loop, or worse, silent broadcasting. Fails if a future edit adds the +4 to
    only some of these.
    """
    src = _ENV_PATH.read_text()
    tree = ast.parse(src)
    for fn_name in ("_obs_noise_base_std", "_get_observations"):
        node = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name
        )
        body = ast.unparse(node)
        assert "use_extra_policy_obs" in body, f"{fn_name} does not track use_extra_policy_obs"
    # The obs-width guard lives in __init__ alongside the other expected_obs_dim branches.
    init = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "__init__"
    )
    init_src = ast.unparse(init)
    assert "apply_extra_policy_obs" in init_src, "materializer never called from __init__"
    assert "use_extra_policy_obs" in init_src, "obs-width guard does not account for gen-2"


def test_extra_obs_computed_once_and_shared():
    """compute_student_extra_obs advances the zero-order hold and draws sensor noise.

    Calling it twice in one step would hand policy_obs and the student key two different
    signals -- silently, and only when both flags are on. Fails if a future edit restores
    the second call at the publish site.
    """
    tree = ast.parse(_ENV_PATH.read_text())
    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_get_observations"
    )
    calls = [
        c
        for c in ast.walk(node)
        if isinstance(c, ast.Call)
        and isinstance(c.func, ast.Name)
        and c.func.id == "compute_student_extra_obs"
    ]
    assert len(calls) == 1, f"compute_student_extra_obs called {len(calls)}x per step, expected 1"


def test_extra_obs_advance_is_guarded_by_step_id():
    """The sensor model must advance at most once per env step.

    _get_observations is called an EXTRA time per training iteration by
    ConstraintEncoderRunner.log -> log_encoder_metrics, and compute_student_extra_obs
    advances a differentiator, an LPF and the ZOH tick on every call. Without the guard
    the sensor model runs at the wrong rate -- and, because rsl_rl's logging path is
    outside the inference_mode the buffers were written under, the in-place
    _depth_meas_prev write raises RuntimeError("Inplace update to inference tensor").
    That is what killed the first Phase D launch (2026-08-03).

    Behavioural proof is the live run: a teacher training past its first log() call
    exercises exactly this path. This test is the regression pin against the guard being
    dropped, so it asserts the guard's two moving parts are both wired to the call site.
    """
    tree = ast.parse(_ENV_PATH.read_text())
    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_get_observations"
    )
    body = ast.unparse(node)
    assert "_extra_last_step" in body, "no step-id guard around the sensor-model advance"
    assert "common_step_counter" in body, "step guard is not keyed on the env step counter"
    # The guard is only meaningful if the held sample is what the repeat call returns.
    assert "_student_extra_held" in body, "repeat call does not serve the held sample"

    # Initialised alongside its sibling ZOH state, not in some unrelated place: the whole
    # extra-obs buffer set has to be allocated together or _reset_idx stops being branch-free.
    owner = [
        n.name
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
        and "_extra_tick = 0" in ast.unparse(n)
        and "_extra_last_step" in ast.unparse(n)
    ]
    assert owner, "_extra_last_step is not initialised with the other extra-obs ZOH buffers"
