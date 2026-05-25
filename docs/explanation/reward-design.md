# Reward Functions

> **Status**: 2026-02-28 | **Source**: `mdp/rewards.py`, `config.py`
>
> Hero Agent ALBC 보상함수의 수학적 분석, 설계 근거, 실측 수치.
> Multi-scale gradient 구조: Gaussian tracking + settling + linear error + regularization penalties.

---

## Overview

Hero Agent ALBC 환경의 보상은 6개 항의 가중합으로 구성된다:

$$r_t = \underbrace{w_1 \cdot e^{-\phi_t^2 / \sigma^2} \cdot \Delta t}_{\text{tracking}} + \underbrace{w_2 \cdot \text{settling}(\phi_t) \cdot \Delta t}_{\text{settling}} + \underbrace{w_3 \cdot \text{PBRS}(\phi)}_{\text{progress}} + \underbrace{w_4 \cdot \text{hf}^2 \cdot \Delta t}_{\text{joint osc.}} + \underbrace{w_5 \cdot \|\dot\gamma\|^2 \cdot \Delta t}_{\text{joint vel.}} + \underbrace{w_7 \cdot \text{lin\_err}(\phi_t) \cdot \Delta t}_{\text{linear err.}}$$

여기서 $\phi_t = \|\mathbf{e}_t^{rp}\|_2$ (roll/pitch error의 L2 norm), $\Delta t$ = step_dt, $\sigma$ = tracking sigma이다.

### Configuration

| Symbol | ALBCRewardCfg (Base RL) | Description |
|:---|:---|:---|
| $w_1$ | 5.0 | `tracking_weight` |
| $\sigma$ | 0.35 rad | `tracking_sigma` (~20.1 deg 1/e point) |
| $w_2$ | 3.0 | `settling_weight` |
| $\theta_{thr}$ | 0.175 rad | `settling_threshold` (~10 deg) |
| $k$ | 20.0 | `settling_sharpness` (1/rad) |
| $w_3$ | 0.3 | `progress_weight` (NOT dt-scaled) |
| $w_4$ | -2.5 | `joint_oscillation_weight` |
| $w_5$ | -1.0 | `joint_velocity_weight` |
| $w_6$ | 0.0 | `angular_velocity_weight` (disabled) |
| $w_7$ | -1.0 | `linear_error_weight` |
| max_err | 1.0 rad | `linear_error_max` (~57 deg) |
| curriculum ratio | 0.5 | `penalty_curriculum_ratio` |
| $\Delta t$ | 0.005 | `step_dt` (decimation=1, sim dt=0.005) |

**Source**: `mdp/rewards.py` (`ALBCRewardCfg`), `config.py`

### Design Principles

1. **Multi-scale gradient 구조**: 3단계 gradient가 전체 오차 범위를 커버한다.
   - 0-10도: settling (sharpness=20, weight=3.0, 근접 유도)
   - 5-25도: tracking sigma=0.35 (주 correction 범위, 강화된 gradient)
   - 25도+: linear_error (상수 gradient, tail coverage)
2. **Passive equilibrium 방지**: sigma=0.35에서 "do nothing" tracking = 5.0*0.367 = 1.83. 개선 여지 5.0 - 1.83 = 3.17 (sigma=0.5/w=3.0의 1.39 대비 2.28배 증가).
3. **Gaussian kernel 정규화**: $e^{-\phi^2/\sigma^2}$ 형태로 [0, 1] 자연 바운딩. 가중치 해석이 직관적.
4. **dt-scaling 규칙**: "순간 상태 품질" 측정 항 -> dt-scaled, progress (PBRS)는 state transition 기반이므로 NOT dt-scaled.
5. **Penalty curriculum**: 모든 음수 가중치 항(linear_error 포함)이 0->1로 선형 증가. 초기 탐색 보장 후 점진적 규제.
6. **PBRS (Ng 1999)**: potential-based reward shaping으로 optimal policy 보존.

