# Command and Task Definition (`envs/main`)

> Verified against commit c5a8a08.

> **Scope**: The command (goal) side of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — what the policy
> is asked to track, how commands are sampled and resampled mid-episode, how the
> command enters the observation and produces the tracking error, and how the
> tracking reward consumes that error. This is an **attitude-only** task:
> roll/pitch attitude + yaw-rate, **no linear-velocity command** (no DVL on the
> real robot).
>
> This is a code-level reference verified against disk. It complements
> `action-pipeline.md` (what the policy *outputs*) and `exploration-and-noise.md`
> (how the policy *explores*) — this doc is the **input/goal axis**: what the
> policy is trying to achieve. The full 69D observation breakdown lives in
> `main-network-architecture.md` §2.1; here we cover only the command-derived part.

---

## 1. Overview

The command is a 3D vector `_ang_cmd = [roll_att, pitch_att, yaw_rate]`. It is
sampled per env, held for a fixed window, resampled mid-episode, and occasionally
zeroed to a hover. It enters the observation noise-free (it is our own quantity,
not a sensed one), drives the tracking error and the leaky integral, and feeds the
exponential tracking reward.

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

**One important non-obvious fact up front (§6): the command curriculum is
scaffolded but inactive.** The per-env `cmd_*_scale` factors exist and multiply the
command range, but nothing ever writes them — they stay `1.0` for the whole run.
DORAEMON randomizes *physics*, not command difficulty. Command difficulty is a fixed
config knob, not a curriculum.

---

## 2. Command space

From `ALBCEnvCfg` (`config.py`):

| Command | cfg field | Range | Meaning | Location |
|---|---|---|---|---|
| roll/pitch attitude | `att_cmd_rp_range` | (-π/6, π/6) = ±30° | absolute roll & pitch attitude target (rad) | `config.py:454` |
| yaw rate | `yaw_rate_cmd_range` | (-0.5, 0.5) | body-frame yaw angular-velocity target (rad/s) | `config.py:456` |

Note the **mixed command type**: roll/pitch are *attitude* (position) targets, while
yaw is a *rate* (velocity) target. There is no yaw *attitude* command and no
linear-velocity command at all. Timing/zeroing knobs:

| cfg field | Value | Meaning | Location |
|---|---|---|---|
| `vel_cmd_resample_steps` | 250 | resample every 250 control steps = 5 s at 50 Hz | `config.py:458` |
| `vel_cmd_zero_prob` | 0.1 | per-env chance a resample yields a zero (hover) command | `config.py:460` |
| `play_mode` | False | eval mode: fix all commands to zero (hover), no resampling | `config.py:463` |

The `vel_cmd_*` names are legacy (they once drove a linear-velocity command); they
are retained now only as the shared command-timing/zeroing knobs and no longer
produce any linear velocity. The docstring at `_sample_velocity_command` records
this explicitly.

---

## 3. Sampling — `_sample_velocity_command`

`albc_env.py:719–753`. Uniform in `[-1, 1]`, scaled by the range and the (always-1.0)
per-env scale:

```python
att_max = abs(self.cfg.att_cmd_rp_range[1])          # pi/6
yaw_max = abs(self.cfg.yaw_rate_cmd_range[1])         # 0.5
att_s = self._cmd_att_scale[env_ids].unsqueeze(1)     # 1.0
yaw_s = self._cmd_yaw_scale[env_ids]                  # 1.0
self._ang_cmd[env_ids, :2] = torch.empty(n, 2, ...).uniform_(-1, 1) * (att_max * att_s)
self._ang_cmd[env_ids, 2]  = torch.empty(n, ...).uniform_(-1, 1) * (yaw_max * yaw_s)
```

Then a per-env zero mask overrides some envs to a hover:

```python
zero_mask = torch.rand(n, ...) < self.cfg.vel_cmd_zero_prob   # 0.1
if zero_mask.any():
    self._ang_cmd[env_ids[zero_mask]] = 0.0
self._vel_cmd_step_counter[env_ids] = 0
```

**Two ways to get a zero command:** the 10 % `vel_cmd_zero_prob` mask (training,
teaches station-keeping) and the `play_mode` early-return (eval, *all* commands zero
so evaluation is pure hover). The play-mode branch (`:732–735`) returns before any
sampling:

```python
if self.cfg.play_mode:
    self._ang_cmd[env_ids] = 0.0
    self._vel_cmd_step_counter[env_ids] = 0
    return
```

This is why eval (`play.py`, `eval.py`) measures hover / station-keeping performance,
not command-following — a fact worth remembering when reading eval plots.

---

## 4. Command buffer and mid-episode resampling

