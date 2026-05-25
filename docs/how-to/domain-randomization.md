# Domain Randomization

> **Status**: 2026-02-14 (4th extreme strengthening: exceeds TDE stability boundary) | **Source**: `config.py`, `base_env.py`, `mdp/events.py`
>
> Full review of the Domain Randomization (DR) implementation for the Hero Agent ALBC environment.
> 12 categories, 35+ parameters, physical randomization based on the Fossen model.
> Reflects analysis from the BIR Survey (Zhu et al. 2023) and Sim-to-Real Locomotion (Tan et al. 2018).
> **2026-02-14 4th extreme strengthening**: inertia [0.4,2.5], added_mass [0.3,2.0], volume/body_mass +-30%, payload 5kg. Intentionally exceeds the TDE stability boundary M_true/M_hat > 2 to induce learning of an adaptive M_hat.

---

## Overview

DR is applied at two time scales:

1. **Reset-time DR**: parameter sampling at episode start (hydrodynamics, mass, joint gains, sensor bias, etc.). Represents "different robot instances".
2. **Per-step DR**: dynamic variation during the episode (random perturbation, action latency). Represents "environment variation and hardware uncertainty".

---

## DR Items

### A. Initial Pose (6 parameters)

| Item | Range | Distribution | Physical Meaning |
|:---|:---|:---|:---|
| position_x | [-0.5, 0.5] m | Uniform | Horizontal offset |
| position_y | [-0.5, 0.5] m | Uniform | Horizontal offset |
| position_z | [4.0, 5.0] m | Uniform | Initial depth |
| roll | [-0.785, 0.785] rad (+-45deg) | Uniform | Initial roll tilt |
| pitch | [-0.785, 0.785] rad (+-45deg) | Uniform | Initial pitch tilt |
| yaw | [-pi, pi] rad | Uniform | Initial heading |

Quaternion-based rotation (prevents gimbal lock). Position is an additive offset relative to the default value.

The +-45deg range is intentionally aggressive. Since DLS IK naturally handles regions near singularities, learning a robust policy from a wide range of initial attitudes is feasible.

### B. Hydrodynamic Parameters (7 categories, applied to main body + buoy separately)

| Item | Range | Method | DOF | Physical Meaning |
|:---|:---|:---|:---|:---|
| added_mass_scale | **[0.3, 2.0]** | Multiplicative | 6 (independent) | Added mass uncertainty (+-70/+100%) |
| linear_damping_scale | [0.7, 1.3] | Multiplicative | 6 (independent) | Friction damping uncertainty (+-30%) |
| quadratic_damping_scale | [0.6, 1.4] | Multiplicative | 6 (independent) | Form drag uncertainty (+-40%) |
| volume_scale | **[0.7, 1.3]** | Multiplicative | scalar | Buoyancy uncertainty (+-30%) |
| cob_offset | +-1cm (xy), +-4cm (z) | Additive | 3 | Center of buoyancy error |
| cog_offset | +-1cm (xy), **+-6cm (z)** | Additive | 3 | Center of gravity error |
| inertia_scale | **[0.4, 2.5]** | Multiplicative | 3 (independent) | Moment of inertia uncertainty (-60/+150%, intentionally exceeds TDE stability boundary) |

**Rationale for inertia range**: Tan et al. (2018) "estimated inertia under a uniform-density assumption" and used a wide range of [50%, 150%]. The Hero Agent also estimates inertia from URDF under uniform density, so it is expanded to +-40%. Since TDE compensates for inertia variation, it is stable even over a wide range.

**Rationale for added mass range (2026-02-14 strengthening)**: +-30% -> +-50%. Near walls/floors, ground effect causes added mass to vary greatly, and shape changes due to attachments/fouling are also large. Added mass is the hydrodynamic parameter with the greatest uncertainty.

**Rationale for volume/body mass range (2026-02-14 strengthening)**: +-10% -> +-15%. Models water absorption, biofouling, changes in the air volume inside the housing, and minute deformation due to water pressure.

**Rationale for CoG offset z range (2026-02-14 strengthening)**: +-4cm -> +-6cm. Center-of-gravity shift due to payload attachment, cable routing changes, and internal component rearrangement. It directly affects static stability (restoring torque), so it is important for robustness.

Implementation: `_randomize_hydro_model()` in `mdp/events.py`. The base tensor is cached via `_HydroBaseCache` to ensure performance with 4096 parallel environments.

