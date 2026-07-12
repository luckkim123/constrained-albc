# Observation Space (`envs/main`): obs / privileged / proprioception history

> **범위**: 기본 태스크 `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`)의 observation(입력) 쪽 — 69D 전체 정책
> observation `o_t`, 28D privileged observation `p_t`, `o_t` 중간을 채우는 strided
> proprioception history, 그리고 encoder / actor / critic이 이 텐서들을 비대칭적으로
> 소비하는 방식. 이것은 **attitude-only** 태스크다: roll/pitch attitude + yaw-rate이며,
> actor observation에는 **측정된 선속도가 없다**(실제 로봇에 DVL 없음). 측정된 선속도는
> privileged critic 입력에만 존재한다.
>
> 디스크에 대해 검증된 code-level 레퍼런스다. 이것은 **observation 축**으로,
> `action-pipeline.md`(정책이 무엇을 *출력*하는가), `command-and-task.md`(목표/입력 축 —
> command가 obs에 들어와 tracking error를 만드는 방식), `main-network-architecture.md`
> §2.1(전체 encoder / actor / critic 층 구조)을 보완한다. 어떤 주제(command 샘플링,
> action clamp, net 층 크기, ConstraintTRPO 업데이트)가 그 문서들에 속하면, 여기서는
> 반복하지 않고 링크로 넘긴다.

---

## 1. 개요

env는 step마다 두 개의 키를 가진 observation dict를 내보낸다:
`{"policy": o_t (69D), "privileged": p_t (28D)}`
(`albc_env.py:969-998`; `privileged`는 `state_space > 0`일 때만 존재,
`albc_env.py:996-997`, `state_space=28`은 `config.py:341`).

`o_t`는 실제 로봇이 측정 가능한 모든 것으로, step마다 한 번 `_get_observations`
(`albc_env.py:969-982`)에서 세 개의 concat된 sub-block으로 조립된다: 20D 현재
proprioception, 46D strided temporal history, 3D leaky-integrated error. `p_t`는 숨겨진
physics 카탈로그로, 독립적인 domain-randomization(DR) 파라미터당 스칼라 하나(25D) 더하기
실제 body-frame 선속도(3D)다. 이 둘은 세 소비자에게 비대칭적으로 공급된다: encoder는
`p_t`**만** 9D latent `z`로 압축하고, actor는 `o_t + z`를 본다(raw `p_t`는 절대 보지
않음). train-only critic은 `o_t + z + p_t`를 본다.

```
ENV emits  {"policy": o_t (69D), "privileged": p_t (28D)}      # albc_env.py:991,997

  o_t (69D) = proprio(20) + history(46) + integral(3)          # albc_env.py:969-982
  p_t (28D) = DR-backed(25) + measured body lin_vel(3)         # observations.py:88-161

ENCODER   p_t(28) --minmax--> MLP[256,128,64] elu -> LayerNorm -> softsign -> z(9)
                                                                # actor_critic_encoder.py:206-217

ACTOR     cat[ EmpiricalNorm(o_t)(69) , z(9) ] = 78 -> MLP -> action(8)
                                                                # actor_critic_encoder.py:246-256, 175,182
              (never receives raw p_t — asymmetry point)

CRITIC    cat[ o_t(69) , z(9) , p_t(28) ] = 106 -> V(1)        # actor_critic_encoder.py:258-268
COST CRITIC same 106D input -> K heads (K=num_constraints=10)  # _policy_base.py:91
              (train-only; sees everything for low-variance value + gradient into z)
```

**핵심 산수** (각각 `file:line`으로 추적 가능):

- `o_t`: `20 + 46 + 3 = 69` — `PROPRIO_DIM(20) + (10*hist_len + 8*hist_action_len) + integral_dims(3)`, `hist_len=3`, `hist_action_len=2` (`config.py:398,404`)이므로 `20 + (30 + 16) + 3 = 69` (`config.py:337`; guard `albc_env.py:151-162`).
- history: `10*hist_len + 8*hist_action_len = 10*3 + 8*2 = 30 + 16 = 46` (`albc_env.py:973-975`).
- `p_t`: `25 DR-backed + 3 measured lin_vel = 28` — hydro 7 + dynamics 3 + payload 4 + actuator 4 + env 4 + buoy 2 + latency 1 = 25, 더하기 body lin_vel 3 = 28 (`config.py:341`; `rsl_rl_ppo_cfg.py:32-35,148`).
- actor input: `policy_obs_dim(69) + encoder_latent_dim(9) = 78` (`actor_critic_encoder.py:175`).
- critic input: `policy_obs_dim(69) + privileged_dim(28) += encoder_latent_dim(9) = 106`, `critic_uses_z=True`이기 때문 (`actor_critic_encoder.py:102-104`; `rsl_rl_ppo_cfg.py:163`).

---

## 2. Policy observation `o_t` (69D)

