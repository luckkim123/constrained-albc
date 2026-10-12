# Reward System (`envs/main`)

> **Scope**: Reward computation of the default task `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`): the shared tracking kernel, the weighted terms
> `RewardManager` sums each step, the error buffers in `albc_env.py` that feed them, and the
> config override that turns the shipped reward into what actually runs.
>
> Attitude-only ALBC env: the command is roll/pitch attitude plus a world-frame **yaw heading**
> (rad); there is no linear-velocity command. The reward is `dt`-scaled and splits into tracking
> rewards (positive) and penalties (negative-weighted).
>
> **Two channels, do not conflate.** This document covers the scalar reward summed by
> `RewardManager`. The per-constraint costs (`compute_all_costs` in `mdp/constraints.py`) that
> drive the ConstraintTRPO+IPO barrier are a separate signal, see [constraints.md](constraints.md).
> The two share the error buffers (§6) and nothing else.

---

## 1. Overview

The reward for one control step is a `dt`-scaled weighted sum of six builtin terms plus an
optional seventh (`sstv`). `RewardManager.compute()` (`rewards.py`) multiplies every term by its
per-second weight and by `dt = step_dt = 0.02 s` (`sim.dt = 0.005` times `decimation = 4`), so
the reported weights are per-second and the per-step contribution is `weight * 0.02`.

```
_get_rewards()                                    (albc_env.py)
  1. _compute_ang_errors()   -> _att_rp_err, _yaw_err
  2. leaky integral update   (observation only, not reward; gated, see §7)
  3. bias-EMA update         (only if k_bias != 0)
  4. RewardManager.compute(robot, dt=step_dt, env)   -> sum of weight * value * dt
  5. reward += reset_terminated * termination_penalty   (only if != 0; NOT dt-scaled)
  6. constraint costs -> extras["costs"]             (separate channel)
  7. _episode_return_accum += reward                 (DORAEMON success feed, §8)
```

| Class | Terms (`_BUILTIN_TERMS` order) |
|---|---|
| Tracking (reward) | `att_rp`, `yaw` |
| Penalty | `torque`, `thruster`, `smoothness`, `bias` |
| Optional penalty (extra term, off by default) | `sstv` |

`termination_penalty` is applied outside `compute()` and is not one of the tracked terms.

---

## 2. The shared tracking kernel `_exp_quad_saturating`

Both tracking functions call one kernel (`rewards.py`), which combines a Gaussian bump with up
to three penalty shapes:

$$
r_{\text{kernel}} = \exp\!\left(-\frac{e^2}{2\sigma^2}\right) - q_{\text{quad}}\, e^2 - q_{\text{lin}}\, |e|
- c_{\tanh}\,\epsilon_{\tanh}\tanh\!\left(\tfrac{|e|}{\epsilon_{\tanh}}\right)
- c_{\text{atan}}\,\epsilon_{\text{atan}}\tfrac{2}{\pi}\arctan\!\left(\tfrac{|e|}{\epsilon_{\text{atan}}}\right)
$$

The tanh and arctan terms are active only if their coefficient is positive. $e^2$ is `err_sq`
(possibly a weighted sum of squares, §4) and $|e|$ is `err_norm`. The per-term weight `k` is not
applied inside the kernel; `RewardManager.compute()` multiplies it in afterwards.

| Shape | Value at `e=0` | Gradient at `e=0` | Role |
|---|---|---|---|
| `exp(-e^2/2s^2)` | 1 (max) | 0 | positive reward, slope peaks at `|e| = sigma` |
| `quad_ratio * e^2` | 0 | 0 | penalty that dominates at large error |
| `lin_ratio * |e|` | 0 | `lin_ratio` (constant) | disabled, `lin_ratio = 0` everywhere shipped |
| tanh penalty | 0 | `c_tanh` | bounded near-zero force, light tail |
| arctan penalty | 0 | $(2/\pi)\,c_{\text{atan}}$ | bounded near-zero force, heavier tail; never set nonzero |

The exp and quadratic gradients both vanish as `e -> 0`, leaving a dead zone near the setpoint.
The linear penalty was the original fix but caused its own dead zone and is disabled
(`lin_ratio = 0` in every shipped config). The saturating tanh penalty is the only live
mitigation, and it sits on `yaw` only; `att_rp` has no saturating term. The tanh and arctan
blocks are independent `if` statements, so both would stack if both coefficients were set;
"at most one" is a convention, not a code invariant. The kernel can go negative when the
penalties exceed the exp bump.

