# Domain Randomization & DORAEMON (`envs/main`)

> **Scope**: The domain-randomization (DR) system of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`):
> - the 23-parameter DORAEMON entropy-maximization curriculum (engine in
>   `marinelab/marinelab/algorithms/doraemon.py`, ALBC parameter table in
>   `constrained_albc/envs/main/doraemon.py`)
> - the single `DomainRandomizationCfg` config (curriculum-managed and uniform-only parameters
>   live on the same class)
> - how per-env sampled values reach the physics at reset
> - how the scheduler is stepped inside the training loop
> - the fixed uniform-interpolation DR used on the eval side
>
> This is a code-level reference. It reflects the shipped default (`DomainRandomizationCfg`,
> `doraemon.enable = True`).

---

## 1. What Domain Randomization Is Here

There is one DR config class, `DomainRandomizationCfg`; its defaults are the training ranges.
Domain randomization in this project is two disjoint surfaces that share that config object,
plus a third off-by-default surface:

| Surface | What it is | Managed by | Default state |
|:---|:---|:---|:---|
| **DORAEMON physics DR** | 23 parameters (masses, damping, buoyancy geometry, ocean current, payload offsets, obs-noise scale, fault severity, heave-disturbance strength, control-delay strength) | learned Beta curriculum (DORAEMON) | **on** (`enable=True`) |
| **Uniform-only DR** | joint gains/friction/effort, thruster scales, yaw damping, control-action and observation delay | fixed uniform sampling per reset | on (when `randomization.enable`) |
| **Fault injection** | thruster/sensor/joint component failure | `FaultInjectionCfg`, uniform | **off** |

Key facts:
- DORAEMON optimizes physics DR only. Command difficulty is a fixed task knob, not
  curriculum-managed.
- The shipped default instantiates `DomainRandomizationCfg()` directly in `ALBCEnvCfg`, so
  "DR on" with these ranges is simply the shipped state.
- Fault injection (`FaultInjectionCfg`) models component failure, a different thing from
  parameter spread, and is off by default.

**DR is applied imperatively, not via Isaac Lab's `EventManager`.** Despite the `events.py`
module docstring naming the "Isaac Lab EventTerm pattern", the `randomize_*` functions are plain
functions called directly from `_reset_physics`; there is no `EventTerm` registration.

**File map**:

| Path | Role |
|:---|:---|
| `marinelab/marinelab/algorithms/doraemon.py` | the ENGINE (robot-agnostic) |
| `constrained_albc/envs/main/doraemon.py` | ALBC coupling: `_PARAM_DEFS` (23 params), `_NOMINAL_OVERRIDES`, re-export shim |
| `constrained_albc/envs/main/config.py` | `DomainRandomizationCfg` / `FaultInjectionCfg` and the live `DoraemonCfg` |
| `constrained_albc/envs/main/config_simtoreal.py` | plant overrides for the `-SimToReal-v0` tasks |
| `constrained_albc/envs/main/mdp/events.py` | reset-time APPLICATION of sampled values to physics |
| `constrained_albc/envs/main/albc_env.py` | WIRING: samples, stashes, records episodes, owns `_doraemon` |
| `constrained_albc/algorithms/runners/` | per-iteration `_doraemon.step()` call site |
| `constrained_albc/analysis/{eval.py,dr_config.py,common.py}` | EVAL-side fixed DR (bypasses the curriculum) |

---

## 2. The DR Parameter Catalog

The table is partitioned so the curriculum-managed vs uniform-only boundary is unambiguous.
The range SSOT is `config.py`: the literal bounds in `_PARAM_DEFS` are fallback-only, because at
build time `build_param_specs` reads the live bounds from the DR cfg via
`getattr(dr_cfg, field_name)`.

### Block A: DORAEMON-curriculum-managed (23 params, Beta-dimension order)

`_PARAM_DEFS` in `envs/main/doraemon.py` holds 23 entries (`NDIMS = len(_PARAM_DEFS) = 23`).
"Cfg default" is the live range on `DomainRandomizationCfg`; "`_PARAM_DEFS` fallback" is the
literal bound in the table; "Nominal" is the Beta anchor (midpoint of the live range unless
`_NOMINAL_OVERRIDES` sets it).

| # | name | `config.py` field | Cfg default | `_PARAM_DEFS` fallback | Nominal | Meaning |
|:--|:---|:---|:---|:---|:---|:---|
| 0 | payload_mass | `payload_mass_range` | (0.0, 3.0) | (0.0, 1.0) | mid | Arm-carried payload mass, kg (absolute) |
| 1 | added_mass_scale | `added_mass_scale` | (0.5, 1.5) | (0.85, 1.15) | mid | Multiplier on the 6-DOF added-mass diagonal (one scale broadcast to all 6 DOF) |
| 2 | linear_damping_scale | `linear_damping_scale` | (0.4, 1.7) | (0.5, 1.5) | mid | Multiplier on linear drag |
| 3 | quadratic_damping_scale | `quadratic_damping_scale` | (0.4, 1.7) | (0.5, 1.5) | mid | Multiplier on quadratic drag |
| 4 | water_density | `water_density_range` | (995.0, 1025.0) | (995.0, 1025.0) | mid | Water density, kg/m^3 (absolute); scales buoyancy |
| 5 | cog_offset_z | `cog_offset_z` | (-0.04, 0.04) | (-0.02, 0.02) | mid | Center-of-gravity vertical offset, m |
| 6 | cob_offset_z | `cob_offset_z` | (-0.04, 0.04) | (-0.02, 0.02) | mid | Center-of-buoyancy vertical offset, m |
| 7 | volume_scale | `volume_scale` | (0.75, 1.25) | (0.9, 1.1) | mid | Multiplier on displaced volume (buoyancy magnitude) |
| 8 | cob_offset_x | `cob_offset_x` | (-0.02, 0.02) | (-0.01, 0.01) | mid | Center-of-buoyancy fore/aft offset, m |
| 9 | cob_offset_y | `cob_offset_y` | (-0.02, 0.02) | (-0.01, 0.01) | mid | Center-of-buoyancy lateral offset, m |
| 10 | cog_offset_x | `cog_offset_x` | (-0.02, 0.02) | (-0.01, 0.01) | mid | Center-of-gravity fore/aft offset, m |
| 11 | cog_offset_y | `cog_offset_y` | (-0.02, 0.02) | (-0.01, 0.01) | mid | Center-of-gravity lateral offset, m |
| 12 | inertia_scale | `inertia_scale` | (0.4, 4.8) | (0.75, 1.3) | **4.0 (override)** | Multiplier on rigid-body moment of inertia; also pushed into PhysX via `randomize_physx_inertia` |
| 13 | body_mass_scale | `body_mass_scale` | (0.75, 1.25) | (0.9, 1.1) | mid | Multiplier on the PhysX rigid-body mass (`set_masses`), so it randomizes weight as well as inertia |
| 14 | buoy_volume_scale | `buoy_volume_scale` | (0.75, 1.25) | (0.9, 1.1) | mid | Multiplier on the buoy's displaced volume, decorrelated from #7 |
| 15 | buoy_body_mass_scale | `buoy_body_mass_scale` | (0.75, 1.25) | (0.9, 1.1) | mid | Multiplier on the buoy body mass, decorrelated from #13 |
| 16 | payload_cog_offset_z | `payload_cog_offset_z` | (-0.05, 0.0) | (-0.03, 0.0) | mid | Payload center-of-gravity vertical offset, m |
| 17 | payload_cog_offset_xy_u | `payload_cog_offset_xy_u_range` | (0.0, 1.0) | (0.0, 1.0) | **0.0 (override)** | Normalized area-quantile `u` for the payload-CoG XY eccentricity; `events` applies `r = payload_cog_offset_xy_radius * sqrt(u)` |
| 18 | ocean_current_strength | `ocean_current_strength_range` | (0.0, 1.0) | (0.0, 1.0) | **0.0 (override)** | Scalar multiplier on `ocean_current.max_velocity` |
| 19 | obs_noise_scale | `obs_noise_scale_range` | (0.0, 1.0) | (0.0, 1.0) | **0.0 (override)** | Scale of an EXTRA white-noise layer on top of the always-on observation-noise model (std only, not bias) |
| 20 | fault_severity | `fault_severity_range` | (0.0, 1.0) | (0.0, 1.0) | **0.0 (override)** | Scales `fault.thruster_fail_prob` before the Bernoulli compare in `faults.sample_thruster_health` |
| 21 | fz_disturbance_strength | `fz_disturbance_strength_range` | (0.0, 1.0) | (0.0, 1.0) | **0.0 (override)** | Scales `disturbance.fz_max`; the dimension exists even when `disturbance.enable` is False (sampled, then ignored) |
| 22 | control_delay_strength | `control_delay_strength_range` | (0.0, 1.0) | (0.0, 1.0) | **0.0 (override)** | Moves the CEILING of `control_delay_steps`; `events.sample_control_delay_steps` draws the per-env lag from `[lo, lo + round(u*(hi-lo))]` |

Count check: the 23 entries are #0-#22 above (14 physics scales/offsets #0-#13, 2 buoy scales
#14-#15, 2 payload offsets #16-#17, 5 normalized `[0,1]` knobs #18-#22). `_NOMINAL_OVERRIDES`
has 7 entries: the six `0.0` rows (#17-#22) and `inertia_scale = 4.0`.

**Inertia range.** The default is `inertia_scale = (0.4, 4.8)` with nominal 4.0 (the measured
assembly inertia). The paper teacher was launched with `env.randomization.inertia_scale=[3.6,6.2]`;
see `scripts/paper/train_teacher.sh`.

**Added-mass clamp.** After sampling, added mass is clamped per axis to 0.95 times the
randomized rigid-body inertia (§5), so the upper tail of `added_mass_scale` is attenuated when
the co-sampled inertia is small.

**Observation noise.** `obs_noise_scale` multiplies the `_OBS_NOISE_STD` constant (69 entries,
one per base observation channel) per env and adds the result as an extra noise layer.
`apply_bias_ema_obs` (default `use_bias_ema_obs=True`) pads the std with 3 zeros for the
bias-EMA channels, so the live noise model has 72 entries, matching the 72D observation.

### Block B: Uniform-only (in `DomainRandomizationCfg`, not in `_PARAM_DEFS`)

Sampled uniformly at every reset and never touched by the curriculum.

| name | Cfg default | Meaning |
|:---|:---|:---|
| joint_stiffness_range (arm actuator) | (30.0, 150.0) | Arm PD P-gain, absolute |
| joint_damping_range (arm actuator) | (0.3, 7.0) | Arm PD D-gain, absolute |
| joint_effort_limit_range | (0.7, 1.0) | Multiplier on the arm torque limit |
| joint_static_friction_range | (0.0, 0.03) | Arm joint static friction, absolute |
| joint_viscous_friction_range | (0.0, 0.2) | Arm joint viscous friction, absolute |
| thrust_coefficient_scale | (0.7, 1.3) | Multiplier on the thrust coefficient (gain, applied before the clamp) |
| time_constant_scale | (0.7, 1.3) | Multiplier on the thruster rise/fall time constants |
| max_thrust_scale | (0.85, 1.15) | Multiplier on the thrust clamp bound (`max_thrust`), i.e. the achievable wrench |
| yaw_damping_scale | (0.5, 1.5) | Extra scale on yaw (DOF 5) quadratic damping, applied after the broadcast quadratic-damping scale (overwrites index 5) |
| control_delay_steps | (0, 0) | Integer control-step lag on the applied action (1 step = 20 ms at 50 Hz); `(0, 0)` = off. Its ceiling is paced by DORAEMON dimension #22 |
| obs_delay_steps | (0, 0) | Integer control-step lag on the policy observation, applied after the sensor-noise layers; `(0, 0)` = off. Static uniform draw per reset |

`joint_damping_range` is the arm actuator's PhysX damping; `yaw_damping_scale` is the
hydrodynamic quadratic-damping scale on rotational DOF 5. They are unrelated quantities.

The `-SimToReal-v0` tasks (`config_simtoreal.py`) override `thrust_coefficient_scale` to
(0.5, 2.0) and `control_delay_steps` to (0, 3), turn faults on, and lower `performance_lb`
to 200.0. The paper teacher launch (`scripts/paper/train_teacher.sh`) further sets
`control_delay_steps=[7,13]`, `obs_delay_steps=[0,5]` and
`control_delay_strength_range=[0.60,0.70]`.

### Block C: Scalars (not `(lo, hi)` tuples)

| name | value | meaning |
|:---|:---|:---|
| payload_cog_offset_xy_radius | 0.08 | physical `r_max` for the payload XY offset; only the quantile `u` is randomized (Block A #17) |
| buoy_moment_arm | 0.180 | moment arm used by the payload-CoG static-stability clamp (§5) |

### Fault injection (`FaultInjectionCfg`, off by default)

A separate surface: component-failure modeling, not parameter spread. Off unless `fault.enable`
is set (the `-SimToReal-v0` tasks enable it). Thruster fail probability is scaled by DORAEMON
dimension #20; `thruster_always_dead` forces listed channels dead in every env. Applied in the
same reset as DR through a distinct mechanism.

---

## 3. The Beta Distribution: Per-Parameter Curriculum State

The curriculum state is 23 independent Beta distributions, one per parameter, each over that
parameter's physical `[lo, hi]` interval (stored as `_mins` / `_maxs` / `_ranges` in
`BetaDistribution`). A "harder" curriculum is a wider Beta, i.e. more entropy.

### From `(nominal, concentration)` to `Beta(a, b)`

Each parameter's initial Beta is set from its nominal and a shared concentration `c`:

$$
\mu = \mathrm{clip}\!\left(\frac{\text{nominal}-\text{lo}}{\text{hi}-\text{lo}},\,0.01,\,0.99\right),
\qquad a = \mu\,c, \qquad b = (1-\mu)\,c
$$

If either `a` or `b` falls below `_MIN_BETA_PARAM = 1.0`, the mean is preserved by deriving the
other parameter from the clamped one.

> **Concentration.** `BetaDistribution.__init__` has `concentration = 200.0`, but that default
> is dead in the ALBC path: the live scheduler constructs the distribution with
> `DoraemonCfg.init_concentration = 30.0`.

`sample(n)` draws in unit space and rescales to physical; `log_prob` inverts (clamping to
`[1e-6, 1-1e-6]`) and sums across dimensions; `kl_divergence` operates on the unit Betas only.

### The entropy the curriculum maximizes

`BetaDistribution.entropy()` adds a change-of-variables term so entropy is measured on the
physical scale:

$$
H(\phi) = \sum_{i=1}^{23}\Big(H_{\mathrm{Beta}}(a_i,b_i) + \log(\text{hi}_i-\text{lo}_i)\Big)
$$

### `build_param_specs`: fusing the bound sources

`build_param_specs(dr_cfg, param_defs, nominal_overrides)` resolves each parameter's bounds and
nominal:

1. **DR cfg ranges** are the live bounds (via `getattr(dr_cfg, field_name)`).
2. **`_NOMINAL_OVERRIDES`** sets the nominal where present; otherwise the nominal is the
   midpoint of the live range.
3. **`DoraemonCfg.param_overrides`** (applied in `DoraemonScheduler.__init__`) overrides any
   parameter's bounds and resets its nominal to the new midpoint.

The `PARAM_SPECS` constant exported from `envs/main/doraemon.py` uses a plain midpoint of the
`_PARAM_DEFS` fallback bounds and does not apply `_NOMINAL_OVERRIDES`; it is not the live
curriculum start. The live path goes through `build_param_specs` plus `_NOMINAL_OVERRIDES`.

### `EpisodeBuffer`

A ring buffer (default capacity 2000) storing, per finished episode, the sampled `xi`, the
return, and the binary `success`. `BetaDistribution.get_stats()` emits per-dimension physical
mean/std, which become the `DORAEMON/mean/<param>` and `DORAEMON/std/<param>` signals.

---

## 4. The DORAEMON Curriculum Engine

DORAEMON (Domain Randomization via Entropy Maximization, Tiboni et al., ICLR 2024) is
implemented as `DoraemonScheduler`. Every `step_interval` RL iterations it solves one
constrained optimization: widen the DR distribution as much as possible (max entropy) without
letting the estimated success rate drop below a floor and without moving too far in one step.

$$
\max_{\phi=\{(a_i,b_i)\}}\ H(\phi)
\quad\text{s.t.}\quad
\hat G(\phi)\ge\alpha
\ \text{and}\
\mathrm{KL}\!\left(\phi\,\|\,\phi_{\text{prev}}\right)\le\varepsilon
$$

### Config: engine defaults vs the ALBC live override

| field | engine default | **ALBC base** (`config.py`) | role |
|:---|:---|:---|:---|
| `performance_lb` | 80.0 | **250.0** (200.0 in `-SimToReal-v0`) | return threshold for binary success |
| `alpha` | 0.5 | 0.5 | desired IS-estimated success rate ($\alpha$) |
| `kl_ub` | 0.5 | **0.12** | per-step reverse-KL trust region ($\varepsilon$) |
| `init_concentration` | 30.0 | 30.0 | initial Beta `a+b` |
| `step_interval` | 250 | 250 | RL iters between updates |
| `buffer_size` | 2000 | 2000 | episode ring capacity |
| `min_episodes` | 200 | 200 | min buffered before first update |
| `min_ess_ratio` | 0.01 | 0.01 | ESS floor to accept an update |
| `hard_performance_constraint` | True | True | use the inverted problem when infeasible |

Read the caller's `DoraemonCfg`, not the engine defaults. The paper teacher launch sets
`performance_lb=-20.0` and `step_interval=1000000` (effectively freezing the resumed
distribution); see `scripts/paper/train_teacher.sh`.

### `step()` control flow

**Early-exit guards** (checked in order):

1. `n < min_episodes` -> report `{skipped=1, entropy=...}` -> return.
2. Otherwise always report `success_rate`, `entropy_before`, and per-param stats.
3. Not at a `step_interval` boundary (`step_count % step_interval != 0`) -> report
   `{entropy_after, kl_step=0}` -> return.

**At a boundary**, compute `prev_dist = dist.clone()` and
`Ghat = _estimate_success_rate(xi, success, ref=prev_dist)`, then dispatch:

| Condition | Action | `mode` |
|:---|:---|:--:|
| `hard_performance_constraint` and `Ghat < alpha`; `_find_feasible_start` succeeds and the re-estimated `Ghat >= alpha` | feasible start, then `_optimize_entropy` on top of it | `1.0` |
| same infeasible branch, but the re-estimated `Ghat < alpha` | keep the max-success distribution as-is | `-2.0` |
| infeasible and `_find_feasible_start` itself fails | revert to `prev_dist` | `-3.0` |
| `Ghat >= alpha` (feasible) | normal `_optimize_entropy` | `0.0` |

After dispatch it computes `entropy_after`, `kl_step`, `ess`, `ess_ratio`; if
`ess < min_ess_ratio * n` it reverts to `prev_dist` and sets `reverted = 1.0` (independent of
`mode`). Finally it appends `{iter, a, b}` to `_trajectory` for replay.

### The equations behind the engine

**KL constraint (reverse KL, per-dimension sum).** SLSQP receives $g(\phi) = \varepsilon -
\mathrm{KL} \ge 0$:

$$
\mathrm{KL}(\phi\,\|\,\phi_{\text{prev}})
= \sum_{i=1}^{23}\mathrm{KL}\!\Big(\mathrm{Beta}(a_i,b_i)\,\big\|\,\mathrm{Beta}(a_i^{\text{prev}},b_i^{\text{prev}})\Big)\le\varepsilon
$$

**IS success-rate estimate (unnormalized).** Success is binary
$\sigma_k = \mathbb{1}[J_k \ge \texttt{performance\_lb}]$ and the log-ratio is clamped to
$\pm 5$ (`_IS_LOG_CLAMP = 5.0`):

$$
\hat G(\phi)=\frac{1}{K}\sum_{k=1}^{K}\exp\!\Big(\mathrm{clip}\big(\log p_\phi(\xi_k)-\log p_{\phi_{\text{prev}}}(\xi_k),\,-5,\,+5\big)\Big)\,\sigma_k
$$

The denominator is `prev_dist` evaluated live: `_estimate_success_rate` recomputes
`prev_dist.log_prob(xi)` at call time, and no per-episode sampling log-prob is stored.

**ESS revert gate.**

$$
\mathrm{ESS}=\frac{1}{\sum_k w_k^2},\quad w_k\propto\exp\!\big(\log p_\phi(\xi_k)-\log p_{\phi_{\text{prev}}}(\xi_k)\big),\ \textstyle\sum_k w_k=1;
\quad \text{revert if } \mathrm{ESS}<\texttt{min\_ess\_ratio}\cdot n
$$

**`_optimize_entropy`** runs SLSQP in log-space:

- Variables: `log(a), log(b)`; Beta params clamped to `[1.0, 500.0]`.
- A non-converged SLSQP result is accepted only if `perf_ok AND result.fun < init_obj AND
  kl <= kl_ub`, which prevents a stalled solver from committing a sub-floor distribution.
- `_find_feasible_start` returns failure immediately if there are zero successful episodes.

An update can be a no-op in three distinct ways (SLSQP reject, `mode = -3` revert, ESS revert);
only the `mode` and `reverted` metrics distinguish them.

---

## 5. From Sampled Values to Physics (Reset-Time Application)

Application is imperative. The `randomize_*` functions are called from `_reset_physics` and
`_reset_task_and_state` in `albc_env.py`. Per reset the env samples once into a `sampled` dict
keyed by `spec.name`, builds a `DRSampler(cfg, N, device)`, and threads both into every
randomizer.

### The curriculum-vs-uniform bridge: `_sample_or_uniform`

```
_sample_or_uniform(key, sampled, shape, cfg_range, device, broadcast_dim):
    if key in sampled:      -> per-env DORAEMON tensor (scalar broadcast to broadcast_dim DOFs)
    else:                   -> uniform sample from cfg_range
