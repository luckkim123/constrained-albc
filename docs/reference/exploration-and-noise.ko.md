# Exploration과 Action Noise (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 exploration 메커니즘 — 정책의 action-noise
> 파라미터화(`log_std`), 그것이 어떻게 샘플링 분포가 되는지, 업데이트 후 std
> clamp, entropy bonus, 그리고 KL trust region이 있는데도 ConstraintTRPO에서 *왜*
> entropy가 collapse하는지.
>
> 디스크에 대해 검증된 code-level 레퍼런스다. `main-network-architecture.ko.md`
> (§4, §9)와 `action-pipeline.ko.md`(§3.1)가 참조하거나 링크로 넘겼던
> exploration/entropy 내용을 여기로 모은다; 그 문서들은 noise/std/entropy 세부에
> 대해 이제 **여기**를 가리킨다. 이 문서가 exploration 이야기를 end-to-end로
> 소유한다.
>
> **다루지 않음:** 네트워크 층 shape(→ `main-network-architecture.ko.md`)와
> action→물리 경로(→ `action-pipeline.ko.md`). 이 문서는 `log_std` 파라미터에서
> 시작해 로깅되는 noise 메트릭에서 끝난다.

---

## 1. 개요

Exploration은 8D action 위의 **단일 global Gaussian noise**다. 정책은 학습 가능한
log-std 벡터 하나 `log_std`(dim 8)를 갖는다; 샘플링 std는 `exp(log_std)`로,
state-independent이고 배치 전체에 broadcast된다. state-dependent std head도,
tanh-squashing도 없다. 매 업데이트마다 세 힘이 `log_std`에 작용한다:

```
init:  log_std = log(0.7)      # init_noise_std = 0.7, all 8 dims

sample: a ~ Normal(action_mean, exp(log_std))          # act() -- exploration noise

update (ConstraintTRPO.update):
  surrogate = reward_surr + IPO_barrier + entropy_bonus     # 3 terms
     |            |            |             |
     |            |            |             +-- pushes std UP  (per-dim coef)
     |            |            +-- pushes std DOWN (avoid risky samples)
     |            +-- pushes std DOWN (concentrate on high-adv actions)
     +-- natural-gradient TRPO step under KL trust region (bounds STEP SIZE)
  clamp: log_std <- [log(min_std_per_dim), log(max_std)]    # hard floor/ceiling
  log:   Policy/entropy, Noise/std_mean, Noise/std_min
```

**두 개의 독립적인 "noise" 개념 — 혼동 금지.** 이 문서는 **action noise**(정책의
exploration std, `log_std`, 학습 시 학습됨)에 관한 것이다. **observation noise
model**(`config.py`의 `_OBS_NOISE_STD`, `o_t`에 적용되는 고정 센서-시뮬레이션
상수)이 *아니다*. 같은 단어, 다른 대상: action noise는 정책이 *내보내는* 것,
observation noise는 센서가 *오염시키는* 것. §7에서 경계를 명시적으로 긋는다.

---

## 2. `log_std` 파라미터

shape `(num_actions,) = (8,)`의 단일 `nn.Parameter`로, `PolicyBase._init_base`에서
초기화된다(`_policy_base.py:96`):

```python
self.log_std = nn.Parameter(torch.log(init_noise_std * torch.ones(num_actions)))
```

`init_noise_std = 0.7`(`rsl_rl_ppo_cfg.py:132`)이므로 모든 dim이
`log(0.7) ≈ -0.357`, 즉 std 0.7에서 시작한다. **global / state-independent** —
배치의 모든 observation에 대해 동일한 8-vector다. 샘플링 분포는
`_update_distribution`에서 만들어진다(`_policy_base.py:128-130`):

```python
def _update_distribution(self, mean: torch.Tensor) -> None:
    std = torch.exp(self.log_std).expand_as(mean)
    self.distribution = Normal(mean, std)
```

`act()`는 `distribution.sample()`(노이즈 있는 학습 action)을, `act_inference()`는
mean(결정적 eval)을 반환한다. 샘플의 action 쪽 처리 — clamp, split, 물리 — 는
`action-pipeline.ko.md`에 있고, *선택*(global vs state-dependent)의 표준성은
`main-network-architecture.ko.md` §9에 있다(on-policy PPO/TRPO에서 **표준**).

