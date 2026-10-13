#!/usr/bin/env python3
"""Runnable check for --env-dr-anchor. Run with the Isaac python:

    cd /workspace/constrained-albc && /isaac-sim/python.sh tools/check_env_dr_anchor.py

Why a standalone script rather than a pytest case: dr_config imports the env config,
which needs `pxr`, which is only importable after AppLauncher boots. So
tests/test_dr_config.py skips its whole module ("could not import 'dr_config': No
module named 'pxr'") and has never actually exercised this code, and no test in tests/
boots the app -- the three AppLauncher hits there are string literals and comments.

Asserts both halves of the contract:
  OFF (default) -- the hard anchor stays the DomainRandomizationCfg class default, so
                   every exam is byte-identical to the ones run before 2026-09-06.
  ON            -- the hard anchor is the run's own env cfg, so the section-5 band
                   thrust_coefficient_scale=(0.5,2.0) and non-interpolated fields
                   such as control_delay_steps=(0,3) finally reach the exam.
"""
from __future__ import annotations

import argparse
import copy
import os
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args, _ = parser.parse_known_args(["--headless"])
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "constrained_albc", "analysis"))

import dr_config  # noqa: E402
from constrained_albc.envs.main.config import DomainRandomizationCfg  # noqa: E402
from constrained_albc.envs.main.config_simtoreal import ALBCSimToRealEnvCfg  # noqa: E402

FAIL: list[str] = []

# Kit swallows stdout once the app has booted (the script's prints never reach the
# terminal and it exits 0), so every result also goes to a file, line-buffered.
_OUT = open(os.environ.get("ENVDR_OUT", "/tmp/envdr_result.txt"), "w", buffering=1)


def say(msg):
    print(msg)
    _OUT.write(msg + "\n")


def check(label, got, want):
    ok = got == want
    say(f"  {'PASS' if ok else 'FAIL'}  {label}: got {got!r}, want {want!r}")
    if not ok:
        FAIL.append(label)


class _EnvCfgStub:
    """Stands in for env_cfg; capture_env_dr_anchor only reads .randomization."""

    def __init__(self, randomization):
        self.randomization = randomization


default = DomainRandomizationCfg()
s5 = ALBCSimToRealEnvCfg().randomization
say(f"\nclass default thrust_coefficient_scale = {default.thrust_coefficient_scale}")
say(f"section-5     thrust_coefficient_scale = {s5.thrust_coefficient_scale}")
say(f"section-5     control_delay_steps      = {s5.control_delay_steps}")
if default.thrust_coefficient_scale == s5.thrust_coefficient_scale:
    FAIL.append("premise: class default equals the section-5 band -- check proves nothing")

# ---- OFF: historical behaviour -------------------------------------------------
say("\n[OFF] flag not set -- anchor must stay the class default")
check("flag defaults to False", dr_config._USE_ENV_DR_ANCHOR, False)
dr_config.capture_env_dr_anchor(_EnvCfgStub(ALBCSimToRealEnvCfg().randomization))
check("capture is a no-op while off", dr_config._ENV_DR_ANCHOR, None)
check("hard thrust band", dr_config.build_dr_config(1.0).thrust_coefficient_scale,
      default.thrust_coefficient_scale)
check("hard control_delay_steps", dr_config.build_dr_config(1.0).control_delay_steps,
      default.control_delay_steps)

# ---- ON: anchor on the run's own plant -----------------------------------------
say("\n[ON] --env-dr-anchor -- anchor must be the run's env cfg")
dr_config._USE_ENV_DR_ANCHOR = True
dr_config.capture_env_dr_anchor(_EnvCfgStub(ALBCSimToRealEnvCfg().randomization))
check("anchor latched", dr_config._ENV_DR_ANCHOR.thrust_coefficient_scale,
      s5.thrust_coefficient_scale)

hard = dr_config.build_dr_config(1.0)
none = dr_config.build_dr_config(0.0)
mid = dr_config.build_dr_config(0.5)
check("hard thrust band == section-5", hard.thrust_coefficient_scale,
      s5.thrust_coefficient_scale)
