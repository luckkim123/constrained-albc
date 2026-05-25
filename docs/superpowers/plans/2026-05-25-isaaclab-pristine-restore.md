# isaaclab Pristine Restore + Overlay-Owned Train Entry — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strip our code from `isaaclab/scripts/` (restore to upstream) and move train-entry ownership into the `constrained-albc` overlay, so FullDOF training works while isaaclab stays a pristine upstream fork at the `scripts/` layer.

**Architecture:** Restore four isaaclab files to `upstream/main` and delete nine demo scripts. Replace the thin runpy launcher at `constrained-albc/scripts/train.py` with a full overlay train entry that replicates upstream `train.py`'s `main()` body but owns its own runner-dispatch map (the only divergence from upstream). Registration is handled by a one-shot `builtins.__import__` hook that imports `constrained_albc` when `isaaclab_tasks` is imported.

**Tech Stack:** Python, Isaac Lab v2.3, rsl-rl 3.0.1, gymnasium, git (two repos: `/workspace/isaaclab`, `/workspace/constrained-albc`).

**Design doc:** `constrained-albc/docs/superpowers/specs/2026-05-25-isaaclab-pristine-restore-design.md`

**Critical constraints:**
- `feedback-isaaclab-pristine`: NEVER add our code back to isaaclab `scripts/`. The overlay owns its entry.
- `source/isaaclab_rl` (`weight_decay`) and the forked `rsl_rl` package are an INTENTIONAL fork — do NOT touch them.
- `feedback-no-worktree-experiments`: work in the main repos, no new worktrees.
- Training start is user-controlled; the smoke verification in Task 5 is headless and short (a few iterations), already authorized as part of this fix.

---

## File Structure

| File | Repo | Responsibility | Action |
|---|---|---|---|
| `scripts/reinforcement_learning/rsl_rl/train.py` | isaaclab | upstream RL train script | restore to upstream/main |
| `scripts/reinforcement_learning/rsl_rl/play.py` | isaaclab | upstream RL play script | restore to upstream/main |
| `scripts/reinforcement_learning/rsl_rl/play_student.py` | isaaclab | (our file) | delete |
| `scripts/demos/*.py` (9 files) | isaaclab | (our debug scripts) | delete |
| `source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py` | isaaclab | direct-workflow pkg init | restore to upstream/main |
| `scripts/train.py` | constrained-albc | overlay train entry (owns runner dispatch + registration hook) | rewrite (full entry, replaces thin launcher) |

`merge-base` for all upstream comparisons: `cbf51abb5e98d1b3d497c8c73dc989e9f3628b89`. The `upstream` remote is `https://github.com/isaac-sim/IsaacLab.git`; `upstream/main` is fetched locally.

---

### Task 1: Restore isaaclab RL scripts (train.py, play.py) to upstream

**Files:**
- Modify: `/workspace/isaaclab/scripts/reinforcement_learning/rsl_rl/train.py`
- Modify: `/workspace/isaaclab/scripts/reinforcement_learning/rsl_rl/play.py`

- [ ] **Step 1: Capture the contamination as the failing check**

Run:
```bash
cd /workspace/isaaclab && git grep -n "constrained_full_albc\|_RUNNER_MAP" -- scripts/reinforcement_learning/rsl_rl/train.py scripts/reinforcement_learning/rsl_rl/play.py
```
Expected NOW (the bug): several matches in both files (the `_RUNNER_MAP` block and `isaaclab_tasks.direct.constrained_full_albc.runners` string). This is what we are removing.

- [ ] **Step 2: Restore both files to upstream/main**

Run:
```bash
cd /workspace/isaaclab
git checkout upstream/main -- scripts/reinforcement_learning/rsl_rl/train.py
git checkout upstream/main -- scripts/reinforcement_learning/rsl_rl/play.py
```

- [ ] **Step 3: Verify contamination is gone**

Run:
```bash
cd /workspace/isaaclab && git grep -n "constrained_full_albc\|_RUNNER_MAP" -- scripts/reinforcement_learning/rsl_rl/train.py scripts/reinforcement_learning/rsl_rl/play.py; echo "exit=$?"
```
Expected: NO matches, `exit=1` (git grep found nothing). The files now match upstream.

