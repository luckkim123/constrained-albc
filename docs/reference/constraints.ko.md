# 제약 조건 (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`(`constrained_albc/envs/main/`,
> attitude-only ALBC 정책)의 constraint 시스템. 이 태스크에는 10개의 IPO constraint가
> 실려 있다 — **probabilistic 5개**(binary violation-probability budget) +
> **average 5개**(expected-magnitude budget) — `envs/main/config.py`에 정의되고
> `algorithms/constraint_trpo.py`의 `ConstraintTRPO`가 소비한다.
>
> 본 문서는 디스크 코드에 대해 검증한 코드 레벨 레퍼런스다. 레거시 full-DOF 변형
> (`envs/full_dof/`, `Isaac-ConstrainedALBC-Full-*-v0`)은 동일한 constraint 리스트
> 상수를 재사용하지만 다른 태스크이며 여기서 다루지 **않는다**.

> **English version**: [`constraints.md`](constraints.md) (SSOT).

---

## 1. 전체 구조

Constraint 시스템은 깔끔하게 분리된 3개 레이어로 구성된다: **정의(definitions)**는
각 cost가 무엇을 측정하는지 결정하고, **최적화(optimization)**는 cost budget을
어떻게 강제할지 결정하며, **배선(wiring)**은 어떤 budget과 하이퍼파라미터가
실제 run에 도달하는지 결정한다.

1. **정의 (cost 함수).** `mdp/constraints.py`에 10개의 per-step cost 함수가
   있다. 각각 `(num_envs,)` 크기의 non-negative cost 텐서를 반환한다.
   `compute_all_costs()`가 매 스텝 이들을 단일 `(num_envs, K)` 텐서로 쌓는다
   (`constraints.py:326-332`).
2. **최적화 (ConstraintTRPO + IPO log-barrier).** `constraint_trpo.py`는 K개의
   cost budget에 대한 interior-point log-barrier를 TRPO surrogate 목적함수에
   직접 접어 넣는다. 별도의 Lagrangian dual도, projection 스텝도 없다 — 단일
   joint scalar가 natural-gradient 스텝을 구동한다.
3. **배선 (budget).** `config.py`가 각 cost 함수를 per-step budget $D_k$와
   이름에 바인딩한다; 알고리즘은 이를 discounted budget
   $d_k = D_k / (1 - \gamma_c)$로 재조정하고(`constraint_trpo.py:146-151`) 배치의
   mean discounted cost return과 비교한다.

```
cost function f_k(state)  ->  compute_all_costs -> costs (num_envs, K)   [mdp/constraints.py]
        |
        v  per-step cost, one column per constraint
cost GAE (cost_gamma, cost_lam)  ->  J_hat_C_k  (mean discounted cost return, K-vector)
        |
        v
IPO adaptive threshold:  d_k^i = max(d_k, J_hat_C_k + alpha * d_k)         [constraint_trpo.py:306-308]
        |
        v
barrier margin_k = d_k^i - cost_surr_k          # plain difference, NOT / d_k
barrier = -sum_k log(margin_k.clamp(min=1e-8)) / barrier_t                  [constraint_trpo.py:454-464]
        |
        v
surrogate L = -E[A * ratio]  +  barrier  -  entropy_bonus                   [constraint_trpo.py:461,480]
        |
        v
TRPO natural-gradient step under a pure-KL trust region (barrier curvature NOT in Fisher)
```

핵심 구조적 사실: `ConstraintTRPO`에는 probabilistic constraint와 average
constraint를 구별하는 코드가 **전혀 없다**. K개 열 전부가 byte-identical한
GAE, standardization, adaptive-threshold, barrier 코드를 거친다. prob/avg
구분은 오로지 *각 cost 신호가 upstream에서 어떻게 계산되는지*(`mdp/constraints.py`)와
*문서 관례*(`config.py`)에만 존재하며, optimizer가 그것을 소비하는 방식에는
전혀 없다.

---

## 2. Constraint 분류 — probabilistic vs average

실려 있는 10개 constraint는 5 + 5로 나뉜다. 이 구분은 `config.py`의 리스트
순서와 인라인 주석으로만 표현된다 — 엔트리 `[0:5]` 위에 `# --- Probabilistic (5) ---`,
`[5:10]` 위에 `# --- Average (5) ---`(`config.py:56`, `config.py:62`). `ConstraintTermCfg`에는
`is_probabilistic`/`kind`/`type` 필드가 **없다**; 필드는 `func`, `params`,
`budget`, `name`뿐이다(`constraints.py:50-57`).

| 카테고리 | Cost 신호 | Budget $D_k$의 의미 | Feasibility 목표 |
|---|---|---|---|
| Probabilistic (5) | binary indicator $\mathbb{1}[\text{violated}] \in \{0,1\}$ | 최대 violation *확률* | $\mathbb{E}[\mathbb{1}] \le D_k$ |
| Average (5) | continuous non-negative cost | 최대 *expected magnitude* | $\mathbb{E}[\text{cost}] \le D_k$ |

수학적으로 두 카테고리는 동일한 constrained-MDP 객체
$\mathbb{E}[\sum_t \gamma_c^t c_k(s_t,a_t)] \le d_k$이며, per-step cost
$c_k$가 무엇인지만 다르다. probabilistic constraint의 $c_k$는 $\{0,1\}$
indicator이므로 discounted sum은 ($\gamma_c$ discount를 제외하면) violation
count가 되고, budget은 확률로 읽힌다. average constraint의 $c_k$는 continuous
magnitude이므로 budget은 허용된 mean level로 읽힌다.

**이들을 "다르게" 취급하는 메커니즘은 optimizer 안에 없다.**
`constraints.py:14-24`의 docstring이 `[0]-[4]`를 probabilistic, `[5]-[9]`를
average로 번호를 매기며, 그 순서와 근저의 cost-함수 수학(indicator vs
continuous)이 구분의 전부다. 런타임에 `compute_all_costs`
(`constraints.py:326-332`)는 `torch.stack([t.func(...) for t in cfg.terms], dim=-1)`을
수행한다 — 10개 term 전부를 동일하게 취급한다. 짚어둘 만한 결과 하나: binary
indicator들의 per-constraint cost-advantage 열은 분산이 거의 0에 가까워,
standardization 스텝이 std를 `min=1.0`으로 floor-clamp해서 이 binary
채널이 폭주하지 않도록 막는다(Section 4 참조).

---

## 3. 10개 constraint term

모든 값은 `config.py:57-69`에서 그대로 가져왔다. Discounted budget
$d_k = D_k / (1 - \gamma_c)$이며 $\gamma_c = 0.99$이므로 $d_k = 100 \cdot D_k$.

