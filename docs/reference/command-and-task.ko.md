# Command와 Task 정의 (`envs/main`)

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 command(목표) 쪽 — 정책이 무엇을 추종하도록
> 요구받는지, command가 어떻게 샘플되고 episode 중간에 리샘플되는지, command가
> observation에 어떻게 들어가 tracking error를 만드는지, 그리고 tracking reward가
> 그 error를 어떻게 소비하는지. 이건 **attitude-only** 태스크다: roll/pitch attitude
> + yaw-rate, **linear-velocity command 없음**(실기에 DVL 없음).
>
> 디스크에 대해 검증된 code-level 레퍼런스다. `action-pipeline.ko.md`(정책이
> *출력*하는 것)와 `exploration-and-noise.ko.md`(정책이 *탐색*하는 법)를 보완한다 —
> 이 문서는 **입력/목표 축**이다: 정책이 달성하려는 것. 전체 69D observation 분해는
> `main-network-architecture.ko.md` §2.1에 있고; 여기서는 command-derived 부분만
> 다룬다.

---

## 1. 개요

command는 3D 벡터 `_ang_cmd = [roll_att, pitch_att, yaw_rate]`다. env별로 샘플되고,
고정 window 동안 유지되고, episode 중간에 리샘플되고, 가끔 hover로 0이 된다.
observation에 noise-free로 들어가고(센서가 아니라 우리 자신의 양), tracking error와
leaky integral을 구동하고, 지수 tracking reward를 먹인다.

```
SAMPLE  (_sample_velocity_command, per env, every 250 steps)
  roll/pitch ~ U(-1,1) * (pi/6 * cmd_att_scale)      # +-30 deg,  cmd_att_scale = 1.0
  yaw_rate   ~ U(-1,1) * (0.5  * cmd_yaw_scale)       # +-0.5 rad/s, cmd_yaw_scale = 1.0
  with prob 0.1:  _ang_cmd = 0                        # hover / station-keeping
  play_mode:      _ang_cmd = 0 always                # eval = hovering

STORE   _ang_cmd (N, 3): [0:2] roll/pitch attitude (rad), [2] yaw rate (rad/s)

OBSERVE _ang_cmd is the first 3D of the 20D proprioception (obs noise std = 0.0)

ERROR   att_rp_err = wrap(_ang_cmd[:,:2] - (roll,pitch))     # atan2(sin,cos)
        yaw_rate_err = _ang_cmd[:,2] - measured_yaw_rate
        -> leaky integral (3D: roll, pitch, yaw_rate)

REWARD  exp-kernel tracking on att_rp_err (k=9.0) + yaw_rate_err (k=3.5)
```

**먼저 짚을 중요한 비자명 사실 하나(§6): command curriculum은 스캐폴딩만 있고
비활성이다.** env별 `cmd_*_scale` 계수가 존재해 command range를 곱하지만, 아무도
그것을 쓰지 않는다 — 전체 run 동안 `1.0`에 머문다. DORAEMON은 *물리*를 randomize하지
command 난이도가 아니다. command 난이도는 고정 config knob이지 curriculum이 아니다.

---

## 2. Command space

`ALBCEnvCfg`에서(`config.py`):

| Command | cfg field | 범위 | 의미 | 위치 |
|---|---|---|---|---|
| roll/pitch attitude | `att_cmd_rp_range` | (-π/6, π/6) = ±30° | 절대 roll & pitch attitude 목표 (rad) | `config.py:377` |
| yaw rate | `yaw_rate_cmd_range` | (-0.5, 0.5) | body-frame yaw 각속도 목표 (rad/s) | `config.py:379` |

**혼합 command 타입**에 주목: roll/pitch는 *attitude*(위치) 목표인 반면 yaw는
*rate*(속도) 목표다. yaw *attitude* command도, linear-velocity command도 전혀 없다.
타이밍/제로화 knob:

| cfg field | 값 | 의미 | 위치 |
|---|---|---|---|
| `vel_cmd_resample_steps` | 250 | 250 control step마다 리샘플 = 50 Hz에서 5 s | `config.py:381` |
| `vel_cmd_zero_prob` | 0.1 | 리샘플이 zero(hover) command를 낼 env별 확률 | `config.py:383` |
| `play_mode` | False | eval 모드: 모든 command를 0(hover)으로 고정, 리샘플 없음 | `config.py:386` |

