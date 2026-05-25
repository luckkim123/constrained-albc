# ALBC Dynamics Analysis

> 2026-02-11 | Consolidated from research notes 01, 02, 03

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [ALBC Dynamics Model Issues](#2-albc-dynamics-model-issues)
3. [Added Mass Coupling Derivation](#3-added-mass-coupling-derivation)
4. [Inertia Variation Analysis and TDC Stability](#4-inertia-variation-analysis-and-tdc-stability)
5. [Proposed Solution: RL-based Adaptive TDC](#5-proposed-solution-rl-based-adaptive-tdc)

---

## 1. Problem Statement

### TDC: Model-Based Controller

TDC (Time Delay Control) is often called "model-free", but it is in fact a model-based controller.
The design matrix $\bar{M}$ requires a rough estimate of the actual inertia $M(q)$.
The real meaning of "model-free" here is that precise model identification is unnecessary (50% error is tolerated),
not that a model is unnecessary at all.

**Stability condition**:

$$\|I - \bar{M}^{-1}M(q)\| < 1$$

This condition is satisfied when $\bar{M}$ lies within roughly 50%-200% of the actual $M(q)$.

### Why Adaptive $\bar{M}$ is Necessary

The ALBC dynamics model (Eq. 3) considers only the mini-ROV:

$$M\dot{\nu} + C(\nu)\nu + D(\nu)\nu + g(\eta) = \tau_{th} + b(\Gamma)$$

In this model, $M$ is treated as a constant matrix independent of the joint angles $\Gamma$.
In reality, however, the inertia matrix changes significantly due to two causes:

**Cause 1: Position change of the buoyancy element**

- The buoyancy element at the end of the 2-DoF robot arm has a large volume and generates substantial added mass underwater.
- When the buoyancy element position changes with $\Gamma$, the mass distribution changes, and therefore it becomes $M(\Gamma)$.
- As shown in [Section 4](#4-inertia-variation-analysis-and-tdc-stability) of this document,
  the roll inertia alone changes by about 200% (3x).

**Cause 2: Unknown object grasping**

- When grasping an object, changes occur such as inertia $M \to M + M_{obj}$, center of gravity (CoG) shift, and center of buoyancy (CoB) change.
- Directly measuring $m_{obj}$, $I_{obj}$, and CoM position of an unknown object is impractical.

Both causes lead to a violation of the TDC stability condition with a fixed $\bar{M}$.
Therefore, a mechanism to adapt $\bar{M}$ in real time is essential.

---

## 2. ALBC Dynamics Model Issues

The dynamics modeling in the existing ALBC paper has four major problems.

### Issue 1: Buoyancy Element Dynamics Omitted

In the current model, $M$ is constant, and the buoyancy term $b(\Gamma)$ considers only the position of the buoyancy element.
The form that should be corrected:

$$M(\Gamma)\dot{\nu} + C(\nu, \Gamma, \dot{\Gamma})\nu + D(\nu)\nu + g(\eta) = \tau_{th} + b(\Gamma)$$

Omitted dynamics items:

| Omitted item | Description |
|:---|:---|
| $M(\Gamma)$ | $\Gamma$ dependence of the inertia matrix (mass distribution change due to buoyancy element position) |
| $\dot{M}(\Gamma)\nu$ | Coriolis matrix contribution due to time-varying inertia |
| Coriolis/Centripetal | Additional Coriolis terms due to buoyancy element rotational motion |
| Added Mass | Hydrodynamic added mass effect due to the large volume of the buoyancy element |

Component-wise, Link 1/2 have small mass and volume and can be neglected, but
the buoyancy element cannot be neglected because, despite its small mass, its volume is large.

### Issue 2: Free-Floating Dynamics Not Reflected

The current model implicitly assumes the mini-ROV as a fixed base.
Underwater, however, it is a free-floating system with no fixed point (ground).

$$L_{total} = L_{body} + L_{ALBC} = \text{constant (when no external torque)}$$

When the buoyancy element moves, the main body rotates as a reaction due to conservation of angular momentum.
This is the same phenomenon as a space robot's base rotating in the opposite direction when it swings its arm.

Correct dynamics of a free-floating system:

$$\begin{bmatrix} M_{bb} & M_{bm} \\ M_{mb} & M_{mm} \end{bmatrix} \begin{bmatrix} \dot{\nu} \\ \ddot{\Gamma} \end{bmatrix} + \begin{bmatrix} C_b \\ C_m \end{bmatrix} = \begin{bmatrix} \tau_{th} + b(\Gamma) \\ \tau_{joint} \end{bmatrix}$$

Here, $M_{bm}$ and $M_{mb}$ are the Base-Manipulator coupling inertias, and
the ALBC acceleration $\ddot{\Gamma}$ affects the main body acceleration $\dot{\nu}$.
The current model does not have this coupling term.

### Issue 3: Yaw Dynamics Omitted

The existing model presents only Roll/Pitch dynamics and has no Yaw dynamics.
When the buoyancy element position is asymmetric, a yaw moment can occur, and
ignoring yaw coupling in 6-DoF control becomes a problem.

### Issue 4: Object Grasping Dynamics Not Modeled

Changes that occur when grasping an object:

| Change item | Content | Problem |
|:---|:---|:---|
| Inertia matrix | $M \to M + M_{obj}$ | Not measurable for an unknown object |
| Center of gravity (CoG) | $r_G \to r'_G = \frac{m \cdot r_G + m_{obj} \cdot r_{obj}}{m + m_{obj}}$ | Directly affects the restoring force $g(\eta)$ |
| Center of buoyancy (CoB) | $r_B \to r'_B$ | CoG-CoB relationship change |
| Coriolis term | $C(\nu) \to C'(\nu)$ | Needs correction as the inertia matrix changes |

In the ALBC experimental results as well, steady-state error was observed for 200g and 400g objects,
and position/orientation divergence was observed for the 600g object.

### Summary

| Issue | Current model | Required model |
|:---|:---|:---|
| 1. Buoyancy element dynamics | Position only, $M$ constant | Includes $M(\Gamma)$, Coriolis, added mass |
| 2. Free-Floating | Fixed base assumption | Reflects Base-Manipulator coupling |
| 3. Yaw dynamics | None | Full Roll/Pitch/Yaw |
| 4. Object grasping | Not considered | Reflects $M_{obj}$, CoG, CoB changes |

---

## 3. Added Mass Coupling Derivation

This is the derivation of a dynamics model that neglects the physical mass of the buoyancy element and considers only Added Mass.

> **Note**: This derivation assumes $m_{bu} \approx 0$ (massless buoy), but
> the actual URDF buoy body mass is about 0.93 kg. The code implementation (`compute_M_bb`)
> uses `m_{total} = m_{body} + m_A` to include the buoy rigid body mass.

### 3.1 Notation

| Symbol | Definition | Size |
|:---|:---|:---|
| $\eta$ | Earth-fixed position/attitude | $\mathbb{R}^6$ |
| $\nu$ | Body-fixed velocity | $\mathbb{R}^6$ |
| $\Gamma = [\gamma_1, \gamma_2]^T$ | Joint angles | $\mathbb{R}^2$ |
| $\zeta = [\nu^T, \dot{\Gamma}^T]^T$ | Velocity coordinates | $\mathbb{R}^8$ |

### 3.2 Physical Motivation and Added Mass Estimation

Characteristics of the buoyancy element:

| Property | Value | Physical meaning |
|:---|:---|:---|
| Physical mass $m_{bu}$ | $\approx 0$ | Lightweight material (foam, plastic) |
| Volume $V_{bu}$ | Large | Needed to generate buoyancy |
| Added mass $m_A$ | Large | Virtual mass due to fluid displacement |

When the buoyancy element accelerates underwater, the surrounding fluid accelerates with it, so the inertia increases as if there were an additional mass.

$$F = (m + m_A)\dot{v}$$

**Numerical estimation of the ALBC buoyancy element**:

- Buoyancy $F_{bu} = 1.835$ kgf = 18.0 N
- $V_{bu} = F_{bu} / (\rho g) \approx 0.00179$ m$^3$
- Added mass (cylinder assumption, $C_m \approx 1.0$): $m_A \approx 1.0 \times 1025 \times 0.00179 \approx 1.83$ kg

Even with zero physical mass, the added mass is about 1.83 kg.

### 3.3 Buoyancy Element Kinematics

Position of the buoyancy element in the body frame (Forward Kinematics):

$$P_{EE}(\Gamma) = \begin{bmatrix} l_1\cos\gamma_1 + l_2\cos(\gamma_1+\gamma_2) \\ l_1\sin\gamma_1 + l_2\sin(\gamma_1+\gamma_2) \\ h \end{bmatrix}$$

| Parameter | Value | Description |
|:---|:---|:---|
| $l_1, l_2$ | 0.233 m | Link lengths |
| $h$ | 0.230 m | Height from CoG to the ALBC plane (constant) |

Jacobian:

$$\dot{P}_{EE} = J_{bu}(\Gamma)\dot{\Gamma}, \quad J_{bu} = \frac{\partial P_{EE}}{\partial \Gamma} \in \mathbb{R}^{3 \times 2}$$

### 3.4 Buoyancy Element Velocity

Absolute velocity of the buoyancy element in the body frame:

$$v^B_{bu} = \nu_1 + \nu_2 \times P_{EE} + J_{bu}\dot{\Gamma}$$

Expressing the cross product with the skew-symmetric matrix $S(\cdot)$:

$$v^B_{bu} = \nu_1 - S(P_{EE})\nu_2 + J_{bu}\dot{\Gamma} = H_{bu}\nu + J_{bu}\dot{\Gamma}$$

where:

$$H_{bu} = \begin{bmatrix} I_3 & -S(P_{EE}) \end{bmatrix} \in \mathbb{R}^{3 \times 6}$$

### 3.5 Added Mass Kinetic Energy

Total kinetic energy:

$$T = T_{ROV} + T_A = \frac{1}{2}\nu^T M_{ROV}\nu + \frac{1}{2}m_A(v^B_{bu})^T v^B_{bu}$$

Expanding $T_A$:

$$T_A = \frac{1}{2}m_A\nu^T H_{bu}^T H_{bu}\nu + m_A\nu^T H_{bu}^T J_{bu}\dot{\Gamma} + \frac{1}{2}m_A\dot{\Gamma}^T J_{bu}^T J_{bu}\dot{\Gamma}$$

Computing $H_{bu}^T H_{bu}$ (using the $S^T = -S$ property):

$$H_{bu}^T H_{bu} = \begin{bmatrix} I_3 & -S(P_{EE}) \\ S(P_{EE}) & S(P_{EE})^T S(P_{EE}) \end{bmatrix}$$

### 3.6 Skew-Symmetric Matrix Identity

Key identity needed for the derivation (proved via the Levi-Civita symbol):

$$S(r)^T S(r) = \|r\|^2 I_3 - rr^T$$

Applying it to $P_{EE} = [x_{bu}, y_{bu}, h]^T$:

$$S(P_{EE})^T S(P_{EE}) = \begin{bmatrix} y_{bu}^2 + h^2 & -x_{bu}y_{bu} & -x_{bu}h \\ -x_{bu}y_{bu} & x_{bu}^2 + h^2 & -y_{bu}h \\ -x_{bu}h & -y_{bu}h & x_{bu}^2 + y_{bu}^2 \end{bmatrix}$$

Physical interpretation:
- Diagonal components: Parallel axis theorem -- when the added mass $m_A$ is at a distance $d$ from the rotation axis, $\Delta I = m_A d^2$
- Off-diagonal components: Products of inertia -- occur when the added mass is in an asymmetric position

### 3.7 Inertia Matrix Assembly

Organizing the total kinetic energy in the velocity coordinates $\zeta = [\nu^T, \dot{\Gamma}^T]^T$:

$$T = \frac{1}{2}\zeta^T M(\Gamma)\zeta$$

$$M(\Gamma) = \begin{bmatrix} M_{bb}(\Gamma) & M_{bm}(\Gamma) \\ M_{mb}(\Gamma) & M_{mm}(\Gamma) \end{bmatrix}$$

**Body Inertia** $M_{bb}(\Gamma)$:

$$M_{bb}(\Gamma) = M_{ROV} + m_A\begin{bmatrix} I_3 & -S(P_{EE}) \\ S(P_{EE}) & S(P_{EE})^T S(P_{EE}) \end{bmatrix}$$

If the mini-ROV is diagonal ($M_{12} = M_{21} = 0$):

$$M_{bb}(\Gamma) = \begin{bmatrix} (m_{ROV} + m_A)I_3 & -m_A S(P_{EE}) \\ m_A S(P_{EE}) & I_{ROV} + m_A S(P_{EE})^T S(P_{EE}) \end{bmatrix}$$

**Body-Manipulator Coupling** $M_{bm}(\Gamma)$:

$$M_{bm}(\Gamma) = m_A H_{bu}^T J_{bu} = m_A\begin{bmatrix} J_{bu} \\ S(P_{EE})J_{bu} \end{bmatrix} \in \mathbb{R}^{6 \times 2}$$

**Manipulator Inertia** $M_{mm}(\Gamma)$:

$$M_{mm}(\Gamma) = m_A J_{bu}^T J_{bu} \in \mathbb{R}^{2 \times 2}$$

### 3.8 Rotation Inertia Components

Rotation inertia submatrix:

$$I_{rot}(\Gamma) = I_{ROV} + m_A S(P_{EE})^T S(P_{EE})$$

Diagonal components:

$$I_p(\Gamma) = I_{p,ROV} + m_A(y_{bu}^2 + h^2) \quad \text{(Roll)}$$

$$I_q(\Gamma) = I_{q,ROV} + m_A(x_{bu}^2 + h^2) \quad \text{(Pitch)}$$

$$I_r(\Gamma) = I_{r,ROV} + m_A(x_{bu}^2 + y_{bu}^2) \quad \text{(Yaw)}$$

Off-diagonal components (Products of Inertia):

$$I_{pq} = -m_A x_{bu} y_{bu}, \quad I_{pr} = -m_A x_{bu} h, \quad I_{qr} = -m_A y_{bu} h$$

### 3.9 Equations of Motion

Deriving via the Lagrangian approach (Euler-Lagrange + Christoffel symbols):

$$M(\Gamma)\dot{\zeta} + C(\Gamma, \dot{\Gamma})\zeta + D(\zeta)\zeta + g(q) = \tau$$

Extracting the body dynamics (first row):

$$M_{bb}(\Gamma)\dot{\nu} + M_{bm}(\Gamma)\ddot{\Gamma} + C_b(\nu, \Gamma, \dot{\Gamma}) + D_b(\nu)\nu + g_b(\eta) = \tau_{th} + b(\Gamma)$$

Physical meaning of each term:
- $M_{bb}(\Gamma)\dot{\nu}$: Force required for body acceleration (includes added mass, $\Gamma$-dependent)
- $M_{bm}(\Gamma)\ddot{\Gamma}$: Reaction force exerted on the body by joint acceleration
- $C_b$: Coriolis/centrifugal force (includes additional terms due to joint motion)

Comparison with the existing ALBC model:

| Term | Existing model | Derived model (Added Mass) |
|:---|:---|:---|
| Inertia | $M$ (constant) | $M_{bb}(\Gamma) = M_{ROV} + m_A(\cdots)$ |
| Coupling | None | $M_{bm}(\Gamma)\ddot{\Gamma}$ |
| Coriolis | $C(\nu)$ | $C_b(\nu, \Gamma, \dot{\Gamma})$ |
| Key difference | Independent of $\Gamma$ | $\Gamma$ dependence due to added mass |

---

## 4. Inertia Variation Analysis and TDC Stability

### 4.1 Workspace and Inertia Bounds

Buoyancy element reach: $r_{max} = l_1 + l_2 = 0.466$ m

Since $y_{bu} \in [-r_{max}, +r_{max}]$, the bounds of the Roll inertia:

$$I_p^{min} = I_{p,ROV} + m_A h^2 \quad (y_{bu} = 0)$$

$$I_p^{max} = I_{p,ROV} + m_A(r_{max}^2 + h^2) \quad (|y_{bu}| = r_{max})$$

### 4.2 Numerical Analysis

Estimated parameters:

| Parameter | Value |
|:---|:---|
| $m_A$ | 1.83 kg |
| $r_{max}$ | 0.466 m |
| $h$ | 0.230 m |
| $I_{p,ROV}$ | $\approx 0.1$ kg$\cdot$m$^2$ |

Computation results:

$$I_p^{min} = 0.1 + 1.83 \times 0.230^2 = 0.197 \text{ kg}\cdot\text{m}^2$$

$$I_p^{max} = 0.1 + 1.83 \times (0.466^2 + 0.230^2) = 0.594 \text{ kg}\cdot\text{m}^2$$

Relative change:

$$\frac{I_p^{max} - I_p^{min}}{I_p^{min}} = \frac{0.397}{0.197} = 201\%$$

Even considering only added mass, the roll inertia changes by about 200% (3x).

### 4.3 TDC Stability Condition Violation

TDC stability condition: $\|I - \bar{M}^{-1}M(\Gamma)\| < 1$

This means $\bar{M}$ must lie within the 50%-200% range of the actual $M(\Gamma)$.

When fixing $\bar{M} = I_p^{min}$:

$$\bar{M}^{-1}M^{max} = \frac{I_p^{max}}{I_p^{min}} = \frac{0.594}{0.197} = 3.02$$

$$\|I - \bar{M}^{-1}M^{max}\| = |1 - 3.02| = 2.02 > 1$$

The stability condition is violated.
When object grasping is also taken into account, the range of inertia variation is even larger, so with a fixed $\bar{M}$
stable TDC operation is fundamentally impossible.

| Item | Value |
|:---|:---|
| Buoyancy element physical mass | $\approx 0$ (neglected) |
| Added mass $m_A$ | 1.83 kg |
| Roll inertia change | 201% (about 3x) |
| $I_p^{max} / I_p^{min}$ | 3.02 |
| TDC stability | Condition violated ($2.02 > 1$) |
| Conclusion | Adaptive $\bar{M}$ essential |

---

## 5. Proposed Solution: RL-based Adaptive TDC

### 5.1 Core Idea

It integrates the adaptivity of Model-Free RL with the structural stability of Model-Based Control.
Whereas prior work (RL-TDC 2022, AC-TDC 2021, etc.) focused on gain tuning,
the key distinction of this approach is to infer the current physical characteristics of the system from the proprioception history
and adapt $\bar{M}$.

```
Proprioception History (q, dq, a)  -->  Adaptation Module  -->  z_t (latent)
                                                                    |
                                                                    v
                                                            M_bar(z_t)  -->  TDC Controller
```

### 5.2 RMA/HORA 2-Phase Training (background only — deprecated approach)

> The two-phase Teacher/Student pipeline below is **deprecated** and not used by the
> current design (which uses a single-stage asymmetric encoder/critic, see
> [system-overview](system-overview.md)). Retained as conceptual background for the
> adaptive-`M` dynamics formulation; student distillation in the current repo
> (`student/` TCN/GRU) is a separate post-hoc step, not RMA Phase 2.

**Phase 1 (Teacher)**: Simulation with Privileged Information

- Access the ground truth physical quantities of the object (mass, inertia, CoM) in the simulator
- Compress the physical quantities into a latent vector $z_t$ with the Extrinsics Encoder
- Generate $\bar{M}(z_t)$ using $z_t$ and train the base policy

**Phase 2 (Student)**: Adaptation Module

- Estimate the latent vector $\hat{z}_t$ from the proprioception history alone
- Implicitly infer the physical quantities without ground truth
- Directly applicable in the real environment without additional training (zero-shot sim-to-real transfer)

```
[Phase 1 - Simulation]
Ground Truth (m, I, CoM) --> Extrinsics Encoder --> z_t --> M_bar(z_t) --> TDC

[Phase 2 - Simulation]
Proprioception History --> Adaptation Module --> z_hat_t  (approx z_t)

[Deployment - Real World]
Proprioception History --> Adaptation Module --> z_hat_t --> M_bar(z_hat_t) --> TDC
                           (No additional training)
```

### 5.3 Expected Benefits

- Train on diverse objects (mass, shape, CoM distribution) in the simulator
- Adaptively adjust $\bar{M}$ even for unknown objects in the real environment
- Minimize the sim-real gap through domain randomization
- Analyze the correspondence between the latent vector $z_t$ and the actual physical quantities (interpretability)

For the concrete equation derivation of the TDC control law, see [tdc-control-law.md](tdc-control-law.md).
For the overall system configuration (action/obs space, algorithm, network structure), see [system-overview.md](system-overview.md).

---

**Created**: 2026-02-11
**Updated**: 2026-02-11
**Status**: Consolidated reference -- derived from research notes 01 (Research Idea), 02 (ALBC Dynamics Issues), 03 (Added Mass Coupling)