---

## Potential: Definition and Computation

### Attitude Error

로봇의 현재 쿼터니언 $\mathbf{q}$에서 오일러 각도 $(\phi_r, \phi_p, \phi_y)$를 추출하고, 목표 자세 $(\phi_r^*, \phi_p^*, \phi_y^*)$와의 차이를 계산한다:

$$\mathbf{e}_t = \text{atan2}\!\big(\sin(\boldsymbol{\phi}^* - \boldsymbol{\phi}_t),\; \cos(\boldsymbol{\phi}^* - \boldsymbol{\phi}_t)\big) \in [-\pi, \pi]^3$$

`atan2(sin, cos)` wrapping으로 각도 차이가 항상 $[-\pi, \pi]$ 범위에 있도록 보장한다.

**Source**: `base_env.py` (`compute_error`)

### Target Attitude Randomization

목표 자세 $\boldsymbol{\phi}^*$는 환경 설정에 따라 에피소드마다 랜덤화된다:

| Config | `randomize_target_attitude` | 동작 |
|:---|:---|:---|
| `ALBCEnvCfg` (디버그, DR off) | `False` | 고정 $(0, 0, 0)$ |
| `ALBCTrainEnvCfg` (훈련, DR on) | `True` | 에피소드마다 랜덤 |

랜덤화 시 `target_attitude_range = (0.5, 0.5, 0.0)` 범위에서 uniform sampling:

$$\phi_r^* \in [-0.5, +0.5] \text{ rad} \;(\approx \pm28\degree), \quad \phi_p^* \in [-0.5, +0.5] \text{ rad}, \quad \phi_y^* = 0$$

Yaw 목표는 항상 0으로 고정 (range=0.0).

**Source**: `base_env.py` (`reset_targets`), `config.py`

### Potential Value

Attitude error의 **roll, pitch 성분만** L2 norm을 취한 것이 potential이다:

$$\phi_t = \|\mathbf{e}_t^{rp}\|_2 = \sqrt{e_{roll}^2 + e_{pitch}^2}$$

**Yaw를 제외하는 이유**: ALBC는 부력체(buoy)의 위치를 조절하여 roll/pitch 토크를 생성한다. 구조적으로 Z축(yaw) 토크를 만들 수 없으므로, yaw를 보상에 포함하면 해결 불가능한 과제를 부여하는 것이 된다.

**Source**: `base_env.py` (`update_potentials`)

### Update Timing

매 스텝 `_get_rewards()` 진입 시 `update_potentials()`가 정확히 1회 호출된다:

```python
def update_potentials(self, quat: torch.Tensor) -> None:
    self._prev_potentials = self._potentials.clone()
    self._attitude_error = self.compute_error(quat)
    self._potentials = torch.linalg.norm(self._attitude_error[:, :2], dim=-1)
```

### Initialization on Reset

에피소드 리셋 직후 `initialize_potentials()`가 호출된다:

$$\phi_0 = \phi_{-1} = \|\mathbf{e}_0^{rp}\|_2$$

두 값을 동일하게 설정하여 리셋 직후 PBRS progress가 0을 반환한다.

---

## Individual Reward Terms

### Term 1: Tracking Reward (Gaussian Kernel)

$$r_{tracking} = e^{-\phi_t^2 / \sigma^2}, \quad \sigma = 0.35 \text{ rad}, \quad w = 5.0$$

**Source**: `mdp/rewards.py` (`tracking_reward`)

| $\phi_t$ (에러) | $e^{-\phi_t^2/\sigma^2}$ | dt-scaled | weighted |
|:---|:---|:---|:---|
| 0.0 (완벽) | 1.0000 | 0.00500 | 0.02500 |
| 0.035 (~2도) | 0.9900 | 0.00495 | 0.02475 |
| 0.087 (~5도) | 0.9401 | 0.00470 | 0.02350 |
| 0.175 (~10도) | 0.7788 | 0.00389 | 0.01947 |
| 0.262 (~15도) | 0.5698 | 0.00285 | 0.01425 |
| 0.349 (~20도) | 0.3697 | 0.00185 | 0.00924 |
| 0.524 (~30도) | 0.1063 | 0.00053 | 0.00266 |
| 0.700 (~40도) | 0.0183 | 0.00009 | 0.00046 |

