# 메인 네트워크 아키텍처 (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 신경망 아키텍처. attitude-only ALBC 정책
> (roll/pitch + yaw-rate, 선속도 명령 없음)이며, 8D action(2D arm + 6D thruster),
> 69D actor 관측, 27D privileged 관측을 갖는다.
>
> 본 문서는 `exp/joint1-constraint-redesign` 브랜치에서 디스크 코드에 대해 검증한
> 코드 레벨 레퍼런스다. 네트워크 코드(`encoder/`, `agents/`, `algorithms/`,
> `runners/`)는 이 브랜치에서 `main`과 byte-identical이며, constraint 정의만
> 다르다(§6 참조). 레거시 full-DOF 변형(`envs/full_dof/`,
> `Isaac-ConstrainedALBC-Full-*-v0`, 87D obs / 24D privileged)은 다른 네트워크이며
> 여기서 다루지 않는다.
>
> **English version**: [`main-network-architecture.md`](main-network-architecture.md) (SSOT).
> 두 파일 중 하나를 고치면 다른 하나도 동기화할 것.

---

## 1. 전체 구조 한눈에

RMA/HORA 계열의 teacher actor-critic 정책으로, **비대칭(asymmetric) critic**과
**별도의 multi-head cost critic**을 갖는다. **encoder**가 27D privileged physics
벡터 `p_t`를 9D latent `z`로 압축하고, **actor**는 69D 관측 `o_t`와 `z`만 본다
(`p_t`에는 blind). **reward critic**과 **cost critic**은 모든 정보
(`o_t + z + p_t`, 105D)를 직접 본다.

```
ENV obs dict  ->  {"policy": o_t (69D),  "privileged": p_t (27D)}

ENCODER  (입력 = p_t 27D, 관측 전체가 아님)
  p_t(27D) -> static min-max 정규화 -> [-1, 1]      # HORA식, 결정론적, running stat 없음
          -> MLP[256, 128, 64]  (elu)
          -> LayerNorm(9)                            # pre-softsign
          -> softsign  ->  z (9D)                    # encoder_latent_dim = 9

ACTOR  (입력 78D)
  cat[ EmpiricalNorm(o_t)(69D), z_raw(9D) ]          # o_t만 정규화; z는 이미 softsign으로 bound됨
          -> MLP[256, 128, 64]  (elu)
          -> action_mean (8D = 2D arm + 6D thruster) # action에 output activation 없음
  std = exp(global log_std[8]) -> expand             # state-INDEPENDENT
        init 0.7; ConstraintTRPO가 update 후 clamp

CRITIC  (asymmetric, 입력 105D, critic_uses_z = True)
  cat[ o_t(69D), z(9D), p_t(27D) ] (raw)             # value 그래디언트가 z를 거쳐 encoder로 역류
          -> MLP[512, 256, 128]  (elu) -> value (1D)

COST CRITIC  (multi-head, K = num_constraints)
  cat[ o_t(69D), z(9D), p_t(27D) ] (동일 105D 입력)
          -> MLP[512, 256, 128]  (elu) -> cost_values (K)   # constraint당 scalar head 1개
```

**핵심 설계 결정 3가지.**
1. encoder 입력은 *관측이 아니라 privileged physics 벡터*다(실로봇에서는 관측
   불가). `z`가 actor에게 "이 환경의 물리가 무엇인지"를 알려준다.
2. critic은 비대칭이다 — privileged 정보를 직접 읽고(105D), actor는 압축된 `z`만
   받는다(78D). `critic_uses_z = True`이므로 value-loss 그래디언트가 `z`를 거쳐
   encoder로 역류한다. 따라서 encoder는 정책 신호와 가치 신호 **양쪽**으로 학습된다.
3. encoder는 Adam value 그룹이 아니라 **TRPO natural-gradient 정책 그룹**(actor,
   `log_std`와 함께)에 들어간다 — 분리하면 encoder 그래디언트가 ~85% 감소한다는
   코드 주석이 근거.

---

## 2. 관측·액션 차원

