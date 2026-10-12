# Command and Task Definition (`envs/main`)

**Scope**: the command (goal) side of the default task `Isaac-ConstrainedALBC-TRPO-v0`
(`constrained_albc/envs/main/`) — what the policy is asked to track, how commands are
sampled and resampled, how the command enters the observation and produces the tracking
error, and how the tracking reward consumes that error. The task is **attitude-only**:
a roll/pitch attitude command plus a world-frame yaw **heading** command, and **no
linear-velocity command** (no DVL on the real robot).

| Doc | Covers |
|---|---|
| this doc | command axis: sampling, resample, obs entry, tracking error/reward |
| `action-pipeline.md` | what the policy *outputs* (actions) |
| `exploration-and-noise.md` | how the policy *explores* |
| `observation-space.md` | full 72D observation breakdown (command-derived part covered here only) |
| `reward.md` | reward system in full |

---

## 1. Overview

The command is a 3D vector `_ang_cmd = [roll_att, pitch_att, yaw_heading]` (rad):

- **Sampled** per env, held for a fixed window, resampled mid-episode, occasionally set to a hover.
- **Observed** noise-free (it is our own quantity, not a sensed one).
- **Drives** the tracking errors, the leaky integral and the bias EMA.
- **Feeds** the exponential tracking reward and the yaw-settling constraint.

```
SAMPLE  (_sample_velocity_command, per env, every 250 control steps = 5 s)
  roll/pitch ~ U(-1,1) * pi/6                  # +-30 deg   (att_cmd_rp_range)
  yaw        ~ U(-pi, pi)                      # world-frame heading target (yaw_cmd_range)
  with prob 0.1:  roll = pitch = 0, yaw = current yaw   # hover: level + hold heading
  play_mode:      roll = pitch = 0, yaw = current yaw   # eval = hovering

STORE   _ang_cmd (N, 3): [0:2] roll/pitch attitude (rad), [2] yaw heading (rad)

OBSERVE _ang_cmd is the first 3D of the 20D proprioception (obs noise std = 0.0)

ERROR   att_rp_err = atan2(sin, cos)(_ang_cmd[:,:2] - (roll, pitch))
        yaw_err    = atan2(sin, cos)(_ang_cmd[:,2]  - yaw)        # shortest-path heading error
        -> leaky integral (3D: roll, pitch, yaw) and bias EMA (3D)

REWARD  exp-kernel tracking on att_rp_err (k=9.0) and yaw_err (default k=3.5; paper teacher k=0.0)
```

A zero yaw command would mean "face world heading 0", so a hover command takes the
env's own current yaw instead of 0 rad.

### 1.1 Key fields

| Field | Shape | Meaning |
|---|---|---|
| `_ang_cmd` | (N,3) | command buffer: `[roll_att, pitch_att, yaw_heading]` |
| `_vel_cmd_step_counter` | (N,) | per-env steps since last resample; triggers resample at 250 |
| `_att_rp_err` | (N,2) | wrapped roll/pitch tracking error |
| `_yaw_err` | (N,) | wrapped yaw heading error |
| `_ang_err` | (N,3) | combined error buffer `[roll, pitch, yaw]` (mirrors `_ang_cmd` layout) |
| `_error_integral` | (N,3) | leaky error-gated integral of the three errors (§5.3) |
| `_bias_ema` | (N,3) | ungated EMA of the three errors (§5.3) |

---

## 2. Command space

From `ALBCEnvCfg` (`config.py`):

| Command | cfg field | Range | Meaning |
|---|---|---|---|
| roll/pitch attitude | `att_cmd_rp_range` | (-π/6, π/6) = ±30° | absolute roll & pitch attitude target (rad) |
| yaw heading | `yaw_cmd_range` | (-π, π) | world-frame heading target (rad); the wrapped error picks the shortest turn, so any target is at most π away |

All three are *angle* targets. There is no linear-velocity command at all. Timing and
zeroing knobs:

| cfg field | Value | Meaning |
|---|---|---|
| `vel_cmd_resample_steps` | 250 | resample every 250 control steps = 5 s at 50 Hz |
| `vel_cmd_zero_prob` | 0.1 | per-env chance a resample yields a hover command |
| `play_mode` | False | eval mode: no resampling; roll/pitch fixed to zero, yaw held at the env's current heading |

