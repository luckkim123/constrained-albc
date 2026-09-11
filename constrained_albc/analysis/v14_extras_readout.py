#!/usr/bin/env python3
"""Read A1/A3/A4 extras from a static evaluation without Isaac Lab or torch."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


_MOMENT_SOURCES = (
    "thr",
    "hull_hydro",
    "buoy",
    "payload",
    "grav_buoy",
    "grav_arm",
    "grav_hull",
)


def _alive_from_terminated(terminated: np.ndarray) -> np.ndarray:
    """The terminating step itself is excluded, matching the paper's pre-capsize interval."""
    return ~np.asarray(terminated, dtype=bool)


def _discounted_ctg_sum_forward(cost: np.ndarray, gamma: float) -> float:
    """Sum all truncated discounted cost-to-go values in O(T) forward time."""
    c = np.asarray(cost, dtype=np.float64)
    j = np.arange(1, c.size + 1, dtype=np.float64)
    if gamma == 1.0:
        weights = j
    else:
        weights = (1.0 - np.power(gamma, j)) / (1.0 - gamma)
    return float(np.dot(c, weights))


def _max_window_excursion(
    theta: np.ndarray,
    time_s: np.ndarray,
    alive: np.ndarray,
    window_s: float = 30.0,
) -> np.ndarray:
    """Largest absolute pairwise excursion within a time window, independently per env."""
    theta = np.asarray(theta, dtype=np.float64)
    time_s = np.asarray(time_s, dtype=np.float64)
    alive = np.asarray(alive, dtype=bool)
    if theta.ndim == 1:
        theta = theta[:, None]
    if alive.ndim == 1:
        alive = alive[:, None]
    has_alive = np.any(alive, axis=0)
    result = np.where(has_alive, 0.0, np.nan)

    # Walk time lags (the 30 s W) while vectorizing every pair comparison over envs.
    for lag in range(1, theta.shape[0]):
        in_window = time_s[lag:] - time_s[:-lag] <= window_s
        if not np.any(in_window):
            break
        valid = alive[lag:] & alive[:-lag] & in_window[:, None]
        delta = np.abs(theta[lag:] - theta[:-lag])
        candidate = np.max(np.where(valid, delta, -np.inf), axis=0)
        result = np.where(has_alive, np.maximum(result, candidate), np.nan)
    return result


def _aggregate(values: np.ndarray) -> dict[str, float]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {name: float("nan") for name in ("mean", "median", "p90", "max")}
    return {
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "p90": float(np.percentile(finite, 90)),
        "max": float(np.max(finite)),
    }


def _constraint_metrics(
    costs: np.ndarray,
    alive: np.ndarray,
    terminated: np.ndarray,
    names: list[str],
    budgets: list[float],
    gamma: float,
) -> dict[str, Any]:
    costs = np.asarray(costs, dtype=np.float64)
    if costs.shape[:2] != alive.shape:
        raise ValueError(f"costs shape {costs.shape} does not match alive shape {alive.shape}")
    if costs.shape[2] != len(names) or len(names) != len(budgets):
        raise ValueError(
            f"cost channels/names/budgets disagree: {costs.shape[2]}, {len(names)}, {len(budgets)}"
        )

    n_envs = alive.shape[1]
    result: dict[str, Any] = {}
    for k, (name, budget) in enumerate(zip(names, budgets, strict=True)):
        per_env = {
            metric: np.full(n_envs, np.nan, dtype=np.float64)
            for metric in ("act_rate", "c_mean", "c_over_D", "J_start", "J_ctg_mean", "margin", "J_over_d")
        }
        d_k = budget / (1.0 - gamma) if gamma != 1.0 else float("inf")
        for env_idx in range(n_envs):
            c = costs[:, env_idx, k][alive[:, env_idx]]
            if c.size == 0:
                continue
            per_env["act_rate"][env_idx] = np.mean(c > 0.0)
            per_env["c_mean"][env_idx] = np.mean(c)
            per_env["c_over_D"][env_idx] = np.mean(c) / budget if budget != 0.0 else np.nan
            per_env["J_start"][env_idx] = np.dot(np.power(gamma, np.arange(c.size)), c)
            per_env["J_ctg_mean"][env_idx] = _discounted_ctg_sum_forward(c, gamma) / c.size
            per_env["margin"][env_idx] = d_k - per_env["J_ctg_mean"][env_idx]
            per_env["J_over_d"][env_idx] = (
                per_env["J_ctg_mean"][env_idx] / d_k if d_k != 0.0 else np.nan
            )
        total_alive = int(np.count_nonzero(alive))
        pooled_active = int(np.count_nonzero((costs[:, :, k] > 0.0) & alive))
        result[name] = {
            "budget_D": float(budget),
            "d_k": float(d_k),
            "n_envs": n_envs,
            "n_envs_terminated": int(np.count_nonzero(np.any(terminated, axis=0))),
            "pooled_act_rate": pooled_active / total_alive if total_alive else float("nan"),
            "aggregate": {metric: _aggregate(values) for metric, values in per_env.items()},
            "per_env": {metric: values.tolist() for metric, values in per_env.items()},
        }
    return result


