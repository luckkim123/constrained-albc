# TDC Control Law Derivation

> **Status**: 2026-02-11 | **Source**: `controllers/tdc.py`, `controllers/kinematics.py`
>
> Mathematical derivation and implementation extensions of the ALBC Roll/Pitch TDC (Time Delay Control) control law.
> For the theoretical background, see [tdc-literature.md](tdc-literature.md).

---

## Body Dynamics with Coupling

Body dynamics including added mass (6-DOF):

$$M_{bb}(\Gamma)\dot{\nu} + M_{bm}(\Gamma)\ddot{\Gamma} + C_b(\nu, \Gamma, \dot{\Gamma}) + D_b(\nu)\nu + g_b(\eta) = \tau_{th} + b(\Gamma)$$

| Term | Size | Description |
|:---|:---|:---|
| $M_{bb}(\Gamma)$ | $6 \times 6$ | Body inertia matrix ($\Gamma$-dependent) |
| $M_{bm}(\Gamma)$ | $6 \times 2$ | Body-Manipulator coupling |
| $C_b$ | $6 \times 1$ | Coriolis/centrifugal force |
| $D_b(\nu)\nu$ | $6 \times 1$ | Damping force |
| $g_b(\eta)$ | $6 \times 1$ | Restoring force |
| $\tau_{th}$ | $6 \times 1$ | Thruster input |
| $b(\Gamma)$ | $6 \times 1$ | Buoyancy moment |

For the dynamics derivation details, see [dynamics.md](dynamics.md).

---

## TDC Standard Form

### Lumped Nonlinear Term

Reformulating the body dynamics into the TDC standard form:

$$M_{bb}(\Gamma)\dot{\nu} + N = \tau_{th} + b(\Gamma)$$

where the **lumped nonlinear term** $N$:

$$N = M_{bm}(\Gamma)\ddot{\Gamma} + C_b(\nu, \Gamma, \dot{\Gamma}) + D_b(\nu)\nu + g_b(\eta)$$

| Term | Reason for Inclusion |
|:---|:---|
| $M_{bm}\ddot{\Gamma}$ | Body reaction due to joint acceleration -- acts like a disturbance |
| $C_b$ | Nonlinear Coriolis/centrifugal force |
| $D_b\nu$ | Velocity-dependent damping (linear + nonlinear) |
| $g_b$ | Attitude-dependent restoring force |

Rationale for including $M_{bm}\ddot{\Gamma}$ in $N$: since the ALBC joints are driven independently by position control, from the body controller's perspective $\ddot{\Gamma}$ is an external disturbance. Because the TDE automatically compensates for it via time delay estimation, there is no need to separately estimate $\bar{M}_{bm}$.

### What the TDE Handles

What the TDE term $\hat{N}$ implicitly estimates:

$$\hat{N} \approx \underbrace{(M_{bb} - \bar{M})\dot{\nu}}_{\text{model error}} + \underbrace{M_{bm}\ddot{\Gamma}}_{\text{coupling}} + \underbrace{C_b + D_b\nu + g_b}_{\text{nonlinear dynamics}}$$

**Key point**: the only thing to estimate explicitly in TDC is $\bar{M} \approx M_{bb}(\Gamma)$.

### Stability Condition

$$\|I - \bar{M}^{-1}M_{bb}(\Gamma)\| < 1$$

Since the roll inertia varies by about 200% depending on the workspace, a fixed $\bar{M}$ may violate the stability condition. This is why an adaptive $\bar{M}(\hat{z}_t)$ is needed.

---

## Roll/Pitch TDC Derivation

### Assumptions

- **Small-angle approximation**: $\phi, \theta \approx 0$ $\to$ $\dot{\phi} \approx p$, $\dot{\theta} \approx q$
- **$\Lambda^{-1}$ exists**: $\cos\theta \cos\phi \neq 0$ (always satisfied at small angles)
- **No thruster contribution**: thruster has no direct effect on Roll/Pitch $[\tau_{th}]_{\phi,\theta} = 0$
- **$T_b$ computable**: $F_{bu}$, $h$ are known design parameters

### Notation

| Symbol | Definition | Note |
|:---|:---|:---|
| $[\cdot]_{\phi,\theta}$ | Extract the 4th and 5th components of a 6x1 vector | Roll/Pitch part |
| $M$ | $[M_{bb}]_{\phi,\theta} \in \mathbb{R}^{2\times 2}$ | Roll/Pitch inertia submatrix |
| $\bar{M}$ | Design inertia matrix (constant) | TDC design parameter |
| $\nu$ | $[p, q]^T$ | Roll/Pitch angular velocity |
| $B_t$ | $M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b$ | $T_b$ **not included** |
| $H_t$ | $(M-\bar{M})\dot{\nu}_t+B_t$ | Uncertainty |
| $\Delta T_b$ | $T_{b,t-L} - T_{b,t}$ | Passive restoring change |

### Step 1-2: Roll/Pitch Extraction

Extract only the Roll/Pitch components from the 6-DOF body dynamics (all terms below are Roll/Pitch submatrices/vectors):

$$M\dot{\nu}+M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b=\Lambda \mathbf{p}_{EE}+T_b$$