---

## 3. Term catalog

`ALBCRewardCfg` (`rewards.py`) holds the defaults; `ALBCEnvCfg.reward` (`config.py`) overrides
two of them (`yaw` gains a tanh penalty, `k_bias` is turned on).

| Name | Function | Pre-weight value | Weight field | Dataclass default | Shipped (`config.py`) |
|---|---|---|---|---|---|
| `att_rp` | `att_rp_tracking` | kernel of `e_w^2 = w_roll*roll_err^2 + pitch_err^2` | `att_rp.k` | `k=9.0, sigma=0.10, quad_ratio=0.833`; `att_roll_weight=1.5` | unchanged |
| `yaw` | `yaw_tracking` | kernel of the wrapped heading error (rad) | `yaw.k` | `k=3.5, sigma=0.10, quad_ratio=1.0` | adds `tanh_coef=0.3, tanh_eps=0.10` |
| `torque` | `joint_torque` | `mean(applied_torque[arm joints]^2)` | `k_tau` | `-0.01` | unchanged |
| `thruster` | `thruster_energy` | `mean(actions[:, 2:]^2)` (6 thruster dims) | `k_thr` | `-0.35` | unchanged |
| `smoothness` | `action_smoothness` | `mean(da^2) + mean(d2a^2)` over 8 dims | `k_s` | `-0.1` | unchanged |
| `bias` | `bias_ema_penalty` | `sum_i w_i * bias_ema_i^2` (roll, pitch, yaw heading) | `k_bias` | `0.0` | `-2.0` |
| `sstv` | `ss_window_rp_tv_l1` | after the command settles: `mean(abs(p), abs(q))` | `k_sstv` | `0.0` (term not registered) | unchanged |

Other `ALBCRewardCfg` fields: `termination_penalty = 0.0`, `bias_ema_alpha = 0.99` (about a
100-step, 2 s window at 50 Hz), `bias_weights = (1.5, 1.0, 1.0)` (roll, pitch, yaw),
`sstv_start_step = 125`, `extra_terms = []`.

### 3.1 Paper teacher overrides

The paper teacher (`scripts/paper/train_teacher.sh`) was launched with these reward overrides
on top of the shipped values:

| Override | Effect |
|---|---|
| `env.reward.yaw.k=0.0` | the yaw heading reward contributes nothing (`Reward/yaw` is 0); heading is observed and its rate is constrained (`yaw_rate`, `yaw_settling`), not rewarded |
| `env.reward.att_roll_weight=1.0` | roll and pitch errors weighted equally in `att_rp` |
| `env.reward.bias_weights=[1.5,1.0,0.0]` | the bias-EMA penalty ignores the heading entry |
| `env.reward.k_sstv=-5.0` | enables the roll/pitch angular-rate (SSTV) penalty, §5.5 |

So the paper reward tracks roll and pitch, and penalizes arm-joint torque, thrust energy,
action changes, sustained offset (bias EMA) and roll/pitch angular rate.

### 3.2 Per-step magnitude at zero error

At zero error the tracking kernel is 1.0, so `att_rp` contributes `9.0 * 0.02 = 0.18` per step
and `yaw` (default `k = 3.5`) contributes `0.07`; with `yaw.k = 0.0` the yaw term is 0.

---

## 4. The tracking terms

### 4.1 `att_rp_tracking`

```python
rp_err    = env._att_rp_err                                             # (N, 2): [roll_err, pitch_err]
err_sq    = cfg.att_roll_weight * rp_err[:, 0].pow(2) + rp_err[:, 1].pow(2)
err_abs_w = cfg.att_roll_weight * rp_err[:, 0].abs() + rp_err[:, 1].abs()   # Manhattan, not sqrt(err_sq)
return _exp_quad_saturating(err_sq, err_abs_w, cfg.att_rp)
```

`err_sq` feeds the exp and quadratic terms; `err_abs_w` feeds only the linear/tanh/arctan
penalties, none of which is active on `att_rp`. The shipped default `att_roll_weight = 1.5` is
documented in `rewards.py` as compensation for weak roll authority in the thruster allocation
matrix (Mx coefficient 0.007 against My 0.145 in `_BASE_ALLOCATION_MATRIX`, `config.py`); the
paper teacher runs with `att_roll_weight = 1.0`.

