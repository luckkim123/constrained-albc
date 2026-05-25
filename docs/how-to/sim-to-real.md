# Sim-to-Real Gap Reduction

> **Status**: 2026-02-11 | **Source**: `config.py`, `mdp/events.py`
>
> Hero Agent ALBC arm의 simulation-reality gap 분석 및 배포 전략.

---

## 1. Gap Analysis

### 1.1 Actuator Gap

| Property | Simulation (Current) | Real (Dynamixel XM430) |
|:---|:---|:---|
| PD Control | PhysX implicit PD (continuous) | Internal PID (~1kHz) |
| Command Rate | Every physics step (200Hz) | 10Hz (USB bulk read/write) |
| Response Delay | 0 | 50-100ms settling |
| Gain Uncertainty | DR +-20% | Register-dependent |
| Actuator Model | `ImplicitActuatorCfg` | Dynamixel XM430-W350 |

### 1.2 Sensor Gap

| Property | Simulation | Real |
|:---|:---|:---|
| IMU Rate | 200Hz (physics sync) | 100-200Hz (VN-100, BNO055) |
| IMU Noise | DR: N(0, 0.01 rad) euler, N(0, 0.02 rad/s) angular vel | Gyro: ~0.01 rad/s, Accel: ~0.1 m/s^2 |
| IMU Bias | DR: U(-0.005, 0.005) euler, U(-0.01, 0.01) angular vel | Gyro drift (temperature dependent) |
| Joint Encoder | Exact (PhysX state) | 12-bit (0.088 deg resolution) |
| Latency | 0 | 1-5ms (I2C/SPI) |

### 1.3 Dynamics Gap

| Property | Simulation | Real |
|:---|:---|:---|
| Hydrodynamics | Fossen lumped parameter model | Full 3D flow interaction |
| Buoyancy | Constant volume (DR +-10%) | Temperature/depth dependent |
| Ocean Current | Constant + noise per episode | Spatially varying, turbulent |
| Cable Forces | None | Tether drag + tension |
| Joint Friction | DR: static [0, 0.05], viscous [0, 0.3] | Coulomb + viscous (temperature dependent) |

---

## 2. Actuator Modeling

### 2.1 Current: ImplicitActuatorCfg

```python
actuators={
    "arm": ImplicitActuatorCfg(
        joint_names_expr=["joint.*"],
        stiffness=100.0,   # Asset default (DR: +-20%)
        damping=3.0,       # Asset default (DR: +-20%)
    ),
},
```

PhysX 내부에서 연속 PD를 계산한다. 명령이 즉시 반영되며 delay가 없다.

| Environment | Kp Center | Kd Center | DR Range |
|:---|:---|:---|:---|
| Base RL (v0, Base-v0) | 100.0 | 3.0 | +-20% ([80,120], [2.4,3.6]) |
| TDC (TDC-v0) | 200.0 | 10.0 | +-20% ([160,240], [8,12]) |

TDC 환경에서 Kp/Kd가 높은 이유: TDC controller가 빠른 position tracking을 요구한다.
DLS IK의 small delta position commands를 정확히 추종하려면 높은 강성이 필요.

### 2.2 DelayedPDActuator -- 실패 기록 (2026-02-10)

`ImplicitActuatorCfg` -> `DelayedPDActuatorCfg` 마이그레이션을 시도했으나 훈련이 완전히 실패했다.

```python
# 시도한 설정 (현재 미사용)
actuators={
    "arm": DelayedPDActuatorCfg(
        joint_names_expr=["joint.*"],
        stiffness=100.0,
        damping=3.0,
        min_delay=0,
        max_delay=10,  # buffer size (50ms at 200Hz)
    ),
},
```

핵심 차이:

| | ImplicitActuator | DelayedPDActuator |
|:---|:---|:---|
| PD 계산 | PhysX 내부 (연속) | Isaac Lab explicit (200Hz discrete) |
| Delay | 없음 | 0-50ms configurable |
| Gain 해석 | 연속 PD | 200Hz discrete PD |

