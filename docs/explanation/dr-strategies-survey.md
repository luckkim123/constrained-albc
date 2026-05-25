# Domain Randomization Training Strategies: Literature Survey

Date: 2026-02-24

Hero Agent 훈련에서 DR이 강해질수록 attitude error가 단조 증가하는 문제를 해결하기 위해,
선도 연구들의 DR 대응 전략을 조사. Adaptive entropy, DR 커리큘럼, privileged info 활용,
contrastive learning 등 주요 접근법을 비교 분석.

---

## 1. DR 커리큘럼 접근법

### 1.1 Fixed DR (Uniform)

가장 단순한 방식. 처음부터 전체 DR 범위에서 균일 샘플링.

- 장점: 구현 단순, 하이퍼파라미터 없음
- 단점: DR 범위가 넓으면 초기 학습 실패 또는 overly conservative policy
- 사용 사례: RMA, HORA (대신 privileged info로 DR 보상)

### 1.2 Manual Linear Curriculum (현재 Hero Agent)

좁은 DR 범위에서 시작, iteration에 비례하여 선형 확장.

```
param_range(iter) = start + (end - start) * min(1, iter / end_iter)
```

- 장점: 구현 단순, 예측 가능한 진행
- 단점: **Policy 준비 여부와 무관하게 DR이 확장**됨
- 문제: reward 커리큘럼과 동시 진행 시 death spiral 가능 (Hero Agent에서 확인)

### 1.3 ADR (Automatic Domain Randomization) - OpenAI, 2019

> Solving Rubik's Cube with a Robot Hand. OpenAI, 2019.
> https://openai.com/index/solving-rubiks-cube/

**성능 기반 DR 확장/수축.** 핵심 알고리즘:

1. 비랜덤 환경에서 시작 (모든 파라미터 = nominal)
2. 매 iteration: DR 파라미터 하나를 랜덤 선택
3. **Boundary sampling**: 해당 파라미터를 경계값 (상한 또는 하한)에 고정, 나머지는 현재 범위에서 샘플링
4. 해당 환경에서 N 에피소드 성능 평가 -> 버퍼에 축적
5. 평균 성능 > threshold_H -> **경계 확장** (DR 더 어렵게)
6. 평균 성능 < threshold_L -> **경계 수축** (DR 쉽게)
7. 반복

```
For each iteration:
    i = random DR parameter index
    boundary = random choice (lower or upper)
    fix param_i to boundary value, sample others normally
    evaluate performance -> append to buffer[i][boundary]
    if mean(buffer) > phi_H:
        expand boundary by delta
    elif mean(buffer) < phi_L:
        contract boundary by delta
```

핵심 특성:
- **Policy가 준비되면 확장, 실패하면 수축** (선형 커리큘럼과의 결정적 차이)
- Human intervention 불필요 (자동 범위 결정)
- ADR entropy = 분포 다양성 지표, 전이 성능과 상관
- Dactyl에서 루빅큐브 풀기까지 확장 (100+ DR 파라미터)

### 1.4 DORAEMON (ICLR 2024)

> Domain Randomization via Entropy Maximization.
> Tiboni et al., ICLR 2024.
> https://arxiv.org/abs/2311.01885

**Constrained entropy maximization으로 DR 분포 최적화.**

```
max  H(p_phi)                    # DR 분포의 엔트로피 최대화
s.t. E_phi[success(pi)] >= eta   # 현재 policy 성공률 >= threshold
```

- ADR보다 더 원리적: 분포 자체를 최적화 (경계만 조절하는 ADR과 달리)
- 고정 DR 대비 항상 우수 (wider generalization)
- 자연스럽게 커리큘럼 유도: 성공률 제약이 점진적 확장을 강제
- Sim-to-Real 제로샷 전이 성공 (robotic manipulation)

### 1.5 Active Domain Randomization (CoRL 2019)

> Active Domain Randomization.
> Mehta et al., CoRL 2019.
> https://arxiv.org/abs/1904.04762

