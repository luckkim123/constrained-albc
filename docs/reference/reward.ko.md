# Reward 시스템 (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 전체 reward 계산 — 공유 tracking
> 커널, `RewardManager`가 매 step 합산하는 6개의 가중 항, 그것들을 먹이는
> `albc_env.py`의 error 버퍼, 그리고 shipped reward를 실제로 돌아가는 형태로
> 바꾸는 config override. 이것은 attitude-only ALBC env(roll/pitch + yaw-rate
> 명령, 선속도 명령 없음)이며, reward는 `dt`-스케일되고 tracking reward(양수)와
> penalty(음수 가중)로 나뉜다.
>
> 디스크에 대해 검증된 code-level 레퍼런스다. `thruster_energy` /
> `action_smoothness`가 penalize하는 8D action 경로를 다루는
> `action-pipeline.md`의 **reward 쪽 짝 문서**이며, encoder / actor / critic,
> ConstraintTRPO 업데이트, 그리고 이 reward 항들과는 *별개 채널*인 cost-critic
> constraint를 다루는 `main-network-architecture.md`의 짝이기도 하다. 어떤 주제
> (constraint, DORAEMON curriculum, action clamp)가 그 문서들에 속하면 여기서는
> 반복하지 않고 링크로 넘긴다.
>
> **두 채널을 혼동하지 말 것.** 이 문서는 `RewardManager`가 합산하는 **scalar
> reward**를 다룬다. ConstraintTRPO+IPO barrier를 구동하는 **per-constraint
> cost**(`compute_all_costs`, `mdp/constraints.py`)는 별개 신호다 —
> `main-network-architecture.md` §4–5 참조. 둘은 error 버퍼(§6)를 공유할 뿐
> 그 외에는 아무것도 공유하지 않는다.

---

## 1. 개요

한 control step의 reward는 **6개 항의 `dt`-스케일 가중합**이다.
`RewardManager.compute()`(`rewards.py:194-212`)가 합을 만든다; 모든 항은
초당 가중치와 `dt = step_dt = 0.02 s`를 곱한 뒤 더해지므로, 보고되는 `k` 값은
초당 값이고 실효 per-step 기여는 `k * 0.02`다(§6, §7).

```
_get_rewards()                                          (albc_env.py:1036)
  1. _compute_ang_errors()          -> _att_rp_err, _yaw_rate_err   (albc_env.py:1027-1035)
  2. leaky integral update  (OBS, not reward; gated by reward sigma) (albc_env.py:1045-1065)
  3. bias-EMA update        (only if k_bias != 0)                    (albc_env.py:1067-1079)
  4. reward = RewardManager.compute(robot, dt=step_dt, env)         (albc_env.py:1081-1085)
       for name, weight, value in terms:                            (rewards.py:207)
           scaled   = value * weight * dt
           reward  += scaled
           episode_sums[name] += scaled
  5. reward += reset_terminated * termination_penalty  (if != 0; NOT dt-scaled) (albc_env.py:1088-1089)
  6. constraint costs -> extras["costs"]   (separate channel)       (albc_env.py:1092-1093)
  7. _episode_return_accum += reward        (DORAEMON success feed)  (albc_env.py:1101-1102)
```

6개 항(`RewardManager._NAMES`, `rewards.py:185`)은 두 개의 **tracking
reward**(양수, §2의 공유 exp-커널 위에 세워짐)와 네 개의 **penalty**(음수
가중치로 합에 실려 들어가는 non-negative magnitude)로 나뉜다:

| Class | Terms |
|---|---|
| Tracking (reward) | `att_rp`, `yaw_vel` |
| Penalty | `torque`, `thruster`, `smoothness`, `bias` |

`att_rp`와 `yaw_vel`은 이 attitude-only env의 유일한 두 tracking 함수다;
`lin_vel_tracking`은 여기 없다(그 함수는 형제 `envs/full_dof/mdp/rewards.py`에만
존재한다, §9). 일곱 번째 reward 기여인 `termination_penalty`는 `compute()`
바깥에서 적용되며 6개의 tracked/logged 항에 **속하지 않는다**(§9).

---

## 2. 공유 tracking 커널 — `_exp_quad_saturating`

두 tracking 함수 모두 하나의 커널 `_exp_quad_saturating(err_sq, err_norm,
term)`(`rewards.py:109-129`)을 호출한다. 이것은 양의 Gaussian bump에 최대 세 가지
penalty shape을 결합하는 순수 함수다:

```
exp_term = exp(-err_sq / (2 * sigma^2))                                    (rewards.py:121)
penalty  = quad_ratio * err_sq + lin_ratio * err_norm                      (rewards.py:122)
if tanh_coef  > 0:  penalty += tanh_coef  * tanh_eps  * tanh(err_norm/tanh_eps)              (rewards.py:123-124)
if arctan_coef> 0:  penalty += arctan_coef* arctan_eps* (2/pi)*atan(err_norm/arctan_eps)     (rewards.py:125-128)
return exp_term - penalty                                                   (rewards.py:129)
```

$$
r_{\text{kernel}} = \underbrace{\exp\!\left(-\frac{e^2}{2\sigma^2}\right)}_{\text{reward, }(0,1]} \;-\; \underbrace{q_{\text{quad}}\, e^2}_{\text{quadratic}} \;-\; \underbrace{q_{\text{lin}}\, |e|}_{\text{linear (default 0)}} \;-\; \underbrace{c_{\tanh}\,\epsilon_{\tanh}\tanh\!\left(\tfrac{|e|}{\epsilon_{\tanh}}\right)}_{\text{tanh, only if } c_{\tanh}>0} \;-\; \underbrace{c_{\text{atan}}\,\epsilon_{\text{atan}}\tfrac{2}{\pi}\arctan\!\left(\tfrac{|e|}{\epsilon_{\text{atan}}}\right)}_{\text{arctan, only if } c_{\text{atan}}>0}
$$