`log_std`는 *live wire*다: 학습되는 파라미터이며, optimizer split(§5)에서 어디에
사는지가 KL trust region이 collapse를 damp하게 하는 열쇠다.

---

## 3. Std clamp — 비대칭, log 공간, step 후

TRPO step 후, `ConstraintTRPO.update`가 `log_std`를 in-place clamp한다
(`constraint_trpo.py:484-491`):

```python
with torch.no_grad():
    log_max = math.log(self.max_std)
    if self._log_min_std is not None:               # per-dim floor path
        self.policy.log_std.data.clamp_(max=log_max)
        self.policy.log_std.data = torch.max(self.policy.log_std.data, self._log_min_std)
    else:                                            # scalar fallback
        self.policy.log_std.data.clamp_(min=math.log(self.min_std), max=log_max)
```

주목할 세 가지, 각각 흔한 오독:

1. **`std`가 아니라 `log_std`를 clamp한다.** 경계는 `log(min_std)`와
   `log(max_std)`; 선형 std는 clamp된 값의 `exp`다.
2. **상한과 하한은 다른 연산이다.** 상한은 `clamp_(max=…)`; per-dim 하한은 별도의
   `torch.max(log_std, _log_min_std)`. scalar-fallback 분기만 둘을 한 `clamp_`으로
   처리한다.
3. **gradient step 후의 hard projection**이지 loss의 항이 아니다. TRPO step은
   `log_std`를 어디로든 몰 수 있고, clamp가 이후 `[floor, ceiling]`로 되돌린다.
   optimizer가 낮추려는 std를 스스로 *올릴* 수는 없다 — floor를 넘는 undershoot만
   막는다(§6: std를 실제로 유지하는 건 entropy bonus).

### 3.1 경계 (per-dim floor)

`RslRlConstraintTRPOAlgorithmCfg`에서(`rsl_rl_ppo_cfg.py:232-236`):

| 경계 | 값 | 비고 |
|---|---|---|
| `max_std` | 2.0 | scalar 상한, 모든 dim |
| `min_std` | 0.05 | scalar 하한 (per-dim 비었을 때만 fallback) |
| `min_std_per_dim` | (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05) | **arm dim = 0.10, thruster dim = 0.05** |

per-dim floor가 live다(비어있지 않아 scalar `min_std`를 override). arm dim이 더
빨리 collapse하므로 **더 높은 floor(0.10 vs 0.05)**를 받는다 — cfg 주석은 arm dim이
**iter 1404**에 scalar floor에 닿는 반면 thruster dim은 0.14 위에 머문다고
기록한다. `min_std_per_dim`은 **project-custom**(rsl_rl upstream에 없음); std floor
자체의 표준성은 `main-network-architecture.ko.md` §9에서 논한다.

---

## 4. Entropy bonus — per-dim, IPO barrier와 나란히

entropy는 surrogate에 세 번째 가법 항으로 들어간다(`constraint_trpo.py:466-480`):

```python
mean_entropy = self.policy.entropy.mean()
self._last_mean_entropy = mean_entropy.item()
if self._entropy_coef_per_dim is not None:
    per_dim_ent = self.policy.distribution.entropy()             # [batch, action_dim]
    entropy_bonus = -(self._entropy_coef_per_dim * per_dim_ent).sum(dim=-1).mean()
else:
    entropy_bonus = -self._entropy_coef * mean_entropy
return reward_surr + barrier + entropy_bonus
```

TRPO가 미분하는 surrogate는 `reward_surr + barrier + entropy_bonus`다. *최소화*되므로
`-coef·H`는 entropy `H`를 최대화한다 — `log_std_i`에 대한 gradient는
`+entropy_coef_i`, noise를 올리는 상수 push다(코드 주석). per-dim이 live
경로(`entropy_coef_per_dim`이 비어있지 않음)라, 각 action dim이 자기 계수를 갖는다.

### 4.1 계수

| cfg | 값 | 위치 |
|---|---|---|
| `entropy_coef` (scalar) | 0.003 | `rsl_rl_ppo_cfg.py:223` (per-dim 비었을 때 fallback) |
| `entropy_coef_per_dim` | (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001) | `rsl_rl_ppo_cfg.py:229` — **arm = 0.01, thruster = 0.001** |