- ADR과 다른 접근: "가장 informative한" DR 환경을 능동적으로 탐색
- Discriminator로 randomized vs reference 환경의 trajectory 구분
- Discriminator output을 reward로 사용 -> SVPG로 sampling policy 최적화
- 결과: policy에게 어려운 환경을 더 많이 샘플링 (curriculum 자동 유도)

---

## 2. Exploration / Adaptive Entropy 전략

### 2.1 axPPO (2024)

> Proximal Policy Optimization with Adaptive Exploration.
> 2024. https://arxiv.org/abs/2405.04664

**Recent return 기반 entropy 스케일링.**

```
L(theta) = E[L_CLIP - c1*L_VF + G_recent * c2 * S[pi](s)]

G_recent = (1/G_max) * mean(recent tau steps batch returns)
```

- G_recent in [0, 1]: 성능 좋을 때 높음, 나쁠 때 낮음
- **성능 좋을 때 entropy 증가** (exploit 강화) -- Hero Agent와 반대 방향
- 고정 c2 대비 성능 변동에 덜 민감
- 주의: DR 환경이 아닌 순수 exploration 환경 (sparse reward) 타겟

### 2.2 SAC Automatic Alpha Tuning

> Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL.
> Haarnoja et al., 2018. + Meta-SAC, 2020.
> https://arxiv.org/abs/2007.01932

**Target entropy로 alpha 자동 조절.**

```
min_alpha  E[-alpha * log pi(a|s) - alpha * H_target]
H_target = -dim(action_space)   # 일반적 default
```

- Off-policy 특성상 DR 환경에서도 안정적
- Alpha가 자동으로 올바른 수준 유지 (DR 강도에 무관)
- PPO와 달리 entropy가 objective에 직접 포함

### 2.3 Entropy-Controlled Intrinsic Motivation (2024)

> Entropy-Controlled Intrinsic Motivation for Quadruped Robot Locomotion.
> 2024. https://arxiv.org/html/2512.06486

- 복잡 terrain에서 entropy 기반 intrinsic motivation
- Entropy 낮아지면 (exploitation 과다) -> intrinsic reward 증가 -> exploration 강제
- Terrain curriculum과 결합

### 2.4 선도 연구들의 공통점

**대부분 entropy를 명시적으로 조절하지 않음.**

| 방법 | Entropy 전략 | DR 대응 |
|------|-------------|---------|
| ADR (OpenAI) | 고정 | DR 범위를 policy 성능에 맞춤 |
| DORAEMON | 고정 | DR 분포 자체를 최적화 |
| RMA/HORA | 고정 | Privileged info로 DR 보상 |
| HIM | 고정 | Contrastive embedding으로 DR 보상 |
| Extreme Parkour | 고정 | Terrain curriculum (성능 기반) |
| axPPO | Adaptive | 성능 좋을 때 entropy 증가 (반대 방향) |
| Hero Agent (현재) | Adaptive | 성능 나빠지면 entropy 증가 |

---

## 3. Privileged Info / Adaptation 전략

### 3.1 RMA (Rapid Motor Adaptation)

> Kumar et al., RSS 2021.
> https://ar5iv.labs.arxiv.org/html/2107.04034

**2-Phase regression 기반 adaptation.**

Phase 1 (RL + Encoder):
- Policy + encoder(mu) 동시 학습 (PPO)
- Encoder: privileged env parameters -> extrinsics vector z
- Policy: [proprioception, z] -> actions
- **풀 DR, 커리큘럼 없음** (privileged info가 DR을 보상)

Phase 2 (Adaptation):
- Policy + encoder 동결
- Adaptation module(phi) 학습: proprio history -> z_hat (supervised)
- z_hat이 z를 대체하여 실제 환경에서 작동

핵심 통찰:
- Privileged info가 있으면 DR이 어려워도 학습 가능 (policy가 환경을 "안다")
- Regression target (z)이 DR noise에 오염될 수 있음 (HIM에서 지적)

### 3.2 HIM (Hybrid Internal Model, ICLR 2024)

> Long et al., ICLR 2024.
> https://arxiv.org/abs/2312.11460

