# Time Delay Control (TDC) - Literature Survey

> **Status**: 2026-02-11 | Standalone theory document
>
> TDC 이론 및 문헌 조사. 이 시스템에 대한 구체적인 구현은 [tdc-control-law.md](tdc-control-law.md)를, 튜닝 과정은 [debug-history.md](../reference/debug-history.md)를 참조.

---

## 1. Origins

TDC was independently proposed by Youcef-Toumi & Ito (1990) and Hsia & Gao (1990).

**Core idea**: 시스템 동역학을 모르더라도, 직전 time step의 제어 입력(torque)과 상태(acceleration)를 이용하여 미지의 동역학을 추정할 수 있다. 이 메커니즘을 **Time Delay Estimation (TDE)** 이라 한다.

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

TDE의 핵심: 과거 torque $\tau(t-L)$와 과거 acceleration $\ddot{q}(t-L)$만으로 현재의 미지 동역학을 추정할 수 있다.

### Step 4: TDC Control Law

$$\tau(t) = \bar{M} \ddot{q}_{ref}(t) + \hat{N}(t) = \bar{M} \ddot{q}_{ref}(t) + \tau(t - L) - \bar{M} \ddot{q}(t - L)$$

### Step 5: Desired Error Dynamics

For tracking error $e = q_d - q$:

$$\ddot{q}_{ref} = \ddot{q}_d + K_d \dot{e} + K_p e$$

Where:
- $K_d$: Derivative gain matrix (diagonal)
- $K_p$: Proportional gain matrix (diagonal)
- $\ddot{q}_d$: Desired trajectory acceleration

Ideal case (zero TDE error)에서 error dynamics:

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

$\bar{M}$은 TDC에서 가장 중요한 설계 파라미터이다.

### Stability Condition

$$\| I - \bar{M}^{-1} M(q) \| < 1 \quad \text{(spectral norm)}$$

Workspace 전체에서 성립해야 한다.

### Practical Guidelines

| Guideline | Description |
|:----------|:------------|
| Diagonal matrix | $\bar{M} = \text{diag}(m_1, m_2, \ldots)$ for simplicity |
| Range | Typically 50% ~ 150% of true inertia diagonal elements |
| Too small | TDE error amplified, risk of instability |
| Too large | Sluggish response, poor control performance |
| Nominal inertia | $\bar{M} \approx M(q_0)$ at a representative configuration |

### Effect on Closed-Loop

- $\bar{M}$은 **bandwidth limiter** 역할: 큰 $\bar{M}$은 sensitivity를 낮추지만 responsiveness도 감소.
- $\bar{M}^{-1} M(q)$ 비율이 TDE의 동역학 상쇄 정도를 결정. $\bar{M} = M(q)$이면 완벽 상쇄 (하지만 그러면 이미 모델을 알고 있는 것).

---

## 4. TDE Error Analysis

실제로는 $N(t) \neq N(t-L)$이므로 TDE error $\epsilon$이 존재:

$$\epsilon(t) = N(t) - N(t-L)$$

### Error Characteristics

| Factor | Effect on TDE Error |
|:-------|:--------------------|
| Smaller $L$ (sampling period) | Smaller error |
| Faster-changing dynamics | Larger error |
| Higher accelerations | Larger error ($N$ depends on $\ddot{q}$) |

### Stability Under TDE Error

TDE error가 있는 closed-loop error dynamics:

$$\ddot{e} + K_d \dot{e} + K_p e = \bar{M}^{-1} \epsilon(t)$$

**Ultimate boundedness** (Lyapunov-based):
- Tracking error는 bounded이지만 asymptotically zero가 아니다.
- Bound는 $\| \bar{M}^{-1} \epsilon \|$에 비례.

### Mitigation Strategies

1. **Minimize L**: 가능한 한 빠른 sampling rate 사용.
2. **Sliding mode compensation**: TDE error 보상을 위한 switching term 추가.
3. **Adaptive $\bar{M}$**: $\| I - \bar{M}^{-1} M(q) \|$을 줄이도록 $\bar{M}$을 온라인 조정.
4. **Disturbance observer**: TDE error 추정을 위한 보조 observer 추가.

---

## 5. Variants