arm dim이 thruster dim보다 **10배 강한 entropy push**를 받아, 더 높은 arm std
floor(§3.1)와 대응된다 — 둘 다 같은 실측 문제(arm noise가 먼저 collapse)를 겨냥한다.
**Adaptive entropy는 비활성**: `target_entropy`/entropy scheduler가 없고 계수는
고정이다. (이전 adaptive-entropy 시도는 실패 — `adaptive-entropy-failed` project
memory / network 문서 참조.)

실측 효과, cfg 주석 기준: `entropy_coef=0.003`은 noise를 0.36→0.55로 회복(04-09
run); `entropy_coef=0`은 noise를 0.12로 collapse시켰다(04-10 run).

---

## 5. 왜 `log_std`가 TRPO 그룹에 있나 (Adam이 아니라)

ConstraintTRPO는 파라미터를 name prefix로 두 optimizer 그룹으로 나눈다
(`constraint_trpo.py:153-174`):

```python
# 1. Policy (actor + encoder + log_std): TRPO natural gradient (no optimizer)
#    log_std included in TRPO so KL trust region protects against entropy collapse.
# 2. Value (critic + cost_critic): Adam
value_prefixes = ("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")
for name, param in self.policy.named_parameters():
    if any(name.startswith(p) for p in value_prefixes):
        value_params.append(param)          # -> Adam (value_lr)
    else:
        self._policy_params.append(param)   # -> TRPO natural gradient (actor, encoder, log_std)
```

`log_std`는 의도적으로 **TRPO natural-gradient 그룹**에 있지 Adam value 그룹이
아니다. 이유(cfg 주석): KL trust region 아래 두면 Fisher curvature가 std를 *보게* 돼,
entropy를 급락시킬 step이 KL로 bound된다. sigma slice의 offset은
로깅용으로 추적된다(`_sigma_param_offset`, `:175-177`).

**FVP는 `log_std`를 포함한다.** Fisher-vector product
(`_fisher_vector_product`, `constraint_trpo.py:354-365`)는
`Normal(action_mean, action_std)` 위의 순수 KL Hessian으로, `self._policy_params`에
대해 미분된다 — 여기에 `log_std`가 들어있다. `action_std = exp(log_std)`이므로
`log_std`는 진짜로 Fisher curvature와 surrogate KL에 기여한다; **로깅 전용이
아니다**. (`main-network-architecture.ko.md` §4와 동일 결론.)

같은 split 주석은 **encoder**를 policy 그룹에 두는 것도 기록한다: 분리하면(run
2026-03-30) actor→z 경로만으로는 너무 약해 encoder gradient가 ~85% 떨어졌다(`:157`).
그건 encoder 사실로 network 문서 §4에서 교차 참조되고; 여기서는 `log_std`가 그
그룹을 공유한다는 점만이 요점이다.

---

## 6. KL trust region이 있는데도 왜 entropy가 collapse하나

흔한 오해는 TRPO의 KL trust region이 entropy collapse를 *막는다*는 것이다. 아니다 —
trust region은 각 step의 **크기**를 bound하지 **방향**을 bound하지 않는다. 목적함수
gradient가 매 step 더 작은 std를 가리키면, 각 step은 작아도 정책은 꾸준히 zero
entropy로 걸어간다; trust region은 하강을 늦출 뿐이다. 두 힘이 std를 내리고, 하나가
올린다:

1. **Surrogate / advantage (하강).** Policy gradient가 high-advantage action의 확률을
   올린다; Gaussian에서 선택한 action에 확률을 집중시키는 것 *자체가* std를 줄이는
   것이다. trust region이 막을 수 없는 PPO/TRPO 공통의 구조적 압력이다.
2. **IPO log-barrier (하강, project-specific).** 큰 std는 가끔 constraint 위반
   action을 샘플해 constraint margin `d_k - hat{J}_{C_k}`를 줄이고 `log(margin)`을
   낮춘다. 그래서 barrier는 정책이 위험한 action 샘플링을 멈추도록 std를 줄이는 압력을
   더한다 — constraint가 정책을 "조심스럽게" 만든다.
