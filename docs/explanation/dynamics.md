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

TDC(Time Delay Control)는 흔히 "model-free"로 불리지만, 실제로는 model-based controller이다.
설계 행렬 $\bar{M}$이 실제 관성 $M(q)$의 대략적 추정치를 필요로 한다.
여기서 "model-free"의 진짜 의미는 정밀한 모델 식별이 불필요하다는 것(50% 오차 허용)이지,
모델이 아예 불필요하다는 의미가 아니다.

**안정성 조건**:

$$\|I - \bar{M}^{-1}M(q)\| < 1$$

이 조건은 $\bar{M}$이 실제 $M(q)$의 약 50%~200% 범위 내에 있어야 충족된다.

### Why Adaptive $\bar{M}$ is Necessary

ALBC 동역학 모델(Eq. 3)은 mini-ROV만 고려한다:

$$M\dot{\nu} + C(\nu)\nu + D(\nu)\nu + g(\eta) = \tau_{th} + b(\Gamma)$$

이 모델에서 $M$은 관절 각도 $\Gamma$에 독립적인 상수 행렬로 취급된다.
그러나 실제로는 두 가지 원인에 의해 관성 행렬이 크게 변한다:

**원인 1: 부력제(Buoyancy Element)의 위치 변화**

- 2-DoF 로봇 팔 끝단의 부력제는 큰 부피를 가지며, 수중에서 상당한 부가질량(added mass)을 생성한다.
- 부력제 위치가 $\Gamma$에 따라 변하면 질량 분포가 변하고, 따라서 $M(\Gamma)$가 된다.
- 본 문서의 [Section 4](#4-inertia-variation-analysis-and-tdc-stability)에서 보이듯,
  roll 관성만으로도 약 200%(3배) 변화가 발생한다.

**원인 2: 미지 물체 파지(Object Grasping)**

- 물체 파지 시 관성 $M \to M + M_{obj}$, 질량 중심(CoG) 이동, 부력 중심(CoB) 변화 등이 발생한다.
- 미지 물체의 $m_{obj}$, $I_{obj}$, CoM 위치를 직접 측정하는 것은 비실용적이다.

두 원인 모두 고정된 $\bar{M}$으로는 TDC 안정성 조건 위배를 초래한다.
따라서 $\bar{M}$을 실시간으로 적응시키는 메커니즘이 필수적이다.

---

## 2. ALBC Dynamics Model Issues

기존 ALBC 논문의 동역학 모델링에는 네 가지 주요 문제점이 있다.

### Issue 1: Buoyancy Element Dynamics Omitted

현재 모델에서 $M$은 상수이고, 부력항 $b(\Gamma)$는 부력제의 위치만 고려한다.
수정되어야 할 형태:

$$M(\Gamma)\dot{\nu} + C(\nu, \Gamma, \dot{\Gamma})\nu + D(\nu)\nu + g(\eta) = \tau_{th} + b(\Gamma)$$

누락된 동역학 항목:

| 누락 항목 | 설명 |
|:---|:---|
| $M(\Gamma)$ | 관성 행렬의 $\Gamma$ 의존성 (부력제 위치에 따른 질량 분포 변화) |
| $\dot{M}(\Gamma)\nu$ | 시변 관성에 의한 Coriolis 행렬 기여 |
| Coriolis/Centripetal | 부력제 회전 운동으로 인한 추가 Coriolis 항 |
| Added Mass | 부력제의 큰 부피로 인한 수력학적 부가질량 효과 |

구성 요소별로 보면, Link 1/2는 질량과 부피가 작아 무시 가능하지만,
부력제는 질량은 작아도 부피가 커서 무시할 수 없다.

### Issue 2: Free-Floating Dynamics Not Reflected

현재 모델은 mini-ROV를 고정된 base로 암묵적으로 가정한다.
그러나 수중에서는 고정점(ground)이 없는 free-floating system이다.

$$L_{total} = L_{body} + L_{ALBC} = \text{constant (외부 토크 없을 때)}$$

부력제가 움직이면 각운동량 보존에 의해 main body가 반작용으로 회전한다.
이는 우주 로봇이 팔을 돌리면 base가 반대로 회전하는 현상과 동일하다.

Free-floating system의 올바른 동역학:

$$\begin{bmatrix} M_{bb} & M_{bm} \\ M_{mb} & M_{mm} \end{bmatrix} \begin{bmatrix} \dot{\nu} \\ \ddot{\Gamma} \end{bmatrix} + \begin{bmatrix} C_b \\ C_m \end{bmatrix} = \begin{bmatrix} \tau_{th} + b(\Gamma) \\ \tau_{joint} \end{bmatrix}$$

여기서 $M_{bm}$, $M_{mb}$는 Base-Manipulator 커플링 관성이며,
ALBC 가속 $\ddot{\Gamma}$가 main body 가속 $\dot{\nu}$에 영향을 준다.
현재 모델에는 이 커플링 항이 없다.

### Issue 3: Yaw Dynamics Omitted

기존 모델은 Roll/Pitch 동역학만 제시하고, Yaw 동역학이 없다.
부력제 위치가 비대칭일 경우 yaw 모멘트가 발생할 수 있으며,
6-DoF 제어에서 yaw coupling을 무시하면 문제가 된다.

### Issue 4: Object Grasping Dynamics Not Modeled

물체 파지 시 발생하는 변화:

| 변화 항목 | 내용 | 문제 |
|:---|:---|:---|
| 관성 행렬 | $M \to M + M_{obj}$ | 미지 물체의 경우 측정 불가 |
| 질량 중심 (CoG) | $r_G \to r'_G = \frac{m \cdot r_G + m_{obj} \cdot r_{obj}}{m + m_{obj}}$ | 복원력 $g(\eta)$에 직접 영향 |
| 부력 중심 (CoB) | $r_B \to r'_B$ | CoG-CoB 관계 변화 |
| Coriolis 항 | $C(\nu) \to C'(\nu)$ | 관성 행렬 변화에 따라 수정 필요 |

ALBC 실험 결과에서도 200g, 400g 물체는 steady-state error,
600g 물체에서는 position/orientation 발산이 관찰되었다.

### Summary

| Issue | 현재 모델 | 필요한 모델 |
|:---|:---|:---|
| 1. 부력제 동역학 | 위치만 고려, $M$ 상수 | $M(\Gamma)$, Coriolis, 부가질량 포함 |
| 2. Free-Floating | 고정 base 가정 | Base-Manipulator 커플링 반영 |
| 3. Yaw 동역학 | 없음 | Roll/Pitch/Yaw 전체 |
| 4. 물체 파지 | 고려 안함 | $M_{obj}$, CoG, CoB 변화 반영 |

---

## 3. Added Mass Coupling Derivation

부력제의 물리적 질량을 무시하고, Added Mass만 고려한 동역학 모델의 유도 과정이다.

> **Note**: 이 유도에서는 $m_{bu} \approx 0$ (massless buoy)으로 가정하지만,
> 실제 URDF의 buoy body mass는 약 0.93 kg이다. 코드 구현(`compute_M_bb`)에서는
> `m_{total} = m_{body} + m_A`를 사용하여 buoy rigid body mass를 포함한다.

### 3.1 Notation

| 기호 | 정의 | 크기 |
|:---|:---|:---|
| $\eta$ | Earth-fixed 위치/자세 | $\mathbb{R}^6$ |
| $\nu$ | Body-fixed 속도 | $\mathbb{R}^6$ |
| $\Gamma = [\gamma_1, \gamma_2]^T$ | 관절 각도 | $\mathbb{R}^2$ |
| $\zeta = [\nu^T, \dot{\Gamma}^T]^T$ | 속도 좌표 | $\mathbb{R}^8$ |

### 3.2 Physical Motivation and Added Mass Estimation

부력제의 특성:

| 속성 | 값 | 물리적 의미 |
|:---|:---|:---|
| 물리적 질량 $m_{bu}$ | $\approx 0$ | 경량 재질 (폼, 플라스틱) |
| 부피 $V_{bu}$ | 큼 | 부력 생성 필요 |
| Added mass $m_A$ | 큼 | 유체 변위에 의한 가상 질량 |

부력제가 수중에서 가속하면 주변 유체도 함께 가속되어, 마치 추가 질량이 있는 것처럼 관성이 증가한다.

$$F = (m + m_A)\dot{v}$$

**ALBC 부력제 수치 추정**:

- 부력 $F_{bu} = 1.835$ kgf = 18.0 N
- $V_{bu} = F_{bu} / (\rho g) \approx 0.00179$ m$^3$
- Added mass (원통 가정, $C_m \approx 1.0$): $m_A \approx 1.0 \times 1025 \times 0.00179 \approx 1.83$ kg

물리적 질량이 0이어도 added mass는 약 1.83 kg이다.

### 3.3 Buoyancy Element Kinematics

Body frame에서 부력제의 위치 (Forward Kinematics):

$$P_{EE}(\Gamma) = \begin{bmatrix} l_1\cos\gamma_1 + l_2\cos(\gamma_1+\gamma_2) \\ l_1\sin\gamma_1 + l_2\sin(\gamma_1+\gamma_2) \\ h \end{bmatrix}$$

| 파라미터 | 값 | 설명 |
|:---|:---|:---|
| $l_1, l_2$ | 0.233 m | 링크 길이 |
| $h$ | 0.230 m | CoG에서 ALBC 평면까지 높이 (상수) |

Jacobian:

$$\dot{P}_{EE} = J_{bu}(\Gamma)\dot{\Gamma}, \quad J_{bu} = \frac{\partial P_{EE}}{\partial \Gamma} \in \mathbb{R}^{3 \times 2}$$

### 3.4 Buoyancy Element Velocity

Body frame에서 부력제의 절대 속도:

$$v^B_{bu} = \nu_1 + \nu_2 \times P_{EE} + J_{bu}\dot{\Gamma}$$

Cross product를 skew-symmetric matrix $S(\cdot)$로 표현하면:

$$v^B_{bu} = \nu_1 - S(P_{EE})\nu_2 + J_{bu}\dot{\Gamma} = H_{bu}\nu + J_{bu}\dot{\Gamma}$$

여기서:

$$H_{bu} = \begin{bmatrix} I_3 & -S(P_{EE}) \end{bmatrix} \in \mathbb{R}^{3 \times 6}$$

### 3.5 Added Mass Kinetic Energy

전체 운동에너지:

$$T = T_{ROV} + T_A = \frac{1}{2}\nu^T M_{ROV}\nu + \frac{1}{2}m_A(v^B_{bu})^T v^B_{bu}$$

$T_A$를 전개하면:

$$T_A = \frac{1}{2}m_A\nu^T H_{bu}^T H_{bu}\nu + m_A\nu^T H_{bu}^T J_{bu}\dot{\Gamma} + \frac{1}{2}m_A\dot{\Gamma}^T J_{bu}^T J_{bu}\dot{\Gamma}$$

$H_{bu}^T H_{bu}$를 계산하면 ($S^T = -S$ 성질 이용):

$$H_{bu}^T H_{bu} = \begin{bmatrix} I_3 & -S(P_{EE}) \\ S(P_{EE}) & S(P_{EE})^T S(P_{EE}) \end{bmatrix}$$

### 3.6 Skew-Symmetric Matrix Identity

유도에 필요한 핵심 항등식 (Levi-Civita 기호를 통해 증명):

$$S(r)^T S(r) = \|r\|^2 I_3 - rr^T$$

$P_{EE} = [x_{bu}, y_{bu}, h]^T$에 적용하면:

$$S(P_{EE})^T S(P_{EE}) = \begin{bmatrix} y_{bu}^2 + h^2 & -x_{bu}y_{bu} & -x_{bu}h \\ -x_{bu}y_{bu} & x_{bu}^2 + h^2 & -y_{bu}h \\ -x_{bu}h & -y_{bu}h & x_{bu}^2 + y_{bu}^2 \end{bmatrix}$$

물리적 해석:
- 대각 성분: Parallel axis theorem -- added mass $m_A$가 회전축에서 거리 $d$만큼 떨어지면 $\Delta I = m_A d^2$
- 비대각 성분: Products of inertia -- added mass가 비대칭 위치에 있을 때 발생

### 3.7 Inertia Matrix Assembly

전체 운동에너지를 속도 좌표 $\zeta = [\nu^T, \dot{\Gamma}^T]^T$로 정리:

$$T = \frac{1}{2}\zeta^T M(\Gamma)\zeta$$

$$M(\Gamma) = \begin{bmatrix} M_{bb}(\Gamma) & M_{bm}(\Gamma) \\ M_{mb}(\Gamma) & M_{mm}(\Gamma) \end{bmatrix}$$

**Body Inertia** $M_{bb}(\Gamma)$:

$$M_{bb}(\Gamma) = M_{ROV} + m_A\begin{bmatrix} I_3 & -S(P_{EE}) \\ S(P_{EE}) & S(P_{EE})^T S(P_{EE}) \end{bmatrix}$$

Mini-ROV가 대각 형태 ($M_{12} = M_{21} = 0$)라면:

$$M_{bb}(\Gamma) = \begin{bmatrix} (m_{ROV} + m_A)I_3 & -m_A S(P_{EE}) \\ m_A S(P_{EE}) & I_{ROV} + m_A S(P_{EE})^T S(P_{EE}) \end{bmatrix}$$

**Body-Manipulator Coupling** $M_{bm}(\Gamma)$:

$$M_{bm}(\Gamma) = m_A H_{bu}^T J_{bu} = m_A\begin{bmatrix} J_{bu} \\ S(P_{EE})J_{bu} \end{bmatrix} \in \mathbb{R}^{6 \times 2}$$

**Manipulator Inertia** $M_{mm}(\Gamma)$:

$$M_{mm}(\Gamma) = m_A J_{bu}^T J_{bu} \in \mathbb{R}^{2 \times 2}$$

### 3.8 Rotation Inertia Components

회전 관성 부분행렬:

$$I_{rot}(\Gamma) = I_{ROV} + m_A S(P_{EE})^T S(P_{EE})$$

대각 성분:

$$I_p(\Gamma) = I_{p,ROV} + m_A(y_{bu}^2 + h^2) \quad \text{(Roll)}$$

$$I_q(\Gamma) = I_{q,ROV} + m_A(x_{bu}^2 + h^2) \quad \text{(Pitch)}$$

$$I_r(\Gamma) = I_{r,ROV} + m_A(x_{bu}^2 + y_{bu}^2) \quad \text{(Yaw)}$$

비대각 성분 (Products of Inertia):

$$I_{pq} = -m_A x_{bu} y_{bu}, \quad I_{pr} = -m_A x_{bu} h, \quad I_{qr} = -m_A y_{bu} h$$

### 3.9 Equations of Motion

Lagrangian approach (Euler-Lagrange + Christoffel symbols)로 유도하면:

$$M(\Gamma)\dot{\zeta} + C(\Gamma, \dot{\Gamma})\zeta + D(\zeta)\zeta + g(q) = \tau$$

Body dynamics (첫 번째 행)를 추출하면:

$$M_{bb}(\Gamma)\dot{\nu} + M_{bm}(\Gamma)\ddot{\Gamma} + C_b(\nu, \Gamma, \dot{\Gamma}) + D_b(\nu)\nu + g_b(\eta) = \tau_{th} + b(\Gamma)$$

각 항의 물리적 의미:
- $M_{bb}(\Gamma)\dot{\nu}$: Body 가속에 필요한 힘 (added mass 포함, $\Gamma$ 의존)
- $M_{bm}(\Gamma)\ddot{\Gamma}$: 관절 가속도가 body에 미치는 반작용력
- $C_b$: Coriolis/원심력 (관절 운동에 의한 추가 항 포함)

기존 ALBC 모델과의 비교:

| 항 | 기존 모델 | 유도된 모델 (Added Mass) |
|:---|:---|:---|
| 관성 | $M$ (상수) | $M_{bb}(\Gamma) = M_{ROV} + m_A(\cdots)$ |
| 커플링 | 없음 | $M_{bm}(\Gamma)\ddot{\Gamma}$ |
| Coriolis | $C(\nu)$ | $C_b(\nu, \Gamma, \dot{\Gamma})$ |
| 핵심 차이 | $\Gamma$ 무관 | Added mass에 의한 $\Gamma$ 의존성 |

---

## 4. Inertia Variation Analysis and TDC Stability

### 4.1 Workspace and Inertia Bounds

부력제 도달 범위: $r_{max} = l_1 + l_2 = 0.466$ m

$y_{bu} \in [-r_{max}, +r_{max}]$이므로, Roll 관성의 경계:

$$I_p^{min} = I_{p,ROV} + m_A h^2 \quad (y_{bu} = 0)$$

$$I_p^{max} = I_{p,ROV} + m_A(r_{max}^2 + h^2) \quad (|y_{bu}| = r_{max})$$

### 4.2 Numerical Analysis

추정 파라미터:

| 파라미터 | 값 |
|:---|:---|
| $m_A$ | 1.83 kg |
| $r_{max}$ | 0.466 m |
| $h$ | 0.230 m |
| $I_{p,ROV}$ | $\approx 0.1$ kg$\cdot$m$^2$ |

계산 결과:

$$I_p^{min} = 0.1 + 1.83 \times 0.230^2 = 0.197 \text{ kg}\cdot\text{m}^2$$

$$I_p^{max} = 0.1 + 1.83 \times (0.466^2 + 0.230^2) = 0.594 \text{ kg}\cdot\text{m}^2$$

상대 변화:

$$\frac{I_p^{max} - I_p^{min}}{I_p^{min}} = \frac{0.397}{0.197} = 201\%$$

Added mass만 고려해도 roll 관성이 약 200%(3배) 변화한다.

### 4.3 TDC Stability Condition Violation

TDC 안정성 조건: $\|I - \bar{M}^{-1}M(\Gamma)\| < 1$

이는 $\bar{M}$이 실제 $M(\Gamma)$의 50%~200% 범위 내에 있어야 함을 의미한다.

$\bar{M} = I_p^{min}$으로 고정 시:

$$\bar{M}^{-1}M^{max} = \frac{I_p^{max}}{I_p^{min}} = \frac{0.594}{0.197} = 3.02$$

$$\|I - \bar{M}^{-1}M^{max}\| = |1 - 3.02| = 2.02 > 1$$

안정성 조건이 위배된다.
물체 파지까지 고려하면 관성 변화 폭은 더 커지므로, 고정된 $\bar{M}$으로는
안정적인 TDC 운용이 근본적으로 불가능하다.

| 항목 | 값 |
|:---|:---|
| 부력제 물리적 질량 | $\approx 0$ (무시) |
| Added mass $m_A$ | 1.83 kg |
| Roll 관성 변화 | 201% (약 3배) |
| $I_p^{max} / I_p^{min}$ | 3.02 |
| TDC 안정성 | 조건 위배 ($2.02 > 1$) |
| 결론 | 적응적 $\bar{M}$ 필수 |

---

## 5. Proposed Solution: RL-based Adaptive TDC

### 5.1 Core Idea

Model-Free RL의 적응성과 Model-Based Control의 구조적 안정성을 통합한다.
기존 연구(RL-TDC 2022, AC-TDC 2021 등)가 게인 튜닝에 초점을 맞춘 반면,
본 접근법은 proprioception 이력으로부터 현재 시스템의 물리적 특성을 추론하여
$\bar{M}$을 적응시키는 것이 핵심 차별점이다.

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

- 시뮬레이터에서 물체의 ground truth 물리량(질량, 관성, CoM)에 접근
- Extrinsics Encoder로 물리량을 latent vector $z_t$로 압축
- $z_t$를 이용하여 $\bar{M}(z_t)$를 생성하고 base policy 학습

**Phase 2 (Student)**: Adaptation Module

- Proprioception 이력만으로 latent vector $\hat{z}_t$를 추정
- Ground truth 없이도 암묵적으로 물리량 추론
- 실환경에서 추가 학습 없이 바로 적용 가능 (zero-shot sim-to-real transfer)

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

- 시뮬레이터에서 다양한 물체(질량, 형태, CoM 분포)에 대해 학습
- 실환경에서 미지 물체에도 적응적으로 $\bar{M}$ 조정
- Domain randomization으로 sim-real gap 최소화
- Latent vector $z_t$와 실제 물리량 사이 correspondence 분석 가능 (해석 가능성)

TDC 제어 법칙의 구체적인 수식 유도는 [tdc-control-law.md](tdc-control-law.md)를 참조.
시스템 전반 구성(action/obs 공간, 알고리즘, 네트워크 구조)은 [system-overview.md](system-overview.md)를 참조.

---

**Created**: 2026-02-11
**Updated**: 2026-02-11
**Status**: Consolidated reference -- derived from research notes 01 (Research Idea), 02 (ALBC Dynamics Issues), 03 (Added Mass Coupling)
