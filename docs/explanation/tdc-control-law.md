# TDC Control Law Derivation

> **Status**: 2026-02-11 | **Source**: `controllers/tdc.py`, `controllers/kinematics.py`
>
> ALBC Roll/Pitch TDC (Time Delay Control) 제어 법칙의 수학적 유도와 구현 확장 사항.
> 이론적 배경은 [tdc-literature.md](tdc-literature.md) 참조.

---

## Body Dynamics with Coupling

Added mass를 포함한 body dynamics (6-DOF):

$$M_{bb}(\Gamma)\dot{\nu} + M_{bm}(\Gamma)\ddot{\Gamma} + C_b(\nu, \Gamma, \dot{\Gamma}) + D_b(\nu)\nu + g_b(\eta) = \tau_{th} + b(\Gamma)$$

| Term | Size | Description |
|:---|:---|:---|
| $M_{bb}(\Gamma)$ | $6 \times 6$ | Body 관성 행렬 ($\Gamma$ 의존) |
| $M_{bm}(\Gamma)$ | $6 \times 2$ | Body-Manipulator 커플링 |
| $C_b$ | $6 \times 1$ | Coriolis/원심력 |
| $D_b(\nu)\nu$ | $6 \times 1$ | 감쇠력 |
| $g_b(\eta)$ | $6 \times 1$ | 복원력 |
| $\tau_{th}$ | $6 \times 1$ | 추력기 입력 |
| $b(\Gamma)$ | $6 \times 1$ | 부력 모멘트 |

동역학 유도 상세는 [dynamics.md](dynamics.md) 참조.

---

## TDC Standard Form

### Lumped Nonlinear Term

Body dynamics를 TDC 표준 형태로 재구성:

$$M_{bb}(\Gamma)\dot{\nu} + N = \tau_{th} + b(\Gamma)$$

여기서 **lumped nonlinear term** $N$:

$$N = M_{bm}(\Gamma)\ddot{\Gamma} + C_b(\nu, \Gamma, \dot{\Gamma}) + D_b(\nu)\nu + g_b(\eta)$$

| Term | Reason for Inclusion |
|:---|:---|
| $M_{bm}\ddot{\Gamma}$ | 관절 가속도에 의한 body 반작용 -- 외란처럼 작용 |
| $C_b$ | 비선형 Coriolis/원심력 |
| $D_b\nu$ | 속도 의존 감쇠 (선형 + 비선형) |
| $g_b$ | 자세 의존 복원력 |

$M_{bm}\ddot{\Gamma}$를 $N$에 포함시키는 근거: ALBC 관절은 위치 제어로 독립 구동되므로 body controller 입장에서 $\ddot{\Gamma}$는 외부 외란이다. TDE가 시간 지연 추정으로 자동 보상하므로 $\bar{M}_{bm}$을 별도 추정할 필요가 없다.

### TDE가 처리하는 내용

TDE term $\hat{N}$이 암묵적으로 추정하는 것:

$$\hat{N} \approx \underbrace{(M_{bb} - \bar{M})\dot{\nu}}_{\text{모델 오차}} + \underbrace{M_{bm}\ddot{\Gamma}}_{\text{커플링}} + \underbrace{C_b + D_b\nu + g_b}_{\text{비선형 동역학}}$$

**핵심**: TDC에서 명시적으로 추정할 것은 $\bar{M} \approx M_{bb}(\Gamma)$뿐이다.

### Stability Condition

$$\|I - \bar{M}^{-1}M_{bb}(\Gamma)\| < 1$$

Roll 관성이 workspace에 따라 약 200% 변동하므로 고정 $\bar{M}$은 안정성 조건 위배 가능. 이것이 적응적 $\bar{M}(\hat{z}_t)$가 필요한 이유이다.

---

## Roll/Pitch TDC Derivation

### Assumptions

- **소각도 근사**: $\phi, \theta \approx 0$ $\to$ $\dot{\phi} \approx p$, $\dot{\theta} \approx q$
- **$\Lambda^{-1}$ 존재**: $\cos\theta \cos\phi \neq 0$ (소각도에서 항상 만족)
- **Thruster 무기여**: Roll/Pitch에 thruster 직접 영향 없음 $[\tau_{th}]_{\phi,\theta} = 0$
- **$T_b$ 계산 가능**: $F_{bu}$, $h$가 알려진 설계 파라미터