실패 원인 (미진단):
- Gain 튜닝: 연속 PD에 적합한 값이 discrete 200Hz PD에서는 다르게 동작
- Delay buffer와 env reset 간의 상호작용
- Kp=100에서 bandwidth ~9Hz (Nyquist 100Hz의 9%로 이론상 안전하지만, 실제 비선형 dynamics에서는 불충분할 가능성)

현재 상태: `ImplicitActuatorCfg`로 복귀. DelayedPDActuator는 미래 과제로 남겨둠.

### 2.3 Per-Environment Actuator Configuration

| Environment | Kp | Kd | Delay | Gain DR |
|:---|:---|:---|:---|:---|
| `Isaac-FullDOF-TRPO-v0` (train) | 100 | 3 | 0 | +-20% |
| `Isaac-FullDOF-TDC-v0` | 200 | 10 | 0 | +-20% |

---

## 3. Isaac Gym Reference

Isaac Gym 원래 구현의 actuator 설정:

| Parameter | Final (heroagent.py) | Early (heroagent_welldone.py) |
|:---|:---|:---|
| Kp | 500 | 1000 |
| Kd | 1 | 3 |
| control_step | 4 | 1 |
| dt | 0.005 | 0.005 |
| substeps | 6 | 2 |

`substeps=6`: PD가 매 substep마다 재계산 -> 1200Hz effective PD rate.
Isaac Lab에서는 TGS iterations이 이 역할을 부분적으로 대체하지만,
TGS는 constraints refinement이지 true time advance가 아니므로 동작이 다르다.

---

## 4. Dynamixel Step Response Measurement

실물 calibration을 위한 step response 측정 절차.

### 4.1 Equipment

- Dynamixel XM430-W350 (ALBC arm joints)
- Dynamixel SDK (Python/C++)
- U2D2 interface
- Bulk read at ~100Hz (position, velocity, current)

### 4.2 Procedure

1. Servo를 position mode로 설정 (Profile Velocity = 0 for step input)
2. Initial position: 0 deg
3. Step command: +30 deg
4. Bulk read로 feedback 기록 (~100Hz)
5. 측정 항목:
   - Rise time (10% -> 90%): 예상 50-100ms
   - Overshoot: 예상 5-15%
   - Settling time (+-2%): 예상 200-400ms
   - Steady-state error: < 0.088 deg (1 encoder count)

### 4.3 Repeat Conditions

- 여러 position 구간에서 반복 (0->30, 30->60, 60->0)
- Load 유무 (buoy attached vs detached)
- 수중/수상 (물의 점성 감쇠 효과)

---

## 5. Simulation PD Tuning to Match Real Response

### 5.1 Settling Time Matching

Settling time은 주로 Kp에 의존한다.

$$t_s = \frac{4}{\zeta \cdot \omega_n}, \quad \omega_n = \sqrt{K_p / J}$$

Real settling time이 300ms이고 J ~ 0.03 kg*m^2이면:

$$\omega_n = \frac{4}{0.87 \times 0.3} = 15.3 \text{ rad/s}, \quad K_p = \omega_n^2 \cdot J = 7.0$$

### 5.2 Overshoot Matching

Overshoot는 damping ratio ($\zeta$)에 의존한다:

$$\% \text{OS} = \exp\!\left(\frac{-\pi \zeta}{\sqrt{1 - \zeta^2}}\right) \times 100$$

| Overshoot | $\zeta$ |
|:---|:---|
| 10% | 0.59 |
| 5% | 0.69 |
| 0% | >= 1.0 |

### 5.3 Delay Matching

Real에서 측정한 "0 -> first movement" 시간을 physics step 수로 환산:

$$\text{delay\_steps} = \text{round}(\text{delay\_time} / \text{physics\_dt})$$

예: 15ms / 5ms = 3 steps.

