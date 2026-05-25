# Domain Randomization

> **Status**: 2026-02-14 (4차 극단 강화: TDE stability boundary 초과) | **Source**: `config.py`, `base_env.py`, `mdp/events.py`
>
> Hero Agent ALBC 환경의 Domain Randomization(DR) 구현 전체 검토.
> 12개 카테고리, 35+ 파라미터, Fossen 모델 기반 물리적 랜덤화.
> BIR Survey (Zhu et al. 2023) 및 Sim-to-Real Locomotion (Tan et al. 2018) 분석 반영.
> **2026-02-14 4차 극단 강화**: inertia [0.4,2.5], added_mass [0.3,2.0], volume/body_mass +-30%, payload 5kg. TDE stability boundary M_true/M_hat > 2를 의도적으로 초과하여 adaptive M_hat 학습 유도.

---

## Overview

DR은 두 가지 시간 스케일로 적용된다:

1. **Reset-time DR**: 에피소드 시작 시 파라미터 샘플링 (수력학, 질량, 관절 게인, 센서 바이어스 등). "다른 로봇 인스턴스"를 나타냄.
2. **Per-step DR**: 에피소드 진행 중 동적 변동 (random perturbation, action latency). "환경 변동 및 하드웨어 불확실성"을 나타냄.

---

## DR Items

### A. Initial Pose (6 parameters)

| Item | Range | Distribution | Physical Meaning |
|:---|:---|:---|:---|
| position_x | [-0.5, 0.5] m | Uniform | 수평 오프셋 |
| position_y | [-0.5, 0.5] m | Uniform | 수평 오프셋 |
| position_z | [4.0, 5.0] m | Uniform | 초기 깊이 |
| roll | [-0.785, 0.785] rad (+-45deg) | Uniform | 초기 roll 기울기 |
| pitch | [-0.785, 0.785] rad (+-45deg) | Uniform | 초기 pitch 기울기 |
| yaw | [-pi, pi] rad | Uniform | 초기 방향 |

Quaternion 기반 회전 (gimbal lock 방지). Position은 기본값에 대한 additive offset.

+-45deg 범위는 의도적으로 공격적이다. DLS IK가 singularity 근처를 자연스럽게 처리하므로, 넓은 초기 자세에서의 robust policy 학습이 가능하다.

### B. Hydrodynamic Parameters (7 categories, main body + buoy 각각 적용)

| Item | Range | Method | DOF | Physical Meaning |
|:---|:---|:---|:---|:---|
| added_mass_scale | **[0.3, 2.0]** | Multiplicative | 6 (independent) | Added mass 불확실성 (+-70/+100%) |
| linear_damping_scale | [0.7, 1.3] | Multiplicative | 6 (independent) | 마찰 감쇠 불확실성 (+-30%) |
| quadratic_damping_scale | [0.6, 1.4] | Multiplicative | 6 (independent) | 형상 항력 불확실성 (+-40%) |
| volume_scale | **[0.7, 1.3]** | Multiplicative | scalar | 부력 불확실성 (+-30%) |
| cob_offset | +-1cm (xy), +-4cm (z) | Additive | 3 | 부력 중심 오차 |
| cog_offset | +-1cm (xy), **+-6cm (z)** | Additive | 3 | 질량 중심 오차 |
| inertia_scale | **[0.4, 2.5]** | Multiplicative | 3 (independent) | 관성 모멘트 불확실성 (-60/+150%, TDE stability boundary 초과 의도) |

**Inertia 범위 근거**: Tan et al. (2018)은 관성을 "균일 밀도 가정으로 추정"하여 [50%, 150%]의 넓은 범위를 사용. Hero Agent도 URDF 기반 균일밀도 추정이므로 +-40%로 확대. TDE가 관성 변화를 보상하므로 넓은 범위에서도 안정적.

**Added mass 범위 근거 (2026-02-14 강화)**: +-30% -> +-50%. 벽/바닥 근접 시 ground effect로 added mass가 크게 변하며, 부착물/fouling에 의한 형상 변화도 크다. Added mass는 수력학 파라미터 중 불확실성이 가장 큰 항목.

**Volume/body mass 범위 근거 (2026-02-14 강화)**: +-10% -> +-15%. 수분 흡수, 생물 부착(fouling), 하우징 내 공기량 변화, 수압에 의한 미세 변형 모델링.

**CoG offset z 범위 근거 (2026-02-14 강화)**: +-4cm -> +-6cm. 페이로드 부착, 케이블 배선 변화, 내부 부품 재배치에 의한 질량 중심 이동. 정적 안정성(복원 토크)에 직접 영향하므로 robustness에 중요.