### C. Ocean Current (3 active + 3 disabled)

| Item | Range | Distribution |
|:---|:---|:---|
| linear_x/y | **[-0.75, 0.75] m/s** + N(0, 0.15) | Uniform + Gaussian |
| linear_z | **[-0.375, 0.375] m/s** + N(0, 0.075) | Uniform + Gaussian |
| angular_x/y/z | 0 (disabled) | - |

The same ocean current is applied to the main body and buoy (same body of water). Constant during the episode (reset-time only). Since the episode length (~15s) is shorter than the time scale of current variation, time-varying modeling is unnecessary. **0.75 m/s is about 1.5 knots, a medium-to-strong current speed in coastal/harbor operating environments.**

### D. Joint Initial State (2 parameters)

| Item | Range | Note |
|:---|:---|:---|
| joint1_pos | [-pi, pi] rad | Clamped within joint limits, full range |
| joint2_pos | [-pi, pi] rad | Target buffer is also synchronized |

### E. Payload (4 parameters, only when `enable_payload=True`)

The payload is applied to the **gripper body** (connected to the base by a fixed joint, offset (0, 0.0881, -0.185)). PhysX automatically propagates forces through the fixed joint.

| Item | Range | Note |
|:---|:---|:---|
| mass | **[0.0, 5.0] kg** | Weight model only (no drag), 0 = no payload (50% of body weight) |
| cog_offset_x | **[-0.30, 0.30] m** | CoG offset relative to the attachment point |
| cog_offset_y | **[-0.30, 0.30] m** | CoG offset relative to the attachment point |
| cog_offset_z | [-0.20, 0.0] m | Downward offset below the attachment point |

**Rationale for CoG offset range (2026-02-14 change)**: +-50cm relative to the 33cm body is physically extreme (meaning a 50cm-long rod-shaped tool). Reduced to +-30cm to improve the robustness-optimality trade-off (cf. Tan et al.: an overly wide range causes the policy to sacrifice optimality in the mid-range while preparing for extreme cases).

Implementation: `randomize_payload()` in `mdp/events.py`.
- Payload force: $F = mg$, transformed into the gripper body frame
- Payload torque: $\tau = (\mathbf{r}_{attach} + \mathbf{r}_{cog}) \times F$
- The CoG offset models the payload's mass distribution uncertainty (asymmetric tools, long rods, etc.)

### F. Joint Actuator Gains (2 parameters)

| Item | Range (Base RL) | Range (TDC) | Note |
|:---|:---|:---|:---|
| stiffness (Kp) | [80.0, 120.0] | [160.0, 240.0] | Asset default: 100.0 / TDC optimal: 200.0 |
| damping (Kd) | [2.4, 3.6] | [8.0, 12.0] | Asset default: 3.0 / TDC optimal: 10.0 |

The same value is applied to both ALBC joints within an environment. The TDC environment uses a separate gain range.

### G. Body Mass (1 parameter, multiplicative scale)

| Item | Range | Note |
|:---|:---|:---|
| body_mass_scale | **[0.7, 1.3]** | Same scale applied to all rigid bodies (+-30%) |

Uses the PhysX `set_masses()` API. Models manufacturing tolerance. Inertia is randomized separately via the hydro DR `inertia_scale`.

### H. Water Density (1 parameter)

| Item | Range | Note |
|:---|:---|:---|
| water_density | [995.0, 1025.0] kg/m^3 | Full range from fresh water to sea water |

Per-env tensor. Affects both buoyancy ($F_b = \rho V g$) and drag ($F_d = 0.5 \rho C_d A v^2$).

### I. Sensor Noise (IMU bias + white noise)

| Item | Range | Note |
|:---|:---|:---|
| euler noise (3D) | **N(0, 0.02 rad)** | White noise per step |
| euler bias (3D) | **U(-0.02, 0.02 rad)** | Per-episode sampling |
| ang_vel noise (3D) | **N(0, 0.04 rad/s)** | White noise per step |
| ang_vel bias (3D) | **U(-0.03, 0.03 rad/s)** | Per-episode sampling |
| other dims (7D) | 0 | No noise on att_error, joint_pos, prev_actions |

**Rationale for IMU noise range (2026-02-14 change)**: expanded to a general MEMS IMU level (previously: assumed a high-precision IMU). Tan et al. (2018) used euler bias +-0.05 rad, noise std 0.05 rad. The current value is an intermediate level, conservatively modeling a general commercial MEMS.

