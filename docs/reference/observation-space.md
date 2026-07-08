# Observation Space (`envs/main`): obs / privileged / proprioception history

> **Scope**: The observation (input) side of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — the full 69D
> policy observation `o_t`, the 27D privileged observation `p_t`, the strided
> proprioception history that fills the middle of `o_t`, and how the encoder /
> actor / critic consume these tensors asymmetrically. This is an **attitude-only**
> task: roll/pitch attitude + yaw-rate, with **no measured linear velocity** in the
> actor observation (no DVL on the real robot); measured linear velocity exists only
> in the privileged critic input.
>
> This is a code-level reference verified against disk. It is the **observation
> axis** and complements `action-pipeline.md` (what the policy *outputs*),
> `command-and-task.md` (the goal/input axis — how the command enters the obs and
> produces the tracking error), and `main-network-architecture.md` §2.1 (the full
> encoder / actor / critic layer structure). Where a topic (command sampling, action
> clamp, net layer sizes, ConstraintTRPO update) belongs to those documents, this one
> links out rather than duplicating.

---

## 1. Overview

The env emits a two-key observation dict per step:
`{"policy": o_t (69D), "privileged": p_t (27D)}`
(`albc_env.py:969-998`; `privileged` present only when `state_space > 0`,
`albc_env.py:996-997`, `state_space=27` in `config.py:341`).

`o_t` is everything the real robot can measure — assembled once per step in
`_get_observations` (`albc_env.py:969-982`) as three concatenated sub-blocks:
20D current proprioception, a 46D strided temporal history, and a 3D leaky-integrated
error. `p_t` is the hidden physics catalogue — one scalar per independent
domain-randomization (DR) parameter (24D) plus the true body-frame linear velocity
(3D). The two feed three consumers asymmetrically: the encoder compresses **only**
`p_t` into a 9D latent `z`; the actor sees `o_t + z` (never raw `p_t`); the
train-only critic sees `o_t + z + p_t`.

```
ENV emits  {"policy": o_t (69D), "privileged": p_t (27D)}      # albc_env.py:991,997

  o_t (69D) = proprio(20) + history(46) + integral(3)          # albc_env.py:969-982
  p_t (27D) = DR params(24) + measured body lin_vel(3)         # observations.py:88-161

ENCODER   p_t(27) --minmax--> MLP[256,128,64] elu -> LayerNorm -> softsign -> z(9)
                                                                # actor_critic_encoder.py:206-217

ACTOR     cat[ EmpiricalNorm(o_t)(69) , z(9) ] = 78 -> MLP -> action(8)
                                                                # actor_critic_encoder.py:246-256, 175,182
              (never receives raw p_t — asymmetry point)

CRITIC    cat[ o_t(69) , z(9) , p_t(27) ] = 105 -> V(1)        # actor_critic_encoder.py:258-268
COST CRITIC same 105D input -> K heads (K=num_constraints=10)  # _policy_base.py:91
              (train-only; sees everything for low-variance value + gradient into z)
```

**Headline arithmetic** (each traceable to `file:line`):

- `o_t`: `20 + 46 + 3 = 69` — `PROPRIO_DIM(20) + (10*hist_len + 8*hist_action_len) + integral_dims(3)`, with `hist_len=3`, `hist_action_len=2` (`config.py:398,404`), so `20 + (30 + 16) + 3 = 69` (`config.py:337`; guard `albc_env.py:151-162`).
- history: `10*hist_len + 8*hist_action_len = 10*3 + 8*2 = 30 + 16 = 46` (`albc_env.py:973-975`).
- `p_t`: `24 DR + 3 measured lin_vel = 27` — hydro 7 + dynamics 5 + payload 4 + actuator 4 + env 4 = 24, plus body lin_vel 3 = 27 (`config.py:341`; `rsl_rl_ppo_cfg.py:32-35,148`).
- actor input: `policy_obs_dim(69) + encoder_latent_dim(9) = 78` (`actor_critic_encoder.py:175`).
- critic input: `policy_obs_dim(69) + privileged_dim(27) += encoder_latent_dim(9) = 105` because `critic_uses_z=True` (`actor_critic_encoder.py:102-104`; `rsl_rl_ppo_cfg.py:163`).

---

## 2. Policy observation `o_t` (69D)

`o_t` is the asymmetric-actor input: 20D current proprioception + 46D temporal
history + 3D leaky integral. It is deliberately DVL-free — no measured linear
velocity, no lin_vel command, and no lin_vel tracking error appear anywhere in
`o_t`; measured body lin_vel lives only in `p_t` (`observations.py:158`), preserving
the actor/critic asymmetry.