| # | 이름 | 함수 | 핵심 파라미터/임계값 | Budget $D_k$ | 유형 | 물리적으로 제한하는 것 |
|---|---|---|---|---:|---|---|
| 0 | `attitude` | `attitude_limit_cost` | `limit=1.396` rad (80°) | 0.01 | prob | roll/pitch 크기 |
| 1 | `arm_torque` | `torque_limit_cost` | `limit_nm=9.5` | 0.08 | prob | arm joint 토크 |
| 2 | `arm_joint_vel` | `velocity_limit_cost` | `limit_rad_per_s=4.189` | 0.02 | prob | arm joint 속도 |
| 3 | `joint1_pos` | `joint1_position_cost` | `limit_rad=4*pi` (12.566) | 0.01 | prob | joint-1 절대 각도 |
| 4 | `cumul_yaw` | `cumulative_yaw_cost` | `limit_rad=8*pi` (25.133) | 0.01 | prob | 누적 yaw 회전 |
| 5 | `thruster_util` | `thruster_utilization_cost` | (파라미터 없음) | 0.40 | avg | thruster 사용권한(authority) |
| 6 | `rp_rate` | `rp_rate_cost` | `soft_threshold=0.5` | 0.10 | avg | roll/pitch 각속도 |
| 7 | `yaw_rate` | `yaw_rate_cost` | `soft_threshold=0.55` | 0.10 | avg | yaw 각속도 |
| 8 | `rp_vel_settling` | `rp_vel_settling_cost` | `settling_threshold=0.087` | 0.20 | avg | roll/pitch 정착(settling) |
| 9 | `manipulability` | `manipulability_cost` | `w_threshold=0.3` | 0.05 | avg | arm manipulability 하한 |

리스트 바로 위 주석 하나가 이전 수술 이력을 기록한다: `thruster_rate`는 제거됐고
("`entropy_coef>0`와 구조적으로 불양립: 노이즈만으로도 5배 위반") `thruster_sat`는
`thruster_util`(average, budget 0.40, "원래 형태")로 되돌려졌다 —
`config.py:53-54`.

### 3.1 Probabilistic term (`[0:5]`)

각각 $\{0,1\}$ indicator를 반환하며, discounted-sum budget이 violation
확률이 된다.

- **`attitude`** — $\mathbb{1}[\lvert\text{roll}\rvert > \text{limit} \ \lor\ \lvert\text{pitch}\rvert > \text{limit}]$, $\text{limit}=1.396$ rad.
- **`arm_torque`** — $\mathbb{1}[\max_j \lvert\tau_j\rvert > 9.5\,\text{Nm}]$.
- **`arm_joint_vel`** — $\mathbb{1}[\max_j \lvert\dot q_j\rvert > 4.189\,\text{rad/s}]$.
- **`joint1_pos`** — $\mathbb{1}[\lvert\theta_1\rvert > 4\pi]$, 즉 joint-1 절대
  각도가 $\pm 4\pi$ 레일을 넘김.
- **`cumul_yaw`** — $\mathbb{1}[\lvert\theta_{\text{yaw,cum}}\rvert > 8\pi]$,
  누적(unwrapped) yaw.

### 3.2 Average term (`[5:10]`)

각각 continuous non-negative cost를 반환하며, discounted-sum budget이
expected magnitude가 된다.

- **`thruster_util`** — `thruster_utilization_cost`는 **설정 가능한 임계값이
  없다**(`ConstraintTermCfg.params` 기본값 `{}`에 의존, `constraints.py:55`).
  docstring(`constraints.py:20`)에 따르면 per-env 최대 절대 정규화 thruster
  state $\max_i \lvert s_i \rvert$를 반환한다. 10개 중 유일한
  control-authority 채널이다.
- **`rp_rate`** — $0.5$에서 hinge된 soft-thresholded roll/pitch 각속도
  cost: cost는 soft threshold를 넘어야만 발생한다.
- **`yaw_rate`** — $0.55$에서 hinge된 soft-thresholded yaw-rate cost.
- **`rp_vel_settling`** — mean roll/pitch 각속도 $(\lvert p \rvert + \lvert q \rvert)/2$이되,
  attitude error가 target의 `settling_threshold=0.087` rad($5\,\text{deg}$) 이내일
  때만 nonzero로 masking된다: transit 중(att error가 threshold보다 큼)에는
  cost가 0이고 settling 중(att error가 threshold 이하)에만 active다. 이름과
  구현이 일치한다(`constraints.py:206-228`). 단 `settling_threshold`가 각속도
  자체가 아니라 *attitude error*를 게이트한다는 점은 유의할 caveat이다.
- **`manipulability`** — manipulability 하한 `w_threshold=0.3` 아래에서
  hinge된다; arm의 manipulability 측정치가 하한 밑으로 떨어지면 cost가
  발생한다.

다성분 average cost 2개(`thruster_util`, `rp_rate`)는 per-step cost **안에서** 공간
`max`($\max_i \lvert s_i\rvert$, $\max(\lvert p\rvert,\lvert q\rvert)$)로 축약한다 — 이는
category error가 아니라 이론적으로 정합이다. average 제약의 "average"는 시간·확률에 대한
기댓값 $\mathbb{E}[\sum_t \gamma_c^t c_k]$이고, `max`는 per-step 신호 $c_k$의 모양일 뿐이다.
따라서 `max`-inside-average는 **시간 평균된 peak**(할인 평균이 smoothing해서 짧은 스파이크는
관대한 *soft* peak)를 bound한다. 이는 $\mathbb{E}[\max_i]$이지 $\max_i \mathbb{E}$가 아니며,
"어느 step에서도 절대 초과 금지"라는 hard bound도 아니다(그건 probabilistic indicator가 필요).
`rp_vel_settling`은 `mean`을, `yaw_rate`/`manipulability`는 단일 양을 쓰므로 `max`는 다성분
축약이 필요한 곳에만 등장한다.

### 3.3 실험 전용 joint1 term (미출시)

joint1-anti-drift 실험 라인(Section 7)을 위한 average cost 함수 하나가 별도로
존재하며, 실려 있는 10개에는 포함되지 않는다(`constraints.py:26-29`):

- **`joint1_cumulative_cost`** — $\lvert q^{\text{des}}_1 - q^{\text{nom}}_1 \rvert$,
  unwrapped된 누적 command displacement(`constraints.py:271`, 사용:
  `env._joint_pos_targets[:, 0] - env._nominal_joint_pos[0]`). 이제 이것이
  유일한 joint1 anti-drift 메커니즘이다 — wrapped-instantaneous constraint
  (구 "arm A", `joint1_centering_cost`)와 reward-side centering penalty
  둘 다 2026-07에 제거됐다.

### 3.4 Threshold provenance와 actuator hard-cap layering

