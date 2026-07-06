# Reward System (`envs/main`)

> **Scope**: The full reward computation of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — the shared
> tracking kernel, the seven weighted terms that `RewardManager` sums each step,
> the error buffers in `albc_env.py` that feed them, and the config override that
> turns the shipped reward into what actually runs. This is the attitude-only
> ALBC env (roll/pitch + yaw-rate command, no linear-velocity command); the reward
> is `dt`-scaled and split into tracking rewards (positive) and penalties
> (negative-weighted).
>
> This is a code-level reference verified against disk. It is the **reward-side
> companion** to `action-pipeline.md` (the 8D action path that
> `thruster_energy` / `action_smoothness` penalize) and
> `main-network-architecture.md` (encoder / actor / critic, the ConstraintTRPO
> update, and the cost-critic constraints that are a *separate* channel from these
> reward terms). Where a topic (constraints, DORAEMON curriculum, action clamps)
> belongs to those documents it is linked, not duplicated.
>
> **Two channels, do not conflate.** This document covers the **scalar reward**
> summed by `RewardManager`. The **per-constraint costs** (`compute_all_costs`,
> `mdp/constraints.py`) that drive the ConstraintTRPO+IPO barrier are a distinct
> signal — see `main-network-architecture.md` §4–5. The two share the error
> buffers (§6) but nothing else.

---

## 1. Overview

The reward for one control step is a **`dt`-scaled weighted sum of seven terms**.
`RewardManager.compute()` (`rewards.py:208-227`) builds the sum; every term is
multiplied by its per-second weight and by `dt = step_dt = 0.02 s` before being
added, so the reported `k` values are per-second and the effective per-step
contribution is `k * 0.02` (§6, §7).

```
_get_rewards()                                          (albc_env.py:1009)
  1. _compute_ang_errors()          -> _att_rp_err, _yaw_rate_err   (albc_env.py:1000-1007)
  2. leaky integral update  (OBS, not reward; gated by reward sigma) (albc_env.py:1019-1038)
  3. bias-EMA update        (only if k_bias != 0)                    (albc_env.py:1042-1052)
  4. reward = RewardManager.compute(robot, dt=step_dt, env)         (albc_env.py:1054-1058)
       for name, weight, value in terms:                            (rewards.py:222)
           scaled   = value * weight * dt
           reward  += scaled
           episode_sums[name] += scaled
  5. reward += reset_terminated * termination_penalty  (if != 0; NOT dt-scaled) (albc_env.py:1061-1062)
  6. constraint costs -> extras["costs"]   (separate channel)       (albc_env.py:1065-1066)
  7. _episode_return_accum += reward        (DORAEMON success feed)  (albc_env.py:1074-1075)
```

The seven terms (`RewardManager._NAMES`, `rewards.py:199`) split into three
**tracking rewards** (positive, built on the shared exp-kernel of §2) and four
**penalties** (non-negative magnitudes carried into the sum by a negative weight):

| Class | Terms |
|---|---|
| Tracking (reward) | `att_rp`, `yaw_vel` |
| Penalty | `torque`, `thruster`, `smoothness`, `bias`, `joint1_center` |

`att_rp` and `yaw_vel` are the only two tracking terms actually summed. A third
tracking function, `lin_vel_tracking`, exists in the file but is **not** wired
into `RewardManager` (§4.3, §9) — it is dead in this attitude-only env. An eighth
reward contribution, `termination_penalty`, is applied outside `compute()` and is
**not** one of the seven tracked/logged terms (§5.5, §9).

---

## 2. The shared tracking kernel — `_exp_quad_saturating`

All three tracking functions call one kernel, `_exp_quad_saturating(err_sq,
err_norm, term)` (`rewards.py:97-117`), a pure function that combines a positive
Gaussian bump with up to three penalty shapes:

```
exp_term = exp(-err_sq / (2 * sigma^2))                                    (rewards.py:109)
penalty  = quad_ratio * err_sq + lin_ratio * err_norm                      (rewards.py:110)
if tanh_coef  > 0:  penalty += tanh_coef  * tanh_eps  * tanh(err_norm/tanh_eps)              (rewards.py:111-112)
if arctan_coef> 0:  penalty += arctan_coef* arctan_eps* (2/pi)*atan(err_norm/arctan_eps)     (rewards.py:113-116)
return exp_term - penalty                                                   (rewards.py:117)
```

$$
r_{\text{kernel}} = \underbrace{\exp\!\left(-\frac{e^2}{2\sigma^2}\right)}_{\text{reward, }(0,1]} \;-\; \underbrace{q_{\text{quad}}\, e^2}_{\text{quadratic}} \;-\; \underbrace{q_{\text{lin}}\, |e|}_{\text{linear (default 0)}} \;-\; \underbrace{c_{\tanh}\,\epsilon_{\tanh}\tanh\!\left(\tfrac{|e|}{\epsilon_{\tanh}}\right)}_{\text{tanh, only if } c_{\tanh}>0} \;-\; \underbrace{c_{\text{atan}}\,\epsilon_{\text{atan}}\tfrac{2}{\pi}\arctan\!\left(\tfrac{|e|}{\epsilon_{\text{atan}}}\right)}_{\text{arctan, only if } c_{\text{atan}}>0}
$$