`o_t`는 asymmetric-actor 입력이다: 20D 현재 proprioception + 46D temporal history +
3D leaky integral. 의도적으로 DVL-free다 — 측정된 선속도, lin_vel command, lin_vel
tracking error 어느 것도 `o_t`에 나타나지 않으며, 측정된 body lin_vel은 `p_t`에만
존재한다(`observations.py:158`). 이로써 actor/critic 비대칭이 보존된다.

두 개의 독립적인 검사가 69를 신뢰할 수 있게 만든다: construction-time `ValueError`
guard(`albc_env.py:151-162`)는 `20 + 10*hist_len + 8*hist_action_len +
(integral_dims if use_integral_obs)`를 재계산하여 불일치 시 loud하게 실패하고(assert와
달리 `python -O`에서도 살아남음), 여기에 per-step runtime assert
`policy_obs.shape[-1] == observation_space`(`albc_env.py:992-995`)가 더해진다.

### 2.1 Current proprioception (20D, indices 0:20)

`compute_policy_obs`(`observations.py:70-85`)가 구성한다.

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 0:3 | ang_cmd (command) | 3 | Attitude command `[roll_att, pitch_att, yaw_rate_cmd]`. roll/pitch은 절대 attitude setpoint(rad, ±30°)이고, 3번째는 yaw-**rate** command(rad/s)다. lin-vel command 없음. | `env._ang_cmd` (`observations.py:73`); buffer `albc_env.py:304`, sampled `albc_env.py:635-636` | Noise-free: `_OBS_NOISE_STD[0:3]=0.0`, `_OBS_BIAS_MAG[0:3]=0` (`config.py:241,261`) — 우리가 명령한 양이다. |
| 3:6 | euler angles | 3 | body의 측정된 roll, pitch, yaw(rad), `root_quat_w`의 캐시된 euler에서. | `env._euler_cache`의 `stack([roll,pitch,yaw])` (`observations.py:65,75`) | Noisy: std 0.02 + bias 0.02 (`config.py:242,262`). |
| 6:9 | root_ang_vel_b | 3 | 측정된 body-frame 각속도 `(p,q,r)` rad/s. IMU 측정 가능; actor가 보는 **유일한** 측정 속도(DVL 없음). | `robot.data.root_ang_vel_b` (`observations.py:76`) | Noisy: std 0.04 + bias 0.03 (`config.py:243,263`). 선속도는 의도적으로 제외(`p_t`에만, `observations.py:158`). |
| 9:11 | joint_pos | 2 | Raw 누적 arm joint 각도(연속 회전 모터 2개, wrap 없음). | `robot.data.joint_pos[:, _albc_joint_ids]` (`observations.py:66,78`) | Noisy: std 0.02 + bias 0.02 (`config.py:244,264`). |
| 11:13 | joint_vel | 2 | 2개 ALBC joint의 joint 속도(rad/s). | `robot.data.joint_vel[:, _albc_joint_ids]` (`observations.py:67,79`) | Noisy: std 0.04 + bias 0.03 (`config.py:245,265`). |
| 13:14 | manipulability | 1 | Yoshikawa index `w`, [0,1]로 정규화(1=최대 dexterity, 0=singularity). `w=sqrt(|l1*l2*sin(theta2)|)/sqrt(l1*l2)`. | `env._manipulability` (`observations.py:80`); computed `albc_env.py:592-594` | Noise-free: std 0.0, bias 0 (`config.py:246,266`) — 계산된 kinematic 양. |
| 14:20 | thruster_state | 6 | 6개 ESC 채널 m0–m5의 필터링된 thruster 출력(1차 lag 액추에이터 state). | `env._thruster.state` (`observations.py:68,82`); None이면 zeros fallback | Noisy: std 0.02 + bias 0.01 (`config.py:247,267`). 채널 순서는 firmware-ESC이며 raw sim 순서가 아님(`config.py:86-91`). |

### 2.2 Temporal history (46D, indices 20:66)

per-step feature 전체와 비대칭 slice는 §3 참조. 요약:

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 20:50 | jb_hist (joint+body, all 3 steps) | 30 | per-step `[joint_pos_err(2), joint_vel(2), ang_err(3), euler(3)]` = 10D, `hist_len=3` strided step 전부에 대해 유지, oldest-first. | `_hist_buf[:, :, :10].reshape` (`albc_env.py:973`) | `= 10*hist_len = 30`. per-dim noise가 step마다 `([0.02]*2+[0.04]*2 + [0.04]*3+[0.02]*3)`을 반복(`config.py:249,251`). |
| 50:66 | act_hist (action, newest 2 steps) | 16 | 전체 8D action `[2D arm delta, 6D thruster]`, 가장 최근 `hist_action_len=2` step만 유지. 가장 오래된 step의 action은 버려짐. | `_hist_buf[:, -hist_action_len:, 10:].reshape` (`albc_env.py:975`) | `= 8*hist_action_len = 16`. Noise-free(`[0.0]*16`, `config.py:253,273`) — 우리 자신의 command. |