### 4.2 `yaw_tracking`

```python
err = env._yaw_err                       # wrapped heading error, rad
return _exp_quad_saturating(err.pow(2), err.abs(), env.cfg.reward.yaw)
```

The yaw command is a world-frame heading target (`yaw_cmd_range = (-pi, pi)` in `config.py`),
and `_yaw_err` is the wrapped shortest-path difference (§6.1). No weighting is applied. The
shipped config adds `tanh_coef = 0.3, tanh_eps = 0.10`, making `yaw` the only tracking term
with a saturating penalty (gradient 0.3 at zero error). The paper teacher sets `yaw.k = 0.0`
(§3.1), which removes the whole term.

---

## 5. The penalty terms

The penalties return non-negative magnitudes; the sign lives in the weight. All are `dt`-scaled
at the same single point as the tracking terms.

### 5.1 `joint_torque`

`mean(applied_torque[albc_joint_ids]^2)`, read from `robot.data.applied_torque`: the
post-actuator-model, post-clamp torque, not the raw commanded action.

### 5.2 `thruster_energy`

`mean(env._actions[:, 2:]^2)`. The action layout is `[2D arm delta, 6D thruster]`, so the
slice takes the 6 thruster dims and excludes the 2 arm dims.

### 5.3 `action_smoothness`

$$
\text{mean}(\Delta a^2) + \text{mean}(\Delta^2 a^2),\quad
\Delta a = a_t - a_{t-1},\ \ \Delta^2 a = a_t - 2a_{t-1} + a_{t-2}
$$

computed over all 8 action dims. It reads the commanded triple
(`_cmd_actions`, `_prev_cmd_actions`, `_prev_prev_cmd_actions`), not the delayed/applied triple,
because the actor cannot observe control-action latency. With control-delay DR off
(`control_delay_steps = (0, 0)`, the default) the two triples are identical.

### 5.4 `bias_ema_penalty`

`sum_i w_i * bias_ema_i^2` over the 3-channel `env._bias_ema` (roll, pitch, wrapped heading
error), with `w` preallocated from `cfg.bias_weights`. It penalizes a sustained per-env offset
that the per-step tracking reward cannot see. The EMA update
`bias_ema = a*bias_ema + (1-a)*err` in `_get_rewards` is gated on the same
`k_bias != 0` condition, so `k_bias = 0` freezes `_bias_ema` at 0. The EMA is ungated (no error
magnitude threshold), unlike the leaky integral of §7. With `use_bias_ema_obs = True` (the
default) `_bias_ema` is also appended to the policy observation (observation 69D -> 72D,
`apply_bias_ema_obs` in `config.py`), which requires a nonzero `k_bias`.

### 5.5 `sstv` (roll/pitch angular-rate penalty)

`ss_window_rp_tv_l1`: `mean(abs(root_ang_vel_b[:, :2]))` masked to environments whose command
step counter is at least `sstv_start_step` (125 steps = 2.5 s at 50 Hz), i.e. after the
command has settled. It is registered as an extra term named `sstv` only when `k_sstv != 0`
(default `0.0`, paper teacher `-5.0`). The DORAEMON success return excludes this term (§8).

### 5.6 Joint1 anti-drift is constraint-side

There is no reward-side joint1 centering term. Joint1 is a continuous-rotation motor with no
PhysX position limit; anti-drift is handled by the `joint1_pos` constraint and the optional
`joint1_cumulative` term (see [constraints.md](constraints.md)).

---

## 6. Error buffers and `dt` scaling

### 6.1 `_compute_ang_errors`

`_compute_ang_errors` (`albc_env.py`) runs once per step at the top of `_get_rewards`:

```python
roll, pitch, yaw = self._euler_cache
raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
self._att_rp_err = torch.atan2(torch.sin(raw), torch.cos(raw))        # wrapped roll/pitch error
yaw_raw = self._ang_cmd[:, 2] - yaw
self._yaw_err = torch.atan2(torch.sin(yaw_raw), torch.cos(yaw_raw))   # wrapped heading error
```

`_ang_cmd` is `[roll_cmd, pitch_cmd, yaw_cmd]`, with `yaw_cmd` a world-frame heading in rad.
All three errors are wrapped into $(-\pi, \pi]$, so a heading target 359 degrees away reads as
a 1 degree error. The same wrap runs on reset against the fresh post-reset pose, and
`_error_integral` and `_bias_ema` are zeroed there.