Constraint threshold는 **한 종류의 hyperparameter가 아니다** — 튜닝 규칙이 정반대인 두 그룹으로
갈린다.

- **Hard safety rail (물리 근거).** `attitude`(80° tilt 안전), `arm_torque`(`limit_nm=9.5` = arm
  모터 **stall torque**), `arm_joint_vel`(`4.189` rad/s), `joint1_pos`($4\pi$ 케이블 감김 레일),
  `cumul_yaw`($8\pi$ 테더 감김 레일). arm 레일 2개는 asset의 PhysX 하드캡 **안쪽**에 있다 —
  `effort_limit_sim=13.0` Nm, `velocity_limit_sim=6.28` rad/s($2\pi$)(`marinelab/.../albc/albc.py:200-201`).
  즉 `9.5 < 13.0`, `4.189 < 6.28`: **soft IPO 제약이 hard clamp보다 먼저 문다**(의도된 layering),
  그리고 threshold 위에 indicator가 fire할 수 있는 live band가 있어 제약이 살아있다(§9 일치:
  `arm_torque` $\hat J_C/d_k = 0.407$ fire, `arm_joint_vel` $0.031$ deep slack). **불변식: soft
  threshold는 hard cap 안쪽에 있어야 한다.** 뒤집으면 제약이 조용히 죽는다 — 계획된
  `velocity_limit_sim` $6.28 \to 3.1$ retrain(실제 XW540 팔에 맞춤)은 $3.1 < 4.189$가 되어 PhysX가
  3.1에서 자르니 `velocity_limit_cost`가 영영 fire 못함(**dead constraint**, budget·cost head는
  차지). Fix는 omx wiki `arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt.md`에
  문서화 — 하드캡 내릴 때 `limit_rad_per_s`도 새 캡 안쪽으로 함께 내림. 레일은 reward가 아니라
  **실제 물리값**(측정/sysid 기반)으로만 튜닝한다.
- **Soft shaping threshold (판단으로 선택).** `rp_rate`(`0.5`), `yaw_rate`(`0.55`),
  `rp_vel_settling`(`0.087`), `manipulability`(`0.3`). graded hinge 벌점이 시작되는 지점을 정하는
  behavior/comfort 엔벨로프이지 안전 한계가 아니며, **정당한 실험 튜닝 대상이다**. threshold는
  cost가 시작되는 *위치*를, budget $D_k$는 허용 *양*을 정하므로 둘은 결합돼 있다: budget만이 아니라
  제약별로 (threshold, budget)를 **함께 튜닝**한다. threshold가 운용점에서 먼 제약의 budget만
  튜닝하면 no-op이다 — §9에서 9/10이 slack이라, 변경이 실제로 제약을 binding 쪽으로 밀기 전엔 대개
  아무것도 안 바뀐다. 1-GPU 순차 환경에선 mostly-flat 응답면(절벽은 `thruster_util` 하나)에 대한
  joint grid sweep보다 **한 번에 한 제약씩** baseline 대비 co-tuning이 맞다.

**`cumul_yaw` headroom (기록, 저우선).** $8\pi$(4 rev)는 관측 운용 peak($\sim 1.22$ rev, §9 완전
inert)의 $\approx 3.3\times$이다. $6\pi$(3 rev)로의 cosmetic 트림은 여전히 inert — 행동상 no-op이라
향후 config 수정에 묻어가면 됨; *bind 의도* 값은 $\lesssim 2.5\pi$가 필요하고 정상 yaw 기동과
충돌하는지 따져야 한다.

---

## 4. ConstraintTRPO 최적화

알고리즘 본체: `algorithms/constraint_trpo.py`. `ConstraintTRPO`는 독립형
알고리즘이며(alias `ALBCConstraintTRPO`, `rsl_rl_ppo_cfg.py:25`),
`rsl_rl.PPO`의 서브클래스가 **아니다**.

**Provenance — 이것은 NORBC의 "Modified IPO"를 충실히 구현한 것이다(짜깁기 하이브리드가
아님).** 최적화 전체가 Kim et al., "Not Only Rewards But Also Constraints: Applications on
Legged Robot Locomotion", arXiv:2308.12517v4, 2024(KAIST Hwangbo lab)를 따르며, 모듈
docstring(`constraint_trpo.py:16-18`)에 명시돼 있다. 대응은 1:1이다: discounted budget
$d_k = D_k/(1-\gamma_c)$ = NORBC Eq. (8); **raw** $\hat{J}_{C_k}$ 레벨 + **표준화된** cost
surrogate로 이뤄진 trust-region barrier 목적함수(§4.1, §4.3) = NORBC Eq. (10); adaptive
threshold $d_k^i = \max(d_k, \hat{J}_{C_k} + \alpha d_k)$ = NORBC Eq. (11); multi-head cost
critic = NORBC의 shared-backbone cost value. NORBC는 IPO 원본의 PPO 스텝을 TRPO 스텝으로
교체한다(안정적 개선 + feasibility *checking*을 위한 선택 — enforcement가 아님). 따라서
아래에 기록된 두 이론적 "soft spot"(§4.1의 barrier saturation cap, §4.3의 raw-vs-표준화
margin)은 NORBC의 **의도된 설계이지 구현 결함이 아니다**. 상세 + 독립 검토 결론: wiki
`constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1.md`.

### 4.1 IPO log-barrier

Interior-point 목적함수(모듈 docstring 형태):

$$
\begin{aligned}
\max_{\pi}\quad & \mathbb{E}\!\left[A(s,a)\right] + \frac{1}{t}\sum_{k} \log\!\left(d_k^{i} - \hat{J}_{C_k}\right) \\
\text{s.t.}\quad & \mathrm{KL}\!\left(\pi \,\|\, \pi_i\right) \le \delta_{\max} \\
\text{where}\quad & d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right)
\end{aligned}
$$

코드에서 barrier는 update마다 다음과 같이 구성된다(`constraint_trpo.py:454-464`):

$$
\begin{aligned}
\text{margin}_k &= \underbrace{(d_k^{i} - \hat{J}_{C_k})}_{\text{barrier\_base}} - \text{cost\_surr}_k \\
\text{cost\_surr}_k &= \frac{1}{1-\gamma_c}\,\mathbb{E}\!\left[\text{ratio}\cdot \hat{A}^{C}_k\right] \\
\text{barrier} &= -\frac{1}{t}\sum_k \log\!\big(\text{margin}_k.\text{clamp}(\min=10^{-8})\big)
\end{aligned}
$$

