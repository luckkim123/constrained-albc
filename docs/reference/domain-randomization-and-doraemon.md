# Domain Randomization & DORAEMON (`envs/main`)

> Verified against commit c5a8a08.

> **Scope**: The domain-randomization (DR) system of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — the
> 20-parameter DORAEMON entropy-maximization curriculum in
> `marinelab/marinelab/algorithms/doraemon.py`, the single `DomainRandomizationCfg`
> config (curriculum-managed vs uniform-only params live on the same class), how
> per-env sampled values reach the physics at reset, how the scheduler is stepped
> inside the training loop, and the fixed uniform-interpolation DR used on the
> eval side.
>
> This is a code-level reference verified against disk (adversarially
> cross-checked). It reflects the shipped default (`DomainRandomizationCfg`,
> `doraemon.enable = True`). The legacy full-DOF variant (`envs/full_dof/`) has
> its own, non-identical DORAEMON surface (18 params as of this writing — no
> buoy volume/mass decorrelation) and is out of scope here.

---

## 1. What Domain Randomization Is Here

**Update 2026-07-07**: `DomainRandomizationCfg` and `HardDomainRandomizationCfg`
were merged into a single class (commit `3e1f81f`). There is no more
base/soft-vs-hard config split — one class holds what used to be the Hard
(training) values directly. The class docstring still says "formerly
`HardDomainRandomizationCfg`" as a historical marker (`config.py:138`); the
class name it replaced no longer exists anywhere in the codebase.

Domain randomization in this project is **two disjoint surfaces that happen to
share one config object** (`DomainRandomizationCfg`), plus a third off-by-default
surface. Keeping them apart is the single most important thing to understand:

| Surface | What it is | Managed by | Default state |
|:---|:---|:---|:---|
| **DORAEMON physics DR** | 20 physics parameters (masses, damping, buoyancy geometry, ocean current, payload XY-offset, obs-noise scale) | learned Beta curriculum (DORAEMON) | **on** (`enable=True`) |
| **Uniform-only DR** | joint gains/friction/effort, thruster scales, control-action delay | fixed uniform sampling per reset | on (when `randomization` active) |
| **Fault injection** | thruster/sensor/joint component failure | `FaultInjectionCfg`, uniform | **off** |