$\sigma = 0.35$ rad은 5-25도 범위에서 강한 gradient를 제공한다. 30도에서도 0.106 (유효한 신호 유지). 40도 이상에서는 linear_error가 보완.

**"Do nothing" 분석**: 초기화 ±30도 범위에서 평균 tracking = $5.0 \times 0.367 = 1.83$. 개선 여지 5.0 - 1.83 = 3.17 (sigma=0.5/w=3.0의 1.39 대비 2.28배 증가)로 passive equilibrium 수렴을 강력하게 방지.

### Term 2: Settling Bonus (Sigmoid)

$$r_{settling} = \sigma(k \cdot (\theta_{thr} - \phi_t)), \quad k = 60, \; \theta_{thr} = 0.035 \text{ rad}, \quad w = 2.0$$

**Source**: `mdp/rewards.py` (`settling_bonus`)

| $\phi_t$ (에러) | settling | dt-scaled | weighted |
|:---|:---|:---|:---|
| 0.0 (완벽) | 0.8909 | 0.00445 | 0.00891 |
| 0.017 (~1도) | 0.7311 | 0.00366 | 0.00731 |
| 0.035 (threshold) | 0.5000 | 0.00250 | 0.00500 |
| 0.052 (~3도) | 0.2689 | 0.00134 | 0.00269 |
| 0.070 (~4도) | 0.1091 | 0.00055 | 0.00109 |
| 0.10 (~5.7도) | 0.0180 | 0.00009 | 0.00018 |

Sigma=0.5 tracking이 5-30도를 커버하므로, settling은 0-4도 정밀 제어에 집중한다. sharpness=60에서 2도 근처 max gradient = 60/4 = 15.0 (이전 30/4 = 7.5의 2배).

### Term 3: Progress Reward (PBRS)

$$r_{progress} = \phi_{t-1} - \gamma \cdot \phi_t, \quad \gamma = 0.99, \quad w = 0.3$$

**Source**: `mdp/rewards.py` (`progress_reward_pbrs`)

Ng et al. (1999) potential-based reward shaping으로 optimal policy를 보존한다. NOT dt-scaled. $\gamma$는 PPO discount factor와 일치시켜야 한다 (`ALBCRewardCfg.progress_gamma`).

Error 감소 시 양수 보상 제공:
- $\phi_{t-1} = 0.30, \; \phi_t = 0.28$: $r = 0.30 - 0.99 \cdot 0.28 = 0.0228 \to w \cdot r = 0.0068$
- Error 증가 시 음수로 전환, 자연스러운 gradient 제공

Off-policy (SAC) replay buffer에서도 안전하게 사용 가능. 대안으로 `progress_reward` (tanh 기반)가 있으나, PBRS가 이론적 보장이 강하다.

### Term 4: Joint Oscillation Penalty (EMA High-Pass)

$$r_{osc} = \text{mean}((\dot{\gamma} - \text{EMA}(\dot{\gamma}))^2), \quad \alpha_{EMA} = 0.2, \quad w = -2.5$$

**Source**: `mdp/rewards.py` (`joint_oscillation_penalty`)

EMA가 저주파 성분을 추적하고, 차이(고주파 잔차)를 제곱 페널티로 부과한다. 부드러운 움직임은 허용하면서 고주파 진동만 선택적으로 억제한다.

$\alpha = 0.2$는 50Hz 제어 주파수에서 약 1.6Hz cutoff에 해당한다.

### Term 5: Joint Velocity Penalty