두 가지 구현상의 사실이 중요하다. 첫째, **`margin`은 순수 차이일 뿐, $d_k$로
정규화되지 않는다** — 파일 어디에도 $\hat{J}_C / d_k$ 나눗셈이 없다. 둘째,
margin의 두 항은 **동일한 discounted-cost 스케일에 있지만 코드에서 동일한
계수를 곱하지 않는다**: `barrier_base = adaptive_d_k - mean_cost_returns`는
명시적 $1/(1-\gamma_c)$를 갖지 않는 반면, `cost_surr`는
`constraint_trpo.py:462`에서 `inv_one_minus_gamma`로 스케일된다(`mean_cost_returns`와
`adaptive_d_k` 둘 다 budget 재조정 $d_k = D_k/(1-\gamma_c)$를 통해 이미
discounted-return 스케일에 있음). `clamp(min=1e-8)`은 barrier가 infeasibility
경계에서/이후에도 결코 $-\infty$/$+\infty$에 문자 그대로 도달하지 못하게 막는다 —
구체적으로는 **제약당 $-\log(10^{-8})/t \approx 18.42/100 \approx 0.184$에서
포화(saturate)**하므로, reward-surrogate 이득이 ~0.184를 넘는 스텝은 경계를 그대로
통과한다. 이 clamp는 **NORBC Eq. (9)/(10)에는 없는** 수치 가드이며, interior-point의
"경계를 못 넘음" 성질을 경계 근처에서 엄밀히 강제하는 대신 조용히 완화한다. 이는
NORBC의 soft·near-satisfaction 설계(하드 per-step 보장을 주장하지 않음)와 일관되며,
adaptive threshold가 매 iteration raw cost return으로 재고정하므로 self-correcting이다.
(이 캠페인에서 앞서 barrier가 "$+\infty$로 발산해 스텝을 자동 거부한다"고 말한 것은
틀렸다 — clamp가 캡한다.)

**barrier_t / barrier_alpha — 실제 런타임 값(문서 drift 경고).**
`barrier_t = 100.0`은 클래스 생성자 기본값(`constraint_trpo.py:64`)과 agent
cfg(`rsl_rl_ppo_cfg.py:217`) 둘 다 동일 — drift 없음. **`barrier_alpha`는 확인된
drift가 있다**: 생성자 기본값은 `0.02`(`constraint_trpo.py:65`)이지만 실제
학습된 모든 run에 도달하는 값인 agent cfg는 `0.05`
(`rsl_rl_ppo_cfg.py:218`)다. `RslRlConstraintTRPOAlgorithmCfg` 필드는 build
시점에 생성자 kwarg로 dispatch되므로, cfg가 해당 필드를 공급할 때마다
**실효값은 0.05이고, 0.02 생성자 기본값은 죽은 코드**다. 일부 이전 노트는
0.02를(또는 이미 superseded된 0.05-vs-0.02 wiki 페이지를) 보고했으나, 코드
진실은 **agent cfg에서 주입되는 0.05**다. 의심스러울 땐 클래스 시그니처가
아니라 resolve된 per-run `params/agent.yaml`을 읽을 것.

### 4.2 Adaptive threshold와 violations 진단 지표

Adaptive threshold는 매 update마다 현재 배치의 mean cost return으로부터
재계산된다(`constraint_trpo.py:306-308`, `:446`에서 호출):

$$
d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right), \qquad
\hat{J}_{C_k} = \big(\text{mean cost return}\big)_k.\text{clamp}(\min=0)
$$

보고되는 `violations` 모니터링 지표는 $\hat{J}_{C_k}$를 adaptive threshold가
아니라 **raw** budget $d_k$와 비교한다: `violations = (mean_cost_returns - self.d_k)`
(`constraint_trpo.py:447`). `adaptive_d_k`는 barrier margin(`:454`)과 로깅되는
barrier margin(`:449`) 안에서만 사용된다.

### 4.3 Feasibility, GAE, standardization

- **Cost GAE.** Per-constraint advantage는 reward GAE와 동일한 재귀적
  $\delta/\lambda$-return 공식을 쓰되 `cost_gamma=0.99`, `cost_lam=0.95`,
  vectorized K-dim accumulator를 사용하고 시간 역순으로 실행한 뒤, rollout
  전체에서 NaN/Inf를 포함하는 constraint 열을 0으로 만드는 non-finite
  sanitize를 거친다(`constraint_trpo.py:285-300`). `cost_gamma`는 반드시
  $< 1$이어야 하며 아니면 생성자가 `ValueError`를 던진다(`:143-144`).
- **Feasibility level은 true return이 아니라 추정치다 (cost critic과의 결합).**
  모든 feasibility 판정을 구동하는 cost return — `barrier_base`, `violations`,
  adaptive threshold에 들어가는 `mean_cost_returns`(`constraint_trpo.py:443,447,454`)
  — 는 raw Monte-Carlo 할인합이 아니라 **GAE($\lambda_c$) return**
  `cost_returns = cost_advantage + cost_value`(`:291`)이다. 따라서 제약 만족 판정이
  `cost_lam=0.95` bias와 cost critic의 추정 오차를 함께 물려받는다. 이는 reward 측을
  미러링하지만 결과가 다르다: biased reward value는 policy-gradient 효율만 깎지만,
  *과소추정하는* cost critic은 실제 cost return이 이미 예산을 넘었는데도 barrier가
  **feasible**로 읽게 만든다 — 이 설계(critic 기반 constrained RL 공통)에 내재한
  추정 기반 제약 위반 리스크이지 코드 결함이 아니다.
- **Time-out bootstrapping.** time-out 시(termination이 아님) per-constraint
  cost는 `cost_gamma`와 per-constraint value 벡터로 bootstrap되며, 이는
  reward 측 bootstrap을 cost 채널에서 그대로 미러링한다
  (`constraint_trpo.py:264-266`).