Here $e^2$ is `err_sq` (the argument, possibly a *weighted* sum of squares — §4.1)
and $|e|$ is `err_norm` (a Manhattan-weighted or true-Euclidean magnitude
depending on caller — §4). The per-term weight `k` is **not** applied inside the
kernel (no `term.k` reference exists in `rewards.py:97-117`); it is multiplied in
later by `compute()` (§6). The `TrackingTermCfg` docstring formula
`r = k * (exp(...) - ...)` (`rewards.py:49`) folds in a `k` the function never
applies — that `k` is the caller's subsequent multiply.

### 2.1 Gradient intuition, per shape

| Shape | Value at `e=0` | Gradient at `e=0` | Tail | Role |
|---|---|---|---|---|
| `exp(-e^2/2s^2)` | `1` (max) | `0` | saturates to 0 | positive reward; slope peaks at `|e|=sigma`, vanishes near 0 |
| `quad_ratio * e^2` | `0` | `0` | grows unbounded | penalty that dominates for large error |
| `lin_ratio * |e|` | `0` | `lin_ratio * sign(e)` (constant) | grows linearly | constant force even near 0 — **but default 0, see §2.2** |
| `tanh` penalty | `0` | `c_tanh` (finite) | sech²-decay (exponential) | smoothed near-0 force, bounded tail |
| `arctan` penalty | `0` | `c_atan * 2/pi ≈ 0.637 c_atan` | 1/(1+x²)-decay (heavier) | smoothed near-0 force, Cauchy-like tail |

The exp term is positive in $(0,1]$, maxed at $e=0$ (pinned by
`test_*_peaks_at_zero`, `tests/test_rewards.py:113,124,139`); its slope
$-\tfrac{e}{\sigma^2}\exp(-e^2/2\sigma^2)$ peaks at $|e|=\sigma$ and collapses
toward 0 near $e=0$. Both the exp and quadratic gradients therefore **vanish as
`e -> 0`**, which the module docstring names as the "SS-error dead zone"
(`rewards.py:14-17`): once the policy is inside roughly $\sigma$, neither term
still rewards pushing the error to zero. The saturating tanh/arctan penalties (and
the disabled linear penalty) exist to restore a finite non-vanishing gradient at
$e=0$ without the unbounded-at-infinity force of the raw linear term.

The kernel returns `exp_term - penalty` and **can go negative** if the penalties
exceed the exp bump; the tracking terms are only tested for peak-at-1 and
monotonic-decrease, not non-negativity (§10).

### 2.2 The `lin_ratio` dead-zone gotcha and the docstring contradiction

`lin_ratio` defaults to `0.0` (`rewards.py:59`, comment `# linear penalty ratio
(disabled: caused dead zone)`) and is **never set nonzero anywhere** — none of the
three `TrackingTermCfg` constructions (`rewards.py:70,72,73`) nor the config
override (`config.py:423`) passes it. So the linear penalty is inert on all three
tracking terms in the shipped config.

This is a genuine self-contradiction inside `rewards.py`: the module docstring
frames the linear term as *"the critical fix for SS error tolerance … a constant
downward force on |e|, ensuring the policy keeps reducing SS error all the way to
zero"* (`rewards.py:14-17`), while the field-level comment (`rewards.py:59`) says
it was disabled *because* it caused a dead zone. Both statements are in the file;
no resolving comment exists. As shipped, the SS-error dead zone the docstring
warns about is present — mitigated only on `yaw_vel` by its tanh penalty (§2.3),
not on `att_rp` at all.

### 2.3 tanh vs arctan: convention, not code-enforced

The two saturating blocks are **independent `if` statements** (`rewards.py:111`
and `:113`); nothing prevents both firing if both coefficients were positive — they
would stack additively. The docstring's *"only one of tanh/arctan at a time"*
(`rewards.py:51`) is a config-authoring convention, not a code invariant. In the
shipped config only `tanh_coef` is ever nonzero, and only on `yaw_vel`
(`config.py:423`); `arctan_coef` is never set (§3, §4).

---

## 3. Term-by-term catalog

`RewardManager._NAMES = ["att_rp", "yaw_vel", "torque", "thruster",
"smoothness", "bias", "joint1_center"]` (`rewards.py:199`) — seven terms,
assembled 1:1 from the `terms` list in `compute()` (`rewards.py:213-221`).

| # | Name | Function (`rewards.py`) | Formula (pre-weight, pre-dt) | Weight field | Dataclass default | Shipped value | On? |
|---|---|---|---|---|---|---|---|
| 1 | `att_rp` | `att_rp_tracking` (128-138) | `exp(-e_w²/2σ²) − q·e_w²` where `e_w² = 1.5·roll² + pitch²` | `att_rp.k` | `k=9.0, σ=0.10, quad=0.833` (70) | unchanged | **ON** (reward) |
| 2 | `yaw_vel` | `yaw_vel_tracking` (141-144) | `exp(-e²/2σ²) − q·e² − tanh_coef·ε·tanh(|e|/ε)` | `yaw_vel.k` | `k=3.5, σ=0.10, quad=1.0` (73) | **override**: `+tanh_coef=0.3, tanh_eps=0.10` (config.py:423) | **ON** (reward + tanh penalty) |
| 3 | `torque` | `joint_torque` (147-149) | `mean(applied_torque[albc_joints]²)` | `k_tau` | `-0.01` (74) | unchanged | ON |
| 4 | `thruster` | `thruster_energy` (152-154) | `mean(actions[:, 2:]²)` (6 thruster dims) | `k_thr` | `-0.35` (75) | unchanged | ON |
| 5 | `smoothness` | `action_smoothness` (157-161) | `mean(da²) + mean(d2a²)` over all 8 dims | `k_s` | `-0.1` (76) | unchanged | ON |
| 6 | `bias` | `bias_ema_penalty` (164-172) | `Σᵢ wᵢ · bias_emaᵢ²` (3D roll/pitch/yaw-rate) | `k_bias` | `0.0` — disabled (88) | **override**: `-2.0` (config.py:429) | **ON** (override) |
| 7 | `joint1_center` | `joint1_centering_penalty` (175-190) | `wrap(θ₁)²`, `wrap = atan2(sin,cos)` | `k_joint1_center` | `0.0` — disabled (83) | unchanged | **OFF** |