$$r_{vel} = \text{mean}(\dot\gamma^2), \quad w = -1.0$$

**Source**: `mdp/rewards.py` (`joint_velocity_penalty`)

관절 속도의 제곱 평균 페널티. 빠른 관절 운동을 억제하여 제어 안정성과 에너지 효율을 향상시킨다. Joint oscillation (고주파만)과 달리 모든 관절 속도를 페널티 대상으로 한다.

### Term 6: Angular Velocity Penalty

$$r_{angvel} = \sum_{i \in \{p, q\}} \omega_i^2, \quad w = -1.5$$

**Source**: `mdp/rewards.py` (`angular_velocity_penalty`)

Roll/pitch 각속도(body frame)의 제곱합. Yaw는 제어 불가능하므로 제외. `sum` (not `mean`) 사용: 축 수가 2로 고정이므로 결과 동일하나, 총 각속도 크기에 비례하는 penalty를 명시적으로 표현.

DR 환경에서 강한 외란 하에 과도한 각속도 진동을 억제한다. 가중치 -1.5는 tracking(3.0)의 절반으로, ang_vel > 0.7 rad/s에서도 tracking gradient를 완전히 억압하지 않도록 조정되었다 (이전 -3.0에서 하향 조정).

### Term 7: Linear Error Penalty

$$r_{lin} = \min(\phi_t / \phi_{max}, \; 1.0), \quad \phi_{max} = 1.0 \text{ rad}, \quad w = -1.0$$

**Source**: `mdp/rewards.py` (`linear_error_penalty`)

큰 오차(>30도)에서 Gaussian tracking의 gradient가 소멸할 때 **상수 gradient**를 제공한다. 출력 [0, 1], max_err에서 clamped.

| $\phi_t$ (에러) | raw | dt-scaled | weighted (full curriculum) |
|:---|:---|:---|:---|
| 0.087 (~5도) | 0.087 | 0.00044 | -0.00044 |
| 0.175 (~10도) | 0.175 | 0.00088 | -0.00088 |
| 0.349 (~20도) | 0.349 | 0.00175 | -0.00175 |
| 0.524 (~30도) | 0.524 | 0.00262 | -0.00262 |
| 0.785 (~45도) | 0.785 | 0.00393 | -0.00393 |
| 1.0 (= max_err) | 1.000 | 0.00500 | -0.00500 |

Gradient = $1/\phi_{max}$ = 1.0/rad으로 **모든 오차 수준에서 일정**. Penalty curriculum에 따라 0->1 ramp되므로 초기에는 비활성, 점진적으로 강화된다. Tracking과 같은 방향으로 작용 (둘 다 오차 감소 유인).

---

## Multi-Scale Gradient Design

3단계 gradient 구조로 전체 오차 범위를 커버한다:

```
오차 0도 ----[settling]---- 4도 ----[tracking sigma=0.35]---- 25도+ ----[linear_error]----
          precision band         main correction range           tail coverage
          (sharpness=20)         (2.77x stronger gradient)       (constant gradient)
```

| 범위 | 주 gradient 원천 | 특성 |
|:---|:---|:---|
| 0-4도 | settling (k=20) | max gradient 5.0/rad, 정밀 수렴 |
| 4-25도 | tracking (sigma=0.35) | Gaussian gradient, 강화된 주 correction |
| 25도+ | linear_error | 상수 1.0/rad, tail coverage |

---

## Penalty Curriculum

모든 음수 가중치 항에 선형 ramp curriculum이 적용된다:

$$w_{eff}(i) = w_{full} \cdot \min(1, \; i / i_{end})$$

| Parameter | Value |
|:---|:---|
| `penalty_curriculum_ratio` | 0.5 |
| Applies to | `joint_oscillation`, `joint_velocity`, `angular_velocity`, `linear_error` (all negative-weight terms) |
| Scale at iter 0 | 0.0 (penalties disabled) |
| Scale at 50% of max_iter | 1.0 (full penalties) |

