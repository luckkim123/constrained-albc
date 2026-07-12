# Action 파이프라인 (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 action 전 경로 — 정책의 raw Gaussian 출력에서
> 시작해, 경계 clamp를 거쳐, 두 개의 물리 액추에이터 경로(arm delta-PD, 6-thruster
> TAM wrench)로 갈라지고, 다시 observation으로 되먹여지기까지. 8D action은
> `[2D arm delta, 6D thruster command]`이다.
>
> 디스크에 대해 검증된 code-level 레퍼런스다. encoder / actor / critic 층 구조와
> ConstraintTRPO 업데이트를 다루는 `main-network-architecture.ko.md`의 **action 쪽
> 짝 문서**다. std clamp·entropy·log_std처럼 네트워크 내부에 속하는 주제는 여기서
> 반복하지 않고 링크로 넘긴다.
>
> **브랜치 주의.** 아래 물리 파라미터 사실은 marinelab `main` 기준이다(기본 설치
> 대상; 로컬 `main` = `8364cd6`, 커밋 `0c882df`의 per-thruster fault 경로를 병합한
> 상태). 즉 `main`에는 fault 경로가 **존재**하고(기본 off) 비선형 thrust curve는
> **없다**. curve는 여전히 별도 미병합 브랜치 `exp/thruster-curve`(커밋 `d34debc`,
> 기본 off)에만 있다 — 이 브랜치는 이후 fault도 병합해(marinelab 커밋 `0ed193e`,
> unpushed) curve와 fault를 **둘 다** 가지며, 순서는 curve → coeff → health →
> clamp다(§5.3-5.4). 어느 쪽이 checkout돼 있어도 문서가 정확하도록 §5.3/§5.4/§7에
> 상태를 표시했다.

---

## 1. 개요

action은 8D 벡터다. 정책은 이를 **squashing도 clamping도 없는 raw Gaussian
샘플**로 내보내며, 모든 경계는 네트워크 *하류*에서 적용된다. 이후 벡터는 소스
벡터 외에는 아무것도 공유하지 않는 두 개의 물리적으로 다른 액추에이터 경로로
갈라진다:

```
POLICY  (actor MLP -> Gaussian)
  a ~ Normal(action_mean(8), exp(log_std)(8))          # act(): sample, NO clamp
  a = action_mean                                       # act_inference(): mean, NO clamp

BOUNDARY  (two independent clamps to [-1, 1])
  (1) RslRlVecEnvWrapper.step():  a <- clamp(a, -clip_actions, +clip_actions)   # if configured
  (2) ALBCEnv._update_action_buffers(): self._actions = a.clamp(-1, 1)          # always

SPLIT
  a[0:2]  ARM     -> q_des += 0.10 * a     (delta integrator, unbounded)
                  -> set_joint_position_target  -> ImplicitActuator PD (Kp=100, Kd=3)
  a[2:8]  THRUSTER-> first-order filter (tau_up=0.1, tau_down=0.05)  -> state s in [-1,1]
                  -> [optional thrust curve]  -> * thrust_coeff (40) -> clamp(+-50 N)
                  -> [optional * health]      -> 6x6 TAM  -> body wrench (F 3D, M 3D)

FEEDBACK
  filtered thruster state s (6D) re-enters the 20D proprioception as "thruster_state"
  the full 8D action re-enters the temporal history (8D x 2 steps = 16D)
```

**핵심 설계 선택.** (a) Gaussian은 *unbounded*이고, `[-1, 1]`은 정책 쪽 squashing이
아니라 env가 강제하는 *해석 계약(interpretation contract)*이다(SAC의 tanh와 달리
PPO/TRPO의 표준). (b) 같은 8D 벡터가 완전히 다른 두 dynamics를 구동한다: arm
차원은 **위치-delta 적분기**(PD target 위의 leak 없는 누적기)이고, thruster 차원은
**힘 저역통과 필터**(1차 ESC lag)다. (c) observation은 raw 명령이 아니라 *필터링된*
thruster state를 되먹인다 — 정책은 ESC-feedback 같은 신호를 본다.

### 1.1 단일 8D 벡터가 두 dynamics를 구동하는 이유 (multi-head 미채택)