**Contrastive learning 기반 환경 embedding. RMA regression의 대안.**

Architecture:
```
과거 5스텝 proprioception history
    |
Embedding Extractor (MLP 512->256->128)
    |
    +-- Explicit: v_hat (velocity) -- MSE regression (ground truth)
    +-- Implicit: l_hat in R^16   -- SwAV contrastive learning
    |
Policy: [partial_obs, v_hat, l_hat] -> actions
Critic: [privileged_obs] -> value (학습 시에만)
```

SwAV Contrastive Learning:
```
J_SwAV = -1/2 * sum(q_source * log(p_target) + q_target * log(p_source))
```
- Source: 과거 관측 history -> encoder -> embedding
- Target: 미래 관측 (successor state) -> encoder -> embedding
- Prototype: K개의 learnable cluster center
- Sinkhorn-Knopp: batch 내 균등 할당 강제 (collapse 방지)

2-Phase 최적화 (매 iteration):
```
Phase A (HIO): SwAV + velocity MSE로 embedding 업데이트, policy frozen
Phase B (PPO): Embedding frozen, actor/critic만 PPO 업데이트
```

DR 파라미터 (커리큘럼 없이 전체 범위):
| Parameter | Range |
|-----------|-------|
| Body/Link mass | +/-20% |
| CoM offset | +/-0.1m |
| Payload | -1~3 kg |
| Ground friction | 0.2~2.75 |
| Restitution | 0.0~1.0 |
| Motor strength | +/-20% |
| Joint Kp/Kd | +/-20% |
| System delay | 0~3dt |
| External force | +/-30N |

성능 (vs RMA):
| 환경 | HIM | RMA |
|------|-----|-----|
| Short stairs 성공률 | 100% | 60% |
| Long stairs (cm) | 176.5 | 75.4 |
| 복합 terrain | 85% | 45% |
| 변형 경사면 | 55% | 10% |

핵심 차이점 (vs RMA):
- RMA: "마찰이 0.5, 질량이 1.2배" 추정 (regression)
- HIM: "이 환경은 A와 비슷, B와 다르다" 구분 (contrastive)
- Regression은 DR noise에 target 오염, contrastive는 상대적 차이만 학습

### 3.3 Extreme Parkour (ICRA 2024)

> Cheng et al., ICRA 2024.
> https://ar5iv.labs.arxiv.org/html/2309.14341

**Teacher-Student distillation + 성능 기반 terrain curriculum.**

Phase 1 (Teacher, RL):
- 입력: proprioception + scandots(특권) + heading + flag
- ROA (Regularized Online Adaptation): 환경 파라미터 estimator 동시 학습
- PPO로 학습

Phase 2 (Student, DAgger):
- 입력: proprioception + depth image(58x87, 10Hz) + heading prediction
- Teacher action을 MSE로 모방
- Student 자신의 action으로 환경 step (distribution shift 해결)

Curriculum (성능 기반):
```python
if distance_traveled > 0.5 * terrain_length:
    difficulty += 1  # 승격
elif distance_traveled < 0.5 * v_cmd * T:
    difficulty -= 1  # 강등
```

MTS (Mixture of Teacher and Student):
- Heading prediction이 oracle과 0.6 rad 이내 -> student prediction 사용
- 그 외 -> oracle heading 강제 (학습 안정성)

달성 성능:
- High jump: 0.5m (로봇 높이 2배)
- Long jump: 0.8m (로봇 길이 2배)
- 경사면: 37도
- Handstand 보행 가능

Exploration: **명시적 메커니즘 없음.** Terrain diversity가 자연 exploration 역할.

---

## 4. Isaac Lab 커뮤니티 실전 권장사항

> https://github.com/isaac-sim/IsaacLab/discussions/2813

### 단계적 도입 순서
1. DR 없이 / 최소 DR로 안정적 학습 확인
2. Friction, actuator gains부터 점진적 도입
3. Sensor noise, perturbation 등 복잡 요인 확장

### 구체적 범위 예시 (AnymalC)
- Static friction: 0.7~1.3
- Stiffness scale: 0.75~1.5
- Damping scale: 0.3~3.0