```

A key present in `sampled` is DORAEMON-managed; absent means uniform. That is the only thing
that distinguishes the two.

### Base caching: `_HydroBaseCache`

`_HydroBaseCache` caches the base hydrodynamic fields lazily on the first reset (a frozen
baseline, so scaling never compounds across resets). When `rigid_body_inertia` is unset,
inertia falls back to `0.5 * added_mass[3:6]` with a warning.

### Scale vs absolute vs offset

| semantics | fields |
|:---|:---|
| scale on cached base | added_mass, linear/quadratic damping, volume, inertia, body_mass |
| absolute value | water_density, payload_mass |
| base + offset | center-of-buoyancy, center-of-gravity |

- Rotational DOF 5 (yaw) is processed twice: the quadratic-damping scale is applied, then
  overwritten by `yaw_damping_scale`.
- The main body and the buoy share the sampled keys, except volume (`volume_scale` vs
  `buoy_volume_scale`) and mass (`body_mass_scale` vs `buoy_body_mass_scale`).
- The sampled `inertia_scale` reaches both the hydrodynamics model and PhysX
  (`randomize_physx_inertia`, via a congruence transform that keeps the tensor symmetric
  positive-definite).
- Buoyancy is recomputed after the volume and water-density draws, before the CoB/CoG offsets.
- When `enable = False` the randomizers early-return.

### Payload

Payload mass is absolute; the CoG XY offset is sampled on a disk of radius
`payload_cog_offset_xy_radius` via `r = r_max * sqrt(u)` (area-uniform), with `u` the
DORAEMON-managed `payload_cog_offset_xy_u` dimension (Block A #17). The mid-episode payload
toggle is off by default (`payload_toggle_steps = 0`).

### Ocean current strength

Resolution order: DORAEMON-sampled `ocean_current_strength` if present, else a uniform sample
from `ocean_current_strength_range`, else no scaling. The strength in `[0, 1]` multiplies
`ocean_current.max_velocity`, and the path is gated on the env having an ocean-current
component (`_has_ocean_current`).

### Two stability clamps

**Added-mass vs generalized inertia** keeps $M_a / I < 1$, gated on `apply_added_mass_force`
and `body_mass` being present:

$$
M_a[i]\ \le\ 0.95\,\cdot\,\mathrm{gen\_inertia}[i],
\qquad \mathrm{gen\_inertia}=[\,m_{\text{body}},m_{\text{body}},m_{\text{body}},\ I_{xx},I_{yy},I_{zz}\,]
$$

**Payload-CoG static stability** caps the CoG offset so the buoyancy restoring moment
dominates gravity's tipping moment (scale capped at `1.0`; buoy force $F_{bu}$, moment arm
$h$ = `buoy_moment_arm`):

$$
m\,g\,\lVert r^{\text{eff}}_{xy}\rVert_2\ \le\ F_{bu}\,h,
\qquad r_{\max}=\frac{F_{bu}\,h}{m\,g}\ (\infty\ \text{if}\ m\le 10^{-6}),
\qquad s=\min\!\Big(\frac{r_{\max}}{\max(\lVert r^{\text{eff}}_{xy}\rVert,\,10^{-8})},\,1\Big)
$$

---

## 6. Training-Loop Wiring

The env owns `_doraemon`, created in `_init_doraemon`, branching on `replay_curriculum_path`:
empty gives a `DoraemonScheduler` (live learning), set gives a `CurriculumReplayer` (frozen,
§7). When active, per-env buffers `_episode_dr_xi` and `_episode_return_accum` are allocated.

```
per RESET   : xi, _ = _doraemon.sample(N)              -> stash per-env -> events apply xi to physics
per STEP    : _episode_return_accum += reward           (the sstv term is excluded, see reward.md §8)
on next RESET (per finished env):
              success = (_episode_return_accum >= performance_lb)   # binarization is in the CALLER
              _doraemon.record_episodes(xi, returns, success)