아래 모든 차원은 디스크 코드로 검증됐고, `albc_env.py`의 런타임 assertion으로
강제된다(조립된 obs가 `observation_space = 69`와 다르면 `ValueError`).

### 2.1 Actor 관측 — 69D (`o_t`)

| 블록 | 구성 | 차원 |
|---|---|---:|
| 현재 proprioception | ang_cmd(3) + euler(3) + ang_vel(3) + joint_pos(2) + joint_vel(2) + manipulability(1) + thruster_state(6) | 20 |
| Joint/body history | (joint_err 4 + body_err 6) x 3 steps (`hist_len=3`) | 30 |
| Action history | full_action 8 x 2 steps (`hist_action_len=2`) | 16 |
| Integral error | leaky integrator [roll, pitch, yaw_rate] | 3 |
| **합계** | | **69** |

출처: `mdp/observations.py:compute_policy_obs()`(20D 현재) +
`albc_env.py:_get_observations()`(46D history + 3D integral).
`policy_obs_dim=69`(`agents/rsl_rl_ppo_cfg.py:138`).

### 2.2 Privileged 관측 — 27D (`p_t`)

시뮬레이터 전용 ground truth(DR된 물리 파라미터 + 측정 선속도. 선속도는 실로봇에
센서가 없음 — DVL 없음).

| 그룹 | 구성 | 차원 |
|---|---|---:|
| Hydrodynamics | volume(1) + CoG(3) + CoB(3) | 7 |
| Dynamic response | Ixx + linear/quadratic damping (roll) + body_mass + added_mass (surge) | 5 |
| Payload | mass(1) + CoG offset(3) | 4 |
| Actuator | Kp + Kd + thrust_coeff + time_constant_up | 4 |
| Environment | water_density(1) + ocean current velocity (3) | 4 |
| 측정 선속도 | body linear velocity u, v, w | 3 |
| **합계** | | **27** |

출처: `mdp/observations.py:compute_privileged_obs()`. 앞 24D는 DR 파라미터,
마지막 3D는 측정 body 선속도(critic 전용)다 — 실로봇이 측정할 수 없으므로 `o_t`에서
제외된다. `privileged_dim=27`(`agents/rsl_rl_ppo_cfg.py:139`).

### 2.3 Action — 8D

| 인덱스 | 구성요소 | 매핑 |
|---|---|---|
| `[0:2]` | arm joint delta (2D) | `q_des += 0.10 * a` (`ALBC_JOINT_NAMES`에 누적되는 PD target) |
| `[2:8]` | thruster 명령 (6D) | T0-T5, `ThrusterModel.apply_dynamics()`에 입력, 6x6 TAM으로 body-frame 6-DOF wrench로 할당 |

raw action은 사용 전 `[-1, 1]`로 clamp된다(`albc_env.py`). actor MLP은 action mean을
직접 출력한다 — **output activation 없음**(action에 tanh/softsign 미적용; softsign은
latent `z`에만 적용).

### 2.4 네트워크로의 라우팅

`_get_observations()`는 `{"policy": (N, 69), "privileged": (N, 27)}`를 반환한다.
encoder는 `privileged`를, actor는 `policy + z`를, critic·cost critic은
`policy + z + privileged`를 소비한다. 비대칭 분할은 rsl-rl `obs_groups` 경로로
하지 **않는다** — 두 그룹 모두 `["policy", "privileged"]`로 선언되고, 정책 클래스가
`policy_obs_dim=69`·`privileged_dim=27` cfg 필드로 내부에서 slice한다.

---

## 3. 네트워크 레이어 (cfg -> 차원)

런타임 네트워크는 `_ALBCPolicyCfg`(`agents/rsl_rl_ppo_cfg.py`)를 dict로 flatten한 뒤
`OnPolicyRunner`가 `class_name="ALBCActorCriticEncoder"`(`:153`)를 `eval()`로 resolve하고
나머지를 kwargs로 넘겨 빌드된다.