3. **Entropy bonus (상승).** `-coef·H` 항이 `log_std`를 dim별 상수 gradient로
   올린다(§4), 유일한 반대 압력.

순수 TRPO는 압력 1만 갖는 반면 이 알고리즘은 1 + 2를 가지므로, entropy가 vanilla
TRPO보다 *더 빨리* collapse한다 — 정확히 그래서 (project-custom) entropy bonus와
per-dim floor가 존재한다. collapse-and-recovery는 실측된다(§4.1). 압력 2(IPO
barrier)는 메커니즘 추론 + 일반 constrained-RL 문헌 지지이며, 통제 실험으로 **분리되지
않았다** — 보류된 테스트는
`docs/plans/2026-06-30-entropy-collapse-ipo-barrier-experiment.md`에 있다. "TRPO +
entropy bonus"의 문헌 표준성(**비표준**, EnTRPO novelty)은
`main-network-architecture.ko.md` §9에 있다.

---

## 7. Action noise vs. observation noise (혼동 금지)

둘 다 "noise"라 불리고 둘 다 Gaussian이지만, 역할이 다른 다른 대상이다:

| | Action noise | Observation noise |
|---|---|---|
| 무엇 | 정책 exploration std | 센서-시뮬레이션 오염 |
| 대상 | `log_std` (`_policy_base.py:96`) | `_OBS_NOISE_STD` (`config.py:206`) |
| 학습됨? | **예** — 학습 파라미터, 매 업데이트 clamp됨 | **아니오** — 고정 cfg 상수 |
| 적용 대상 | env *전*의 action | 정책 *전*의 observation `o_t` |
| 목적 | exploration 구동 | sim-to-real robustness |
| 이 문서 | **다룸** | 범위 밖 (obs/DR 문서 참조) |

`_OBS_NOISE_STD`는 69D `o_t`에 더해지는 dim별 Gaussian(+ 균등 가법 bias)이며, 특히
첫 3 dim(command `ang_cmd`)과 모든 action-history dim은 0.0이다 — 그것들은 센서가
아니라 우리 자신의 양이다. 그 obs-noise 모델은 observation 파이프라인에 속하지 여기가
아니다. 이 문서의 주제 전체는 `log_std`다.

---

## 8. 무엇을 볼 것인가 (로깅 메트릭)

`ConstraintEncoderRunner._log_constraint_metrics`가 매 iteration noise/entropy 상태를
로깅한다(`runners/constraint_encoder_runner.py:324, 337-338`):

| 메트릭 | 의미 | 이걸로 읽는 것 |
|---|---|---|
| `Policy/entropy` | `_last_mean_entropy` (배치 평균) | 전체 exploration 수준; 0으로 단조 하강 = collapse |
| `Noise/std_mean` | 8 dim 위 `log_std.exp().mean()` | entropy 튜닝이 겨냥하는 0.36↔0.55 대역 |
| `Noise/std_min` | `log_std.exp().min()` | 어느 dim이 floor에 고정됐나 (arm dim이 먼저) |
| `Grad/sigma_step` / `Grad/sigma_dir` | natural-gradient step의 sigma 성분 (norm / signed mean) | 이번 iteration에 noise를 올리는지 내리는지 |

`Noise/std_min`이 정확히 0.05(또는 arm dim은 0.10)에 앉으면 floor가 binding —
entropy bonus가 압력 1+2에 졌고 clamp가 선을 지키고 있다는 뜻이다. per-dim 튜닝을
촉발한 신호가 이것이다.

---

## 9. Knob map

특별한 언급이 없으면 모두 `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py`.