- [ ] **Step 4: Verify the files are byte-identical to upstream**

Run:
```bash
cd /workspace/isaaclab
diff <(git show upstream/main:scripts/reinforcement_learning/rsl_rl/train.py) scripts/reinforcement_learning/rsl_rl/train.py && echo "train.py OK"
diff <(git show upstream/main:scripts/reinforcement_learning/rsl_rl/play.py) scripts/reinforcement_learning/rsl_rl/play.py && echo "play.py OK"
```
Expected: both print "... OK" with no diff output.

- [ ] **Step 5: Commit**

```bash
cd /workspace/isaaclab
git add scripts/reinforcement_learning/rsl_rl/train.py scripts/reinforcement_learning/rsl_rl/play.py
git commit -m "revert: restore rsl_rl train.py/play.py to upstream (remove our _RUNNER_MAP)

The split left our _RUNNER_MAP contamination (pointing at the defunct
isaaclab_tasks.direct.constrained_full_albc namespace) in these scripts.
Runner dispatch for our custom runners moves to the constrained-albc overlay.

Constraint: isaaclab scripts/ stays pristine upstream
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Delete our files from isaaclab (play_student.py + 9 demos)

**Files:**
- Delete: `/workspace/isaaclab/scripts/reinforcement_learning/rsl_rl/play_student.py`
- Delete: `/workspace/isaaclab/scripts/demos/analyze_hero_mass.py`
- Delete: `/workspace/isaaclab/scripts/demos/check_hero_mass.py`
- Delete: `/workspace/isaaclab/scripts/demos/check_mass_only.py`
- Delete: `/workspace/isaaclab/scripts/demos/check_usd_physics.py`
- Delete: `/workspace/isaaclab/scripts/demos/check_usd_simple.py`
- Delete: `/workspace/isaaclab/scripts/demos/debug_usd_structure.py`
- Delete: `/workspace/isaaclab/scripts/demos/hero_agent_hydro_demo.py`
- Delete: `/workspace/isaaclab/scripts/demos/test_full_dof_env.py`
- Delete: `/workspace/isaaclab/scripts/demos/verify_physics_values.py`

- [ ] **Step 1: Confirm these 9 demos + play_student are OUR files (absent from upstream)**

Run:
```bash
cd /workspace/isaaclab
for f in scripts/reinforcement_learning/rsl_rl/play_student.py \
         scripts/demos/analyze_hero_mass.py scripts/demos/check_hero_mass.py \
         scripts/demos/check_mass_only.py scripts/demos/check_usd_physics.py \
         scripts/demos/check_usd_simple.py scripts/demos/debug_usd_structure.py \
         scripts/demos/hero_agent_hydro_demo.py scripts/demos/test_full_dof_env.py \
         scripts/demos/verify_physics_values.py; do
  git cat-file -e upstream/main:"$f" 2>/dev/null && echo "IN UPSTREAM (do NOT delete): $f" || echo "ours: $f"
done
```
Expected: every line prints `ours: <file>`. If any prints `IN UPSTREAM`, STOP and re-check — do not delete an upstream file.

- [ ] **Step 2: Delete the files**

Run:
```bash
cd /workspace/isaaclab
git rm scripts/reinforcement_learning/rsl_rl/play_student.py \
       scripts/demos/analyze_hero_mass.py scripts/demos/check_hero_mass.py \
       scripts/demos/check_mass_only.py scripts/demos/check_usd_physics.py \
       scripts/demos/check_usd_simple.py scripts/demos/debug_usd_structure.py \
       scripts/demos/hero_agent_hydro_demo.py scripts/demos/test_full_dof_env.py \
       scripts/demos/verify_physics_values.py