정책은 정규화된 `[-1, 1]` 명령만 내보내고, 스케일·dynamics 차이(arm `delta_scale
0.10` vs thruster `thrust_coeff 40`; arm PD는 즉시 반응 vs thruster는 1차 필터
lag — 정책은 필터링된 `thruster_state`로 이 lag를 observation에서 본다)는 env가
흡수한다. 이건 표준적인 구성이다. output layer는 이미 8개의 독립 scalar head다
(linear last layer, per-dim `log_std`) — 공유되는 건 hidden trunk `[256, 128, 64]`
뿐이다. 즉 "단일 vs multi-head" 질문은 실질적으로 "arm과 thruster가 hidden trunk를
공유해야 하는가"로 좁혀진다. 현재는 공유 trunk다: attitude 제어에서 arm과
thruster는 강하게 결합돼 있다(thruster가 attitude를 만들고, arm 동작이 반작용/CoG로
그걸 교란) — 이 결합을 살리려면 공유 trunk가 자연스러운 선택이고, head를 분리하면
표현 단계에서 그 결합을 끊는 셈이다. trunk 분리는 두 subtask가 이질적이면서
간섭하거나 한쪽 gradient가 다른 쪽을 지배할 때만 이득이다 — 현재 코드베이스에는
그 증거가 없다. arm/thruster gradient의 cosine similarity를 로깅하거나
separate-network ablation으로 먼저 측정하지 않고 multi-head를 도입하지 말 것
(`.claude/rules/03` — 근거 없는 일반적 해법 금지).

---

## 2. Action space — 8D

`action_space = 8` (`config.py:303`), `[2D arm delta, 6D thruster]`로 분할.

| Index | 구성 | 해석 | 하류 |
|---|---|---|---|
| `[0:2]` | arm joint delta | `q_des += delta_scale * a` (`delta_scale=0.10`, `config.py:360`) | `ALBC_JOINT_NAMES`(2 joints)에 누적되는 PD position target |
| `[2:8]` | thruster commands (T0-T5) | 1차 필터로 `state ∈ [-1,1]`, 이후 스케일링 + TAM 할당 | 6×6 allocation matrix로 body-frame 6-DOF wrench |

2개 arm joint(`albc_joint_names`)는 **연속 회전 모터**다 — 물리적 위치 제한이 없어
delta target은 wrap되지 않는다(§4). 6개 thruster는 ALBC ROS control package TAM을
따른다(`config.py:90-97`).

---

## 3. 정책 출력과 두 개의 경계 clamp

### 3.1 정책은 clamp하지 않는다

두 action 진입점 모두 raw 네트워크 출력을 반환한다:

- `act()` (`actor_critic_encoder.py:272`): `actor_obs = cat[EmpiricalNorm(o_t), z_raw]`를
  만들고, `distribution = Normal(actor(actor_obs), exp(log_std))`를 세운 뒤
  `distribution.sample()`을 반환한다 — docstring도 명시적이다: *"Sample action from
  Gaussian policy (no action clamping)."*
- `act_inference()` (`:279`): `actor(actor_obs)`를 그대로 반환한다 — mean, 역시
  *"no clamping."*

`std = exp(log_std)`는 배치 전체에 broadcast되는 단일 global 파라미터
(state-independent)다. clamp·entropy 거동·문헌 표준성은
`main-network-architecture.ko.md` §4와 §9에 있다. 여기서는 **범위 밖**이다 — 이
문서는 샘플된 `a`가 존재하는 시점부터 시작한다.

### 3.2 Clamp #1 — vecenv wrapper (`clip_actions`, 현재 no-op)

`RslRlVecEnvWrapper.step()`은 action을 env로 넘기기 *전에* clamp한다
(`isaaclab_rl/rsl_rl/vecenv_wrapper.py:151-154`):

```python
if self.clip_actions is not None:
    actions = torch.clamp(actions, -self.clip_actions, self.clip_actions)
```

값은 wrapper 생성 시 `agent_cfg.clip_actions`에서 온다
(`scripts/train.py:292`: `RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)`).
`clip_actions is None`이면 no-op이고 clamp #2만 적용된다.

**현재 상태: 이 clamp는 실제로 no-op이다.** `rsl_rl_ppo_cfg.py`가 `clip_actions`를
설정하지 않아 isaaclab 기본값 `None`을 그대로 물려받는다(`rl_cfg.py:181`).
`train.py:292`가 `agent_cfg.clip_actions`(`=None`)를 그대로 wrapper에 넘기고,
`train_student.py:120`도 `clip_actions=None`을 명시적으로 넘긴다. 즉 모든 실행
경로에서 **clamp #2(§3.3)만** action을 실제로 제한한다 — §3.3의 탐색 함의는
전부 clamp #2에서 나온다.

