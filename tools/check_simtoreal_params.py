#!/usr/bin/env python3
"""as-run gate for the section-5 plant. Plain python3, no Isaac boot needed:

    cd /workspace/constrained-albc && python3 tools/check_simtoreal_params.py <run_dir>...

Diffs what a run ACTUALLY used -- `<run_dir>/params/env.yaml`, written by the launcher
after Hydra resolution -- against the seven plant overrides and three DORAEMON
fields that `config_simtoreal.py` re-declares for the retrain-simtoreal-2026-09
section-5 plant. Exit 0 if every field matches, 1 if any does not, so it can
gate a launch script. `--variant` selects the expected table for the two N6 arms
(`config_simtoreal.py` `ALBCSimToRealNoDoraemonEnvCfg` / `ALBCSimToRealNoDREnvCfg`).

WHY THIS EXISTS. The seven plant fields default to the OLD plant in the code, so a launch that
forgets the override block trains happily on 40 N/unit, zero delay, no faults and lb=250
-- the configuration `finding/315` measured stalling -- and reports nothing wrong. That
is the shape of `finding/318`: a run that looked successful and was scored on the wrong
plant. `finding/352` is filed as needs-apply-before-retrain for exactly this and asks for
the way to forget the block to be removed. paper-ablation-5000 PLAN.md §4-5 answers with
per-arm cfg subclasses (`config_simtoreal.py`) AND this check, because a cfg subclass is
only a promise until something reads what the run actually did. §8-R-2 calls the A6 arm a
"pipeline canary" -- it is only a canary if this runs on its output.

WHY NOT A PYTEST CASE. The repo already has `tests/test_simtoreal_cfg.py`, which resolves
the config objects directly; it cannot run in this container, because a standalone
AppLauncher exits 0 mid-Kit-boot with no traceback (`finding/352`, `finding/379`), so the
test passes by not running. Reading the YAML the run left behind needs neither Isaac nor
torch, so this check actually executes. It also measures a different thing: the config
class says what was *configured*, this says what was *used*.

The env.yaml carries `!!python/object` tags for torch tensors, which is why the PyYAML
loader below drops unknown python tags instead of `yaml.unsafe_load` (that import chain
needs torch and defeats the point of a dependency-free gate).
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

# field path -> (expected value, why it moved)
SECTION5_PLANT: dict[tuple[str, ...], tuple[object, str]] = {
    ("thrusters", "thrust_coefficient"): (13.0, "R-1 measured band; was 40.0"),
    ("randomization", "thrust_coefficient_scale"): ((0.5, 2.0), "was (0.7, 1.3)"),
    ("randomization", "control_delay_steps"): ((0, 3), "finding/264, 152 ms; was (0, 0)"),
    ("fault", "enable"): (True, "was False"),
    ("fault", "thruster_fail_prob"): (0.30, "was 0.10"),
    ("fault", "thruster_dead_frac"): (0.5, "was 0.0"),
    ("doraemon", "performance_lb"): (200.0, "finding/315; was 250.0"),
    # Derived from both frozen_params/p3b_r2050/env.yaml and p5_r4450/env.yaml;
    # both artifacts agreed: enable=True, kl_ub=0.12, step_interval=250.
    ("doraemon", "enable"): (
        True,
        "config_simtoreal.py re-declares this because a bare "
        "DoraemonCfg(performance_lb=200.0) would silently reset enable/kl_ub/step_interval",
    ),
    ("doraemon", "kl_ub"): (
        0.12,
        "config_simtoreal.py re-declares this because a bare "
        "DoraemonCfg(performance_lb=200.0) would silently reset enable/kl_ub/step_interval",
    ),
    ("doraemon", "step_interval"): (
        250,
        "config_simtoreal.py re-declares this because a bare "
        "DoraemonCfg(performance_lb=200.0) would silently reset enable/kl_ub/step_interval",
    ),
}

# N6b collapses every physics DR range to a point: the eval `none` nominal table
# (analysis/dr_config._TRUE_NOMINAL_PHYSICS) plus the two buoy scales it omits.
# Written out, not imported: a gate that reads the table it checks cannot catch a
# wrong table, and dr_config's import chain needs the sim stack.
N6B_POINTS: dict[str, float] = {
    "added_mass_scale": 1.0, "linear_damping_scale": 1.0, "quadratic_damping_scale": 1.0,
    "volume_scale": 1.0, "inertia_scale": 1.0, "body_mass_scale": 1.0,
    "buoy_volume_scale": 1.0, "buoy_body_mass_scale": 1.0, "yaw_damping_scale": 1.0,
    "joint_effort_limit_range": 1.0, "thrust_coefficient_scale": 1.0,
    "time_constant_scale": 1.0, "max_thrust_scale": 1.0,
    "cob_offset_x": 0.0, "cob_offset_y": 0.0, "cob_offset_z": 0.0,
    "cog_offset_x": 0.0, "cog_offset_y": 0.0, "cog_offset_z": 0.0,
    "water_density_range": 1000.0, "joint_stiffness_range": 100.0, "joint_damping_range": 3.0,
    "joint_static_friction_range": 0.0, "joint_viscous_friction_range": 0.0,
    "payload_mass_range": 0.0, "payload_cog_offset_z": 0.0,
    "payload_cog_offset_xy_u_range": 0.0, "ocean_current_strength_range": 0.0,
    "obs_noise_scale_range": 0.0,
}

_N6_NO_DORAEMON = {
    ("doraemon", "enable"): (False, "N6 arms train with the DORAEMON curriculum off"),
    ("randomization", "enable"): (True, "enable=False would also skip the thruster-fault draw"),
}

VARIANTS: dict[str, dict[tuple[str, ...], tuple[object, str]]] = {
    "section5": SECTION5_PLANT,
    "n6-nodoraemon": SECTION5_PLANT | _N6_NO_DORAEMON,
    "n6-nodr": SECTION5_PLANT
    | _N6_NO_DORAEMON
    | {("randomization", k): ((v, v), "N6b nominal point") for k, v in N6B_POINTS.items()}
    | {
        ("randomization", "payload_cog_offset_xy_radius"): (0.0, "N6b nominal point"),
        ("randomization", "fault_severity_range"): ((0.0, 1.0), "N6b keeps N6a's fault draw"),
    },
}


class _TolerantLoader(yaml.SafeLoader):
    """SafeLoader that keeps tuples and drops every other python tag."""


_TolerantLoader.add_constructor("tag:yaml.org,2002:python/tuple", lambda ldr, node: tuple(ldr.construct_sequence(node)))
_TolerantLoader.add_multi_constructor("tag:yaml.org,2002:python/", lambda ldr, suffix, node: None)


def _dig(cfg: object, path: tuple[str, ...]) -> object:
    for key in path:
        if not isinstance(cfg, dict):
            return None
        cfg = cfg.get(key)
    return cfg


def _resolve(run: pathlib.Path) -> pathlib.Path:
    """Accept a run dir, its params/ dir, or the env.yaml itself."""
    if run.is_file():
        return run
    for candidate in (run / "params" / "env.yaml", run / "env.yaml"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"no params/env.yaml under {run}")


def check(run: pathlib.Path, variant: str = "section5") -> bool:
    path = _resolve(run)
    cfg = yaml.load(path.read_text(), Loader=_TolerantLoader)
    ok = True
    print(f"\n{path}")
    for field, (expected, why) in VARIANTS[variant].items():
        actual = _dig(cfg, field)
        # yaml gives lists for sequences that were not tagged as tuples.
        if isinstance(actual, list) and isinstance(expected, tuple):
            actual = tuple(actual)
        hit = actual == expected
        ok &= hit
        print(
            f"  [{'ok ' if hit else 'BAD'}] {'.'.join(field):45s} {actual!r:14s}"
            f" expected {expected!r}" + ("" if hit else f"   ({why})")
        )
    print(f"  => {variant}" if ok else f"  => NOT {variant}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--variant", choices=VARIANTS, default="section5")
    ap.add_argument("run_dir", nargs="+", type=pathlib.Path, help="run directory, its params/ dir, or an env.yaml")
    args = ap.parse_args()
    return 0 if all([check(r, args.variant) for r in args.run_dir]) else 1


if __name__ == "__main__":
    sys.exit(main())
