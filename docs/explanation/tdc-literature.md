# Time Delay Control (TDC) - Literature Survey

> **Status**: 2026-02-11 | Standalone theory document
>
> TDC theory and literature survey. For the concrete implementation for this system, see [tdc-control-law.md](tdc-control-law.md); for the tuning process, see [debug-history.md](../reference/debug-history.md).

---

## 1. Origins

TDC was independently proposed by Youcef-Toumi & Ito (1990) and Hsia & Gao (1990).

**Core idea**: Even without knowing the system dynamics, the unknown dynamics can be estimated using the control input (torque) and state (acceleration) of the immediately preceding time step. This mechanism is called **Time Delay Estimation (TDE)**.

### Key References

| Year | Authors | Contribution |
|:-----|:--------|:-------------|
| 1990 | Youcef-Toumi & Ito | Original TDC for systems with unknown dynamics |
| 1990 | Hsia & Gao | Independent TDC proposal for robot manipulators |
| 2013 | Jin, Lee, Chang | TDC + Nonlinear Damping + Terminal Sliding Mode |
| 2017 | Cho, Jin, Chang, Lee | Inclusive and Enhanced TDC (IETDC) |
| 2019 | Lee, Chang | Stable Gain Adaptation for TDC |
| 2020 | Chen et al. | Velocity-Free Adaptive TDC |
| 2024 | Taefi et al. | Model-free Adaptive-Robust TDC |

---

## 2. Mathematical Formulation

### Step 1: System Dynamics

General n-DOF robot manipulator dynamics:

$$M(q)\ddot{q} + C(q, \dot{q})\dot{q} + g(q) + f(\dot{q}) + d(t) = \tau$$

Where:
- $M(q)$: Inertia matrix ($n \times n$, positive definite)
- $C(q, \dot{q})\dot{q}$: Coriolis and centrifugal forces
- $g(q)$: Gravity
- $f(\dot{q})$: Friction
- $d(t)$: External disturbances
- $\tau$: Control input (torque)

### Step 2: Dynamics Reformulation with M-bar

Introduce an arbitrary **constant diagonal matrix** $\bar{M}$:

$$\bar{M} \ddot{q} + N(q, \dot{q}, \ddot{q}, t) = \tau$$

Where $N$ is the **lumped uncertainty** (everything unknown):

$$N(q, \dot{q}, \ddot{q}, t) = [M(q) - \bar{M}] \ddot{q} + C(q, \dot{q})\dot{q} + g(q) + f(\dot{q}) + d(t)$$

### Step 3: Time Delay Estimation (TDE)

$N$ is unknown, but assuming **N changes negligibly over one sampling period $L$**:

$$\hat{N}(t) \approx N(t - L) = \tau(t - L) - \bar{M} \ddot{q}(t - L)$$

The crux of TDE: the current unknown dynamics can be estimated using only the past torque $\tau(t-L)$ and past acceleration $\ddot{q}(t-L)$.

### Step 4: TDC Control Law

$$\tau(t) = \bar{M} \ddot{q}_{ref}(t) + \hat{N}(t) = \bar{M} \ddot{q}_{ref}(t) + \tau(t - L) - \bar{M} \ddot{q}(t - L)$$

### Step 5: Desired Error Dynamics

For tracking error $e = q_d - q$:

$$\ddot{q}_{ref} = \ddot{q}_d + K_d \dot{e} + K_p e$$

Where:
- $K_d$: Derivative gain matrix (diagonal)
- $K_p$: Proportional gain matrix (diagonal)
- $\ddot{q}_d$: Desired trajectory acceleration

Error dynamics in the ideal case (zero TDE error):

$$\ddot{e} + K_d \dot{e} + K_p e = 0$$

Standard 2nd-order linear damped system. Gain selection:
- Natural frequency: $\omega_n = \sqrt{K_p}$
- Damping ratio: $\zeta = K_d / (2 \omega_n)$

### Complete TDC Block Diagram

```
                   +--------+
  q_d, q_dot_d --> | Desired |
  q_ddot_d ------> | Error   |--> q_ddot_ref --+
  q, q_dot ------> | Dynamics|                 |
                   +--------+                  |
                                               v
                              +----------------------------------+
                              |  tau = M_bar * q_ddot_ref        |
                              |      + tau(t-L)                  |
                              |      - M_bar * q_ddot(t-L)       |
                              +----------------------------------+
                                               |
                                               v
                                           [ Plant ]
                                               |
                                     q, q_dot, q_ddot
```

---

## 3. M-bar Selection