The `vel_cmd_*` names are legacy (they once drove a linear-velocity command); they now
only serve as the shared command-timing/zeroing knobs.

---

## 3. Sampling — `_sample_velocity_command`

Roll/pitch are drawn uniformly in `[-att_max, att_max]` and yaw uniformly in
`yaw_cmd_range`:

```python
att_max = abs(self.cfg.att_cmd_rp_range[1])                       # pi/6
yaw_lo, yaw_hi = self.cfg.yaw_cmd_range                           # (-pi, pi)
self._ang_cmd[env_ids, :2] = torch.empty(n, 2, ...).uniform_(-1, 1) * att_max
self._ang_cmd[env_ids, 2]  = torch.empty(n, ...).uniform_(yaw_lo, yaw_hi)
```

A per-env zero mask then overrides some envs to a hover (level, hold current heading):

```python
zero_mask = torch.rand(n, ...) < self.cfg.vel_cmd_zero_prob       # 0.1
self._ang_cmd[zero_ids, :2] = 0.0
self._ang_cmd[zero_ids, 2]  = yaw_now[zero_ids]
```

**Two ways to get a hover command:** the 10% `vel_cmd_zero_prob` mask (training, teaches
station-keeping) and the `play_mode` early return (eval: roll/pitch zero, yaw = current
heading, no random sampling). Eval therefore measures hover / station-keeping, not
command-following — keep that in mind when reading eval plots.

---

## 4. Command buffer and mid-episode resampling

`_ang_cmd` is `(num_envs, 3)`, initialized to zero in `ALBCEnv.__init__`. The slot layout
is fixed: `[0]` roll, `[1]` pitch, `[2]` yaw — mirrored by `_ang_err`, `_error_integral`
and `_bias_ema`.

In `_pre_physics_step`, a per-env counter drives resampling:

```python
self._vel_cmd_step_counter += 1
resample_mask = self._vel_cmd_step_counter >= self._vel_cmd_resample_steps    # 250
if resample_mask.any():
    self._sample_velocity_command(resample_mask.nonzero(as_tuple=True)[0])
```

Each env resamples independently once its own counter reaches 250 (the counter is reset
to 0 at each sample). With `episode_length_s = 30` at 50 Hz (1500 control steps) an env
sees a new command about every 5 s, so the policy must track a changing target.

---

## 5. Command in the observation and the tracking error

### 5.1 In the observation (noise-free)

`compute_policy_obs` (`mdp/observations.py`) puts `_ang_cmd` as the **first 3D** of the
20D proprioception. The command is noise-free: the first 3 dims of `_OBS_NOISE_STD`
(`config.py`) and of the bias model are `0.0` — it is our own set-point, not a sensor
reading.

### 5.2 The tracking error

`_compute_ang_errors` (`albc_env.py`) turns command minus measured state into the error
the reward, integral and constraints use:

```python
roll, pitch, yaw = self._euler_cache
raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
self._att_rp_err = torch.atan2(torch.sin(raw), torch.cos(raw))
yaw_raw = self._ang_cmd[:, 2] - yaw
self._yaw_err = torch.atan2(torch.sin(yaw_raw), torch.cos(yaw_raw))
self._ang_err[:, :2] = self._att_rp_err
self._ang_err[:, 2]  = self._yaw_err
```

All three errors are angle-wrapped with `atan2(sin, cos)`, so a command near ±π and a
state on the other side of the wrap give the short-way error, not a spurious ~2π.

### 5.3 The leaky integral and the bias EMA

Both are updated in `_get_rewards`.

| Buffer | Update | Cfg |
|---|---|---|
| `_error_integral` | `I <- integral_leak * I + gate * err * dt`, clamped to `±integral_clamp`; `gate = (abs(err) < integral_gate_threshold)` per axis | `integral_leak=0.99`, `integral_clamp=2.0`, `integral_gated=True`, `integral_gate_threshold=(0.10, 0.10, 0.10)` rad |
| `_bias_ema` | `a * bias_ema + (1-a) * err`, ungated | `reward.bias_ema_alpha=0.99`; updated only when `reward.k_bias != 0` |

