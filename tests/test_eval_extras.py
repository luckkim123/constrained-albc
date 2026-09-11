#!/usr/bin/env python3
"""Plain numpy/torch regression tests for static-eval extras (no Isaac Lab import)."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import pathlib
import sys
import types

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_module(name: str, path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_readout() -> types.ModuleType:
    return _load_module("v14_extras_readout_test", ROOT / "constrained_albc/analysis/v14_extras_readout.py")


def test_cost_to_go_identity() -> None:
    readout = _load_readout()
    rng = np.random.default_rng(1209)
    costs = rng.random(50)
    gamma = 0.99
    n_alive = 37
    brute = sum(
        sum(gamma ** (j - t) * costs[j] for j in range(t, n_alive))
        for t in range(n_alive)
    )
    actual = readout._discounted_ctg_sum_forward(costs[:n_alive], gamma)
    np.testing.assert_allclose(actual, brute, rtol=1e-12, atol=1e-12)


def test_alive_masking() -> None:
    readout = _load_readout()
    terminated = np.zeros((10, 1), dtype=bool)
    terminated[5:, 0] = True
    alive = readout._alive_from_terminated(terminated)
    costs = np.ones((10, 1, 1), dtype=np.float32)
    costs[5:, 0, 0] = 1000.0
    result = readout._constraint_metrics(costs, alive, terminated, ["probe"], [1.0], 0.99)
    assert np.flatnonzero(alive[:, 0]).tolist() == [0, 1, 2, 3, 4]
    np.testing.assert_allclose(result["probe"]["per_env"]["c_mean"], [1.0])


def test_unwrap_and_window() -> None:
    readout = _load_readout()
    true_theta = np.linspace(0.0, 12.0 * np.pi, 241)[:, None]
    wrapped = (true_theta + 2.0 * np.pi) % (4.0 * np.pi) - 2.0 * np.pi
    recovered = np.unwrap(wrapped, period=4.0 * np.pi, axis=0)
    turns = np.max(np.abs(recovered - recovered[0])) / (2.0 * np.pi)
    np.testing.assert_allclose(turns, 6.0, atol=1e-6)

    rng = np.random.default_rng(887)
    theta = rng.normal(size=(36, 4)).cumsum(axis=0)
    time_s = np.cumsum(rng.uniform(0.05, 0.5, size=36))
    alive = np.ones_like(theta, dtype=bool)
    alive[29:, 2] = False
    window_s = 2.0
    actual = readout._max_window_excursion(theta, time_s, alive, window_s)
    expected = np.zeros(theta.shape[1])
    for env_idx in range(theta.shape[1]):
        indices = np.flatnonzero(alive[:, env_idx])
        expected[env_idx] = max(
            abs(theta[i, env_idx] - theta[j, env_idx])
            for i in indices for j in indices
            if abs(time_s[i] - time_s[j]) <= window_s
        )
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


def _argument_defaults(tree: ast.AST) -> dict[str, object]:
    defaults: dict[str, object] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        if not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            continue
        for keyword in node.keywords:
            if keyword.arg == "default" and isinstance(keyword.value, ast.Constant):
                defaults[node.args[0].value] = keyword.value.value
    return defaults


def test_default_path_static_guard() -> None:
    source_path = ROOT / "constrained_albc/analysis/eval.py"
    source = source_path.read_text()
    tree = ast.parse(source)
    defaults = _argument_defaults(tree)
    assert defaults["--save-extras"] is False
    assert defaults["--save-moments"] is False
    assert defaults["--levels"] is None

    # The selector may skip loop entries, but must not rebuild DR_LEVELS and alter seed indices.
    for node in ast.walk(tree):
        targets = []
        value = None
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
        if any(isinstance(target, ast.Name) and target.id == "DR_LEVELS" for target in targets):
            value_source = ast.get_source_segment(source, value) or ""
            assert "args_cli.levels" not in value_source

    array_data_is_filtered = False
    write_uses_array_data = False
    extras_is_popped = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "array_data" for target in node.targets
        ):
            if isinstance(node.value, ast.DictComp):
                value_source = ast.get_source_segment(source, node.value) or ""
                array_data_is_filtered |= "isinstance" in value_source and "np.ndarray" in value_source
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "write_eval_npz":
            write_uses_array_data |= any(
                isinstance(arg, ast.Name) and arg.id == "array_data" for arg in node.args
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "pop":
            extras_is_popped |= bool(
                node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "_extras"
            )
    assert array_data_is_filtered
    assert write_uses_array_data
    assert extras_is_popped


def test_quaternion_helpers() -> None:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("torch tests require torch; run --numpy-only outside the container") from exc
    extras = _load_module("eval_extras_math_test", ROOT / "constrained_albc/analysis/_eval_dr/extras.py")
    half = np.pi / 4.0
    q = torch.tensor([[np.cos(half), 0.0, 0.0, np.sin(half)]], dtype=torch.float64)
    x = torch.tensor([[1.0, 0.0, 0.0]], dtype=torch.float64)
    y = extras.quat_rotate(q, x)
    torch.testing.assert_close(y, torch.tensor([[0.0, 1.0, 0.0]], dtype=torch.float64), atol=1e-12, rtol=1e-12)
    torch.testing.assert_close(extras.quat_rotate_inverse(q, y), x, atol=1e-12, rtol=1e-12)

    q_batch = q.repeat(3, 1)
    x_batch = x.repeat(3, 1)
    assert extras.quat_rotate(q_batch, x_batch).shape == (3, 3)
    assert extras.quat_rotate_inverse(q_batch, x_batch).shape == (3, 3)


def test_moment_about() -> None:
    import torch

    extras = _load_module("eval_extras_moment_test", ROOT / "constrained_albc/analysis/_eval_dr/extras.py")
    ident = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
    origin = torch.zeros((1, 3), dtype=torch.float64)
    point_x = torch.tensor([[1.0, 0.0, 0.0]], dtype=torch.float64)
    force_z = torch.tensor([[0.0, 0.0, 10.0]], dtype=torch.float64)
    zero = torch.zeros((1, 3), dtype=torch.float64)
    actual = extras.moment_about(origin, ident, point_x, ident, force_z, zero)
    torch.testing.assert_close(actual, torch.tensor([[0.0, -10.0, 0.0]], dtype=torch.float64))

    half = np.pi / 4.0
    q_z = torch.tensor([[np.cos(half), 0.0, 0.0, np.sin(half)]], dtype=torch.float64)
    rotated_ref = extras.moment_about(origin, q_z, point_x, ident, force_z, zero)
    torch.testing.assert_close(
        rotated_ref, torch.tensor([[-10.0, 0.0, 0.0]], dtype=torch.float64), atol=1e-12, rtol=1e-12
    )
    torque_x_local = torch.tensor([[1.0, 0.0, 0.0]], dtype=torch.float64)
    pure_torque = extras.moment_about(origin, q_z, origin, q_z, zero, torque_x_local)
    torch.testing.assert_close(pure_torque, torque_x_local, atol=1e-12, rtol=1e-12)


def test_gravity_moment_about() -> None:
    import torch

    extras = _load_module("eval_extras_gravity_test", ROOT / "constrained_albc/analysis/_eval_dr/extras.py")
    ident = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float64)
    origin = torch.zeros((1, 3), dtype=torch.float64)
    com = torch.tensor([[0.0, 1.0, 0.0]], dtype=torch.float64)
    mass = torch.ones(1, dtype=torch.float64)
    gravity = torch.tensor([0.0, 0.0, -9.81], dtype=torch.float64)
    actual = extras.gravity_moment_about(origin, ident, com, mass, gravity)
    torch.testing.assert_close(actual, torch.tensor([[-9.81, 0.0, 0.0]], dtype=torch.float64))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--numpy-only",
        action="store_true",
        help="Run the readout and AST tests only (for hosts without torch).",
    )
    args = parser.parse_args()

    numpy_tests = (
        test_cost_to_go_identity,
        test_alive_masking,
        test_unwrap_and_window,
        test_default_path_static_guard,
    )
    torch_tests = (test_quaternion_helpers, test_moment_about, test_gravity_moment_about)
    for test in numpy_tests:
        test()
    print(f"numpy/AST eval-extras checks passed ({len(numpy_tests)})")
    if not args.numpy_only:
        for test in torch_tests:
            test()
        print(f"torch eval-extras checks passed ({len(torch_tests)})")
    else:
        print(f"torch eval-extras checks not run ({len(torch_tests)}; --numpy-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
