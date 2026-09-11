#!/usr/bin/env python3
"""Plain-Python regression checks for tools/check_simtoreal_params.py.

Run inside the container from the repo root with ``python3 tests/test_check_simtoreal_params.py``.
The three artifacts default to the real as-run ``params/env.yaml`` of the runs that define
the cases (logs/ is not tracked, so this only runs where those runs live); override each
with a flag.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import subprocess
import sys
import tempfile

import yaml


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "tools" / "check_simtoreal_params.py"


def _run(path: pathlib.Path, variant: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--variant", variant, str(path)],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _expect(
    path: pathlib.Path, should_pass: bool, field: str | None = None, variant: str = "section5"
) -> subprocess.CompletedProcess[str]:
    result = _run(path, variant)
    if (result.returncode == 0) != should_pass:
        raise AssertionError(
            f"{path}: expected pass={should_pass}, rc={result.returncode}\n{result.stdout}"
        )
    if field is not None and f"[BAD] {field}" not in result.stdout:
        raise AssertionError(f"{path}: expected BAD {field}\n{result.stdout}")
    print(f"[{'pass' if should_pass else 'fail'}] {path.name} [{variant}]" + (f" ({field})" if field else ""))
    return result


def _bad_fields(output: str) -> set[str]:
    return {
        line.split("] ", 1)[1].split()[0]
        for line in output.splitlines()
        if line.startswith("  [BAD]")
    }


def _mutate(source: pathlib.Path, dest: pathlib.Path, old: str, new: str) -> None:
    text = source.read_text()
    if text.count(old) != 1:
        raise AssertionError(f"expected exactly one {old!r} in {source}, got {text.count(old)}")
    dest.write_text(text.replace(old, new))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    T = "logs/rsl_rl/albc_trpo_teacher"
    ap.add_argument("--p3b", type=pathlib.Path, help="section-5 plant run (must pass)",
                    default=pathlib.Path(f"{T}/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/params/env.yaml"))
    ap.add_argument("--smoke", type=pathlib.Path, help="A6 PPO-Enc smoke run (must pass)",
                    default=next(iter(sorted(REPO_ROOT.glob("logs/rsl_rl/albc_ablation/ablation_smoke/ppo-enc_smoke_*/params/env.yaml"))), pathlib.Path("missing-A6-smoke")))
    ap.add_argument("--p5", type=pathlib.Path, help="p5 resumed run, a different plant (must fail)",
                    default=pathlib.Path(f"{T}/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/params/env.yaml"))
    args = ap.parse_args()
    p3b, smoke, p5 = (a if a.is_absolute() else REPO_ROOT / a for a in (args.p3b, args.smoke, args.p5))
    for artifact in (p3b, smoke, p5):
        if not artifact.is_file():
            raise FileNotFoundError(artifact)

    _expect(p3b, True)
    _expect(smoke, True)
    p5_result = _expect(p5, False, "randomization.control_delay_steps")
    p5_bad = _bad_fields(p5_result.stdout)
    if p5_bad != {"randomization.control_delay_steps", "doraemon.performance_lb"}:
        raise AssertionError(f"{p5}: expected only delay and performance_lb, got {p5_bad}\n{p5_result.stdout}")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = pathlib.Path(tmp)
        cases = (
            ("doraemon_enable.yaml", "  enable: true\n  performance_lb: 200.0", "  enable: false\n  performance_lb: 200.0", "doraemon.enable"),
            ("doraemon_kl.yaml", "  kl_ub: 0.12", "  kl_ub: 0.13", "doraemon.kl_ub"),
            ("doraemon_interval.yaml", "  step_interval: 250", "  step_interval: 251", "doraemon.step_interval"),
            ("thrust.yaml", "  thrust_coefficient: 13.0", "  thrust_coefficient: 40.0", "thrusters.thrust_coefficient"),
        )
        for name, old, new, field in cases:
            mutated = tmpdir / name
            _mutate(p3b, mutated, old, new)
            _expect(mutated, False, field)

        # N6 variants. The artifacts are built from p3b by editing the loaded YAML, so
        # every field outside the edit keeps p3b's as-run value.
        spec = importlib.util.spec_from_file_location("gate", CHECKER)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        cfg = yaml.load(p3b.read_text(), Loader=gate._TolerantLoader)

        def dump(name: str) -> pathlib.Path:
            out = tmpdir / name
            out.write_text(yaml.dump(cfg))
            return out

        cfg["doraemon"]["enable"] = False
        n6a = dump("n6a.yaml")
        _expect(n6a, True, variant="n6-nodoraemon")
        _expect(n6a, False, "doraemon.enable")
        _expect(n6a, False, "randomization.inertia_scale", variant="n6-nodr")

        for k, v in gate.N6B_POINTS.items():
            cfg["randomization"][k] = (v, v)
        cfg["randomization"]["payload_cog_offset_xy_radius"] = 0.0
        n6b = dump("n6b.yaml")
        _expect(n6b, True, variant="n6-nodr")
        _expect(n6b, False, "randomization.thrust_coefficient_scale", variant="n6-nodoraemon")

        cfg["randomization"]["buoy_volume_scale"] = (0.75, 1.25)
        _expect(dump("n6b_buoy.yaml"), False, "randomization.buoy_volume_scale", variant="n6-nodr")
        cfg["randomization"]["buoy_volume_scale"] = (1.0, 1.0)
        cfg["randomization"]["enable"] = False
        _expect(dump("n6b_disabled.yaml"), False, "randomization.enable", variant="n6-nodr")

    print("check_simtoreal_params regression checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