$\bar{M}$ is the most important design parameter in TDC.

### Stability Condition

$$\| I - \bar{M}^{-1} M(q) \| < 1 \quad \text{(spectral norm)}$$

It must hold over the entire workspace.

### Practical Guidelines

| Guideline | Description |
|:----------|:------------|
| Diagonal matrix | $\bar{M} = \text{diag}(m_1, m_2, \ldots)$ for simplicity |
| Range | Typically 50% ~ 150% of true inertia diagonal elements |
| Too small | TDE error amplified, risk of instability |
| Too large | Sluggish response, poor control performance |
| Nominal inertia | $\bar{M} \approx M(q_0)$ at a representative configuration |

### Effect on Closed-Loop

- $\bar{M}$ acts as a **bandwidth limiter**: a large $\bar{M}$ lowers sensitivity but also reduces responsiveness.
- The $\bar{M}^{-1} M(q)$ ratio determines the degree of dynamics cancellation by TDE. If $\bar{M} = M(q)$, cancellation is perfect (but then the model is already known).

---

## 4. TDE Error Analysis

In practice $N(t) \neq N(t-L)$, so a TDE error $\epsilon$ exists:

$$\epsilon(t) = N(t) - N(t-L)$$

### Error Characteristics

| Factor | Effect on TDE Error |
|:-------|:--------------------|
| Smaller $L$ (sampling period) | Smaller error |
| Faster-changing dynamics | Larger error |
| Higher accelerations | Larger error ($N$ depends on $\ddot{q}$) |

### Stability Under TDE Error

Closed-loop error dynamics with TDE error:

$$\ddot{e} + K_d \dot{e} + K_p e = \bar{M}^{-1} \epsilon(t)$$

**Ultimate boundedness** (Lyapunov-based):
- The tracking error is bounded but not asymptotically zero.
- The bound is proportional to $\| \bar{M}^{-1} \epsilon \|$.

### Mitigation Strategies

1. **Minimize L**: use as fast a sampling rate as possible.
2. **Sliding mode compensation**: add a switching term to compensate for the TDE error.
3. **Adaptive $\bar{M}$**: adjust $\bar{M}$ online to reduce $\| I - \bar{M}^{-1} M(q) \|$.
4. **Disturbance observer**: add an auxiliary observer to estimate the TDE error.

---

## 5. Variants

### 5.1 Standard TDC (Youcef-Toumi, 1990)

$$\tau = \bar{M}(\ddot{q}_d + K_d \dot{e} + K_p e) + \tau(t-L) - \bar{M} \ddot{q}(t-L)$$

Simple and effective, but the TDE error is not compensated.

### 5.2 TDC + Sliding Mode

Add a switching term to handle the TDE error:

$$\tau = \bar{M} \ddot{q}_{ref} + \hat{N} + \bar{M} K_s \text{sign}(s)$$

Here $s$ is the sliding surface (e.g., $s = \dot{e} + \lambda e$).
It reduces the tracking error bound but can introduce chattering.

### 5.3 Enhanced TDC (IETDC, Cho et al. 2017)

Three components:
1. TDE (standard)
2. Nonlinear desired error dynamics (DED)
3. TDE error correction via nonlinear sliding surface

Improves robustness without chattering.

### 5.4 Adaptive TDC

- **Adaptive $\bar{M}$**: online tuning of $\bar{M}$ based on a Nussbaum function or gradient.
- **Adaptive gains**: adjust $K_p$, $K_d$ based on tracking performance.

### 5.5 TDC + Disturbance Observer

Estimate and compensate for the TDE error $\epsilon(t)$ with an auxiliary observer. Provides a tighter tracking bound.

---

## 6. Underwater Vehicle Applications

TDC is particularly well-suited to underwater robots:

1. **Complex hydrodynamics**: Added mass, nonlinear damping, and Coriolis force are difficult to model precisely. TDC bypasses this requirement.
2. **Environmental disturbances**: Ocean currents and waves are naturally handled as part of the lumped uncertainty $N$.
3. **Parameter variation**: Buoyancy and added mass change with depth, payload, and attitude. TDC adapts implicitly through TDE.

### Hero Agent ALBC Application

The ALBC (Arm-Linked Buoyancy Control) arm of Hero Agent applies the theory of this document to roll/pitch attitude control. Key features:

- A 2-DOF planar arm adjusts the buoy's position to generate restoring torque
- An anti-diagonal Lambda matrix converts roll/pitch into coupled torque
- TDE compensates for hydrodynamic coupling, payload variation, and buoyancy uncertainty
- The RL encoder estimates $\bar{M}$ online, realizing the Adaptive TDC of Section 5.4

