# Sim-to-Real Gap Reduction

> **Status**: 2026-02-11 | **Source**: `config.py`, `mdp/events.py`
>
> Simulation-reality gap analysis and deployment strategy for the Hero Agent ALBC arm.

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

PhysX computes continuous PD internally. Commands are applied immediately with no delay.

| Environment | Kp Center | Kd Center | DR Range |
|:---|:---|:---|:---|
| Base RL (v0, Base-v0) | 100.0 | 3.0 | +-20% ([80,120], [2.4,3.6]) |
| TDC (TDC-v0) | 200.0 | 10.0 | +-20% ([160,240], [8,12]) |

Reason Kp/Kd are high in the TDC environment: the TDC controller requires fast position tracking.
High stiffness is needed to accurately track the small delta position commands of DLS IK.

### 2.2 DelayedPDActuator -- Failure record (2026-02-10)

A migration from `ImplicitActuatorCfg` -> `DelayedPDActuatorCfg` was attempted, but training failed completely.

```python
# Attempted configuration (currently unused)
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

Key differences:

| | ImplicitActuator | DelayedPDActuator |
|:---|:---|:---|
| PD computation | PhysX internal (continuous) | Isaac Lab explicit (200Hz discrete) |
| Delay | none | 0-50ms configurable |
| Gain interpretation | continuous PD | 200Hz discrete PD |

Failure causes (undiagnosed):
- Gain tuning: values suitable for continuous PD behave differently in discrete 200Hz PD
- Interaction between the delay buffer and env reset
- At Kp=100, bandwidth ~9Hz (9% of the Nyquist 100Hz, theoretically safe, but possibly insufficient under real nonlinear dynamics)

Current status: reverted to `ImplicitActuatorCfg`. DelayedPDActuator is left as future work.

### 2.3 Per-Environment Actuator Configuration

| Environment | Kp | Kd | Delay | Gain DR |
|:---|:---|:---|:---|:---|
| `Isaac-FullDOF-TRPO-v0` (train) | 100 | 3 | 0 | +-20% |
| `Isaac-FullDOF-TDC-v0` | 200 | 10 | 0 | +-20% |

---

## 3. Isaac Gym Reference

Actuator configuration of the original Isaac Gym implementation:

| Parameter | Final (heroagent.py) | Early (heroagent_welldone.py) |
|:---|:---|:---|
| Kp | 500 | 1000 |
| Kd | 1 | 3 |
| control_step | 4 | 1 |
| dt | 0.005 | 0.005 |
| substeps | 6 | 2 |

`substeps=6`: PD is recomputed every substep -> 1200Hz effective PD rate.
In Isaac Lab, TGS iterations partially replace this role, but
since TGS is constraints refinement rather than true time advance, the behavior is different.

---

## 4. Dynamixel Step Response Measurement

Step response measurement procedure for real-hardware calibration.

### 4.1 Equipment

- Dynamixel XM430-W350 (ALBC arm joints)
- Dynamixel SDK (Python/C++)
- U2D2 interface
- Bulk read at ~100Hz (position, velocity, current)

### 4.2 Procedure

1. Set the servo to position mode (Profile Velocity = 0 for step input)
2. Initial position: 0 deg
3. Step command: +30 deg
4. Record feedback via bulk read (~100Hz)
5. Measured items:
   - Rise time (10% -> 90%): expected 50-100ms
   - Overshoot: expected 5-15%
   - Settling time (+-2%): expected 200-400ms
   - Steady-state error: < 0.088 deg (1 encoder count)

### 4.3 Repeat Conditions

- Repeat over several position ranges (0->30, 30->60, 60->0)
- With/without load (buoy attached vs detached)
- Underwater/above-water (water viscous damping effect)

---

## 5. Simulation PD Tuning to Match Real Response

### 5.1 Settling Time Matching

Settling time depends mainly on Kp.

$$t_s = \frac{4}{\zeta \cdot \omega_n}, \quad \omega_n = \sqrt{K_p / J}$$

If the real settling time is 300ms and J ~ 0.03 kg*m^2:

$$\omega_n = \frac{4}{0.87 \times 0.3} = 15.3 \text{ rad/s}, \quad K_p = \omega_n^2 \cdot J = 7.0$$

### 5.2 Overshoot Matching

Overshoot depends on the damping ratio ($\zeta$):

$$\% \text{OS} = \exp\!\left(\frac{-\pi \zeta}{\sqrt{1 - \zeta^2}}\right) \times 100$$

| Overshoot | $\zeta$ |
|:---|:---|
| 10% | 0.59 |
| 5% | 0.69 |
| 0% | >= 1.0 |

### 5.3 Delay Matching

Convert the "0 -> first movement" time measured on the real robot into a number of physics steps:

$$\text{delay\_steps} = \text{round}(\text{delay\_time} / \text{physics\_dt})$$

Example: 15ms / 5ms = 3 steps.

### 5.4 Dynamixel PID Register vs SI Units

The Dynamixel PID gain register is not in SI units.
PWM = Kp_dxl * pos_error + Ki_dxl * integral + Kd_dxl * vel.
Since the conversion coefficient differs per motor model, step-response-based system identification is more practical.

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

Key point: the TDC controller's EE position is always computed from the FK of the **actual joint position**.
Even if the difference between the rate-limited desired position and the actual position accumulates,
windup does not accumulate because it is recomputed based on the actual position at the next step.

### 6.2 Real Robot Adaptation

For Dynamixel:
1. Set the Profile Velocity register to max_vel (hardware rate limiting)
2. Send the position command directly (velocity integration unnecessary)
3. Compute the TDC controller's EE position via FK from the present position of the bulk read

In simulation, the velocity command is integrated to generate the position target, but
on the real robot, Dynamixel generates the trajectory internally, so the position command is used directly.

---

## 7. Real Robot Deployment Checklist

### 7.1 Pre-deployment

- [ ] Dynamixel step response measurement completed
- [ ] Tune simulation PD gain to match the step response
- [ ] Adjust delay range based on the measured delay
- [ ] Adjust DR range to match the real-hardware variation
- [ ] Prepare the underwater test environment (water tank)

### 7.2 Hardware Setup

- [ ] Verify servo ID, baudrate, operating mode with Dynamixel Wizard
- [ ] Set Profile Velocity (rate limiting)
- [ ] Minimize Return Delay Time (0 or 1)
- [ ] Set torque limit (safety)
- [ ] Verify emergency stop mechanism

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

- [system-overview.md](../explanation/system-overview.md): Simulation configuration details
- [domain-randomization.md](domain-randomization.md): DR ranges and sensor noise
- [tdc-control-law.md](../explanation/tdc-control-law.md): TDC controller equations

---

**Created**: 2026-02-11
**Updated**: 2026-02-11