### 2.3 Error integral (3D, indices 66:69)

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 66:69 | error_integral | 3 | `[roll_err, pitch_err, yaw_rate_err]`의 leaky error-gated integral(Hwangbo-2017 integral-feedback 패턴). `I = leak*I + gate*err*step_dt`, `gate = (|err| < reward sigma)`, clamped `|I| <= 2.0`. | `env._error_integral` (`albc_env.py:981-982`); `_get_rewards`에서 갱신(`albc_env.py:1020,1033-1038`); buffer `albc_env.py:312` | Noise-free: `[0.0]*3` (`config.py:255,275`) — 계산됨. `use_integral_obs=True`(`config.py:343`)이기 때문에만 존재; `integral_dims=3, leak=0.99, clamp=2.0, gated=True` (`config.py:344-347`). flag가 False면 `o_t`는 66D가 됨. |

integral은 error-gated다: `|err|`가 reward tracking sigma보다 작을 때만
`err*dt`를 누적하고(gate 텐서는 `__init__`에서 `reward.att_rp.sigma` /
`reward.yaw_vel.sigma`로부터 미리 구성, `albc_env.py:164-175`), `0.99/step`으로
leak하며, windup-clamp되어 `|I| <= 2.0`(`albc_env.py:1038`)이다. 두 개의
angle-integral(roll, pitch)과 하나의 **rate**-integral(yaw rate)을 섞는다는 점에
주의.

### 2.4 Observation noise

Noise는 emit 시 항상 켜져 있는 `NoiseModelWithAdditiveBias`(`config.py:509-512`)와
fault-injection 경로 `faults.apply_sensor_noise`(`albc_env.py:987-989`)를 통해 69D
벡터 전체에 한 번 적용된다. `_OBS_NOISE_STD`와 `_OBS_BIAS_MAG`는 69-length
벡터(`config.py:239-278`)로, command(3), manipulability(1), 모든 action-history(16),
모든 integral(3) 항목이 `0.0`이다 — 이들은 계산되거나 명령된 것이지 센싱된 것이
아니므로 noise가 더해질 것이 없다. 측정된 euler / ang_vel / joint / thruster
채널(그리고 그 history 복사본)만 Gaussian std + uniform additive bias를 받는다.
fault injection이 비활성화되면 `apply_sensor_noise`는 identity(`faults.py:73-77`)이므로
벡터는 byte-identical하게 유지된다. 활성화되면 **동일한** 69D `_OBS_NOISE_STD` base를
스케일하므로 zero-noise 차원은 여전히 추가 noise를 0으로 받는다.

---

## 3. Temporal history (46D): per-step 18D feature vs reassembled 46D slice

history는 과거 controller/system state의 strided ring buffer다. 제어 step마다 env는
**18D** feature 벡터(`_get_hist_features`, `albc_env.py:455-495`)를 계산하고, 이를 깊이
`hist_len=3`의 ring buffer에 쓰되 `hist_stride=3`번째 제어 step마다만
쓰며(`_update_hist`, `albc_env.py:497-512`), emit 시 **46D**를 비대칭적으로
slice한다(`_get_observations`, `albc_env.py:971-976`).

### 3.1 Per-step 18D feature (`hist_feature_dim=18`)

`hist_feature_dim = 18 = joint(4) + body(6) + action(8)` (`config.py:398-405`).

| per-step index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 0:2 | joint_pos_error | 2 | 2개 arm joint에 대한 `q_des_{t-1} - q_actual_t`. `_get_hist_features`가 `_apply_joint_pd_action`보다 먼저 실행되므로 `_joint_pos_targets`는 여전히 `q_des_{t-1}`을 담고 있어 **이전** step의 PD target을 사용. 설계상 actuator-lag 신호. | `_joint_pos_targets - joint_pos[:, _albc_joint_ids]` (`albc_env.py:473-474,488`) | feature-time noise/normalization 없음. |
| 2:4 | joint_vel | 2 | step t에서 2개 arm joint의 joint 속도(raw rad/s). | `joint_vel[:, _albc_joint_ids]` (`albc_env.py:475,489`) | Raw 단위. |
| 4:6 | att_rp_err | 2 | Roll/pitch attitude command error(rad), `atan2(sin,cos)`으로 [-π,π]에 wrap. | `att_raw = _ang_cmd[:,:2] - stack([roll,pitch]); atan2(sin,cos)` (`albc_env.py:480-481`) | Wrapped angle; 3D ang_err의 채널 0–1. |
| 6:7 | yaw_rate_err | 1 | Yaw-**rate** command error(rad/s, body frame): 명령된 yaw rate에서 측정된 body-frame yaw 각속도를 뺀 값. Yaw는 rate-controlled이지 attitude-controlled가 아님. | `_ang_cmd[:,2] - root_ang_vel_b[:,2]` (`albc_env.py:483-484`) | `[4:7] = ang_err = [att_rp_err(2), yaw_rate_err(1)]`; lin_vel_err **없음**(attitude-only). |
| 7:10 | euler_rpy | 3 | 절대 body Euler 각도(roll, pitch, yaw), rad. | `euler_xyz_from_quat(root_quat_w)` (`albc_env.py:477,491`) | 절대 orientation state(error 아님). |
| 10:18 | prev_action | 8 | 현재 state를 만든 전체 action: 2D arm delta + 6D thruster(ESC m0–m5). `_prev_actions`(state t로 이어진 step에 적용된 action)를 사용. | `_prev_actions` (`albc_env.py:492`); set `albc_env.py:444-453`, clamped [-1,1] | 이 `[10:18]` sub-block만 newest-2-steps slice의 대상. |