### 3.1 Shipped effective-weight table (definitive)

Exactly **two of twelve** `ALBCRewardCfg` fields are touched by the shipped config
(`config.py:422-430`): `yaw_vel` (gains a tanh penalty) and `k_bias` (turned on at
`-2.0`). Everything else runs off the `rewards.py` dataclass defaults.

| Field | Dataclass default (`rewards.py`) | Config override (`config.py:422-430`) | Shipped effective value | Overridden? |
|---|---|---|---|---|
| `att_rp` | `k=9.0, σ=0.10, quad_ratio=0.833` (70) | — | `k=9.0, σ=0.10, quad=0.833, lin=0, tanh=0, arctan=0` | No |
| `att_roll_weight` | `1.5` (71) | — | `1.5` | No |
| `lin_vel` | `k=4.0, σ=0.10, quad=1.0` (72) | — | same, **but term unused** (§4.3) | No (moot) |
| `yaw_vel` | `k=3.5, σ=0.10, quad=1.0` (73) | `+tanh_coef=0.3, tanh_eps=0.10` (423) | `k=3.5, σ=0.10, quad=1.0, tanh=0.3, tanh_eps=0.10` | **Yes** |
| `k_tau` | `-0.01` (74) | — | `-0.01` | No |
| `k_thr` | `-0.35` (75) | — | `-0.35` | No |
| `k_s` | `-0.1` (76) | — | `-0.1` | No |
| `k_joint1_center` | `0.0` (83) | — | `0.0` (disabled) | No |
| `termination_penalty` | `0.0` (84) | — | `0.0` (disabled) | No |
| `k_bias` | `0.0` (88) | `-2.0` (429) | `-2.0` (term ON) | **Yes** |
| `bias_ema_alpha` | `0.99` (89) | — | `0.99` (~100-step / 2 s window at 50 Hz) | No |
| `bias_weights` | `(1.5, 1.0, 1.0)` (91) | — | `(1.5, 1.0, 1.0)` | No |

The `yaw_vel` override is a **full reconstruction** of the nested
`TrackingTermCfg`, not a partial patch — `k`, `sigma`, `quad_ratio` are restated at
their default values, so the only *substantive* change is turning on the tanh
term. `att_rp`, `lin_vel`, `lin_ratio`, and `arctan_coef` are all untouched and
keep their dataclass defaults.

### 3.2 Effective per-step magnitude at zero error

With `dt = 0.02` (§6), at zero error the tracking kernel is `1.0`, so `att_rp`
contributes `9.0 * 0.02 * 1 = 0.18` per step and `yaw_vel` contributes
`3.5 * 0.02 * 1 = 0.07` per step (its tanh penalty is 0 at exactly $e=0$ since
$\tanh(0)=0$). Over a 30 s episode at 50 Hz (`episode_length_s=30.0`,
`config.py:334`; 1500 steps), `att_rp` alone at zero error every step would
accumulate `0.18 * 1500 = 270` — consistent with the DORAEMON
`performance_lb=250.0` calibration (§8).

---

## 4. The three tracking terms

### 4.1 `att_rp_tracking` — roll-weighted, Manhattan norm for saturating

`att_rp_tracking` (`rewards.py:128-138`) forms two error aggregates and hands them
to the kernel:

```python
rp_err    = env._att_rp_err                                             # (N, 2): [roll_err, pitch_err]
err_sq    = cfg.att_roll_weight * rp_err[:, 0].pow(2) + rp_err[:, 1].pow(2)     # weighted sum of squares
err_abs_w = cfg.att_roll_weight * rp_err[:, 0].abs() + rp_err[:, 1].abs()       # Manhattan (L1) weighted
return _exp_quad_saturating(err_sq, err_abs_w, cfg.att_rp)
```

$$
e_w^2 = w_{\text{roll}}\, e_{\text{roll}}^2 + e_{\text{pitch}}^2, \qquad |e_w| = w_{\text{roll}}\, |e_{\text{roll}}| + |e_{\text{pitch}}|
$$

`err_sq` feeds the exp and quadratic terms; `err_abs_w` is a Manhattan (L1)
weighted sum of absolute values — **not** a Euclidean `sqrt(err_sq)` — and feeds
`err_norm`, i.e. the (disabled-here) linear/tanh/arctan penalties. Roll is
up-weighted by `att_roll_weight = 1.5` (`rewards.py:71`) in *both* aggregates, so
roll error costs more per unit than pitch (pinned by
`test_att_rp_roll_weighted_more_than_pitch`, `tests/test_rewards.py:131`). Since
neither saturating nor linear penalty is active on `att_rp` in the shipped config
(§3.1), `att_rp` runs purely on `exp − quad_ratio·e_w²`.

