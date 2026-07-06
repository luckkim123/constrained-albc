# 도메인 랜덤화 & DORAEMON (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 도메인 랜덤화(DR) 시스템 —
> `marinelab/marinelab/algorithms/doraemon.py`의 16-파라미터 DORAEMON 엔트로피
> 최대화 커리큘럼, `DomainRandomizationCfg` / `HardDomainRandomizationCfg`의 두
> 분리된 DR 표면, 샘플링된 값이 reset 시점에 어떻게 물리에 도달하는지, 스케줄러가
> 훈련 루프 안에서 어떻게 step 되는지, 그리고 eval 측에서 쓰는 고정
> uniform-보간 DR.
>
> 본 문서는 디스크 코드에 대해 검증한(적대적 교차검증) 코드 레벨 레퍼런스다.
> shipped 기본값(`HardDomainRandomizationCfg`, `doraemon.enable = True`)을
> 반영한다. 레거시 full-DOF 변형(`envs/full_dof/`)은 동일한 16-파라미터
> DORAEMON 표면을 공유하지만 여기서 다루지 않는다.
>
> **English version**: [`domain-randomization-and-doraemon.md`](domain-randomization-and-doraemon.md) (SSOT).
> 두 파일 중 하나를 고치면 다른 하나도 동기화할 것.

---

## 1. 여기서의 도메인 랜덤화란

이 프로젝트의 DR은 **하나의 config 객체(`DomainRandomizationCfg`)를 공유하지만
서로 분리된 두 표면** + off-by-default인 세 번째 표면으로 구성된다. 이 셋을
구분하는 것이 가장 중요하다:

| 표면 | 정체 | 관리 주체 | 기본 상태 |
|:---|:---|:---|:---|
| **DORAEMON 물리 DR** | 16개 물리 파라미터(질량·감쇠·부력 형상·해류) | 학습되는 Beta 커리큘럼(DORAEMON) | **on** (`enable=True`) |
| **Uniform-only DR** | joint gain/friction/effort, thruster scale, payload 디스크 반경 | reset마다 고정 uniform 샘플 | on (`randomization` 활성 시) |
| **Fault injection** | thruster/sensor/joint 컴포넌트 고장 | `FaultInjectionCfg`, uniform | **off** |