### 3.2 Reassembled 46D slice (비대칭)

buffer는 `3 x 18 = 54`개의 숫자를 저장하지만, obs는 joint+body(`[0:10]`)를 **3 step
전부**(30D)에서 취하고 action(`[10:18]`)은 **가장 최근 2 step만**(16D)에서 취해 = 46이지
54가 아니다. 가장 오래된 step의 8D action은 조용히 버려진다(`albc_env.py:975`).
joint+body 응답 history는 전체 span에 걸쳐 유지할 가치가 있지만, 가장 최근 두 개의 제어
입력만 되먹여진다.

```
jb_hist  = _hist_buf[:, :, :10].reshape(N, -1)            # 10 * hist_len = 30  -> o_t[20:50]
act_hist = _hist_buf[:, -hist_action_len:, 10:].reshape() # 8  * hist_action_len = 16 -> o_t[50:66]
temporal_history = 10*hist_len + 8*hist_action_len = 30 + 16 = 46
```

`jb_hist` 메모리 레이아웃은 per-step interleaved(`joint4+body6`가 step마다, 3× 반복,
oldest-first)이며, `observations.py:22-24` docstring이 개념적으로 암시하는 "joint 12D
다음 body 18D" grouping이 **아니다** — 그 docstring은 총합을 서술하지 row-major flatten
순서를 서술하지 않는다.

### 3.3 Striding과 buffer 메커니즘

- **Strided recording**: `_update_hist`는 `hist_step_counter % hist_stride == 0`일 때만 쓰므로(`albc_env.py:506`), 저장된 3 step은 3 제어-step 간격이다. 유효 temporal span = `hist_len * hist_stride * step_dt = 3 * 3 * 0.02 = 0.18s`이지 3개 연속 50 Hz step이 아니다. `hist_stride`는 obs 벡터 자체에서는 보이지 않는 temporal-coverage knob다.
- **Shift-and-append**: `_hist_buf[ids,:-1] = _hist_buf[ids,1:]` 다음 `_hist_buf[ids,-1] = new_entry` (`albc_env.py:511-512`). Index -1은 항상 newest, index 0은 oldest — 그래서 `-hist_action_len:`이 newest action을 잡는다.
- **Per-env masking**: `% stride` 조건은 `record_mask`(`albc_env.py:506,510`)를 통해 환경별로 평가되므로, 서로 다른 env는 stride cycle의 서로 다른 phase에 있을 수 있다. 각 env의 buffer는 독립적으로 진행된다.
- **`hist_len == 0` 경로**: `_hist_buf`는 None(`albc_env.py:294-296`); `_update_hist`는 early-return하고 `_get_observations`는 history block 전체를 건너뛰므로, history는 정확히 0D를 기여하고 `o_t`는 proprio(+integral)가 된다.

---

## 4. Privileged observation `p_t` (28D)