**DORAEMON optimizes physics DR only.** Command/task difficulty is a fixed task
knob at scale `1.0` and is explicitly *not* curriculum-managed
(`albc_env.py:1503` — "DORAEMON optimizes physics DR only; command difficulty
is a fixed task knob"). The shipped default config instantiates
`DomainRandomizationCfg()` directly (`config.py:504`), so **"DR on" with what
used to be called the *hard* ranges is simply the shipped state** — there is no
separate softer class to fall back to. Fault injection (`FaultInjectionCfg`,
`config.py:316`) models component *failure*, a different thing from parameter
*spread*, and is off by default.

**DR is applied imperatively, not via Isaac Lab's `EventManager`.** Despite the
`events.py:6` docstring naming the "Isaac Lab EventTerm pattern", the
`randomize_*` functions are plain functions called directly from
`_reset_physics` — there is no `EventTerm` registration. Treat the docstring as
aspirational.

**File map** (where each piece lives):

```
marinelab/marinelab/algorithms/doraemon.py     # the ENGINE (robot-agnostic, 909 lines)
constrained_albc/envs/main/doraemon.py         # ALBC coupling: _PARAM_DEFS (20 params) + re-export shim
constrained_albc/envs/main/config.py           # DomainRandomizationCfg / FaultInjectionCfg + the live DoraemonCfg override
constrained_albc/envs/main/mdp/events.py       # reset-time APPLICATION of sampled values to physics
constrained_albc/envs/main/albc_env.py         # WIRING: samples, stashes, records episodes, owns _doraemon
constrained_albc/envs/main/runners/            # per-iteration _doraemon.step() call site
constrained_albc/analysis/{eval.py,dr_config.py,common.py}   # EVAL-side fixed DR (bypasses the curriculum)
```

---

## 2. The DR Parameter Catalog

This is the reference's centerpiece. The table is partitioned so the
**curriculum-managed vs uniform-only** boundary is unambiguous. Since the
2026-07-07 merge there is only one range per parameter (`config.py` is the range
SSOT). `_PARAM_DEFS` literal bounds (`envs/main/doraemon.py:41`) are
**fallback-only** — at build time `build_param_specs` reads live bounds from the
DR cfg via `getattr(dr_cfg, field_name)`.

> **NDIMS history**: 15 (pre-2026-07) -> 16 -> **17** (`payload_cog_offset_xy_u`
> promoted, 2026-07-07, `7f8e6c8`) -> **18** (`obs_noise_scale` registered,
> 2026-07-08, `034e866`) -> **20** (`buoy_volume_scale` +
> `buoy_body_mass_scale` added as part of the union p_t layout, 2026-07-12,
> `d7be189`). Curriculum starts at nominal `u = 0` / `0.0` for every promoted
> param below so default training behavior is unchanged until DORAEMON widens
> it.

### Block A — DORAEMON-curriculum-managed (20 params, Beta-dimension order)

| # | name | `config.py` field | range | nominal | meaning (what it multiplies / models) |
|:--|:---|:---|:---|:---|:---|
| 0 | payload_mass | `payload_mass_range` | (0.0, 3.0) | mid | Arm-carried payload mass in **kg (absolute)**. The dominant sim-to-real unknown for the manipulator. |
| 1 | added_mass_scale | `added_mass_scale` | (0.5, 1.5) | mid | Multiplier on the 6-DOF **added-mass** diagonal (inertia of water entrained during acceleration). Single scale broadcast to all 6 DOF. |
| 2 | linear_damping_scale | `linear_damping_scale` | (0.4, 1.7) | mid | Multiplier on **linear drag** (∝ velocity; dominates slow motion). |
| 3 | quadratic_damping_scale | `quadratic_damping_scale` | (0.4, 1.7) | mid | Multiplier on **quadratic drag** (∝ velocity²; dominates fast motion). |
| 4 | water_density | `water_density_range` | (995.0, 1025.0) | mid | Water density in **kg/m³ (absolute)**, fresh→sea. Scales buoyancy and drag together. |
| 5 | cog_offset_z | `cog_offset_z` | (-0.04, 0.04) | mid | Center-of-gravity vertical offset in **m (absolute)**. With cob, sets restoring-torque / metacentric height. |
| 6 | cob_offset_z | `cob_offset_z` | (-0.04, 0.04) | mid | Center-of-buoyancy vertical offset in **m (absolute)**. Governs metacentric height (attitude stability). |
| 7 | volume_scale | `volume_scale` | (0.75, 1.25) | mid | Multiplier on displaced **volume** → directly scales buoyancy magnitude. |
| 8 | cob_offset_x | `cob_offset_x` | (-0.02, 0.02) | mid | Center-of-buoyancy fore/aft offset in **m (absolute)** → biases roll/pitch restoring torque. |
| 9 | cob_offset_y | `cob_offset_y` | (-0.02, 0.02) | mid | Center-of-buoyancy lateral offset in **m (absolute)**. |
| 10 | cog_offset_x | `cog_offset_x` | (-0.02, 0.02) | mid | Center-of-gravity fore/aft offset in **m (absolute)**. |
| 11 | cog_offset_y | `cog_offset_y` | (-0.02, 0.02) | mid | Center-of-gravity lateral offset in **m (absolute)**. |
| 12 | inertia_scale | `inertia_scale` | (0.4, 2.0) | mid | Multiplier on rigid-body **moment of inertia** (rotational responsiveness). Constrained by added_mass/inertia < 1 + post-DR 0.95·I clamp. |
| 13 | body_mass_scale | `body_mass_scale` | (0.75, 1.25) | mid | Multiplier on the actual PhysX rigid-body mass (`set_masses`), broadcast to all bodies (main + buoy). Since PhysX applies gravity to this mass, it randomizes **weight** too, not just inertia — this is the vehicle's gravity/weight DR. (Payload weight is a separate channel: `payload_mass` as an external wrench on the gripper.) |
| 14 | buoy_volume_scale | `buoy_volume_scale` | (0.75, 1.25) | mid | Multiplier on the **buoy's** displaced volume, decorrelated from the main-body `volume_scale[7]` (separately-fabricated float, own manufacturing tolerance). Added 2026-07-12 (union p_t layout). |
| 15 | buoy_body_mass_scale | `buoy_body_mass_scale` | (0.75, 1.25) | mid | Multiplier on the **buoy** body mass, decorrelated from the main-body `body_mass_scale[13]`. Added 2026-07-12. |
| 16 | payload_cog_offset_z | `payload_cog_offset_z` | (-0.05, 0.0) | mid | Payload center-of-gravity vertical offset in **m (absolute)**. |
| 17 | payload_cog_offset_xy_u | `payload_cog_offset_xy_u_range` | (0.0, 1.0) | **0.0 (override)** | Normalized area-quantile u in [0,1] for the payload-CoG XY eccentricity. events maps it to physical radius via r = payload_cog_offset_xy_radius * sqrt(u) (sqrt = area-uniform correction). Curriculum starts at u=0 (no XY offset) and widens to u=1 (full r_max). The physical r_max (payload_cog_offset_xy_radius=0.08) is a fixed constant; only u is randomized. |
| 18 | ocean_current_strength | `ocean_current_strength_range` | (0.0, 1.0) | **0.0 (override)** | Scalar [0,1] multiplier on `ocean_current.max_velocity`. Curriculum starts at 0 (no current) and expands as the policy masters easier variants. |
| 19 | obs_noise_scale | `obs_noise_scale_range` | (0.0, 1.0) | **0.0 (override)** | Normalized [0,1] scale for an EXTRA white-noise layer added on top of the always-on 69D `_OBS_NOISE_STD` observation-noise model (std only, not bias). Curriculum starts at 0 (byte-identical to the base noise model) and widens toward 1.0 (+1x std, total std √2x) as the policy masters cleaner variants. Added 2026-07-08. |

`NDIMS = 20` (`envs/main/doraemon.py`). The `DomainRandomizationCfg` docstring
still carries a historical comment ("DORAEMON saturated all 15 parameters",
`config.py:145`) describing a run from when NDIMS was 15 — read it as a dated
note, not the current count.

### Block B — Uniform-only (in `DomainRandomizationCfg`, *not* in `_PARAM_DEFS`)

These are sampled uniformly every reset and are **never** touched by the
curriculum (no Beta, no widening). Nominal is n/a.

| name | range | meaning (what it multiplies / models) |
|:---|:---|:---|
| joint_stiffness_range (**arm actuator**, PhysX) | (30.0, 150.0) | Arm PD **P-gain** (Kp) **absolute**. Sim base 100; measured ζ≈0.7 confirms this regime. |
| joint_damping_range (**arm actuator**, PhysX) | (0.3, 7.0) | Arm PD **D-gain** (Kd) **absolute**. Sim base 3. |
| joint_effort_limit_range | (0.7, 1.0) | Multiplier on arm **torque limit** (1.0 = rated). |
| joint_static_friction_range | (0.0, 0.03) | Arm joint **static (Coulomb) friction**, absolute. |
| joint_viscous_friction_range | (0.0, 0.2) | Arm joint **viscous friction**, absolute. |
| thrust_coefficient_scale (**thruster**) | (0.7, 1.3) | Multiplier on **thrust coefficient** (force error). Covers T200 unit spread + fwd/rev magnitude asymmetry. |
| time_constant_scale (**thruster**) | (0.7, 1.3) | Multiplier on thruster **rise/fall time constant** (response lag). |
| yaw_damping_scale (**hydrodynamic** quad-damping, DOF-5) | (0.5, 1.5) | Extra scale on **yaw** (DOF-5) quadratic damping only, applied after the DOF-broadcast quad-damping (overwrites index 5). |
| control_delay_steps (**latency**, integer control steps) | (0, 0) | Discrete N-step lag on the applied action (1 step = 20 ms @ 50 Hz control rate); `(0, 0)` = off, byte-identical to no delay. Added 2026-07-09 (`5907fc6`, "add control_delay_steps DR config field (off by default)"). Sampled per-env at reset via `_draw_control_delay` (`albc_env.py:52,328`) and applied every step by `_apply_control_delay` (`albc_env.py:74,624`). The normalized delay value is itself a `p_t` privileged-obs dim — see `observation-space.md` §4 idx 24. `config.py`'s own comment marks this a deliberate simplification: static uniform DR like `time_constant_scale`, not on the DORAEMON curriculum, because an integer delay is awkward for the Beta-continuous sampler (`config.py:224-226`). |

> **Two "damping" name collisions.** `joint_damping_range` is the *arm
> actuator's* PhysX joint damping; `yaw_damping_scale` is the *hydrodynamic*
> quadratic-damping scale on rotational DOF-5. They are unrelated physical
> quantities that both contain "damping". These uniform-only actuator ranges live
> on the cfg family but are **never** touched by the DORAEMON curriculum; the
> source cfg (`config.py`) is the authority for their exact ranges.

### Block C — Scalars (not `(lo, hi)` tuples)

| name | value | meaning |
|:---|:---|:---|
| payload_cog_offset_xy_radius | 0.08 | physical r_max constant; the XY offset radius is DORAEMON-managed via payload_cog_offset_xy_u (Block A #17) as r = r_max * sqrt(u). This scalar only sets the ceiling. |

### Fault injection (`FaultInjectionCfg`, off by default)

A **separate surface** — component-failure modeling, not parameter spread. Off
unless explicitly enabled. Representative fields: thruster-fail probability,
thruster/joint health ranges, sensor-noise scale. Applied in the same reset as DR
but through a distinct mechanism (see §5).

---

## 3. The Beta Distribution: Per-Parameter Curriculum State

The curriculum state is **20 independent Beta distributions**, one per parameter,
each defined over that parameter's physical `[lo, hi]` interval (stored as
`_mins` / `_maxs` / `_ranges` inside `BetaDistribution`, `doraemon.py:115`). A
"harder" curriculum = wider Betas = more entropy.

### From `(nominal, concentration)` to `Beta(a, b)`

Each parameter's initial Beta is set from its nominal (anchor) and a shared
concentration `c` (`doraemon.py:130`):

$$
\mu = \mathrm{clip}\!\left(\frac{\text{nominal}-\text{lo}}{\text{hi}-\text{lo}},\,0.01,\,0.99\right),
\qquad a = \mu\,c, \qquad b = (1-\mu)\,c
$$

If either `a` or `b` falls below `_MIN_BETA_PARAM = 1.0`, the mean is preserved by
deriving the other parameter (a mean-preserving branch, `doraemon.py:130`).

> **Concentration gotcha (two disagreeing defaults).**
> `BetaDistribution.__init__` has `concentration = 200.0` (`doraemon.py:118`), but
> that default is **dead** in the ALBC path — the live scheduler constructs the
> distribution with `DoraemonCfg.init_concentration = 30.0` (`doraemon.py:351`).
> Read the scheduler's cfg, not the class default.

`sample(n)` draws in unit space and rescales to physical; `log_prob` inverts
(clamping to `[1e-6, 1-1e-6]`) and sums across dimensions; `kl_divergence`
operates on the **unit** Betas only (the `log(range)` term cancels).

### The entropy the curriculum maximizes

`BetaDistribution.entropy()` adds a change-of-variables term so entropy is
measured on the *physical* scale (`doraemon.py:173`):

$$
H(\phi) = \sum_{i=1}^{20}\Big(H_{\mathrm{Beta}}(a_i,b_i) + \log(\text{hi}_i-\text{lo}_i)\Big)
$$

This is the objective DORAEMON maximizes (§4).

### `build_param_specs`: fusing three bound sources

`build_param_specs` (`doraemon.py:65`) fuses the DR cfg ranges + `_PARAM_DEFS`
order + `_NOMINAL_OVERRIDES` into the `ParamSpec` list the distribution is built
from. Nominal = midpoint **except** three overrides in `_NOMINAL_OVERRIDES`
(`envs/main/doraemon.py:83-87`): `ocean_current_strength`, `payload_cog_offset_xy_u`,
and `obs_noise_scale` all start at `0.0`, so the curriculum **starts with no
ocean current / no payload XY offset / no extra observation noise** and widens
toward the full range as the policy learns simpler variants (`mu = 0` clamps to
`0.01` → `a = 1.0, b = 99.0` at `c = 30`). A third bound source,
`cfg.param_overrides` (`doraemon.py:332`), can override any parameter's bounds and
resets its nominal to the midpoint.

> **`PARAM_SPECS` module constant vs the live start.** The
> `PARAM_SPECS` list exported from `envs/main/doraemon.py` uses a **plain
> midpoint** nominal and does **not** apply `_NOMINAL_OVERRIDES` — it is kept
> byte-identical to a pre-promotion snapshot so a regression guard passes. **Do
> not** cite `PARAM_SPECS` as the live curriculum start; the live path goes
> through `build_param_specs` + `_NOMINAL_OVERRIDES`.

### `EpisodeBuffer`

A ring buffer (cap `2000`, `doraemon.py:228`) storing, per finished episode: the
sampled `xi`, the return, the binary `success`, and the `log_probs`.
`get_stats()` (`doraemon.py:208`) emits per-dimension **physical** mean/std — these
are the `DORAEMON/mean/<param>` and `DORAEMON/std/<param>` wandb signals.

---

## 4. The DORAEMON Curriculum Engine

DORAEMON — **Domain Randomization via Entropy Maximization** (Tiboni et al.,
ICLR 2024) — is implemented as `DoraemonScheduler` (`doraemon.py:300`). Every
`step_interval` RL iterations it solves **one constrained optimization**: widen
the DR distribution as much as possible (max entropy) without letting the
policy's estimated success rate drop below a floor and without moving too far in
one step.

$$
\max_{\phi=\{(a_i,b_i)\}}\ H(\phi)
\quad\text{s.t.}\quad
\hat G(\phi)\ge\alpha
\ \text{and}\
\mathrm{KL}\!\left(\phi\,\|\,\phi_{\text{prev}}\right)\le\varepsilon
$$

### Config: engine defaults vs the ALBC live override

| field | engine default (`doraemon.py:38`) | **ALBC live** (`config.py:527`) | role |
|:---|:---|:---|:---|
| `performance_lb` | 80.0 | **250.0** | return threshold for binary success |
| `alpha` | 0.5 | 0.5 | desired IS-estimated success rate ($\alpha$) |
| `kl_ub` | 0.5 (ref default 1.0) | **0.12** | per-step reverse-KL trust region ($\varepsilon$) |
| `init_concentration` | 30.0 | 30.0 | initial Beta `a+b` |
| `step_interval` | 250 | 250 | RL iters between updates |
| `buffer_size` | 2000 | 2000 | episode ring capacity |
| `min_episodes` | 200 | 200 | min buffered before first update |
| `min_ess_ratio` | 0.01 | 0.01 | ESS floor to accept an update |
| `hard_performance_constraint` | True | True | use inverted problem when infeasible |

> **Always read the caller's `DoraemonCfg`, not the engine defaults.** The
> shipped `kl_ub` is **0.12** and `performance_lb` is **250.0** (`config.py:527`).
> The engine's `kl_ub` docstring ("relaxed for kl_ub=2.0", `doraemon.py:46`) and
> its `80.0` default are both stale relative to the ALBC config. `performance_lb`
> was calibrated from a recon run (`trpo_baseline_260608_160453`): with `lb=68`
> the success flag was always 1 (below the observed minimum return ~82), so the
> `Ghat >= alpha` constraint was inert and the curriculum widened
> unconstrained; `lb=250` (the p25 return) restores a live signal.

### `step()` control flow (`doraemon.py:384`)

```
step(iteration):
  xi, returns, success, log_probs = buffer.get_all()
  if n < min_episodes:           -> metrics{skipped=1, entropy=...}   RETURN  (note key is 'entropy', not entropy_before/after)
  report success_rate, entropy_before, per-param stats  (ALWAYS)
  if step_count % step_interval != 0:  -> metrics{kl_step=0}          RETURN  (report-only between updates)

  prev_dist = dist.clone()
  Ghat = _estimate_success_rate(xi, success, ref=prev_dist)

  if hard_performance_constraint and Ghat < alpha:      # INFEASIBLE
     feasible, ok = _find_feasible_start(prev_dist, ...)  # inverted problem: max Ghat, budget kl_ub - 1e-5
     if ok:
        set_flat_params(feasible)
        if _estimate_success_rate() >= alpha:
           _optimize_entropy(prev_dist, ...) ; mode = 1.0   # inverted + optimize
        else:
           mode = -2.0                                       # kept max-success dist
     else:
        dist = prev_dist ; mode = -3.0                       # inverted failed -> revert
  else:                                                  # FEASIBLE (or soft)
     _optimize_entropy(prev_dist, ...) ; mode = 0.0          # normal

  entropy_after, kl_step = ...
  ess, ess_ratio = _compute_ess(...)
  if ess < min_ess_ratio * n:   dist = prev_dist ; reverted = 1.0    # ESS revert
  _trajectory.append({iter, a, b})                                    # for replay
```

The `mode` metric is a **multi-valued code**, not a boolean: `0.0` normal, `1.0`
inverted+optimize, `-2.0` kept max-success, `-3.0` inverted-failure revert.

### The four equations behind the engine

**KL constraint (reverse KL, per-dimension sum).** SLSQP receives it as
$g(\phi) = \varepsilon - \mathrm{KL} \ge 0$ (`doraemon.py:551`; helper
`_compute_kl` at `doraemon.py:91`):

$$
\mathrm{KL}(\phi\,\|\,\phi_{\text{prev}})
= \sum_{i=1}^{20}\mathrm{KL}\!\Big(\mathrm{Beta}(a_i,b_i)\,\big\|\,\mathrm{Beta}(a_i^{\text{prev}},b_i^{\text{prev}})\Big)\le\varepsilon
$$

**IS success-rate estimate (unnormalized).** Success is binary
$\sigma_k = \mathbb{1}[J_k \ge \texttt{performance\_lb}]$ and the log-ratio is
clamped to $\pm 5$ (`_IS_LOG_CLAMP = 5.0`, `doraemon.py:88`):

$$
\hat G(\phi)=\frac{1}{K}\sum_{k=1}^{K}\exp\!\Big(\mathrm{clip}\big(\log p_\phi(\xi_k)-\log p_{\phi_{\text{prev}}}(\xi_k),\,-5,\,+5\big)\Big)\,\sigma_k
$$

> **The denominator is `prev_dist` evaluated *live*, not the buffered
> `log_probs`.** `_estimate_success_rate` (`doraemon.py:486`) recomputes
> `prev_dist.log_prob(xi)` at call time. The class docstring line
> (`doraemon.py:307`, "Unnormalized IS with stored per-episode log probs") is
> **stale** — the stored `log_probs` (and `returns`) are effectively dead for the
> optimization.

**ESS revert gate.** After optimizing, the update is discarded if the
importance-sampling estimator is too degenerate (`doraemon.py:458`):

$$
\mathrm{ESS}=\frac{1}{\sum_k w_k^2},\quad w_k\propto\exp\!\big(\log p_\phi(\xi_k)-\log p_{\phi_{\text{prev}}}(\xi_k)\big),\ \textstyle\sum_k w_k=1;
\quad \text{revert if } \mathrm{ESS}<\texttt{min\_ess\_ratio}\cdot n
$$

The optimization itself is SLSQP in **log-space** (`_optimize_entropy`,
`doraemon.py:577`): variables are `log(a), log(b)`, Beta params clamped to
`[1.0, 500.0]`. A non-converged SLSQP result is accepted **only if**
`perf_ok AND result.fun < init_obj AND kl <= kl_ub` (`doraemon.py:653`) — this
guard exists so a stalled solver cannot commit a sub-floor distribution.
`_find_feasible_start` (`doraemon.py:679`) returns `False` immediately if there
are zero successful episodes.

---

## 5. From Sampled Values to Physics (Reset-Time Application)

Application is **imperative**, not `EventManager`-driven. The `randomize_*`
functions are called from `_reset_physics` (defined `albc_env.py:1467`) and
`_reset_task_and_state` (`albc_env.py:1546`).

**Per reset the controller samples once** into a `sampled` dict keyed by
`spec.name` (`albc_env.py:1493`), builds a `DRSampler(cfg, N, device)` (`:1488`), and
threads both into every randomizer.

### The curriculum-vs-uniform bridge: `_sample_or_uniform`

`_sample_or_uniform` (`events.py:46`) is the exact switch that makes a parameter
curriculum-managed or uniform-only:

```
_sample_or_uniform(field_name, sampled, shape, cfg_range, device, broadcast_dim):
    if field_name in sampled:      -> per-env DORAEMON tensor (scalar broadcast to broadcast_dim DOFs)
    else:                          -> uniform sample from cfg_range
```

A key present in `sampled` ⇒ DORAEMON-managed; absent ⇒ uniform. That is the
**only** thing that distinguishes the two.

### Base caching: `_HydroBaseCache`

`_HydroBaseCache` (`events.py:144`) caches 8 hydrodynamic base fields lazily on
the first reset (frozen baseline so scaling never compounds across resets). When
`rigid_body_inertia` is unset, inertia falls back to `0.5 * added_mass[3:6]` with a
warning.

### Scale vs absolute vs offset (differs per field)

| semantics | fields |
|:---|:---|
| **scale on cached base** | added_mass, linear/quadratic damping, volume, inertia, body_mass |
| **absolute value** | water_density, payload_mass |
| **base + offset** | center-of-buoyancy (CoB), center-of-gravity (CoG) |

Notable ordering quirks: rotational **DOF-5 (yaw) is double-processed** — the
quadratic-damping scale is applied, then overwritten by `yaw_damping_scale`; both
`env._hydro` and `env._buoy_hydro` share one sampled scale; buoyancy is recomputed
after CoB/CoG offsets. When `enable = False` the randomizers early-return
(no-op).

### Payload

Payload mass is absolute; the CoG XY offset is sampled on a disk of radius
`payload_cog_offset_xy_radius` via `r = r_max * sqrt(u)` (area-uniform
correction). `u` is now the DORAEMON-managed `payload_cog_offset_xy_u` dim
(Block A #15), not a uniform `torch.rand` draw — only `r_max` is a fixed
scalar (Block C). `_apply_xyz_offset_with_doraemon` (`events.py:63`) and
`_clamp_payload_cog_stability` (`events.py:88`) enforce static stability.

> **Payload toggle is off by default.** `_setup_payload_toggle` returns early
> when `payload_toggle_steps == 0`, and the default is `0` (no mid-episode
> payload toggle). Do not assume the payload toggles mid-episode unless the cfg
> sets a nonzero toggle.

### Ocean current strength

Three-way resolution (`events.py:294`, `ocean_current.py`): use the
DORAEMON-sampled `ocean_current_strength` if present, else a uniform sample from
`ocean_current_strength_range`, else fall back. The strength `[0, 1]` multiplies
`ocean_current.max_velocity` **after** the noise term, and the whole path is
gated on the env actually having an ocean-current component (`_has_ocean_current`).

### Two stability clamps

**Added-mass vs generalized inertia** (`events.py:214`) — keeps
$M_a / I < 1$ for numerical stability, gated on `apply_added_mass_force` AND
`body_mass` being present:

$$
M_a[i]\ \le\ 0.95\,\cdot\,\mathrm{gen\_inertia}[i],
\qquad \mathrm{gen\_inertia}=[\,m_{\text{body}},m_{\text{body}},m_{\text{body}},\ I_{xx},I_{yy},I_{zz}\,]
$$

**Payload-CoG static stability** (`events.py:88`) — caps the CoG offset so the
buoyancy restoring moment dominates gravity's tipping moment (scale capped at
`1.0`; uses buoy force $F_{bu}$ and moment arm $h$):

$$
m\,g\,\lVert r^{\text{eff}}_{xy}\rVert_2\ \le\ F_{bu}\,h,
\qquad r_{\max}=\frac{F_{bu}\,h}{m\,g}\ (\infty\ \text{if}\ m\le 10^{-6}),
\qquad s=\min\!\Big(\frac{r_{\max}}{\max(\lVert r^{\text{eff}}_{xy}\rVert,\,10^{-8})},\,1\Big)
$$

---

## 6. Training-Loop Wiring

The env owns `_doraemon`, created in `_init_doraemon` (`albc_env.py:445`),
branching on `replay_curriculum_path`: empty ⇒ `DoraemonScheduler` (live
learning), set ⇒ `CurriculumReplayer` (frozen, §7). When active, per-env buffers
`_episode_dr_xi` / `_episode_dr_log_probs` / `_episode_return_accum` are
allocated.

**End-to-end loop:**

```
per RESET   : xi, log_probs = _doraemon.sample(N)      -> stash per-env -> events apply xi to physics
per STEP    : _episode_return_accum += reward           (gated on _doraemon active)
on next RESET (per finished env):
              success = (_episode_return_accum >= performance_lb)   # <-- binarization is HERE, in the CALLER
              _doraemon.record_episodes(xi, returns, success, log_probs)   (albc_env.py:1399)
per ITER    : runner.log() -> metrics = _doraemon.step(iteration=it)  -> re-emit under DORAEMON/ prefix
```

> **The success binarization lives in the caller, not the engine.**
> `success = return >= performance_lb` is computed in `albc_env.py:1398` and the
> engine's `record_episodes` receives a **pre-computed `success` tensor**. This is
> why the engine class docstring (`doraemon.py:307`) is misleading — the engine
> never binarizes and never reads the stored `log_probs` for its math.

**Runner split.** The default TRPO path uses `ConstraintEncoderRunner`
(`runners/constraint_encoder_runner.py:256`, passes `iteration=`); PPO ablations
use `OnPolicyDoraemonRunner` (`runners/on_policy_doraemon_runner.py:83`, no
`iteration` kwarg → `_trajectory` iter falls back to `_step_count`). Behavior is
otherwise identical.

**Checkpointing.** `state_dict` (`doraemon.py:773`) serializes `dist_a` / `dist_b`
+ step/episode counts + the full episode buffer. `export_recording`
(`doraemon.py:765`, `DoraemonScheduler` **only**) writes the curriculum trajectory
for replay; it is guarded by `hasattr`, so a replay run writes nothing.

**Emitted metrics** (under the `DORAEMON/` prefix): `success_rate`,
`entropy_before` / `entropy_after` (or plain `entropy` in the skip branch),
`kl_step`, `ess` / `ess_ratio`, `mode` (multi-valued, see §4), `reverted`,
`skipped`, and per-parameter `mean/<name>` / `std/<name>`.

---

## 7. Curriculum Replay

`CurriculumReplayer` (`doraemon.py:817`) is the **frozen-curriculum path**, active
when `replay_curriculum_path` is set (`albc_env.py:460`). It duck-types
`DoraemonScheduler` (`sample` / `step` / `record_episodes` / `state_dict`) but does
**no learning**:

- `sample()` still draws from a Beta.
- `step()` is a **hold-last step function** keyed on the `iteration` arg
  (`doraemon.py:884`): the distribution at iter `t` is the last recorded `(a, b)`
  with `iter <= t`. If `iteration` is `None` it defaults to `0` — so a runner that
  does not thread `iteration` freezes the replay at the first recorded entry.
- `record_episodes` is a **no-op**; `load_state_dict` is a **no-op**;
  `state_dict` returns only `dist_a` / `dist_b` (the schedule drives the
  distribution, so there is nothing to checkpoint-restore).

**Recording format** (`export_recording`): `{param_names, param_bounds,
trajectory}`. `_validate` (`doraemon.py:847`) hard-checks param **name order** and
**bounds** (tolerance `1e-9`) against the recording and raises on mismatch or an
empty trajectory. The replayer's own `DoraemonCfg()` and throwaway
`concentration = 2.0` (immediately overwritten by `_apply(0)`) exist only so the
env's success computation does not crash — the computed success is then discarded.

---

## 8. Eval-Side DR

**Eval DR is a fixed *uniform interpolation* that bypasses the DORAEMON Beta
curriculum entirely.** There is no `step()` / `record_episodes` during eval; the
only DORAEMON contact is *reading* the run's final `mean` / `std` from
TensorBoard. The entry point is `analysis/eval.py` — **not** the `eval_dr.py`
that the rules/CLAUDE.md still name (that file does not exist under that name).

### The four levels

`none / soft / medium / hard` use fixed scale fractions `0.0 / 0.3 / 0.6 / 1.0`
(the `DR_SCALE` map at `common.py:36`, which also carries a 5th `ood: 1.0`),
linearly interpolating between a true-nominal single point (scale `0`) and a
**hard anchor** (scale `1`). Per-level application is `apply_dr_config` in
`eval.py:345`; the hard anchor itself is built by `get_hard_dr_config`
(`dr_config.py:275`) from the DORAEMON-learned `mean ± 2·std` clamped to
PARAM_SPEC bounds (`dr_config.py:237`).

> **`soft`/`hard` are interpolation *endpoints*, not two different config
> classes** — there is only one `DomainRandomizationCfg` now (§1). The hard
> anchor defaults to the run's **DORAEMON-learned** distribution (per-param
> `mean ± 2·std` from TB, clamped to PARAM_SPEC bounds; `load_doraemon_dr`,
> `dr_config.py:206`), with a plain `DomainRandomizationCfg()` instance used
> directly as the fallback when no DORAEMON tags exist (`dr_config.py:286`).
> `get_hard_dr_config` (`dr_config.py:275`) returns a **deepcopy** so an
> OOD-level `setattr` cannot clobber the global anchor.