### 3.3 Clamp #2 — env action buffer (항상)

`ALBCEnv._update_action_buffers()` (`albc_env.py:452`)는 `_pre_physics_step` 맨 위에서
호출되며, 3-deep action 이력을 조건 없이 clamp하고 회전시킨다:

```python
self._prev_prev_actions = self._prev_actions.clone()
self._prev_actions       = self._actions.clone()
self._actions            = actions.clone().clamp(-1.0, 1.0)
```

항상 성립하는 clamp는 이것이다. **탐색에 대한 함의:** 정책 std가 unbounded이고
*물리로의 입력*만 clamp되므로, 큰 `log_std`는 ±1에서 saturate되는 범위 밖 샘플에
확률 질량을 낭비한다 — 이것이 std가 줄어드는 경향의 구조적 이유 중 하나다(network
문서의 entropy-collapse 논의 참조). 이 clamp는 매끄러운 squash가 아니라 hard
saturation이라, gradient가 경계를 통해 되흐르지 않는다.

**gradient 관점 명확화.** 외부 clamp가 "정책이 자신이 내보내지 않은 값으로부터
학습한다"는 뜻은 아니다 — policy gradient는 `log π(raw a | o)`를 쓴다. 즉 clamp
*이전의* raw 샘플이 업데이트가 credit을 주는 대상이며, 이 점에서 clamp는 아무
불일치도 만들지 않는다. 실제 문제는 **credit 배정의 왜곡**이다: `a=1.5`와
`a=3.5`가 둘 다 `1.0`으로 clamp되므로, `[1, ∞)` 범위 밖 구간은 환경 입장에서
서로 구별되지 않는다 — 이 구별 불가능성 + 경계 밖 확률 질량 낭비가 std를 줄이는
쪽으로 미는 하방 압력이다. tanh-squash와의 대비는 §8 참조(여기서 중복 서술하지
않음).

---

## 4. Arm 경로 — delta 적분기 → PD

`_pre_physics_step`은 `arm_actions = self._actions[:, :2]`를 슬라이스하고, control
decimation으로 gating해 `_apply_joint_pd_action`을 호출한다(`albc_env.py:558-560`):

```python
arm_actions = self._actions[:, :2]
if self._control_step_counter % self.cfg.control_decimation == 0:
    self._apply_joint_pd_action(arm_actions)
```

### 4.1 Delta 누적 (unbounded)

`_apply_joint_pd_action` (`:567-578`)은 **leak 없는 위치 적분기**다:

```python
self._joint_pos_targets += self._delta_scale * actions   # delta_scale = 0.10
```

`a ∈ [-1, 1]`이고 `delta_scale = 0.10`이므로, step당 target 변화는 최대
**0.10 rad/step**(코드 주석 기준 전형적 action 크기에서 ≈ 0.08 rad)이다. 이 delta
파라미터화는 의도적이다: step당 위치 변화를 제한해 step 명령에 의한 PD 액추에이터
saturation을 방지한다.

**`_joint_pos_targets`는 절대 wrap·clamp되지 않는다.** 쓰기는 셋뿐이다:
nominal 초기화(`:278`, `nominal_joint_pos = (0.0, π/2)`), `+=` 누적(`:578`), 측정된
joint 위치로의 reset(`:1315`). 어느 것도 clamp하지 않는다. joint가 연속 회전 모터라
target 적분기는 설계상 무한히 커진다; joint1 케이블 wrapping은 target을 clamp하는
게 아니라 `joint1_position_cost` **constraint**(`|θ_cum| > 4π` budget)로 보호된다.
(joint1 anti-drift 작업이 clamp가 아니라 constraint-redesign 문제인 이유가 정확히
이것이다: `main-network-architecture.ko.md` §5.1과 joint1 캠페인 문서 참조.)