def _joint1_source_metrics(
    theta: np.ndarray,
    time_s: np.ndarray,
    alive: np.ndarray,
) -> dict[str, Any]:
    theta = np.asarray(theta, dtype=np.float64)
    n_envs = theta.shape[1]
    max_rad = np.full(n_envs, np.nan)
    drift = np.full(n_envs, np.nan)
    for env_idx in range(n_envs):
        indices = np.flatnonzero(alive[:, env_idx])
        if indices.size == 0:
            continue
        values = theta[indices, env_idx]
        max_rad[env_idx] = np.max(np.abs(values - values[0]))
        elapsed_min = (time_s[indices[-1]] - time_s[indices[0]]) / 60.0
        if elapsed_min > 0.0:
            drift[env_idx] = (values[-1] - values[0]) / (2.0 * np.pi) / elapsed_min
    window_rad = _max_window_excursion(theta, time_s, alive, window_s=30.0)
    max_turns = max_rad / (2.0 * np.pi)
    window_turns = window_rad / (2.0 * np.pi)
    per_env = {
        "max_excursion_rad": max_rad,
        "max_excursion_turns": max_turns,
        "max_excursion_30s_rad": window_rad,
        "max_excursion_30s_turns": window_turns,
        "net_drift_rev_per_min": drift,
    }
    return {
        "n_envs_over_1_rev": int(np.count_nonzero(max_turns > 1.0)),
        "aggregate": {metric: _aggregate(values) for metric, values in per_env.items()},
        "per_env": {metric: values.tolist() for metric, values in per_env.items()},
    }


def _masked_per_env_stat(values: np.ndarray, alive: np.ndarray, operation: str) -> np.ndarray:
    result = np.full(values.shape[1], np.nan, dtype=np.float64)
    for env_idx in range(values.shape[1]):
        selected = values[:, env_idx][alive[:, env_idx]]
        if selected.size:
            if operation == "min":
                result[env_idx] = np.min(selected)
            elif operation == "max":
                result[env_idx] = np.max(selected)
            elif operation == "mean_abs":
                result[env_idx] = np.mean(np.abs(selected))
            else:
                raise ValueError(f"unknown operation: {operation}")
    return result


def _joint_metrics(
    data: dict[str, np.ndarray],
    extras: dict[str, np.ndarray],
    time_s: np.ndarray,
    alive: np.ndarray,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "joint1_target": _joint1_source_metrics(data["joint1_target"], time_s, alive)
    }
    if "joint_pos" in extras:
        joint_pos = np.asarray(extras["joint_pos"], dtype=np.float64)
        unwrapped = np.unwrap(joint_pos, period=4.0 * np.pi, axis=0)
        result["joint1_measured_unwrapped"] = _joint1_source_metrics(
            unwrapped[..., 0], time_s, alive
        )
        theta2_min = _masked_per_env_stat(unwrapped[..., 1], alive, "min")
        theta2_max = _masked_per_env_stat(unwrapped[..., 1], alive, "max")
        result["theta2_unwrapped"] = {
            "min_rad": _aggregate(theta2_min),
            "max_rad": _aggregate(theta2_max),
            "range_rad": _aggregate(theta2_max - theta2_min),
            "per_env_min_rad": theta2_min.tolist(),
            "per_env_max_rad": theta2_max.tolist(),
            "per_env_range_rad": (theta2_max - theta2_min).tolist(),
        }
    if "joint_vel" in extras:
        joint_vel = np.asarray(extras["joint_vel"], dtype=np.float64)
        result["mean_abs_qdot"] = {}
        for joint_idx, name in enumerate(("joint1", "joint2")):
            values = _masked_per_env_stat(joint_vel[..., joint_idx], alive, "mean_abs")
            result["mean_abs_qdot"][name] = {
                "aggregate": _aggregate(values),
                "per_env": values.tolist(),
            }
    return result


def _rms(values: np.ndarray, mask: np.ndarray) -> float:
    selected = np.asarray(values, dtype=np.float64)[mask]
    return float(np.sqrt(np.mean(np.square(selected)))) if selected.size else float("nan")