Two independent checks make the 69 trustworthy: a construction-time `ValueError`
guard (`albc_env.py:151-162`) that recomputes
`20 + 10*hist_len + 8*hist_action_len + (integral_dims if use_integral_obs)` and
fails loud on mismatch (survives `python -O`, unlike an assert), plus a per-step
runtime assert `policy_obs.shape[-1] == observation_space` (`albc_env.py:992-995`).

### 2.1 Current proprioception (20D, indices 0:20)

Built by `compute_policy_obs` (`observations.py:70-85`).

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 0:3 | ang_cmd (command) | 3 | Attitude command `[roll_att, pitch_att, yaw_rate_cmd]`. roll/pitch are absolute attitude setpoints (rad, ±30°); the 3rd is a yaw-**rate** command (rad/s). No lin-vel command. | `env._ang_cmd` (`observations.py:73`); buffer `albc_env.py:304`, sampled `albc_env.py:635-636` | Noise-free: `_OBS_NOISE_STD[0:3]=0.0`, `_OBS_BIAS_MAG[0:3]=0` (`config.py:241,261`) — our own commanded quantity. |
| 3:6 | euler angles | 3 | Measured roll, pitch, yaw of body (rad), from cached euler of `root_quat_w`. | `stack([roll,pitch,yaw])` from `env._euler_cache` (`observations.py:65,75`) | Noisy: std 0.02 + bias 0.02 (`config.py:242,262`). |
| 6:9 | root_ang_vel_b | 3 | Measured body-frame angular velocity `(p,q,r)` rad/s. IMU-measurable; the **only** measured velocity the actor sees (no DVL). | `robot.data.root_ang_vel_b` (`observations.py:76`) | Noisy: std 0.04 + bias 0.03 (`config.py:243,263`). Lin-vel deliberately excluded (only in `p_t`, `observations.py:158`). |
| 9:11 | joint_pos | 2 | Raw cumulative arm joint angles (2 continuous-rotation motors, no wrap). | `robot.data.joint_pos[:, _albc_joint_ids]` (`observations.py:66,78`) | Noisy: std 0.02 + bias 0.02 (`config.py:244,264`). |
| 11:13 | joint_vel | 2 | Arm joint velocities (rad/s) for the 2 ALBC joints. | `robot.data.joint_vel[:, _albc_joint_ids]` (`observations.py:67,79`) | Noisy: std 0.04 + bias 0.03 (`config.py:245,265`). |
| 13:14 | manipulability | 1 | Yoshikawa index `w` normalized to [0,1] (1=max dexterity, 0=singularity). `w=sqrt(|l1*l2*sin(theta2)|)/sqrt(l1*l2)`. | `env._manipulability` (`observations.py:80`); computed `albc_env.py:592-594` | Noise-free: std 0.0, bias 0 (`config.py:246,266`) — computed kinematic quantity. |
| 14:20 | thruster_state | 6 | Filtered thruster output for 6 ESC channels m0–m5 (first-order-lag actuator state). | `env._thruster.state` (`observations.py:68,82`); zeros fallback if None | Noisy: std 0.02 + bias 0.01 (`config.py:247,267`). Channel order is firmware-ESC, not raw sim order (`config.py:86-91`). |

### 2.2 Temporal history (46D, indices 20:66)

See §3 for the full per-step feature and the asymmetric slice. Summary:

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 20:50 | jb_hist (joint+body, all 3 steps) | 30 | Per-step `[joint_pos_err(2), joint_vel(2), ang_err(3), euler(3)]` = 10D, kept for all `hist_len=3` strided steps, oldest-first. | `_hist_buf[:, :, :10].reshape` (`albc_env.py:973`) | `= 10*hist_len = 30`. Per-dim noise repeats `([0.02]*2+[0.04]*2 + [0.04]*3+[0.02]*3)` per step (`config.py:249,251`). |
| 50:66 | act_hist (action, newest 2 steps) | 16 | Full 8D action `[2D arm delta, 6D thruster]` kept for only the newest `hist_action_len=2` steps. Oldest step's action is dropped. | `_hist_buf[:, -hist_action_len:, 10:].reshape` (`albc_env.py:975`) | `= 8*hist_action_len = 16`. Noise-free (`[0.0]*16`, `config.py:253,273`) — our own command. |

### 2.3 Error integral (3D, indices 66:69)

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 66:69 | error_integral | 3 | Leaky error-gated integral of `[roll_err, pitch_err, yaw_rate_err]` (Hwangbo-2017 integral-feedback pattern). `I = leak*I + gate*err*step_dt`, `gate = (|err| < reward sigma)`, clamped `|I| <= 2.0`. | `env._error_integral` (`albc_env.py:981-982`); updated in `_get_rewards` (`albc_env.py:1020,1033-1038`); buffer `albc_env.py:312` | Noise-free: `[0.0]*3` (`config.py:255,275`) — computed. Present only because `use_integral_obs=True` (`config.py:343`); `integral_dims=3, leak=0.99, clamp=2.0, gated=True` (`config.py:344-347`). If the flag were False, `o_t` would be 66D. |