**개념 명확화: 이건 PID error-적분기가 아니라 position-command 적분기다.**
`_joint_pos_targets`는 PD 오차를 누적하는 게 아니라, 정책이 매 step delta로
조종하는 *살아있는 위치 명령*이다. reset은 **episode 경계에서만** 일어난다 —
episode 내에서는 unbounded 누적, episode reset에서 env별로 *측정된* joint 위치로
재초기화(`:1315`)된다. 측정값으로 재초기화하는 이유는 anti-bump: PD torque
`~ Kp·(q_des - q_measured)`이므로 reset 순간 `q_des = q_measured`로 맞추면 초기
자세가 무작위로 뒤섞여도 오차가 0에서 시작해 초기 torque 킥이 없다. **"joint가
target에 도달하면 적분기를 reset하고 다음 target을 계산한다"는 waypoint-following
방식은 이 구조에 맞지 않으며 제어를 깨뜨린다** — target 도달은 유지(hold)
상태이지 reset 트리거가 아니다. target 도달 시 `q_des`를 0/nominal로 되돌리면
팔이 원점으로 튕겨나간다. 유효한 reset 트리거는 episode 경계 하나뿐이다.

### 4.2 PD 액추에이터

`_apply_action` (`:780`)이 누적된 target을 쓴다:

```python
self._robot.set_joint_position_target(self._joint_pos_targets, joint_ids=self._albc_joint_ids)
```

joint는 robot asset의 `ImplicitActuatorCfg`로 구동된다
(`marinelab/assets/albc/albc.py:196-202`):

| 필드 | 값 | 비고 |
|---|---|---|
| stiffness (Kp) | 100.0 | `J ≈ 0.15 kg·m²`에서 `ω_n ≈ 57.7 rad/s` |
| damping (Kd) | 3.0 | damping ratio ≈ 0.7 (near-critical) |
| `effort_limit_sim` | 13.0 Nm | PhysX hard cap, `arm_torque` constraint가 쓰는 9.5 Nm 모터 stall보다 위 |
| `velocity_limit_sim` | 3.1 rad/s | 측정된 XW540-T260 no-load plateau(2026-07-06), PhysX hard cap |

**혼동하기 쉬운 두 개의 arm 경계.** 13.0 Nm / 3.1 rad/s 수치는 액추에이터의
**PhysX hard cap**이다. constraint 항 `arm_torque`(`limit_nm=9.5`)와
`arm_joint_vel`(`limit_rad_per_s=2.8`)은 *측정된* torque/velocity 위의 **soft cost
budget**이다 — penalize할 뿐, clip하지 않는다. 정책은 constraint cost를 물면서
2.8 rad/s를 넘어 3.1 rad/s 물리 cap까지 갈 수 있다. constraint 제한을 물리 제한과
동일시하지 말 것.

**Kp=100/Kd=3 근거는 이론 계산이지 실기 측정이 아니다.** `albc.py:198-201` 주석
기준: Kp=100 → `J ≈ 0.15 kg·m²` 가정 하 `ω_n ≈ 57.7 rad/s`, Kd=3 → damping ratio
≈ 0.7(near-critical) — 둘 다 2차 시스템 이론식에서 역산한 값이며 모터 모델명은
이 파일에 없다. 실제 하드웨어는 Dynamixel XM430-W350(내부 ~1kHz PID)이고,
sim gain을 Dynamixel gain으로 매핑하는 코드/수치는 없다 — register 값이 SI 단위가
아니라 모델별 변환이 필요해 직접 매핑이 불가능하며, 대신 step-response
system-identification이 필요하다(`sim-to-real.md:230-231`, 아직 미측정 TODO).
discrete PID(1kHz, integer register, PWM saturation, firmware filter) vs continuous
PhysX `ImplicitActuator` PD는 **구조적** 격차라 DR로 메울 수 없다 — gain DR은
*값*을 무작위화할 뿐 *컨트롤러 형태*는 바꾸지 못한다.

DR은 reset마다 env별로 joint gain/effort/friction을 랜덤화한다
(`config.py:126-131, 183-184`; `randomize_joint_gains`, `mdp/events.py:457-469`);
joint fault는 effort limit을 env별 health로 스케일한다(`faults.apply_joint_health`,
`faults.py:80`). **gain DR은 중심값을 스케일하는 게 아니라 절대 범위를 직접
샘플링**한다 — nominal 100/3은 DR-off일 때의 값일 뿐, 스케일 중심이 아니다.
기본 범위: stiffness `[40, 120]`, damping `[0.5, 5.0]`; hard(encoder 훈련) 범위:
stiffness `[30, 150]`, damping `[0.3, 7.0]`. effort_limit은 스케일 `[0.7, 1.0]`
(`config.py:129`). reset 시에만 적용되고 step마다 갱신되지 않으며, DORAEMON
curriculum 파라미터가 아니라 고정 범위다.

---