### Implementation

`RewardManager.update_curriculum(iteration)` 메서드에서 `penalty_scale`을 갱신한다. `compute()` 내부에서 `weight < 0`인 항에만 scale을 곱한다:

```python
if weight < 0:
    scaled_value = scaled_value * self._penalty_scale
```

Runner의 `log()` 메서드에서 매 iteration 호출:
```python
raw_env._reward_manager.update_curriculum(iteration)
```

초기 학습에서 penalty 없이 자유롭게 탐색하고, 점진적으로 규제를 강화하여 smooth하고 에너지 효율적인 행동으로 수렴한다.

---

## Scale Balance Analysis

### Expected Per-step Balance (15s episode)

#### Base RL (error ~ 15 deg = 0.262 rad, hf ~ 0.5 rad/s, full curriculum)

| Term | Raw | Weight | dt | Per-step | Share |
|:---|:---|:---|:---|:---|:---|
| tracking | 0.570 | 5.0 | 0.005 | **+0.01425** | **53%** |
| settling | ~0.045 | 3.0 | 0.005 | +0.00067 | 2.5% |
| progress | ~0.01 | 0.3 | no | +0.00300 | 11% |
| joint_oscillation | ~0.25 | -2.5 | 0.005 | -0.00312 | 12% |
| joint_velocity | ~0.04 | -1.0 | 0.005 | -0.00020 | 0.7% |
| angular_velocity | - | 0.0 | 0.005 | 0 | 0% |
| linear_error | 0.262 | -1.0 | 0.005 | -0.00131 | 5% |
| **Net** | | | | **+0.01329** | |

Positive 항(tracking+settling+progress=67%)이 지배. Sigma=0.35에서 tracking gradient가 sigma=0.5 대비 2.77배 강화. 15도->10도 이동의 marginal benefit이 양수(+0.00207)로 전환되어 적극적 수렴을 유도.

### Episode Budget (15s, normalized per second, full curriculum)

| Error | Tracking/s | Settling/s | Linear err/s | Penalties/s | Total/s |
|:---|:---|:---|:---|:---|:---|
| 2 deg | +4.95 | +1.00 | -0.09 | -0.35 | **+5.51** |
| 5 deg | +4.70 | +0.04 | -0.17 | -0.35 | **+4.22** |
| 10 deg | +3.89 | ~0 | -0.35 | -0.35 | **+3.19** |
| 15 deg | +2.85 | ~0 | -0.52 | -0.35 | **+1.98** |
| 20 deg | +1.85 | ~0 | -0.70 | -0.35 | **+0.80** |
| 30 deg | +0.53 | ~0 | -1.05 | -0.35 | **-0.87** |
| 45 deg | +0.03 | ~0 | -1.57 | -0.35 | **-1.89** |

Sigma=0.35 + weight=5.0에 의해 15도에서도 강한 양수 보상(+1.98/s)을 유지. 20도 이상에서 급감하고, 25도 이상에서 음수 진입. 초기화 범위(±30도) 끝에서도 linear_error가 gradient를 제공.

### Key Observations

1. **Multi-scale gradient**: tracking(sigma=0.35, w=5.0)이 5-25도를 강하게 커버, settling이 0-4도를 커버, linear_error가 25도+ tail을 커버. 전 범위에서 gradient dead zone 없음.
2. **Passive equilibrium 해소**: "do nothing" 기대 보상 1.83 (w=5.0*0.367), 개선 여지 3.17로 이전(1.39) 대비 2.28배 증가.
3. **Marginal benefit 양수 전환**: 15도->10도 이동 시 tracking 증가(+0.00519)가 osc cost(-0.00312)를 초과. Net marginal +0.00207/step으로 적극적 수렴 유도.
4. **Joint oscillation penalty 절반**: -2.5 (이전 -5.0)로 축소. 여전히 원래(-1.0)의 2.5배이나, tracking과의 balance에서 움직임 penalty가 지배하지 않음.
5. **Episode reward 정규화**: `_collect_episode_metrics()`에서 `/ max_episode_length_s`로 나누어 episode 길이에 무관한 per-second 평균을 로깅.