The integral is error-gated: it accumulates `err*dt` only when `|err|` is below the
reward tracking sigma (gate tensor pre-built in `__init__` from
`reward.att_rp.sigma` / `reward.yaw_vel.sigma`, `albc_env.py:164-175`), leaks at
`0.99/step`, and is windup-clamped to `|I| <= 2.0` (`albc_env.py:1038`). Note it
mixes two angle-integrals (roll, pitch) and one **rate**-integral (yaw rate).

### 2.4 Observation noise

Noise is applied once to the whole 69D vector at emit via the always-on
`NoiseModelWithAdditiveBias` (`config.py:509-512`) plus the fault-injection path
`faults.apply_sensor_noise` (`albc_env.py:987-989`). `_OBS_NOISE_STD` and
`_OBS_BIAS_MAG` are 69-length vectors (`config.py:239-278`) whose command(3),
manipulability(1), all action-history(16), and all integral(3) entries are `0.0` —
these are computed/commanded, not sensed, so noise adds nothing there. Only measured
euler / ang_vel / joint / thruster channels (and their history copies) receive
Gaussian std + uniform additive bias. When fault injection is disabled,
`apply_sensor_noise` is identity (`faults.py:73-77`), so the vector stays
byte-identical; when enabled it scales the **same** 69D `_OBS_NOISE_STD` base, so
zero-noise dims still receive zero extra noise.

---

## 3. Temporal history (46D): per-step 18D feature vs reassembled 46D slice

The history is a strided ring buffer of past controller/system state. Per control
step the env computes an **18D** feature vector (`_get_hist_features`,
`albc_env.py:455-495`), writes it into a ring buffer of depth `hist_len=3` but only
every `hist_stride=3`-th control step (`_update_hist`, `albc_env.py:497-512`), and
at emit slices out **46D** asymmetrically (`_get_observations`,
`albc_env.py:971-976`).

### 3.1 Per-step 18D feature (`hist_feature_dim=18`)

`hist_feature_dim = 18 = joint(4) + body(6) + action(8)` (`config.py:398-405`).

| per-step index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 0:2 | joint_pos_error | 2 | `q_des_{t-1} - q_actual_t` for the 2 arm joints. Uses the **previous** step's PD target because `_get_hist_features` runs before `_apply_joint_pd_action`, so `_joint_pos_targets` still holds `q_des_{t-1}`. An actuator-lag signal, by design. | `_joint_pos_targets - joint_pos[:, _albc_joint_ids]` (`albc_env.py:473-474,488`) | No feature-time noise/normalization. |
| 2:4 | joint_vel | 2 | Joint velocities of the 2 arm joints at step t (raw rad/s). | `joint_vel[:, _albc_joint_ids]` (`albc_env.py:475,489`) | Raw units. |
| 4:6 | att_rp_err | 2 | Roll/pitch attitude command error (rad), wrapped to [-π,π] via `atan2(sin,cos)`. | `att_raw = _ang_cmd[:,:2] - stack([roll,pitch]); atan2(sin,cos)` (`albc_env.py:480-481`) | Wrapped angle; channels 0–1 of the 3D ang_err. |
| 6:7 | yaw_rate_err | 1 | Yaw-**rate** command error (rad/s, body frame): commanded yaw rate minus measured body-frame yaw angular velocity. Yaw is rate-controlled, not attitude-controlled. | `_ang_cmd[:,2] - root_ang_vel_b[:,2]` (`albc_env.py:483-484`) | `[4:7] = ang_err = [att_rp_err(2), yaw_rate_err(1)]`; **no** lin_vel_err (attitude-only). |
| 7:10 | euler_rpy | 3 | Absolute body Euler angles (roll, pitch, yaw) in rad. | `euler_xyz_from_quat(root_quat_w)` (`albc_env.py:477,491`) | Absolute orientation state (not an error). |
| 10:18 | prev_action | 8 | The full action that produced the current state: 2D arm delta + 6D thruster (ESC m0–m5). Uses `_prev_actions` (the action applied on the step that led to state t). | `_prev_actions` (`albc_env.py:492`); set `albc_env.py:444-453`, clamped [-1,1] | Only this `[10:18]` sub-block is subject to the newest-2-steps slice. |

### 3.2 Reassembled 46D slice (the asymmetry)

The buffer stores `3 x 18 = 54` numbers, but the obs takes joint+body (`[0:10]`)
from **all 3** steps (30D) and action (`[10:18]`) from only the **newest 2** steps
(16D) = 46, not 54. The oldest step's 8D action is silently dropped
(`albc_env.py:975`). The joint+body response history is worth keeping over the full
span, but only the two most recent control inputs are fed back.