- **Per-constraint cost-advantage standardization (NORBC Sec IV-B).** K개
  cost-advantage 열 각각은 flatten된 batch 차원에서 독립적으로
  mean/std-정규화되며, std는 **`min=1.0`**으로 floor-clamp된다
  (`constraint_trpo.py:437-438`). 이는 통상적인 `1e-8` epsilon이 아니라 의도적인
  anti-amplification 선택이다: 인라인 주석(`:436`)은 `# clamp(min=1.0): binary
  constraints can have near-zero std, causing 1e8 amplification.`라고
  적혀 있다. Reward advantage는 별도로 통상적인 `1e-8` guard로
  정규화된다(`:424-426`).
  - **따라서 barrier margin은 raw 레벨과 표준화된 delta를 섞는데 — 이것은 NORBC Eq.
    (10) 그 자체이지 코드 버그가 아니다.** `barrier_base`는 표준화 안 된
    `mean_cost_returns`를 쓰고, `cost_surr`는 표준화된 advantage를 쓴다(`:454` vs
    `:462`). NORBC는 *zero-mean* 절반에 의존해 문제를 `ratio=1`에서 항상 feasible로
    유지한다: 이때 $\mathbb{E}[\hat{A}^C_k]\approx 0$이라
    $\text{margin}_k \approx d_k^i - \hat{J}_{C_k} \ge \alpha d_k > 0$이 되어 매 update
    시작점에서 $\log$이 항상 정의된다. *std* 절반은 10개+ 제약을 안정적으로 쌓기 위한
    NORBC의 gradient-conditioning 장치다. 실무적 결과 — 런타임 cost-advantage std가 1을
    넘는 제약은 유효 경계가 살짝 **더 관대**해짐(barrier는 표준화 단위로 반응하는데
    예산은 raw) — 은 따라서 **어떤 제약의 cost-adv std가 실제로 1을 넘지 않는 한
    잠복(dormant)**이며, 이는 런 데이터로 답할 경험적 질문이지 패치할 버그가 아니다.
    표준화가 NORBC의 near-satisfaction 보장을 엄밀히 무효화하는지는 NORBC 자체에 대한
    비판이라 이 코드베이스 범위 밖이다.

### 4.4 TRPO trust-region 스텝

Natural-gradient 스텝은 **단일 결합 surrogate scalar**에 대해 동작한다
(`constraint_trpo.py:461,480`):

$$
L = -\,\mathbb{E}\!\left[A\cdot \text{ratio}\right] \;+\; \text{barrier} \;-\; \beta_{\text{ent}}\, H
$$

- **Gradient 그룹.** $g = \nabla_\theta L$, $\theta = (\text{actor}, \text{encoder}, \log\sigma)$에
  대해.
- **Fisher-vector product는 순수 KL curvature만 사용한다** — old policy와
  new policy 사이 Gaussian KL을 통한 double backprop에 Tikhonov damping
  $Fv + \lambda_{\text{cg}} v$가 더해진다(`constraint_trpo.py:354-365`). barrier의
  curvature는 Fisher에 **결코** 들어가지 않으므로, KL trust region은 constraint
  기하학을 "알지" 못한다.
- **Conjugate gradient.** `cg_iters=10`과 조기 종료 residual tolerance
  `1e-10`으로 $F x = g$를 푼다(`:367-386`).
- **스텝 크기.** $\Delta\theta = -\sqrt{\delta_{\max} / (\tfrac{1}{2}\tilde g^\top g)}\,\tilde g$;
  $\tfrac{1}{2}\tilde g^\top g \le 0$이거나 non-finite이면, 또는 스텝 방향에
  NaN/Inf가 있으면 update가 중단된다(`False` 반환, 스텝 없음, `:539-547`).
- **Line search.** Backtracking, shrink factor `0.5`, 최대 10회 backtrack;
  surrogate가 엄밀히 감소하고 **동시에** 실현된 $\mathrm{KL} \le \delta_{\max}\cdot \text{line\_search\_kl\_margin}$
  (margin `1.5`)일 때만 스텝을 수락한다(`:400-410`). 수락 경계가 초기 스텝
  크기를 정하는 $\delta_{\max}$보다 **더 느슨하다**는 점에 유의 — 수락된
  스텝은 명목 trust-region 반경을 최대 50%까지 초과할 수 있다. 소진 시
  파라미터는 `old_params`로 되돌아간다.

**실제 trust-region 값.** `max_kl`도 drift한다: 생성자 기본값 `0.002`
(`constraint_trpo.py:43`) vs agent cfg `0.005`(`rsl_rl_ppo_cfg.py:191`) —
agent cfg(0.005, 2.5배 더 느슨함)가 이긴다. `cg_damping=0.1`과
`line_search_kl_margin=1.5`는 생성자와 cfg가 일치한다(drift 없음).

### 4.5 std clamping

매 `_trpo_step` 이후(line-search 성공 여부와 무관하게) `log_std`가
clamp된다(`constraint_trpo.py:485-491`). 런타임에는 `min_std_per_dim`이
non-empty이므로 **per-dim floor 분기가 실제로 실행되는 것**이다:

$$
\text{min\_std\_per\_dim} = (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05), \qquad \text{max\_std} = 2.0
$$

Arm dim(인덱스 0,1)은 `0.10`에서, thruster dim(2-7)은 `0.05`에서 floor된다
(`rsl_rl_ppo_cfg.py:236`). scalar `min_std=0.05` agent-cfg 필드는
`min_std_per_dim`이 non-empty일 때(기본값이 그러함) 런타임에 **죽은
코드**다 — per-dim 텐서만 적용된다. 생성자의 scalar 기본값
(`min_std=0.01`, `min_std_per_dim=()`)은 scalar 분기를 타겠지만, cfg가 둘 다
override한다.

Entropy bonus도 동일한 per-dim-wins 패턴을 따른다: agent-cfg
`entropy_coef_per_dim = (0.01, 0.01, 0.001×6)`(`rsl_rl_ppo_cfg.py:229`)가
scalar `entropy_coef=0.003`(`:223`)을 override하므로, 후자도 런타임에는
죽은 코드다.

### 4.6 Cost critic

- **파라미터 그룹 분할.** 두 개의 서로소 그룹. **정책 그룹**(actor + encoder +
  `log_std`)은 TRPO natural gradient로 업데이트된다 — Adam도, optimizer
  객체도 없음; `log_std`는 KL trust region이 노이즈 변화를 제한하도록
  의도적으로 이 그룹에 포함되며, encoder도 분리 시 encoder 그래디언트가
  ~85% 감소한다는(코드 주석, `constraint_trpo.py:154-158`) 이유로 이 그룹에
  유지된다. **value 그룹**(`value_prefixes` 튜플 `critic.` / `cost_critic.` /
  `value_backbone.` / `reward_head.` / `cost_head.`에 매칭)은 `value_lr`로
  Adam이 업데이트한다(`:160-186`).
- **단일 multi-head cost critic.** cost critic은 관측당 K차원 벡터를
  생성하는 **하나의** 네트워크이며(`evaluate_costs()`), K개의 별도 네트워크가
  **아니다**. Reward critic과 cost critic은 하나의 backward pass에서 함께
  업데이트된다: $\text{total} = \text{value\_loss\_coef}\cdot L_V + \text{cost\_value\_loss\_coef}\cdot L_{V_C}$,
  두 계수 모두 `1.0`(`constraint_trpo.py:591-605`). Per-constraint MSE는
  배치에 대해 `.mean(dim=0)`으로 K-vector를 만든 뒤, constraint에 대해
  `.mean()`으로 scalar가 된다(`:596-597`). Critic head의 activation 상세는
  이 파일이 아니라 정책 클래스 `ALBCActorCriticEncoder`에 있다 — network-architecture
  레퍼런스 참조.