## 5. Thruster 경로 — 필터 → curve → coefficient → TAM

thruster 차원 `self._actions[:, 2:]`는 marinelab `ThrusterModel`
(`marinelab/core/thruster.py`)로 간다. env는 `_pre_physics_step`에서 매 physics step
필터를 전진시키고(`albc_env.py:562-563`):

```python
if self._thruster is not None:
    self._thruster.apply_dynamics(self._actions[:, 2:], self.physics_dt)
```

`_apply_action`(`:806`)에서 결과 wrench를 읽어 hydrodynamic force에 더한 뒤 body에
쓴다.

### 5.1 1차 필터 (비대칭 time constant)

`apply_dynamics`(`thruster.py:97`)는 명령을 `[-1, 1]`로 clamp하고(§3.2와 독립인
thruster *자체*의 clamp), **방향 의존** time constant로 1차 lag를 돌린다 — spin-up이
spin-down보다 느리다:

```python
target_state = commands.clamp(-1.0, 1.0)
tau   = torch.where(target_state > self._state, tau_up, tau_down)   # 0.1 up / 0.05 down
alpha = dt / tau
self._state = self._state + alpha * (target_state - self._state)
```

`self._state ∈ [-1, 1]`은 정규화된 필터링 명령 — ESC-lag 모델이다. DR에서
`tau_up/tau_down`과 `thrust_coeff`는 env별이다(`config.py:140-141`;
`randomize_parameters`, `thruster.py:175`).

### 5.2 명령 shaping → 힘 → clamp → TAM

`compute_wrench`(`thruster.py:134`)는 필터링된 state를 body wrench로 바꾼다:

```python
command          = self._thrust_command()                 # identity, or thrust curve (§5.3)
thrust_magnitude = command * thrust_coeff                 # per-env if DR, else 40.0
thrust_magnitude = thrust_magnitude.clamp(-max_thrust, max_thrust)   # +-50 N
[thrust_magnitude = thrust_magnitude * health]            # fault path, marinelab main only (§5.4)
body_wrench      = einsum("ij,nj->ni", allocation_matrix, thrust_magnitude)  # 6x6 TAM
forces  = body_wrench[:, :3]
torques = body_wrench[:, 3:]
```

6×6 allocation matrix(`config.py:90-97`)는 6개 per-thruster force를 body-frame 6-DOF
wrench로 매핑한다:

| Row | DOF | T0 | T1 | T2 | T3 | T4 | T5 | 배치 |
|---|---|---|---|---|---|---|---|---|
| Fx | surge | 0.707 | -0.707 | 0.707 | -0.707 | 0 | 0 | 수평 4개 (45° vectored) |
| Fy | sway | -0.707 | -0.707 | 0.707 | 0.707 | 0 | 0 | " |
| Fz | heave | 0 | 0 | 0 | 0 | 1 | 1 | 수직 2개 |
| Mx | roll | 0.007 | 0.007 | -0.007 | -0.007 | 0 | 0 | 작은 arm |
| My | pitch | 0.007 | -0.007 | 0.007 | -0.007 | 0.145 | -0.145 | 수직 쌍이 지배 |
| Mz | yaw | 0.144 | 0.144 | 0.144 | 0.144 | 0 | 0 | 수평 4개 |

roll arm이 아주 작아(0.007 m) 큰 payload CoG offset이 roll TAM 권한을 초과할 수
있는 이유가 이것이다 — HardDR의 `payload_cog_offset_xy_radius`가 정확히 이 이유로
0.15→0.08로 축소됐다(`config.py:174-180`): roll 권한
`4 × 50 N × 0.007 m = 1.4 Nm` vs. 0.15 m의 3 kg payload가 만드는 ~4.5 Nm.

### 5.3 선택적 비선형 thrust curve (`exp/thruster-curve`, 기본 off, `main`에는 없음)

`_thrust_command`(`thruster.py:122`)는 `cfg.enable_thrust_curve`가 False이면
identity다 — 기본값이자 `main` 브랜치 거동이라, `compute_wrench`가 선형 모델과
byte-identical이다. 활성화하면(`exp/thruster-curve` 브랜치에만 존재) **정규화 명령
공간에서** BlueROV T200 fidelity 모델을 적용한다:

- **Deadband**: `|state| < thrust_deadband (0.075)` → 0, T200 ESC의 중립 부근 PWM
  deadzone을 모델링.