### 5.4 Dynamixel PID Register vs SI Units

Dynamixel의 PID gain register는 SI 단위가 아니다.
PWM = Kp_dxl * pos_error + Ki_dxl * integral + Kd_dxl * vel.
환산 계수는 모터 모델마다 다르므로, step response 기반 system identification이 더 실용적이다.

---

## 6. Anti-windup in Real Deployment

### 6.1 Simulation Pattern

```python
# Rate-limit joint velocity
clamped_vel = torch.clamp(desired_vel, -max_vel, max_vel)
new_pos = current_pos + clamped_vel * dt

# Update EE position from ACTUAL joint state (not desired)
controller.update_ee_position(FK(actual_joint_pos))
```

핵심: TDC controller의 EE position은 항상 **실제 관절 위치**의 FK에서 계산된다.
rate-limiting된 desired position과 actual position의 차이가 쌓여도,
다음 step에서 실제 위치 기준으로 재계산하므로 windup이 누적되지 않는다.

### 6.2 Real Robot Adaptation

Dynamixel의 경우:
1. Profile Velocity register를 max_vel로 설정 (하드웨어 rate limiting)
2. Position command를 직접 전송 (velocity integration 불필요)
3. TDC controller의 EE position을 bulk read의 present position에서 FK로 계산

Simulation에서는 velocity command를 적분하여 position target을 생성하지만,
real에서는 Dynamixel이 내부적으로 trajectory를 생성하므로 position command를 직접 사용한다.

---

## 7. Real Robot Deployment Checklist

### 7.1 Pre-deployment

- [ ] Dynamixel step response 측정 완료
- [ ] Simulation PD gain을 step response에 맞춰 튜닝
- [ ] Delay range를 measured delay에 기반하여 조정
- [ ] DR 범위를 실물 편차에 맞춰 조정
- [ ] 수중 테스트 환경 준비 (water tank)

### 7.2 Hardware Setup

- [ ] Dynamixel Wizard로 servo ID, baudrate, operating mode 확인
- [ ] Profile Velocity 설정 (rate limiting)
- [ ] Return Delay Time 최소화 (0 or 1)
- [ ] Torque limit 설정 (안전)
- [ ] Emergency stop 메커니즘 확인

### 7.3 Software Integration

- [ ] ROS2 node: Dynamixel SDK bulk read/write (10Hz command, 100Hz feedback)
- [ ] IMU driver: VN-100 or BNO055 (100-200Hz)
- [ ] TDC controller node: 50Hz (matching simulation control_decimation=4)
- [ ] FK/IK: same parameters as simulation (L1=L2=0.233m)
- [ ] Latency measurement: end-to-end (command -> actuator movement)

### 7.4 Validation

- [ ] Step response comparison: sim vs real
- [ ] TDC attitude stabilization: 15 deg initial tilt -> recovery
- [ ] Ocean current disturbance rejection (if available)
- [ ] Long-duration stability test (> 5 min)

### 7.5 Policy Transfer (RL)

- [ ] Export trained policy weights (actor + adapt_tconv only)
- [ ] Verify observation preprocessing matches simulation
  - Joint normalization: `(pos - lower) / range * 2 - 1`
  - Attitude: Euler from quaternion (same convention)
  - Angular velocity: body frame
- [ ] Action postprocessing: `[-1, 1]` joint velocity -> integrate to position target
- [ ] Adaptation module z: history ring buffer at 50Hz, adapt_tconv inference
- [ ] Online monitoring: z statistics, M_hat values, TDE residual ratio

---

## Related Documents

- [system-overview.md](../explanation/system-overview.md): 시뮬레이션 설정 상세
- [domain-randomization.md](domain-randomization.md): DR 범위 및 센서 노이즈
- [tdc-control-law.md](../explanation/tdc-control-law.md): TDC 제어기 수식

---

**Created**: 2026-02-11
**Updated**: 2026-02-11