| 컴포넌트 | 입력 | Hidden | 출력 | Activation | cfg 라인 |
|---|---|---|---|---|---|
| Encoder | 27 (`privileged_dim`) | [256, 128, 64] | 9 (`encoder_latent_dim`) | elu + LayerNorm + softsign | hidden `:130`, latent `:134`, act `:135` |
| Actor | 78 = 69 + 9 | [256, 128, 64] | 8 (`num_actions`) | elu | `:126`, act `:128` |
| Critic | 105 = 69 + 9 + 27 | [512, 256, 128] | 1 | elu | `:127`, act `:128` |
| Cost critic | 105 (동일) | [512, 256, 128] | K | elu | `:160` |

- actor에서는 `o_t`(69D)만 EmpiricalNorm을 거친다; `z`는 raw로 들어간다.
- `critic_uses_z=True`(`:154`)이면 critic 입력이 105D가 된다(False면 96D).
- `encoder_output_norm=True`(`:155`)가 softsign 직전 LayerNorm을 추가한다.
- cost critic은 `num_constraints > 0`일 때만 빌드된다.

**실제로 shape을 결정하는 필드(live wires):** `policy_obs_dim=69`(`:138`),
`privileged_dim=27`(`:139`), `encoder_latent_dim=9`(`:134`),
`critic_uses_z=True`(`:154`), `encoder_output_norm=True`(`:155`),
`num_constraints`(env에서 auto-sync, §6 참조), 그리고 네 개의 `*_hidden_dims` 리스트.
`init_noise_std=0.7`(`:123`)이나 `*_normalization` 플래그는 레이어 shape을 바꾸지 않는다.

**Encoder 입력 정규화**는 static min-max(HORA식)이며 `EmpiricalNormalization`이
아니다(`encoder_obs_normalization=False`, `:136`): encoder가 `(2*p_t - (U+L)) / (U-L)`를
계산한다. running statistics 없이 결정론적이라 `z` drift / KL spike를 피한다.

경계 `[U, L]`은 runner build 시점에 **DR config에서 도출**된다
(`envs/main/utils/priv_obs_bounds.py`의 `derive_priv_obs_bounds_from_dr()`,
`num_constraints` auto-sync처럼 `ConstraintEncoderRunner.__init__`이 주입). bound = DR
범위 정확히(마진 0)이므로 DR을 바꾸면 자동 동기화된다. `agents/rsl_rl_ppo_cfg.py`의 옛
하드코딩 `_PRIV_OBS_LOWER/UPPER`는 construct-time fallback으로만 남는다(`student/teacher.py`가
아직 import). 이 상수들은 DR과 drift해 있었고(payload-mass overflow, stale CoG-xy radius) —
이것이 도출 refactor의 이유다. 종단 `_assert_bounds_match_dr()`가 향후 DR 변경으로 도출
경계가 어긋나면 loud-fail한다. (브랜치 `exp/dr-derived-norm-bounds`, audit 항목 B1;
`docs/plans/2026-06-30-dr-derived-priv-obs-normalization-bounds.md` 참조.)

### 3.1 클래스 계층

`PolicyBase(nn.Module)`이 공통 base다(obs-group 파싱, dim 체크,
critic / cost_critic 구성, global `log_std`, Gaussian). `forward()`는
`NotImplementedError`를 던지고, 실제 진입점은 `act() / act_inference() / evaluate()
/ evaluate_costs()`다. 두 서브클래스가 이를 **형제로** 상속한다:

- `ActorCriticEncoder(PolicyBase)` — encoder teacher 정책(배포 default,
  `class_name="ALBCActorCriticEncoder"`).
- `ActorCriticAsymConstrained(PolicyBase)` — NoEncoder ablation(actor가 69D `o_t`만,
  critic은 `cat([o_t, p_t]) = 96D`, `class_name="ALBCActorCriticAsymConstrained"`,
  `:296`).

`ActorCriticAsymConstrained`는 `ActorCriticEncoder`를 상속하지 **않는다**.

---

## 4. Actor std 처리

`std`는 **단일 global `log_std` 파라미터**(state-INDEPENDENT)로 batch 전체에
broadcast된다: `log_std = nn.Parameter(num_actions)`, `std = exp(log_std)`. per-state
std head는 없다 — `state_dependent_std`는 어느 `envs/main` cfg에도 설정돼 있지 않다
(per-state std head는 별도의 미병합 실험 브랜치 `exp/attitude-only-state-std`).

