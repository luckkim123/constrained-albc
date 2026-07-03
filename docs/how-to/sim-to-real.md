# Sim-to-Real Gap Reduction

> **Status**: 2026-02-11 | **Source**: `config.py`, `mdp/events.py`
>
> Simulation-reality gap analysis and deployment strategy for the Hero Agent ALBC arm.

---

## 1. Gap Analysis

### 1.1 Actuator Gap

| Property | Simulation (Current) | Real (Dynamixel XW540-T260) |
|:---|:---|:---|
| PD Control | PhysX implicit PD (continuous) | Internal PID (~1kHz) |
| Command Rate | Every physics step (200Hz) | 10Hz (USB bulk read/write) |
| Response Delay | 0 | 50-100ms settling |
| Gain Uncertainty | DR: abs range [40,120] Nm/rad | Register-dependent |
| Actuator Model | `ImplicitActuatorCfg` | Dynamixel XW540-T260 |

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

### 1.4 What is actually measurable with the onboard sensor suite

A 2026-07-02 audit enumerated all sim parameters and narrowed the real-hardware measurement
program to **3 genuine targets**, then checked each against the actual onboard sensors. The real
robot carries **IMU + pressure ONLY** — no DVL, and **no load cell / force-torque sensor**.

| Measurement target | IMU + pressure + Dynamixel bus telemetry? | Needs load cell? | Why |
|:---|:---|:---|:---|
| TAM roll/pitch moment-arm | No | Yes | measures FORCE; a single thruster's angular accel folds unknown inertia $I$ + added-mass $A$ into $M = (I + A)\dot\omega$ (underdetermined) — IMU cannot recover force |
| Thrust curve (deadband + nonlinearity) | No | Yes | same — force is not recoverable from IMU acceleration |
| Arm joint step-response | Yes | No | Dynamixel bus telemetry (present position/velocity/current); uses neither IMU nor pressure — see §4 |
| (bonus) Net buoyancy | Yes | No | thrusters off, log depth $z(t)$ with the pressure sensor — simplest onboard measurement |

A free-decay test (tilt-and-release with IMU) is observable but **useless for parameter ID**: the
oscillation frequency lumps GM, inertia, and added-mass into one equation,
$\omega_n^2 = \rho g V\,GM / (I + A)$, so none of them is separable from a single measurement.

**Verdict**: without a load cell, the only real measurement that reduces the gap now is the **arm
step-response** (bus telemetry, §4), with **net buoyancy** (pressure) as a cheap bonus. The TAM
moment-arm and thrust curve cannot be measured onboard, so their sim-to-real uncertainty is
handled by **Domain Randomization bands** instead of measurement (TAM and `max_thrust` currently
have no DR band — a silent systematic-bias risk).

---

## 2. Actuator Modeling

### 2.1 Current: ImplicitActuatorCfg

```python
actuators={
    "arm": ImplicitActuatorCfg(
        joint_names_expr=["joint.*"],
        stiffness=100.0,   # Asset default (DR: abs range [40,120], hard [30,150])
        damping=3.0,       # Asset default (DR: abs range [0.5,5.0], hard [0.3,7.0])
    ),
},
```

PhysX computes continuous PD internally. Commands are applied immediately with no delay.

| Environment | Kp (DR-off) | Kd (DR-off) | DR Range |
|:---|:---|:---|:---|
| Base RL (v0, Base-v0) | 100.0 | 3.0 | Kp [40,120] (hard [30,150]), Kd [0.5,5.0] (hard [0.3,7.0]) |
| TDC (TDC-v0) | 200.0 | 10.0 | +-20% ([160,240], [8,12]) |

Note: DR samples Kp/Kd by **uniform sampling of a fixed absolute range** and overwrites the joint gain
(`randomize_joint_gains`, `mdp/events.py:457-469`, `dr.get(cfg.joint_stiffness_range)`) -- it is not a
+-percentage scaled around the nominal 100.0/3.0. Those nominal values are only what is used when DR is
disabled, not a preserved center. (This applies to the Base RL row above; the TDC row's ranges are
unverified this pass and left as previously documented.)

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
| `Isaac-FullDOF-TRPO-v0` (train) | 100 | 3 | 0 | abs range [40,120]/[0.5,5.0] (hard [30,150]/[0.3,7.0]) |
| `Isaac-FullDOF-TDC-v0` | 200 | 10 | 0 | +-20% |

---

### 2.4 Thruster Channel Ordering (sim TAM <-> firmware ESC)

The sim thruster allocation matrix (TAM) column order MUST match the physical
robot firmware's ESC channel order. In `envs/main`/`envs/full_dof` the thruster is
NOT a USD prim -- it is an analytical model: `ThrusterModel.compute_wrench()`
applies `einsum("ij,nj->ni", TAM, thrust)` to turn a 6D per-thruster command into
a body wrench (`Fx..Mz`) injected as an external force. Column `j` of the TAM is the
ONLY thing that defines what physical direction sim thruster slot `j` produces, so
matching the robot is purely a TAM column-order question -- no USD edit is involved.

The robot firmware (agent-jetson `pid.cpp`) wires `m0,m3` = vertical (heave/depth,
`PID_control_depth`) and `m1,m2,m4,m5` = horizontal (`PID_control_yaw`). The sim
originally had heave on columns `T4,T5`. The fix (2026-07-03, main `238932c`)
reorders the TAM columns to firmware order via a single named constant:

```python
# config.py (identical in envs/main and envs/full_dof)
_ESC_CHANNEL_ORDER = (4, 0, 1, 5, 2, 3)  # new column j = base column ORDER[j]
allocation_matrix = _reorder_columns(_BASE_ALLOCATION_MATRIX, _ESC_CHANNEL_ORDER)
```

- Reorder columns in sim (canonical) rather than keeping a permutation adapter in
  the deploy mixer -- an adapter makes a "temporary" mapping permanent (a hidden
  sim-real seam). After reorder + retrain, sim slot order == firmware ESC order and
  the deploy mixer permutation becomes identity.
- Column permutation is physics-invariant (singular values / achievable-wrench space
  unchanged; `new = old @ P`). It only relabels slots, so there is no "regressed ->
  revert" path -- it is not an A/B experiment.
- The vertical pair (`m0<-T4`, `m3<-T5`) is CONFIRMED. The horizontal-4 individual
  mapping (`m1<-T0, m2<-T1, m4<-T2, m5<-T3`) is PROVISIONAL, pending B1 watertank
  measurement -- to update it, edit ONLY the `_ESC_CHANNEL_ORDER` tuple.
- Old checkpoints were trained on the old column order -> DO NOT load them under the
  new TAM. Retrain from scratch (fold in with other confirmed pre-retrain fixes).

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

- Dynamixel XW540-T260 (ALBC arm joints)
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

Measured on the real joint driver (`agent-jetson` repo, `joint_angle_command.cpp` + `dynamixel_config.h`): the driver
actively writes Position P/I/D gain registers 84/82/80 with P=800, I=1, D=40, and also sets the Profile Velocity
register. These are raw integer register values (model-specific PWM scaling), not SI units, so they cannot be
substituted directly for the sim `ImplicitActuatorCfg` Kp/Kd. The nonzero I gain also means the real controller has
a structurally different form from the sim's continuous PhysX PD (no integral term).

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
- [ ] Thruster channel order: confirm sim TAM `_ESC_CHANNEL_ORDER` matches the
      firmware ESC wiring; deploy mixer permutation should be identity (see 2.4).
      After B1 watertank, confirm the horizontal-4 mapping and update the tuple.

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
**Updated**: 2026-07-03