### 5.1 Standard TDC (Youcef-Toumi, 1990)

$$\tau = \bar{M}(\ddot{q}_d + K_d \dot{e} + K_p e) + \tau(t-L) - \bar{M} \ddot{q}(t-L)$$

단순하고 효과적이지만 TDE error가 보상되지 않는다.

### 5.2 TDC + Sliding Mode

TDE error 처리를 위한 switching term 추가:

$$\tau = \bar{M} \ddot{q}_{ref} + \hat{N} + \bar{M} K_s \text{sign}(s)$$

여기서 $s$는 sliding surface (e.g., $s = \dot{e} + \lambda e$).
Tracking error bound를 줄이지만 chattering이 발생할 수 있다.

### 5.3 Enhanced TDC (IETDC, Cho et al. 2017)

Three components:
1. TDE (standard)
2. Nonlinear desired error dynamics (DED)
3. TDE error correction via nonlinear sliding surface

Chattering 없이 robustness를 개선.

### 5.4 Adaptive TDC

- **Adaptive $\bar{M}$**: Nussbaum function 또는 gradient 기반 $\bar{M}$ 온라인 튜닝.
- **Adaptive gains**: Tracking performance 기반 $K_p$, $K_d$ 조정.

### 5.5 TDC + Disturbance Observer

보조 observer로 TDE error $\epsilon(t)$를 추정하여 보상. 더 tight한 tracking bound 제공.

---

## 6. Underwater Vehicle Applications

TDC는 수중 로봇에 특히 적합하다:

1. **Complex hydrodynamics**: Added mass, nonlinear damping, Coriolis force는 정밀 모델링이 어렵다. TDC는 이 요구를 우회한다.
2. **Environmental disturbances**: 해류와 파랑은 lumped uncertainty $N$의 일부로 자연스럽게 처리된다.
3. **Parameter variation**: 부력과 added mass는 깊이, 페이로드, 자세에 따라 변한다. TDC는 TDE를 통해 암묵적으로 적응한다.

### Hero Agent ALBC Application

Hero Agent의 ALBC (Arm-Linked Buoyancy Control) arm은 이 문서의 이론을 roll/pitch 자세 제어에 적용한다. 주요 특징:

- 2-DOF planar arm이 buoy의 위치를 조절하여 복원 토크를 생성
- Anti-diagonal Lambda 행렬이 roll/pitch를 coupled torque로 변환
- TDE가 hydrodynamic coupling, payload 변동, buoyancy 불확실성을 보상
- RL encoder가 $\bar{M}$을 온라인으로 추정하여 Section 5.4의 Adaptive TDC를 실현

구현 상세는 [tdc-control-law.md](tdc-control-law.md), 튜닝 과정은 [debug-history.md](../reference/debug-history.md) 참조.

### Relevant Work

- **Nonlinear robust control of UVMS based on TDE** (IEEE ICRA 2017):
  Underwater vehicle-manipulator system의 coupled dynamics에 적용.
- **Robust trajectory control of underwater vehicles using TDC** (Ocean Engineering 2006):
  AUV의 6-DOF trajectory tracking에서 TDC를 실증.
- **Chattering-suppression SMC with TDE for underwater manipulator** (JMSE 2023):
  TDE와 continuous sliding mode를 결합하여 smooth control 달성.

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

TDE의 주요 실용적 과제: $\ddot{q}(t-L)$을 얻어야 한다.

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

1. **Model-free**: 동역학 식별이 불필요. $\bar{M}$ (대략적 관성 추정)만 있으면 된다.
2. **Three design parameters**: $\bar{M}$, $K_p/K_d$, $L$.
3. **Acceleration estimation**이 주요 실용적 과제. 시뮬레이션에서는 물리 엔진에서 trivially 얻을 수 있다.
4. **Standard TDC is sufficient** as a starting point. TDE error가 문제를 일으키면 sliding mode나 adaptive extension을 추가할 수 있다.
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

- [tdc-control-law.md](tdc-control-law.md): Hero Agent ALBC의 TDC 제어 법칙 유도 및 구현
- [debug-history.md](../reference/debug-history.md): TDC 튜닝 과정 전체 기록
- [dynamics.md](dynamics.md): ALBC 동역학 분석 및 added mass coupling
