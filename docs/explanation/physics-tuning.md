# Physics Environment Tuning

> **Status**: 2026-07-12 (refreshed: `max_angular_velocity`/`angular_damping`/`effort_limit_sim`
> corrected against current disk; `marinelab.physics` references updated to `marinelab.core`
> after the 2026-07-12 shim removal) | **Source**: `marinelab/marinelab/assets/albc/albc.py`,
> `marinelab/marinelab/core/hydrodynamics.py`, `constrained_albc/envs/main/config.py`,
> `isaaclab/source/isaaclab/isaaclab/assets/articulation/articulation.py`

Physics-environment stability issues and their resolutions, found while simulating the same
ALBC UUV in MarineGym (Isaac Gym/Sim 4.x, reference-only) vs Isaac Lab (Isaac Sim 5.x, this
project's engine). This is rationale — for current DR ranges see
[`reference/domain-randomization-and-doraemon.md`](../reference/domain-randomization-and-doraemon.md);
for how to change them see [`how-to/domain-randomization.md`](../how-to/domain-randomization.md).

## Effort Limit as Impulse (PhysX)

### Problem

PhysX's `set_dof_max_forces()` interprets the value as **impulse (Nm-s)**. The
`eDRIVE_LIMITS_ARE_FORCES` flag is not exposed in the Isaac Sim USD schema, so the default
is impulse mode.

### MarineGym Solution

```python
impulse_limit = effort_limit * physics_dt  # 9.5 * 0.005 = 0.0475 Nm-s
physics_view.set_dof_max_forces(impulse_limit)
```

### Isaac Lab Status (verified against current disk)

The ALBC arm actuator sets `ImplicitActuatorCfg(effort_limit_sim=13.0)` (Nm; above the
Dynamixel XW540 stall torque of 9.5 Nm — `marinelab/marinelab/assets/albc/albc.py`). Isaac
Lab's naming has moved on from the plain `effort_limit` field the earlier version of this
doc cited: `effort_limit_sim` is now the PhysX-facing field, and for implicit actuators it is
aliased 1:1 to `effort_limit` (`isaaclab/actuators/actuator_pd.py`).

`Articulation.write_joint_effort_limit_to_sim()` (`assets/articulation/articulation.py:805`)
passes the limit straight to `root_physx_view.set_dof_max_forces()` with **no dt
conversion** — confirmed by reading the current Isaac Sim 5.1 source, not inferred. Whether
PhysX's implicit-actuator PD path (a solver constraint, not a raw applied force) makes the
impulse-vs-force distinction moot in practice is still unverified; if it matters, compare
joint torque between the two simulators under the same action, or set `effort_limit_sim` to
an extreme low value (e.g. 0.1 Nm) and observe joint behavior.

## Joint Max Velocity

### Applied Fix

```python
ImplicitActuatorCfg(velocity_limit_sim=3.1)  # measured XW540-T260 no-load plateau, 2026-07-06
```

URDF `velocity="30"` rad/s is unrealistic (Dynamixel XW540: ~4.19 rad/s no-load). MarineGym
uses 6.28 rad/s (2π); this repo uses the measured 3.1 rad/s (XW540-T260, 2026-07-06) —
verified current in `marinelab/marinelab/assets/albc/albc.py`.

## Rigid Body Max Angular Velocity

### Applied Fix (corrected — previous doc text was stale)

```python
RigidBodyPropertiesCfg(max_angular_velocity=720.0)  # deg/s (= 4*pi rad/s)
```

Current value in `marinelab/marinelab/assets/albc/albc.py` is **720.0 deg/s**, not the
180.0 deg/s an earlier version of this page claimed. The code comment explains why: "arm
links accumulate parent joint velocities" — the arm's rotating links compound the base
body's angular rate plus the joint's own spin, so a tighter cap tuned for the base body
alone would clip legitimate arm motion. MarineGym's reference value (3.14 rad/s ≈ 180
deg/s) does not carry this compounding concern since it caps a different body configuration.

## Damping Stability Clamp

Both MarineGym and Isaac Lab implement a per-axis added-mass/inertia ratio clamp the same
way — verified in `marinelab/marinelab/core/hydrodynamics.py`.

| Item | MarineGym | Isaac Lab |
|---|---|---|
| Clamp inertia | Uses DR'd rigid_inertia directly | DR-independent `_clamp_inertia`, frozen at init (safer) |
| Factor | 0.8 (warning threshold) | 0.8 (warning threshold, `_validate_added_mass_stability`) |

Isaac Lab's `_clamp_inertia` is cached once in `HydrodynamicsModel.__init__` and never
re-derived from a DR-randomized inertia, so a wide DR `inertia_scale` range cannot loosen
this particular stability guard mid-run.

## Added Mass Stability Constraint

### Applied Fix

1. **Initialization**: `HydrodynamicsModel._validate_added_mass_stability()`
   (`marinelab/marinelab/core/hydrodynamics.py`) raises `ValueError` per-axis if
   `M_a[i] / I_rigid[i] >= 1.0`, warns if `> 0.8`.

2. **Post-DR enforcement**: a per-axis clamp applied at the end of DR hydrodynamics
   randomization (`constrained_albc/envs/main/mdp/events.py`):

```python
threshold = 0.95
max_am = threshold * gen_inertia
clamped = torch.where(exceeded, max_am, am_diag)
```

### Comparison

| Item | MarineGym | Isaac Lab |
|---|---|---|
| Approach | Per-axis ratio clamp (0.95) | Per-axis ratio clamp (0.95), same mechanism |
| Init validation | `ValueError` if >= 1.0 | `ValueError` if >= 1.0 |
| Runtime | Clamp after DR | Clamp after DR |

Note this is the module previously imported as `marinelab.physics` — that shim was removed
2026-07-12; import `HydrodynamicsModel` from `marinelab.core`.

## Solver Configuration

| Item | MarineGym | Isaac Lab |
|---|---|---|
| Physics dt | 0.005s | 0.005s (`ALBCEnvCfg.sim.dt`) |
| Control frequency | 50Hz | 50Hz (`decimation=4` at 200Hz physics) |
| Position iterations | 4 | 8 (`solver_position_iteration_count`, ALBC asset) |
| Velocity iterations | 0 | 4 (`solver_velocity_iteration_count`, ALBC asset) |
| Rigid body angular_damping | 0.2 | 0.2 (explicitly set, matches MarineGym — not a PhysX default) |
| enable_stabilization | True | `False` (isaaclab `PhysxCfg` default; not overridden) |

Isaac Lab uses higher solver quality (2x position iterations + 4x velocity iterations) than
MarineGym.

## Acceleration Filtering

| Item | MarineGym | Isaac Lab |
|---|---|---|
| Method | Finite-difference + EMA (alpha=0.3) | Uses PhysX acceleration directly (primary) |
| Fallback | - | Finite-difference + EMA (alpha=0.3) |

Isaac Lab is more accurate here: PhysX provides acceleration that reflects all
constraints/forces, rather than being derived by differencing velocity.