| Knob | 값 | 위치 |
|---|---|---|
| `init_noise_std` | 0.7 | `:132` |
| `entropy_coef` (scalar fallback) | 0.003 | `:223` |
| `entropy_coef_per_dim` | (0.01, 0.01, 0.001×6) | `:229` |
| `min_std` / `max_std` (scalar) | 0.05 / 2.0 | `:232` / `:233` |
| `min_std_per_dim` | (0.10, 0.10, 0.05×6) | `:236` |
| std clamp 적용 (log 공간) | — | `constraint_trpo.py:484-491` |
| surrogate의 entropy bonus | — | `constraint_trpo.py:466-480` |
| param-group split (log_std → TRPO) | — | `constraint_trpo.py:153-174` |
| FVP가 log_std 포함 | — | `constraint_trpo.py:354-365` |
| log_std 파라미터 | — | `_policy_base.py:96` |
| `_update_distribution` (std = exp) | — | `_policy_base.py:128-130` |
| entropy/noise 로그 키 | Policy/entropy, Noise/std_mean, Noise/std_min | `constraint_encoder_runner.py:324, 337-338` |

---

## 10. 참고와 한계

- **clamp는 optimizer가 낮추려는 std를 올릴 수 없다.** floor/ceiling projection이지
  spring이 아니다. noise를 유지하는 건 entropy bonus의 일이고; clamp는 floor 아래
  undershoot와 ceiling 위 blow-up만 막는다.
- **`min_std_per_dim`과 `entropy_coef_per_dim`은 같은 문제의 두 knob**이다(arm dim이
  먼저 collapse). 함께 튜닝되며; 하나만 바꾸면 per-dim split이 닫으려던 confound가
  다시 열린다.
- **IPO-barrier → entropy 압력(압력 2)은 추론이지 분리된 게 아니다.** barrier
  메커니즘 + constrained-RL 문헌에 기댄다; 압력 1과 분리할 통제 실험은 보류다(§6).
- 정적 코드 구조 레퍼런스다. 특정 run에서 entropy가 *실제로* collapse하는지는 런타임
  진단 질문이다 — §8 메트릭을 읽고 config에서 넘겨짚지 말 것.

---

## 11. Action bounding: clamp는 정당한가 + 미검증 실험 여지

> **결론 (2026-07-02 검토, 문헌 + 코드 대조).** 현재 raw Gaussian + `[-1,1]` hard
> clamp 구성은 **정당하고 표준**이다. tanh-squashing으로 바꾸는 것은 개선이 아니라
> 문제를 옮기는 것이다. 아래는 근거와, clamp를 건드리지 *않는* 미검증 실험 여지다.

### 11.1 clamp가 정당한 이유