여기서 $e^2$는 `err_sq`(인자, *가중* 제곱합일 수 있음 — §4.1)이고 $|e|$는
`err_norm`(caller에 따라 Manhattan-weighted이거나 진짜 Euclidean magnitude —
§4)이다. per-term 가중치 `k`는 커널 **내부에서** 적용되지 않는다
(`rewards.py:109-129`에 `term.k` 참조가 없다); 나중에 `compute()`가 곱한다(§6).
`TrackingTermCfg` docstring의 공식 `r = k * (exp(...) - ...)`
(`rewards.py:58`)는 함수가 실제로는 적용하지 않는 `k`를 접어 넣은 것이며 — 그
`k`는 caller가 뒤이어 곱하는 값이다.

### 2.1 shape별 gradient 직관

| Shape | Value at `e=0` | Gradient at `e=0` | Tail | Role |
|---|---|---|---|---|
| `exp(-e^2/2s^2)` | `1` (max) | `0` | saturates to 0 | positive reward; slope peaks at `|e|=sigma`, vanishes near 0 |
| `quad_ratio * e^2` | `0` | `0` | grows unbounded | penalty that dominates for large error |
| `lin_ratio * |e|` | `0` | `lin_ratio * sign(e)` (constant) | grows linearly | constant force even near 0 — **but default 0, see §2.2** |
| `tanh` penalty | `0` | `c_tanh` (finite) | sech²-decay (exponential) | smoothed near-0 force, bounded tail |
| `arctan` penalty | `0` | `c_atan * 2/pi ≈ 0.637 c_atan` | 1/(1+x²)-decay (heavier) | smoothed near-0 force, Cauchy-like tail |

exp 항은 $(0,1]$에서 양수이고 $e=0$에서 최대(`test_*_peaks_at_zero`,
`tests/test_rewards.py:114,128,128` — §10.1 참조)이며; 그 slope
$-\tfrac{e}{\sigma^2}\exp(-e^2/2\sigma^2)$는 $|e|=\sigma$에서 최대이고 $e=0$
근처에서 0으로 붕괴한다. 따라서 exp와 quadratic gradient 모두 **`e -> 0`에서
소멸**하며, 이를 모듈 docstring은 "dead zone"(`rewards.py:18-23`)이라
부른다: 정책이 대략 $\sigma$ 안에 들어오면 어느 항도 더 이상 error를 0으로
밀도록 reward하지 않는다. saturating tanh/arctan penalty(그리고 비활성 linear
penalty)는 raw linear 항이 갖는 무한대에서의 unbounded force 없이 $e=0$에서
유한한 non-vanishing gradient를 복원하려고 존재한다.

커널은 `exp_term - penalty`를 반환하며 penalty가 exp bump를 넘으면 **음수가 될 수
있다**; tracking 항은 peak-at-1과 monotonic-decrease만 테스트되고 non-negativity는
테스트되지 않는다(§10).

### 2.2 `lin_ratio` dead-zone 함정 — 설계상 해소됨

`lin_ratio`는 기본값이 `0.0`(`rewards.py:79`, 주석 `# linear penalty ratio
(disabled: caused dead zone)`)이고 **어디에서도 nonzero로 설정되지 않는다** —
두 `TrackingTermCfg` 생성(`rewards.py:90,92`)도, config
override(`config.py:439`)도 이를 넘기지 않는다. 그래서 shipped config에서 linear
penalty는 두 tracking 항 모두에서 무력하다.

이것은 예전에 `rewards.py` 내부의 자기모순처럼 읽혔다: 모듈 docstring은 한때 linear
항을 SS-error의 fix로 서술했고, 필드 주석은 그것이 dead zone을 유발해서
비활성화됐다고 말했다. docstring은 이제 화해됐다(`rewards.py:14-23`): linear
penalty는 SS-error dead zone에 대한 시도된 fix**였지만**, 그 자체의 dead zone을
유발해 모든 곳에서 비활성화됐다(`lin_ratio=0`); 실제 완화책은 `yaw_vel` 하나에만
걸린 saturating tanh penalty다(`config.py:439`, `tanh_coef=0.3`). `att_rp`에는
saturating 항이 없으므로 그 SS-error dead zone은 남아있다 — 이는 미해소 모순이
아니라 문서화된, 의도된 gap이다.

### 2.3 tanh vs arctan: 코드가 아니라 관례로 강제됨

두 saturating 블록은 **독립적인 `if` 문**(`rewards.py:123`과 `:125`)이다; 두 계수
모두 양수라면 둘 다 fire되는 것을 막는 것은 없으며 — 그러면 additively 쌓일
것이다. docstring의 *"tanh/arctan 중 한 번에 하나만"*(`rewards.py:63-73`)은
config-authoring 관례이지 코드 불변식이 아니다. shipped config에서는 `tanh_coef`만
nonzero이고, `yaw_vel`에서만 그렇다(`config.py:439`); `arctan_coef`는 결코 설정되지
않는다(§3, §4). docstring은 `arctan`을 tanh의 **kept-but-unused** heavy-tail
대안으로 명시적으로 서술한다 — 더 긴 reach의 saturating 항이 필요한 미래 실험
(예: §2.2의 `att_rp` dead zone을 채우는 것)의 후보이지, dead code가 아니다.

---

## 3. 항별 카탈로그

`RewardManager._NAMES = ["att_rp", "yaw_vel", "torque", "thruster",
"smoothness", "bias"]`(`rewards.py:185`) — 6개 항이며,
`compute()`의 `terms` 리스트(`rewards.py:199-206`)에서 1:1로 조립된다.