def _moment_scope(extras: dict[str, np.ndarray], mask: np.ndarray) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for axis, axis_idx in (("roll_x", 0), ("pitch_y", 1)):
        rms_by_source = {
            source: _rms(extras[f"m_{source}"][..., axis_idx], mask)
            for source in _MOMENT_SOURCES
        }
        buoy_net_rms = _rms(
            np.asarray(extras["m_buoy"], dtype=np.float64)[..., axis_idx]
            + np.asarray(extras["m_grav_buoy"], dtype=np.float64)[..., axis_idx],
            mask,
        )
        buoy_denom = rms_by_source["buoy"] + rms_by_source["thr"]
        buoy_net_denom = buoy_net_rms + rms_by_source["thr"]
        result[axis] = {
            "rms": rms_by_source,
            "buoy_net_rms": buoy_net_rms,
            "buoy_share": rms_by_source["buoy"] / buoy_denom if buoy_denom else float("nan"),
            "buoy_net_share": buoy_net_rms / buoy_net_denom if buoy_net_denom else float("nan"),
        }
    return result


def _moment_metrics(
    data: dict[str, np.ndarray],
    extras: dict[str, np.ndarray],
    alive: np.ndarray,
) -> dict[str, Any]:
    missing = [f"m_{source}" for source in _MOMENT_SOURCES if f"m_{source}" not in extras]
    if missing:
        raise ValueError(f"moment recording is incomplete; missing {', '.join(missing)}")
    result = {"all_alive": _moment_scope(extras, alive)}
    target_roll = np.asarray(data.get("target_roll_deg", np.zeros(alive.shape[0])))
    target_pitch = np.asarray(data.get("target_pitch_deg", np.zeros(alive.shape[0])))
    attitude_steps = (target_roll != 0.0) | (target_pitch != 0.0)
    if np.any(attitude_steps):
        result["attitude_block"] = _moment_scope(extras, alive & attitude_steps[:, None])
    return result


def analyze_level(
    data: dict[str, np.ndarray],
    extras: dict[str, np.ndarray],
    meta: dict[str, Any],
) -> dict[str, Any]:
    terminated = np.asarray(data["terminated"], dtype=bool)
    time_s = np.asarray(data["time"], dtype=np.float64)
    alive = _alive_from_terminated(terminated)
    result: dict[str, Any] = {
        "n_envs": int(alive.shape[1]),
        "n_envs_terminated": int(np.count_nonzero(np.any(terminated, axis=0))),
        "alive_steps": int(np.count_nonzero(alive)),
    }
    if "costs" in extras:
        result["constraints"] = _constraint_metrics(
            extras["costs"],
            alive,
            terminated,
            list(meta["constraint_names"]),
            list(meta["constraint_budgets"]),
            float(meta["cost_gamma"]),
        )
    if "joint1_target" in data:
        result["joints"] = _joint_metrics(data, extras, time_s, alive)
    if "m_thr" in extras:
        result["moments"] = _moment_metrics(data, extras, alive)
    return result


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _fmt(value: Any, digits: int = 3) -> str:
    return "--" if value is None or not np.isfinite(value) else f"{value:.{digits}f}"


def _print_markdown(report: dict[str, Any]) -> None:
    constraint_rows = []
    joint_rows = []
    moment_rows = []
    for level, values in report["levels"].items():
        for name, constraint in values.get("constraints", {}).items():
            agg = constraint["aggregate"]
            pooled_rate = constraint["pooled_act_rate"]
            constraint_rows.append(
                (
                    level,
                    name,
                    100.0 * pooled_rate if pooled_rate is not None else None,
                    agg["c_over_D"]["mean"],
                    agg["J_over_d"]["mean"],
                    agg["margin"]["mean"],
                )
            )
        for source in ("joint1_target", "joint1_measured_unwrapped"):
            if source not in values.get("joints", {}):
                continue
            joint = values["joints"][source]
            turns = joint["aggregate"]["max_excursion_turns"]
            window = joint["aggregate"]["max_excursion_30s_turns"]
            drift = joint["aggregate"]["net_drift_rev_per_min"]
            joint_rows.append(
                (level, source, turns["mean"], turns["p90"], turns["max"], window["p90"],
                 drift["mean"], joint["n_envs_over_1_rev"])
            )
        for scope, axes in values.get("moments", {}).items():
            for axis, moment in axes.items():
                moment_rows.append(
                    (level, scope, axis, moment["rms"]["thr"], moment["rms"]["buoy"],
                     moment["buoy_net_rms"], moment["buoy_share"], moment["buoy_net_share"])
                )

    if constraint_rows:
        print("\n| Level | Constraint | Active % | mean c/D | mean J/d | mean margin |")
        print("|---|---|---:|---:|---:|---:|")
        for row in constraint_rows:
            print(f"| {row[0]} | {row[1]} | {_fmt(row[2], 2)} | {_fmt(row[3])} | {_fmt(row[4])} | {_fmt(row[5])} |")
    if joint_rows:
        print("\n| Level | Joint1 source | Excursion turns mean/P90/max | 30s P90 | Drift rev/min | >1 rev |")
        print("|---|---|---:|---:|---:|---:|")
        for row in joint_rows:
            triple = "/".join(_fmt(value) for value in row[2:5])
            print(f"| {row[0]} | {row[1]} | {triple} | {_fmt(row[5])} | {_fmt(row[6])} | {row[7]} |")
    if moment_rows:
        print("\n| Level | Scope | Axis | Thr RMS | Buoy RMS | Net buoy RMS | Buoy share | Net share |")
        print("|---|---|---|---:|---:|---:|---:|---:|")
        for row in moment_rows:
            print(
                f"| {row[0]} | {row[1]} | {row[2]} | {_fmt(row[3])} | {_fmt(row[4])} | "
                f"{_fmt(row[5])} | {_fmt(row[6])} | {_fmt(row[7])} |"
            )