### The three modes (there are exactly three)

| mode | what it does | mechanism |
|:---|:---|:---|
| **static** | DR fixed for the whole episode; the *command* switches per segment | `apply_dr_config` per level (`eval.py:1183`) |
| **periodic** | mid-episode DR **shock** | module-level `apply_dr_mid_episode` builds a fresh `DRSampler` |
| **segmented** | **also** changes DR mid-episode | env method `raw_env.randomize_physics_mid_episode` with `torch.manual_seed(master_seed + seg_idx)` for a reproducible switch sequence |

> **A task-named `sudden` mode does not exist** — the rules mention it, but the
> code has only static/periodic/segmented. Note that **both** periodic and
> segmented change DR mid-episode, via two *different* code paths (periodic builds
> a fresh sampler; segmented reseeds per segment for reproducibility).

### `dr_snapshot`

`_eval_dr/dr_snapshot.py` (`:45`) is a **pure post-hoc reshaper** of
already-fixed, post-clamp physics tensors into `dr_<name>[N]` arrays for logging —
it is **not** a DR freeze/realize step. Reproducible fixed physics comes instead
from `--deterministic-dr`, which collapses each `(lo, hi)` tuple to its midpoint.
There is also a 5th OOD level (full DORAEMON-derived) that bypasses
`apply_dr_config` entirely.