`p_t`는 `state_space > 0`(`config.py:341` = 28)일 때마다 `compute_privileged_obs`
(`observations.py:88-161`)가 내보낸다. 이것은 의도적으로 **비중복(non-redundant)**
카탈로그다: dims 0–24는 정확히 독립 DR 파라미터당 스칼라 하나이며(docstring이 명시적으로
언급, `observations.py:93-94`), dims 25–27은 4번째 종류의 채널 — 실제 body-frame 선속도
`(u,v,w)`로, DR 파라미터가 **아니라** actor가 눈이 가려진 실제 측정값이다. 비중복은
설계상 의도다: encoder는 진짜로 28D → 9D를 압축해야 하며, 상관된 중복을 모델링하면 latent
용량을 낭비하게 된다. Union layout(2026-07-12): 옛 27D layout 대비 Ixx와 linear
damping roll이 제거됐고, buoy volume/mass 스칼라와 control-action delay가
추가됐다.

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 0 | body_volume | 1 | Main body 배제 체적(buoyancy driver). Base 0.009 m³. | `_hydro.volume` (`observations.py:137`) | Norm `scale(volume, volume_scale)` (`priv_obs_bounds.py:130`). DR. |
| 1:4 | body_CoG_xyz | 3 | Body center of gravity offset. Base `(0,0,-0.05)`; z non-zero. | `_hydro.center_of_gravity` (`observations.py:138`) | Norm `offset(...)` (`priv_obs_bounds.py:131-133`); z→[-0.09,-0.01]. DR. |
| 4:7 | body_CoB_xyz | 3 | Body center of buoyancy offset. Base `(0,0,0)`. CoG–CoB 분리가 restoring moment를 설정. | `_hydro.center_of_buoyancy` (`observations.py:139`) | Norm `offset(...)` (`priv_obs_bounds.py:134-136`). DR. |
| 7 | quad_damp_roll | 1 | 대표 quadratic damping, roll 축. Base 1.0. | `_hydro.quadratic_damping[:, 3:4]` (`observations.py:156`) | Roll만(index 3). `scale(...)` (`priv_obs_bounds.py:140`). DR. Ixx와 linear damping roll은 union layout(2026-07-12)에서 제거됨. |
| 8 | body_mass | 1 | Body dry mass. Base 9.18 kg. | `_hydro.body_mass` (`observations.py:157`) | `scale(...)` (`priv_obs_bounds.py:141`). payload_mass[10]와 구별됨. DR. |
| 9 | added_mass_surge | 1 | added-mass 행렬의 Surge(x) 대각. Base 8.0. | `_hydro.added_mass_matrix[:, 0, 0]` (`observations.py:158`) | Surge만(6×6의 `[0,0]`), raw DR upper 12.0 (`priv_obs_bounds.py:142`). DR. |
| 10 | payload_mass | 1 | End-effector payload mass. Base 0; DR은 [0,3] kg 샘플링. | `_payload_mass` (`observations.py:160`) | **Direct** range `[0,3]` (`priv_obs_bounds.py:144`). 옛 하드코딩 `[-0.1,2.2]`는 norm 버그(3→1.35>1). DR. |
| 11:14 | payload_CoG_offset_xyz | 3 | mount 기준 Payload CoG offset. xy는 radius에서, z는 direct. | `_payload_cog_offset` (`observations.py:161`) | x,y = `[-r,r]`, `r=0.08 m`(옛 0.17은 stale); z direct `[-0.05,0]` (`priv_obs_bounds.py:145-147`). DR. |
| 14 | joint_stiffness_Kp | 1 | Arm joint implicit-actuator stiffness(Kp). | `_robot.data.joint_stiffness[:, jid:jid+1]` (`observations.py:163`), `jid=_albc_joint_ids[0]` (`obs:120`) | **Direct** range (`priv_obs_bounds.py:149`). Live actuator gain. DR. |
| 15 | joint_damping_Kd | 1 | Arm joint implicit-actuator damping(Kd). | `_robot.data.joint_damping[:, jid:jid+1]` (`observations.py:164`) | **Direct** range (`priv_obs_bounds.py:150`). [14]와 동일 jid. DR. |
| 16 | thrust_coeff | 1 | Thruster force coefficient(단위 command당 N). Base 40. | `thr._thrust_coeff` (`observations.py:125,165`); cfg-scalar fallback (`obs:128`) | 3-way fallback (`obs:124-132`). `scale(...)`. DR. |
| 17 | thruster_time_const_up | 1 | Thruster spin-up 시상수. Base 0.1. | `thr._time_constant_up` (`observations.py:126,166`); cfg-scalar fallback (`obs:129`) | [16]과 동일 fallback branch. `scale(...)`. DR. |
| 18 | water_density | 1 | 주변 물 밀도. Base ~998; DR은 absolute range 샘플링. | `_hydro.water_density` (`observations.py:168`) | **Direct absolute**(×998 없음) (`priv_obs_bounds.py:154`). DR. |
| 19:22 | ocean_current_xyz | 3 | **world** frame의 ocean current 선속도 — 외란(external disturbance). | `_hydro.current.velocity_w[:, :3]` (`observations.py:169`) | World frame, 6개 중 첫 3개. Symmetric bounds `±ocean_max[i]*s_hi` (`priv_obs_bounds.py:155-157`). DR. |
| 22 | buoy_volume | 1 | Buoy 배제 체적(main body volume[0]과 decorrelated). | `_buoy_hydro.volume` (`observations.py:173`) | `scale(buoy_volume, buoy_volume_scale)` (`priv_obs_bounds.py:176`). DR-backed, union layout(2026-07-12)에서 추가. |
| 23 | buoy_body_mass | 1 | Buoy body mass(main body mass[8]와 decorrelated). | `_buoy_hydro.body_mass` (`observations.py:174`) | `scale(buoy_body_mass, buoy_body_mass_scale)` (`priv_obs_bounds.py:177`). DR-backed, union layout(2026-07-12)에서 추가. |
| 24 | control_action_delay | 1 | 정규화된 control-action delay(latency DR); latency DR이 off면 `0`. | `_control_delay_steps / max(control_delay_steps[1], 1)` (`observations.py:177-180`) | 고정 range `(0.0, 1.0)` (`priv_obs_bounds.py:180`). DR-backed, union layout(2026-07-12)에서 추가. |
| 25:28 | measured_body_lin_vel_uvw | 3 | **실제** body-frame 선속도 `(u,v,w)`. 유일한 non-DR 채널: 실제 측정값. | `_robot.data.root_lin_vel_b` (`observations.py:182`) | DR-backed **아님**. 고정 norm range `[-1,1]`(물리 clamp가 아니라 norm span, `priv_obs_bounds.py:159-161`). Actor는 **눈이 가려짐**; critic+encoder는 봄 → 비대칭. |