`vel_cmd_*` 이름은 legacy다(한때 linear-velocity command를 구동했음); 지금은 공유
command-타이밍/제로화 knob으로만 남아있고 더는 linear velocity를 만들지 않는다.
`_sample_velocity_command`의 docstring이 이를 명시적으로 기록한다.

---

## 3. 샘플링 — `_sample_velocity_command`

`albc_env.py:610-643`. `[-1, 1]`에서 균등, range와 (항상-1.0인) env별 scale로 스케일:

```python
att_max = abs(self.cfg.att_cmd_rp_range[1])          # pi/6
yaw_max = abs(self.cfg.yaw_rate_cmd_range[1])         # 0.5
att_s = self._cmd_att_scale[env_ids].unsqueeze(1)     # 1.0
yaw_s = self._cmd_yaw_scale[env_ids]                  # 1.0
self._ang_cmd[env_ids, :2] = torch.empty(n, 2, ...).uniform_(-1, 1) * (att_max * att_s)
self._ang_cmd[env_ids, 2]  = torch.empty(n, ...).uniform_(-1, 1) * (yaw_max * yaw_s)
```

그다음 env별 zero mask가 일부 env를 hover로 override한다:

```python
zero_mask = torch.rand(n, ...) < self.cfg.vel_cmd_zero_prob   # 0.1
if zero_mask.any():
    self._ang_cmd[env_ids[zero_mask]] = 0.0
self._vel_cmd_step_counter[env_ids] = 0
```

**zero command를 얻는 두 경로:** 10% `vel_cmd_zero_prob` mask(학습, station-keeping을
가르침)와 `play_mode` early-return(eval, *모든* command 0이라 evaluation이 순수
hover). play-mode 분기(`:622-625`)는 샘플링 전에 return한다:

```python
if self.cfg.play_mode:
    self._ang_cmd[env_ids] = 0.0
    self._vel_cmd_step_counter[env_ids] = 0
    return
```

그래서 eval(`play.py`, `eval.py`)은 command-following이 아니라 hover /
station-keeping 성능을 측정한다 — eval plot을 읽을 때 기억할 사실이다.

---

## 4. Command 버퍼와 episode-중간 리샘플

### 4.1 버퍼

`_ang_cmd`는 `(num_envs, 3)`, 0으로 초기화(`albc_env.py:303-304`):

```python
# [0:2] = roll/pitch attitude (rad), [2] = yaw rate (rad/s)
self._ang_cmd = torch.zeros(self.num_envs, 3, device=self.device)
```

slot 의미는 고정: `[0]` roll attitude, `[1]` pitch attitude, `[2]` yaw rate. 같은
3-channel 레이아웃이 error 버퍼 `_ang_err`, integral `_error_integral`, reward
sigma에 미러링된다 — 세 "channel" 모두 전 구간 [roll, pitch, yaw_rate]다.

### 4.2 리샘플 트리거

`_pre_physics_step`에서(`albc_env.py:527-534`), env별 카운터가 리샘플을 구동한다:

```python
self._vel_cmd_step_counter += 1
resample_steps = self._vel_cmd_resample_steps           # 250
if resample_steps > 0:
    resample_mask = self._vel_cmd_step_counter >= resample_steps
    if resample_mask.any():
        self._sample_velocity_command(resample_mask.nonzero(as_tuple=True)[0])
```

각 env는 자기 카운터가 250에 닿으면 독립적으로 리샘플한다(카운터는 각 샘플에서 0으로
리셋되고, reset에서도 episode-length jitter와 함께 리셋돼 env들이 desync). 그래서 한
3000-step episode 안에서 env는 대략 5 s마다 새 command를 본다 — 정책은 고정 target이
아니라 *변하는 target을 추종*해야 한다.

---

## 5. Observation 속의 command와 tracking error

### 5.1 Observation 안 (noise-free)

`compute_policy_obs`(`mdp/observations.py`)는 `_ang_cmd`를 20D proprioception의
**첫 3D**로 넣는다(`:71-73`):

```python
return torch.cat([
    env._ang_cmd,                              # 3D: [roll_att_cmd, pitch_att_cmd, yaw_rate_cmd]
    torch.stack([roll, pitch, yaw], dim=-1),   # 3D: euler
    ...
```