- **별도 네트워크, 그러나 gradient clip 하나를 공유 (reward/cost 결합).** `self.critic`
  (scalar reward value)과 `self.cost_critic`(K-dim)은 파라미터가 서로소인 **독립** MLP
  둘이다 — backbone 공유 없음(`encoder/_policy_base.py:86,91`); `value_prefixes`의
  `value_backbone.` 항목은 분류용 catch일 뿐 `ALBCActorCriticEncoder`의 실제 공유 trunk가
  아니다. 파라미터가 서로소라 결합 `total.backward()`는 두 gradient를 교차 결합하지 않는다
  ($\partial L_{V_C}/\partial\,\theta_{\text{reward critic}} = 0$). **단 한 곳이 둘을 결합한다:**
  value 업데이트가 두 critic 파라미터의 **합집합**에 대해 *단일*
  `clip_grad_norm_(self._value_params, max_grad_norm=1.0)`을 적용한다(`constraint_trpo.py:601-605`).
  cost critic은 rare-event return을 맞추는 $K=10$ head라 gradient가 합산 norm을 지배할 수
  있고, 합집합 norm이 `1.0`을 넘으면 clip이 *두* critic을 같은 비율로 축소해 노이즈 많은 cost
  critic이 reward critic의 실효 스텝을 throttle할 수 있다. 서로 독립인 두 네트워크 사이의 실제
  결합 — flag만 하고 유해함은 미증명(런타임 value-group grad-norm 확인 필요).

---

## 5. Constraint-margin 정규화 ($\hat{J}_C / d_k$)

**Optimizer는 절대 margin을 저장한다; binding/slack 판단을 하려면 반드시
먼저 $d_k$로 정규화해야 한다.** 이는 분석 규칙이지 코드 동작이 아니다 —
barrier 자체는 절대 margin을 올바르게 사용하지만(Section 4.1), 사람이나
엔진이 TensorBoard에서 `Constraint/margin/<name>`을 읽을 때는 constraint
간 비교를 위해 $d_k$로 나눠야 한다.

부호가 뒤집히는 이유: discounted budget $d_k = 100 \cdot D_k$는 10개
constraint에 걸쳐 **40배**의 범위를 갖는다(`attitude`는 $D_k=0.01$에서
$d_k = 1.0$, `thruster_util`은 $D_k=0.40$에서 $d_k = 40.0$). Slack이 깊지만
budget이 큰 constraint는 절대 margin이 크게 나오고, budget에 가깝지만
budget이 작은 constraint는 절대 margin이 작게 나온다. 따라서 raw margin을
그대로 읽으면 결론이 뒤바뀐다.

올바른 정규화 값은 다음과 같다.

$$
\frac{\hat{J}_{C_k}}{d_k} = 1 - \frac{\text{margin}_k}{d_k},
$$

이는 adaptive floor가 작동하지 않은, 즉
`Constraint/viol/<name> == -Constraint/margin/<name>`이 정확히 성립하는
**slack 영역에서만** 유효하다(`constraint_trpo.py:447` vs `:449`).
$\hat{J}_{C_k} + \alpha d_k > d_k$이면 adaptive threshold가 작동해
$d_k^i \ne d_k$가 되고, 그 identity가 깨진다.

**실험적 발견(그렇게 명시).** 실제 teacher-run 리포트(`report.md:174,180`)가
`attitude`와 `cumul_yaw`를 절대 margin이 숫자상 작아 보인다는 이유로
"binding family"로 오독한 사례가 있다 — 실제로는 $\hat{J}_C/d_k = 0.003$과
$0.000$(가장 깊은 slack)이었던 반면, 진짜로 binding인 `thruster_util`
($\hat{J}_C/d_k \approx 0.87$)은 단지 budget이 커서 절대 margin이 *크게*
나온 것이었다. 엔진은 commit `4ff9ea1`(2026-06-07)부터 정규화한다:
`.omx/profile/analyze_training.py`가 `_constraint_binding_ratio`(`:416-430`,
$1 - \text{margin}/d_k$)를 계산하고 `JC/dk=` 컬럼(`:809`)으로 max ratio 기준
binding 채널을 플래그하며(`:820`) `test_constraint_margin_norm.py`로 pin된다.
저수준 `_constraint_margin()`(`:370-379`)은 여전히 raw 절대 margin을 반환하지만
그 소비자(`:803`)가 정규화한다. 수동 공식과 마찬가지로 엔진 비율도 로깅된 margin을
소비하므로 slack 영역에서만 정확하고, 진짜 binding 채널은 margin이 $\alpha d_k$로
동결돼 $1-\alpha = 0.95$에서 saturate한다. 출처: omx wiki
`constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md`.

---

## 6. DORAEMON과 constraint

DORAEMON은 domain-randomization 커리큘럼이다. 여기서 다루는 초점은
constraint/feasibility 메커니즘과의 상호작용이며, DR 메커니즘 자체는
marinelab에 있다. 메인 env는 네 필드를 override한다(`config.py:479`):
`DoraemonCfg(enable=True, kl_ub=0.12, performance_lb=250.0, step_interval=250)`.

- **`alpha`는 feasibility floor이지, DR lever가 아니다.** DORAEMON의
  `alpha`(config 근거 주석에서 `0.5`로 인용됨, `config.py:473-474`; 실제
  필드 기본값은 marinelab의 `DoraemonCfg`에서 오며 읽은 파일들에서는 검증되지
  않음)는 curriculum-difficulty 스텝이 *수락*되는지 여부를 게이트한다 —
  randomization을 직접 넓히지 않는다. **실험적 발견:** `alpha`를 `0.50 -> 0.75`로
  올린 것(E5, run `trpo_260606_225859`)은 거의 null intervention이었다 —
  `success_rate`가 run 내내 `0.96-0.99`로 포화돼 있어 floor가 스텝을 게이트한
  적이 없었기 때문이다. DR-expansion 속도를 실제로 제약하는 것은 per-update
  trust-region KL(`kl_ub`, 그 run에서 0.06 고정)이다. robustness를 넓히려면
  `alpha`가 아니라 `kl_ub` 또는 DR 분산을 직접 움직여야 한다. 출처: omx wiki
  `doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md`.