```
jb_hist  = _hist_buf[:, :, :10].reshape(N, -1)            # 10 * hist_len = 30  -> o_t[20:50]
act_hist = _hist_buf[:, -hist_action_len:, 10:].reshape() # 8  * hist_action_len = 16 -> o_t[50:66]
temporal_history = 10*hist_len + 8*hist_action_len = 30 + 16 = 46
```

`jb_hist` memory layout is per-step interleaved (`joint4+body6` per step, repeated
3×, oldest-first), **not** the "joint 12D then body 18D" grouping the
`observations.py:22-24` docstring conceptually implies — that docstring describes
totals, not the row-major flatten order.

### 3.3 Striding and buffer mechanics

- **Strided recording**: `_update_hist` writes only when `hist_step_counter % hist_stride == 0` (`albc_env.py:506`), so the 3 stored steps are 3 control-steps apart. Effective temporal span = `hist_len * hist_stride * step_dt = 3 * 3 * 0.02 = 0.18s`, not 3 consecutive 50 Hz steps. `hist_stride` is a temporal-coverage knob invisible from the obs vector itself.
- **Shift-and-append**: `_hist_buf[ids,:-1] = _hist_buf[ids,1:]` then `_hist_buf[ids,-1] = new_entry` (`albc_env.py:511-512`). Index -1 is always newest, index 0 oldest — this is why `-hist_action_len:` grabs the newest actions.
- **Per-env masking**: the `% stride` condition is evaluated per environment via `record_mask` (`albc_env.py:506,510`), so different envs can be at different phases of the stride cycle; each env's buffer advances independently.
- **`hist_len == 0` path**: `_hist_buf` is None (`albc_env.py:294-296`); `_update_hist` early-returns and `_get_observations` skips the whole history block, so history contributes exactly 0D and `o_t` becomes proprio(+integral).

---

## 4. Privileged observation `p_t` (27D)

`p_t` is emitted by `compute_privileged_obs` (`observations.py:88-161`) whenever
`state_space > 0` (`config.py:341` = 27). It is a deliberately **non-redundant**
catalogue: dims 0–23 are exactly one scalar per independent DR parameter (the
docstring states this explicitly, `observations.py:93-94`), and dims 24–26 are a
fourth-class channel — the true body-frame linear velocity `(u,v,w)`, which is **not**
a DR parameter but a real measurement the actor is blinded to. Non-redundancy is by
design: the encoder must genuinely compress 27D → 9D and would waste latent capacity
modeling correlated duplicates.