| 필드 | 값 | cfg 라인 |
|---|---|---|
| init_noise_std | 0.7 | `:123` |
| min_std / max_std (clamp 바닥/천장) | 0.05 / 2.0 | `:221` / `:222` |
| min_std_per_dim (arm=0.10, thruster=0.05) | (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05) | `:225` |
| entropy_coef (scalar) | 0.003 | `:212` |
| entropy_coef_per_dim (arm=0.01, thruster=0.001) | (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001) | `:218` |

clamp는 정책 클래스 **내부에 없다** — `ConstraintTRPO`가 매 update 후 `log_std`를
dim별로 clamp한다(§5).

---

## 5. ConstraintTRPO + IPO 업데이트

알고리즘 본문: `algorithms/constraint_trpo.py`
(`class_name="ALBCConstraintTRPO"`, `:177`). 목적함수(모듈 docstring 인용):

$$
\begin{aligned}
\max_{\pi}\quad & \mathbb{E}\!\left[A(s,a)\right] + \frac{1}{t}\sum_{k} \log\!\left(d_k^{i} - \hat{J}_{C_k}\right) \\
\text{s.t.}\quad & \mathrm{KL}\!\left(\pi \,\|\, \pi_i\right) \le \delta \\
\text{where}\quad & d_k^{i} = \max\!\left(d_k,\; J_{C_k} + \alpha\, d_k\right)
\end{aligned}
$$

업데이트 단위 흐름:

```
ROLLOUT -> reward GAE + constraint별 cost GAE (K constraints, cost storage shape (T,N,K))
  |
update():
  - IPO adaptive thresholds (위반 시 threshold 상향, -log 폭주 방지)
  - surrogate 구성 후 natural-gradient TRPO step (아래 수식 참조)
  - clamp log_std to [log min_std, log max_std]  (dim별)
  - Adam MSE on critic + cost_critic (num_learning_epochs x num_mini_batches)
```

`update()` 내부의 natural-gradient step:

$$
\begin{aligned}
\text{IPO threshold:}\quad & d_k^{i} = \max\!\left(d_k,\; J_{C_k} + \alpha\, d_k\right) \\
\text{surrogate:}\quad & L = -\,\mathbb{E}\!\left[A\cdot r\right] \;-\; \frac{1}{t}\sum_k \log(\text{margin}_k) \;-\; \beta_{\text{ent}}\, H \\
\text{gradient:}\quad & g = \nabla_{\theta} L \quad (\theta = \text{actor},\, \text{encoder},\, \log\sigma),\quad \lVert g \rVert \le 1.0 \\
\text{natural grad:}\quad & \tilde{g} = F^{-1} g \;\;(\text{CG, } \texttt{cg\_iters}=10),\quad Fv = \nabla^2_{\theta}\,\mathrm{KL}(\mathcal{N})\,v + \lambda_{\text{cg}}\, v \\
\text{step:}\quad & \Delta\theta = -\sqrt{\frac{\delta_{\max}}{\tfrac{1}{2}\,\tilde{g}^{\top} g}}\;\tilde{g} \\
\text{line search:}\quad & \Delta L > 0 \ \text{및}\ \mathrm{KL} \le 1.5\,\delta_{\max} \text{이면 accept}\quad(\text{backtrack} \times 10)
\end{aligned}
$$

여기서 $r$은 importance ratio, $H$는 정책 entropy, $\beta_{\text{ent}}$는 entropy
계수, $\lambda_{\text{cg}}$는 CG damping, $\delta_{\max}=\texttt{max\_kl}$.

**파라미터 그룹 분할**(이름 prefix 기준): `("critic.", "cost_critic.")`에 매칭되는
이름은 **Adam** optimizer(`value_lr`)로, 나머지 — actor MLP, `encoder.*`, bare
`log_std` — 는 **TRPO natural-gradient** 그룹으로 간다. encoder는 의도적으로 정책
그룹에 둔다(분리 시 encoder 그래디언트가 ~85% 감소, 코드 주석); `log_std`는 KL trust
region이 entropy collapse를 damping하도록 정책 그룹에 둔다.

