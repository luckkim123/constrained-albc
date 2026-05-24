# Installation

`constrained-albc` sits at the top of a three-layer stack. The layers must be installed
in order because each depends on the one below it.

## Prerequisites

- The Docker image for this workspace already provides Isaac Sim 5.1.0 and the
  Isaac Lab editable install. Verify with:

  ```bash
  cd /workspace/isaaclab && ./isaaclab.sh -p -c "import isaaclab; print(isaaclab.__version__)"
  ```

- `marinelab` Git LFS meshes must be present before installation. Pull them if needed:

  ```bash
  cd /workspace/marinelab && git lfs pull
  ```

## Layer 1 — isaaclab (already done in Docker)

The base GPU simulation layer. Installed editable from inside the workspace as part of
Docker image build. No action required on a normal workspace start.

If you need to reinstall from scratch:

```bash
cd /workspace/isaaclab && ./isaaclab.sh --install
```

## Layer 2 — marinelab

Provides shared marine physics, the UUV (BlueROV2 / Hero Agent) assets, and the
`marinelab` Python package that `constrained-albc` imports.

```bash
cd /workspace/isaaclab && ./isaaclab.sh -p -m pip install -e /workspace/marinelab
```

> All `pip install` calls in this stack must go through `./isaaclab.sh -p -m pip` so
> that Isaac Lab's bundled Python (not the system Python) receives the package.

## Layer 3 — constrained-albc (this repo)

```bash
cd /workspace/isaaclab && ./isaaclab.sh -p -m pip install -e /workspace/constrained-albc
```

Verify the six task IDs registered:

```bash
cd /workspace/isaaclab && ./isaaclab.sh -p -c "
import gymnasium as gym
tasks = [k for k in gym.envs.registry if 'FullDOF' in k]
print('\n'.join(sorted(tasks)))
"
```

Expected output:

```
Isaac-FullDOF-NoEncoder-v0
Isaac-FullDOF-PPO-Enc-v0
Isaac-FullDOF-PPO-v0
Isaac-FullDOF-TDC-v0
Isaac-FullDOF-TRPO-NoIPO-v0
Isaac-FullDOF-TRPO-v0
```

## RSL-RL fork — critical dependency

> **A stock `rsl-rl-lib` from PyPI will fail at runtime.**

This repo requires **two** forks to be present; both ship with the workspace and are
installed as part of Isaac Lab's bundled environment:

1. **Forked `isaaclab_rl`** — adds `state_dependent_std` and `weight_decay` fields to
   the runner cfg classes. A stock `isaaclab_rl` raises `TypeError` when the agent cfgs
   in `constrained_albc/envs/*/agents/` are constructed.

2. **Forked `rsl_rl` package** — adds `state_dependent_std` ctor kwarg to
   `actor_critic.py` and encoder-aware learning-rate param groups to `ppo.py`. Without
   this fork the encoder LR is silently merged with actor/critic, breaking the
   asymmetric-encoder training.

See [`architecture.md`](architecture.md) (RSL-RL cfg dependency section) for the exact
file paths and line numbers in the forked packages.

## Reinstalling after a worktree swap

If you switch git worktrees or modify `pyproject.toml`, re-run the full Layer 3 install
command above. Partial installs (e.g. only reinstalling `constrained-albc` without
reinstalling `marinelab`) can produce `obs_dim` mismatches at runtime because the
editable namespace may partially revert to a previous version.