Both are appended to the observation (indices 66:69 and 69:72, see `observation-space.md`)
to give the policy a memory of *sustained* offset that per-step tracking reward ignores.

---

## 6. Command difficulty is a fixed knob

Command ranges are fixed config values (`att_cmd_rp_range`, `yaw_cmd_range`); harder
commands mean editing those tuples. DORAEMON (see [glossary.md](glossary.md)) randomizes
*physics*, not command difficulty — there is no command curriculum.

---

## 7. Tracking reward and yaw constraints (how the command error is scored)

The command error drives the tracking reward via the shared kernel
`_exp_quad_saturating` (`mdp/rewards.py`): `exp(-e²/2σ²) - quad·e² - lin·|e| - (saturating)`.

| Term | Consumes | Default cfg |
|---|---|---|
| `att_rp_tracking` (`reward.att_rp`) | `_att_rp_err`, roll-weighted | k=9.0, σ=0.10, quad_ratio=0.833, `att_roll_weight=1.5` |
| `yaw_tracking` (`reward.yaw`) | `_yaw_err` | k=3.5, σ=0.10, quad_ratio=1.0, tanh_coef=0.3, tanh_eps=0.10 |

Roll is up-weighted (`att_roll_weight=1.5`) because roll has weak TAM (see
[glossary.md](glossary.md)) actuation, so roll error is penalized harder to compensate.

**Paper setting.** The paper's controller rewards **only roll and pitch tracking**: the
heading command and the heading are observed, and the heading rate is constrained, but
heading tracking itself is not rewarded. The released default keeps `reward.yaw.k = 3.5`;
the paper teacher (`scripts/paper/train_teacher.sh`) ran with `env.reward.yaw.k=0.0`.

The yaw channel is still shaped by two average-cost constraints that read the same
state (`config.py`, `mdp/constraints.py`):

| Constraint | Cost | Budget |
|---|---|---|
| `yaw_rate` | `max(0, abs(ω_z) - 0.55 rad/s)` — caps the slew rate toward a heading target | 0.10 |
| `yaw_settling` | `abs(ω_z)` gated on `abs(yaw_err) <= 0.087 rad` — damps oscillation about the target | 0.20 |

---

## 8. Knob map

| Knob | Value |
|---|---|
| `att_cmd_rp_range` | (-π/6, π/6) = ±30° |
| `yaw_cmd_range` | (-π, π) rad, world-frame heading |
| `vel_cmd_resample_steps` | 250 (5 s @ 50 Hz) |
| `vel_cmd_zero_prob` | 0.1 |
| `play_mode` (eval = hover) | False |
| command in obs | first 3D of proprioception, noise-free |
| `integral_*` | leak 0.99 / clamp 2.0 / gate 0.10 rad per axis |
| `reward.att_rp` / `reward.yaw` (k, σ) | 9.0 / 3.5 default (paper yaw k = 0.0), σ = 0.10 |

---

## 9. Notes and limitations

- **Eval is hover, not command-following.** `play_mode=True` holds roll/pitch at zero and yaw at the current heading, so eval measures station-keeping under DR/disturbance, not tracking of a moving set-point.
- **All three command axes are angles** (rad). The privileged critic still sees measured linear velocity (`main-network-architecture.md`), but the actor gets no linear command.
- This is a static code-structure reference. Whether the sampled command distribution is tracked well on a given run is a runtime/eval question.

---

## Source files

- `constrained_albc/envs/main/config.py` — command ranges, resample/zero/play knobs, integral cfg, `_OBS_NOISE_STD` (command dims = 0), constraint terms
- `constrained_albc/envs/main/albc_env.py` — `_sample_velocity_command`, `_ang_cmd`, resample trigger in `_pre_physics_step`, `_compute_ang_errors`, integral and bias-EMA update in `_get_rewards`
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` (command as first 3D)
- `constrained_albc/envs/main/mdp/rewards.py` — `att_rp_tracking` / `yaw_tracking`, `_exp_quad_saturating` kernel
- `constrained_albc/envs/main/mdp/constraints.py` — `yaw_rate_cost`, `yaw_settling_cost`