action 샘플은 clamp 없는 raw Gaussian이다 (`actor_critic_encoder.py:277`
`distribution.sample()`, "no action clamping"). clamp는 env buffer에서만 일어난다
(`albc_env.py:452` `self._actions = actions.clone().clamp(-1.0, 1.0)`). vecenv
`clip_actions`(Clamp#0)는 미설정 → isaaclab default `None` → **no-op**; 실제 작동하는
clamp는 이 env buffer 하나뿐이다.

log-prob은 **clamp 전 raw 샘플**에 대해 계산되고(`constraint_trpo.py:459`), clamp는
env dynamics에만 적용된다. 따라서 "policy 밀도"와 "실행 액션"이 각자 일관된다 — clamp를
policy가 아니라 environment의 일부로 보는 **on-policy PPO/TRPO 표준 관행**이다
(SB3 PPO=`DiagGaussianDistribution`+clip, tanh 없음; PPO/TRPO 원논문도 plain Gaussian).

### 11.2 tanh로 바꾸면 안 되는 이유 (개선이 아니라 이전)

1. **이 태스크는 최적 액션이 액션 공간 *중앙*이다.** arm은 delta integrator
   (`albc_env.py:567-578` `q_des += 0.10·a`)라 idle(a≈0)이 최적이고 경계 attractor가
   없다; thruster는 hover라 소량 command 평형(0 근처)이 최적이다. 따라서 tanh saturation
   ($1-\tanh^2(u)\to0$ at boundary)이 gradient를 죽이는 문제는 이 태스크에 **거의 해당
   안 된다**. (과거 EE-position absolute mode는 최적점이 workspace *경계*라 tanh/clamp가
   gradient-freeze를 냈다 — `project_delta_ee_decision.md`. 그 실패 메커니즘은 현재
   joint-space에는 없으므로 "tanh=arm freeze" 논리를 현재에 그대로 적용하면 틀린다.)
2. **on-policy TRPO + tanh는 검증된 조합이 아니다.** tanh-squashing은 SAC 계열
   (off-policy, reparameterization, entropy-in-objective)의 정의적 요소이고 Jacobian
   보정 $-\sum_i\log(1-\tanh^2(u_i))$가 그 objective상 자연스럽다 (Haarnoja 2018,
   arXiv:1801.01290 App.C). TRPO의 KL trust region은 정책 분포 위에서 계산되는데 tanh를
   넣으면 "policy"·"KL"의 기하가 바뀐다 — squashed-Gaussian TRPO를 검증한 문헌은 **없다**
   (출처 없음). 즉 ConstraintTRPO+IPO+FVP 전체(§5) 재설계 부담인데 §11.2-1 때문에 upside가
   없다.
3. **보정 누락 시 entropy 계산이 틀어진다.** tanh만 넣고 Jacobian 보정을 빠뜨리면 log-prob이
   잘못된 밀도로 계산돼 entropy bonus가 경계 근처에서 체계적으로 틀린다 → §4·§6의 collapse
   방어 수학이 깨진다.

### 11.3 clamp의 유일한 미측정 값 + 실험 여지 (코드 변경 없이 문서만; 착수 전 이 절 확인)

clamp가 정당해도 "완벽 무해"는 아니다. clip의 알려진 결함은 gradient 소실이 아니라
**경계 밖 샘플의 log-prob bias**다 (Fujita & Maeda 2018, arXiv:1802.07564, CAPG). 이
bias는 액션이 경계에 자주 saturate될수록 커진다. §11.2-1처럼 최적점이 중앙 + std가 작으면
(floor 0.05~0.10) saturate가 드물어 bias가 실전에서 작을 것으로 *추정*되나 — **실측 안
됨**. 이것이 남은 실험들의 근거다:

| # | 실험 | 근거 | 성격 |
|---|---|---|---|
| 1 | **`clip_fraction` 로깅 추가** (`|a|≥1` 비율) | 현재 미로깅(코드 확인). saturate 빈도를 재야 §11.3 bias가 실전 문제인지 판단 가능. 문헌도 "파이프라인 바꾸기 전 이것부터 재라" 권고 | **코드 변경**(로깅 몇 줄, 알고리즘 불변, 훈련 게이트 무관). 최우선 |
| 2 | `max_std=2.0` / `init_noise_std=0.7` 재검토 | 다른 knob(entropy_coef 0.003, per-dim coef, arm floor)은 실측 근거 있으나 이 둘만 근거 코멘트 0건 = 관성 | 비교 학습런(훈련 게이트). 실험 1 결과에 종속 |
| 3 | IPO barrier→entropy 인과 분리 (`entropy_coef_per_dim=0` vs 현행) | 문서 §6이 "inferred, not isolated"로 자인, 참조 계획서도 부재 | 비교 학습런(훈련 게이트). tanh와 무관, 독립 |

**폐기**: tanh vs raw+clamp 비교런 — §11.2에서 부적절 확정.

> **문헌 출처.** Haarnoja et al. 2018 (SAC, arXiv:1801.01290) — tanh Jacobian 보정.
> Fujita & Maeda 2018 (Clipped Action Policy Gradient, ICML, arXiv:1802.07564) — clip
> bias 이론. Schulman 2015 (TRPO, arXiv:1502.05477) / 2017 (PPO, arXiv:1707.06347) —
> plain Gaussian 관행. Chou et al. 2017 (ICML, Beta policy) — clip·squash 둘 다 경계
> artifact 지적. "squashed TRPO 검증 문헌 없음"·"경계 최적점 tanh-vs-clip 직접 비교 논문
> 없음"은 조사상 출처 없음(날조 아님, 공백 명시).

---

## 소스 파일

- `constrained_albc/envs/main/encoder/_policy_base.py` — `log_std` 파라미터(`:96`), `_update_distribution`(`:128`)
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — std clamp(`:484`), entropy bonus(`:466`), param-group split(`:153`), FVP(`:354`)
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `init_noise_std`, `entropy_coef(_per_dim)`, `min/max_std`, `min_std_per_dim`
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — `Policy/entropy`, `Noise/std_*` 로깅
- `constrained_albc/envs/main/config.py` — `_OBS_NOISE_STD` (§7에서 대비되는 *observation* noise)