```

- [ ] **Step 3: Verify upstream demos are untouched**

Run:
```bash
cd /workspace/isaaclab
git status --short scripts/demos/ | grep -v '^D ' || echo "only deletions staged (good)"
ls scripts/demos/quadcopter.py scripts/demos/arms.py && echo "upstream demos intact"
```
Expected: "only deletions staged (good)" and "upstream demos intact". No upstream demo (quadcopter.py, arms.py, etc.) was removed.

- [ ] **Step 4: Commit**

```bash
cd /workspace/isaaclab
git commit -m "chore: remove our debug/demo + play_student scripts from isaaclab

These are hero/full_dof-specific debug scripts and a student play script that
never belonged in the upstream fork. Recoverable from git history if needed.
play_student/play entry is deferred to the overlay (YAGNI; eval_dr.py is the
canonical Full-DOF evaluation tool).

Constraint: isaaclab scripts/ stays pristine upstream
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Restore isaaclab direct/__init__.py to upstream

**Files:**
- Modify: `/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py`

- [ ] **Step 1: Show the contamination (our accidental deletion of `import gymnasium`)**

Run:
```bash
cd /workspace/isaaclab
diff <(git show upstream/main:source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py) source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py
```
Expected NOW: a diff showing `< import gymnasium as gym` (upstream has it, we deleted it).

- [ ] **Step 2: Restore to upstream**

Run:
```bash
cd /workspace/isaaclab
git checkout upstream/main -- source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py
```

- [ ] **Step 3: Verify it matches upstream**

Run:
```bash
cd /workspace/isaaclab
diff <(git show upstream/main:source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py) source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py && echo "direct/__init__.py OK"
```
Expected: "direct/__init__.py OK" with no diff.

- [ ] **Step 4: Commit**

```bash
cd /workspace/isaaclab
git add source/isaaclab_tasks/isaaclab_tasks/direct/__init__.py
git commit -m "revert: restore direct/__init__.py to upstream (re-add import gymnasium)

We had accidentally removed the upstream 'import gymnasium as gym' line. This
restores the pristine upstream file.

Constraint: isaaclab pristine (scripts/ + this accidental source/ edit)
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Rewrite the overlay train entry to own runner dispatch

**Files:**
- Modify (full rewrite): `/workspace/constrained-albc/scripts/train.py` (currently the thin runpy launcher, untracked)

This replaces the runpy-delegation launcher with a full train entry that replicates
upstream `train.py`'s structure. The ONLY divergence from upstream is the runner-dispatch
block (owns `_RUNNER_MAP` for our two custom runners). The header (argparse, AppLauncher,
rsl-rl version check) and `main()` body are copied verbatim from upstream/main so the
overlay tracks upstream behavior; the registration hook and runner map are the overlay's.

- [ ] **Step 1: Write the full overlay train entry**

Write `/workspace/constrained-albc/scripts/train.py` with exactly this content:

```python
#!/usr/bin/env python3
# Copyright (c) 2026.
"""Overlay train entry for constrained-albc environments.

isaaclab stays a pristine upstream fork: its train.py only knows OnPolicyRunner /
DistillationRunner and only imports isaaclab_tasks. This overlay entry owns two
overlay concerns that must NOT live in isaaclab:

  1. Registration: a one-shot ``builtins.__import__`` hook imports ``constrained_albc``
     when ``isaaclab_tasks`` is imported (which is AFTER AppLauncher boots SimulationApp,
     so the USD ``pxr`` runtime exists), triggering the overlay's gym.register() calls.
  2. Runner dispatch: a ``_RUNNER_MAP`` for the two custom runners
     (ConstraintEncoderRunner, OnPolicyDoraemonRunner) that upstream train.py does not know.

Everything else (argparse, AppLauncher, rsl-rl version check, main() body) is replicated
from upstream/main ``scripts/reinforcement_learning/rsl_rl/train.py`` so this entry tracks
upstream behavior. When rebasing isaaclab onto a newer upstream, diff that file against
this main() body to catch drift.

Usage (run via isaaclab's runtime):
    cd /workspace/isaaclab && ./isaaclab.sh -p \
        /workspace/constrained-albc/scripts/train.py \
        --task Isaac-FullDOF-TRPO-v0 --num_envs 4 --headless
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import builtins
import os
import sys

from isaaclab.app import AppLauncher

# Make upstream cli_args importable (it lives next to upstream train.py and uses
# `import cli_args  # isort: skip`, relying on sys.path).
ISAACLAB_PATH = os.environ.get("ISAACLAB_PATH", "/workspace/isaaclab")
UPSTREAM_RL_DIR = os.path.join(ISAACLAB_PATH, "scripts", "reinforcement_learning", "rsl_rl")
if UPSTREAM_RL_DIR not in sys.path:
    sys.path.insert(0, UPSTREAM_RL_DIR)

import cli_args  # isort: skip

# One-shot post-import hook: import constrained_albc the moment isaaclab_tasks is
# imported below (after AppLauncher has booted, so pxr exists), to register overlay envs.
_real_import = builtins.__import__
_overlay_loaded = False


def _import_with_overlay(name, *args, **kwargs):
    module = _real_import(name, *args, **kwargs)
    global _overlay_loaded
    if not _overlay_loaded and name == "isaaclab_tasks":
        _overlay_loaded = True
        import constrained_albc  # noqa: F401  triggers gym.register()
    return module


builtins.__import__ = _import_with_overlay

# add argparse arguments
parser = argparse.ArgumentParser(description="Train an RL agent with RSL-RL.")
parser.add_argument("--video", action="store_true", default=False, help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video (in steps).")
parser.add_argument("--video_interval", type=int, default=2000, help="Interval between video recordings (in steps).")
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument(
    "--agent", type=str, default="rsl_rl_cfg_entry_point", help="Name of the RL agent configuration entry point."
)
parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
parser.add_argument("--max_iterations", type=int, default=None, help="RL Policy training iterations.")
parser.add_argument(
    "--distributed", action="store_true", default=False, help="Run training with multiple GPUs or nodes."
)
parser.add_argument("--export_io_descriptors", action="store_true", default=False, help="Export IO descriptors.")
parser.add_argument(
    "--ray-proc-id", "-rid", type=int, default=None, help="Automatically configured by Ray integration, otherwise None."
)
# append RSL-RL cli arguments
cli_args.add_rsl_rl_args(parser)
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

# always enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Check for minimum supported RSL-RL version."""