**Why 1.5x on roll.** The weight is grounded in the shipped Thruster Allocation
Matrix, not a lone heuristic: `_BASE_ALLOCATION_MATRIX` (`config.py:77-84`, sourced
from the ALBC ROS control package `config/TAM.yaml`) gives the roll (Mx) row a
moment-arm coefficient of `0.007` (`config.py:81`) versus the pitch (My) row's
vertical-pair coefficient `0.145` (`config.py:82`) — a ~20x smaller roll moment
arm. A second corroboration is the payload-DR comment `4 x 50 N x 0.007 m = 1.4 Nm`
of roll authority (`config.py:207-212`). The roll axis is genuinely weakly
actuated, so its tracking error is upweighted before penalization
(comment `rewards.py:71`: "weak TAM actuation: 0.007m vs pitch 0.145m").

### 4.2 `yaw_vel_tracking` — scalar, the only saturating term in the shipped config

`yaw_vel_tracking` (`rewards.py:141-144`) tracks a scalar yaw *rate* error (not yaw
angle):

```python
err = env._yaw_rate_err
return _exp_quad_saturating(err.pow(2), err.abs(), env.cfg.reward.yaw_vel)
```

No weighting: `err_sq = err²`, `err_norm = |err|`. The dataclass default
(`rewards.py:73`) has no saturating term, but the shipped config
(`config.py:423`) overrides `yaw_vel` to
`TrackingTermCfg(k=3.5, sigma=0.10, quad_ratio=1.0, tanh_coef=0.3, tanh_eps=0.10)`
— identical `k`/`sigma`/`quad_ratio`, plus the tanh penalty. **`yaw_vel` is the
only tracking term carrying an active saturating penalty**; from that penalty
alone the gradient at zero error is $c_{\tanh}=0.3$. This partially fills the
dead zone (§2.2) on yaw rate but not on roll/pitch.

### 4.3 `lin_vel_tracking` — DEFINED but structurally DEAD

`lin_vel_tracking` (`rewards.py:121-125`) is the only tracking function using a
true Euclidean norm (`err_norm = sqrt(err_sq)`, clamped at `1e-12` to avoid a NaN
gradient through `sqrt` at exactly zero). It is marked `# UNUSED in attitude_only
(kept for cfg compatibility; not in RewardManager).` (`rewards.py:120`) and is
**absent** from both `_NAMES` (`rewards.py:199`) and the `terms` list
(`rewards.py:213-221`). The `ALBCRewardCfg.lin_vel` field (`rewards.py:72`) exists
only for dataclass/config shape compatibility with the legacy full-DOF env.

This is not merely dormant-but-safe — it would **crash** if invoked against a live
`ALBCEnv` in main: `env._lin_vel_err` is never assigned anywhere in
`envs/main/albc_env.py`, so a call would raise `AttributeError`. The only caller in
the repo is the unit test `test_lin_vel_tracking_peaks_at_zero_error`
(`tests/test_rewards.py:113`), which supplies `_lin_vel_err` on a `SimpleNamespace`
stand-in. In the sibling `envs/full_dof/mdp/rewards.py` (a distinct hand-forked
file) `lin_vel_tracking` **is** wired into that variant's `RewardManager` — so the
dead-code status is specific to main.

The module docstring at `rewards.py:6,20` still lists `r_lin` as a summed term; it
is stale (§9).

---

## 5. The penalty terms

All four active penalties return **non-negative magnitudes**; the negative sign
lives entirely in the weight (`k_tau`, `k_thr`, `k_s`, `k_bias`). Every penalty is
`dt`-scaled identically to the tracking terms (§6) — there is one scaling point for
all seven terms.

### 5.1 `joint_torque` — post-clamp applied torque

`joint_torque` (`rewards.py:147-149`): `mean(applied_torque[albc_joints]²)`. It
reads `robot.data.applied_torque` — Isaac Lab's **post-actuator-model, post-clamp**
torque actually applied, not the policy's raw commanded action (inline comment
`rewards.py:148`: "post-clamp applied torque"). A reader assuming this penalizes
raw action magnitude would be wrong: it penalizes the physically realized torque
after actuator dynamics, effort-limit clamping, and DR-randomized effort-limit
scaling (`action-pipeline.md` §4.2). Joint fault injection that reduces the effort
limit can therefore *lower* this penalty even for the same commanded action.

### 5.2 `thruster_energy` — 6 thruster dims only

`thruster_energy` (`rewards.py:152-154`): `mean(env._actions[:, 2:]²)`. The action
layout is `[2D arm delta, 6D thruster]` (`action-pipeline.md` §2), so slicing
`[:, 2:]` takes the 6 thruster dims (indices 2-7) and **excludes the 2 arm dims**.
Pinned by `test_thruster_energy_uses_thruster_action_slice`
(`tests/test_rewards.py:154`): an 8D action `[9,9,1,0,0,0,0,0]` yields
`mean([1,0,0,0,0,0]²) = 1/6`, unaffected by the large arm values. Only
`joint_torque` (§5.1, reading physical torque) captures any arm-side energy cost.