Implementation: `_randomize_hydro_model()` in `mdp/events.py`. Base tensor는 `_HydroBaseCache`로 캐싱하여 4096 병렬 환경에서의 성능 보장.

### C. Ocean Current (3 active + 3 disabled)

| Item | Range | Distribution |
|:---|:---|:---|
| linear_x/y | **[-0.75, 0.75] m/s** + N(0, 0.15) | Uniform + Gaussian |
| linear_z | **[-0.375, 0.375] m/s** + N(0, 0.075) | Uniform + Gaussian |
| angular_x/y/z | 0 (disabled) | - |

Main body와 buoy에 동일한 해류 적용 (동일 수역). 에피소드 중 일정 (reset-time only). 에피소드 길이 (~15s)가 해류 변동 시간 스케일보다 짧으므로 시변 모델링은 불필요. **0.75 m/s는 약 1.5 knots로, 연안/항만 운용 환경의 중-강 해류 속도.**

### D. Joint Initial State (2 parameters)

| Item | Range | Note |
|:---|:---|:---|
| joint1_pos | [-pi, pi] rad | 관절 한계 내 클램핑, 전 범위 |
| joint2_pos | [-pi, pi] rad | Target buffer도 동기화 |

### E. Payload (4 parameters, `enable_payload=True`일 때만)

Payload는 **gripper body**에 적용된다 (base에 고정 조인트로 연결, 오프셋 (0, 0.0881, -0.185)). PhysX가 고정 조인트를 통해 힘을 자동 전파한다.

| Item | Range | Note |
|:---|:---|:---|
| mass | **[0.0, 5.0] kg** | Weight 모델만 (drag 없음), 0=페이로드 없음 (체중 50%) |
| cog_offset_x | **[-0.30, 0.30] m** | 부착점 기준 CoG 오프셋 |
| cog_offset_y | **[-0.30, 0.30] m** | 부착점 기준 CoG 오프셋 |
| cog_offset_z | [-0.20, 0.0] m | 부착점 아래 방향 오프셋 |

**CoG offset 범위 근거 (2026-02-14 변경)**: 33cm 차체 대비 +-50cm는 물리적으로 극단적 (50cm 길이의 막대형 도구 의미). +-30cm로 축소하여 robustness-optimality trade-off 개선 (Tan et al. 참조: 너무 넓은 범위는 정책이 극단적 케이스에 대비하느라 중간 범위에서의 최적성을 희생).

Implementation: `randomize_payload()` in `mdp/events.py`.
- Payload force: $F = mg$, gripper body frame으로 변환
- Payload torque: $\tau = (\mathbf{r}_{attach} + \mathbf{r}_{cog}) \times F$
- CoG offset은 페이로드의 질량 분포 불확실성 모델링 (비대칭 도구, 긴 막대 등)

### F. Joint Actuator Gains (2 parameters)

| Item | Range (Base RL) | Range (TDC) | Note |
|:---|:---|:---|:---|
| stiffness (Kp) | [80.0, 120.0] | [160.0, 240.0] | Asset default: 100.0 / TDC optimal: 200.0 |
| damping (Kd) | [2.4, 3.6] | [8.0, 12.0] | Asset default: 3.0 / TDC optimal: 10.0 |

동일 환경 내 두 ALBC 관절에 같은 값 적용. TDC 환경은 별도 게인 범위 사용.

### G. Body Mass (1 parameter, multiplicative scale)

| Item | Range | Note |
|:---|:---|:---|
| body_mass_scale | **[0.7, 1.3]** | 모든 rigid body에 동일 스케일 (+-30%) |

PhysX `set_masses()` API 사용. 제조 공차 모델링. 관성은 hydro DR의 `inertia_scale`로 별도 랜덤화.

### H. Water Density (1 parameter)

| Item | Range | Note |
|:---|:---|:---|
| water_density | [995.0, 1025.0] kg/m^3 | 담수~해수 전 범위 |

Per-env tensor. 부력 ($F_b = \rho V g$)과 항력 ($F_d = 0.5 \rho C_d A v^2$) 모두에 영향.

### I. Sensor Noise (IMU bias + white noise)

| Item | Range | Note |
|:---|:---|:---|
| euler noise (3D) | **N(0, 0.02 rad)** | White noise per step |
| euler bias (3D) | **U(-0.02, 0.02 rad)** | Per-episode 샘플링 |
| ang_vel noise (3D) | **N(0, 0.04 rad/s)** | White noise per step |
| ang_vel bias (3D) | **U(-0.03, 0.03 rad/s)** | Per-episode 샘플링 |
| other dims (7D) | 0 | att_error, joint_pos, prev_actions에는 노이즈 없음 |