### Notation

| Symbol | Definition | Note |
|:---|:---|:---|
| $[\cdot]_{\phi,\theta}$ | 6x1 벡터의 4, 5번째 성분 추출 | Roll/Pitch 부분 |
| $M$ | $[M_{bb}]_{\phi,\theta} \in \mathbb{R}^{2\times 2}$ | Roll/Pitch 관성 부분행렬 |
| $\bar{M}$ | 설계 관성 행렬 (상수) | TDC 설계 파라미터 |
| $\nu$ | $[p, q]^T$ | Roll/Pitch 각속도 |
| $B_t$ | $M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b$ | $T_b$ **미포함** |
| $H_t$ | $(M-\bar{M})\dot{\nu}_t+B_t$ | 불확실성 |
| $\Delta T_b$ | $T_{b,t-L} - T_{b,t}$ | 수동 복원 변화량 |

### Step 1-2: Roll/Pitch Extraction

6-DOF body dynamics에서 Roll/Pitch 성분만 추출 (이하 모든 항은 Roll/Pitch 부분행렬/벡터):

$$M\dot{\nu}+M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b=\Lambda \mathbf{p}_{EE}+T_b$$

여기서 $\mathbf{p}_{EE} = [x_{EE}, y_{EE}]^T$.

**$\Lambda$와 $T_b$** (cross product $\mathbf{r} \times F_{body}$에서 유도):

$$\Lambda_t = \begin{bmatrix} 0 & c_\theta c_\phi F_{bu} \\ -c_\theta c_\phi F_{bu} & 0 \end{bmatrix}, \quad T_b = \begin{bmatrix} -c_\theta s_\phi F_{bu} h \\ -s_\theta F_{bu} h \end{bmatrix}$$

$\phi>0$ (양의 roll) 시 복원 토크는 음의 방향이어야 하므로 $T_b$의 부호는 음. $\Lambda$도 동일한 cross product에서 유도되어 부호가 결정된다.

| Term | Meaning | Treatment |
|:---|:---|:---|
| $\Lambda$ | 능동 제어 항 | 제어 입력 |
| $T_b$ | 수동 복원 항 | **명시적 계산** (TDE 제외) |

### Step 3-4: Uncertainty Definition

$T_b$를 제외한 불확실 항만 $B_t$로 정의:

$$B_t = M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b$$

그러면: $M\dot{\nu}+B_t=\Lambda \mathbf{p}_{EE}+T_b$

불확실성 $H_t$ 정의:

$$H_t = (M-\bar{M})\dot{\nu}_t+B_t$$

$T_b$를 $H_t$에서 분리하는 이유: $T_b$는 현재 자세 $(\phi, \theta)$와 알려진 상수 $(F_{bu}, h)$로 정확히 계산 가능. TDE 추정 부담을 줄이고 정확도를 높인다.

### Step 5-6: System Equation

$M = \bar{M} + (M - \bar{M})$로 분리하고 $H_t$ 대입:

$$\Lambda_t \mathbf{p}_{EE,t}=\bar{M}\dot{\nu}_t+H_t-T_{b,t}$$

$H_t$에 대해 정리하면:

$$H_t=\Lambda_t \mathbf{p}_{EE,t}-\bar{M}\dot{\nu}_t+T_{b,t}$$

### Step 7: Time Delay Estimation (TDE)

TDE 핵심 가정: 충분히 짧은 시간 $L$ 동안 $H$가 크게 변하지 않음 ($H_t \approx H_{t-L}$).

$$\hat{H}_t = H_{t-L}=\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+T_{b,t-L}$$

- $\Lambda_{t-L}$: 시간 $t-L$에서의 자세로 계산
- $T_{b,t-L}$: 시간 $t-L$에서의 자세로 계산

### Step 8: Desired Dynamics

원하는 폐루프 동역학 (ALBC는 수평 유지 $\dot{\nu}_d = 0$):

$$\dot{\nu}^{ref} = K_d\dot{e} + K_p e$$