- **`performance_lb`와 `kl_ub`는 설계상 함께 올려졌다**(`config.py:466-478`).
  `performance_lb`는 `68.0 -> 250.0`으로, `kl_ub`는 `0.06 -> 0.12`로 올라갔다.
  이 보정은 recon run(`trpo_baseline_260608_160453`, 1146 iter)을 사용했다:
  그 run의 DORAEMON episode-return 분포는 min=81.9 / p5=227 / p25=250 /
  median=264 / p95=291이었다. `lb=68`이 최솟값보다 *아래*에 있으면
  `success = return >= 68`이 항상 `1`이 되어, feasibility constraint
  ($\hat G \ge \alpha$)가 **비활성(inert)**이 되고 curriculum이 self-pacing
  피드백 없이 DR을 무제한으로 넓혔다. `lb=250`(p25)은 시작 `success_rate`를
  ~0.65로 만든다 — `alpha=0.5`보다 위라서 분포는 여전히 확장되지만 신호는
  1에 고정되지 않고 다시 살아난다; median보다 낮게 선택한 이유는 reward
  plateau가 `success_rate`를 0으로 끌어내리지 않게 하기 위함이다. `kl_ub`는
  올라간 `lb`가 야기하는 느려진 확장 속도를 보상할 만큼 분포를 빠르게
  넓히기 위해 두 배로 늘어났다. 두 lever는 설계상 함께 움직인다: `lb`
  단독은 DR을 쉽게 만들고, `kl_ub` 단독은 `success_rate`를 1에 고정된
  채로 남긴다.

- **`success`의 정의.** `success = accumulated_episode_return >= performance_lb`,
  `albc_env.py`에서 계산됨(`_episode_return_accum += reward`;
  `success = return >= performance_lb`; `config.py:467` 주석).

`step_interval = 250`은 curriculum이 얼마나 자주 업데이트되는지를 정한다.

---

## 7. joint1 anti-drift 실험

기본 비활성 토글이 joint-1 anti-drift를 테스트하기 위해 **11번째**
constraint term을 추가할 수 있다. `ALBCEnvCfg`의 필드 2개:

- `joint1_constraint_arm: str = "none"` — `{"none", "B"}` 중 하나
  (`config.py:552`).
- `joint1_constraint_budget: float = 0.05` — joint1 term의 per-step average
  budget $d_k$(`config.py:553`).

**Materialization 경로.** `apply_joint1_constraint_arm()`
(`constraints.py:279-299`)이 arm을 읽는다; `"none"`은 no-op; `"B"`는
`joint1_cumulative_cost` term을 추가(이름 `joint1_cumulative`); 그 외 값(이제는
존재하지 않는 구 `"A"` 포함)은 `ValueError`를 던진다.
`env_cfg.constraints.terms = [*env_cfg.constraints.terms, term]`을 통해 추가한다.

**왜 cfg의 `__post_init__`이 아니라 `ALBCEnv.__init__`에서 호출되는가.**
호출 지점은 `albc_env.py:128`, `ALBCEnv.__init__` 내부(payload-viz와
DR-sampler init 이후)다. 이는 의도적이다: hydra의
`update_class_from_dict` override는 cfg `__post_init__` *이후*,
`ALBCEnv.__init__` 실행 *이전*에 적용된다(`constraints.py:279-291`,
`albc_env.py:123-127`). 이 호출을 `__post_init__`에 넣으면 항상
`arm="none"`을 관측하게 되어, arm B 대신 조용히 baseline과 중복되는
run이 생성될 것이다.

**유일한 anti-drift 메커니즘.** arm B(`joint1_cumulative_cost`)가 이제 코드베이스
전체에서 유일한 joint1 anti-drift 메커니즘이다. reward-side centering penalty와
wrapped-instantaneous constraint(구 "arm A") 둘 다 2026-07에 제거됐으므로,
이전의 "double-counting을 피하려면 reward의 centering 계수를 0.0으로
설정하라"는 요구사항은 더 이상 적용되지 않는다 — 이제 double-count될 대상
자체가 없다.

**동작 — station-keeping 하에서는 결코 binding되지 않음(실험적 발견).**
평탄한 target station-keeping 태스크에서 joint1-cumulative constraint는
사실상 결코 binding되지 않는다: 정책은 $\pm 4\pi$(2회전) 레일 깊숙이 안쪽인
**0.36 회전** 근처에 자연스럽게 자리 잡으며, violation 지표는 매 iteration
**-0.9997**(거의 완전한 headroom)에 머물고, 4개 DR 난이도 레벨 전체에서
peak $\lvert\theta_{\text{cum}}\rvert$가 ~1.22 회전을 넘은 적이 없다
(64개 env 중 0개가 $> 4\pi$). 출처: omx wiki
`joint1_cumulative_rotation_constraint_never_binds_policy_parks_a.md`
(run `trpo_joint1_cumul_rot_260629_183545`). *주의:* 그 wiki의 run은 이
term을 probabilistic $\mathbb{1}[\lvert\theta_{\text{cum}}\rvert > 4\pi] \le 0.01$
constraint로 프레이밍하는 반면, 실려 있는 코드의 함수
`joint1_cumulative_cost`는 *average* $\lvert q^{\text{des}}_1 - q^{\text{nom}}_1 \rvert$
cost다 — 동일한 실험 라인이 run에 따라 두 변형을 오간다; 실질(결코
binding되지 않음)은 유지된다.

**Binding되지 않으면서도 OOD로 일반화됨(실험적 발견).** station-keeping
하에서 결코 binding되지 않음에도, 동일한 constraint 라인은
out-of-distribution에서도 누적 회전 drift를 bounded 상태로 유지한다(drift
slope $2.2\times 10^{-4}$ rad/s, p95 최종 $\lvert\text{drift}\rvert = 0.177$
rad $< 0.224$ rad budget) — 심지어 무관한 attitude tracker가 진짜 OOD
heavy tail을 보이는 동안에도 그렇다(roll steady-state error env-median
0.36° vs env-mean 3.87°, worst env 63°). 출처: omx wiki
`joint1_cumulative_ipo_constraint_generalizes_drift_bounded_at_oo.md`
(run `trpo_cumul_constraint_260627_231709`). *주의:* 이 페이지는 이를
"binding average-constraint"라고 부르는 반면 위의 동반 페이지는 동일
라인을 결코 binding되지 않는다고 문서화한다 — 이 불일치는 소스 지식 자체에
있으며(아마도 "binding"이 "active/present"를 느슨하게 의미하도록 쓰인 것으로
보임), 여기서는 조정하지 않고 그대로 표시해 둔다.

**기본 비활성 = byte-identical.** 기본값인 `arm="none"`에서는
`apply_joint1_constraint_arm`이 즉시 반환하고, 실려 있는 10개 term
집합은 그대로 유지되며 K는 10을 유지한다. arm B를 활성화하면 정확히 하나의
cost-critic head가 추가된다; MLP 레이어 수, 차원, activation은 변하지
않는다.

---

## 8. 로깅 / 지표

