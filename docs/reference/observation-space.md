# Observation Space (`envs/main`): obs / privileged / proprioception history

**Scope**: The observation (input) side of the default task
`Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — the 72D policy
observation `o_t`, the 28D privileged observation `p_t`, the strided proprioception
history that fills the middle of `o_t`, and how the encoder / actor / critic consume
these tensors asymmetrically. The task is **attitude-only**: roll/pitch attitude
commands plus a world-frame yaw heading command, with **no measured linear velocity** in
the actor observation (no DVL on the real robot); measured linear velocity exists only
in the privileged critic input.

This page is the **observation axis**. It complements `action-pipeline.md` (what the
policy outputs), `command-and-task.md` (how the command enters the obs and produces the
tracking error) and `main-network-architecture.md` (layer structure). For the board-side
yaw contract see [`how-to/deploy.md`](../how-to/deploy.md).

---

## 1. Overview

The env emits a two-key dict per step: `{"policy": o_t (72D), "privileged": p_t (28D)}`
(`albc_env.py: _get_observations`; `privileged` is present when `state_space > 0`,
`state_space=28`).

`o_t` is everything the real robot can measure, assembled in `_get_observations` from
four concatenated blocks: 20D current proprioception, a 46D strided temporal history,
a 3D leaky-integrated tracking error, and a 3D bias EMA. `p_t` is the hidden physics
catalogue — one scalar per independent domain-randomization (DR) parameter (25D) plus
the true body-frame linear velocity (3D). The encoder compresses **only** `p_t` into a
9D latent `z`; the actor sees `o_t + z` (never raw `p_t`); the train-only critic sees
`o_t + z + p_t`.

```
ENV emits  {"policy": o_t (72D), "privileged": p_t (28D)}

  o_t (72D) = proprio(20) + history(46) + integral(3) + bias_ema(3)
  p_t (28D) = DR-backed(25) + measured body lin_vel(3)

ENCODER   p_t(28) --minmax--> MLP[256,128,64] elu -> LayerNorm -> softsign -> z(9)

ACTOR     cat[ EmpiricalNorm(o_t)(72) , z(9) ] = 81 -> MLP[256,128,64] -> action(8)
              (never receives raw p_t — asymmetry point)