| # | Name | Function (`rewards.py`) | Formula (pre-weight, pre-dt) | Weight field | Dataclass default | Shipped value | On? |
|---|---|---|---|---|---|---|---|
| 1 | `att_rp` | `att_rp_tracking` (132-142) | `exp(-e_w²/2σ²) − q·e_w²` where `e_w² = 1.5·roll² + pitch²` | `att_rp.k` | `k=9.0, σ=0.10, quad=0.833` (90) | unchanged | **ON** (reward) |
| 2 | `yaw_vel` | `yaw_vel_tracking` (145-148) | `exp(-e²/2σ²) − q·e² − tanh_coef·ε·tanh(|e|/ε)` | `yaw_vel.k` | `k=3.5, σ=0.10, quad=1.0` (92) | **override**: `+tanh_coef=0.3, tanh_eps=0.10` (config.py:439) | **ON** (reward + tanh penalty) |
| 3 | `torque` | `joint_torque` (151-153) | `mean(applied_torque[albc_joints]²)` | `k_tau` | `-0.01` (93) | unchanged | ON |
| 4 | `thruster` | `thruster_energy` (156-158) | `mean(actions[:, 2:]²)` (6 thruster dims) | `k_thr` | `-0.35` (94) | unchanged | ON |
| 5 | `smoothness` | `action_smoothness` (161-165) | `mean(da²) + mean(d2a²)` over all 8 dims | `k_s` | `-0.1` (95) | unchanged | ON |
| 6 | `bias` | `bias_ema_penalty` (168-176) | `Σᵢ wᵢ · bias_emaᵢ²` (3D roll/pitch/yaw-rate) | `k_bias` | `0.0` — disabled (100) | **override**: `-2.0` (config.py:445) | **ON** (override) |

### 3.1 Shipped 실효 가중치 표 (definitive)

`ALBCRewardCfg`의 10개 필드 중 **정확히 두 개**만 shipped config가 건드린다
(`config.py:438-446`): `yaw_vel`(tanh penalty를 얻음)과 `k_bias`(`-2.0`에서 켜짐).
나머지 전부는 `rewards.py` dataclass 기본값으로 돌아간다.

| Field | Dataclass default (`rewards.py`) | Config override (`config.py:438-446`) | Shipped effective value | Overridden? |
|---|---|---|---|---|
| `att_rp` | `k=9.0, σ=0.10, quad_ratio=0.833` (90) | — | `k=9.0, σ=0.10, quad=0.833, lin=0, tanh=0, arctan=0` | No |
| `att_roll_weight` | `1.5` (91) | — | `1.5` | No |
| `yaw_vel` | `k=3.5, σ=0.10, quad=1.0` (92) | `+tanh_coef=0.3, tanh_eps=0.10` (439) | `k=3.5, σ=0.10, quad=1.0, tanh=0.3, tanh_eps=0.10` | **Yes** |
| `k_tau` | `-0.01` (93) | — | `-0.01` | No |
| `k_thr` | `-0.35` (94) | — | `-0.35` | No |
| `k_s` | `-0.1` (95) | — | `-0.1` | No |
| `termination_penalty` | `0.0` (96) | — | `0.0` (disabled) | No |
| `k_bias` | `0.0` (100) | `-2.0` (445) | `-2.0` (term ON) | **Yes** |
| `bias_ema_alpha` | `0.99` (101) | — | `0.99` (~100-step / 2 s window at 50 Hz) | No |
| `bias_weights` | `(1.5, 1.0, 1.0)` (103) | — | `(1.5, 1.0, 1.0)` | No |

`yaw_vel` override는 부분 패치가 아니라 중첩된 `TrackingTermCfg`의 **완전
재구성**이다 — `k`, `sigma`, `quad_ratio`가 기본값 그대로 재기술되므로, 유일한
*실질적* 변경은 tanh 항을 켜는 것뿐이다. `att_rp`, `lin_ratio`,
`arctan_coef`는 모두 손대지 않은 채 dataclass 기본값을 유지한다.

### 3.2 error가 0일 때의 실효 per-step magnitude

`dt = 0.02`(§6)에서, error가 0일 때 tracking 커널은 `1.0`이므로 `att_rp`는 step당
`9.0 * 0.02 * 1 = 0.18`을 기여하고 `yaw_vel`은 step당 `3.5 * 0.02 * 1 = 0.07`을
기여한다($\tanh(0)=0$이므로 정확히 $e=0$에서 tanh penalty는 0이다). 50 Hz에서
30 s episode(`episode_length_s=30.0`, `config.py:350`; 1500 step) 동안 `att_rp`만
매 step error 0이면 `0.18 * 1500 = 270`이 누적되며 — 이는 DORAEMON
`performance_lb=250.0` 캘리브레이션(§8)과 일치한다.

---

## 4. 두 tracking 항

### 4.1 `att_rp_tracking` — roll-weighted, saturating용 Manhattan norm

`att_rp_tracking`(`rewards.py:132-142`)은 두 개의 error aggregate를 만들어 커널에
넘긴다:

```python
rp_err    = env._att_rp_err                                             # (N, 2): [roll_err, pitch_err]
err_sq    = cfg.att_roll_weight * rp_err[:, 0].pow(2) + rp_err[:, 1].pow(2)     # weighted sum of squares
err_abs_w = cfg.att_roll_weight * rp_err[:, 0].abs() + rp_err[:, 1].abs()       # Manhattan (L1) weighted
return _exp_quad_saturating(err_sq, err_abs_w, cfg.att_rp)
```

$$
e_w^2 = w_{\text{roll}}\, e_{\text{roll}}^2 + e_{\text{pitch}}^2, \qquad |e_w| = w_{\text{roll}}\, |e_{\text{roll}}| + |e_{\text{pitch}}|
$$

`err_sq`는 exp와 quadratic 항을 먹이고; `err_abs_w`는 절댓값의 Manhattan(L1)
가중합이며 — Euclidean `sqrt(err_sq)`가 **아니다** — `err_norm`, 즉 (여기서
비활성인) linear/tanh/arctan penalty를 먹인다. roll은 *두* aggregate 모두에서
`att_roll_weight = 1.5`(`rewards.py:91`)로 up-weight되므로, roll error가 단위당
pitch보다 더 비싸다(`test_att_rp_roll_weighted_more_than_pitch`,
`tests/test_rewards.py:120`로 고정). shipped config에서 `att_rp`에는 saturating도
linear penalty도 활성이 아니므로(§3.1), `att_rp`는 순수하게
`exp − quad_ratio·e_w²`로 돌아간다.