### 핵심 원칙
- DR 범위를 줄여서 학습을 쉽게 만들지 말 것 (실제 환경 대응력 저하)
- 대신 하이퍼파라미터 튜닝으로 해결
- 실제 센서/환경 측정값으로 현실적 범위 설정

---

## 5. Hero Agent에 대한 시사점

### 현재 문제

DR 커리큘럼(선형)이 policy 준비와 무관하게 확장 -> attitude error 단조 증가.
Adaptive entropy로 대응 중이나, 문헌에서 이 접근은 드묾.

### 문헌 기반 대안 분석

#### Option A: ADR 스타일 성능 기반 커리큘럼 (추천도: ★★★)

현재 선형 ramp -> boundary sampling + threshold 기반 확장으로 전환.

장점:
- Policy가 준비 안 됐으면 DR이 확장되지 않음 (death spiral 원천 방지)
- Adaptive entropy 불필요해질 수 있음
- OpenAI에서 100+ 파라미터까지 검증됨

구현 복잡도: 중간
- 각 DR 파라미터에 boundary sampling + performance buffer 필요
- Threshold 설정 필요 (phi_H, phi_L)
- BaseRunner.log() 수정

#### Option B: Encoder 학습 안정화 (추천도: ★★☆)

HORA 원논문은 커리큘럼 없이 풀 DR + encoder로 작동.
우리 encoder가 불안정한 이유를 진단하고 안정화에 집중.

장점:
- 커리큘럼 자체가 불필요해질 수 있음
- 원논문의 검증된 파이프라인

단점:
- 수중 로봇은 legged보다 control authority가 낮아 동일 적용이 어려울 수 있음
- Encoder 불안정 원인이 DR noise에 의한 regression target 오염이면 근본적 한계

#### Option C: HIM 스타일 Contrastive Encoder (추천도: ★★☆)

Regression encoder -> contrastive encoder로 교체.

장점:
- DR noise에 robust한 representation
- HIM 논문에서 RMA 대비 큰 성능 우위 입증

단점:
- 구현 복잡도 높음 (SwAV, Sinkhorn-Knopp, prototype 관리)
- 2-phase 최적화 (HIO + PPO) 필요
- 기존 파이프라인 대폭 변경

#### Option D: 현재 접근 유지 + 파라미터 튜닝 (추천도: ★☆☆)

Adaptive entropy + linear DR curriculum 유지, 파라미터만 조절.

장점: 코드 변경 최소
단점: 문헌에서 이 조합의 성공 사례 부재, 근본 해결이 아닐 수 있음

---

## References

1. OpenAI. "Solving Rubik's Cube with a Robot Hand." 2019.
   https://openai.com/index/solving-rubiks-cube/
2. Tiboni et al. "DORAEMON: Domain Randomization via Entropy Maximization." ICLR 2024.
   https://arxiv.org/abs/2311.01885
3. Mehta et al. "Active Domain Randomization." CoRL 2019.
   https://arxiv.org/abs/1904.04762
4. "Proximal Policy Optimization with Adaptive Exploration (axPPO)." 2024.
   https://arxiv.org/abs/2405.04664
5. Haarnoja et al. "Meta-SAC: Auto-tune Entropy Temperature." 2020.
   https://arxiv.org/abs/2007.01932
6. Kumar et al. "RMA: Rapid Motor Adaptation for Legged Robots." RSS 2021.
   https://ar5iv.labs.arxiv.org/html/2107.04034
7. Long et al. "HIM: Hybrid Internal Model for Agile Legged Locomotion." ICLR 2024.
   https://arxiv.org/abs/2312.11460
8. Cheng et al. "Extreme Parkour with Legged Robots." ICRA 2024.
   https://ar5iv.labs.arxiv.org/html/2309.14341
9. Isaac Lab Discussion #2813: Tips for Domain Randomization.
   https://github.com/isaac-sim/IsaacLab/discussions/2813
10. "Entropy-Controlled Intrinsic Motivation for Quadruped." 2024.
    https://arxiv.org/html/2512.06486