CRITIC    cat[ o_t(72) , z(9) , p_t(28) ] = 109 -> V(1)
COST CRITIC same 109D input -> K heads (K = num_constraints = 10)
```

**Why 72 and not 69.** The cfg declares `observation_space = 69` (`config.py`,
`ALBCEnvCfg`), and `use_bias_ema_obs=True` (the default) makes `apply_bias_ema_obs`
bump it to 72 at env construction by appending the 3D `_bias_ema` buffer. The agent cfg
literal `policy_obs_dim` (in `agents/rsl_rl_ppo_cfg.py`) is likewise 69, and
`sync_policy_obs_dim` (`algorithms/runners/__init__.py`) overwrites it with the env's
real width before the policy is built — so every runner trains at 72. A hardcoded 69 in
an agent cfg that bypasses this sync aborts the run.

**Headline arithmetic**

- `o_t`: `20 + 46 + 3 + 3 = 72`. History: `10*hist_len + 8*hist_action_len = 10*3 + 8*2 = 46`
  (`hist_len=3`, `hist_action_len=2`). The env raises `ValueError` at construction if the
  assembled width differs from `observation_space` (guard in `ALBCEnv.__init__`).
- `p_t`: hydro 7 + dynamics 3 + payload 4 + actuator 4 + env 4 + buoy 2 + latency 1 = 25
  DR-backed, plus body lin_vel 3 = 28.
- actor input: `policy_obs_dim(72) + encoder_latent_dim(9) = 81`.
- critic input: `72 + 28 + 9 = 109` because `critic_uses_z=True`
  (`algorithms/encoder/actor_critic_encoder.py`).

---

## 2. Policy observation `o_t` (72D)

`o_t` is the actor input: 20D proprioception + 46D history + 3D integral + 3D bias EMA.
It is DVL-free — no measured linear velocity, no lin_vel command, no lin_vel tracking
error; measured body lin_vel lives only in `p_t`.

### 2.1 Current proprioception (20D, indices 0:20)

Built by `compute_policy_obs` (`mdp/observations.py`).

| index | name | dim | meaning | noise |
|:---|:---|:--:|:---|:---|
| 0:3 | ang_cmd | 3 | `[roll_att, pitch_att, yaw_heading]`. Roll/pitch are absolute attitude setpoints (rad, ±30°); the third is the **world-frame yaw heading target** (rad, ±π). No lin-vel command. | none (our own command) |
| 3:6 | euler angles | 3 | Measured roll, pitch, yaw (rad). | std 0.02 + bias 0.02 |
| 6:9 | root_ang_vel_b | 3 | Body-frame angular velocity `(p,q,r)` rad/s. The only measured velocity the actor sees. | std 0.04 + bias 0.03 |
| 9:11 | joint_pos | 2 | Raw cumulative arm joint angles (continuous-rotation motors, no wrap). | std 0.02 + bias 0.02 |
| 11:13 | joint_vel | 2 | Arm joint velocities (rad/s). | std 0.04 + bias 0.03 |
| 13:14 | manipulability | 1 | Yoshikawa index `w` normalized to [0,1]. | none (computed) |
| 14:20 | thruster_state | 6 | Filtered thruster output for the 6 ESC channels (first-order-lag state), in firmware-ESC channel order. | std 0.02 + bias 0.01 |

### 2.2 Temporal history (46D, indices 20:66)

See §3 for the per-step feature.

| index | name | dim | meaning |
|:---|:---|:--:|:---|
| 20:50 | jb_hist | 30 | Per-step `[joint_pos_err(2), joint_vel(2), ang_err(3), euler(3)]` = 10D for all `hist_len=3` strided steps, oldest-first. |
| 50:66 | act_hist | 16 | Full 8D action `[2D arm delta, 6D thruster]` for only the newest `hist_action_len=2` steps. Noise-free. |

### 2.3 Error integral (3D, indices 66:69)

Leaky error-gated integral of `[roll_err, pitch_err, yaw_err]` (Hwangbo-2017
integral-feedback pattern), where `yaw_err` is the wrapped heading error:
`I = leak*I + gate*err*step_dt`, `gate = (|err| < integral_gate_threshold)`, clamped to
`|I| <= integral_clamp`. Defaults: `integral_leak=0.99`, `integral_clamp=2.0`,
`integral_gated=True`, `integral_gate_threshold=(0.10, 0.10, 0.10)` rad per axis
(decoupled from the reward sigmas). Updated in `_get_rewards`; present because
`use_integral_obs=True`. Noise-free (computed).

### 2.4 Bias EMA (3D, indices 69:72)

The 3D `_bias_ema` buffer `[roll, pitch, yaw]`, an ungated EMA of the tracking errors
(`bias_ema = a*bias_ema + (1-a)*err`, `bias_ema_alpha=0.99`, window about 2 s at 50 Hz).
The `reward.k_bias` penalty already reads it; exposing it to the policy removes the
non-Markov part of that penalty. It is appended by `_get_observations` only when
`use_bias_ema_obs=True`, and `apply_bias_ema_obs` raises if `reward.k_bias == 0`
(the buffer is not updated otherwise). Noise-free (computed).

### 2.5 Observation noise

Noise is applied once to the whole vector at emit, by two layers that read the same
per-dim `_OBS_NOISE_STD` / `_OBS_BIAS_MAG` vectors (`config.py`): the always-on
`NoiseModelWithAdditiveBias` and the fault/DR path `faults.apply_sensor_noise`. Both
vectors are 69 long in the source; `apply_bias_ema_obs` (and `_obs_noise_base_std` in
the env) pad them with 3 zeros for the bias-EMA channels.

- **Zero-noise dims** (computed or commanded): command(3), manipulability(1), action
  history(16), integral(3), bias EMA(3).
- **Noised dims**: measured euler / ang_vel / joint / thruster channels and their history copies.
- `apply_sensor_noise` scales the **same** base std, so zero-noise dims also get zero extra noise
  from the fault layer and from the DORAEMON-managed `obs_noise_scale` layer.

---

## 3. Temporal history (46D): per-step 18D feature vs reassembled 46D slice

A strided ring buffer of past state, built each control cycle:

1. **Compute** an 18D feature (`_get_hist_features`).
2. **Write** it into a ring buffer of depth `hist_len=3`, only every `hist_stride=3`-th control step (`_update_hist`).
3. **Slice** 46D out asymmetrically at emit (`_get_observations`).

### 3.1 Per-step 18D feature (`hist_feature_dim=18`)

| per-step index | name | dim | meaning |
|:---|:---|:--:|:---|
| 0:2 | joint_pos_error | 2 | `q_des_{t-1} - q_actual_t` for the 2 arm joints. `_get_hist_features` runs before `_apply_joint_pd_action`, so `_joint_pos_targets` still holds the previous step's target — an actuator-lag signal, by design. |
| 2:4 | joint_vel | 2 | Arm joint velocities at step t (raw rad/s). |
| 4:6 | att_rp_err | 2 | Roll/pitch attitude error (rad), wrapped via `atan2(sin,cos)`. |
| 6:7 | yaw_err | 1 | Yaw **heading** error (rad): `atan2(sin,cos)(yaw_cmd - yaw)`, wrapped to (-π, π]; its sign is the shortest turn direction. |
| 7:10 | euler_rpy | 3 | Absolute body Euler angles (rad). |
| 10:18 | prev_action | 8 | The action that produced the current state: 2D arm delta + 6D thruster. |

`[4:7]` is `ang_err = [att_rp_err(2), yaw_err(1)]`; there is no lin_vel_err (attitude-only).

### 3.2 Reassembled 46D slice (the asymmetry)

The buffer stores `3 x 18 = 54` numbers, but the obs takes joint+body (`[0:10]`) from
**all 3** steps (30D) and action (`[10:18]`) from only the **newest 2** steps (16D) = 46.
The oldest step's 8D action is dropped.

```
jb_hist  = _hist_buf[:, :, :10].reshape(N, -1)            # 10 * hist_len = 30  -> o_t[20:50]
act_hist = _hist_buf[:, -hist_action_len:, 10:].reshape() # 8  * hist_action_len = 16 -> o_t[50:66]
```

`jb_hist` is laid out per step (`joint4 + body6` per step, repeated 3x, oldest-first).

### 3.3 Striding and buffer mechanics

- **Strided recording**: `_update_hist` writes only when `hist_step_counter % hist_stride == 0`, so the 3 stored steps are 3 control steps apart. With `step_dt = 0.02 s` (50 Hz) the effective span is `hist_len * hist_stride * step_dt = 0.18 s`.
- **Shift-and-append**: index -1 is always newest, index 0 oldest.
- **Per-env masking**: the stride condition is evaluated per environment, so envs can be at different phases.
- **`hist_len == 0`**: `_hist_buf` is None and the history block contributes 0D.

---

## 4. Privileged observation `p_t` (28D)

`p_t` is emitted by `compute_privileged_obs` (`mdp/observations.py`) whenever
`state_space > 0`. It is a deliberately **non-redundant** catalogue: dims 0–24 are one
scalar per independent DR parameter, dims 25–27 are the true body-frame linear velocity
`(u,v,w)` — not a DR parameter but a real measurement the actor is blinded to. The
encoder must genuinely compress 28D to 9D rather than model correlated duplicates.
With `use_privileged_fault_obs=True` (default False) the vector is extended to 34D with
the per-thruster health; the default task does not use it.

| index | name | dim | meaning | source |
|:---|:---|:--:|:---|:---|
| 0 | body_volume | 1 | Main body displaced volume (buoyancy driver). | `_hydro.volume` |
| 1:4 | body_CoG_xyz | 3 | Body center-of-gravity offset. | `_hydro.center_of_gravity` |
| 4:7 | body_CoB_xyz | 3 | Body center-of-buoyancy offset; CoG–CoB separation sets the restoring moment. | `_hydro.center_of_buoyancy` |
| 7 | quad_damp_roll | 1 | Quadratic damping, roll axis (representative scalar). | `_hydro.quadratic_damping[:, 3:4]` |
| 8 | body_mass | 1 | Body dry mass. | `_hydro.body_mass` |
| 9 | added_mass_surge | 1 | Surge diagonal of the added-mass matrix. | `_hydro.added_mass_matrix[:, 0, 0]` |
| 10 | payload_mass | 1 | End-effector payload mass. | `_payload_mass` |
| 11:14 | payload_CoG_offset_xyz | 3 | Payload CoG offset from the mount. | `_payload_cog_offset` |
| 14 | joint_stiffness_Kp | 1 | Arm joint actuator stiffness. | `_robot.data.joint_stiffness` |
| 15 | joint_damping_Kd | 1 | Arm joint actuator damping. | `_robot.data.joint_damping` |
| 16 | thrust_coeff | 1 | Thruster force coefficient. | `thr._thrust_coeff` (cfg-scalar fallback) |
| 17 | thruster_time_const_up | 1 | Thruster spin-up time constant. | `thr._time_constant_up` (cfg-scalar fallback) |
| 18 | water_density | 1 | Ambient water density. | `_hydro.water_density` |
| 19:22 | ocean_current_xyz | 3 | Ocean current velocity, **world** frame. | `_hydro.current.velocity_w[:, :3]` |
| 22 | buoy_volume | 1 | Buoy displaced volume (decorrelated from the main body). | `_buoy_hydro.volume` |
| 23 | buoy_body_mass | 1 | Buoy mass (decorrelated from the main body). | `_buoy_hydro.body_mass` |
| 24 | control_action_delay | 1 | Normalized control-action delay (latency DR); 0 when off. | `_control_delay_steps / max(control_delay_steps[1], 1)` |
| 25:28 | measured_body_lin_vel_uvw | 3 | **True** body-frame linear velocity. The one non-DR channel. Actor blinded; critic and encoder see it. | `_robot.data.root_lin_vel_b` |

**Arithmetic**: `7 + 3 + 4 + 4 + 4 + 2 + 1 = 25` DR-backed, plus 3 measured = 28 =
`cfg.state_space` = `policy.privileged_dim` = `PRIV_OBS_DIM` (`utils/priv_obs_bounds.py`).
Several dims are representative scalars of a multi-DOF quantity (damping index 3 = roll;
added-mass `[0,0]` = surge), so `p_t` is a sparse probe of the physics.

**Normalization** is static min-max from the DR bounds, applied inside the encoder — not
a running normalizer. `derive_priv_obs_bounds_from_dr` (`utils/priv_obs_bounds.py`)
makes the bounds equal the DR sampling range exactly (margin 0), and
`_assert_bounds_match_dr` re-checks every DR-backed dim; the measured-velocity tail has
no DR field and uses a fixed `[-1, 1]` span.

---

## 5. Asymmetric consumption (encoder / actor / critic)

The main env uses an asymmetric actor-critic with a privileged encoder (class
`ALBCActorCriticEncoder`). Layer sizes and the ConstraintTRPO update are in
`main-network-architecture.md`; this section covers data flow and dims.

`obs_groups["policy"]` and `obs_groups["critic"]` are both `["policy","privileged"]`
(`agents/rsl_rl_ppo_cfg.py`), but rsl-rl does **not** auto-sum them for the custom
policy class: `_init_base` (`algorithms/encoder/_policy_base.py`) parses the group
positionally as `[policy_obs_key, privileged_key]` and the network routes the two
tensors itself. Only the plain PPO baseline (`class_name="ActorCritic"`) relies on
auto-summing, with `policy=["policy"]` (72D actor) and `critic=["policy","privileged"]`
(100D).

| tensor | dim | meaning |
|:---|:--:|:---|
| encoder in: p_t | 28 | Full privileged vector, min-max normalized to [-1,1] with DR-derived bounds (built in `algorithms/runners/constraint_encoder_runner.py`, not cfg literals). |
| encoder out: z | 9 | `softsign(LayerNorm(encoder(p_t)))`, bounded in (-1,1). |
| actor [0:72] | 72 | `EmpiricalNormalization(o_t)` — the only normalized part of the actor input. |
| actor [72:81] | 9 | `z`, concatenated raw. The actor never receives raw `p_t`. |
| actor out | 8 | Action mean (2D arm + 6D thruster); Gaussian policy with a global `log_std`. |
| critic [0:72] | 72 | `o_t`, raw (`critic_obs_normalization=False`). |
| critic [72:81] | 9 | `z`, so the value-loss gradient flows back into the encoder (`critic_uses_z=True`). |
| critic [81:109] | 28 | Raw `p_t`. |
| critic out | 1 | Scalar `V(s)`. |
| cost_critic out | K = 10 | One head per constraint, same 109D input; `K` is auto-synced from the env's constraint list. |

**Consumption arithmetic**: encoder `28 -> 9`; actor `72 + 9 = 81 -> 8`; critic
`72 + 28 + 9 = 109 -> 1`; cost critic `109 -> 10`. The NoEncoder ablation has actor 72
and critic `72 + 28 = 100` (no `z`); the PPO baseline has actor 72 and critic 100.

The `policy_obs_dim` / `privileged_dim` literals in `agents/rsl_rl_ppo_cfg.py` are
overwritten at runner construction by `sync_policy_obs_dim` / `sync_privileged_dim`, and
the hardcoded `_PRIV_OBS_LOWER/UPPER` lists are only a standalone-build fallback
(still imported by `algorithms/student/teacher.py`); reason about normalization from
the DR-derived bounds, not from those literals.

---

## 6. Non-obvious facts

- **Asymmetric history slice**: the 46D history is not `18*3 = 54`; joint+body use all 3 steps, action only the newest 2.
- **History is strided, not contiguous**: 3 stored steps span 0.18 s of real time.
- **No measured linear velocity in `o_t`** — deliberate DVL-free design; `root_lin_vel_b` appears only in `p_t[25:28]`.
- **Yaw is a heading channel**: `ang_cmd[2]` is a world-frame heading target (rad). Every yaw error term — the history `yaw_err`, the integral channel, the bias-EMA channel — is the wrapped heading error. The board must wrap it the same way (see `how-to/deploy.md`).
- **Noise zeroes our own quantities**: command, manipulability, action history, integral and bias EMA entries are 0.0 in the noise vectors; only measured euler / ang_vel / joint / thruster channels (and history copies) are noised.
- **`joint_pos_error` uses `q_des_{t-1}`**: a one-step-stale actuator-lag signal, by design.
- **The critic sees `z` and `p_t`**: `p_t` gives the lowest-variance value target; `z` is there to route value-loss gradient into the encoder.
- **Only `o_t` is normalized on the actor path**; `z` is concatenated raw because softsign already bounds it, and normalizing a non-stationary encoder output with running statistics destabilizes the KL.