---

## Reward Manager Architecture

### Pipeline

```
_get_rewards() [base_env.py]
    |
    +-- update_potentials()              # prev <- current, recompute current
    |
    +-- RewardManager.compute()           # iterate active terms
            |
            +-- tracking_reward()            --> * weight * dt
            +-- settling_bonus()             --> * weight * dt
            +-- progress_reward_pbrs()       --> * weight (no dt)
            +-- joint_oscillation_penalty()  --> * weight * dt * penalty_scale
            +-- joint_velocity_penalty()     --> * weight * dt * penalty_scale
            +-- angular_velocity_penalty()   --> * weight * dt * penalty_scale
            +-- linear_error_penalty()       --> * weight * dt * penalty_scale
            |
            +-- accumulate to _episode_sums
            |
            +-- return total_reward
```

### Zero-Weight Optimization

`RewardManager.__init__`에서 `weight=0.0`인 항은 `_term_cfgs`에 등록되지 않는다. 특정 보상 항을 config에서 0으로 설정하면 자동으로 비활성화된다.

### Environment-Specific Registration

`_build_reward_terms()`에서 config의 각 가중치를 확인하고 0이 아닌 항만 등록한다:

| Environment | Active Terms |
|:---|:---|
| RL (`Isaac-FullDOF-TRPO-v0`) | 7개 (tracking, settling, progress, joint_osc, joint_vel, ang_vel, linear_error) |
| TDC (`Isaac-FullDOF-TDC-v0`) | 7개 base + mhat_accuracy, tdc_torque (if weight != 0) |

TDC 환경에서 `tdc_env._build_reward_terms()`가 base를 상속 + 확장한다.

### Logging Integration

`RewardManager.reset(env_ids)` 호출 시 리셋되는 환경들의 에피소드 합 평균을 반환한다. `base_env._collect_episode_metrics()`를 통해 WandB/TensorBoard에 **per-second 평균으로 정규화**되어 기록된다:

```python
log[f"Episode_Reward/{name}"] = value / self.max_episode_length_s
```

로깅 항목:
- `Episode_Reward/tracking`
- `Episode_Reward/settling`
- `Episode_Reward/progress`
- `Episode_Reward/joint_oscillation`
- `Episode_Reward/joint_velocity`
- `Episode_Reward/angular_velocity`
- `Episode_Reward/linear_error`

---

## Comparison with Reference Implementations

### Isaac Gym Reference (`references/isaacgym_agent/tasks/heroagent.py`)

```python
# line 770
pose_reward = 8 * torch.exp(-potentials)

# line 766
progress_reward = potentials - prev_potentials

# line 776
total_reward = pose_reward + progress_reward - 2 * actions_cost_scale * actions_cost
```

| 항목 | Isaac Gym | Isaac Lab (현재) |
|:---|:---|:---|
| Tracking | $8 \cdot e^{-\phi}$ (Laplacian) | $5.0 \cdot e^{-\phi^2 / \sigma^2}$ (Gaussian, $\sigma=0.35$) |
| Progress | $\phi_{t-1} - \phi_t$ (raw delta) | $\phi_{t-1} - \gamma \phi_t$ (PBRS, $\gamma=0.99$) |
| Settling | 없음 | $3.0 \cdot \sigma(20 \cdot (0.175 - \phi))$ |
| Linear error | 없음 | $-1.0 \cdot \min(\phi/1.0, 1.0)$ |
| Action cost | $-2 \cdot \|a\|^2$ | 없음 (제거됨) |
| Alive reward | 0.5/step | 없음 |
| Joint oscillation | 없음 | $-2.5 \cdot \text{EMA-HP}(\dot\gamma)^2$ |
| Joint velocity | 없음 | $-1.0 \cdot \|\dot\gamma\|^2$ |
| Angular velocity | 없음 | $0.0 \cdot \|\omega_{rp}\|^2$ (disabled) |
| dt scaling | 없음 | 상태 품질 항에 적용 |
| Curriculum | 없음 | 모든 penalty, ratio=0.5 ramp |