import importlib.metadata as metadata
import platform

from packaging import version

# check minimum supported rsl-rl version
RSL_RL_VERSION = "3.0.1"
installed_version = metadata.version("rsl-rl-lib")
if version.parse(installed_version) < version.parse(RSL_RL_VERSION):
    if platform.system() == "Windows":
        cmd = [r".\isaaclab.bat", "-p", "-m", "pip", "install", f"rsl-rl-lib=={RSL_RL_VERSION}"]
    else:
        cmd = ["./isaaclab.sh", "-p", "-m", "pip", "install", f"rsl-rl-lib=={RSL_RL_VERSION}"]
    print(
        f"Please install the correct version of RSL-RL.\nExisting version is: '{installed_version}'"
        f" and required version is: '{RSL_RL_VERSION}'.\nTo install the correct version, run:"
        f"\n\n\t{' '.join(cmd)}\n"
    )
    exit(1)

"""Rest everything follows."""

import logging
import time
from datetime import datetime

import gymnasium as gym
import torch
from rsl_rl.runners import DistillationRunner, OnPolicyRunner

from isaaclab.envs import (
    DirectMARLEnv,
    DirectMARLEnvCfg,
    DirectRLEnvCfg,
    ManagerBasedRLEnvCfg,
    multi_agent_to_single_agent,
)
from isaaclab.utils.dict import print_dict
from isaaclab.utils.io import dump_yaml

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# Overlay-owned runner dispatch (the one divergence from upstream train.py).
from constrained_albc.envs.constrained_full_albc.runners import (
    ConstraintEncoderRunner,
    OnPolicyDoraemonRunner,
)

# import logger
logger = logging.getLogger(__name__)

