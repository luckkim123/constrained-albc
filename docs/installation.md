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

Verify the seven task IDs registered. `constrained_albc` must be imported first — its
`__init__.py` is what triggers `gym.register()` for every task; pip-installing the
package alone does not register anything:

```bash
cd /workspace/isaaclab && ./isaaclab.sh -p -c "
import constrained_albc  # noqa: F401  triggers gym.register() for all task IDs
import gymnasium as gym
tasks = [k for k in gym.envs.registry if 'ConstrainedALBC' in k]
print('\n'.join(sorted(tasks)))
"
```

Expected output:

```
Isaac-ConstrainedALBC-Full-NoEncoder-v0
Isaac-ConstrainedALBC-Full-PPO-Enc-v0
Isaac-ConstrainedALBC-Full-PPO-v0
Isaac-ConstrainedALBC-Full-TRPO-NoIPO-v0
Isaac-ConstrainedALBC-Full-TRPO-v0
Isaac-ConstrainedALBC-TDC-v0
Isaac-ConstrainedALBC-TRPO-v0
```

See [`reference/task-reference.md`](reference/task-reference.md) for what each task ID
is, its observation dims, and its typical launch command.

## RSL-RL dependency (stock)

constrained-albc runs on **stock `rsl-rl-lib==3.1.2`** — no fork is required.

```bash
/isaac-sim/python.sh -m pip install rsl-rl-lib==3.1.2 --no-deps
```

`isaaclab_rl` is the clean isaaclab fork-point version (no local cfg fields added).
The main TRPO pipeline ships its own `ConstraintTRPO` algorithm and `ActorCriticEncoder`
policy (custom, injected into the runner namespace), so it does not depend on any
rsl_rl modification. See [`architecture.md`](architecture.md) → "RSL-RL dependency".

## Reinstalling after a worktree swap

If you switch git worktrees or modify `pyproject.toml`, re-run the full Layer 3 install
command above. Partial installs (e.g. only reinstalling `constrained-albc` without
reinstalling `marinelab`) can produce `obs_dim` mismatches at runtime because the
editable namespace may partially revert to a previous version.