- **Signed-square**: deadband 밖에서 `sign(state) * state²`, 2차 프로펠러 법칙
  (thrust ∝ ω², ω ∝ command)에 대응.

출력은 `[-1, 1]`에 머물러 하류 `* thrust_coeff` 범위는 불변이다. 이는 DR이 흉내낼
수 없는 구조적 비선형이다(곱셈 스케일은 zero-region이나 quadratic 형태를 만들 수
없음) — sim-to-real audit 참조. baseline 거동이 아니라 기본 off 토글이다
(`getattr` 폴백 → byte-identical).

### 5.4 선택적 per-thruster fault (marinelab `main`에 병합됨, 기본 off)

marinelab `main`에서 `ThrusterModel.__init__`은 `enable_fault`를 받는다
(`thruster.py:41`). True이면 env별 per-thruster health 버퍼 `∈ [0, 1]`를 할당하고
(`:83-84`), `compute_wrench`가 ±50 N clamp **전에** *unsaturated* magnitude에 health를
곱한다(`:148-149`) — degrade된 thruster가 peak force를 낮게 갖도록. `set_thruster_health`
(`:168`)가 주입하고, env는 `faults.sample_thruster_health`(`faults.py:27`)로 샘플해
reset 시 밀어 넣는다. `enable_fault`가 False이면 버퍼를 할당하지 않고 곱을 건너뛴다
(byte-identical). fault는 기본 off다(`FaultInjectionCfg.enable=False`,
`config.py:266`); FTC 연구 인프라로, DR과 구분된다(fault = 컴포넌트 *고장*, DR =
valid-but-different 차량).

> **Working-tree 주의 (해소됨).** `exp/thruster-curve` 브랜치(§5.3)는 원래 fault
> 커밋 이전에 분기돼 그 `thruster.py`에 `enable_fault` 파라미터가 없었고, `main`의
> `config.py:432` `FaultInjectionCfg` / `_init_thrusters`의 `enable_fault=...`
> (`albc_env.py:357`)가 생성자에서 거부되는 발산이 있었다. marinelab 커밋
> `0ed193e`(unpushed)에서 fault를 `exp/thruster-curve`에도 병합해 해소했다 — 그
> 브랜치는 이제 curve와 fault를 둘 다 가지며, 적용 순서는 curve → coeff → health →
> clamp다. `main`은 여전히 fault만 있고 curve는 없다(§5.3).

---

## 6. Observation으로의 action 되먹임

action은 네트워크를 떠나기만 하는 게 아니라 다음 observation으로 두 방식으로
되돌아온다(둘 다 69D `o_t`의 일부):

1. **필터링된 thruster state (6D)** — current proprioception 안. `compute_policy_obs`
   (`mdp/observations.py:68`)는 `env._thruster.state`를 읽는다 — *필터링된* 1차 state
   (§5.1)로, *"6D: filtered thruster output"*(`:82`)로 라벨돼 있고 raw 명령이
   **아니다**. 실기가 보고할 ESC feedback을 흉내낸다.
2. **전체 8D action 이력 (16D)** — temporal history 안. `_get_hist_features`
   (`albc_env.py:486-495`)가 `self._prev_actions`(현재 state를 만든 8D action)를 ring
   버퍼에 기록하고; `_get_observations`가 최신 `hist_action_len=2` step을 슬라이스한다
   → `8 × 2 = 16D`(`:975`).

그래서 정책은 자기 최근 action에 대해 부분적으로 closed-loop다. 전체 69D 구성은
`main-network-architecture.ko.md` §2.1에 표로 있다; 여기서는 *어느 부분이
action-derived인가*만이 요점이다.

---

## 7. 어디서 무엇을 바꾸나 (action knob map)