| index | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| 0 | body_volume | 1 | Main body displaced volume (buoyancy driver). Base 0.009 m³. | `_hydro.volume` (`observations.py:137`) | Norm `scale(volume, volume_scale)` (`priv_obs_bounds.py:130`). DR. |
| 1:4 | body_CoG_xyz | 3 | Body center of gravity offset. Base `(0,0,-0.05)`; z non-zero. | `_hydro.center_of_gravity` (`observations.py:138`) | Norm `offset(...)` (`priv_obs_bounds.py:131-133`); z→[-0.09,-0.01]. DR. |
| 4:7 | body_CoB_xyz | 3 | Body center of buoyancy offset. Base `(0,0,0)`. CoG–CoB separation sets restoring moment. | `_hydro.center_of_buoyancy` (`observations.py:139`) | Norm `offset(...)` (`priv_obs_bounds.py:134-136`). DR. |
| 7 | body_Ixx | 1 | Representative rigid-body inertia (roll/x). Base 0.0994. | `_hydro.rigid_body_inertia[:, 0:1]` (`observations.py:141`) | Ixx **only** (index 0 of tensor). `scale(...)` (`priv_obs_bounds.py:138`). DR. |
| 8 | lin_damp_roll | 1 | Representative linear damping, roll axis. Base 0.3. | `_hydro.linear_damping[:, 3:4]` (`observations.py:142`) | Roll only (index 3; 0-2=lin xyz, 3-5=ang). DR. |
| 9 | quad_damp_roll | 1 | Representative quadratic damping, roll axis. Base 1.0. | `_hydro.quadratic_damping[:, 3:4]` (`observations.py:143`) | Roll only (index 3). `scale(...)` (`priv_obs_bounds.py:140`). DR. |
| 10 | body_mass | 1 | Body dry mass. Base 9.18 kg. | `_hydro.body_mass` (`observations.py:144`) | `scale(...)` (`priv_obs_bounds.py:141`). Distinct from payload_mass[12]. DR. |
| 11 | added_mass_surge | 1 | Surge (x) diagonal of added-mass matrix. Base 8.0. | `_hydro.added_mass_matrix[:, 0, 0]` (`observations.py:145`) | Surge only (`[0,0]` of 6×6), raw DR upper 12.0 (`priv_obs_bounds.py:142`). DR. |
| 12 | payload_mass | 1 | End-effector payload mass. Base 0; DR samples [0,3] kg. | `_payload_mass` (`observations.py:147`) | **Direct** range `[0,3]` (`priv_obs_bounds.py:144`). Old hardcoded `[-0.1,2.2]` was a norm bug (3→1.35>1). DR. |
| 13:16 | payload_CoG_offset_xyz | 3 | Payload CoG offset from mount. xy from radius, z direct. | `_payload_cog_offset` (`observations.py:148`) | x,y = `[-r,r]`, `r=0.08 m` (old 0.17 stale); z direct `[-0.05,0]` (`priv_obs_bounds.py:145-147`). DR. |
| 16 | joint_stiffness_Kp | 1 | Arm joint implicit-actuator stiffness (Kp). | `_robot.data.joint_stiffness[:, jid:jid+1]` (`observations.py:150`), `jid=_albc_joint_ids[0]` (`obs:120`) | **Direct** range (`priv_obs_bounds.py:149`). Live actuator gain. DR. |
| 17 | joint_damping_Kd | 1 | Arm joint implicit-actuator damping (Kd). | `_robot.data.joint_damping[:, jid:jid+1]` (`observations.py:151`) | **Direct** range (`priv_obs_bounds.py:150`). Same jid as [16]. DR. |
| 18 | thrust_coeff | 1 | Thruster force coefficient (N per unit command). Base 40. | `thr._thrust_coeff` (`observations.py:125,152`); cfg-scalar fallback (`obs:128`) | 3-way fallback (`obs:124-132`). `scale(...)`. DR. |
| 19 | thruster_time_const_up | 1 | Thruster spin-up time constant. Base 0.1. | `thr._time_constant_up` (`observations.py:126,153`); cfg-scalar fallback (`obs:129`) | Same fallback branch as [18]. `scale(...)`. DR. |
| 20 | water_density | 1 | Ambient water density. Base ~998; DR samples absolute range. | `_hydro.water_density` (`observations.py:155`) | **Direct absolute** (no ×998) (`priv_obs_bounds.py:154`). DR. |
| 21:24 | ocean_current_xyz | 3 | Ocean current linear velocity in **world** frame — the external disturbance. | `_hydro.current.velocity_w[:, :3]` (`observations.py:156`) | World frame, first 3 of 6. Symmetric bounds `±ocean_max[i]*s_hi` (`priv_obs_bounds.py:155-157`). DR. |
| 24:27 | measured_body_lin_vel_uvw | 3 | **True** body-frame linear velocity `(u,v,w)`. The one non-DR channel: a real measurement. | `_robot.data.root_lin_vel_b` (`observations.py:158`) | **Not** DR-backed. Fixed norm range `[-1,1]` (a norm span, not a physical clamp, `priv_obs_bounds.py:159-161`). Actor **blinded**; critic+encoder see it → asymmetry. |

**Arithmetic**: `7 (hydro: vol 1 + CoG 3 + CoB 3) + 5 (dynamics: Ixx 1 +
lin_damp_roll 1 + quad_damp_roll 1 + body_mass 1 + added_mass_surge 1) + 4 (payload:
mass 1 + CoG 3) + 4 (actuator: Kp 1 + Kd 1 + thrust_coeff 1 + time_const_up 1) + 4
(env: water_density 1 + ocean_current 3) + 3 (measured lin_vel) = 27` =
`cfg.state_space` (`config.py:341`) = `policy.privileged_dim` (`rsl_rl_ppo_cfg.py:148`)
= `PRIV_OBS_DIM` (`priv_obs_bounds.py:40`). The DR-backed prefix is 24; the
measured-velocity tail is 3; `24 + 3 = 27`, matching the cfg comment
"24D from HardDomainRandomizationCfg + 3D measured lin_vel" (`rsl_rl_ppo_cfg.py:32-35`).

**Representative-scalar selection**: several dims collapse a multi-DOF quantity to
one representative axis — Ixx[7] takes only index 0 of the inertia tensor,
lin_damp[8]/quad_damp[9] take only index 3 (roll) of the 6-DOF damping vector,
added_mass[11] takes only `[0,0]` (surge) of the 6×6 matrix. So `p_t` is a **sparse
probe** of the physics, not the full parameter set.

**Normalization** is static min-max from DR bounds, applied inside the encoder before
its MLP — not a running normalizer. `derive_priv_obs_bounds_from_dr`
(`priv_obs_bounds.py:43`) computes bounds equal to the DR sampling range exactly
(margin 0) so DR config and normalization can never drift, reading base physical
values from the asset hydro cfg SSOT and DR ranges from the DR cfg instance; a
runtime `_assert_bounds_match_dr` (`priv_obs_bounds.py:212-262`) re-drift-guards every
DR-backed dim and skips the measured-velocity tail (no DR field, fixed `[-1,1]`).