### 6.2 `dt` scaling

`RewardManager.compute()` applies two structurally identical loops, one over `_BUILTIN_TERMS`
and one over `cfg.extra_terms` (plus `sstv`):

```python
scaled = func(robot, env) * weight * dt
self._buf += scaled
self._episode_sums[name] += scaled
```

`step_dt` is inherited from Isaac Lab's `DirectRLEnv` (`sim.dt * decimation = 0.02 s`).
`termination_penalty` is added after `compute()` returns and is not `dt`-scaled.

---

## 7. Integral gate (observation, not reward)

`integral_gated = True` gates the leaky integral `_error_integral` that feeds the 3D integral
channel of the policy observation (never the reward sum). The per-axis gate threshold is
`integral_gate_threshold = (0.10, 0.10, 0.10)` rad in `config.py`: the integral accumulates
only while `|err|` is below it. It is a separate field, decoupled from `reward.*.sigma`, so
retuning a tracking sigma does not retune the gate.

---

## 8. DORAEMON success feedback

Accumulated episode return is the binary success signal for the DR curriculum:

1. Every step, `_episode_return_accum += reward`, minus the `sstv` term when it is active
   (`Curriculum/return_total` logs the return including `sstv`).
2. On reset, `success = (returns >= doraemon.cfg.performance_lb)` is computed in
   `_log_and_reset_rewards` and passed to `doraemon.record_episodes(...)`.
3. Episodes with `episode_length_buf == 0` (the initial `env.reset()`) are skipped.

`performance_lb` is 250.0 in the base config (`DoraemonCfg(enable=True, kl_ub=0.12,
performance_lb=250.0, step_interval=250)`), 200.0 in the `-SimToReal-v0` task
(`config_simtoreal.py`), and the paper teacher launch overrides it to `-20.0` with
`step_interval=1000000`. See [domain-randomization-and-doraemon.md](domain-randomization-and-doraemon.md).

---

## 9. Logging

On reset, `RewardManager.reset(env_ids)` returns the mean over the resetting envs of each
term's episode-summed, `dt`-scaled, signed contribution. `_collect_episode_metrics` divides
each by `max_episode_length_s` and logs `Reward/<name>`:

`Reward/att_rp`, `Reward/yaw`, `Reward/torque`, `Reward/thruster`, `Reward/smoothness`,
`Reward/bias`, plus `Reward/sstv` when `k_sstv != 0` (and any `extra_terms`), and the sum
`Reward/total`.

The denominator is the fixed `max_episode_length_s`, not the actual episode length, so an
episode that terminates early shows a smaller value purely from fewer accumulated steps.
Tracking error metrics are logged separately, e.g. `Track/att/roll_err_deg`,
`Track/att/pitch_err_deg`, `Track/yaw/err_deg`.

---

## 10. Tests

`tests/test_rewards.py` (repo-root `tests/`) imports `rewards.py` directly and uses
`SimpleNamespace` env stand-ins. It pins: kernel peak at zero error for `att_rp` and `yaw`,
roll weighted more than pitch, `joint_torque` as mean square, the thruster action slice
(arm dims excluded), `action_smoothness` zero for constant actions and reading the commanded
triple, `bias_ema_penalty` per-axis weighting and the preallocated `_bias_w`, the
extra-terms registry path through `compute()`, and `sstv` off by default and `-5.0 * mean(|p|,|q|) * dt` when on.
It does not exercise the tanh/arctan branches or `RewardManager.reset()`.

---

## Source files

- `constrained_albc/envs/main/mdp/rewards.py`: `TrackingTermCfg`, `RewardTermCfg`, `ALBCRewardCfg`, `_exp_quad_saturating`, the term functions, `RewardManager`
- `constrained_albc/envs/main/config.py`: `reward` override, `integral_gate_threshold`, `yaw_cmd_range`, `use_bias_ema_obs`, `doraemon`
- `constrained_albc/envs/main/albc_env.py`: `_compute_ang_errors`, `_get_rewards`, `_collect_episode_metrics`, `_log_and_reset_rewards`
- `scripts/paper/train_teacher.sh`: the paper teacher's reward overrides
- `tests/test_rewards.py`