per ITER    : runner.log() -> metrics = _doraemon.step(iteration=it)  -> re-emit under DORAEMON/ prefix
```

The success binarization lives in the caller (`_log_and_reset_rewards` in `albc_env.py`); the
engine's `record_episodes` receives a pre-computed `success` tensor.

**Runner split:**

| Path | Runner | `iteration` kwarg |
|:---|:---|:---|
| TRPO (default) | `ConstraintEncoderRunner` | passed |
| PPO ablations | `OnPolicyDoraemonRunner` | not passed, so the `_trajectory` iter falls back to `_step_count` |

**Checkpointing.** `state_dict` serializes `dist_a` / `dist_b`, step/episode counts, and the full
episode buffer; the runner saves it as `doraemon_state.pt`, and `load_state_dict` raises if the
checkpoint's dimension count differs from the current `NDIMS`. `export_recording`
(`DoraemonScheduler` only) writes the curriculum trajectory for replay.

**Emitted metrics** (all under `DORAEMON/`): `success_rate`, `entropy_before`/`entropy_after`,
`kl_step`, `ess`/`ess_ratio`, `mode`, `reverted`, `skipped`, and per-parameter
`mean/<name>` / `std/<name>`.

---

## 7. Curriculum Replay

`CurriculumReplayer` is the frozen-curriculum path, active when `replay_curriculum_path` is
set. It duck-types `DoraemonScheduler` (`sample` / `step` / `record_episodes` / `state_dict`)
but does no learning:

- `sample()` still draws from a Beta.
- `step()` is a hold-last step function keyed on `iteration`: the distribution at iter `t` is
  the last recorded `(a, b)` with `iter <= t`. If `iteration` is `None` it defaults to `0`, so a
  runner that does not thread `iteration` freezes the replay at the first recorded entry.
- `record_episodes` and `load_state_dict` are no-ops; `state_dict` returns only `dist_a` /
  `dist_b`.

**Recording format** (`export_recording`): `{param_names, param_bounds, trajectory}`.
`_validate` hard-checks the param name order and bounds (tolerance `1e-9`) against the
recording and raises on mismatch.

---

## 8. Eval-Side DR

Eval DR is a fixed uniform interpolation that bypasses the DORAEMON Beta curriculum entirely.
There is no `step()` / `record_episodes` during eval; the only DORAEMON contact is reading the
run's final `mean` / `std` from TensorBoard. The entry point is `analysis/eval.py`.

### The levels

| Level | none | soft | medium | hard | ood (optional 5th) |
|:---|:--:|:--:|:--:|:--:|:--:|
| Scale fraction (`DR_SCALE` in `common.py`) | 0.0 | 0.3 | 0.6 | 1.0 | 1.0 |

`apply_dr_config` (`eval.py`) calls `build_dr_config(scale)` (`dr_config.py`), which linearly
interpolates each tuple field between a true-nominal point (scale 0) and a hard anchor (scale 1).
The hard anchor, in priority order:

1. the run's DORAEMON-learned distribution (`load_doraemon_dr`: per-param `mean +/- 2*std`
   from TensorBoard, clamped to the spec bounds);
2. the latched env anchor (`--env-dr-anchor`);
3. a plain `DomainRandomizationCfg()`.

`get_hard_dr_config` returns a deepcopy so an OOD-level `setattr` cannot clobber the global
anchor. The `ood` level, appended with `--ood`, bypasses `apply_dr_config` and uses
`build_ood_dr_config` on the DORAEMON-derived anchor. `soft`/`hard` are interpolation endpoints,
not separate config classes.

### The three modes

| mode | what it does | mechanism |
|:---|:---|:---|
| **static** | DR fixed for the whole episode; the command switches per segment | `apply_dr_config` per level |
| **periodic** | mid-episode DR shock | `apply_dr_mid_episode` builds a fresh `DRSampler` and re-randomizes hydro, mass, payload, ocean current |
| **segmented** | also changes DR mid-episode | env method `randomize_physics_mid_episode` with `torch.manual_seed(master_seed + seg_idx)` for a reproducible switch sequence |

No other eval mode exists.

### `dr_snapshot`

`_eval_dr/dr_snapshot.py` is a pure post-hoc reshaper of already-fixed, post-clamp physics
tensors into `dr_<name>[N]` arrays for logging; it is not a DR freeze/realize step. Reproducible
fixed physics instead comes from `--deterministic-dr`, which collapses each `(lo, hi)` tuple to
its midpoint.

---

## 9. Gotchas

1. **`performance_lb` is a return threshold, not a success rate.** It binarizes success; the
   success-rate target is `alpha` (0.5). Confusing them inverts the constraint.
2. **The engine does not binarize; the caller does** (`_log_and_reset_rewards` in `albc_env.py`).
3. **Read the caller's `DoraemonCfg`, not the engine defaults.** Base `kl_ub` is 0.12 and
   `performance_lb` is 250.0, not the engine's 0.5 / 80.0.
4. **`_PARAM_DEFS` literal bounds are fallback-only.** `build_param_specs` reads the live bounds
   from `config.py`; `NDIMS = 23`.
5. **Resuming across a changed `NDIMS` fails.** `load_state_dict` raises on a dimension
   mismatch, and `CurriculumReplayer._validate` raises on a name or bounds mismatch.
6. **Two concentration defaults disagree.** `BetaDistribution.__init__ = 200.0` is dead in the
   ALBC path; the live scheduler uses `DoraemonCfg.init_concentration = 30.0`.
7. **DR is applied imperatively from `_reset_physics`, not via `EventTerm`/`EventManager`.**
   Field semantics differ (scale on cached base vs absolute vs base+offset), DOF 5 (yaw) is
   processed twice, and the added-mass clamp is skipped when `apply_added_mass_force` is off.
8. **Eval `soft`/`hard` are interpolation endpoints**, not separate config classes.

---

## Source files

| Concern | File |
|:---|:---|
| Engine: `DoraemonCfg`, `BetaDistribution`, `EpisodeBuffer`, `DoraemonScheduler`, `CurriculumReplayer`, `build_param_specs` | `marinelab/marinelab/algorithms/doraemon.py` |
| `_PARAM_DEFS` (23), `_NOMINAL_OVERRIDES`, `PARAM_SPECS`, `NDIMS` | `constrained_albc/envs/main/doraemon.py` |
| DR ranges and the live `DoraemonCfg` | `constrained_albc/envs/main/config.py` |
| `-SimToReal-v0` plant overrides | `constrained_albc/envs/main/config_simtoreal.py` |
| Reset-time application | `constrained_albc/envs/main/mdp/events.py` |
| Sample + record wiring | `constrained_albc/envs/main/albc_env.py` |
| Runner step call site | `constrained_albc/algorithms/runners/constraint_encoder_runner.py`, `on_policy_doraemon_runner.py` |
| Eval levels / anchor / modes | `constrained_albc/analysis/{eval.py,dr_config.py,common.py}` |