### 5.3 `action_smoothness` — first + second order over all 8 dims

`action_smoothness` (`rewards.py:157-161`): `mean(da²) + mean(d2a²)` where
`da = a_t − a_{t-1}` (first-order, action-velocity) and
`d2a = a_t − 2a_{t-1} + a_{t-2}` (second-order, jerk-like). Unlike `thruster_energy`
this is computed over **all 8 action dims**. It is zero only at true steady state
(prev == prev_prev == current), not merely at zero action
(`test_action_smoothness_zero_when_constant`, `tests/test_rewards.py:161`). The
three action buffers are rotated at the top of `_pre_physics_step`
(`action-pipeline.md` §3.3) and zeroed together on reset, so the first post-reset
step's `da`/`d2a` are measured against zero, not stale cross-episode history.

### 5.4 `bias_ema_penalty` — sustained-offset penalty with env-side coupling

`bias_ema_penalty` (`rewards.py:164-172`): `Σᵢ wᵢ · bias_emaᵢ²` over the 3-channel
`env._bias_ema` (roll, pitch, yaw-rate), with per-axis weights
`env._reward_manager._bias_w` preallocated once from `cfg.bias_weights`
(`rewards.py:206`; default `(1.5, 1.0, 1.0)`, `rewards.py:91`). It penalizes a
sustained per-env tracking offset that per-step tracking reward cannot see (roll
is weighted higher, matching its weak authority). Off by dataclass default
(`k_bias=0.0`) but **ON in the shipped config** at `k_bias=-2.0`
(`config.py:429`).

**The env-side coupling (a two-file gotcha).** The EMA buffer update in
`albc_env.py:1042-1052` is itself gated on `if self.cfg.reward.k_bias != 0.0:`, so
turning `k_bias` on/off flips two coupled things in two different files: (a) the
reward term's weight becomes nonzero (`rewards.py:219`), and (b) the EMA update
loop `bias_ema = α·bias_ema + (1−α)·err3` starts running. When `k_bias == 0`, the
update is skipped entirely and `_bias_ema` stays frozen at its reset value `0`
(not decaying) — so `bias_ema_penalty` would return `0` even though the function
still executes every step. In the shipped config the update runs every step
(`α = 0.99`, a ~100-step / 2 s time constant at 50 Hz, so it tracks sustained
offset, not per-step noise). Unlike the leaky integrator (§7), this EMA update is
**ungated** — it always incorporates the current error, no magnitude threshold.

### 5.5 `joint1_centering_penalty` — default-off, angle-wrapped

`joint1_centering_penalty` (`rewards.py:175-190`): `wrap(θ₁)²` with
`wrap = atan2(sin θ₁, cos θ₁)`, reading only joint1 (`env._albc_joint_ids[0]`,
`rewards.py:188`). Joint1 is a continuous-rotation motor with no PhysX position
limit, driven by a pure delta-integrator (`action-pipeline.md` §4.1); nothing pulls
it back to nominal, so sim-to-real micro-bias would drift it monotonically on the
real robot. This term supplies the missing restoring gradient. The wrap ensures a
full revolution ($\theta_1 = 2\pi$, physically identical to 0) is **not** penalized
as a large error — only the genuine angular distance is
(`test_joint1_centering_wraps_full_revolution`, `tests/test_rewards.py:222`).

It is **OFF by default** (`k_joint1_center=0.0`, `rewards.py:83`, comment:
"byte-identical to runs without this term") and never overridden by the shipped
config. Note it still **executes every step** (the `atan2/sin/cos` runs) and
contributes exactly `0.0` — so `Reward/joint1_center` always logs `0.0`, which
reads as "disabled," not "measured zero." A constraint-side joint1 anti-drift
mechanism (`joint1_constraint_arm`, `main-network-architecture.md` §5.1) is a
separate, mutually-exclusive-by-convention lever from this reward-side term.

---

## 6. Error buffers, the reward call site, and `dt` scaling

### 6.1 `_compute_ang_errors` — the wrap

`_compute_ang_errors` (`albc_env.py:1000-1007`) runs once per step at the top of
`_get_rewards`, before the integral and bias updates:

```python
roll, pitch, _ = self._euler_cache
raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
self._att_rp_err   = torch.atan2(torch.sin(raw), torch.cos(raw))         # wrapped roll/pitch error
self._yaw_rate_err = self._ang_cmd[:, 2] - self._robot.data.root_ang_vel_b[:, 2]
```

`_ang_cmd` layout is `[roll_cmd, pitch_cmd, yaw_rate_cmd]` (comment
`albc_env.py:303`, tensor allocated `:304`). The roll/pitch error is **wrapped**
via `atan2(sin, cos)` into $(-\pi, \pi]$: a naive subtraction can return `+359°`
when the true angular distance is `−1°`, which would blow up `err²` in the kernel
and corrupt the integral/EMA accumulators. `_yaw_rate_err` is **not** wrapped — it
is a rate (rad/s), not an angle, so there is no periodicity to fold. `_euler_cache`
is refreshed once per step in `_get_dones` (`albc_env.py:1230`) and again at the
end of `_reset_idx` (`:1268`) so a same-step reset sees a valid post-reset pose.