### 4.1 Buffer

`_ang_cmd` is `(num_envs, 3)`, initialized to zero (`albc_env.py:357`):

```python
# [0:2] = roll/pitch attitude (rad), [2] = yaw rate (rad/s)
self._ang_cmd = torch.zeros(self.num_envs, 3, device=self.device)
```

Slot semantics are fixed: `[0]` roll attitude, `[1]` pitch attitude, `[2]` yaw rate.
The same 3-channel layout is mirrored by the error buffer `_ang_err`, the integral
`_error_integral`, and the reward sigmas — all three "channels" are
[roll, pitch, yaw_rate] throughout.

### 4.2 Resample trigger

In `_pre_physics_step` (`albc_env.py:627–633`), a per-env counter drives resampling:

```python
self._vel_cmd_step_counter += 1
resample_steps = self._vel_cmd_resample_steps           # 250
if resample_steps > 0:
    resample_mask = self._vel_cmd_step_counter >= resample_steps
    if resample_mask.any():
        self._sample_velocity_command(resample_mask.nonzero(as_tuple=True)[0])
```

Each env resamples independently once its own counter reaches 250 (the counter is
reset to 0 at each sample, and also at reset with episode-length jitter, so envs
desynchronize). So within one 3000-step episode an env sees a new command roughly
every 5 s — the policy must *track a changing target*, not a fixed one.

Note: at the initial full-batch reset every env's resample counter starts at 0 (the
episode-length jitter applies to `episode_length_buf`, not to `_vel_cmd_step_counter`),
so the first mid-episode resample fires batch-synchronized at step 250; desync only
emerges later via staggered terminations.

---

## 5. Command in the observation and the tracking error

### 5.1 In the observation (noise-free)

`compute_policy_obs` (`mdp/observations.py`) puts `_ang_cmd` as the **first 3D** of
the 20D proprioception (`:71–74`):

```python
return torch.cat([
    env._ang_cmd,                              # 3D: [roll_att_cmd, pitch_att_cmd, yaw_rate_cmd]
    torch.stack([roll, pitch, yaw], dim=-1),   # 3D: euler
    ...
```

The command is **noise-free** in the observation noise model: the first 3 dims of
`_OBS_NOISE_STD` (`config.py:261`, `# ang_cmd ... (our command, no noise)`) and of
the bias model are `0.0`. This is deliberate — the command is our own set-point, not
a sensor reading, so it carries no sensor noise. (This is the same distinction
`exploration-and-noise.md` §7 draws for observation noise generally.)

### 5.2 The tracking error

`_compute_ang_errors` (`albc_env.py:1117–1124`) turns command minus measured state
into the error the reward and integral use:

```python
roll, pitch, _ = self._euler_cache
raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
self._att_rp_err = torch.atan2(torch.sin(raw), torch.cos(raw))          # wrapped to [-pi, pi]
self._yaw_rate_err = self._ang_cmd[:, 2] - self._robot.data.root_ang_vel_b[:, 2]
self._ang_err[:, :2] = self._att_rp_err
self._ang_err[:, 2]  = self._yaw_rate_err
```

- **Attitude error is angle-wrapped** (`atan2(sin, cos)`) so a command near ±π and a
  state on the other side of the wrap give the short-way error, not a spurious ~2π.
- **Yaw error is a plain rate difference** (no wrap — it is a velocity, not an angle).

### 5.3 The leaky integral

The 3 command channels also feed a leaky integrator (`_get_rewards`,
`albc_env.py:1135–1155`): `I ← integral_leak · I + gate · err · dt`, clamped to
`±integral_clamp`, with the same 3 channels `[roll, pitch, yaw_rate]`. It is
error-gated (only accumulates when `|err| < reward sigma`) and appended to the 69D
observation as the trailing 3D. Its purpose (Hwangbo-2017 pattern) is to give the
policy a memory of *sustained* offset that per-step tracking reward ignores. The
integral cfg (`integral_leak=0.99`, `integral_clamp=2.0`, `integral_gated=True`) is
in `config.py:386–388`.

---

## 6. Command "curriculum" — scaffolded but INACTIVE

The per-env command-range scales are initialized to 1.0 (`albc_env.py:375–377`):

```python
# Per-env command range scales (DORAEMON-managed, default 1.0 if disabled)
self._cmd_lin_scale = torch.ones(self.num_envs, device=self.device)
self._cmd_att_scale = torch.ones(self.num_envs, device=self.device)
self._cmd_yaw_scale = torch.ones(self.num_envs, device=self.device)
```