**IMU 노이즈 범위 근거 (2026-02-14 변경)**: 일반 MEMS IMU 수준으로 확대 (이전: high-precision IMU 가정). Tan et al. (2018)은 euler bias +-0.05 rad, noise std 0.05 rad를 사용. 현재 값은 그 중간 수준으로, 일반 상업용 MEMS를 보수적으로 모델링.

`NoiseModelWithAdditiveBiasCfg` 사용. Bias는 리셋 시 샘플링 (per-episode gyro drift 모델), white noise는 매 스텝 추가. Obs dims 0-5 (IMU)에만 적용, dims 6-12는 정확.

### J. Joint Friction (2 parameters)

| Item | Range | Note |
|:---|:---|:---|
| static_friction | [0.0, 0.05] | Coulomb 마찰 계수 |
| viscous_friction | [0.0, 0.3] | 속도 비례 저항 |

두 ALBC 관절에 동일 값 적용.

### K. Random Perturbation (per-step, Tan et al. 2018)

**Per-step DR**: 에피소드 진행 중 주기적 외란 인가. Reset-time DR과 달리 매 physics step 업데이트.

| Item | Value | Note |
|:---|:---|:---|
| enable_perturbation | True | DR 활성화 시 자동 적용 |
| force_range | **[0.0, 30.0] N** | ~10kg 차체에 최대 3.0 m/s^2 가속 |
| torque_range | **[0.0, 4.5] Nm** | 30N x 0.15m (half-body moment arm) |
| interval | **100 physics steps (~0.5s)** | 이벤트 간 쿨다운 (난류 환경) |
| duration | **20 physics steps (~0.1s)** | 충격 지속 시간 |

**근거**: Tan et al. (2018)은 200스텝마다 130-220N의 랜덤 외력을 인가하여 균형 회복 능력을 학습시켰다 (25kg 로봇, 5.2-8.8 m/s^2). Hero Agent는 ~10kg 수중 차량으로, 최대 15N (1.5 m/s^2)은 수중 환경에서 발생하는 비정상 외란을 모델링:
- 해류 급변 (해류는 reset-time에 상수로 설정되나, 실제로는 변동)
- 테더(tether) 장력 변동
- 물체 파지 순간 반작용력
- 구조물 접촉 반작용

**Implementation**: `base_env._update_perturbation()` (per-step 호출).
- Per-env 타이머로 비동기 perturbation 트리거 (환경간 위상 랜덤화)
- 랜덤 방향 (unit sphere) x 균일 크기 -> 3D wrench 생성
- Main body의 hydro forces에 additive로 적용
- Reset 시 타이머 위상 재랜덤화 (환경 동기화 방지)

### L. Action Latency (per-step, Tan et al. 2018)

**Per-step DR**: RL action 적용에 지연을 추가. 실제 하드웨어의 통신/연산 지연 모델링.

| Item | Value | Note |
|:---|:---|:---|
| action_latency_range | **[0, 4] physics steps** | 0-20ms at 200Hz |

**근거**: Tan et al. (2018) Table I에서 control latency를 [0, 40ms]로 명시적 랜덤화. Hero Agent에서는:
- 통신 지연: ROV 하드웨어의 RS-485/Ethernet 통신 0~10ms
- 연산 지연: 정책 추론 + 전처리 ~2-10ms (임베디드 시스템)
- TDC 영향: TDE 추정 오차 상한이 sampling period에 비례하므로, 실효 지연이 TDE 정확도에 직접 영향

**Implementation**: `base_env._get_delayed_actions()`.
- Ring buffer `_action_history`: (num_envs, max_latency+1, action_dim)
- Per-env latency `_action_latency`: reset시 uniform 샘플링, 에피소드 중 고정
- `self._actions`는 raw (비지연) 값 유지 -> observation/reward에는 영향 없음
- Control에만 delayed actions 사용 -> 에이전트가 지연을 인지하지 못하는 상황 모델링
- TDC env는 `_pre_physics_step()` 전체를 오버라이드하므로 영향 없음

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

Encoder 훈련을 위한 24D privileged information:

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
| Hydrostatic | Volume, CoB, CoG, inertia, body_mass | - | 자세 제어의 핵심 파라미터 |
| Hydrodynamic | Surge added mass | Sway/heave added mass, damping | Surge M_a가 effective inertia에 지배적 |
| External | Payload (mass + CoG) | Ocean current | 페이로드는 복원 토크 직접 변경 |
| Sensor | - | Noise/bias | 관측 노이즈는 policy robustness로 처리 |
| Perturbation | - | Force/torque | 비예측적 외란으로 robust policy에 기여 |