command는 observation noise model에서 **noise-free**다: `_OBS_NOISE_STD`
(`config.py:206`, `# ang_cmd ... (our command, no noise)`)의 첫 3 dim과 bias 모델이
`0.0`이다. 의도적이다 — command는 센서 읽기가 아니라 우리 자신의 set-point라 센서
noise를 갖지 않는다. (이건 `exploration-and-noise.ko.md` §7이 observation noise 전반에
대해 긋는 것과 같은 구분이다.)

### 5.2 Tracking error

`_compute_ang_errors`(`albc_env.py:1000-1007`)가 command 빼기 측정 상태를 reward와
integral이 쓰는 error로 바꾼다:

```python
roll, pitch, _ = self._euler_cache
raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
self._att_rp_err = torch.atan2(torch.sin(raw), torch.cos(raw))          # wrapped to [-pi, pi]
self._yaw_rate_err = self._ang_cmd[:, 2] - self._robot.data.root_ang_vel_b[:, 2]
self._ang_err[:, :2] = self._att_rp_err
self._ang_err[:, 2]  = self._yaw_rate_err
```

- **attitude error는 angle-wrap된다**(`atan2(sin, cos)`) — command가 ±π 근처이고
  상태가 wrap 반대편이면 spurious ~2π가 아니라 short-way error를 준다.
- **yaw error는 단순 rate 차이**다(wrap 없음 — 각도가 아니라 속도).

### 5.3 Leaky integral

3개 command channel은 leaky integrator도 먹인다(`_get_rewards`,
`albc_env.py:1018-1038`): `I ← integral_leak · I + gate · err · dt`, `±integral_clamp`로
clamp, 같은 3 channel `[roll, pitch, yaw_rate]`. error-gated이고(`|err| < reward
sigma`일 때만 누적) 69D observation에 trailing 3D로 append된다. 목적(Hwangbo-2017
패턴)은 per-step tracking reward가 무시하는 *지속적* offset의 기억을 정책에 주는
것이다. integral cfg(`integral_leak=0.99`, `integral_clamp=2.0`, `integral_gated=True`)는
`config.py:310-314`에 있다.

---

## 6. Command "curriculum" — 스캐폴딩만 있고 비활성

env별 command-range scale은 1.0으로 초기화된다(`albc_env.py:319-321`):

```python
# Per-env command range scales (DORAEMON-managed, default 1.0 if disabled)
self._cmd_lin_scale = torch.ones(self.num_envs, device=self.device)
self._cmd_att_scale = torch.ones(self.num_envs, device=self.device)
self._cmd_yaw_scale = torch.ones(self.num_envs, device=self.device)
```

`_sample_velocity_command`(§3)에서 command range의 곱수로 읽힌다. **그러나 아무도
쓰지 않는다** — `_reset_physics`의 코드 주석(`albc_env.py:1368-1369`)이 대놓고
말한다:

```python
# Command scales fixed at 1.0 (not DORAEMON-managed).
# DORAEMON optimizes physics DR only; command difficulty is a task knob.
```

그래서 "DORAEMON-managed" init 주석에도 불구하고, **command 난이도는 curriculum으로
스케일되지 않는다**. DORAEMON의 Beta-분포 curriculum은 *물리* 파라미터(hydrodynamics,
payload, ocean current, actuator gain — `config.py` DR와 `doraemon.py` 참조)에
작용하지 command range에는 작용하지 않는다. command range는 **고정 config
knob**(`att_cmd_rp_range`, `yaw_rate_cmd_range`)이다; command를 어렵게 하려면 그
tuple을 편집하지 curriculum을 켜는 게 아니다. `cmd_*_scale` 버퍼는 구현되지 않은
command curriculum을 위한 dormant 스캐폴딩이다.

> 이건 분석 규칙이 경고하는 "name vs. implementation" gap의 전형이다:
> `_cmd_*_scale` 이름과 "DORAEMON-managed" 주석은 live command curriculum을 시사하지만,
> 구현은 상수 1.0을 보여준다. command 난이도를 adaptive라고 서술하지 말 것.

---

## 7. Tracking reward (command error를 어떻게 채점하나)