They are read in `_sample_velocity_command` (§3) as multipliers on the command
range. **But nothing ever writes them** — a code comment in `_reset_physics`
(`albc_env.py:1502–1503`) states it outright:

```python
# Command scales fixed at 1.0 (not DORAEMON-managed).
# DORAEMON optimizes physics DR only; command difficulty is a task knob.
```

So despite the "DORAEMON-managed" init comment, **command difficulty is not
curriculum-scaled**. DORAEMON's Beta-distribution curriculum acts on *physics*
parameters (hydrodynamics, payload, ocean current, actuator gains — see
`config.py` DR and `doraemon.py`), not on command ranges. The command range is a
**fixed config knob** (`att_cmd_rp_range`, `yaw_rate_cmd_range`); to make commands
harder you edit those tuples, you do not turn on a curriculum. The `cmd_*_scale`
buffers are dormant scaffolding for a command curriculum that is not implemented.

> This is the kind of "name vs. implementation" gap the analysis rules warn about:
> the `_cmd_*_scale` name and the "DORAEMON-managed" comment suggest a live command
> curriculum; the implementation shows a constant 1.0. Do not describe command
> difficulty as adaptive.

---

## 7. Tracking reward (how the command error is scored)

The command error drives the tracking reward via a shared exponential-quadratic
kernel `_exp_quad_saturating` (`mdp/rewards.py:109–129`):
`exp(-e²/2σ²) - quad·e² - lin·|e| - (saturating)`.

| Term | Consumes | cfg (k, σ) | Location |
|---|---|---|---|
| `att_rp_tracking` | `_att_rp_err` (roll,pitch), roll-weighted | k=9.0, σ=0.10, quad_ratio=0.833, `att_roll_weight=1.5` | `rewards.py:91,132–142` |
| `yaw_vel_tracking` | `_yaw_rate_err` | k=3.5, σ=0.10, quad_ratio=1.0, tanh_coef=0.3 | `config.py:467`, `rewards.py:145–148` |

Roll is up-weighted (`att_roll_weight=1.5`) inside the attitude error because roll
has weak TAM actuation (the 0.007 m roll arm vs. the 0.145 m pitch arm — see
`action-pipeline.md` §5.2), so roll error is penalized harder to compensate. The
reward kernel machinery itself is a separate reward-doc topic; here the point is only
that the command error (§5.2) is what these terms consume, closing the loop from
command → error → reward.

---

## 8. Knob map

| Knob | Value | Location |
|---|---|---|
| `att_cmd_rp_range` | (-π/6, π/6) = ±30° | `config.py:454` |
| `yaw_rate_cmd_range` | (-0.5, 0.5) rad/s | `config.py:456` |
| `vel_cmd_resample_steps` | 250 (5 s @ 50 Hz) | `config.py:458` |
| `vel_cmd_zero_prob` | 0.1 | `config.py:460` |
| `play_mode` (eval = hover) | False | `config.py:463` |
| command buffer `_ang_cmd` | (N, 3) [roll, pitch, yaw_rate] | `albc_env.py:357` |
| `cmd_*_scale` (INACTIVE, always 1.0) | 1.0 | `albc_env.py:375–377`, `1502–1503` |
| command in obs (first 3D, noise-free) | — | `observations.py:71–74`, `config.py:261` |
| error compute (attitude wrapped) | — | `albc_env.py:1117–1124` |
| integral (3 channels, gated leaky) | leak 0.99 / clamp 2.0 | `config.py:386–388`, `albc_env.py:1135–1155` |
| att / yaw tracking reward (k, σ) | 9.0 / 3.5, 0.10 | `rewards.py:91`, `config.py:467` |

---

## 8.5. Why yaw is a *rate* command (roll/pitch are *attitude*)

The mixed scheme — roll/pitch as absolute-attitude targets, yaw as a rate target —
is asserted throughout the code and docs but **its engineering rationale is never
stated in-code**. This section records what a multi-source review (control-design
adversarial check + marine-control literature + git-history audit, 2026-07-09)
established, separating what is verified from what is not.

**History: yaw-as-rate is inherited, not a deliberate decision.** Before
`git 11dcad6` (2026-04-01, "attitude command conversion") *all three axes were
angular-velocity (rate) commands* (the task paradigm was velocity-tracking). That
commit promoted **only roll/pitch** from rate to absolute attitude and left yaw as a
rate (renaming its semantics from generic "angular velocity" to "yaw rate"). Yaw was
**never** an absolute-angle command in the repo's history (`git log --all` shows no
yaw-angle/heading command ever). So "yaw is a rate" is the *residue of not touching
yaw* when roll/pitch were converted — not a documented "yaw must be a rate" choice.
`full_dof` handles yaw identically (only adds a linear-velocity command); it gives no
differential clue.