For implementation details, see [tdc-control-law.md](tdc-control-law.md); for the tuning process, see [debug-history.md](../reference/debug-history.md).

### Relevant Work

- **Nonlinear robust control of UVMS based on TDE** (IEEE ICRA 2017):
  Applied to the coupled dynamics of an underwater vehicle-manipulator system.
- **Robust trajectory control of underwater vehicles using TDC** (Ocean Engineering 2006):
  Demonstrated TDC in 6-DOF trajectory tracking of an AUV.
- **Chattering-suppression SMC with TDE for underwater manipulator** (JMSE 2023):
  Combined TDE with continuous sliding mode to achieve smooth control.

---

## 7. Practical Design Guidelines

### Parameter Selection Summary

| Parameter | Guideline | Typical Range |
|:----------|:----------|:--------------|
| $L$ (time delay) | = control loop period, as small as possible | 1 ~ 10 ms |
| $\bar{M}$ | Diagonal, ~50-150% of true inertia | System-dependent |
| $K_p$ | $\omega_n^2$ for desired natural frequency | 10 ~ 1000 |
| $K_d$ | $2 \zeta \omega_n$ for desired damping | 1 ~ 100 |
| $\zeta$ | Damping ratio | 0.7 ~ 1.0 (critically damped) |

### Acceleration Measurement

The main practical challenge of TDE: $\ddot{q}(t-L)$ must be obtained.

| Method | Pros | Cons |
|:-------|:-----|:-----|
| Numerical differentiation | Simple | Noisy, amplifies sensor noise |
| Low-pass filtered derivative | Reduces noise | Introduces phase lag |
| Observer (e.g., Kalman) | Optimal estimation | More complex |
| IMU (for attitude systems) | Direct measurement | Sensor cost, drift |

### Digital Implementation

```python
# At each control step k (period = L):
q_ddot_prev = (q_dot[k-1] - q_dot[k-2]) / L     # or from observer
tau_prev     = tau[k-1]                             # stored from last step

N_hat = tau_prev - M_bar * q_ddot_prev              # TDE

e     = q_d[k] - q[k]
e_dot = q_dot_d[k] - q_dot[k]
q_ddot_ref = q_ddot_d[k] + Kd * e_dot + Kp * e     # desired error dynamics

tau[k] = M_bar * q_ddot_ref + N_hat                 # TDC control law
```

---

## 8. Key Takeaways for Implementation

1. **Model-free**: dynamics identification is unnecessary. Only $\bar{M}$ (a rough inertia estimate) is needed.
2. **Three design parameters**: $\bar{M}$, $K_p/K_d$, $L$.
3. **Acceleration estimation** is the main practical challenge. In simulation it can be obtained trivially from the physics engine.
4. **Standard TDC is sufficient** as a starting point. If the TDE error causes problems, a sliding mode or adaptive extension can be added.
5. **Stability is guaranteed** as long as $\| I - \bar{M}^{-1} M(q) \| < 1$ and $L$ is sufficiently small.

---

## References

- Youcef-Toumi, K., & Ito, O. (1990). A Time Delay Controller for Systems with Unknown Dynamics. ASME J. Dynamic Systems, Measurement, and Control.
- Hsia, T.C., & Gao, L.S. (1990). Robot Manipulator Control Using Decentralized Linear Controller and Nonlinear Disturbance Observer. IEEE ICRA.
- Cho, G.R., Jin, M., Chang, P.H., & Lee, J. (2017). Robust Control of Robot Manipulators Using Inclusive and Enhanced Time Delay Control. IEEE/ASME Transactions on Mechatronics.
- Jin, M., Lee, J., & Chang, P.H. (2013). Stability Guaranteed Time-Delay Control Using Nonlinear Damping and Terminal Sliding Mode. IEEE Transactions on Industrial Electronics.
- Lee, J., & Chang, P.H. (2019). Stable Gain Adaptation for Time-Delay Control. IFAC-PapersOnLine.
- Chen, Z., et al. (2020). Velocity-Free Adaptive Time Delay Control of Robotic System. Mathematical Problems in Engineering.

---

## Related Documents

- [tdc-control-law.md](tdc-control-law.md): Derivation and implementation of the TDC control law for Hero Agent ALBC
- [debug-history.md](../reference/debug-history.md): Full record of the TDC tuning process
- [dynamics.md](dynamics.md): ALBC dynamics analysis and added mass coupling
