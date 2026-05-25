# Physics Environment Analysis

MarineGym(Isaac Gym/Sim 4.x) vs Isaac Lab(Isaac Sim 5.x)에서 동일한 ALBC UUV를 시뮬레이션하면서 발견한 물리 환경 안정성 문제와 해결 방안을 정리합니다.

## Effort Limit as Impulse (PhysX)

### Problem
PhysX의 `set_dof_max_forces()`는 값을 **impulse(Nm-s)**로 해석함. `eDRIVE_LIMITS_ARE_FORCES` 플래그가 Isaac Sim USD 스키마에 노출되지 않아 기본값이 impulse 모드.

### MarineGym Solution
```python
impulse_limit = effort_limit * physics_dt  # 9.5 * 0.005 = 0.0475 Nm-s
physics_view.set_dof_max_forces(impulse_limit)
```

### Isaac Lab Status
`ImplicitActuatorCfg(effort_limit=10.0)` -> `articulation.py:write_joint_effort_limit_to_sim()` -> `root_physx_view.set_dof_max_forces(effort_limits)`. **dt 변환 없이 직접 전달.**

변환 없이 전달하면: 10.0 Nm-s / 0.005s = 2000 Nm 실효 제한 (사실상 무제한). ImplicitActuator는 PhysX 내부 PD를 사용하므로 solver 제약으로 작동하여 실질적 영향은 제한적이나, 추가 조사 필요.

Isaac Sim 5.x에서 동작이 변경되었을 가능성 있음. 검증 방법:
1. 동일 action으로 양쪽 시뮬레이터의 joint torque 비교
2. `effort_limit`을 극단적으로 낮게 설정(0.1 Nm)하고 joint 동작 관찰

## Joint Max Velocity

### Applied Fix
```python
ImplicitActuatorCfg(velocity_limit_sim=6.28)  # 2*pi rad/s
```
URDF `velocity="30"` rad/s는 비현실적 (Dynamixel XW540: ~4.19 rad/s no-load).
MarineGym도 동일하게 6.28 rad/s로 설정.

## Rigid Body Max Angular Velocity

### Applied Fix
```python
RigidBodyPropertiesCfg(max_angular_velocity=180.0)  # deg/s (= pi rad/s)
```
PhysX default ~5729 deg/s (~100 rad/s) -> 180 deg/s로 제한. MarineGym: 3.14 rad/s (동일).

## Damping Stability Clamp

MarineGym과 Isaac Lab 모두 동일한 방식으로 구현 완료.

| Item | MarineGym | Isaac Lab |
|------|-----------|-----------|
| Clamp inertia | DR'd rigid_inertia 직접 사용 | DR-independent `_clamp_inertia` (더 안전) |
| Factor | 0.8 | 0.8 |

Isaac Lab이 더 안전한 구현: DR로 inertia가 증가해도 clamp는 기본 관성으로 유지.

## Added Mass Stability Constraint

### Applied Fix
1. **Initialization**: `HydrodynamicsModel._init_hydrodynamic_matrices()`에서 per-axis ratio 검증 추가. `M_a[i] / I_rigid[i] >= 1.0`이면 `ValueError`, `> 0.8`이면 warning.

2. **Post-DR enforcement**: `_randomize_hydro_model()` 끝에서 per-axis clamp 적용.
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

Isaac Lab이 더 높은 solver quality (2x position iterations + velocity iterations).

## Acceleration Filtering

| Item | MarineGym | Isaac Lab |
|------|-----------|-----------|
| Method | Finite-difference + EMA (alpha=0.3) | PhysX acceleration 직접 사용 (primary) |
| Fallback | - | Finite-difference + EMA (alpha=0.3) |

Isaac Lab이 더 정확: PhysX가 모든 constraint/force를 반영한 가속도 제공.