| Knob | 값 | 위치 (file:line) |
|---|---|---|
| action_space | 8 (2 arm + 6 thruster) | `config.py:303` |
| delta_scale (arm step당) | 0.10 | `config.py:360` |
| nominal_joint_pos (arm init target) | (0.0, π/2) | `config.py:359` |
| arm actuator Kp / Kd | 100.0 / 3.0 | `marinelab/assets/albc/albc.py:196-202` |
| arm effort / velocity cap (PhysX) | 13.0 Nm / 3.1 rad/s | `albc.py:196-202` |
| thruster count / max_thrust | 6 / 50.0 N | `config.py:85-86` |
| thrust_coefficient | 40.0 | `config.py:87` |
| time_constant_up / down | 0.1 / 0.05 | `config.py:88-89` |
| allocation matrix (6×6 TAM) | §5.2 참조 | `config.py:90-97` |
| `clip_actions` (vecenv clamp) | `agent_cfg.clip_actions` | `scripts/train.py:292`, `vecenv_wrapper.py:151` |
| env action clamp | `[-1, 1]` (항상) | `albc_env.py:452` |
| thruster command clamp | `[-1, 1]` (항상) | `thruster.py:108` |
| `enable_thrust_curve` / `thrust_deadband` | False / 0.075 (`exp/thruster-curve`) | `marinelab/assets/uuv_cfg.py:143,148` |
| `enable_fault` / thruster_health | False (`main`) | `config.py:266`; `thruster.py:41,149` |
| control_decimation (arm PD rate) | 1 | `config.py:357` |
| thruster/joint DR scales | cfg 참조 | `config.py:126-131,140-141,183-187` |

---

## 8. 참고·표준성·한계

- **`[-1, 1]` 경계는 squash가 아니라 해석이다.** PPO/TRPO의 표준: 네트워크는 raw
  Gaussian mean을 내보내고 환경이 범위를 해석한다(여기서는 `clamp`로). SAC식
  tanh-squashing(log-prob Jacobian 보정 포함)은 *쓰지 않으며*, 썼다면 다른
  알고리즘이 된다. MLP 마지막 층은 linear(`last_activation=None`); `act()` clamp
  없음. (`main-network-architecture.ko.md` §9와 동일 결론.)
- **두 clamp는 버그가 아니라 설계상 중복이다.** clamp #1(vecenv, 선택)과
  clamp #2(env 버퍼, 항상) 모두 `[-1, 1]`을 겨냥한다; env clamp가 정본이고, wrapper
  clamp는 `clip_actions is None`일 때 no-op인 라이브러리 레벨 가드다.
- **arm target 적분기는 의도적으로 unbounded다.** `[-π, π]` wrap도, joint limit
  clamp도 없다 — joint가 연속 회전이고, drift는 clamp가 아니라 *constraint* 문제다
  (`joint1_position_cost`, `cumulative_yaw_cost`). 버그로 보고 clamp를 추가하면 제어
  권한을 조용히 바꾼다.
- **thruster fault는 `main`에 병합됐고 thrust curve는 아직 별도 브랜치다**
  (§5.3-5.4). `main` = fault 있음 + curve 없음. `exp/thruster-curve`는 이제 fault도
  병합해(marinelab `0ed193e`) curve와 fault를 **둘 다** 가진다 — 더 이상 상호
  배타적이지 않다. 이 문서의 기본 서술은 marinelab `main`이다.
- 정적 코드 구조 레퍼런스다. 정책이 실제로 전체 action 범위를 *쓰는지*, 특정 기동에
  thruster 필터 lag가 중요한지는 이 문서가 아니라 eval/분석의 런타임 dynamics
  질문이다.

---

## 소스 파일

- `constrained_albc/envs/main/encoder/actor_critic_encoder.py` — `act()` / `act_inference()` (clamp 없음), actor obs 조립
- `constrained_albc/envs/main/encoder/_policy_base.py` — global `log_std`, Gaussian `_update_distribution`
- `constrained_albc/envs/main/albc_env.py` — `_update_action_buffers` (clamp #2), `_apply_joint_pd_action` (delta 적분기), `_apply_action` (PD + wrench), `_get_hist_features` (action 이력), `_pre_physics_step` (dispatch)
- `constrained_albc/envs/main/config.py` — `action_space`, `delta_scale`, `ALBCThrusterCfg` (TAM, coeff, tau), `FaultInjectionCfg`
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` (필터링된 thruster_state 되먹임)
- `constrained_albc/envs/main/mdp/faults.py` — `sample_thruster_health`, `apply_joint_health`
- `marinelab/core/thruster.py` — `apply_dynamics` (1차 필터), `_thrust_command` (curve), `compute_wrench` (coeff, clamp, health, TAM). 참고: `albc_env.py:350`은 deprecated `marinelab.physics` shim으로 import하며, 이는 `marinelab.core`를 re-export한다; 실제 소스는 `core/`다.
- `marinelab/assets/albc/albc.py` — arm joint용 `ImplicitActuatorCfg`
- `isaaclab/source/isaaclab_rl/isaaclab_rl/rsl_rl/vecenv_wrapper.py` — `clip_actions` (clamp #1)
