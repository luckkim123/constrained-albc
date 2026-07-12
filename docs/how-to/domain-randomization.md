# How To: Configure Domain Randomization

> **Scope**: task-oriented steps for enabling/disabling DR, working with the DORAEMON
> curriculum, and adding a new DR parameter on the default task
> (`Isaac-ConstrainedALBC-TRPO-v0`, `constrained_albc/envs/main/`).
>
> **Numbers (ranges, dim counts, field names) are not repeated here** — the SSOT is
> [`reference/domain-randomization-and-doraemon.md`](../reference/domain-randomization-and-doraemon.md).
> This page only shows *how* to change things.

---

## Where the pieces live

| Piece | File |
|:---|:---|
| DR parameter ranges (`DomainRandomizationCfg`) | `constrained_albc/envs/main/config.py` |
| DORAEMON scheduler config (`DoraemonCfg`) | `constrained_albc/envs/main/config.py` (`ALBCEnvCfg.doraemon`) |
| ALBC's curriculum-parameter list (`_PARAM_DEFS`) | `constrained_albc/envs/main/doraemon.py` |
| DORAEMON engine (robot-agnostic) | `marinelab/marinelab/algorithms/doraemon.py` |
| Reset-time application of sampled values to physics | `constrained_albc/envs/main/mdp/events.py` |