_RUNNER_MAP = {
    "FullDOFConstraintEncoderRunner": ConstraintEncoderRunner,
    "OnPolicyDoraemonRunner": OnPolicyDoraemonRunner,
}

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.deterministic = False
torch.backends.cudnn.benchmark = False


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    """Train with RSL-RL agent."""
    # override configurations with non-hydra CLI arguments
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs
    agent_cfg.max_iterations = (
        args_cli.max_iterations if args_cli.max_iterations is not None else agent_cfg.max_iterations
    )

    # handle deprecated configurations
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, installed_version)

    # set the environment seed
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    if args_cli.distributed and args_cli.device is not None and "cpu" in args_cli.device:
        raise ValueError(
            "Distributed training is not supported when using CPU device. "
            "Please use GPU device (e.g., --device cuda) for distributed training."
        )

    # multi-gpu training configuration
    if args_cli.distributed:
        env_cfg.sim.device = f"cuda:{app_launcher.local_rank}"
        agent_cfg.device = f"cuda:{app_launcher.local_rank}"
        seed = agent_cfg.seed + app_launcher.local_rank
        env_cfg.seed = seed
        agent_cfg.seed = seed

    # specify directory for logging experiments
    log_root_path = os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    log_root_path = os.path.abspath(log_root_path)
    print(f"[INFO] Logging experiment in directory: {log_root_path}")
    log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Exact experiment name requested from command line: {log_dir}")
    if agent_cfg.run_name:
        log_dir += f"_{agent_cfg.run_name}"
    log_dir = os.path.join(log_root_path, log_dir)

    # set the IO descriptors export flag if requested
    if isinstance(env_cfg, ManagerBasedRLEnvCfg):
        env_cfg.export_io_descriptors = args_cli.export_io_descriptors
    else:
        logger.warning(
            "IO descriptors are only supported for manager based RL environments. No IO descriptors will be exported."
        )

    env_cfg.log_dir = log_dir

    # create isaac environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)

    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    if agent_cfg.resume or agent_cfg.algorithm.class_name == "Distillation":
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)

    # wrap for video recording
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "train"),
            "step_trigger": lambda step: step % args_cli.video_interval == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording videos during training.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    start_time = time.time()

    # wrap around environment for rsl-rl
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    # create runner from rsl-rl (overlay-owned dispatch for custom runners)
    runner_cls = _RUNNER_MAP.get(agent_cfg.class_name)
    if runner_cls is not None:
        print(f"[INFO] Using overlay runner {runner_cls.__name__} for training.")
        runner = runner_cls(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    elif agent_cfg.class_name == "OnPolicyRunner":
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    elif agent_cfg.class_name == "DistillationRunner":
        runner = DistillationRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    else:
        raise ValueError(f"Unsupported runner class: {agent_cfg.class_name}")

    # write git state to logs
    runner.add_git_repo_to_log(__file__)
    if agent_cfg.resume or agent_cfg.algorithm.class_name == "Distillation":
        print(f"[INFO]: Loading model checkpoint from: {resume_path}")
        runner.load(resume_path)

    # dump the configuration into log-directory
    dump_yaml(os.path.join(log_dir, "params", "env.yaml"), env_cfg)
    dump_yaml(os.path.join(log_dir, "params", "agent.yaml"), agent_cfg)

    # run training
    runner.learn(num_learning_iterations=agent_cfg.max_iterations, init_at_random_ep_len=True)

    print(f"Training time: {round(time.time() - start_time, 2)} seconds")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
```

- [ ] **Step 2: Static sanity check (no Isaac Sim boot — just syntax + import-shape)**

Run:
```bash
cd /workspace/constrained-albc && python3 -c "import ast; ast.parse(open('scripts/train.py').read()); print('syntax OK')"
```
Expected: "syntax OK".

- [ ] **Step 3: Verify the runpy-delegation pattern is fully gone**

Run:
```bash
cd /workspace/constrained-albc && grep -n "runpy\|run_path" scripts/train.py; echo "exit=$?"
```
Expected: no matches, `exit=1`. The thin launcher is fully replaced.

- [ ] **Step 4: Commit**

```bash
cd /workspace/constrained-albc
git add scripts/train.py
git commit -m "feat(scripts): overlay-owned train entry with runner dispatch

Replace the thin runpy launcher with a full train entry replicated from
upstream/main train.py main(). The only divergence is the overlay-owned
_RUNNER_MAP (ConstraintEncoderRunner, OnPolicyDoraemonRunner) plus the one-shot
import hook that registers constrained_albc envs after AppLauncher boots.
isaaclab train.py stays pristine.

Constraint: isaaclab scripts/ pristine; overlay owns its entry
Rejected: runpy delegation to upstream train.py | cannot dispatch 2 custom runners
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: End-to-end smoke verification (FullDOF training reaches iteration 0)

**Files:** none (verification only)

- [ ] **Step 1: Verify isaaclab scripts/ has zero of our contamination vs upstream**

Run:
```bash
cd /workspace/isaaclab
git grep -n "constrained_full_albc\|constrained_albc\|hero_agent\|_RUNNER_MAP" -- scripts/ ; echo "exit=$?"
```
Expected: no matches, `exit=1`. No trace of our code anywhere under isaaclab `scripts/`.

- [ ] **Step 2: Run the headless smoke train (background) and capture the log**

Run:
```bash
cd /workspace/isaaclab
rm -f /tmp/pristine_smoke.log
nohup ./isaaclab.sh -p /workspace/constrained-albc/scripts/train.py \
    --task Isaac-FullDOF-TRPO-v0 --num_envs 4 --max_iterations 2 --headless \
    > /tmp/pristine_smoke.log 2>&1 &
echo "launched pid $!"
```
Note: `--max_iterations 2` keeps the run short; headless is faster than livestream for a pass/fail check. GPU0 default (`feedback-gpu-allocation`).

- [ ] **Step 3: Wait for the success or failure signal**

Run:
```bash
until grep -qE "Learning iteration|Traceback|NameNotFound|ModuleNotFoundError|Unsupported runner|Error executing" /tmp/pristine_smoke.log; do sleep 8; done
echo "=== signal ==="
grep -nE "Using overlay runner|Learning iteration|Traceback|NameNotFound|ModuleNotFoundError|Unsupported runner|Error executing|Training time" /tmp/pristine_smoke.log | head -20
```
Expected: `[INFO] Using overlay runner ConstraintEncoderRunner for training.` followed by `Learning iteration 0/2` (or similar). NO `Traceback` / `ModuleNotFoundError` / `Unsupported runner`. If a traceback appears, the task is BLOCKED — read the full log and report.

- [ ] **Step 4: Confirm clean completion**

Run:
```bash
grep -E "Training time|Learning iteration 1" /tmp/pristine_smoke.log | tail -5
```
Expected: training advances past iteration 0 (e.g. "Learning iteration 1/2") and/or prints "Training time: ... seconds". This proves env registration + runner dispatch + a full train step all work end-to-end.

- [ ] **Step 5: Record the verification in changelog**

Append to `/workspace/isaaclab/changelog.md` (newest entry first, under today's date) a short entry documenting: the contamination found (isaaclab scripts/ carried `_RUNNER_MAP`), the resolution (restore scripts/ to upstream, overlay owns train entry), and the smoke-test evidence (FullDOF reached iteration N with overlay runner). Follow the changelog skill format (Context / Decisions / Open Questions — no file-level diffs). Then commit only `changelog.md`:

```bash
cd /workspace/isaaclab
git add changelog.md
git commit -m "docs: changelog for isaaclab pristine-restore session

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Notes for the executor

- **Two repos**: Tasks 1-3 + 5 commit in `/workspace/isaaclab`; Task 4 commits in `/workspace/constrained-albc`. Do not cross-stage.
- **Do NOT push** — pushing is user-controlled (`02-operations.md`). Stop after committing locally.
- **Do NOT touch** `source/isaaclab_rl` (`weight_decay`) or the forked `rsl_rl` package — intentional fork per the design doc.
- If Task 5 smoke fails with a NEW error (not the original `ModuleNotFoundError`), that is a real finding — read the log, do not paper over it, report to the user.
- The overlay train entry replicates upstream main(); if a future upstream rebase changes train.py main(), re-diff and update the overlay entry (drift control noted in the entry's docstring).