where $\mathbf{p}_{EE} = [x_{EE}, y_{EE}]^T$.

**$\Lambda$ and $T_b$** (derived from the cross product $\mathbf{r} \times F_{body}$):

$$\Lambda_t = \begin{bmatrix} 0 & c_\theta c_\phi F_{bu} \\ -c_\theta c_\phi F_{bu} & 0 \end{bmatrix}, \quad T_b = \begin{bmatrix} -c_\theta s_\phi F_{bu} h \\ -s_\theta F_{bu} h \end{bmatrix}$$

When $\phi>0$ (positive roll), the restoring torque must be in the negative direction, so the sign of $T_b$ is negative. $\Lambda$ is also derived from the same cross product, which determines its sign.

| Term | Meaning | Treatment |
|:---|:---|:---|
| $\Lambda$ | Active control term | Control input |
| $T_b$ | Passive restoring term | **Explicit computation** (excluded from TDE) |

### Step 3-4: Uncertainty Definition

Define only the uncertain terms excluding $T_b$ as $B_t$:

$$B_t = M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b$$

Then: $M\dot{\nu}+B_t=\Lambda \mathbf{p}_{EE}+T_b$

Definition of the uncertainty $H_t$:

$$H_t = (M-\bar{M})\dot{\nu}_t+B_t$$

Reason for separating $T_b$ from $H_t$: $T_b$ can be computed exactly from the current attitude $(\phi, \theta)$ and the known constants $(F_{bu}, h)$. This reduces the TDE estimation burden and increases accuracy.

### Step 5-6: System Equation

Splitting as $M = \bar{M} + (M - \bar{M})$ and substituting $H_t$:

$$\Lambda_t \mathbf{p}_{EE,t}=\bar{M}\dot{\nu}_t+H_t-T_{b,t}$$

Rearranging for $H_t$:

$$H_t=\Lambda_t \mathbf{p}_{EE,t}-\bar{M}\dot{\nu}_t+T_{b,t}$$

### Step 7: Time Delay Estimation (TDE)

Key TDE assumption: over a sufficiently short time $L$, $H$ does not change much ($H_t \approx H_{t-L}$).

$$\hat{H}_t = H_{t-L}=\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+T_{b,t-L}$$

- $\Lambda_{t-L}$: computed from the attitude at time $t-L$
- $T_{b,t-L}$: computed from the attitude at time $t-L$

### Step 8: Desired Dynamics

Desired closed-loop dynamics (ALBC maintains horizontal, $\dot{\nu}_d = 0$):

$$\dot{\nu}^{ref} = K_d\dot{e} + K_p e$$

Under the small-angle approximation:

$$e = \begin{bmatrix} \phi_d - \phi \\ \theta_d - \theta \end{bmatrix}, \quad \dot{e} \approx \begin{bmatrix} -p \\ -q \end{bmatrix}$$

### Step 9: Final Control Law

Substituting $\dot{\nu}^{ref}$ into the system equation and applying the TDE:

$$\boxed{\mathbf{p}_{EE,t}=\Lambda^{-1}_t\left[\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+\bar{M}(K_d\dot{e}_t+K_pe_t)+\Delta T_b\right]}$$

where $\Delta T_b = T_{b,t-L} - T_{b,t}$.

Physical meaning of $\Delta T_b$: $\Delta T_b \approx -\dot{T}_b \cdot L$. When the stabilization goal ($\phi, \theta \to 0$) is achieved, the influence of the $\Delta T_b$ term naturally decreases.

---

## Implementation Extensions

Extensions from the derivation result to the actual implementation. Python implementation: `controllers/tdc.py`, `controllers/kinematics.py`.

### DLS Lambda Inverse

Step 9 of the derivation requires $\Lambda^{-1}_t$. $\Lambda$ is anti-diagonal:

$$\Lambda_t = \begin{bmatrix} 0 & l_f \\ -l_f & 0 \end{bmatrix}, \quad l_f = \cos\theta\cos\phi \cdot F_{bu}$$

Since the analytic inverse is proportional to $1/l_f$, when $\phi, \theta \to 90\degree$ and $l_f \to 0$, a singularity diverges.

**Applying DLS (Damped Least Squares)**:

$$\Lambda^{-1}_{DLS} = \begin{bmatrix} 0 & -d \\ d & 0 \end{bmatrix}, \quad d = \frac{l_f}{l_f^2 + \lambda_{dls}^2}$$

$\lambda_{dls} = 0.01$ (fixed damping parameter).

| $l_f$ State | $d$ Behavior | Effect |
|:---|:---|:---|
| $l_f \gg \lambda_{dls}$ (near vertical) | $d \approx 1/l_f$ | Same as the analytic inverse |
| $l_f \to 0$ (near horizontal) | $d \to 0$ | $\mathbf{p}_{EE} \to 0$ (graceful degradation) |

### DLS Inverse Kinematics

DLS is also applied to the IK that converts the $\mathbf{p}_{EE}$ output by the control law into joint angles $\Gamma$.

**Jacobian**:

$$J(\Gamma) = \begin{bmatrix} -l_1 s_1 - l_2 s_{12} & -l_2 s_{12} \\ l_1 c_1 + l_2 c_{12} & l_2 c_{12} \end{bmatrix}$$

**DLS pseudo-inverse** (Yoshikawa adaptive damping):

$$J^{\dagger}_{DLS} = J^T(JJ^T + \lambda^2 I)^{-1}$$

$$\lambda^2 = \lambda_{max}^2 \cdot \text{clamp}(1 - w/w_0, \min=0), \quad w = \det(JJ^T)^{1/(2m)}$$

| Parameter | Value | Description |
|:---|:---|:---|
| $\lambda_{max}$ | 0.15 | Maximum damping (at singularity) |
| $w_0$ | $\sqrt{l_1 \cdot l_2} = 0.233$ | Manipulability normalization reference |
| $w$ | $\det(JJ^T)^{1/(2m)}$ | Dimension-normalized manipulability |

At a singularity ($w \to 0$), $\lambda \to \lambda_{max}$, so the IK output naturally attenuates. The workspace clamp becomes unnecessary, and TDE saturation can also be removed.

The implementation uses `torch.linalg.solve` to be dimension-independent (extensible to higher-DOF).

### Angular Acceleration Filter

$\dot{\nu}$ (angular acceleration) is computed by finite difference, so it is noisy:

$$\dot{\nu}_t \approx \frac{\nu_t - \nu_{t-1}}{\Delta t}$$

Applying a **first-order LPF (EMA)**:

$$\dot{\nu}^{filt}_t = \alpha \cdot \dot{\nu}^{raw}_t + (1 - \alpha) \cdot \dot{\nu}^{filt}_{t-1}, \quad \alpha = 0.05$$

**Caution**: do not filter $\hat{H}$ or $\hat{U}$ (terms containing $T_b$) -- the DC component of $T_b$ would remain as a bias and induce steady-state error.

### Anti-Windup

The control law's $\mathbf{p}_{EE}$ goes through IK -> joint command -> rate limiter. When the rate limiter clips the joint command, the actual EE position and the controller's internal state become inconsistent.

**Solution**: synchronize every step with `update_ee_position(FK(rate_limited_joints))`. Since the controller computes the next step based on the "actually reached EE position", windup is prevented.

### TDE Saturation Removal

Consistent with the C++ reference implementation. Since DLS Lambda_inv + DLS IK handle singularities with natural attenuation, separate TDE magnitude clamping is unnecessary.

For the saturation-related trial and error during the tuning process, see [debug-history.md](../reference/debug-history.md).

---

## Summary

### Key Definitions

| Symbol | Definition | Note |
|:---|:---|:---|
| $B_t$ | $M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b$ | $T_b$ **not included** |
| $H_t$ | $(M-\bar{M})\dot{\nu}_t+B_t$ | Uncertainty (lumped) |
| $\Delta T_b$ | $T_{b,t-L} - T_{b,t}$ | Passive restoring change |

### System Equation

$$\Lambda_t \mathbf{p}_{EE,t}=\bar{M}\dot{\nu}_t+H_t-T_{b,t}$$

### Time Delay Estimation

$$\hat{H}_t=\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+T_{b,t-L}$$

### Final Control Law

$$\mathbf{p}_{EE,t}=\Lambda^{-1}_t\left[\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+\bar{M}(K_d\dot{e}_t+K_pe_t)+\Delta T_b\right]$$

### Design Decisions

| Item | Decision |
|:---|:---|
| $H_t$ unit | Force/moment (not acceleration) |
| $\Lambda$ | Time-varying -- depends on $\phi$, $\theta$ |
| $T_b$ | Explicit computation -- separated from TDE |
| $\bar{M}$ | Design constant -- extended to $\bar{M}(\hat{z}_t)$ when adaptation is needed |
| TDE saturation | Removed -- DLS handles singularities naturally |
| IK method | DLS Jacobian (Yoshikawa adaptive), no workspace clamp needed |
| $\dot{\nu}$ filter | EMA alpha=0.05 (not applied to $\hat{H}$/$\hat{U}$) |
| Anti-windup | FK(rate-limited) synchronization |

### Current Parameters (from `controllers/tdc.py`)

| Parameter | Value | Description |
|:---|:---|:---|
| `m_hat` | (0.15, 0.16) | Design inertia [roll, pitch] (kg-m^2) |
| `kp` | 40 | PD proportional gain |
| `kd` | 12 | PD derivative gain |
| `h` | 0.18 | CoG-to-ABPC vertical offset (m) |
| `dls_lambda_damping` | 0.01 | Lambda DLS damping |
| `ik_dls_lambda` | 0.15 | IK DLS maximum damping |
| `nu_dot_ema_alpha` | 0.05 | Angular acceleration filter coefficient |
| `max_joint_velocity` | 2.5 | Rate limiter (rad/s) |
| `base_position` | (0.002, 0.002) | EE base position (m) |
| TDC dt | 0.02 s (50 Hz) | `step_dt * control_decimation` |

---

**Created**: 2026-02-09
**Updated**: 2026-02-21 (Synced parameter table with TDCControllerCfg actual values.)