---

## 9. Gotchas and Name-vs-Implementation Traps

The cross-cutting pitfalls a reader auditing the source will hit. Each states the
trap and the correcting fact with its anchor.

1. **`performance_lb` is a return threshold, not a success rate.** It binarizes
   success ($\sigma = \mathbb{1}[J \ge \texttt{performance\_lb}]$); the success-*rate*
   target is `alpha` (0.5). Confusing them inverts the constraint. (`doraemon.py:39`)

2. **The engine does not binarize; the caller does.** `success = return >=
   performance_lb` is computed in `albc_env.py:1398`; `record_episodes` receives a
   ready-made `success` tensor. The class docstring at `doraemon.py:307`
   ("stored per-episode log probs") is **stale** — the IS estimator recomputes
   `log_prob` live under `prev_dist` and never uses the buffered `log_probs`.

3. **Read the caller's `DoraemonCfg`, not the engine defaults.** Live `kl_ub` is
   **0.12** and `performance_lb` is **250.0** (`config.py:527`), not the engine's
   `0.5` / `80.0`. The "relaxed for kl_ub=2.0" comment (`doraemon.py:46`) is also
   stale.

4. **Eval `soft`/`hard` are interpolation endpoints, not two cfg classes** — there
   is only one `DomainRandomizationCfg` since the 2026-07-07 merge. The hard
   anchor is the run's DORAEMON-learned distribution when available, else a
   plain `DomainRandomizationCfg()` instance. (`dr_config.py:206`, `:275`)