def _find_levels(output_dir: Path) -> list[str]:
    found = {path.stem.removeprefix("extras_") for path in output_dir.glob("extras_*.npz")}
    preferred = [level for level in ("none", "soft", "medium", "hard", "ood") if level in found]
    return preferred + sorted(found.difference(preferred))


def run_selftest() -> None:
    rng = np.random.default_rng(714)
    c = rng.random(50)
    gamma = 0.99
    n = 37
    brute = sum(sum(gamma ** (j - t) * c[j] for j in range(t, n)) for t in range(n))
    np.testing.assert_allclose(_discounted_ctg_sum_forward(c[:n], gamma), brute, rtol=1e-12)

    terminated = np.zeros((8, 2), dtype=bool)
    terminated[5:, 0] = True
    alive = _alive_from_terminated(terminated)
    assert np.flatnonzero(alive[:, 0]).tolist() == [0, 1, 2, 3, 4]

    true_theta = np.linspace(0.0, 12.0 * np.pi, 121)[:, None]
    wrapped = (true_theta + 2.0 * np.pi) % (4.0 * np.pi) - 2.0 * np.pi
    recovered = np.unwrap(wrapped, period=4.0 * np.pi, axis=0)
    np.testing.assert_allclose(np.max(np.abs(recovered - recovered[0])), 12.0 * np.pi)

    short_theta = rng.normal(size=(30, 3)).cumsum(axis=0)
    short_time = np.arange(30, dtype=float) * 0.7
    short_alive = np.ones_like(short_theta, dtype=bool)
    actual = _max_window_excursion(short_theta, short_time, short_alive, window_s=3.0)
    expected = np.zeros(3)
    for env_idx in range(3):
        expected[env_idx] = max(
            abs(short_theta[i, env_idx] - short_theta[j, env_idx])
            for i in range(30) for j in range(30)
            if abs(short_time[i] - short_time[j]) <= 3.0
        )
    np.testing.assert_allclose(actual, expected)
    print("v14 extras readout selftest passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", nargs="?", help="Static evaluation output directory.")
    parser.add_argument("--json", dest="json_path", default=None, help="Full JSON output path.")
    parser.add_argument("--levels", default=None, help="Comma-separated subset of levels found.")
    parser.add_argument("--selftest", action="store_true", help="Run pure-numpy regression checks.")
    args = parser.parse_args()

    if args.selftest:
        run_selftest()
        return 0
    if args.output_dir is None:
        parser.error("output_dir is required unless --selftest is used")

    output_dir = Path(args.output_dir)
    with (output_dir / "extras_meta.json").open() as stream:
        meta = json.load(stream)
    found = _find_levels(output_dir)
    if args.levels is None:
        levels = found
    else:
        requested = [level.strip() for level in args.levels.split(",") if level.strip()]
        unknown = sorted(set(requested).difference(found))
        if not requested or unknown:
            bad = ", ".join(unknown) if unknown else "<empty>"
            raise SystemExit(f"Unknown --levels value(s): {bad}. Available levels: {', '.join(found)}")
        levels = [level for level in found if level in requested]
    if not levels:
        raise SystemExit(f"No extras_<level>.npz files found in {output_dir}")

    report: dict[str, Any] = {"meta": meta, "levels": {}}
    for level in levels:
        data_path = output_dir / f"data_{level}.npz"
        extras_path = output_dir / f"extras_{level}.npz"
        with np.load(data_path, allow_pickle=False) as archive:
            data = {key: archive[key] for key in archive.files}
        with np.load(extras_path, allow_pickle=False) as archive:
            extras = {key: archive[key] for key in archive.files}
        report["levels"][level] = analyze_level(data, extras, meta)

    report = _jsonable(report)
    json_path = Path(args.json_path) if args.json_path else output_dir / "v14_extras_readout.json"
    if json_path.parent != Path(""):
        os.makedirs(json_path.parent, exist_ok=True)
    with json_path.open("w") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(f"Full JSON: {json_path}")
    _print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