**FVP / log_std.** Fisher-vector product는 `Normal(action_mean, action_std)` 분포에
대한 순수 KL Hessian을 계산한다. `action_std = exp(log_std)`이므로 `log_std`는 Fisher
curvature와 surrogate KL에 **기여한다** — "logging 전용"이 아니다.
`_sigma_param_offset` 인덱스는 logging을 위해 flat step에서 sigma 성분을 slice할 뿐이다.

### 5.1 주요 하이퍼파라미터

| 그룹 | 값 | cfg 라인 |
|---|---|---|
| Trust region / KL | `max_kl=0.005`, `cg_iters=10`, `cg_damping=0.1`, line-search backtracks=10, shrink=0.5, kl_margin=1.5 | `:180-184` |
| IPO barrier | `barrier_t=100.0`, `barrier_alpha=0.05` (둘 다 고정 — scheduling 없음) | `:206` / `:207` |
| Critic (Adam) | `num_learning_epochs=5`, `num_mini_batches=4`, `value_lr=1e-3`, `value_loss_coef=1.0`, `cost_value_loss_coef=1.0`, `max_grad_norm=1.0` | — |
| GAE | `gamma=0.99`, `lam=0.95`, `cost_gamma=0.99`, `cost_lam=0.95` | — |

---

## 6. Cost critic과 constraints (K)

별도의 cost critic 네트워크가 **존재**하며, **single multi-head MLP**다(constraint당
별도 네트워크가 아님):

- **구조**: reward critic과 동일한 105D 비대칭 입력(`cat[o_t, z, p_t]`), hidden
  `[512, 256, 128]`, activation `elu` — reward critic과 같은 shape이되 K개의 scalar
  출력을 갖는다. `num_constraints > 0`일 때만 빌드되고 아니면 `None`
  (`_policy_base.py`). cfg `cost_critic_hidden_dims`(`:160`).
- **Heads**: K개의 scalar 출력, constraint당 head 1개(`evaluate_costs()`가 동일
  critic_obs로 K개 값 반환). cost returns/advantages는 `(T,N,K)` shape.
- **Naming 규약**: `cost_critic.*` prefix가 이것을 TRPO natural-gradient 그룹이 아니라
  Adam value optimizer로 라우팅하는 키다.

**`num_constraints`(K)는 런타임에 resolve된다.** 정적 cfg default는 `0`
placeholder(`:159`)이며, `constraint_encoder_runner.py`가 `super().__init__()` 전에
`len(cfg.constraints.terms)`로 덮어쓴다. 따라서 `cost_critic`은 빌드 시점에 올바른
크기로 만들어진다.

### 6.1 이 브랜치에서의 K

`main`에서, 그리고 `joint1_constraint_arm="none"`(default)일 때 **K = 10**
(probabilistic 5 + average 5)이며 `envs/main/config.py`의 constraint terms로 정의된다.

`exp/joint1-constraint-redesign` 브랜치에서는 `config.py`가 **기본 비활성(off-by-default)**
joint1 anti-drift constraint를 추가한다:

- `joint1_constraint_arm: str = "none"`(`"none"`, `"A"`, `"B"` 중 하나),
  `joint1_constraint_budget: float = 0.05`(per-step average budget `d_k`).
- `"A"` 또는 `"B"`로 설정하면 `apply_joint1_constraint_arm()`(cfg `__post_init__`가
  아니라 `ALBCEnv.__init__`에서 호출)이 constraint term 하나를 추가한다
  → **K = 11**, 즉 cost critic head가 **1개 늘어난다**.
- `"B"`는 `joint1_cumulative_cost`(commanded integrator의 평균)를, `"A"`는
  measured-angle 변형을 선택한다.

constraint 선택은 MLP 레이어 수·차원·activation을 **바꾸지 않는다** — cost critic의
출력 폭(K)만 움직인다.