---

## 5. Asymmetric consumption (encoder / actor / critic)

The main env uses an asymmetric actor-critic with a privileged encoder (class
`ALBCActorCriticEncoder`). Full layer sizes and the ConstraintTRPO update live in
`main-network-architecture.md` §2.1; here we cover only the data flow and dims.

A crucial code-level subtlety: `obs_groups["policy"]=["policy","privileged"]` and
`obs_groups["critic"]=["policy","privileged"]` (`rsl_rl_ppo_cfg.py:281-284`) do **not**
mean rsl-rl auto-sums the two group dims. Because the policy class is a custom
`PolicyBase` subclass, `_init_base` (`_policy_base.py:65-72`) parses the "policy"
group positionally as an ordered `[policy_obs_key, privileged_key]` pair and stores
the keys; the network then splits and routes the two tensors itself. Only the plain
PPO baseline (`class_name="ActorCritic"`) relies on obs_groups auto-summing, and it
uses `policy=["policy"]` (69D actor) / `critic=["policy","privileged"]` (96D)
(`rsl_rl_ppo_cfg.py:416-419`).

| tensor | name | dim | meaning | source | note |
|:---|:---|:--:|:---|:---|:---|
| encoder in | p_t (privileged) | 27 | Full privileged vector — the physical unknowns. | `obs[_privileged_key]`, `_encode` (`actor_critic_encoder.py:208`) | Static min-max → [-1,1] via `(2*p_t - midpoint)/range` (`:213`); bounds DR-derived at build time (`constraint_encoder_runner.py:86-94`), NOT cfg literals. `encoder_obs_indices=None` → all 27 dims used. |
| encoder out | z (latent) | 9 | Compressed proxy for the physical unknowns. | `z = softsign(LayerNorm(encoder(p_t)))` (`actor_critic_encoder.py:216`); `encoder_latent_dim=9` (`rsl_rl_ppo_cfg.py:143`) | MLP[256,128,64] elu → LayerNorm (pre-softsign, `rsl_rl_ppo_cfg.py:164`) → softsign. Bounded to (-1,1) so it needs no running-stat norm. |
| actor [0:69] | normalized o_t | 69 | Measurable obs (20 proprio + 46 history + 3 integral). | `obs_normed = actor_obs_normalizer(o_t)` (`actor_critic_encoder.py:253,255`); `policy_obs_dim=69` (`rsl_rl_ppo_cfg.py:147`) | Only `o_t` is EmpiricalNormalization-normalized (normalizer sized 69, `:176`); z is excluded. |
| actor [69:78] | z (raw) | 9 | Encoder latent concatenated onto o_t; the actor's only window into the privileged physics. | `cat([obs_normed, z])` (`actor_critic_encoder.py:256`); `num_actor_obs = 69+9 = 78` (`:175`) | Actor **never** receives raw p_t. z passed raw (softsign already bounds it). |
| actor out | action mean | 8 | 8D action (2D arm + 6D thruster); Gaussian policy, no clamp in the net. | `actor = MLP(78, 8, [256,128,64], elu)` (`actor_critic_encoder.py:182`) | `log_std` separate `nn.Parameter` (`_policy_base.py:96`); std clamp applied in the TRPO step, not here (see `action-pipeline.md`). |
| critic [0:69] | o_t | 69 | Same measurable obs as actor (raw; `critic_obs_normalization=False`). | `parts=[obs[_policy_obs_key]]` (`actor_critic_encoder.py:264`) | `critic_obs_normalizer` is `nn.Identity` (`_policy_base.py:83-85`). |
| critic [69:78] | z | 9 | Encoder latent injected into critic so value-loss gradient flows back through z into the encoder. | `if _critic_uses_z: parts.append(_encode(obs))` (`actor_critic_encoder.py:265-266`); `critic_uses_z=True` (`rsl_rl_ppo_cfg.py:163`) | This is why `num_critic_obs += encoder_latent_dim` (`:103-104`). If False, critic = 96D and encoder gets gradient only from actor surrogate. |
| critic [78:105] | p_t | 27 | Raw privileged vector — the train-only critic sees ground-truth physics directly. | `parts.append(obs[_privileged_key])` (`actor_critic_encoder.py:267`); `num_critic_obs=69+27+9=105` (`:102-104`) | Critic sees BOTH z and raw p_t; z is present for the gradient path, not because the critic needs compression. |
| critic out | value | 1 | Scalar `V(s)` for GAE/TRPO advantage. | `critic = MLP(105, 1, [512,256,128], elu)` (`_policy_base.py:86`) | `normalize_value=False` for default TRPO runner (`rsl_rl_ppo_cfg.py:286`). |
| cost_critic out | per-constraint cost values | 10 | Multi-head cost value, one head per IPO constraint (`K=num_constraints`, auto-synced from env; main env = 10). | `cost_critic = MLP(105, num_constraints, [512,256,128], elu)` (`_policy_base.py:91`) | Shares the identical 105D input. K starts 0 in cfg, auto-synced by `ConstraintEncoderRunner.__init__` (`constraint_encoder_runner.py:42-63`). K=10 (5 prob + 5 avg). |

