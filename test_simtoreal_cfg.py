"""Proves ALBCSimToRealEnvCfg == ALBCEnvCfg + the seven p3b_resume.sh overrides.

A config variant that merely LOOKS like the override block is worth nothing -- the
lesson from `feedback-each-arm-own-plant-confounds-comparison` is that a change is
verified at the resolved output, never at the source that requested it. So this
diffs the two resolved configs and asserts the difference set is EXACTLY the seven
fields, with exactly the launched values, and nothing else moved.

Run:  /isaac-sim/python.sh test_simtoreal_cfg.py   (needs an idle box: Kit takes a lock)

"""
import argparse

from isaaclab.app import AppLauncher

# These cfgs are plain dataclasses, but importing them pulls isaaclab.sim, which needs
# USD/omni bindings that exist only inside a launched Kit app. Stubbing them out was
# tried and rejected: a stubbed field would resolve to a stub object and the diff would
# pass vacuously. So the app is launched for real, the way eval.py does it -- a bare
# AppLauncher({"headless": True}) boots Kit and then exits 0 during startup with no
# traceback, because add_app_launcher_args() is what fills in the experience file and
# the rest of the launcher defaults. Kit also takes a process-wide lock, so run this
# when no eval is running.
_parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(_parser)
_args = _parser.parse_args(["--headless"])
app = AppLauncher(_args).app

from isaaclab.utils import class_to_dict  # noqa: E402

from constrained_albc.envs.main.config import ALBCEnvCfg  # noqa: E402
from constrained_albc.envs.main.config_simtoreal import ALBCSimToRealEnvCfg  # noqa: E402

# The override block, verbatim from g0c_runner/p3b_resume.sh (COMMON + DELTA).
EXPECTED = {
    "fault.enable": True,
    "fault.thruster_fail_prob": 0.30,
    "fault.thruster_dead_frac": 0.5,
    "randomization.control_delay_steps": (0, 3),
    "thrusters.thrust_coefficient": 13.0,
    "randomization.thrust_coefficient_scale": (0.5, 2.0),
    "doraemon.performance_lb": 200.0,
}


def flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        p = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flat(v, p + "."))
        else:
            out[p] = v
    return out


def norm(v):
    return tuple(v) if isinstance(v, (list, tuple)) else v


base = flat(class_to_dict(ALBCEnvCfg()))
variant = flat(class_to_dict(ALBCSimToRealEnvCfg()))
assert base, "class_to_dict returned nothing -- the comparison would vacuously pass"

assert base.keys() == variant.keys(), (
    f"field set changed: only-in-base={base.keys() - variant.keys()}, "
    f"only-in-variant={variant.keys() - base.keys()}"
)

moved = {k for k in base if norm(base[k]) != norm(variant[k])}

unexpected = moved - EXPECTED.keys()
assert not unexpected, f"variant changed fields the override block does not: {sorted(unexpected)}"

missing = EXPECTED.keys() - moved
assert not missing, (
    "these overrides did NOT take effect in the variant -- it equals the default here: "
    + str({k: base[k] for k in sorted(missing)})
)

for k, want in EXPECTED.items():
    got = norm(variant[k])
    assert got == norm(want), f"{k}: variant has {got!r}, override block says {want!r}"

print(f"PASS  {len(base)} fields compared; exactly {len(moved)} moved, all seven as launched")
for k in sorted(EXPECTED):
    print(f"  {k:44} {base[k]!r:>11}  ->  {norm(variant[k])!r}")
app.close()