The identical wrap-and-subtract is duplicated on reset in `_reset_task_and_state`
(`albc_env.py:1439-1444`) against the fresh post-reset pose, so the first
observation/reward after a reset is not stale; `_error_integral` and `_bias_ema`
are zeroed immediately after (`:1446-1447`). (The buffer `self._ang_err`, written
here at `:1006-1007`, is vestigial write-only state — never read anywhere in the
env; the reward functions read `_att_rp_err`/`_yaw_rate_err` directly.)

### 6.2 Reward call site and `dt` scaling

`RewardManager` is constructed once at init (`albc_env.py:255`) and called with
`dt=self.step_dt` (`albc_env.py:1054-1058`). Inside `compute()`
(`rewards.py:222-225`):

```python
for name, weight, value in terms:
    scaled = value * weight * dt
    self._buf            += scaled
    self._episode_sums[name] += scaled
```

`step_dt` is **inherited from Isaac Lab's base `DirectRLEnv` class** (framework
level, computed as `sim.dt * decimation`); `albc_env.py` never assigns it, only
reads it (e.g. `:101`). With `sim.dt = 0.005` (`config.py:356`) and
`decimation = 4` (`config.py:335`), `step_dt = 0.02 s` (50 Hz). So the reported
`k` values are **per-second**; effective per-step is `k * 0.02` (§3.2). Every term
— tracking and penalty alike — is scaled at this single point; the only reward
contribution exempt is `termination_penalty`, added *after* `compute()` returns
(`albc_env.py:1061-1062`, no `* dt`), which is why it is not one of the seven
tracked terms.

---

## 7. The reward-sigma / integral-gate coupling

This is a configuration coupling, not a reward term. `integral_gated=True`
(`config.py:347`) gates the **observation** integral `_error_integral` — a leaky
integrator feeding the 3D integral channel of the 69D observation
(`main-network-architecture.md` §2.1), never the reward sum. But its gate
threshold is literally the **reward kernel's sigma**: `_integral_gate_sigmas` is
pre-built once at `__init__` from `[cfg.reward.att_rp.sigma,
cfg.reward.att_rp.sigma, cfg.reward.yaw_vel.sigma]` (`albc_env.py:164-173`), and
each step `gate = (err_stack.abs() < self._integral_gate_sigmas).float()`
accumulates only while the per-axis error is inside the reward's Gaussian width
(`albc_env.py:1029-1038`).

The two systems (tracking reward vs integral observation) are decoupled in effect
but coupled in configuration through this one shared `sigma` value. Consequence:
retuning `reward.att_rp.sigma` or `reward.yaw_vel.sigma` silently changes the
integral-observation gating too. In the shipped config all three gate thresholds
are `0.10 rad ≈ 5.7°` (`att_rp.sigma` and `yaw_vel.sigma` both `0.10`). The comment
explaining this lives at `albc_env.py:164-165`, not next to the `sigma` field in
`rewards.py`, so the dependency is easy to miss.

---

## 8. Config and experiment context

### 8.1 `performance_lb` and DORAEMON success feedback

The reward does not only shape the policy — its accumulated episode return is the
**binary success signal** for the DORAEMON DR curriculum (the domain-randomization
reference; `DoraemonCfg` in marinelab). Every step
`_episode_return_accum += reward` (`albc_env.py:1075`); on reset, inside
`_log_and_reset_rewards` (`albc_env.py:1276-1287`),
`success = (returns >= performance_lb).float()` is fed to
`doraemon.record_episodes(...)`. Episodes with `episode_length_buf == 0` (the
initial `env.reset()` before any step) are filtered out (`:1277-1279`) so they do
not enter the buffer as fake zero-return failures.

The shipped `doraemon` cfg (`config.py:479`) is
`DoraemonCfg(enable=True, kl_ub=0.12, performance_lb=250.0, step_interval=250)`; of
these only `kl_ub` and `performance_lb` are genuine overrides of the marinelab
`DoraemonCfg` dataclass defaults (`kl_ub=0.5`, `performance_lb=80.0`;
`enable=True`/`step_interval=250` already match the defaults). The calibration
history (`config.py:466-478`, **experiment-history commentary, not a mechanism**)
records that `performance_lb` was raised `68.0 -> 250.0` after a recon run whose
episode-return distribution was min=81.9 / p5=227 / p25=250 / median=264 / p95=291
(n=2000): the old `lb=68` sat below the minimum return, so success was always 1 and
the feasibility constraint was inert. `lb=250` (p25) puts starting success ~0.65,
live again but below median so a reward plateau cannot drag it to 0.

### 8.2 The `r13` `k_bias=-2.0` rationale (experiment history, not mechanism)