---

## 7. 어디를 고치나 (다음 실험 knob 맵)

별도 표기 없으면 모두 `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py`.

| 아키텍처 knob | 값 | 위치 (file:line) |
|---|---|---|
| actor hidden | [256, 128, 64] | `:126` |
| critic hidden | [512, 256, 128] | `:127` |
| cost_critic hidden | [512, 256, 128] | `:160` |
| actor/critic activation | elu | `:128` |
| encoder hidden | [256, 128, 64] | `:130` |
| encoder activation | elu | `:135` |
| encoder_latent_dim (z) | 9 | `:134` |
| encoder_output_norm (pre-softsign LayerNorm) | True | `:155` |
| encoder static min-max bounds | `_PRIV_OBS_LOWER/UPPER` | 동일 파일에 정의 |
| encoder_obs_normalization | False | `:136` |
| critic_uses_z (105D vs 96D) | True | `:154` |
| init_noise_std | 0.7 | `:123` |
| min_std / max_std (algo clamp) | 0.05 / 2.0 | `:221` / `:222` |
| min_std_per_dim | (0.10, 0.10, 0.05 x6) | `:225` |
| entropy_coef / per_dim | 0.003 / (0.01 x2, 0.001 x6) | `:212` / `:218` |
| max_kl / cg_iters / cg_damping | 0.005 / 10 / 0.1 | `:180-182` |
| barrier_t / barrier_alpha (IPO) | 100.0 / 0.05 | `:206` / `:207` |
| num_constraints (auto-sync K) | 0 -> 런타임 10 (joint1 constraint 켜면 11) | `:159` (실제 K = `config.py` constraint terms) |
| policy_obs_dim / privileged_dim | 69 / 27 | `:138` / `:139` |
| joint1 constraint arm / budget (해당 브랜치) | "none" / 0.05 | `envs/main/config.py` |

---

## 8. 주의사항·한계

- **`envs/main`에는 `state_dependent_std`가 없다.** `std`는 batch 전체에 broadcast되는
  단일 global `log_std` 파라미터다. per-state std head는 별도의 미병합 실험 브랜치
  (`exp/attitude-only-state-std`)에 있다.
- **encoder auxiliary loss 없음.** encoder에 reconstruction/KL/contrastive head가
  없다; 유일한 추론 훅은 기본 비활성 z-ablation(`mode=None`)이다. 이는 프로젝트
  규칙과 일치한다(reconstruction loss 실패: decoder가 `z`를 무시하고 `z`가 collapse).
- 런타임 `K`와 각 `_PRIV_OBS_LOWER/UPPER` 엔트리의 물리적 의미는 env config / `mdp/`에
  정의돼 있다; 여기서는 길이(priv 27, constraints 10/11)만 교차검증했다.
- 본 문서는 정적 코드 구조 레퍼런스다. 런타임 학습 dynamics(예: `z` collapse 여부)는
  별개 진단 대상이며 `analysis/encoder_tools.py sweep`을 사용한다.

---

## 9. 설계 근거와 문헌상 위치

2026-06-30 policy head(std 파라미터화, action output, entropy)의 코드 + 문헌 검토
결론. 각 선택이 분야 표준인지 프로젝트 고유 확장인지 기록해, 후속 작업이 무엇이
합의에 기대고 무엇이 우리 실측에 기대는지 구분할 수 있게 한다.