**DORAEMON은 물리 DR만 최적화한다.** command/task 난이도는 scale `1.0`으로 고정된
task knob이며 커리큘럼 관리 대상이 *아니다* (`albc_env.py:1368` — "DORAEMON
optimizes physics DR only; command difficulty is a fixed task knob"). shipped 기본
config은 `HardDomainRandomizationCfg`를 쓰므로(`config.py:460`) **"DR on" +
*hard* 범위가 shipped 상태**이고, 더 부드러운 `DomainRandomizationCfg`는 그
부모 baseline이다. Fault injection(`FaultInjectionCfg`, `config.py:295`)은 컴포넌트
*고장*을 모델링하는 것으로 파라미터 *분산*과는 다른 것이며, 기본 off다.

**DR은 명령형(imperative)으로 적용되며 Isaac Lab의 `EventManager`를 쓰지 않는다.**
`events.py:6` docstring이 "Isaac Lab EventTerm pattern"이라 명시하지만, 실제로
`randomize_*` 함수들은 `_reset_physics`에서 직접 호출되는 평범한 함수다 —
`EventTerm` 등록은 없다. docstring은 지향적 문구로 취급하라.

**파일 맵** (각 조각의 위치):

```
marinelab/marinelab/algorithms/doraemon.py     # 엔진 (robot-agnostic, 906줄)
constrained_albc/envs/main/doraemon.py         # ALBC 결합: _PARAM_DEFS(16개) + re-export shim
constrained_albc/envs/main/config.py           # DomainRandomizationCfg / HardDR / FaultInjectionCfg + live DoraemonCfg 오버라이드
constrained_albc/envs/main/mdp/events.py       # reset 시점 물리 적용
constrained_albc/envs/main/albc_env.py         # 와이어링: 샘플·스태시·episode 기록·_doraemon 소유
constrained_albc/envs/main/runners/            # iteration마다 _doraemon.step() 호출 지점
constrained_albc/analysis/{eval.py,dr_config.py,common.py}   # EVAL 측 고정 DR (커리큘럼 우회)
```

---

## 2. DR 파라미터 카탈로그

이 문서의 핵심 표다. **커리큘럼 관리 vs uniform-only** 경계가 명확하도록 3블록으로
분할했다. **활성 범위는 HARD 열**이다(shipped cfg가 `HardDomainRandomizationCfg`).
`_PARAM_DEFS` 리터럴 bound(`envs/main/doraemon.py:41`)는 **fallback 전용**이며,
build 시점에 `build_param_specs`가 `getattr(dr_cfg, field_name)`로 live bound를
읽으므로 **`config.py`가 범위의 SSOT**다.

### 블록 A — DORAEMON 커리큘럼 관리 (16개, Beta 차원 순서)

| # | name | `config.py` 필드 | SOFT 범위 | HARD 범위 | nominal |
|:--|:---|:---|:---|:---|:---|
| 0 | payload_mass | `payload_mass_range` | (0.0, 1.0) | (0.0, 3.0) | mid |
| 1 | added_mass_scale | `added_mass_scale` | (0.85, 1.15) | (0.5, 1.5) | mid |
| 2 | linear_damping_scale | `linear_damping_scale` | (0.5, 1.5) | (0.4, 1.7) | mid |
| 3 | quadratic_damping_scale | `quadratic_damping_scale` | (0.5, 1.5) | (0.4, 1.7) | mid |
| 4 | water_density | `water_density_range` | (995.0, 1025.0) | (995.0, 1025.0) \* | mid |
| 5 | cog_offset_z | `cog_offset_z` | (-0.02, 0.02) | (-0.04, 0.04) | mid |
| 6 | cob_offset_z | `cob_offset_z` | (-0.02, 0.02) | (-0.04, 0.04) | mid |
| 7 | volume_scale | `volume_scale` | (0.9, 1.1) | (0.75, 1.25) | mid |
| 8 | cob_offset_x | `cob_offset_x` | (-0.01, 0.01) | (-0.02, 0.02) | mid |
| 9 | cob_offset_y | `cob_offset_y` | (-0.01, 0.01) | (-0.02, 0.02) | mid |
| 10 | cog_offset_x | `cog_offset_x` | (-0.01, 0.01) | (-0.02, 0.02) | mid |
| 11 | cog_offset_y | `cog_offset_y` | (-0.01, 0.01) | (-0.02, 0.02) | mid |
| 12 | inertia_scale | `inertia_scale` | (0.75, 1.3) | (0.4, 2.0) | mid |
| 13 | body_mass_scale | `body_mass_scale` | (0.9, 1.1) | (0.75, 1.25) | mid |
| 14 | payload_cog_offset_z | `payload_cog_offset_z` | (-0.03, 0.0) | (-0.05, 0.0) | mid |
| 15 | ocean_current_strength | `ocean_current_strength_range` | (0.0, 1.0) | (0.0, 1.0) \* | **0.0 (override)** |

\* `HardDomainRandomizationCfg`는 `water_density`와 `ocean_current_strength`를
오버라이드하지 **않는다**. 이 둘은 hard == soft.

`NDIMS = 16` (`envs/main/doraemon.py`). `ocean_current_strength`는 r13에서
추가됐고, 그래서 `HardDR` docstring(`config.py:187`)의 낡은 주석이 아직도 "15
parameters"라고 한다 — 그 주석은 틀렸고 실제는 16개다.

### 블록 B — Uniform-only (`DomainRandomizationCfg`에 있으나 `_PARAM_DEFS`에 없음)

reset마다 uniform 샘플되며 커리큘럼이 **절대** 건드리지 않는다(Beta 없음, 확장
없음). nominal은 n/a.

| name | SOFT | HARD |
|:---|:---|:---|
| joint_damping_range (**arm 액추에이터**, PhysX) | (0.5, 5.0) | (0.3, 7.0) |
| yaw_damping_scale (**유체역학** quad-damping, DOF-5) | (0.5, 1.5) | hard 오버라이드 없음 |

> **"damping" 이름 충돌 2건.** `joint_damping_range`는 *arm 액추에이터*의 PhysX
> joint damping이고, `yaw_damping_scale`은 회전 DOF-5의 *유체역학* quadratic-damping
> scale이다. 둘 다 "damping"을 포함하지만 무관한 물리량이다. (joint
> stiffness/effort/friction, thruster scale 범위도 cfg 계열에 존재한다. 블록 A에
> 없는 것은 uniform-only로 취급하고, 정확한 범위는 소스 cfg를 근거로 삼을 것.)

### 블록 C — 스칼라 (`(lo, hi)` 튜플이 아님)

| name | SOFT | HARD | 의미 |
|:---|:---|:---|:---|
| payload_cog_offset_xy_radius | 0.10 | 0.08 | payload-CoG XY offset 샘플링 디스크 반경 |

### Fault injection (`FaultInjectionCfg`, 기본 off)

**별개 표면** — 파라미터 분산이 아니라 컴포넌트 고장 모델링이다. 명시적으로
켜지 않으면 off. 대표 필드: thruster-fail 확률, thruster/joint health 범위, sensor
noise scale. DR과 같은 reset에서 적용되지만 별도 메커니즘을 통한다(§5).

---

## 3. Beta 분포: 파라미터별 커리큘럼 상태

커리큘럼 상태는 **16개 독립 Beta 분포**이며, 파라미터마다 하나씩 그 물리적
`[lo, hi]` 구간 위에 정의된다(`BetaDistribution` 내부의 `_mins` / `_maxs` /
`_ranges`, `doraemon.py:115`). "더 어려운" 커리큘럼 = 더 넓은 Beta = 더 큰
엔트로피.

### `(nominal, concentration)` → `Beta(a, b)`

각 파라미터의 초기 Beta는 nominal(앵커)과 공유 concentration `c`에서 설정된다
(`doraemon.py:130`):

$$
\mu = \mathrm{clip}\!\left(\frac{\text{nominal}-\text{lo}}{\text{hi}-\text{lo}},\,0.01,\,0.99\right),
\qquad a = \mu\,c, \qquad b = (1-\mu)\,c
$$

`a` 또는 `b`가 `_MIN_BETA_PARAM = 1.0` 아래로 떨어지면, 평균을 보존하며 다른
파라미터를 유도한다(mean-preserving 분기, `doraemon.py:130`).

> **Concentration 함정(불일치하는 두 기본값).** `BetaDistribution.__init__`에는
> `concentration = 200.0`(`doraemon.py:118`)이 있으나 ALBC 경로에서는 **죽은
> 값**이다 — live 스케줄러는 `DoraemonCfg.init_concentration = 30.0`으로 분포를
> 생성한다(`doraemon.py:351`). 클래스 기본값이 아니라 스케줄러의 cfg를 읽어라.

`sample(n)`은 unit 공간에서 뽑아 물리 스케일로 rescale하고, `log_prob`은 역변환
후(`[1e-6, 1-1e-6]`로 clamp) 차원에 걸쳐 합산한다. `kl_divergence`는 **unit** Beta
위에서만 작동한다(`log(range)` 항이 상쇄).

### 커리큘럼이 최대화하는 엔트로피

`BetaDistribution.entropy()`는 변수변환 항을 더해 엔트로피를 *물리* 스케일에서
측정한다(`doraemon.py:173`):

$$
H(\phi) = \sum_{i=1}^{16}\Big(H_{\mathrm{Beta}}(a_i,b_i) + \log(\text{hi}_i-\text{lo}_i)\Big)
$$

이것이 DORAEMON이 최대화하는 목적함수다(§4).

### `build_param_specs`: 세 bound 소스의 융합

`build_param_specs`(`doraemon.py:65`)는 DR cfg 범위 + `_PARAM_DEFS` 순서 +
`_NOMINAL_OVERRIDES`를 융합해 분포를 만들 `ParamSpec` 리스트를 만든다. nominal =
midpoint, **단** `ocean_current_strength` → `0.0`(`envs/main/doraemon.py:66`)이므로
커리큘럼은 **해류 없이 시작**해 정책이 더 단순한 변형을 학습하면서 전체 범위로
확장한다(`mu = 0`이 `0.01`로 clamp → `c = 30`에서 `a = 1.0, b = 99.0`). 세 번째
bound 소스인 `cfg.param_overrides`(`doraemon.py:332`)는 임의 파라미터의 bound를
오버라이드하고 nominal을 midpoint로 리셋할 수 있다.

> **`PARAM_SPECS` 모듈 상수 vs live 시작점.** `envs/main/doraemon.py`가
> export하는 `PARAM_SPECS` 리스트는 **plain midpoint** nominal을 쓰며
> `_NOMINAL_OVERRIDES`를 적용하지 **않는다** — 회귀 가드를 통과시키려 promotion
> 이전 스냅샷과 byte-identical로 유지된다. **live 커리큘럼 시작점으로
> `PARAM_SPECS`를 인용하지 말 것**. live 경로는 `build_param_specs` +
> `_NOMINAL_OVERRIDES`를 거친다.

### `EpisodeBuffer`

링 버퍼(cap `2000`, `doraemon.py:228`)로, 끝난 episode마다 샘플된 `xi`, return,
이진 `success`, `log_probs`를 저장한다. `get_stats()`(`doraemon.py:208`)는 차원별
**물리** mean/std를 emit한다 — 이것이 `DORAEMON/mean/<param>` 및
`DORAEMON/std/<param>` wandb 신호다.

---

## 4. DORAEMON 커리큘럼 엔진

DORAEMON — **Domain Randomization via Entropy Maximization**(Tiboni et al.,
ICLR 2024) — 은 `DoraemonScheduler`(`doraemon.py:300`)로 구현된다. `step_interval`
RL iteration마다 **하나의 제약 최적화**를 푼다: 정책의 추정 성공률이 하한 아래로
떨어지지 않고 한 step에 너무 멀리 이동하지 않으면서 DR 분포를 최대한 넓힌다(max
엔트로피).

$$
\max_{\phi=\{(a_i,b_i)\}}\ H(\phi)
\quad\text{s.t.}\quad
\hat G(\phi)\ge\alpha
\ \text{그리고}\
\mathrm{KL}\!\left(\phi\,\|\,\phi_{\text{prev}}\right)\le\varepsilon
$$

### Config: 엔진 기본값 vs ALBC live 오버라이드

| 필드 | 엔진 기본값 (`doraemon.py:38`) | **ALBC live** (`config.py:479`) | 역할 |
|:---|:---|:---|:---|
| `performance_lb` | 80.0 | **250.0** | 이진 success의 return 임계값 |
| `alpha` | 0.5 | 0.5 | 목표 IS-추정 성공률 ($\alpha$) |
| `kl_ub` | 0.5 (ref 기본 1.0) | **0.12** | step당 reverse-KL 신뢰영역 ($\varepsilon$) |
| `init_concentration` | 30.0 | 30.0 | 초기 Beta `a+b` |
| `step_interval` | 250 | 250 | 업데이트 간 RL iter 수 |
| `buffer_size` | 2000 | 2000 | episode 링 용량 |
| `min_episodes` | 200 | 200 | 첫 업데이트 전 최소 버퍼 |
| `min_ess_ratio` | 0.01 | 0.01 | 업데이트 수용 ESS 하한 |
| `hard_performance_constraint` | True | True | infeasible 시 inverted problem 사용 |

> **엔진 기본값이 아니라 caller의 `DoraemonCfg`를 읽어라.** shipped `kl_ub`는
> **0.12**, `performance_lb`는 **250.0**이다(`config.py:479`). 엔진의 `kl_ub`
> docstring("relaxed for kl_ub=2.0", `doraemon.py:46`)과 `80.0` 기본값은 둘 다 ALBC
> config 기준으로 낡았다. `performance_lb`는 recon
> run(`trpo_baseline_260608_160453`)에서 캘리브레이션됐다: `lb=68`이면 success
> 플래그가 항상 1(관측 최소 return ~82 아래)이라 `Ghat >= alpha` 제약이 무력화돼
> 커리큘럼이 무제약으로 확장됐고, `lb=250`(return p25)이 live 신호를 복원한다.

### `step()` 제어 흐름 (`doraemon.py:384`)

```
step(iteration):
  xi, returns, success, log_probs = buffer.get_all()
  if n < min_episodes:           -> metrics{skipped=1, entropy=...}   RETURN  (키는 entropy_before/after가 아니라 'entropy')
  report success_rate, entropy_before, per-param stats  (항상)
  if step_count % step_interval != 0:  -> metrics{kl_step=0}          RETURN  (업데이트 사이 report-only)

  prev_dist = dist.clone()
  Ghat = _estimate_success_rate(xi, success, ref=prev_dist)

  if hard_performance_constraint and Ghat < alpha:      # INFEASIBLE
     feasible, ok = _find_feasible_start(prev_dist, ...)  # inverted problem: max Ghat, budget kl_ub - 1e-5
     if ok:
        set_flat_params(feasible)
        if _estimate_success_rate() >= alpha:
           _optimize_entropy(prev_dist, ...) ; mode = 1.0   # inverted + optimize
        else:
           mode = -2.0                                       # max-success 분포 유지
     else:
        dist = prev_dist ; mode = -3.0                       # inverted 실패 -> revert
  else:                                                  # FEASIBLE (또는 soft)
     _optimize_entropy(prev_dist, ...) ; mode = 0.0          # normal

  entropy_after, kl_step = ...
  ess, ess_ratio = _compute_ess(...)
  if ess < min_ess_ratio * n:   dist = prev_dist ; reverted = 1.0    # ESS revert
  _trajectory.append({iter, a, b})                                    # replay용
```

`mode` 메트릭은 boolean이 아니라 **다중값 코드**다: `0.0` normal, `1.0`
inverted+optimize, `-2.0` max-success 유지, `-3.0` inverted-실패 revert.

### 엔진 뒤의 네 방정식

**KL 제약(reverse KL, 차원별 합).** SLSQP는 이를
$g(\phi) = \varepsilon - \mathrm{KL} \ge 0$ 형태로 받는다(`doraemon.py:551`; 헬퍼
`_compute_kl`은 `doraemon.py:91`):

$$
\mathrm{KL}(\phi\,\|\,\phi_{\text{prev}})
= \sum_{i=1}^{16}\mathrm{KL}\!\Big(\mathrm{Beta}(a_i,b_i)\,\big\|\,\mathrm{Beta}(a_i^{\text{prev}},b_i^{\text{prev}})\Big)\le\varepsilon
$$

**IS 성공률 추정(unnormalized).** success는 이진
$\sigma_k = \mathbb{1}[J_k \ge \texttt{performance\_lb}]$이고 log-ratio는 $\pm 5$로
clamp된다(`_IS_LOG_CLAMP = 5.0`, `doraemon.py:88`):

$$
\hat G(\phi)=\frac{1}{K}\sum_{k=1}^{K}\exp\!\Big(\mathrm{clip}\big(\log p_\phi(\xi_k)-\log p_{\phi_{\text{prev}}}(\xi_k),\,-5,\,+5\big)\Big)\,\sigma_k
$$

> **분모는 buffered `log_probs`가 아니라 *live로 평가한* `prev_dist`다.**
> `_estimate_success_rate`(`doraemon.py:486`)는 호출 시점에
> `prev_dist.log_prob(xi)`를 재계산한다. 클래스 docstring 줄(`doraemon.py:307`,
> "Unnormalized IS with stored per-episode log probs")은 **낡았다** — 저장된
> `log_probs`(및 `returns`)는 최적화에서 사실상 죽은 값이다.

**ESS revert 게이트.** 최적화 후, importance-sampling 추정기가 너무 degenerate하면
업데이트를 폐기한다(`doraemon.py:458`):

$$
\mathrm{ESS}=\frac{1}{\sum_k w_k^2},\quad w_k\propto\exp\!\big(\log p_\phi(\xi_k)-\log p_{\phi_{\text{prev}}}(\xi_k)\big),\ \textstyle\sum_k w_k=1;
\quad \text{revert if } \mathrm{ESS}<\texttt{min\_ess\_ratio}\cdot n
$$

최적화 자체는 **log-space** SLSQP다(`_optimize_entropy`, `doraemon.py:577`):
변수는 `log(a), log(b)`, Beta 파라미터는 `[1.0, 500.0]`로 clamp. 수렴하지 않은
SLSQP 결과는 **오직** `perf_ok AND result.fun < init_obj AND kl <= kl_ub`
일 때만 수용된다(`doraemon.py:653`) — 이 가드는 stall한 solver가 하한 미달 분포를
commit하지 못하게 한다. `_find_feasible_start`(`doraemon.py:679`)는 성공 episode가
0개면 즉시 `False`를 반환한다.

---

## 5. 샘플된 값에서 물리로 (reset 시점 적용)

적용은 **명령형**이며 `EventManager` 구동이 아니다. `randomize_*` 함수들은
`_reset_physics`(정의 `albc_env.py:1333`)와 `_reset_task_and_state`
(`albc_env.py:1398`)에서 호출된다.

**reset마다 컨트롤러가 한 번 샘플**해 `spec.name`을 키로 하는 `sampled` dict를
만들고(`albc_env.py:1362`), `DRSampler(cfg, N, device)`를 구성해 둘 다 각
randomizer로 전달한다.

### 커리큘럼-vs-uniform 다리: `_sample_or_uniform`

`_sample_or_uniform`(`events.py:46`)이 파라미터를 커리큘럼 관리로 만들지
uniform-only로 만들지 결정하는 정확한 스위치다:

```
_sample_or_uniform(field_name, sampled, shape, cfg_range, device, broadcast_dim):
    if field_name in sampled:      -> per-env DORAEMON 텐서 (스칼라를 broadcast_dim DOF로 broadcast)
    else:                          -> cfg_range에서 uniform 샘플
```

`sampled`에 키가 있으면 ⇒ DORAEMON 관리, 없으면 ⇒ uniform. 이것이 둘을
구분하는 **유일한** 것이다.

### base 캐싱: `_HydroBaseCache`

`_HydroBaseCache`(`events.py:144`)는 첫 reset에서 8개 유체역학 base 필드를 lazily
캐싱한다(frozen baseline이라 scaling이 reset 간 누적되지 않음). `rigid_body_inertia`가
미설정이면 inertia는 경고와 함께 `0.5 * added_mass[3:6]`로 fallback한다.

### scale vs absolute vs offset (필드마다 다름)

| 의미 | 필드 |
|:---|:---|
| **cached base에 scale** | added_mass, linear/quadratic damping, volume, inertia, body_mass |
| **absolute 값** | water_density, payload_mass |
| **base + offset** | center-of-buoyancy(CoB), center-of-gravity(CoG) |

주목할 순서 quirk: 회전 **DOF-5(yaw)는 이중 처리**된다 — quadratic-damping scale이
적용된 뒤 `yaw_damping_scale`로 덮어써진다. `env._hydro`와 `env._buoy_hydro`는 하나의
샘플 scale을 공유하고, 부력은 CoB/CoG offset 이후 재계산된다. `enable = False`면
randomizer들은 early-return(no-op)한다.

### Payload

payload 질량은 absolute, CoG XY offset은 반경 `payload_cog_offset_xy_radius`의
디스크에서 `r = r_max * sqrt(U)`로 샘플된다(면적 균등).
`_apply_xyz_offset_with_doraemon`(`events.py:63`)와
`_clamp_payload_cog_stability`(`events.py:88`)가 정적 안정성을 강제한다.

> **payload toggle은 기본 off.** `_setup_payload_toggle`은 `payload_toggle_steps
> == 0`이면 early-return하고, 기본값이 `0`이다(mid-episode payload toggle 없음).
> cfg가 nonzero toggle을 설정하지 않는 한 payload가 mid-episode에 토글된다고
> 가정하지 말 것.

### 해류 강도

3-way 해석(`events.py:294`, `ocean_current.py`): DORAEMON 샘플된
`ocean_current_strength`가 있으면 사용, 없으면 `ocean_current_strength_range`에서
uniform 샘플, 그것도 없으면 fallback. 강도 `[0, 1]`은 noise 항 **이후**에
`ocean_current.max_velocity`에 곱해지고, 전체 경로는 env가 실제로 ocean-current
컴포넌트를 가질 때만(`_has_ocean_current`) 실행된다.

### 두 안정성 clamp

**Added-mass vs 일반화 inertia**(`events.py:214`) — 수치 안정성을 위해
$M_a / I < 1$을 유지하며, `apply_added_mass_force` AND `body_mass` 존재 시에만
게이트된다:

$$
M_a[i]\ \le\ 0.95\,\cdot\,\mathrm{gen\_inertia}[i],
\qquad \mathrm{gen\_inertia}=[\,m_{\text{body}},m_{\text{body}},m_{\text{body}},\ I_{xx},I_{yy},I_{zz}\,]
$$

**Payload-CoG 정적 안정성**(`events.py:88`) — 부력 복원 모멘트가 중력의 전도
모멘트를 지배하도록 CoG offset을 제한한다(scale은 `1.0`로 cap; 부력 $F_{bu}$와
모멘트 암 $h$ 사용):

$$
m\,g\,\lVert r^{\text{eff}}_{xy}\rVert_2\ \le\ F_{bu}\,h,
\qquad r_{\max}=\frac{F_{bu}\,h}{m\,g}\ (\infty\ \text{if}\ m\le 10^{-6}),
\qquad s=\min\!\Big(\frac{r_{\max}}{\max(\lVert r^{\text{eff}}_{xy}\rVert,\,10^{-8})},\,1\Big)
$$

---

## 6. 훈련 루프 와이어링

env가 `_doraemon`을 소유하며 `_init_doraemon`(`albc_env.py:381`)에서 생성되고,
`replay_curriculum_path`로 분기한다: 비어 있으면 ⇒ `DoraemonScheduler`(live 학습),
설정되면 ⇒ `CurriculumReplayer`(frozen, §7). 활성 시 per-env 버퍼
`_episode_dr_xi` / `_episode_dr_log_probs` / `_episode_return_accum`가 할당된다.

**End-to-end 루프:**

```
per RESET   : xi, log_probs = _doraemon.sample(N)      -> per-env 스태시 -> events가 xi를 물리에 적용
per STEP    : _episode_return_accum += reward           (_doraemon 활성 시 게이트)
on next RESET (끝난 env마다):
              success = (_episode_return_accum >= performance_lb)   # <-- 이진화는 여기, CALLER에서
              _doraemon.record_episodes(xi, returns, success, log_probs)   (albc_env.py:1281)
per ITER    : runner.log() -> metrics = _doraemon.step(iteration=it)  -> DORAEMON/ prefix로 재emit
```

> **success 이진화는 엔진이 아니라 caller에 있다.** `success = return >=
> performance_lb`는 `albc_env.py:1281`에서 계산되고, 엔진의 `record_episodes`는
> **미리 계산된 `success` 텐서**를 받는다. 그래서 엔진 클래스
> docstring(`doraemon.py:307`)이 오해를 부른다 — 엔진은 이진화하지도, 저장된
> `log_probs`를 그 수식에 쓰지도 않는다.

**Runner 분기.** 기본 TRPO 경로는 `ConstraintEncoderRunner`
(`runners/constraint_encoder_runner.py:253`, `iteration=` 전달)를 쓰고, PPO
ablation은 `OnPolicyDoraemonRunner`(`runners/on_policy_doraemon_runner.py:83`,
`iteration` kwarg 없음 → `_trajectory` iter가 `_step_count`로 fallback)를 쓴다. 그
외 동작은 동일하다.

**체크포인팅.** `state_dict`(`doraemon.py:773`)는 `dist_a` / `dist_b` + step/episode
카운트 + 전체 episode 버퍼를 직렬화한다. `export_recording`(`doraemon.py:765`,
`DoraemonScheduler` **전용**)은 replay용 커리큘럼 trajectory를 쓰며, `hasattr`
가드가 있어 replay run은 아무것도 쓰지 않는다.

**Emit 메트릭**(`DORAEMON/` prefix): `success_rate`, `entropy_before` /
`entropy_after`(skip 분기에서는 plain `entropy`), `kl_step`, `ess` / `ess_ratio`,
`mode`(다중값, §4), `reverted`, `skipped`, 파라미터별 `mean/<name>` /
`std/<name>`.

---

## 7. 커리큘럼 Replay

`CurriculumReplayer`(`doraemon.py:814`)는 **frozen 커리큘럼 경로**이며,
`replay_curriculum_path`가 설정될 때 활성화된다(`albc_env.py:396`).
`DoraemonScheduler`를 duck-type(`sample` / `step` / `record_episodes` /
`state_dict`)하지만 **학습은 하지 않는다**:

- `sample()`은 여전히 Beta에서 뽑는다.
- `step()`은 `iteration` 인자를 키로 하는 **hold-last step 함수**다
  (`doraemon.py:865`): iter `t`의 분포는 `iter <= t`인 마지막 기록 `(a, b)`다.
  `iteration`이 `None`이면 `0`으로 기본 설정 — 그래서 `iteration`을 전달하지 않는
  runner는 replay를 첫 기록 항목에 고정시킨다.
- `record_episodes`는 **no-op**, `load_state_dict`는 **no-op**, `state_dict`는
  `dist_a` / `dist_b`만 반환한다(스케줄이 분포를 구동하므로 checkpoint-복원할 게
  없음).

**기록 포맷**(`export_recording`): `{param_names, param_bounds, trajectory}`.
`_validate`(`doraemon.py:843`)는 param **name 순서**와 **bound**(tolerance `1e-9`)를
기록과 hard-check하고 불일치나 빈 trajectory면 raise한다. replayer 자신의
`DoraemonCfg()`와 throwaway `concentration = 2.0`(`_apply(0)`이 즉시 덮어씀)은
env의 success 계산이 crash하지 않도록만 존재한다 — 계산된 success는 이후
버려진다.

---

## 8. Eval 측 DR

**Eval DR은 DORAEMON Beta 커리큘럼을 완전히 우회하는 고정 *uniform 보간*이다.**
eval 중에는 `step()` / `record_episodes`가 없다. DORAEMON과의 유일한 접점은 run의
최종 `mean` / `std`를 TensorBoard에서 *읽는* 것뿐이다. 엔트리 포인트는
`analysis/eval.py`이며 — rules/CLAUDE.md가 아직 명시하는 `eval_dr.py`가 **아니다**
(그 이름의 파일은 없다).

### 네 레벨

`none / soft / medium / hard`는 고정 scale 분수 `0.0 / 0.3 / 0.6 / 1.0`
(`common.py:36`의 `DR_SCALE` 맵, 5번째 `ood: 1.0`도 포함)을 써서, true-nominal
단일점(scale `0`)과 **hard 앵커**(scale `1`) 사이를 선형 보간한다. 레벨별 적용은
`eval.py:345`의 `apply_dr_config`이고, hard 앵커 자체는 DORAEMON-학습된
`mean ± 2·std`를 PARAM_SPEC bound로 clamp해 `get_hard_dr_config`
(`dr_config.py:253`)가 만든다(`dr_config.py:237`).

> **`soft`는 `DomainRandomizationCfg`가 아니고 `hard`는
> `HardDomainRandomizationCfg`가 아니다(기본).** 둘 다 보간 *엔드포인트*다. hard
> 앵커는 기본적으로 run의 **DORAEMON-학습된** 분포(파라미터별 TB의
> `mean ± 2·std`, PARAM_SPEC bound에 clamp; `build_hard_dr_from_doraemon`,
> `dr_config.py:185`)로 설정되며, `HardDomainRandomizationCfg`는 DORAEMON 태그가
> 없을 때의 fallback으로만 쓰인다. `get_hard_dr_config`(`dr_config.py:253`)는
> **deepcopy**를 반환해 OOD 레벨의 `setattr`가 전역 앵커를 clobber하지 못하게 한다.

### 세 모드 (정확히 세 개)

| 모드 | 하는 일 | 메커니즘 |
|:---|:---|:---|
| **static** | DR을 episode 전체에 고정; *command*는 segment마다 전환 | 레벨마다 `apply_dr_config`(`eval.py:1183`) |
| **periodic** | mid-episode DR **충격** | 모듈 레벨 `apply_dr_mid_episode`가 새 `DRSampler` 구성 |
| **segmented** | **역시** mid-episode DR 변경 | env 메서드 `raw_env.randomize_physics_mid_episode` + `torch.manual_seed(master_seed + seg_idx)`로 재현 가능한 전환 시퀀스 |

> **task-명 `sudden` 모드는 존재하지 않는다** — rules가 언급하지만 코드에는
> static/periodic/segmented만 있다. periodic과 segmented **둘 다** mid-episode에
> DR을 바꾸며, 서로 *다른* 코드 경로를 쓴다(periodic은 새 sampler 구성, segmented는
> segment마다 재현성을 위해 reseed).

### `dr_snapshot`

`_eval_dr/dr_snapshot.py`(`:45`)는 이미 고정된 post-clamp 물리 텐서를 로깅용
`dr_<name>[N]` 배열로 바꾸는 **순수 post-hoc 재구성기**다 — DR freeze/realize
단계가 **아니다**. 재현 가능한 고정 물리는 각 `(lo, hi)` 튜플을 midpoint로
collapse하는 `--deterministic-dr`에서 온다. `apply_dr_config`를 완전히 우회하는
5번째 OOD 레벨(full DORAEMON-유도)도 있다.

---

## 9. 함정과 이름-vs-구현 트랩

소스를 감사하는 독자가 부딪힐 cross-cutting 함정들. 각 항목은 트랩과 그 교정
사실을 앵커와 함께 제시한다.

1. **`performance_lb`는 return 임계값이지 성공률이 아니다.** success를
   이진화한다($\sigma = \mathbb{1}[J \ge \texttt{performance\_lb}]$). 성공-*률*
   목표는 `alpha`(0.5)다. 이 둘을 혼동하면 제약이 뒤집힌다. (`doraemon.py:39`)

2. **엔진은 이진화하지 않고 caller가 한다.** `success = return >=
   performance_lb`는 `albc_env.py:1281`에서 계산되고 `record_episodes`는 완성된
   `success` 텐서를 받는다. `doraemon.py:307`의 클래스 docstring("stored
   per-episode log probs")은 **낡았다** — IS 추정기는 `prev_dist` 하에서
   `log_prob`을 live 재계산하며 buffered `log_probs`를 쓰지 않는다.

3. **엔진 기본값이 아니라 caller의 `DoraemonCfg`를 읽어라.** live `kl_ub`는
   **0.12**, `performance_lb`는 **250.0**이다(`config.py:479`). 엔진의
   `0.5` / `80.0`이 아니다. "relaxed for kl_ub=2.0" 주석(`doraemon.py:46`)도 낡았다.

4. **Eval `soft`/`hard`는 학습된 분포 위 보간 엔드포인트**이지 두 cfg 클래스가
   아니다. "soft = DomainRandomizationCfg, hard = HardDomainRandomizationCfg"는
   기본적으로 틀린 전제다. (`dr_config.py:185`, `:253`)

5. **Eval 모드는 세 개뿐**(static/periodic/segmented)이고 `sudden`은 없으며,
   `eval_dr.py`는 실제 엔트리 포인트가 아니다(`eval.py`가 맞다). periodic *과*
   segmented 둘 다 mid-episode에 DR을 바꾸며 경로가 다르다.

6. **`_PARAM_DEFS` 리터럴 bound는 fallback 전용.** `build_param_specs`가
   `getattr`로 `config.py`에서 live bound를 읽는다 — `config.py`가 범위 SSOT.
   `config.py:187`의 "15 parameters" 주석에도 불구하고 `NDIMS = 16`.

7. **업데이트는 세 가지 방식으로 silent no-op될 수 있다**(SLSQP 거부 /
   `mode = -3` inverted-실패 revert / ESS revert) — 모두 분포를 그대로 둔다.
   `mode`와 `reverted` 메트릭만이 이를 구분한다. `entropy_after ==
   entropy_before`가 업데이트 시도가 없었음을 의미하지 **않는다**.

8. **두 concentration 기본값이 불일치한다.** `BetaDistribution.__init__ = 200.0`은
   ALBC 경로에서 죽은 값이고, live 스케줄러는 `DoraemonCfg.init_concentration =
   30.0`을 쓴다.

9. **DR은 `EventTerm`/`EventManager`가 아니라 `_reset_physics`에서 명령형으로
   적용**된다(`events.py:6` docstring에도 불구하고). 필드 의미도 다르다(cached base에
   SCALE vs ABSOLUTE vs base+OFFSET). 회전 DOF-5(yaw)는 이중 처리되고,
   added-mass clamp는 `apply_added_mass_force`가 off면 silent 스킵된다.

---

## 부록: 파일/라인 빠른 색인

| 관심사 | 앵커 |
|:---|:---|
| 엔진 config 기본값 | `marinelab/algorithms/doraemon.py:38` |
| `step()` 제어 흐름 | `doraemon.py:384` |
| Infeasible 분기 / inverted problem | `doraemon.py:430`, `:679` |
| IS success 추정 | `doraemon.py:486` |
| `_optimize_entropy` (SLSQP) | `doraemon.py:577` |
| ESS revert | `doraemon.py:458` |
| `BetaDistribution` | `doraemon.py:115` |
| `build_param_specs` | `doraemon.py:65` |
| `CurriculumReplayer` | `doraemon.py:814` |
| 16개 param 정의 / override | `constrained_albc/envs/main/doraemon.py:41`, `:66` |
| DR 범위 (soft/hard) | `constrained_albc/envs/main/config.py:133`, `:184` |
| **Live `DoraemonCfg` override** | `config.py:479` |
| Reset 시점 적용 | `envs/main/mdp/events.py:46`, `:88`, `:144`, `:214` |
| Sample + record 와이어링 | `albc_env.py:381`, `:1281`, `:1362` |
| Runner step 호출 지점 | `runners/constraint_encoder_runner.py:253` |
| Eval 레벨 / 앵커 | `analysis/dr_config.py:185`, `:253`; `common.py:36`; `eval.py:345` |
| Eval 모드 | `analysis/eval.py:890` (static), `:1183` (레벨 루프), `:1517` (periodic) |