There is no CLI flag for individual DR parameters — DR is configured in Python, either by
editing `config.py` directly (durable change) or by mutating the env cfg object in a script
before `gym.make()` (one-off change, see [Working examples](#working-examples)).

---

## 1. Toggle DR entirely on or off

`DomainRandomizationCfg.enable` is the single global switch. When `False`, every
`randomize_*` function in `mdp/events.py` early-returns (no-op) and the env falls back to
its nominal physics.

```python
# constrained_albc/envs/main/config.py, class ALBCEnvCfg
randomization: DomainRandomizationCfg = DomainRandomizationCfg()  # enable=True by default
```

To disable for a one-off run, mutate the field before environment construction (see
[Working examples](#working-examples)):

```python
env_cfg.randomization.enable = False
```

Note `doraemon.enable` (`ALBCEnvCfg.doraemon`) is a **separate** switch — see §3.

---

## 2. Enable/disable a single DR dimension

Every DR parameter is a `(lo, hi)` tuple field on `DomainRandomizationCfg`. There are two
places you can narrow or fix a dimension, and they do different things:

| Where | Effect |
|:---|:---|
| `DomainRandomizationCfg.<field>` in `config.py` | The **SSOT range**. Feeds both the uniform-sampling fallback (`mdp/events.py`) *and* the DORAEMON Beta bounds (via `build_param_specs`, which reads this field with `getattr`) *and* the eval-side hard-anchor fallback. |
| `ALBCEnvCfg.doraemon.param_overrides` (a `dict[str, tuple[float, float]]`) | Overrides **only** the DORAEMON curriculum's Beta bounds for that dimension, at scheduler-init time. Leaves the SSOT `config.py` range (and eval anchor) untouched — use this for a quick curriculum-only ablation. |

To fully disable one dimension (freeze it at its nominal value), collapse its range to a
single point:

```python
# durable: edit config.py
ocean_current_strength_range: tuple[float, float] = (0.0, 0.0)   # was (0.0, 1.0)
```

```python
# one-off: curriculum-only, script-level
env_cfg.doraemon.param_overrides = {"ocean_current_strength": (0.0, 0.0)}
```

`control_delay_steps` (§4) is a special case: its own default `(0, 0)` already means "off"
and skips allocating the delay buffer entirely — no separate toggle needed.

---

## 3. The DORAEMON curriculum

A parameter in `_PARAM_DEFS` (`envs/main/doraemon.py`) is curriculum-managed — drawn from a per-parameter Beta distribution that `DoraemonScheduler` (`marinelab/marinelab/algorithms/doraemon.py`) widens over training, gated by:

| Field | Role |
|:---|:---|
| `doraemon.performance_lb` / `alpha` | policy success-rate floor the curriculum must clear before widening |
| `doraemon.kl_ub` | per-step KL trust region bounding how fast a Beta can widen |
| `_PARAM_DEFS` membership | the only test for "curriculum-managed" — not listed means uniform sampling every reset instead (joint gains, thruster scales, `control_delay_steps`, …) |

To disable learning and freeze at whatever the curriculum last reached, set
`env_cfg.doraemon.enable = False` (falls back to uniform sampling of the `DomainRandomizationCfg`
ranges — see `envs/_core/student/runner.py`'s pattern). Full mechanics (Beta math, `step()` control flow,
eval-side interpolation, replay): [`reference/domain-randomization-and-doraemon.md`](../reference/domain-randomization-and-doraemon.md).

---

## 4. Enable action-latency DR (`control_delay_steps`)

`control_delay_steps: tuple[int, int]` (integer control steps; 1 step = 20ms @ 50Hz) adds a
random per-env transport delay to the applied action, drawn uniformly at reset. It is
**not** a `_PARAM_DEFS` entry — integer delay does not fit the continuous Beta sampler, so it
stays uniform-only by design.

```python
# config.py — enable a 0-3 step (0-60ms) random action delay
control_delay_steps: tuple[int, int] = (0, 3)   # default: (0, 0) = off
```

`(0, 0)` skips allocating the `DelayBuffer` entirely (`_draw_control_delay` in
`albc_env.py`), so leaving it at the default has zero overhead.

---

## 5. Enable the observation-noise DR knob (`obs_noise_scale`)

There are two independent noise layers on the 69D observation:

1. **Always-on sensor noise model** (`NoiseModelWithAdditiveBiasCfg`, `_OBS_NOISE_STD` /
   `_OBS_BIAS_MAG` in `config.py`) — applies regardless of DR.
2. **DR-managed extra layer** (`obs_noise_scale`, a `_PARAM_DEFS` entry) — a `[0, 1]`
   curriculum knob that scales the *same* per-channel `_OBS_NOISE_STD` pattern and adds it
   on top of layer 1. Nominal starts at `0.0` (byte-identical to no DR noise) and widens
   toward `1.0` (total std ≈ √2× layer 1 alone) as the curriculum progresses.

To force it to a fixed value instead of letting DORAEMON widen it (e.g. for an ablation that
always trains with extra noise):

```python
env_cfg.doraemon.param_overrides = {"obs_noise_scale": (1.0, 1.0)}
```

When `randomization.enable` is `False`, `_dr_obs_noise_scale` is never allocated (`None`) —
layer 2 has no effect regardless of the DORAEMON setting.

---

## 6. Add a new DR parameter

Follow the `_PARAM_DEFS` pattern to make a new physical parameter curriculum-managed
(uniform-only parameters only need step 1 + step 4).

1. **Add the range field** to `DomainRandomizationCfg` in `config.py`:

   ```python
   thruster_deadzone_scale: tuple[float, float] = (0.8, 1.2)
   ```

2. **Register it in `_PARAM_DEFS`** (`envs/main/doraemon.py`) — this is what makes it a
   curriculum dimension (increments `NDIMS`):

   ```python
   _PARAM_DEFS: list[tuple[str, str, float, float]] = [
       ...
       ("thruster_deadzone_scale", "thruster_deadzone_scale", 0.8, 1.2),
   ]
   ```

   The 3rd/4th elements are only the module-load fallback bounds (used when no DR cfg is
   supplied); the live range always comes from `config.py` via `getattr`.

3. **Optionally set a non-midpoint starting nominal** in `_NOMINAL_OVERRIDES` (same file) —
   e.g. `"thruster_deadzone_scale": 1.0` to start at "no deadzone" and widen from there, the
   same pattern `ocean_current_strength` and `obs_noise_scale` use.

4. **Wire the application** — a `_PARAM_DEFS` entry only makes the value *available* in the
   per-reset `sampled` dict; something must still read it. In `mdp/events.py`, use
   `_sample_or_uniform` so the physics code transparently falls back to a uniform draw when
   the parameter isn't (yet, or ever) DORAEMON-managed:

   ```python
   deadzone_scales = _sample_or_uniform(
       "thruster_deadzone_scale", sampled, n, cfg.thruster_deadzone_scale, device,
   )
   ```

   (If the consumer isn't in `mdp/events.py` — e.g. an observation-side effect like
   `obs_noise_scale` — apply the same `sampled.get(name, ...)` fallback pattern directly at
   the consuming call site in `albc_env.py`.)

Skipping step 4 is a common mistake: the parameter will show up in DORAEMON's
`mean/<param>` / `std/<param>` wandb metrics and consume curriculum budget, but never
actually perturb the simulation.

---

## Working examples

### Train with the shipped defaults (DR + DORAEMON both on)

No flags needed — `DomainRandomizationCfg.enable=True` and `DoraemonCfg.enable=True` are
the checked-in defaults on `ALBCEnvCfg`:

```bash
cd /workspace/constrained-albc && python scripts/train.py \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --num_envs 4096 --max_iterations 5000 \
    --logger wandb --log_project_name albc_trpo
```

### One-off override before training (durable change without editing `config.py`)

`scripts/train.py:main(env_cfg, agent_cfg)` receives the registered `ALBCEnvCfg` instance
before `gym.make()` — mutate it there, or in a thin wrapper script that imports `main`:

```python
from constrained_albc.envs.main.config import DomainRandomizationCfg

env_cfg.randomization.control_delay_steps = (0, 3)          # enable latency DR
env_cfg.doraemon.param_overrides = {                          # freeze one dim
    "ocean_current_strength": (0.0, 0.0),
}
```

### Post-construction override (matches `envs/_core/student/runner.py`'s pattern)

For scripts that already called `gym.make` (e.g. eval/play scripts), reach the cfg through
the unwrapped env:

```python
env_cfg = env.unwrapped.cfg
env_cfg.doraemon.enable = False                    # freeze curriculum, fall back to uniform
env_cfg.randomization = DomainRandomizationCfg()   # reset to the shipped hard ranges
```

---

## Related documents

- [`reference/domain-randomization-and-doraemon.md`](../reference/domain-randomization-and-doraemon.md) — DR parameter catalog, DORAEMON math, eval-side DR (SSOT for numbers).
- [`explanation/physics-tuning.md`](../explanation/physics-tuning.md) — PhysX/solver stability issues that interact with wide DR ranges (added-mass/inertia clamps, effort-limit impulse semantics).