---

## Implementation Quality

### Strengths

1. **물리적 원칙 기반**: Fossen 모델의 질량, 감쇠, Coriolis, 부력을 정확히 분리
2. **이중 수력학 DR**: Main body와 buoy를 독립적으로 랜덤화 (buoy 부력 = 제어 권한)
3. **CoG 보정 토크**: PhysX nominal CoG와 DR CoG 차이를 정확히 보상
4. **Caching**: `_HydroBaseCache`로 텐서 재생성 방지 (4096 병렬 환경 성능)
5. **이중 시간 스케일 DR**: Reset-time (인스턴스 변동) + Per-step (환경 변동)
6. **Episode decorrelation**: 초기 분산 + jitter + perturbation 위상 랜덤화

### Parameter Range Justification (Tan et al. 2018 comparison)

| Parameter | Hero Agent | Tan et al. | Rationale |
|:---|:---|:---|:---|
| Body mass | **+-30%** | +-20% | 수분 흡수, fouling, 케이블 변동 |
| Added mass | **-70/+100%** | N/A | 가장 불확실한 파라미터, ground effect, TDE 경계 초과 의도 |
| Volume | **+-30%** | N/A | 하우징 공기, 수압 변형, 부력 불확실성 강화 |
| Inertia | **-60/+150%** | +-50% | TDE stability boundary 초과 의도 (M_true/M_hat > 2) |
| IMU noise std | **0.02 rad** | 0.05 rad | 일반 MEMS (소비자급보다 양호) |
| IMU bias | **+-0.02 rad** | +-0.05 rad | 일반 MEMS gyro drift |
| Control latency | **0-20ms** | 0-40ms | 임베디드 시스템 Ethernet/serial |
| Perturbation force | **0-30N** | 130-220N | 체중 비례 (10kg: 3.0 m/s^2 vs 25kg: 5.2-8.8 m/s^2) |
| Ocean current | **0.75 m/s (~1.5kt)** | N/A | 연안/항만 중-강 해류 |
| Payload mass | **0-5.0 kg (50%)** | N/A | 수중 샘플, 센서 장비, 중형 도구 |
| Payload CoG | **+-0.3m** | N/A | 33cm 차체 대비 현실적 범위 |

### Resolved Issues

| Issue | Description | Resolution |
|:---|:---|:---|
| Body mass 미랜덤화 | Net buoyancy 불확실성 비대칭 | Section G: PhysX `set_masses()` (+-10%) |
| Water density 고정 | 담수/해수 간 전이 불가 | Section H: Per-env tensor (995-1025) |
| Sensor noise 없음 | Sim-to-real gap 주요 원인 | Section I: IMU bias + white noise |
| Joint friction 없음 | 관절 저항 미모델링 | Section J: Static + viscous friction |
| Random perturbation 없음 | 비정상 외란 미모델링 | Section K: Per-step wrench (2026-02-14) |
| Control latency 없음 | 하드웨어 지연 미모델링 | Section L: Action delay buffer (2026-02-14) |
| Inertia 범위 보수적 | URDF 추정 불확실성 과소평가 | Section B: +-20% -> +-40% (2026-02-14) |
| Payload CoG 과도 | 33cm 차체 대비 +-50cm 비현실적 | Section E: +-50cm -> +-30cm (2026-02-14) |
| IMU 노이즈 과소 | High-precision 가정 | Section I: MEMS 수준으로 확대 (2026-02-14) |

### Remaining Minor Issues

| Issue | Description | Verdict |
|:---|:---|:---|
| Main/buoy 동일 DR 범위 | Scale factor가 multiplicative이므로 base 값 차이가 자동 반영 | Minor, 필요시 `BuoyDRCfg` 분리 |
| Ocean current 시불변 | 에피소드 ~15s < 해류 변동 시간 | Acceptable |
| Damping 미포함 (privileged obs) | 자세 제어에는 hydrostatic이 지배적 | Design choice |

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

- [system-overview.md](../explanation/system-overview.md): 환경 구조 + encoder의 privileged obs 사용
- [sim-to-real.md](sim-to-real.md): Sim-to-real gap 분석 및 배포

---

**Created**: 2026-02-11
**Updated**: 2026-02-14 (4차 극단 강화: inertia [0.4,2.5], added_mass [0.3,2.0], volume/body_mass +-30%, payload 5kg -- TDE stability boundary 초과 의도. 3차: perturbation 30N/4.5Nm, ocean current 0.75m/s, target +-0.5rad. 2차: perturbation 20N/3Nm, payload 3kg. 1차: perturbation 15N/2Nm, ocean current 0.5m/s)
