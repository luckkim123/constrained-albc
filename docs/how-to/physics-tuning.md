# Physics Environment Analysis

This summarizes the physics-environment stability issues and their solutions found while simulating the same ALBC UUV in MarineGym (Isaac Gym/Sim 4.x) vs Isaac Lab (Isaac Sim 5.x).

## Effort Limit as Impulse (PhysX)

### Problem
PhysX's `set_dof_max_forces()` interprets the value as **impulse (Nm-s)**. The `eDRIVE_LIMITS_ARE_FORCES` flag is not exposed in the Isaac Sim USD schema, so the default is impulse mode.

### MarineGym Solution
```python
impulse_limit = effort_limit * physics_dt  # 9.5 * 0.005 = 0.0475 Nm-s
physics_view.set_dof_max_forces(impulse_limit)
```

### Isaac Lab Status
`ImplicitActuatorCfg(effort_limit=10.0)` -> `articulation.py:write_joint_effort_limit_to_sim()` -> `root_physx_view.set_dof_max_forces(effort_limits)`. **Passed directly without dt conversion.**

If passed without conversion: 10.0 Nm-s / 0.005s = 2000 Nm effective limit (practically unlimited). Since ImplicitActuator uses PhysX's internal PD, it acts as a solver constraint so the practical impact is limited, but further investigation is needed.

The behavior may have changed in Isaac Sim 5.x. Verification methods:
1. Compare the joint torque of both simulators with the same action
2. Set `effort_limit` extremely low (0.1 Nm) and observe the joint behavior

## Joint Max Velocity

### Applied Fix
```python
ImplicitActuatorCfg(velocity_limit_sim=3.1)  # measured XW540-T260 no-load plateau, 2026-07-06
```
URDF `velocity="30"` rad/s is unrealistic (Dynamixel XW540: ~4.19 rad/s no-load).
MarineGym uses 6.28 rad/s (2*pi); this repo now uses the measured 3.1 rad/s
(XW540-T260, 2026-07-06).

## Rigid Body Max Angular Velocity

### Applied Fix
```python
RigidBodyPropertiesCfg(max_angular_velocity=180.0)  # deg/s (= pi rad/s)
```
PhysX default ~5729 deg/s (~100 rad/s) -> limited to 180 deg/s. MarineGym: 3.14 rad/s (identical).

## Damping Stability Clamp

Both MarineGym and Isaac Lab implement this in the same way.

| Item | MarineGym | Isaac Lab |
|------|-----------|-----------|
| Clamp inertia | Uses DR'd rigid_inertia directly | DR-independent `_clamp_inertia` (safer) |
| Factor | 0.8 | 0.8 |

Isaac Lab's implementation is safer: even if inertia increases due to DR, the clamp stays at the base inertia.

## Added Mass Stability Constraint

### Applied Fix
1. **Initialization**: added per-axis ratio validation in `HydrodynamicsModel._init_hydrodynamic_matrices()`. `ValueError` if `M_a[i] / I_rigid[i] >= 1.0`, warning if `> 0.8`.

2. **Post-DR enforcement**: apply a per-axis clamp at the end of `_randomize_hydro_model()`.
```python
threshold = 0.95
max_am = threshold * gen_inertia
clamped = torch.where(exceeded, max_am, am_diag)
```

### Comparison

| Item | MarineGym | Isaac Lab (updated) |
|------|-----------|-----------|
| Approach | Per-axis ratio clamp (0.95) | Per-axis ratio clamp (0.95) + global factor (0.4~0.5) |
| Init validation | ValueError if >= 1.0 | ValueError if >= 1.0 |
| Runtime | Clamp after DR | Clamp after DR |

## Solver Configuration

| Item | MarineGym | Isaac Lab |
|------|-----------|-----------|
| Physics dt | 0.005s | 0.005s |
| Control frequency | 50Hz | 50Hz |
| Position iterations | 4 | 8 |
| Velocity iterations | 0 | 4 |
| Rigid body angular_damping | 0.2 | PhysX default (~0.05) |
| enable_stabilization | True | Not set |

Isaac Lab has higher solver quality (2x position iterations + velocity iterations).

## Acceleration Filtering

| Item | MarineGym | Isaac Lab |
|------|-----------|-----------|
| Method | Finite-difference + EMA (alpha=0.3) | Uses PhysX acceleration directly (primary) |
| Fallback | - | Finite-difference + EMA (alpha=0.3) |

Isaac Lab is more accurate: PhysX provides acceleration that reflects all constraints/forces.