**산수**: `7 (hydro: vol 1 + CoG 3 + CoB 3) + 3 (dynamics: quad_damp_roll 1 +
body_mass 1 + added_mass_surge 1) + 4 (payload: mass 1 + CoG 3) + 4 (actuator: Kp 1
+ Kd 1 + thrust_coeff 1 + time_const_up 1) + 4 (env: water_density 1 + ocean_current
3) + 2 (buoy: volume 1 + body_mass 1) + 1 (latency: control_action_delay) + 3
(measured lin_vel) = 28` = `cfg.state_space` (`config.py:341`) = `policy.privileged_dim`
(`rsl_rl_ppo_cfg.py:148`) = `PRIV_OBS_DIM` (`priv_obs_bounds.py:46`). DR-backed
prefix는 25; measured-velocity tail은 3; `25 + 3 = 28`. Ixx와 linear damping roll은
옛 27D layout 대비 제거됐고, buoy pair(22,23)와 latency dim(24)이 추가돼 DR-backed
prefix가 순증 `24 → 25`(2개 제거, 3개 추가).

**Representative-scalar selection**: 여러 차원이 multi-DOF 양을 하나의 대표 축으로
축약한다 — quad_damp[7]는 6-DOF damping 벡터의 index 3(roll)만, added_mass[9]는
6×6 행렬의 `[0,0]`(surge)만 취한다. 따라서 `p_t`는 전체 파라미터 집합이 아니라
physics에 대한 **sparse probe**다.

**Normalization**은 DR bounds로부터의 static min-max로, MLP 이전 encoder 내부에서
적용된다 — running normalizer가 아니다. `derive_priv_obs_bounds_from_dr`
(`priv_obs_bounds.py:43`)은 DR 샘플링 range와 정확히 동일한 bounds(margin 0)를 계산하여
DR config와 normalization이 절대 drift할 수 없게 하며, base 물리 값은 asset hydro cfg
SSOT에서, DR range는 DR cfg 인스턴스에서 읽는다. runtime `_assert_bounds_match_dr`
(`priv_obs_bounds.py:212-262`)이 모든 DR-backed 차원을 re-drift-guard하고
measured-velocity tail은 건너뛴다(DR field 없음, 고정 `[-1,1]`).

---

## 5. Asymmetric consumption (encoder / actor / critic)

main env는 privileged encoder를 가진 asymmetric actor-critic(클래스
`ALBCActorCriticEncoder`)를 사용한다. 전체 층 크기와 ConstraintTRPO 업데이트는
`main-network-architecture.md` §2.1에 있으며, 여기서는 데이터 흐름과 차원만 다룬다.

결정적인 code-level 미묘함: `obs_groups["policy"]=["policy","privileged"]`와
`obs_groups["critic"]=["policy","privileged"]`(`rsl_rl_ppo_cfg.py:281-284`)는 rsl-rl이
두 group 차원을 auto-sum한다는 뜻이 **아니다**. policy 클래스가 커스텀 `PolicyBase`
서브클래스이므로, `_init_base`(`_policy_base.py:65-72`)는 "policy" group을 순서 있는
`[policy_obs_key, privileged_key]` pair로 위치적으로 파싱하고 키를 저장한다. 그러면
네트워크가 두 텐서를 스스로 split하고 라우팅한다. plain PPO baseline
(`class_name="ActorCritic"`)만이 obs_groups auto-summing에 의존하며,
`policy=["policy"]`(69D actor) / `critic=["policy","privileged"]`(97D)
(`rsl_rl_ppo_cfg.py:416-419`)를 사용한다.