Uses `NoiseModelWithAdditiveBiasCfg`. Bias is sampled at reset (per-episode gyro drift model), and white noise is added every step. Applied only to obs dims 0-5 (IMU); dims 6-12 are exact.

### J. Joint Friction (2 parameters)

| Item | Range | Note |
|:---|:---|:---|
| static_friction | [0.0, 0.05] | Coulomb friction coefficient |
| viscous_friction | [0.0, 0.3] | Velocity-proportional resistance |

The same value is applied to both ALBC joints.

### K. Random Perturbation (per-step, Tan et al. 2018)

**Per-step DR**: periodic external disturbance applied during the episode. Unlike reset-time DR, it updates every physics step.

| Item | Value | Note |
|:---|:---|:---|
| enable_perturbation | True | Applied automatically when DR is enabled |
| force_range | **[0.0, 30.0] N** | Up to 3.0 m/s^2 acceleration on a ~10kg body |
| torque_range | **[0.0, 4.5] Nm** | 30N x 0.15m (half-body moment arm) |
| interval | **100 physics steps (~0.5s)** | Cooldown between events (turbulent environment) |
| duration | **20 physics steps (~0.1s)** | Impulse duration |

**Rationale**: Tan et al. (2018) applied a random external force of 130-220N every 200 steps to train balance recovery (25kg robot, 5.2-8.8 m/s^2). The Hero Agent is a ~10kg underwater vehicle, and the maximum 15N (1.5 m/s^2) models the irregular disturbances that occur in underwater environments:
- Sudden current changes (the current is set as a constant at reset-time, but in reality it varies)
- Tether tension variation
- Reaction force at the moment of grasping an object
- Reaction from structure contact

**Implementation**: `base_env._update_perturbation()` (called per-step).
- Asynchronous perturbation triggering via per-env timers (phase randomization across environments)
- Random direction (unit sphere) x uniform magnitude -> 3D wrench generation
- Applied additively to the main body's hydro forces
- Timer phase re-randomized at reset (prevents environment synchronization)

### L. Action Latency (per-step, Tan et al. 2018)

**Per-step DR**: adds delay to RL action application. Models the communication/computation latency of real hardware.

| Item | Value | Note |
|:---|:---|:---|
| action_latency_range | **[0, 4] physics steps** | 0-20ms at 200Hz |

**Rationale**: Tan et al. (2018) Table I explicitly randomizes control latency over [0, 40ms]. For the Hero Agent:
- Communication latency: 0-10ms over the ROV hardware's RS-485/Ethernet communication
- Computation latency: policy inference + preprocessing ~2-10ms (embedded system)
- TDC impact: since the upper bound of the TDE estimation error is proportional to the sampling period, the effective delay directly affects TDE accuracy

**Implementation**: `base_env._get_delayed_actions()`.
- Ring buffer `_action_history`: (num_envs, max_latency+1, action_dim)
- Per-env latency `_action_latency`: uniformly sampled at reset, fixed during the episode
- `self._actions` retains the raw (undelayed) value -> no effect on observation/reward
- Delayed actions are used only for control -> models a situation where the agent is unaware of the delay
- The TDC env overrides the entire `_pre_physics_step()`, so it is unaffected

---

## Per-Environment DR Activation

| Environment | Task ID | DR | Current | Payload | Noise | Perturb | Latency |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `ALBCEnvCfg` (debug) | — (no DR) | OFF | OFF | OFF | OFF | OFF | OFF |
| `ALBCTrainEnvCfg` | `Isaac-FullDOF-TRPO-v0` | ON | ON | ON | ON | ON | ON |
| TDC cfg | `Isaac-FullDOF-TDC-v0` | ON | ON | ON | ON | ON | N/A |

Note: Latency "N/A" = TDC env overrides `_pre_physics_step()` entirely, so RL action latency does not apply. Perturbation applies to all envs via `_apply_action()`.

---

## DR Application Sequence

Two time scales of DR:

### Reset-time DR (per episode)