**Consumption arithmetic**: encoder `27 → 9`; actor `69 + 9 = 78 → 8`; critic
`69 + 27 = 96, += 9 = 105 → 1`; cost critic `105 → K=10`. NoEncoder ablation critic =
`69 + 27 = 96` (no z, `rsl_rl_ppo_cfg.py:301-304`); PPO baseline actor = 69 (via
`obs_groups=["policy"]`), critic = 96.

The `ConstraintEncoderRunner` overrides the hardcoded `_PRIV_OBS_LOWER/UPPER` cfg
literals (`rsl_rl_ppo_cfg.py:50-120`) at build time with the DR-derived bounds
(`constraint_encoder_runner.py:76-94`); the literals are only a standalone-build
fallback (still imported by `student/teacher.py`) and had drifted from DR (payload
overflow, stale CoG radius). Reasoning about normalization from the cfg literals
alone would be wrong.

---

## 6. Non-obvious facts / gotchas

- **Asymmetric history slice**: the 46D history is NOT `18*3=54`. The 18D-per-step ring buffer splits at index 10 — dims `[0:10]` (joint+body) broadcast over all `hist_len=3` steps (30D), dims `[10:18]` (action) over only the newest `hist_action_len=2` steps (16D). `30+16=46`; the oldest step's action is intentionally dropped (`albc_env.py:973-975`).
- **History is strided, not contiguous**: 3 stored steps span `hist_len*hist_stride*step_dt = 0.18s` of real time, recorded every 3rd control step (`albc_env.py:505-506`), not 3 consecutive 50 Hz steps.
- **No measured linear velocity in `o_t`** — deliberate DVL-free design. Measured `root_lin_vel_b` appears only in `p_t[24:27]` (`observations.py:158`), so the critic/encoder see velocity the actor cannot.
- **Yaw is a RATE channel**: `ang_cmd[2]` is a yaw-rate command and every yaw error term (ang_err, integral) is a rate error (rad/s), whereas roll/pitch are absolute attitude (rad). The 3D integral mixes two angle-integrals and one rate-integral.
- **`joint_pos_error` uses `q_des_{t-1}`**: `_get_hist_features` runs before `_apply_joint_pd_action`, so `_joint_pos_targets` still holds the previous step's target (`albc_env.py:457-459,474`) — a one-step-stale actuator-lag signal, by design.
- **Noise zeroes our own quantities**: `_OBS_NOISE_STD`/`_OBS_BIAS_MAG` are 69-length vectors whose command(3), manipulability(1), action-history(16), and integral(3) entries are `0.0` (`config.py:239-278`). Only measured euler/ang_vel/joint/thruster channels (and history copies) get noise.
- **Two independent dim checks** make 69 trustworthy: a construction-time `ValueError` guard (`albc_env.py:157-162`, survives `python -O`) plus a per-step runtime assert (`albc_env.py:992-995`).
- **`p_t` is non-redundant by design** (`observations.py:93-94`): one scalar per independent DR variable, so the encoder must compress rather than pass-through. Several dims are representative scalars of a multi-DOF quantity (Ixx index 0; damping index 3 = roll; added-mass `[0,0]` = surge).
- **Thruster fallback is a 3-way branch** (`obs:124-132`): per-env DR tensor → cfg scalar broadcast → zeros (no thruster). Dims 18–19 degrade gracefully.
- **Encoder input normalization is static min-max and OVERRIDDEN at runtime** by DR-derived bounds; the cfg `_PRIV_OBS_LOWER/UPPER` literals are a fallback only and had drifted (payload_mass overflow 3→1.35>1, stale CoG xy radius 0.17 vs 0.08 m).
- **Direct vs scale/offset norm forms**: payload_mass[12] `[0,3]` direct, payload_cog_z[15] `[-0.05,0]` direct, water_density[20] direct absolute, joint Kp[16]/Kd[17] direct; CoG/CoB use offset with nonzero base (CoG z base -0.05 → `[-0.09,-0.01]`).
- **`obs_groups` is not auto-summed** for the custom encoder policy — it is parsed positionally into `_policy_obs_key`/`_privileged_key` (`_policy_base.py:65-72`). Only the plain PPO baseline relies on auto-summing.
- **Critic redundantly sees z AND p_t**: `p_t` gives the lowest-variance value target; z's presence is purely to route value-loss gradient into the encoder (`actor_critic_encoder.py:261-263`), a second learning signal beyond the actor surrogate.
- **Only `o_t` is normalized on the actor path** (EmpiricalNorm sized 69); z is concatenated raw because softsign bounds it and normalizing a non-stationary encoder output with running stats causes KL instability. The critic path normalizer is `nn.Identity` by default.
- **`hist_len==0` collapses history to 0D** (`albc_env.py:294-296`); `o_t` becomes proprio(+integral).
- **Stale docstring warning**: `_init_history_buffers` still says "21D per step (joint 4D + body 9D + action 8D)" (`albc_env.py:282`), but `hist_feature_dim=18` and the actual concat is `4+6+8=18` (body is 6D here, not 9D). The 21D/9D wording is leftover from the full-DOF variant; the 18D config value governs the real buffer width.