소각도 근사에서:

$$e = \begin{bmatrix} \phi_d - \phi \\ \theta_d - \theta \end{bmatrix}, \quad \dot{e} \approx \begin{bmatrix} -p \\ -q \end{bmatrix}$$

### Step 9: Final Control Law

시스템 방정식에 $\dot{\nu}^{ref}$를 대입하고 TDE를 적용:

$$\boxed{\mathbf{p}_{EE,t}=\Lambda^{-1}_t\left[\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+\bar{M}(K_d\dot{e}_t+K_pe_t)+\Delta T_b\right]}$$

여기서 $\Delta T_b = T_{b,t-L} - T_{b,t}$.

$\Delta T_b$의 물리적 의미: $\Delta T_b \approx -\dot{T}_b \cdot L$. 안정화 목표 ($\phi, \theta \to 0$) 달성 시 $\Delta T_b$ 항의 영향이 자연히 감소한다.

---

## Implementation Extensions

유도 결과에서 실제 구현까지의 확장 사항. Python 구현: `controllers/tdc.py`, `controllers/kinematics.py`.

### DLS Lambda Inverse

유도의 Step 9에서 $\Lambda^{-1}_t$가 필요하다. $\Lambda$는 anti-diagonal:

$$\Lambda_t = \begin{bmatrix} 0 & l_f \\ -l_f & 0 \end{bmatrix}, \quad l_f = \cos\theta\cos\phi \cdot F_{bu}$$

해석적 역행렬은 $1/l_f$에 비례하므로, $\phi, \theta \to 90\degree$일 때 $l_f \to 0$이면 singularity 발산.

**DLS (Damped Least Squares) 적용**:

$$\Lambda^{-1}_{DLS} = \begin{bmatrix} 0 & -d \\ d & 0 \end{bmatrix}, \quad d = \frac{l_f}{l_f^2 + \lambda_{dls}^2}$$

$\lambda_{dls} = 0.01$ (고정 damping 파라미터).

| $l_f$ State | $d$ Behavior | Effect |
|:---|:---|:---|
| $l_f \gg \lambda_{dls}$ (수직 근처) | $d \approx 1/l_f$ | 해석적 역행렬과 동일 |
| $l_f \to 0$ (수평 근처) | $d \to 0$ | $\mathbf{p}_{EE} \to 0$ (graceful degradation) |

### DLS Inverse Kinematics

제어 법칙이 출력하는 $\mathbf{p}_{EE}$를 관절 각도 $\Gamma$로 변환하는 IK에도 DLS 적용.

**Jacobian**:

$$J(\Gamma) = \begin{bmatrix} -l_1 s_1 - l_2 s_{12} & -l_2 s_{12} \\ l_1 c_1 + l_2 c_{12} & l_2 c_{12} \end{bmatrix}$$

**DLS pseudo-inverse** (Yoshikawa adaptive damping):

$$J^{\dagger}_{DLS} = J^T(JJ^T + \lambda^2 I)^{-1}$$

$$\lambda^2 = \lambda_{max}^2 \cdot \text{clamp}(1 - w/w_0, \min=0), \quad w = \det(JJ^T)^{1/(2m)}$$

| Parameter | Value | Description |
|:---|:---|:---|
| $\lambda_{max}$ | 0.15 | 최대 damping (singularity에서) |
| $w_0$ | $\sqrt{l_1 \cdot l_2} = 0.233$ | Manipulability 정규화 기준 |
| $w$ | $\det(JJ^T)^{1/(2m)}$ | Dimension-normalized manipulability |

Singularity ($w \to 0$)에서 $\lambda \to \lambda_{max}$이므로 IK 출력이 자연히 감쇠. Workspace clamp가 불필요해지며, TDE saturation도 제거 가능.

구현은 `torch.linalg.solve`를 사용하여 dimension-independent (higher-DOF 확장 가능).

### Angular Acceleration Filter

$\dot{\nu}$ (각가속도)는 유한 차분으로 계산되므로 노이즈가 크다:

$$\dot{\nu}_t \approx \frac{\nu_t - \nu_{t-1}}{\Delta t}$$

**1차 LPF (EMA)** 적용:

$$\dot{\nu}^{filt}_t = \alpha \cdot \dot{\nu}^{raw}_t + (1 - \alpha) \cdot \dot{\nu}^{filt}_{t-1}, \quad \alpha = 0.05$$

**주의**: $\hat{H}$ 또는 $\hat{U}$ ($T_b$ 포함 항)에는 필터링하지 않음 -- $T_b$의 DC 성분이 bias로 남아 정상상태 오차 유발.

### Anti-Windup

제어 법칙의 $\mathbf{p}_{EE}$는 IK -> 관절 명령 -> rate limiter를 거침. Rate limiter가 관절 명령을 잘라내면, 실제 EE 위치와 제어기 내부 상태가 불일치.

**해결**: `update_ee_position(FK(rate_limited_joints))`로 매 스텝 동기화. 제어기가 "실제 도달한 EE 위치"를 기준으로 다음 스텝을 계산하므로 windup 방지.

### TDE Saturation Removal

C++ 참조 구현과 일치. DLS Lambda_inv + DLS IK가 singularity를 자연 감쇠로 처리하므로, 별도의 TDE magnitude clamping이 불필요.

튜닝 과정에서의 saturation 관련 시행착오는 [debug-history.md](../reference/debug-history.md) 참조.

---

## Summary

### Key Definitions

| Symbol | Definition | Note |
|:---|:---|:---|
| $B_t$ | $M_{bm}\ddot{\Gamma}+C_b\nu+D_b\nu+g_b$ | $T_b$ **미포함** |
| $H_t$ | $(M-\bar{M})\dot{\nu}_t+B_t$ | 불확실성 (lumped) |
| $\Delta T_b$ | $T_{b,t-L} - T_{b,t}$ | 수동 복원 변화량 |

### System Equation

$$\Lambda_t \mathbf{p}_{EE,t}=\bar{M}\dot{\nu}_t+H_t-T_{b,t}$$

### Time Delay Estimation

$$\hat{H}_t=\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+T_{b,t-L}$$

### Final Control Law

$$\mathbf{p}_{EE,t}=\Lambda^{-1}_t\left[\Lambda_{t-L}\mathbf{p}_{EE,t-L}-\bar{M}\dot{\nu}_{t-L}+\bar{M}(K_d\dot{e}_t+K_pe_t)+\Delta T_b\right]$$

### Design Decisions

| Item | Decision |
|:---|:---|
| $H_t$ 단위 | 힘/모멘트 (가속도 아님) |
| $\Lambda$ | 시변 -- $\phi$, $\theta$에 의존 |
| $T_b$ | 명시적 계산 -- TDE에서 분리 |
| $\bar{M}$ | 설계 상수 -- 적응 필요 시 $\bar{M}(\hat{z}_t)$로 확장 |
| TDE saturation | 제거됨 -- DLS가 singularity 자연 처리 |
| IK method | DLS Jacobian (Yoshikawa adaptive), workspace clamp 불필요 |
| $\dot{\nu}$ filter | EMA alpha=0.05 ($\hat{H}$/$\hat{U}$에는 미적용) |
| Anti-windup | FK(rate-limited) 동기화 |

### Current Parameters (from `controllers/tdc.py`)

| Parameter | Value | Description |
|:---|:---|:---|
| `m_hat` | (0.15, 0.16) | 설계 관성 [roll, pitch] (kg-m^2) |
| `kp` | 40 | PD 비례 게인 |
| `kd` | 12 | PD 미분 게인 |
| `h` | 0.18 | CoG-to-ABPC 수직 오프셋 (m) |
| `dls_lambda_damping` | 0.01 | Lambda DLS damping |
| `ik_dls_lambda` | 0.15 | IK DLS 최대 damping |
| `nu_dot_ema_alpha` | 0.05 | 각가속도 필터 계수 |
| `max_joint_velocity` | 2.5 | Rate limiter (rad/s) |
| `base_position` | (0.002, 0.002) | EE 기본 위치 (m) |
| TDC dt | 0.02 s (50 Hz) | `step_dt * control_decimation` |

---

**Created**: 2026-02-09
**Updated**: 2026-02-21 (Synced parameter table with TDCControllerCfg actual values.)