```
_reset_idx() execution order:
  1. Logging (episode metrics)
  2. Component reset (robot, action buffers)
  3. Episode length decorrelation (full batch: full range, individual: 10% jitter)
  3b. Perturbation timer reset (random phase) + action latency sampling
  4. Hydrodynamics reset + DR
     - hydro.reset() + buoy_hydro.reset() (density also reset)
     - payload reset to defaults
     - randomize_hydrodynamics() [if enabled] (includes water density)
     - randomize_body_mass() [if enabled]
     - randomize_payload() [if enabled]
     - randomize_ocean_current() [if has current]
  5. Attitude task reset
  6. Robot state reset
     - randomize_joint_positions() [if DR]
     - randomize_robot_pose() [if DR]
  7. Joint actuator DR (always applied -- resets to defaults when DR disabled)
     - randomize_joint_gains()
     - randomize_joint_friction()
  8. Potential initialization
```

### Per-step DR (every physics step)

```
_apply_action() per-step events:
  1. _update_perturbation()
     - Advance per-env timer
     - At phase 0: generate random wrench (force + torque)
     - At phase duration: clear wrench
     - Add to main body hydro forces

_pre_physics_step() per-step events:
  2. _get_delayed_actions()
     - Shift action history buffer
     - Return delayed action based on per-env latency
     - Used for control integration only (obs uses raw actions)
```

---

## Privileged Observations (Encoder)

24D privileged information for encoder training:

```
Hydrodynamics (7D):    CoG(3), CoB(3), + 1
Dynamic response (5D)
Payload (4D):          cog_offset_xyz(3), + 1
Actuator (4D)
Environment (4D)
```

> Verified against `mdp/observations.py::compute_privileged_obs` (current 24D layout).
> The older `hero_agent` HORA encoder used a 28D privileged vector — that layout is
> deprecated.

| Category | Included | Excluded | Rationale |
|:---|:---|:---|:---|
| Hydrostatic | Volume, CoB, CoG, inertia, body_mass | - | Core parameters for attitude control |
| Hydrodynamic | Surge added mass | Sway/heave added mass, damping | Surge M_a dominates effective inertia |
| External | Payload (mass + CoG) | Ocean current | The payload directly changes the restoring torque |
| Sensor | - | Noise/bias | Observation noise is handled by policy robustness |
| Perturbation | - | Force/torque | Unpredictable disturbance contributes to a robust policy |

---

## Implementation Quality

### Strengths

1. **Grounded in physical principles**: precisely separates the mass, damping, Coriolis, and buoyancy of the Fossen model
2. **Dual hydrodynamic DR**: randomizes the main body and buoy independently (buoy buoyancy = control authority)
3. **CoG correction torque**: precisely compensates for the difference between the PhysX nominal CoG and the DR CoG
4. **Caching**: `_HydroBaseCache` prevents tensor regeneration (4096 parallel environment performance)
5. **Dual time-scale DR**: Reset-time (instance variation) + Per-step (environment variation)
6. **Episode decorrelation**: initial dispersion + jitter + perturbation phase randomization

### Parameter Range Justification (Tan et al. 2018 comparison)

| Parameter | Hero Agent | Tan et al. | Rationale |
|:---|:---|:---|:---|
| Body mass | **+-30%** | +-20% | Water absorption, fouling, cable variation |
| Added mass | **-70/+100%** | N/A | Most uncertain parameter, ground effect, intentionally exceeds the TDE boundary |
| Volume | **+-30%** | N/A | Housing air, water-pressure deformation, strengthened buoyancy uncertainty |
| Inertia | **-60/+150%** | +-50% | Intentionally exceeds the TDE stability boundary (M_true/M_hat > 2) |
| IMU noise std | **0.02 rad** | 0.05 rad | General MEMS (better than consumer grade) |
| IMU bias | **+-0.02 rad** | +-0.05 rad | General MEMS gyro drift |
| Control latency | **0-20ms** | 0-40ms | Embedded system Ethernet/serial |
| Perturbation force | **0-30N** | 130-220N | Proportional to body weight (10kg: 3.0 m/s^2 vs 25kg: 5.2-8.8 m/s^2) |
| Ocean current | **0.75 m/s (~1.5kt)** | N/A | Medium-to-strong coastal/harbor current |
| Payload mass | **0-5.0 kg (50%)** | N/A | Underwater samples, sensor equipment, medium-sized tools |
| Payload CoG | **+-0.3m** | N/A | Realistic range relative to the 33cm body |

### Resolved Issues