**Kernel 비교**: Isaac Gym의 Laplacian $e^{-|\phi|}$는 모든 오차에서 일정한 gradient (-1)를 제공하여 학습이 안정적이었다. Isaac Lab의 Gaussian $e^{-\phi^2/\sigma^2}$은 원점 근처 gradient가 0에 수렴하나 (settling으로 보완), sigma=0.5로 중간 범위 gradient를 강화하고 linear_error로 tail을 보완하여 전 범위 coverage를 달성.

### Cross-Environment Comparison

| Environment | Positive Weights | Penalty Weights | Pos:Neg Ratio |
|:---|:---|:---|:---|
| AnymalC | +1.0 | -0.05, -0.01, -2.5e-5, -2.5e-7 | ~100:1 |
| Quadcopter | +15.0 | -0.05, -0.01 | ~300:1 |
| Hero Agent | **+5.0, +3.0, +0.3** | **-2.5, -1.0, -1.0** | **~2.3:1** |

Hero Agent의 pos:neg 비율(~2.3:1)이 다른 환경 대비 낮지만, 이는 의도적 설계이다. UUV의 강한 DR(added mass +-50% 등) 환경에서 penalty가 과도한 진동을 억제하면서도, tracking weight 강화(5.0)로 적극적 수렴의 marginal benefit을 보장한다.

---

## Design Considerations

### Strengths

1. **Multi-scale gradient**: 전 오차 범위에서 gradient dead zone 없음. Settling(정밀), tracking(중간), linear_error(tail) 3단계 coverage.
2. **Passive equilibrium 방지**: sigma=0.35/w=5.0에서 개선 여지 3.17, 이전(sigma=0.5/w=3.0, 1.39) 대비 2.28배 증가.
3. **dt-invariant**: 적절한 dt 스케일링으로 `decimation` 변경 시 재튜닝 불필요.
4. **Episode-length-independent logging**: `/ max_episode_length_s` 정규화로 생존 시간에 무관한 quality 비교 가능.
5. **PBRS 이론적 보장**: optimal policy 보존, off-policy safe.
6. **Penalty curriculum**: 초기 탐색 보장 -> 점진적 규제 -> 최종 smooth control.

### Known Limitations

1. **30도+ tracking 급감**: sigma=0.35에서 30도 tracking = 0.106, 40도 = 0.018. Linear_error가 보완하지만, sigma=0.3(30도에서 0.047)보다 의도적으로 넓은 sigma를 선택하여 초기화 범위(±30도)에서 유효한 gradient를 유지.
2. **Angular velocity penalty 비활성화**: joint_velocity + joint_oscillation으로 충분히 커버 가능하여 제거됨 (0.0).
3. **Progress weight 상대적 약함**: 0.3 weight는 tracking(5.0)의 1/17. PBRS의 이론적 장점에도 불구하고 실제 gradient 기여가 작을 수 있음.

---

## Related Notes

- [tdc-control-law.md](tdc-control-law.md): TDC 제어기 구조 및 제어 법칙 유도 (보상과 독립)
- [domain-randomization.md](../how-to/domain-randomization.md): Domain Randomization 설정 (보상 robustness에 영향)

---
**Created**: 2026-02-11
**Updated**: 2026-03-01 (Reward tuning: tracking_weight 3.0->5.0, tracking_sigma 0.5->0.35, joint_oscillation -5.0->-2.5, penalty_curriculum_ratio 0.75->0.5. Marginal benefit 15->10deg now positive.)