Constraint 지표는 학습 iteration마다 한 번
`ConstraintEncoderRunner._log_constraint_metrics`가 방출한다(override된
`log()`에서 호출되며 `self._should_log`에 게이트됨;
`constraint_encoder_runner.py:248-250`). 알고리즘은 이 로깅에서만 읽히는
per-step running state(`_last_violations`, `_last_barrier_margins`,
`_last_barrier_penalty`)를 유지한다(`constraint_trpo.py:129-133`).

| 지표 | 의미 |
|---|---|
| `Constraint/viol/<name>` | $\hat{J}_{C_k} - d_k$, **raw** discounted budget과 비교(`constraint_trpo.py:447`); 음수 = slack |
| `Constraint/margin/<name>` | $d_k^i - \hat{J}_{C_k}$ (adaptive-threshold margin, `:449`); **절대값**, $d_k$-정규화 안 됨 |
| `Constraint/barrier_penalty` | 집계된 scalar barrier penalty (per-constraint 접미사 없음) |
| `Policy/line_search_success` | 이번 update의 line-search 수락률 |
| `Policy/entropy` | 평균 정책 entropy |

`<name>` 접미사는 constraint에 설정된 이름이며
(`ALBCConstraintCfg.constraint_names`, `constraints.py:76-77`), 없으면
숫자 인덱스로 대체된다. 네임스페이스는 viol/margin에 대해 2-레벨
`Constraint/<type>/<name>` 계층과 flat한 `Constraint/barrier_penalty`로
구성된다; DORAEMON curriculum 지표는 별도의 `DORAEMON/*` 네임스페이스를,
정책 진단은 `Policy/*` 네임스페이스를 쓴다.

**Anomaly threshold**는 분석 엔진이 플래그한다(`analyze_training.py`
`ANOMALY_RULES`): `line_search_success < 0.5` FAIL("TRPO line search
failing. Cost gradient may dominate. Check barrier_t and constraint
budgets."), `barrier_penalty > 0.1` SPIKE; 그리고 일반 RL-health 규칙
`entropy < 0` COLLAPSED, `noise_std < 0.25` LOW / `>= 0.95` CEILING,
`z_std < 0.1` LOW, `grad_norm < 1e-4` DEAD, `roll_deg > 20` HIGH,
`pitch_deg > 25` HIGH. **오래된 wiki 노트에 대한 정정:** encoder-latent
saturation 규칙은 실제 엔진 코드에서 `Encoder/z_min < -0.98` /
`Encoder/z_max > 0.98`을 쓰며(`analyze_training.py:41-42`), 일부 노트가
말하는 $\pm 0.95$가 **아니다**. `thruster_util_max > 0.95`는 wiki에서
saturation anomaly로 인용되지만 엔진 코드의 `ANOMALY_RULES`에는 대응
항목이 없다 — 코드로 인코딩된 규칙이 아니라 분석 heuristic으로 취급할 것.

---

## 9. 실제로 binding되는 constraint (실험적 발견)

이 섹션의 모든 내용은 이전 분석 run에서 나온 **실험 결과**이며, 위의 코드
정의와는 의도적으로 분리해 두었다. 이것들을 코드 불변식으로 취급하지 말 것;
특정 run이 보여준 것일 뿐이다.

**`thruster_util`만 binding된다.** 실려 있는 10개 constraint 중
`thruster_util`만이 실제로 discounted budget에 도달한다 — teacher run에서
$\hat{J}_C/d_k \approx 0.869\text{-}0.870$. 나머지 9개는 slack에 있으며,
여러 개는 상당히 깊은 slack이다: `rp_vel_settling` 0.455, `arm_torque`
0.407, `rp_rate` 0.319, `yaw_rate` 0.138(slack); `manipulability` 0.038,
`arm_joint_vel` 0.031, `joint1_pos` 0.005, `attitude` 0.003(deep slack);
`cumul_yaw` 0.000("완전히 inert"). 출처: omx wiki
`constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md`.
(참고: teacher run의 binding 수치는 ~0.87이며, 이 teacher run에서 0.94라는
근거는 없다 — 아래 0.944 수치는 teacher가 아니라 E6 budget-halving run의
것이다.)

**Budget ×0.5는 authority를 고갈시킨다.** E6 실험은 10개 budget 전부를
반으로 줄였다. `thruster_util`만 반응해서 binding으로 *더* 파고들었다
($\hat{J}_C/d_k$가 $0.869 \to 0.944$로 상승); 나머지 9개는 slack에
머물렀다. control-authority 채널에서의 그 추가 binding 하나가 authority
starvation을 일으켰다: per-step reward가 54% 하락했고(Reward/total
7.96 -> 3.68), lin_vel reward가 음수가 됐으며(lin_vel reward 채널은 이후
제거됨), 정책 entropy가 붕괴했다(iter 2289에서 0을 통과, teacher run에서는
본 적 없는 anomaly).
**규칙:** control-authority 채널(thruster)을 조이는 것은 파괴적이다.
출처: omx wiki
`constraint_budget_x0_5_binds_only_thruster_util_authority_starva.md`.
이 binding 결론은 slack 영역에서 계산된 것이므로
($\hat{J}_C = d_k - \text{margin}$) `barrier_alpha`와 무관하며 0.02, 0.05
어느 쪽에서도 성립한다.

**`success = return >= 68`이었을 때 feasibility constraint는 inert했다.**
과거 `performance_lb=68`이 최소 episode return보다 아래에 있어서
`success`가 1에 고정됐고, DORAEMON feasibility constraint가 전혀
발동하지 않았으며, curriculum이 self-pacing 피드백 없이 DR을 넓혔다 —
Section 6에서 `lb 68 -> 250` / `kl_ub 0.06 -> 0.12` 재보정의 정확한
동기다.

---

## 소스 파일

- `constrained_albc/envs/main/mdp/constraints.py` — 실려 있는 10개 cost 함수 + 실험 전용 joint1 term 1개, `ConstraintTermCfg`, `ALBCConstraintCfg`, `compute_all_costs`, `apply_joint1_constraint_arm`(2-way `{none, B}`)
- `constrained_albc/envs/main/config.py` — `ALBCEnvCfg`, `_FULL_DOF_CONSTRAINT_TERMS`(실려 있는 10개 budget), DORAEMON override, joint1 토글
- `constrained_albc/envs/main/config_noconstraint.py` — `ALBCNoConstraintEnvCfg`(terms=[], TRPO-NoIPO / PPO-Enc ablation)
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — ConstraintTRPO + IPO barrier, adaptive threshold, cost GAE, TRPO step, std clamp, cost critic
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `RslRlConstraintTRPOAlgorithmCfg`(런타임 barrier_alpha/max_kl/std/entropy 값)
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — `_log_constraint_metrics`, `num_constraints` auto-sync
- `.omx/profile/analyze_training.py` — `ANOMALY_RULES`, `_constraint_margin`