**roll에 1.5배를 주는 이유.** 이 가중치는 단독 heuristic이 아니라 shipped
Thruster Allocation Matrix에 근거한다: `_BASE_ALLOCATION_MATRIX`
(`config.py:77-84`, ALBC ROS control package `config/TAM.yaml`에서 유래)는
roll(Mx) 행에 moment-arm 계수 `0.007`(`config.py:81`)을, pitch(My) 행의
수직-쌍 계수 `0.145`(`config.py:82`)를 부여한다 — roll moment arm이 ~20배 더 작다.
두 번째 확증은 payload-DR 주석 `4 x 50 N x 0.007 m = 1.4 Nm`의 roll
권한(`config.py:207-212`)이다. roll 축은 실제로 약하게 구동되므로, 그 tracking
error가 penalize되기 전에 up-weight된다(주석 `rewards.py:91`: "weak TAM
actuation: 0.007m vs pitch 0.145m").

### 4.2 `yaw_vel_tracking` — scalar, shipped config의 유일한 saturating 항

`yaw_vel_tracking`(`rewards.py:145-148`)은 scalar yaw *rate* error를 추적한다(yaw
각도가 아님):

```python
err = env._yaw_rate_err
return _exp_quad_saturating(err.pow(2), err.abs(), env.cfg.reward.yaw_vel)
```

가중치 없음: `err_sq = err²`, `err_norm = |err|`. dataclass
기본값(`rewards.py:92`)에는 saturating 항이 없지만, shipped
config(`config.py:439`)가 `yaw_vel`을
`TrackingTermCfg(k=3.5, sigma=0.10, quad_ratio=1.0, tanh_coef=0.3, tanh_eps=0.10)`
로 override한다 — `k`/`sigma`/`quad_ratio`는 동일하고 tanh penalty가 추가된다.
**`yaw_vel`은 활성 saturating penalty를 지닌 유일한 tracking 항이다**; 그 penalty
하나만으로 error 0에서의 gradient는 $c_{\tanh}=0.3$이다. 이는 yaw rate에서는 dead
zone(§2.2)을 부분적으로 채우지만 roll/pitch에서는 그렇지 않다.

이 파일에는 `lin_vel_tracking` 함수가 없다 — 이 attitude-only env는 선속도
명령을 가진 적이 없으며, 레거시 shape 호환을 위해 존재하던 dead
`lin_vel_tracking` 함수 + `ALBCRewardCfg.lin_vel` 필드는 2026-07에
제거됐다(§9). 형제 `envs/full_dof/mdp/rewards.py`(레거시 full-DOF env를 위한
별개의 hand-fork 파일)는 여전히 `lin_vel_tracking`을 자신의
`RewardManager`에 연결하고 있다 — 이는 이번 정리와 무관한 별개 모듈이다.

---

## 5. penalty 항들

네 개의 활성 penalty 모두 **non-negative magnitude**를 반환한다; 음의 부호는
전적으로 가중치(`k_tau`, `k_thr`, `k_s`, `k_bias`)에 있다. 모든 penalty는 tracking
항과 동일하게 `dt`-스케일된다(§6) — 6개 항 전부에 대해 스케일링 지점은 하나다.

### 5.1 `joint_torque` — post-clamp applied torque

`joint_torque`(`rewards.py:151-153`): `mean(applied_torque[albc_joints]²)`.
`robot.data.applied_torque`를 읽는데 — Isaac Lab의 **post-actuator-model,
post-clamp**로 실제 적용된 torque이지 정책의 raw commanded action이 아니다(인라인
주석 `rewards.py:152`: "post-clamp applied torque"). 이것이 raw action magnitude를
penalize한다고 가정한 독자는 틀린다: 이것은 actuator dynamics, effort-limit
clamping, DR-무작위화된 effort-limit 스케일링(`action-pipeline.md` §4.2) 이후
물리적으로 실현된 torque를 penalize한다. effort limit을 낮추는 joint fault
injection은 따라서 같은 commanded action에 대해서도 이 penalty를 *낮출* 수 있다.

### 5.2 `thruster_energy` — 6개 thruster 차원만

`thruster_energy`(`rewards.py:156-158`): `mean(env._actions[:, 2:]²)`. action
레이아웃은 `[2D arm delta, 6D thruster]`(`action-pipeline.md` §2)이므로, `[:, 2:]`
슬라이싱은 6개 thruster 차원(인덱스 2-7)을 취하고 **2개 arm 차원은 제외한다**.
`test_thruster_energy_uses_thruster_action_slice`(`tests/test_rewards.py:143`)로
고정: 8D action `[9,9,1,0,0,0,0,0]`는 `mean([1,0,0,0,0,0]²) = 1/6`을 산출하며 큰
arm 값에 영향받지 않는다. arm 쪽 에너지 비용을 포착하는 것은
`joint_torque`(§5.1, 물리 torque를 읽음)뿐이다.

### 5.3 `action_smoothness` — 8개 차원 전부에 대한 1차 + 2차

`action_smoothness`(`rewards.py:161-165`): `mean(da²) + mean(d2a²)`이며 여기서
`da = a_t − a_{t-1}`(1차, action-velocity), `d2a = a_t − 2a_{t-1} +
a_{t-2}`(2차, jerk-like)다. `thruster_energy`와 달리 이것은 **8개 action 차원
전부**에 대해 계산된다. 단지 action이 0일 때가 아니라 진짜 정상상태
(prev == prev_prev == current)에서만 0이다
(`test_action_smoothness_zero_when_constant`, `tests/test_rewards.py:150`). 세
action 버퍼는 `_pre_physics_step` 맨 위에서 회전되고(`action-pipeline.md` §3.3)
reset 시 함께 0으로 초기화되므로, reset 직후 첫 step의 `da`/`d2a`는 stale한
cross-episode history가 아니라 0에 대해 측정된다.

### 5.4 `bias_ema_penalty` — env-side 결합을 지닌 sustained-offset penalty

`bias_ema_penalty`(`rewards.py:168-176`): 3-channel `env._bias_ema`(roll, pitch,
yaw-rate)에 대한 `Σᵢ wᵢ · bias_emaᵢ²`이며, per-axis 가중치
`env._reward_manager._bias_w`는 `cfg.bias_weights`에서 한 번 preallocate된다
(`rewards.py:192`; 기본값 `(1.5, 1.0, 1.0)`, `rewards.py:103`). per-step tracking
reward가 볼 수 없는 sustained per-env tracking offset을 penalize한다(roll이 약한
권한에 맞춰 더 높게 가중된다). dataclass 기본값으로는 off(`k_bias=0.0`)이지만
shipped config에서는 `k_bias=-2.0`으로 **ON**이다(`config.py:445`).

**env-side 결합(two-file 함정).** `albc_env.py:1067-1079`의 EMA 버퍼 업데이트
자체가 `if self.cfg.reward.k_bias != 0.0:`로 gating되므로, `k_bias`를 on/off하면
서로 다른 두 파일에서 결합된 두 가지가 뒤집힌다: (a) reward 항의 가중치가 nonzero가
되고(`rewards.py:205`), (b) EMA 업데이트 루프 `bias_ema = α·bias_ema +
(1−α)·err3`가 돌기 시작한다. `k_bias == 0`일 때는 업데이트가 완전히 건너뛰어지고
`_bias_ema`는 reset 값 `0`에 얼어붙은 채(감쇠하지 않음) 유지된다 — 그래서 함수는
매 step 여전히 실행되더라도 `bias_ema_penalty`는 `0`을 반환한다. shipped config
에서는 업데이트가 매 step 돈다(`α = 0.99`, 50 Hz에서 ~100-step / 2 s 시정수이므로
per-step 노이즈가 아니라 sustained offset을 추적한다). leaky integrator(§7)와 달리
이 EMA 업데이트는 **ungated**다 — 항상 현재 error를 반영하며 magnitude threshold가
없다.

### 5.5 joint1 anti-drift는 이제 constraint 쪽뿐, reward 항이 아니다

이 파일에는 reward 쪽 joint1 centering penalty가 없다: joint1(PhysX position
limit이 없는 연속-회전 모터로, 순수 delta-integrator로 구동됨 —
`action-pipeline.md` §4.1)에 `wrap(θ₁)²` restoring gradient를 공급하던
`joint1_centering_penalty` 함수와 `ALBCRewardCfg.k_joint1_center` 필드는
2026-07에 제거됐다(§9). joint1 anti-drift는 이제 전적으로 **constraint**
쪽에서, `joint1_constraint_arm`(`config.py:552`,
`main-network-architecture.md` §5.1)을 통해 처리된다: 스위치는 2-way
`{"none", "B"}`이며, `"B"`가 `joint1_cumulative_cost`(unwrapped, 적분된
command displacement)를 constraint 항으로 연결한다. 이전에 존재하던
wrapped-instantaneous constraint 변형(`joint1_centering_cost`, "arm A")도
같은 정리에서 제거됐다 — 그 wrap fold는 한 바퀴 전체 drift의 cost를 0으로
만들었는데, 이는 지금 메커니즘을 촉발한 것과 동일한 맹점이었다. 더 이상
reward-side/constraint-side 상호 배타적 lever 쌍은 존재하지 않으며,
constraint 쪽 arm B가 유일하게 남은 joint1 anti-drift 메커니즘이다.

---

## 6. error 버퍼, reward call site, `dt` 스케일링

### 6.1 `_compute_ang_errors` — the wrap

`_compute_ang_errors`(`albc_env.py:1000-1007`)는 integral 및 bias 업데이트 전에
`_get_rewards` 맨 위에서 step당 한 번 돈다:

```python
roll, pitch, _ = self._euler_cache
raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
self._att_rp_err   = torch.atan2(torch.sin(raw), torch.cos(raw))         # wrapped roll/pitch error
self._yaw_rate_err = self._ang_cmd[:, 2] - self._robot.data.root_ang_vel_b[:, 2]
```

`_ang_cmd` 레이아웃은 `[roll_cmd, pitch_cmd, yaw_rate_cmd]`(주석
`albc_env.py:303`, 텐서 할당 `:304`)다. roll/pitch error는 `atan2(sin, cos)`를
통해 $(-\pi, \pi]$로 **wrap**된다: naive subtraction은 진짜 각도 거리가 `−1°`일 때
`+359°`를 반환할 수 있고, 이는 커널에서 `err²`를 폭주시키고 integral/EMA
accumulator를 오염시킬 것이다. `_yaw_rate_err`는 **wrap되지 않는다** — 이는 각도가
아니라 rate(rad/s)이므로 접을 주기성이 없다. `_euler_cache`는 `_get_dones`
(`albc_env.py:1230`)에서 step당 한 번, 그리고 `_reset_idx`(`:1268`) 끝에서 다시
refresh되므로 same-step reset이 유효한 post-reset pose를 본다.

동일한 wrap-and-subtract가 fresh post-reset pose에 대해 `_reset_task_and_state`
(`albc_env.py:1439-1444`)의 reset에서 중복 수행되므로, reset 이후 첫
observation/reward는 stale하지 않다; `_error_integral`과 `_bias_ema`는 바로 뒤에서
0으로 초기화된다(`:1446-1447`). (여기 `:1006-1007`에서 쓰이는 버퍼
`self._ang_err`는 vestigial write-only 상태로 — env 어디에서도 읽히지 않으며;
reward 함수는 `_att_rp_err`/`_yaw_rate_err`를 직접 읽는다.)

### 6.2 reward call site와 `dt` 스케일링

`RewardManager`는 init 시 한 번 생성되고(`albc_env.py:255`) `dt=self.step_dt`로
호출된다(`albc_env.py:1081-1085`). `compute()`(`rewards.py:207-210`) 내부:

```python
for name, weight, value in terms:
    scaled = value * weight * dt
    self._buf            += scaled
    self._episode_sums[name] += scaled
```

`step_dt`는 **Isaac Lab base `DirectRLEnv` 클래스에서 상속**된다(framework 레벨,
`sim.dt * decimation`으로 계산됨); `albc_env.py`는 이를 결코 할당하지 않고 읽기만
한다(예: `:101`). `sim.dt = 0.005`(`config.py:372`)와
`decimation = 4`(`config.py:351`)에서 `step_dt = 0.02 s`(50 Hz)다. 그래서 보고되는
`k` 값은 **초당**이고; 실효 per-step은 `k * 0.02`다(§3.2). 모든 항 — tracking과
penalty 모두 — 이 단일 지점에서 스케일된다; 유일하게 제외되는 reward 기여는
`compute()` 반환 *이후* 더해지는 `termination_penalty`(`albc_env.py:1088-1089`,
`* dt` 없음)이며, 이것이 6개 tracked 항에 속하지 않는 이유다.

---

## 7. reward-sigma / integral-gate 결합

이것은 reward 항이 아니라 config 결합이다. `integral_gated=True`
(`config.py:347`)는 **observation** integral `_error_integral` — 69D observation의
3D integral 채널을 먹이는 leaky integrator(`main-network-architecture.md` §2.1)
— 을 gating하지, 결코 reward 합을 gating하지 않는다. 하지만 그 gate threshold는
문자 그대로 **reward 커널의 sigma**다: `_integral_gate_sigmas`는 `__init__`에서
`[cfg.reward.att_rp.sigma, cfg.reward.att_rp.sigma, cfg.reward.yaw_vel.sigma]`
로부터 한 번 pre-build되고(`albc_env.py:164-173`), 매 step
`gate = (err_stack.abs() < self._integral_gate_sigmas).float()`는 per-axis error가
reward의 Gaussian width 안에 있을 때만 누적한다(`albc_env.py:1029-1038`).

두 시스템(tracking reward vs integral observation)은 효과 면에서는 분리돼 있으나
이 하나의 공유 `sigma` 값을 통해 config 상으로 결합돼 있다. 귀결: `reward.att_rp.sigma`나
`reward.yaw_vel.sigma`를 retune하면 integral-observation gating도 조용히 바뀐다.
shipped config에서 세 gate threshold 모두 `0.10 rad ≈ 5.7°`다(`att_rp.sigma`와
`yaw_vel.sigma` 둘 다 `0.10`). 이를 설명하는 주석은 `rewards.py`의 `sigma` 필드
옆이 아니라 `albc_env.py:164-165`에 있어서 의존성을 놓치기 쉽다.

---

## 8. config와 실험 맥락

### 8.1 `performance_lb`와 DORAEMON success feedback

reward는 정책을 shaping하기만 하는 게 아니라 — 그 누적 episode return이 DORAEMON DR
curriculum(domain-randomization 레퍼런스; marinelab의 `DoraemonCfg`)을 위한
**이진 success 신호**다. 매 step `_episode_return_accum += reward`
(`albc_env.py:1075`); reset 시 `_log_and_reset_rewards`(`albc_env.py:1276-1287`)
내부에서 `success = (returns >= performance_lb).float()`가
`doraemon.record_episodes(...)`에 공급된다. `episode_length_buf == 0`인 episode
(어떤 step도 밟기 전의 초기 `env.reset()`)는 필터링되므로(`:1277-1279`) fake
zero-return failure로 버퍼에 들어가지 않는다.

shipped `doraemon` cfg(`config.py:479`)는
`DoraemonCfg(enable=True, kl_ub=0.12, performance_lb=250.0, step_interval=250)`이며;
이 중 marinelab `DoraemonCfg` dataclass 기본값(`kl_ub=0.5`, `performance_lb=80.0`;
`enable=True`/`step_interval=250`은 이미 기본값과 일치)의 진짜 override는 `kl_ub`와
`performance_lb`뿐이다. 캘리브레이션 이력(`config.py:466-478`, **실험 이력 주석이지
메커니즘이 아님**)은, episode-return 분포가 min=81.9 / p5=227 / p25=250 / median=264
/ p95=291(n=2000)이었던 recon run 이후 `performance_lb`가 `68.0 -> 250.0`으로
올려졌다고 기록한다: 옛 `lb=68`은 최소 return 아래에 있어 success가 항상 1이었고
feasibility constraint가 무력했다. `lb=250`(p25)은 시작 success를 ~0.65로 두어
다시 live하되 median 아래라 reward plateau가 이를 0으로 끌고 갈 수 없다.

### 8.2 `r13` `k_bias=-2.0` 근거 (실험 이력, 메커니즘 아님)

`k_bias=-2.0` override는 **실험 이력 주석**(코드 사실이 아님)인 인라인 주석
(`config.py:424-428`)을 지닌다: 이전 `r12_baseline`이 bias 가중치를
`-1.0`으로(그리고 `latent=16`으로) 반감해 full-strength `r11_emabias`
변형(`k_bias=-2.0`, hard-roll 0.62, "rank #1", "strongest single intervention
across 24 runs") 대비 "rank #7"(hard-roll 1.26)로 regress했다고 기록한다. `r13`은
full strength를 복원한다. rank / metric 주장 어느 것도 `config.py`나 `rewards.py`
로부터 독립적으로 검증 가능하지 않다 — shipped 값에 대한 provenance로 취급하되
검증된 사실로 취급하지 말 것.

---

## 9. 함정 (Gotchas)

디스크에 대해 각각 검증된 함정 모음. 몇몇은 stale docs일 뿐 기능적 버그가 아닌
documentation-vs-code 불일치다 — 실행되는 코드 경로는 내부적으로 일관된다(6
name, 6 term, 6 episode-sum key).

| # | Gotcha | Reality | Cite |
|---|---|---|---|
| 1 | `lin_vel_tracking` / `joint1_centering_penalty`가 아직 이 파일에 있을 것 같음 | 둘 다 `ALBCRewardCfg.lin_vel`/`k_joint1_center`와 함께 **2026-07에 제거됨**; `lin_vel_tracking`은 별개 모듈인 `envs/full_dof/mdp/rewards.py`에 여전히 존재하고, `joint1_centering_penalty`는 완전히 사라졌다(constraint 쪽 `joint1_cumulative_cost`가 지금의 anti-drift 메커니즘, §5.5) | `rewards.py:185,199-206` |
| 2 | 모듈 docstring이 `lin_ratio` 필드 주석과 linear 항이 "the fix"인지를 두고 모순됐었음 | **해소됨**: docstring은 이제 linear penalty가 SS-error를 고치려던 시도였으나 그 자체의 dead zone을 유발해 비활성화됐다고 명시한다(`lin_ratio=0` 전부); 실제 완화책은 `yaw_vel`에만 걸린 tanh penalty뿐이고, `att_rp`에는 saturating 항이 없다 | `rewards.py:14-23,79` |
| 3 | tanh와 arctan은 상호 배타적으로 보임 | 독립적인 `if`문 — 둘 다 설정되면 stack된다; 배타성은 관례다. Shipped config는 **`yaw_vel`에만 tanh를 활성화**한다; `arctan`은 kept-but-unused heavy-tail 대안으로, 결코 nonzero로 설정되지 않는다 | `rewards.py:63-73,123-128; config.py:439` |
| 4 | `rewards.py`만 읽으면 `k_bias=0`이 "bias off"로 읽힘 | Shipped config가 **`k_bias=-2.0`으로 override**한다(항 ON), 그리고 이 override는 *두 번째 파일*(`albc_env.py`)에서 동일한 `k_bias != 0` guard 아래 결합된 EMA-buffer 업데이트를 함께 뒤집는다 | `rewards.py:100; config.py:445; albc_env.py:1069` |
| 5 | `k` 값이 per-step magnitude처럼 보임 | 실제로는 **초당** 값이다; 실효 per-step은 `k * dt`(`* 0.02`)이며, 6개 항 전부에 대해 한 지점에서 스케일된다; `step_dt`는 framework에서 상속되고 `albc_env.py`에서 정의되지 않는다 | `rewards.py:208; config.py:351,372` |
| 6 | `joint_torque`가 commanded action을 penalize한다고 생각하기 쉬움 | **`applied_torque`**를 읽는다 — post-actuator, post-clamp 물리 torque; fault/effort-limit 스케일링이 raw action과 독립적으로 이를 바꾼다 | `rewards.py:151-153` |
| 7 | `termination_penalty`가 reward 항이라고 생각하기 쉬움 | `compute()` **바깥**에서 적용되고, `dt`-스케일**되지 않으며**, `_NAMES`에도 **없다** — 어떤 `Reward/<name>` key로도 나타나지 않는다. 기본 off, 결코 override되지 않음 | `rewards.py:96; albc_env.py:1088-1089` |
| 8 | `reward.*.sigma`를 retune하면 reward만 영향받는다고 생각하기 쉬움 | **또한** integral-observation gate threshold도 retune하는데, 이것이 reward sigma를 빌려쓰기 때문이다 | `albc_env.py:164-173,1056-1065` |
| 9 | `att_roll_weight=1.5`가 설명 없는 상수처럼 보임 | shipped TAM에 근거한다: roll moment arm `0.007 m` vs pitch `0.145 m`(`config.py:81-82`), payload-DR 권한 주석으로 확증됨 | `rewards.py:91; config.py:81-82,207-212` |
| 10 | `envs/main/mdp/rewards.py`와 `envs/full_dof/...`가 하나의 공유 모듈이라고 생각하기 쉬움 | **별개의 hand-forked 파일**; `full_dof`는 여전히 자신의 7-term `RewardManager`에 `lin_vel_tracking`을 연결하고 있다(joint1 항은 애초에 없었음). 한쪽 fix가 다른 쪽에 전파되지 않는다 | `rewards.py:185` vs `full_dof/mdp/rewards.py:173` |

---

## 10. 테스트와 로깅

### 10.1 테스트 불변식 — `tests/test_rewards.py` (9개 테스트)

스위트는 repo-root `tests/test_rewards.py`에 있으며(`constrained_albc/` 패키지
**아래가 아님**). `importlib`로 `rewards.py`를 직접 import하고
(`isaaclab.sim`을 끌어들일 `constrained_albc.__init__`를 우회) `SimpleNamespace`
env 대역을 쓴다 — 이는 **sign convention과 roll-weighting의 whitebox unit pin**
이므로 refactor가 조용히 reward를 뒤집을 수 없다. `RewardManager.compute()`를
end-to-end로 exercise하지는 **않는다**.

| Test (`tests/test_rewards.py:line`) | Invariant | Mechanism protected |
|---|---|---|
| `test_yaw_vel_tracking_peaks_at_zero` (113) | `err=0 -> 1.0` | `yaw_vel` exp kernel |
| `test_att_rp_roll_weighted_more_than_pitch` (120) | roll-only 0.2 < pitch-only 0.2 reward | `att_roll_weight=1.5` up-weighting |
| `test_att_rp_peaks_at_zero` (128) | zero attitude error -> 1.0 | `att_rp` exp base case |
| `test_joint_torque_nonneg_mean_square` (137) | `[3,4] -> mean(9,16)=12.5` | `mean(tau²)` numeric pin |
| `test_thruster_energy_uses_thruster_action_slice` (143) | `[9,9,1,0..] -> 1/6` (arm excluded) | `[:, 2:]` slice |
| `test_action_smoothness_zero_when_constant` (150) | constant -> 0; jump -> >0 | first+second-order difference |
| `test_bias_ema_uses_preallocated_weights` (164) | `w=[1.5,..], ema=[2,0,..] -> 6.0` | per-axis weighting via `_bias_w` |
| `test_bias_ema_zero_when_no_offset` (172) | all-zero ema -> 0.0 | base case |
| `test_reward_manager_preallocates_bias_w` (177) | `__init__` builds `_bias_w` == `cfg.bias_weights` | perf regression net (no per-step rebuild) |

**커버리지 공백**(whitebox-only): `RewardManager.compute()`의 dt-스케일링이나
6-term 합, `RewardManager.reset()`, tanh/arctan 분기(shipped `yaw_vel` tanh
override는 unit 레벨에서 untested), `lin_ratio > 0`, env 레벨 `k_bias != 0`
gating을 구동하는 테스트가 없다. `bias_w`/`bias_ema` fixture는 6-D 벡터
(`tests/test_rewards.py:165-166`)를 쓰는데 — 이는 test-only shape 선택이지 6-D
버퍼의 **증거가 아니다**; 실제 `_bias_ema`는 3-D(`albc_env.py:316`)로, 3-tuple
`bias_weights`와 일치한다. (제거된 `lin_vel_tracking`/`joint1_centering_*` 테스트는
그 함수들과 함께 사라졌다, §9.)

### 10.2 Episode 로깅 — per-term mean을 wandb/TB로

`RewardManager.compute()`는 각 항의 이미 `dt`-스케일되고 이미 부호가 붙은 기여를
`_episode_sums[name]`에 누적한다(`rewards.py:209-210`). reset 시
`RewardManager.reset(env_ids)`(`rewards.py:214-219`)는
`{name: episode_sums[name][env_ids].mean().item()}`(각 항의 episode-summed reward를
**resetting env들에 걸쳐 평균**낸 값)을 반환하고 그 env들의 sum을 0으로 만든다.

`_collect_episode_metrics`(`albc_env.py:1106-1125`)가 각각을 log key로 바꾼다:

```python
for name, value in reward_sums.items():
    normalized = value / self.max_episode_length_s          # FIXED denominator, see below
    log[f"Reward/{name}"] = normalized
    total += normalized
log["Reward/total"] = total
```

방출되는 key는 정확히 `Reward/att_rp`, `Reward/yaw_vel`, `Reward/torque`,
`Reward/thruster`, `Reward/smoothness`, `Reward/bias`
(`_NAMES`와 일치)에 파생 `Reward/total`이다. wandb curve를
항으로 되매핑하려는 독자는 정확한 태그 `Reward/<name>`을 찾아야 한다.

짚어둘 두 가지 정규화 뉘앙스:

- **고정 분모.** `max_episode_length_s`는 `cfg.episode_length_s`(base
  `DirectRLEnv`의 상수)이며, 끝난 episode의 실제 지속시간이 **아니다**. 일찍
  종료되는 episode는 per-step 밀도가 동일해도 순전히 더 적은 step에 걸쳐 누적하기
  때문에 *더 작은* `Reward/*` 값을 보인다 — 이는 진짜 per-episode-length 평균이
  아니라 cross-run 비교 가능성을 위한 고정-분모 정규화다. `_num_resets`가 함께
  log되므로(`albc_env.py:1117`) single-env 극단 trajectory를 가중할 수 있다.
- **`/`-prefix passthrough + stale-`extras` 뉘앙스.** rsl_rl(외부
  `rsl_rl_lib-3.1.2`)은 `/`를 포함한 어떤 key든 그대로 log하고 bare key에는
  `Episode/`를 prefix한다; 여기 모든 key는 이미 `/`를 가지므로 전부 prefix 없이
  통과한다. `self.extras`는 `DirectRLEnv.__init__`에서 한 번 초기화되고 결코
  clear되지 않으며, `self.extras["log"]`는 최소 한 env가 reset될 때만 재할당된다
  — 그래서 reset이 없는 step에서 rsl_rl은 **stale**한 last-reset dict를
  per-iteration `ep_infos` 평균에 다시 append한다. 따라서 per-iteration `Reward/*`
  mean은 reset event에 걸친 깔끔한 mean이 아니라 가장 최근 reset 스냅샷 쪽으로
  치우친다. 이는 external-library 거동으로, curve를 읽는 사람을 위해 여기 표시한다.

---

## 소스 파일

- `constrained_albc/envs/main/mdp/rewards.py` — `TrackingTermCfg`, `ALBCRewardCfg`, `_exp_quad_saturating`, 6개 term 함수, `RewardManager`(`compute`/`reset`)
- `constrained_albc/envs/main/config.py` — `reward` override(`:438-446`), TAM(`:77-84`), command range(`:426-433`), `integral_gated`(`:363`), sim/decimation/episode length(`:350-372`), `doraemon`/`performance_lb`(`:499`), `joint1_constraint_arm`(`:552`)
- `constrained_albc/envs/main/albc_env.py` — `_compute_ang_errors`(`:1027-1035`), integral gate(`:1045-1065`), bias-EMA update(`:1067-1079`), reward call + termination penalty(`:1081-1089`), `_get_rewards`(`:1036-1104`), `_collect_episode_metrics`(`:1106`), DORAEMON success + reset(`:1295-1310`), buffer init(`:298-316`)
- `tests/test_rewards.py` — 10개 whitebox sign/roll-weight pin(repo-root `tests/`, 패키지 아래가 아님)
- `constrained_albc/envs/main/mdp/constraints.py` — `joint1_cumulative_cost`(constraint 쪽 joint1 anti-drift, `apply_joint1_constraint_arm`), `main-network-architecture.md` §5.1 참조
- `marinelab/marinelab/algorithms/doraemon.py` — `DoraemonCfg` 기본값(`envs/main/doraemon.py` shim으로 re-export)