| tensor | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| encoder in | p_t (privileged) | 28 | 전체 privileged 벡터 — 물리적 unknowns. | `obs[_privileged_key]`, `_encode` (`actor_critic_encoder.py:208`) | Static min-max → [-1,1] via `(2*p_t - midpoint)/range` (`:213`); bounds는 build time에 DR-derived(`constraint_encoder_runner.py:86-94`), cfg literal이 **아님**. `encoder_obs_indices=None` → 28 차원 전부 사용. |
| encoder out | z (latent) | 9 | 물리적 unknowns의 압축 proxy. | `z = softsign(LayerNorm(encoder(p_t)))` (`actor_critic_encoder.py:216`); `encoder_latent_dim=9` (`rsl_rl_ppo_cfg.py:143`) | MLP[256,128,64] elu → LayerNorm(pre-softsign, `rsl_rl_ppo_cfg.py:164`) → softsign. (-1,1)에 bounded되어 running-stat norm이 불필요. |
| actor [0:69] | normalized o_t | 69 | 측정 가능한 obs(20 proprio + 46 history + 3 integral). | `obs_normed = actor_obs_normalizer(o_t)` (`actor_critic_encoder.py:253,255`); `policy_obs_dim=69` (`rsl_rl_ppo_cfg.py:147`) | `o_t`만 EmpiricalNormalization-normalize됨(normalizer 크기 69, `:176`); z는 제외. |
| actor [69:78] | z (raw) | 9 | o_t에 concat된 encoder latent; actor가 privileged physics를 보는 유일한 창. | `cat([obs_normed, z])` (`actor_critic_encoder.py:256`); `num_actor_obs = 69+9 = 78` (`:175`) | Actor는 raw p_t를 **절대** 받지 않음. z는 raw로 전달(softsign이 이미 bound). |
| actor out | action mean | 8 | 8D action(2D arm + 6D thruster); Gaussian policy, net 내 clamp 없음. | `actor = MLP(78, 8, [256,128,64], elu)` (`actor_critic_encoder.py:182`) | `log_std`는 별도 `nn.Parameter`(`_policy_base.py:96`); std clamp는 여기가 아니라 TRPO step에서 적용(`action-pipeline.md` 참조). |
| critic [0:69] | o_t | 69 | actor와 동일한 측정 가능 obs(raw; `critic_obs_normalization=False`). | `parts=[obs[_policy_obs_key]]` (`actor_critic_encoder.py:264`) | `critic_obs_normalizer`는 `nn.Identity`(`_policy_base.py:83-85`). |
| critic [69:78] | z | 9 | critic에 주입된 encoder latent, value-loss gradient가 z를 통해 encoder로 되흐르도록. | `if _critic_uses_z: parts.append(_encode(obs))` (`actor_critic_encoder.py:265-266`); `critic_uses_z=True` (`rsl_rl_ppo_cfg.py:163`) | 이것이 `num_critic_obs += encoder_latent_dim`(`:103-104`)인 이유. False면 critic = 97D, encoder는 actor surrogate에서만 gradient를 받음. |
| critic [78:106] | p_t | 28 | Raw privileged 벡터 — train-only critic이 ground-truth physics를 직접 봄. | `parts.append(obs[_privileged_key])` (`actor_critic_encoder.py:267`); `num_critic_obs=69+28+9=106` (`:102-104`) | Critic은 z와 raw p_t를 **둘 다** 봄; z는 gradient 경로를 위한 것이지 critic이 압축을 필요로 해서가 아님. |
| critic out | value | 1 | GAE/TRPO advantage용 스칼라 `V(s)`. | `critic = MLP(106, 1, [512,256,128], elu)` (`_policy_base.py:86`) | 기본 TRPO runner에서 `normalize_value=False`(`rsl_rl_ppo_cfg.py:286`). |
| cost_critic out | per-constraint cost values | 10 | Multi-head cost value, IPO constraint당 head 하나(`K=num_constraints`, env에서 auto-sync; main env = 10). | `cost_critic = MLP(106, num_constraints, [512,256,128], elu)` (`_policy_base.py:91`) | 동일한 106D 입력 공유. K는 cfg에서 0으로 시작, `ConstraintEncoderRunner.__init__`이 auto-sync(`constraint_encoder_runner.py:42-63`). K=10(5 prob + 5 avg). |

**Consumption 산수**: encoder `28 → 9`; actor `69 + 9 = 78 → 8`; critic
`69 + 28 = 97, += 9 = 106 → 1`; cost critic `106 → K=10`. NoEncoder ablation critic =
`69 + 28 = 97`(z 없음, `rsl_rl_ppo_cfg.py:301-304`); PPO baseline actor = 69(via
`obs_groups=["policy"]`), critic = 97.

`ConstraintEncoderRunner`는 하드코딩된 `_PRIV_OBS_LOWER/UPPER` cfg
literal(`rsl_rl_ppo_cfg.py:50-120`)을 build time에 DR-derived bounds로 override한다
(`constraint_encoder_runner.py:76-94`). literal은 standalone-build fallback일
뿐이며(여전히 `student/teacher.py`가 import), DR에서 drift한 상태였다(payload overflow,
stale CoG radius). cfg literal만으로 normalization을 추론하면 틀리게 된다.

---

## 6. 자명하지 않은 사실 / gotcha