command error는 공유 지수-이차 kernel `_exp_quad_saturating`
(`mdp/rewards.py:97-117`)을 통해 tracking reward를 구동한다:
`exp(-e²/2σ²) - quad·e² - lin·|e| - (saturating)`.

| 항 | 소비 | cfg (k, σ) | 위치 |
|---|---|---|---|
| `att_rp_tracking` | `_att_rp_err` (roll,pitch), roll-weighted | k=9.0, σ=0.10, quad_ratio=0.833, `att_roll_weight=1.5` | `rewards.py:70,128-138` |
| `yaw_vel_tracking` | `_yaw_rate_err` | k=3.5, σ=0.10, quad_ratio=1.0, tanh_coef=0.3 | `config.py:390`, `rewards.py:141-144` |

roll은 attitude error 안에서 up-weight된다(`att_roll_weight=1.5`) — roll의 TAM
actuation이 약하기 때문(0.007 m roll arm vs 0.145 m pitch arm — `action-pipeline.ko.md`
§5.2 참조), 그래서 roll error를 더 세게 penalize해 보상한다. reward kernel 기구 자체는
별도의 reward-문서 주제다; 여기서는 command error(§5.2)가 이 항들이 소비하는 것이라는
점만이 요점이다 — command → error → reward 루프를 닫는다.

---

## 8. Knob map

| Knob | 값 | 위치 |
|---|---|---|
| `att_cmd_rp_range` | (-π/6, π/6) = ±30° | `config.py:377` |
| `yaw_rate_cmd_range` | (-0.5, 0.5) rad/s | `config.py:379` |
| `vel_cmd_resample_steps` | 250 (5 s @ 50 Hz) | `config.py:381` |
| `vel_cmd_zero_prob` | 0.1 | `config.py:383` |
| `play_mode` (eval = hover) | False | `config.py:386` |
| command 버퍼 `_ang_cmd` | (N, 3) [roll, pitch, yaw_rate] | `albc_env.py:304` |
| `cmd_*_scale` (비활성, 항상 1.0) | 1.0 | `albc_env.py:319-321`, `1368-1369` |
| command in obs (첫 3D, noise-free) | — | `observations.py:71-73`, `config.py:206` |
| error compute (attitude wrapped) | — | `albc_env.py:1000-1007` |
| integral (3 channel, gated leaky) | leak 0.99 / clamp 2.0 | `config.py:310-314`, `albc_env.py:1018-1038` |
| att / yaw tracking reward (k, σ) | 9.0 / 3.5, 0.10 | `rewards.py:70`, `config.py:390` |

---

## 9. 참고와 한계

- **Eval은 hover지 command-following이 아니다.** `play_mode=True`가 모든 command를
  0으로 만들어, eval은 moving set-point 추종이 아니라 DR/외란 하의 station-keeping을
  측정한다. eval plot을 그 전제로 읽을 것.
- **혼합 command 의미.** roll/pitch는 attitude(위치) 목표; yaw는 rate 목표. yaw-attitude
  command도 linear-velocity command도 없다. privileged critic은 측정 linear velocity를
  여전히 본다(`main-network-architecture.ko.md` §2.2)지만, actor는 linear command를 받지
  않는다.
- **Command curriculum은 구현되지 않았다(§6).** `cmd_*_scale` 스캐폴딩은 inert이고;
  command 난이도는 config range로 고정이다. adaptive/curriculum-scaled로 보고하지 말 것.
- 정적 코드 구조 레퍼런스다. 샘플된 command 분포가 특정 run에서 실제로 잘 추종되는지는
  런타임/eval 질문이다.

---

## 소스 파일

- `constrained_albc/envs/main/config.py` — command range, resample/zero/play knob, integral cfg, `_OBS_NOISE_STD` (command dim = 0)
- `constrained_albc/envs/main/albc_env.py` — `_sample_velocity_command`(`:610`), `_ang_cmd` 버퍼(`:304`), 리샘플 트리거(`:527`), `_compute_ang_errors`(`:1000`), integral update(`:1018`), `cmd_*_scale` init + 비활성 주석(`:319`, `:1368`)
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` (command를 첫 3D로)
- `constrained_albc/envs/main/mdp/rewards.py` — `att_rp_tracking` / `yaw_vel_tracking`, `_exp_quad_saturating` kernel