| Issue | Description | Resolution |
|:---|:---|:---|
| Body mass not randomized | Asymmetric net buoyancy uncertainty | Section G: PhysX `set_masses()` (+-10%) |
| Water density fixed | No transfer between fresh/sea water | Section H: Per-env tensor (995-1025) |
| No sensor noise | Major cause of the sim-to-real gap | Section I: IMU bias + white noise |
| No joint friction | Joint resistance not modeled | Section J: Static + viscous friction |
| No random perturbation | Irregular disturbance not modeled | Section K: Per-step wrench (2026-02-14) |
| No control latency | Hardware delay not modeled | Section L: Action delay buffer (2026-02-14) |
| Conservative inertia range | Underestimated URDF estimation uncertainty | Section B: +-20% -> +-40% (2026-02-14) |
| Excessive payload CoG | +-50cm unrealistic relative to the 33cm body | Section E: +-50cm -> +-30cm (2026-02-14) |
| Underestimated IMU noise | Assumed high-precision | Section I: expanded to MEMS level (2026-02-14) |

### Remaining Minor Issues

| Issue | Description | Verdict |
|:---|:---|:---|
| Same DR range for main/buoy | Since the scale factor is multiplicative, the base value difference is automatically reflected | Minor, split into `BuoyDRCfg` if needed |
| Time-invariant ocean current | Episode ~15s < current variation time | Acceptable |
| Damping not included (privileged obs) | Hydrostatic dominates for attitude control | Design choice |

---

## Base Parameter Reference

### Main Body (HeroAgentHydrodynamicsCfg)

| Parameter | Value |
|:---|:---|
| Geometry | Cylinder R=0.09m, L=0.325m, m=9.18kg |
| Water density | 998 kg/m^3 (default) |
| Volume | 0.00827 m^3 |
| Buoyancy / Weight | 80.9N / 90.1N (net: -9.2N, negatively buoyant) |
| Added mass | (0.6, 5.76, 5.76, 0.04, 0.05, 0.05) |
| Linear damping | (2.0, 4.0, 4.0, 0.1, 0.1, 0.1) |
| Quadratic damping | (26.0, 26.0, 10.7, 1.5, 1.5, 0.01) |
| CoB | (0.0, 0.0, 0.0) |
| CoG | (0.0, 0.0, -0.10) |
| Inertia | (0.0994, 0.0994, 0.0372) |

### Buoy Body (HeroAgentBuoyHydrodynamicsCfg)

| Parameter | Value |
|:---|:---|
| Geometry | Cylinder R=0.085m, H=0.118m, m=0.93kg |
| Volume | 0.00268 m^3 |
| Buoyancy / Weight | 26.2N / 9.1N (net: +17.1N, positively buoyant) |
| Added mass | (0.15, 1.5, 1.5, 0.01, 0.01, 0.01) |
| Linear damping | (0.5, 0.5, 0.5, 0.01, 0.01, 0.01) |
| Quadratic damping | (4.6, 4.6, 4.6, 0.1, 0.1, 0.1) |
| CoB / CoG | (0.0, 0.0, 0.0) / (0.0, 0.0, 0.0) |
| Inertia | (0.00278, 0.00278, 0.00336) |

### System Total

| Parameter | Value |
|:---|:---|
| Total buoyancy | 80.9 + 26.2 = 107.1 N |
| Total weight | ~104.1 N (approximate) |
| Net | ~+3.0 N (slightly positively buoyant) |

---

## References

- Tan, J., et al. (2018). "Sim-to-Real: Learning Agile Locomotion For Quadruped Robots." RSS.
  - Table I: DR parameter ranges (mass, inertia, latency, perturbation)
  - Key insight: perturbation forces + control latency are essential for sim-to-real transfer
- Zhu, Y., et al. (2023). "A Survey on Sim-to-Real Transfer for Robotics." (BIR Survey)
  - Taxonomy of DR categories and theoretical analysis

## Related Documents

- [system-overview.md](../explanation/system-overview.md): Environment structure + encoder's use of privileged obs
- [sim-to-real.md](sim-to-real.md): Sim-to-real gap analysis and deployment

---

**Created**: 2026-02-11
**Updated**: 2026-02-14 (4th extreme strengthening: inertia [0.4,2.5], added_mass [0.3,2.0], volume/body_mass +-30%, payload 5kg -- intentionally exceeds the TDE stability boundary. 3rd: perturbation 30N/4.5Nm, ocean current 0.75m/s, target +-0.5rad. 2nd: perturbation 20N/3Nm, payload 3kg. 1st: perturbation 15N/2Nm, ocean current 0.5m/s)