- **Asymmetric history slice**: 46D history는 `18*3=54`가 아니다. 18D-per-step ring buffer는 index 10에서 split된다 — dims `[0:10]`(joint+body)은 `hist_len=3` step 전부에 걸쳐(30D), dims `[10:18]`(action)은 가장 최근 `hist_action_len=2` step만(16D). `30+16=46`; 가장 오래된 step의 action은 의도적으로 버려짐(`albc_env.py:973-975`).
- **History는 strided이지 contiguous가 아님**: 저장된 3 step은 실제 시간 `hist_len*hist_stride*step_dt = 0.18s`에 걸쳐 있으며, 3번째 제어 step마다 기록됨(`albc_env.py:505-506`). 3개 연속 50 Hz step이 아님.
- **`o_t`에 측정 선속도 없음** — 의도적 DVL-free 설계. 측정된 `root_lin_vel_b`는 `p_t[25:28]`(`observations.py:182`)에만 나타나므로, critic/encoder는 actor가 볼 수 없는 속도를 봄.
- **Yaw는 RATE 채널**: `ang_cmd[2]`는 yaw-rate command이고 모든 yaw error 항(ang_err, integral)은 rate error(rad/s)인 반면, roll/pitch은 절대 attitude(rad)다. 3D integral은 두 angle-integral과 하나의 rate-integral을 섞는다.
- **`joint_pos_error`는 `q_des_{t-1}`을 사용**: `_get_hist_features`가 `_apply_joint_pd_action`보다 먼저 실행되므로, `_joint_pos_targets`는 여전히 이전 step의 target을 담고 있음(`albc_env.py:457-459,474`) — 설계상 one-step-stale actuator-lag 신호.
- **Noise는 우리 자신의 양을 0으로 만듦**: `_OBS_NOISE_STD`/`_OBS_BIAS_MAG`는 69-length 벡터로 command(3), manipulability(1), action-history(16), integral(3) 항목이 `0.0`(`config.py:239-278`). 측정된 euler/ang_vel/joint/thruster 채널(그리고 history 복사본)만 noise를 받음.
- **두 개의 독립 dim 검사**가 69를 신뢰 가능하게 만듦: construction-time `ValueError` guard(`albc_env.py:157-162`, `python -O`에서 살아남음) 더하기 per-step runtime assert(`albc_env.py:992-995`).
- **`p_t`는 설계상 non-redundant**(`observations.py:93-94`): 독립 DR 변수당 스칼라 하나이므로 encoder는 pass-through가 아니라 압축해야 함. 여러 차원은 multi-DOF 양의 대표 스칼라(damping index 3 = roll; added-mass `[0,0]` = surge).
- **Thruster fallback은 3-way branch**(`obs:124-132`): per-env DR 텐서 → cfg scalar broadcast → zeros(no thruster). Dims 18–19는 우아하게 degrade됨.
- **Encoder 입력 normalization은 static min-max이며 runtime에 OVERRIDE됨** — DR-derived bounds로. cfg `_PRIV_OBS_LOWER/UPPER` literal은 fallback일 뿐이며 drift한 상태였음(payload_mass overflow 3→1.35>1, stale CoG xy radius 0.17 vs 0.08 m).
- **Direct vs scale/offset norm 형태**: payload_mass[12] `[0,3]` direct, payload_cog_z[15] `[-0.05,0]` direct, water_density[20] direct absolute, joint Kp[16]/Kd[17] direct; CoG/CoB는 nonzero base로 offset 사용(CoG z base -0.05 → `[-0.09,-0.01]`).
- **`obs_groups`는 커스텀 encoder policy에서 auto-sum되지 않음** — `_policy_obs_key`/`_privileged_key`로 위치적으로 파싱됨(`_policy_base.py:65-72`). plain PPO baseline만 auto-summing에 의존.
- **Critic은 z와 p_t를 중복해서 봄**: `p_t`는 가장 낮은 variance의 value target을 줌; z의 존재는 순전히 value-loss gradient를 encoder로 라우팅하기 위함(`actor_critic_encoder.py:261-263`)이며, actor surrogate를 넘어서는 두 번째 learning signal.
- **actor 경로에서는 `o_t`만 normalize됨**(EmpiricalNorm 크기 69); z는 raw로 concat됨. softsign이 이를 bound하고, non-stationary encoder 출력을 running stats로 normalize하면 KL instability가 발생하기 때문. critic 경로 normalizer는 기본 `nn.Identity`.
- **`hist_len==0`이면 history가 0D로 붕괴**(`albc_env.py:294-296`); `o_t`는 proprio(+integral)가 됨.
- **Stale docstring 경고**: `_init_history_buffers`는 여전히 "21D per step (joint 4D + body 9D + action 8D)"라고 말하지만(`albc_env.py:282`), `hist_feature_dim=18`이고 실제 concat은 `4+6+8=18`(여기서 body는 9D가 아니라 6D)이다. 21D/9D 표현은 full-DOF variant에서 남은 것이며, 18D config 값이 실제 buffer 폭을 지배한다.