5. **Only three eval modes exist** (static/periodic/segmented); `sudden` does
   not, and `eval_dr.py` is not the real entry point (`eval.py` is). Both periodic
   *and* segmented change DR mid-episode, via different code paths.

6. **`_PARAM_DEFS` literal bounds are fallback-only.** `build_param_specs` reads
   live bounds from `config.py` via `getattr` — `config.py` is the range SSOT.
   `NDIMS = 20` despite the historical "15 parameters" comment at `config.py:145`
   (dated to a run from before three later promotions raised it to 20).

7. **An update can be silently no-op'd three distinct ways** (SLSQP reject /
   `mode = -3` inverted-failure revert / ESS revert) that all leave the
   distribution unchanged; only the `mode` and `reverted` metrics distinguish
   them. `entropy_after == entropy_before` does **not** mean no update was
   attempted.

8. **Two concentration defaults disagree.** `BetaDistribution.__init__ = 200.0` is
   dead in the ALBC path; the live scheduler uses
   `DoraemonCfg.init_concentration = 30.0`.

9. **DR is applied imperatively from `_reset_physics`, not via
   `EventTerm`/`EventManager`** despite the `events.py:6` docstring; and field
   semantics differ (SCALE on cached base vs ABSOLUTE vs base+OFFSET). Rotational
   DOF-5 (yaw) is double-processed, and the added-mass clamp is silently skipped
   when `apply_added_mass_force` is off.