check("none thrust band == physics nominal", none.thrust_coefficient_scale, (1.0, 1.0))
lo = 1.0 + 0.5 * (s5.thrust_coefficient_scale[0] - 1.0)
hi = 1.0 + 0.5 * (s5.thrust_coefficient_scale[1] - 1.0)
check("medium thrust band interpolates", mid.thrust_coefficient_scale, (lo, hi))
check("non-interpolated field carries", hard.control_delay_steps, s5.control_delay_steps)

# A later capture must not clobber the first: by then env_cfg.randomization is the
# BUILT cfg, not the plant the run was configured with.
dr_config.capture_env_dr_anchor(_EnvCfgStub(dr_config.build_dr_config(1.0)))
check("first capture wins", dr_config._ENV_DR_ANCHOR.thrust_coefficient_scale,
      s5.thrust_coefficient_scale)

# ---- ON + DORAEMON loaded: the path every exam actually takes -------------------
# `--doraemon-dr` defaults to True, so the hard anchor is normally the checkpoint's own
# learned distribution, built by load_doraemon_dr. thrust_coefficient_scale is NOT a
# DORAEMON-managed param (absent from doraemon.py), so that builder's own base decides
# the band. Uses the real p3b teacher run so load_doraemon_dr actually runs.
say("\n[ON + DORAEMON] the default --doraemon-dr path")
TEACHER = os.path.join(
    REPO, "logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3",
    "trpo_p3b_lb200_s30_r2050_260904_163518",
)
if not os.path.isdir(TEACHER):
    FAIL.append("teacher run dir absent -- the default path went unchecked: %s" % TEACHER)
    say("  FAIL  teacher run dir absent: %s" % TEACHER)
else:
    cfg_full, raw = dr_config.load_doraemon_dr(TEACHER)
    if cfg_full is None:
        FAIL.append("load_doraemon_dr returned None -- the default path went unchecked")
        say("  FAIL  load_doraemon_dr returned None for %s" % TEACHER)
    else:
        say(f"  info  DORAEMON learned dims: {len(raw)}")
        check("DORAEMON cfg keeps the section-5 band",
              cfg_full.thrust_coefficient_scale, s5.thrust_coefficient_scale)
        dr_config._DORAEMON_FULL_DR = cfg_full
        check("hard band under --doraemon-dr",
              dr_config.build_dr_config(1.0).thrust_coefficient_scale,
              s5.thrust_coefficient_scale)
        # A DORAEMON-managed dim must be OVERWRITTEN by the learned distribution, not
        # left at the anchor -- otherwise the anchor would have eaten the curriculum.
        # Comparing learned-vs-anchor cannot show this: this teacher's curriculum is
        # saturated, so the learned bounds legitimately EQUAL the cfg range for most
        # dims (finding/133) and an equal value proves nothing either way. Poison the
        # anchor with a sentinel instead, so "left alone" is unmistakable.
        managed = [k for k in raw if hasattr(s5, k) and k != "thrust_coefficient_scale"]
        if not managed:
            FAIL.append("no DORAEMON-managed dim available to cross-check")
            say("  FAIL  no DORAEMON-managed dim available to cross-check")
        else:
            SENTINEL = (-99.0, -99.0)
            poisoned = copy.deepcopy(dr_config._ENV_DR_ANCHOR)
            for k in managed:
                setattr(poisoned, k, SENTINEL)
            saved = dr_config._ENV_DR_ANCHOR
            dr_config._ENV_DR_ANCHOR = poisoned
            cfg_p, _ = dr_config.load_doraemon_dr(TEACHER)
            dr_config._ENV_DR_ANCHOR = saved
            survivors = [k for k in managed if getattr(cfg_p, k) == SENTINEL]
            check("DORAEMON overwrites every managed dim (sentinel must not survive)",
                  survivors, [])
            check("the unmanaged thrust band still comes from the anchor",
                  cfg_p.thrust_coefficient_scale, s5.thrust_coefficient_scale)

say("\n" + ("FAILED: " + ", ".join(FAIL) if FAIL else "ALL CHECKS PASSED"))
simulation_app.close()
sys.exit(1 if FAIL else 0)