**The one physically-grounded asymmetry (verified).** Roll and pitch have a
metacentric restoring torque (CoB above CoG ⇒ `M ≈ Wh·θ`), so an absolute-attitude
target is natural — there is a physically-defined zero (level). Yaw about the
vertical axis is energetically neutral (symmetric buoyancy placement ⇒ **no restoring
torque**), so there is no privileged heading zero. This asymmetry is real, matches
the project's own dynamics notes (`references/iros_2026/notes/02_problem.md` lists
roll/pitch restoring eqs and marks yaw as having none), and *justifies treating yaw differently
from roll/pitch*. It does **not**, by itself, justify "command the rate" — absence of
a restoring force is the classic argument *for* an active absolute-heading loop, and
the policy already observes absolute yaw (`euler[3:6]` in obs, `observations.py:54`).

**Why it is nonetheless defensible for THIS task.** The task objective contains no
heading requirement (reward is roll/pitch attitude + yaw-*rate*; no yaw-angle term).
When heading is genuinely don't-care, commanding an absolute yaw datum would force the
policy to fight ocean-current yaw torque to hold an *arbitrary* heading, burning
thruster authority (bounded by the `thruster_util` budget) and injecting base motion
into the arm task, for no reward benefit. Letting heading float (rate command) avoids
that. This — not "no restoring force" or "strong TAM authority" — is the sound reason;
`cumulative_yaw_cost` (limit `8π` ≈ 4 revolutions, `config.py:64`) then acts purely as
a *tether-wrapping safety envelope*, not a heading objective. (Its docstring says
exactly "Prevents tether wrapping"; it is a non-binding/inert constraint in practice.)

**Where the standard-practice caveat bites.** Standard marine station-keeping / DP
(Fossen-style cascaded autopilots; ArduSub/BlueROV2 "hold current heading") closes an
outer loop on absolute **heading angle**, using rate only as an inner-loop term — it
does *not* let heading free-drift at rate=0. So the intuition "yaw-as-angle would be
cleaner" aligns with the *station-keeping* convention; the quadrotor precedent for
yaw-as-rate (yaw is the only free rotational DOF because translation consumes
roll/pitch) does **not** transfer to an independent-thruster UUV. The current design is
right *only if* heading truly is a free DOF for the downstream task.

**Unverified / open (do not treat as settled):** (a) whether switching to a yaw-angle
command would *regress* the tuned baseline is untested — it needs a one-variable A/B,
not an assertion; (b) the marine-autopilot convention above rests on secondary sources
(Fossen *Handbook* Ch. 7 primary text was not read); (c) whether the arm/manipulation
objective *implicitly* needs a stable heading (directional sensor, world-frame reach)
was not audited — if it does, the balance tips toward a yaw-angle command. See the omx
wiki card `yaw_command_is_rate_not_angle_inherited_design_defensible_only_i` for the
experiment idea and the differential-diagnosis provenance.

---

## 9. Notes and limitations

- **Eval is hover, not command-following.** `play_mode=True` zeroes all commands, so
  eval measures station-keeping under DR/disturbance, not tracking of a moving
  set-point. Read eval plots with that in mind.
- **Mixed command semantics (rationale in §8.5).** roll/pitch are attitude (position)
  targets; yaw is a rate target. There is no yaw-attitude command and no
  linear-velocity command. The privileged critic still sees measured linear velocity
  (`main-network-architecture.md` §2.2), but the actor gets no linear command. Why yaw
  specifically is a rate — and the case for/against a yaw-angle command — is §8.5.
- **Command curriculum is not implemented (§6).** The `cmd_*_scale` scaffolding is
  inert; command difficulty is fixed by the config ranges. Do not report it as
  adaptive/curriculum-scaled.
- This is a static code-structure reference. Whether the sampled command distribution
  is actually being tracked well on a given run is a runtime/eval question.

---

## Source files

- `constrained_albc/envs/main/config.py` — command ranges, resample/zero/play knobs, integral cfg, `_OBS_NOISE_STD` (command dims = 0)
- `constrained_albc/envs/main/albc_env.py` — `_sample_velocity_command` (`:719`), `_ang_cmd` buffer (`:357`), resample trigger (`:627`), `_compute_ang_errors` (`:1117`), integral update (`:1135`), `cmd_*_scale` init + inactivity note (`:375`, `:1502`)
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` (command as first 3D)
- `constrained_albc/envs/main/mdp/rewards.py` — `att_rp_tracking` / `yaw_vel_tracking`, `_exp_quad_saturating` kernel