---

## 7. Proposed changes (designed 2026-07-08, NOT yet in code)

> This section records `p_t` / DR-space changes decided in a design session but not yet
> implemented. The 27D layout above still describes the LIVE code; these are the pending
> experiments (each isolated on its own `exp/*` branch off a baseline tag, training
> user-gated). Execution specs live in the session prompts; see the session memory
> `project-obs-space-doc-qa-260708` for provenance.

### 7.1 Privileged-obs slim (`p_t` 27 → 22)

Remove five `p_t` dims to reduce the encoder's compression burden and the input/output dim
gap. Per-dim evidence (encoder z-sensitivity sweep on `trpo_baseline_260608`, `scratch/encoder_sweep/`):

| p_t idx | dim | evidence for removal | status |
|:---|:---|:---|:---|
| `[7]` | body_Ixx | z-sweep low sensitivity (range 0.278, 2/9 latents active) | sweep-justified |
| `[8]` | lin_damp_roll | z-sweep lowest tier (range 0.162, 4/9) | sweep-justified |
| `[9]` | quad_damp_roll | z-sweep CONTRADICTS (range 0.641, 7/9 — encoder actively uses it) | user-directed, **baseline-verify required** |
| `[24:27]` | measured lin_vel (u,v,w) | attitude-only task: no lin_vel command, and `lin_vel_tracking` reward is dead code (NOT in `RewardManager._NAMES`, `rewards.py:199`) → not a value-determining variable. High z-sweep (1.08–1.25) reflects hydro↔attitude coupling, not a control need. | task-purpose-justified, **baseline-verify required** |

`water_density[20]` is KEPT (enters buoyancy `F_b=ρgV`; low z-sweep likely reflects overlap
with `volume_scale`, not irrelevance). The two flagged dims (quad_damp, lin_vel) are removed on
the user's decision beyond/against the sweep, so their removal must be confirmed by a WITH-vs-
WITHOUT baseline comparison (critic value-loss, explained-variance, attitude tracking) — not
assumed safe. Ripple: `priv_obs_bounds.py` (`PRIV_OBS_DIM`, `pairs`, `_assert_bounds_match_dr`
re-index), `state_space`/`privileged_dim` literals, critic input dim, checkpoint width (fresh
training, no resume).

### 7.2 DR offset prune + buoy hydro decorrelation

Two independent DORAEMON-space experiments (separate runs, rules/03 confound avoidance):
- **Experiment A (prune, symmetry-justified):** remove body CoB/CoG **xy** offset DR (near-
  cylindrical hull → xy≈0, the least-justified DR axis) and make the buoy CoB/CoG **z**-offset
  main-only (single-material float → CoG=CoB=(0,0,0.059), zero self-restoring, so its z-offset
  DR is a dead knob; the MAIN body does all righting via its deliberate CoG z=-0.05). `NDIMS`
  18→14; `p_t` −4 (CoG/CoB xy → constant → leave p_t, `[1:3]`/`[4:6]`). No gate.
- **Experiment B (decorrelate buoy volume+mass):** the buoy (`env._buoy_hydro`) is a physically
  separate fabricated part from the main hull; today `randomize_hydrodynamics` (`events.py:282-283`)
  applies the SAME per-env scale to both bodies (fully correlated), so independent buoyancy/mass
  tolerance is not representable. Split `volume_scale` and `body_mass_scale` into buoy-specific
  dims (`NDIMS` +2) and ADD them to `p_t` (+2, since they become independent variables). This
  was previously reviewed DORMANT (omx wiki `buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy`,
  2026-07-07: no eval evidence, no measured tolerance); the **user opened the gate by domain
  judgment** (single-material float → independent tolerance, standing in for the tolerance gate).
  water_density stays SHARED (same tank = same water).

If all three land, index re-derivation must be done from the then-current layout, never by hand-
merging stale index maps (the two prompts each independently touch `compute_privileged_obs` +
`priv_obs_bounds.py`). Net `p_t` ≈ 27 − 5 (slim) − 4 (A xy) + 2 (B buoy) = 20; verify by code.