The `k_bias=-2.0` override carries an inline comment (`config.py:424-428`) that is
**experiment-history commentary**, not a code fact: it records that a prior
`r12_baseline` halved the bias weight to `-1.0` (with `latent=16`) and regressed to
"rank #7" (hard-roll 1.26) versus the full-strength `r11_emabias` variant
(`k_bias=-2.0`, hard-roll 0.62, "rank #1", "strongest single intervention across 24
runs"). `r13` restores full strength. None of the rank / metric claims are
independently verifiable from `config.py` or `rewards.py` — treat them as
provenance for the shipped value, not as verified facts.

---

## 9. Gotchas

Consolidated traps, each verified against disk. Several are documentation-vs-code
mismatches that are stale docs, not functional bugs — the running code path is
internally consistent (7 names, 7 terms, 7 episode-sum keys).

| # | Gotcha | Reality | Cite |
|---|---|---|---|
| 1 | `lin_vel_tracking` looks live (exported, has `k=4.0`) | Unused in main; absent from `_NAMES`/`terms`; would **crash** (`_lin_vel_err` unassigned) if invoked on a live env | `rewards.py:120-125,199,213-221` |
| 2 | Module docstring says the linear term is "the critical fix" for SS error | `lin_ratio=0.0` by default, never overridden — the linear penalty is **inert** on all three terms; the dead zone the docstring warns about is present | `rewards.py:14-17,59` |
| 3 | `k_joint1_center=0.0` "off" | Byte-identical to omitting the term, but it still **executes every step** and logs `Reward/joint1_center = 0.0` (reads as measured-zero) | `rewards.py:83,220` |
| 4 | tanh and arctan look mutually exclusive | Independent `if`s — both would stack if set; exclusivity is a convention. Shipped config activates **tanh only on `yaw_vel`**; `att_rp` has no saturating term | `rewards.py:51,111-116; config.py:423` |
| 5 | Reading `rewards.py` alone, `k_bias=0` reads as "bias off" | Shipped config **overrides `k_bias=-2.0`** (term ON), and the override flips a coupled EMA-buffer update in a *second file* (`albc_env.py`) under the identical `k_bias != 0` guard | `rewards.py:88; config.py:429; albc_env.py:1042` |
| 6 | `k` values look like per-step magnitudes | They are **per-second**; effective per-step is `k * dt` (`* 0.02`), scaled at one point for all 7 terms; `step_dt` is framework-inherited, not defined in `albc_env.py` | `rewards.py:223; config.py:335,356` |
| 7 | Docstrings say "6-term" / list `r = r_att + r_lin + ...` | Actual `terms` list has **7** entries; the docstring's 6 even counts the dead `r_lin`. Stale docs, not a code bug | `rewards.py:6,197,199,213-221` |
| 8 | `joint_torque` penalizes commanded action | It reads **`applied_torque`** — post-actuator, post-clamp physical torque; fault/effort-limit scaling changes it independently of the raw action | `rewards.py:148-149` |
| 9 | `termination_penalty` is a reward term | Applied **outside** `compute()`, **not** `dt`-scaled, and **not** in `_NAMES` — never appears under any `Reward/<name>` key. Off by default, never overridden | `rewards.py:84; albc_env.py:1061-1062` |
| 10 | Retuning `reward.*.sigma` only affects the reward | It **also** retunes the integral-observation gate threshold, which borrows the reward sigma | `albc_env.py:164-173,1029-1038` |
| 11 | `att_roll_weight=1.5` is an unexplained constant | Grounded in the shipped TAM: roll moment arm `0.007 m` vs pitch `0.145 m` (`config.py:81-82`), corroborated by the payload-DR authority comment | `rewards.py:71; config.py:81-82,207-212` |
| 12 | `envs/main/mdp/rewards.py` and `envs/full_dof/...` are one shared module | **Distinct hand-forked files**; `full_dof` wires `lin_vel` in and omits `joint1_center`. A fix in one does not propagate | `rewards.py:199` vs `full_dof/mdp/rewards.py:173,188` |

---

## 10. Testing and logging

### 10.1 Test invariants — `tests/test_rewards.py` (17 tests)

The suite is at repo-root `tests/test_rewards.py` (**not** under the
`constrained_albc/` package), 257 lines. It imports `rewards.py` directly via
`importlib` (bypassing `constrained_albc.__init__`, which would pull in
`isaaclab.sim`) and uses `SimpleNamespace` env stand-ins — it is a **whitebox unit
pin of sign conventions and roll-weighting**, so a refactor cannot silently invert
a reward. It does **not** exercise `RewardManager.compute()` end-to-end.

| Test (`tests/test_rewards.py:line`) | Invariant | Mechanism protected |
|---|---|---|
| `test_lin_vel_tracking_peaks_at_zero_error` (113) | `err=0 -> 1.0`; larger `|err|` -> smaller | exp-kernel monotonicity (dead code, pinned anyway) |
| `test_yaw_vel_tracking_peaks_at_zero` (124) | `err=0 -> 1.0` | `yaw_vel` exp kernel |
| `test_att_rp_roll_weighted_more_than_pitch` (131) | roll-only 0.2 < pitch-only 0.2 reward | `att_roll_weight=1.5` up-weighting |
| `test_att_rp_peaks_at_zero` (139) | zero attitude error -> 1.0 | `att_rp` exp base case |
| `test_joint_torque_nonneg_mean_square` (148) | `[3,4] -> mean(9,16)=12.5` | `mean(tau²)` numeric pin |
| `test_thruster_energy_uses_thruster_action_slice` (154) | `[9,9,1,0..] -> 1/6` (arm excluded) | `[:, 2:]` slice |
| `test_action_smoothness_zero_when_constant` (161) | constant -> 0; jump -> >0 | first+second-order difference |
| `test_bias_ema_uses_preallocated_weights` (175) | `w=[1.5,..], ema=[2,0,..] -> 6.0` | per-axis weighting via `_bias_w` |
| `test_bias_ema_zero_when_no_offset` (183) | all-zero ema -> 0.0 | base case |
| `test_reward_manager_preallocates_bias_w` (188) | `__init__` builds `_bias_w` == `cfg.bias_weights` | perf regression net (no per-step rebuild) |
| `test_joint1_centering_zero_at_nominal` (207) | `θ₁=0 -> 0.0` | centering base case |
| `test_joint1_centering_grows_with_abs_theta1` (212) | `θ₁=0.3 -> 0.09`; `1.0 -> 1.0` | `wrap(θ)²` exactly, monotone |
| `test_joint1_centering_wraps_full_revolution` (222) | `θ₁=2π -> ≈0`; `π+0.1 == −(π−0.1)` | `atan2(sin,cos)` wrap |
| `test_joint1_centering_symmetric_sign` (233) | `+0.5 == −0.5` | sign symmetry |
| `test_joint1_centering_only_reads_joint1` (240) | differing joint2 -> identical | reads `_albc_joint_ids[0]` only |
| `test_joint1_center_disabled_by_default` (249) | `ALBCRewardCfg().k_joint1_center == 0.0` | dataclass default off |
| `test_joint1_center_registered_in_names` (255) | `"joint1_center" in _NAMES` | wired for logging even while disabled |

**Coverage gaps** (whitebox-only): no test drives `RewardManager.compute()`
dt-scaling or the 7-term sum, `RewardManager.reset()`, the tanh/arctan branches
(the shipped `yaw_vel` tanh override is untested at unit level), `lin_ratio > 0`,
or the env-level `k_bias != 0` gating. The `bias_w`/`bias_ema` fixtures use a 6-D
vector (`tests/test_rewards.py:176-177`) — a test-only shape choice, **not**
evidence of a 6-D buffer; the real `_bias_ema` is 3-D (`albc_env.py:316`), matching
the 3-tuple `bias_weights`.

### 10.2 Episode logging — per-term means to wandb/TB

`RewardManager.compute()` accumulates each term's already-`dt`-scaled, already-
signed contribution into `_episode_sums[name]` (`rewards.py:224-225`). On reset,
`RewardManager.reset(env_ids)` (`rewards.py:229-234`) returns
`{name: episode_sums[name][env_ids].mean().item()}` (the **mean across the
resetting envs** of each term's episode-summed reward) and zeroes those envs' sums.

`_collect_episode_metrics` (`albc_env.py:1079-1098`) turns each into a log key:

```python
for name, value in reward_sums.items():
    normalized = value / self.max_episode_length_s          # FIXED denominator, see below
    log[f"Reward/{name}"] = normalized
    total += normalized
log["Reward/total"] = total
```

The emitted keys are exactly `Reward/att_rp`, `Reward/yaw_vel`, `Reward/torque`,
`Reward/thruster`, `Reward/smoothness`, `Reward/bias`, `Reward/joint1_center`
(matching `_NAMES`), plus a derived `Reward/total`. A reader mapping a wandb curve
back to a term should look for the exact tag `Reward/<name>`.

Two normalization nuances worth flagging:

- **Fixed denominator.** `max_episode_length_s` is `cfg.episode_length_s` (a
  constant from the base `DirectRLEnv`), **not** the actual duration of the episode
  that ended. An episode that terminates early shows a *smaller* `Reward/*` value
  purely from accumulating over fewer steps, even at identical per-step density —
  this is fixed-denominator normalization for cross-run comparability, not a true
  per-episode-length average. `_num_resets` is logged alongside
  (`albc_env.py:1090`) so a single-env extreme trajectory can be weighted.
- **`/`-prefix passthrough + a stale-`extras` nuance.** rsl_rl (external
  `rsl_rl_lib-3.1.2`) logs any key containing `/` verbatim and prefixes bare keys
  with `Episode/`; since every key here already has a `/`, all pass through
  unprefixed. `self.extras` is initialized once in `DirectRLEnv.__init__` and never
  cleared, and `self.extras["log"]` is only reassigned when at least one env resets
  — so on a step with no resets rsl_rl re-appends the **stale** last-reset dict into
  its per-iteration `ep_infos` average. The per-iteration `Reward/*` mean is thus
  skewed toward the most recent reset snapshot, not a clean mean over reset events.
  This is an external-library behavior, flagged here for anyone reading the curves.

---

## Source files

- `constrained_albc/envs/main/mdp/rewards.py` — `TrackingTermCfg`, `ALBCRewardCfg`, `_exp_quad_saturating`, the 7 term functions, `RewardManager` (`compute`/`reset`)
- `constrained_albc/envs/main/config.py` — `reward` override (`:422-430`), TAM (`:77-84`), command ranges (`:410-417`), `integral_gated` (`:347`), sim/decimation/episode length (`:334-356`), `doraemon`/`performance_lb` (`:466-479`)
- `constrained_albc/envs/main/albc_env.py` — `_compute_ang_errors` (`:1000-1007`), integral gate (`:1019-1038`), bias-EMA update (`:1042-1052`), reward call + termination penalty (`:1054-1062`), `_get_rewards` (`:1009-1077`), `_collect_episode_metrics` (`:1079`), DORAEMON success + reset (`:1276-1290`), buffer init (`:298-316`)
- `tests/test_rewards.py` — 17 whitebox sign/roll-weight/wrap pins (repo-root `tests/`, not under the package)
- `marinelab/marinelab/algorithms/doraemon.py` — `DoraemonCfg` defaults (re-exported via `envs/main/doraemon.py` shim)