| 선택 | 위치 | 근거 |
|---|---|---|
| Global state-independent `log_std` | **표준** (on-policy PPO/TRPO) | "37 Implementation Details of PPO"(state-independent, init 0); HORA `self.sigma = nn.Parameter`; rsl_rl `state_dependent_std=False` 기본값. state-dependent std는 SAC 관행. |
| Linear action output (tanh/clamp 없음) | **표준** (PPO/TRPO) | raw Gaussian mean + 환경단 `[-1,1]` 해석; tanh-squashing은 SAC 특성(Jacobian 보정 필요). `MLP` 마지막 레이어 linear(`last_activation=None`), `act()`에 clamp 없음. |
| `min_std` floor / `max_std` cap | **프로젝트 커스텀** (rsl_rl 상류에 없음) | floor=premature std collapse 방지/exploration 보존, cap=발산 방지. 일부 robot-RL repo(MoE-Loco "clip min std 0.05")에 유사 사례 있으나 표준 레시피 아님. TRPO step 후 `constraint_trpo.py`에서 적용. |
| TRPO에 entropy bonus 추가 | **비표준** (PPO엔 표준, 순수 TRPO엔 아님) | EnTRPO(arXiv:2110.13373)가 "TRPO + entropy regularization"을 *novelty*로 발표 — 표준이면 논문이 안 됨. PPO는 양수 `entropy_coef`가 일상(rsl_rl 0.01, IsaacLab AnymalB 0.005). |
| Per-dim entropy / min_std (arm vs thruster) | **프로젝트 커스텀** | task 특수: arm dim이 더 빨리 붕괴(iter ~1404)해 entropy push(0.01 vs 0.001)와 floor(0.10 vs 0.05)를 더 세게. |

### 9.1 TRPO인데도 entropy가 붕괴하는 이유

"TRPO의 KL trust region이 entropy collapse를 *막아준다*"는 흔한 오해다. 막지
못한다 — trust region은 각 스텝의 **크기**만 제한하지 **방향**은 제한하지
않는다. 목적함수의 gradient가 매 스텝 std 감소 방향을 가리키면 각 스텝은 작아도
정책은 꾸준히 entropy 0으로 걸어가고, trust region은 그 하강을 늦출 뿐이다.
std를 누르는 두 압력:

1. **Surrogate(advantage).** policy gradient는 high-advantage action의 확률을
   높이는데, Gaussian에서 특정 action에 확률을 몰아주는 것 = std 축소다. 이는
   PPO/TRPO 공통의 구조적 압력으로 trust region이 못 막는다.
2. **IPO log-barrier (프로젝트 특이 증폭).** std가 크면 가끔 constraint 위반
   action을 샘플해 margin `d_k - hat{J}_{C_k}`이 줄고 barrier term `log(...)`이
   작아진다. 그래서 barrier가 "위험 샘플을 안 내도록 std를 줄여라"는 압력을 더한다
   — constraint가 정책을 "조심스럽게"(낮은 노이즈) 만든다.

순수 TRPO는 압력 1만, 우리는 1 + 2라서 entropy가 vanilla TRPO보다 *빨리* 붕괴하고,
그래서 (프로젝트 커스텀) entropy bonus가 필요하다. 실측: `entropy_coef=0` -> 노이즈
0.12 붕괴; `entropy_coef=0.003` -> 0.55 회복. 압력 2는 메커니즘 추론 + 일반
constrained-RL 문헌 지지(constraint가 exploration 억제: ESB-CPO arXiv:2302.14339,
safe-RL 리뷰 arXiv:2508.09128)까지이며, **통제 실험으로 분리 입증된 것은 아니다** —
보류된 검증 실험은 `docs/plans/2026-06-30-entropy-collapse-ipo-barrier-experiment.md` 참조.

---

## 소스 파일

- `constrained_albc/envs/main/encoder/_policy_base.py` — `PolicyBase`, global `log_std`, Gaussian, critic/cost_critic 구성
- `constrained_albc/envs/main/encoder/actor_critic_encoder.py` — encoder, actor, asymmetric critic wiring
- `constrained_albc/envs/main/encoder/actor_critic_asym_constrained.py` — NoEncoder ablation 정책
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — ConstraintTRPO + IPO
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — runner, `num_constraints` auto-sync
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `_ALBCPolicyCfg`, 모든 차원·하이퍼파라미터
- `constrained_albc/envs/main/config.py` — `ALBCEnvCfg`, 관측/액션 space, joint1 constraint arm(해당 브랜치)
- `constrained_albc/envs/main/albc_env.py` — obs 조립, action 적용
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` / `compute_privileged_obs`
- `constrained_albc/envs/main/mdp/constraints.py` — constraint terms (K), `apply_joint1_constraint_arm`(해당 브랜치)