---

## Appendix: Quick file/line index

| Concern | Anchor |
|:---|:---|
| Engine config defaults | `marinelab/algorithms/doraemon.py:38` |
| `step()` control flow | `doraemon.py:384` |
| Infeasible dispatch / inverted problem | `doraemon.py:430`, `:679` |
| IS success estimate | `doraemon.py:486` |
| `_optimize_entropy` (SLSQP) | `doraemon.py:577` |
| ESS revert | `doraemon.py:458` |
| `BetaDistribution` | `doraemon.py:115` |
| `build_param_specs` | `doraemon.py:65` |
| `CurriculumReplayer` | `doraemon.py:817` |
| 20 param defs / overrides | `constrained_albc/envs/main/doraemon.py:41`, `:83` |
| DR ranges (single class since 2026-07-07 merge) | `constrained_albc/envs/main/config.py:137-241` |
| **Live `DoraemonCfg` override** | `config.py:527` |
| Reset-time application | `envs/main/mdp/events.py:46`, `:88`, `:144`, `:214` |
| Sample + record wiring | `albc_env.py:445`, `:1398`, `:1493` |
| Runner step call site | `runners/constraint_encoder_runner.py:256` |
| Eval levels / anchor | `analysis/dr_config.py:206`, `:275`; `common.py:36`; `eval.py:345` |
| Eval modes | `analysis/eval.py:890` (static), `:1183` (level loop), `:1517` (periodic) |
