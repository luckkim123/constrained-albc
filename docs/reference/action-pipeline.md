> Verified against commit c5a8a08.

# Action Pipeline (`envs/main`)

> **Scope**: The full action path of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — from the
> policy's raw Gaussian output, through the boundary clamps, to the two physical
> actuator paths (arm delta-PD and 6-thruster TAM wrench), and back into the
> observation. The 8D action is `[2D arm delta, 6D thruster command]`.
>
> This is a code-level reference verified against disk. It is the **action-side
> companion** to `main-network-architecture.md`, which covers the encoder / actor /
> critic layer structure and the ConstraintTRPO update. Where a topic (std clamp,
> entropy, log_std) belongs to the network internals, this document links out
> rather than duplicating.
>
> **Branch note.** All facts below track marinelab `main` (local `main` =
> `02c1007`, 2026-07-12). Three features are merged into `main` as of `20b7ae1`,
> each off-by-default:
>
> - Per-thruster fault path (`0c882df`/`8364cd6`)
> - Non-linear thrust curve (`c155aa7`, originally developed on the now-deleted
>   `exp/thruster-curve` branch)
> - Per-step actuation noise (`cc0d03a`/`18490c1`)
>
> There is no branch split left to track; §5.3/§5.4 describe both toggles as
> plain `main`-branch behavior.

---

## 1. Overview

The action is an 8D vector. The policy emits it as a **raw Gaussian sample with no
squashing and no clamping**; every bound is applied *downstream* of the network.
The vector then splits into two physically distinct actuator paths that share
nothing but the source vector:

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

*Symbols above: `q_des` = commanded joint position target (§4.1); `s` = filtered thruster
state (§5.1); TAM = thrust allocation matrix (§5.2, [glossary.md](glossary.md)); ESC =
electronic speed controller; CoG = center of gravity.*

**Key design choices:**

1. The Gaussian is *unbounded*; `[-1, 1]` is an *interpretation contract* enforced by the env, not a policy-side squashing (this is the PPO/TRPO norm, unlike SAC's tanh).
2. The same 8D vector drives two completely different dynamics: the arm dims are a **position-delta integrator** (a leak-free accumulator on PD targets), while the thruster dims are a **force low-pass filter** (first-order ESC lag).
3. The observation feeds back the *filtered* thruster state, not the raw command, so the policy sees an ESC-feedback-like signal.

### 1.1 Why one 8D vector drives two dynamics (no multi-head)

The policy emits only normalized `[-1, 1]` commands; the env absorbs the scale/timing
gap: arm `delta_scale = 0.10` vs. thruster `thrust_coeff = 40`; arm PD reacts
immediately vs. thruster first-order filter lag (fed back as `thruster_state`). This
is a standard construction.

The output layer is already 8 independent scalar heads (linear last layer, per-dim
`log_std`); only the hidden trunk (`[256, 128, 64]`) is shared, so "single vs.
multi-head" reduces to "should arm and thruster share the trunk." They do: in
attitude control the thruster generates attitude torque and arm motion perturbs it
via reaction force/CoG shift, so a shared trunk preserves that coupling — separate
heads would cut it at the representation stage.

**Don't add multi-head without evidence.** A split only pays off if the subtasks are
heterogeneous enough to interfere, or one gradient dominates — no such evidence
exists here. Measure arm/thruster gradient cosine similarity or run a
separate-network ablation first (`.claude/rules/03` — no generic solutions without
evidence).

---

## 2. Action space — 8D

`action_space = 8` (`config.py:377`), split as `[2D arm delta, 6D thruster]`.

| Index | Component | Interpretation | Downstream |
|---|---|---|---|
| `[0:2]` | arm joint delta | `q_des += delta_scale * a` (`delta_scale=0.10`, `config.py:437`) | accumulated PD position targets on `ALBC_JOINT_NAMES` (2 joints) |
| `[2:8]` | thruster commands (m0–m5) | first-order-filtered to `state ∈ [-1,1]`, then scaled and TAM-allocated | body-frame 6-DOF wrench via the 6×6 allocation matrix |

The 2 arm joints (`albc_joint_names`) are **continuous rotation motors** — there are
no physical position limits, so the delta target is never wrapped (§4). The 6
thrusters follow the ALBC ROS control package TAM, reordered to the robot
firmware ESC channel layout `m0..m5` (`config.py:80–133`; see §5.2).

---

## 3. Policy output and the two boundary clamps

### 3.1 The policy does not clamp

Both action entry points return the raw network output:

- `act()` (`actor_critic_encoder.py:272`): builds `actor_obs = cat[EmpiricalNorm(o_t), z_raw]`,
  sets `distribution = Normal(actor(actor_obs), exp(log_std))`, and returns
  `distribution.sample()` — the docstring is explicit: *"Sample action from Gaussian
  policy (no action clamping)."*
- `act_inference()` (`:279`): returns `actor(actor_obs)` directly — the mean, again
  *"no clamping."*

`std = exp(log_std)` is a single global parameter broadcast across the batch
(state-independent); its clamp and entropy behavior are detailed in
`exploration-and-noise.md` §3–§4, and literature standing in
`main-network-architecture.md` §8. They are **out of scope here** — this
document starts once a sampled `a` exists.

### 3.2 Clamp #1 — vecenv wrapper (`clip_actions`, currently a no-op)

`RslRlVecEnvWrapper.step()` clamps *before* handing actions to the env
(`isaaclab_rl/rsl_rl/vecenv_wrapper.py:153–154`):

```python
if self.clip_actions is not None:
    actions = torch.clamp(actions, -self.clip_actions, self.clip_actions)
```

The value comes from `agent_cfg.clip_actions` at wrapper construction
(`scripts/train.py:256`: `RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)`).
When `clip_actions is None`, this is a no-op and only clamp #2 applies.

**Currently a confirmed no-op, not a hypothetical** — traced across every launch path:

1. `rsl_rl_ppo_cfg.py` does not set `clip_actions` → inherits the isaaclab base default `clip_actions=None` (`rl_cfg.py:181`).
2. `train.py:256` passes that `None` through unchanged.
3. `train_student.py:124` passes `clip_actions=None` explicitly.

So clamp #1 is skipped on every launch path today — **only clamp #2 bounds actions**
— and the entropy-collapse / boundary-mass-waste discussion in §8 attaches to clamp
#2 alone.

### 3.3 Clamp #2 — env action buffer (always)

`ALBCEnv._update_action_buffers()` (`albc_env.py:524`), called at the top of
`_pre_physics_step`, unconditionally clamps and rotates the 3-deep action history:

```python
self._prev_prev_actions = self._prev_actions.clone()
self._prev_actions       = self._actions.clone()
self._actions            = actions.clone().clamp(-1.0, 1.0)
```

This clamp is the one that always holds — a hard saturation, not a smooth
squash, so gradients do not flow back through the boundary.

**Consequence for exploration:** because the policy std is unbounded and only
the *input to physics* is clamped, a large `log_std` wastes probability mass
on out-of-range samples that saturate at ±1 — one structural reason the std
tends to shrink (see the entropy-collapse discussion in the network doc).

---

## 4. Arm path — delta integrator → PD

`_pre_physics_step` slices `arm_actions = self._actions[:, :2]` and, gated by the
control decimation, calls `_apply_joint_pd_action` (`albc_env.py:657–659`).

### 4.1 Delta accumulation (unbounded)

`_apply_joint_pd_action` (`:668–687`) is a **leak-free position integrator**. The
dispatch and the accumulation together:

```python
# dispatch, gated by control_decimation (albc_env.py:657-659)
arm_actions = self._actions[:, :2]
if self._control_step_counter % self.cfg.control_decimation == 0:
    self._apply_joint_pd_action(arm_actions)

# _apply_joint_pd_action body (albc_env.py:668-687)
delta = self._delta_scale * actions                       # delta_scale = 0.10
if self._joint_act_noise_std is not None and self._joint_act_noise_std > 0.0:
    delta = delta * (1.0 + torch.randn_like(delta) * self._joint_act_noise_std)
self._joint_pos_targets += delta
```

The middle line is an optional per-step multiplicative actuation-noise channel
(`ActuationNoiseCfg.joint_noise_std`, `config.py:338–356`), off by default and
independent of DR/fault — when off, `_joint_act_noise_std` is `None` and this
reduces to the original `self._joint_pos_targets += self._delta_scale * actions`.

With `a ∈ [-1, 1]` and `delta_scale = 0.10`, the per-step target change is at most
**0.10 rad/step** (≈ 0.08 rad at typical action magnitudes, per the code comment).
This delta parameterization is deliberate: it limits per-step position change and so
prevents PD actuator saturation from a step command.

**`_joint_pos_targets` is never wrapped or clamped.** Only three call sites write it,
and none clamps:

- Init to nominal (`:322`, `nominal_joint_pos = (0.0, π/2)`)
- The `+=` accumulation (`:687`)
- Reset to the measured joint position (`:1439`, see below)

The joints are continuous rotation motors, so the integrator grows unbounded by
design; joint1 cable wrapping is protected by the `joint1_position_cost` **constraint**
(budget on `|θ_cum| > 4π`, where `θ_cum` is joint1's cumulative rotation angle),
*not* by clamping — exactly why the joint1 anti-drift work is a constraint-redesign
problem, not a clamp (`constraints.md` §7, joint1 campaign docs).

**Position-command integrator, not a PID error-integrator — reset is episode-scoped,
never target-reached.** It accumulates the *commanded* position (`q_des +=
delta_scale * a`), not an error signal, so it grows unbounded *within* an episode,
re-initializing only at episode reset (`_reset_action_buffers`, `:1428`, called from
the env reset at `:1426`), per-env, to the *measured* joint position — not to `0` or
to `nominal_joint_pos`.

This is deliberate anti-bump init: PD torque ≈ `Kp * (q_des - q_measured)` (where
`q_measured` is the measured joint position), so `q_des = q_measured` at reset
zeroes the error even under a randomized initial pose.

**Wrong mental model to avoid:** "reset the integrator once the joint reaches its
target" (the waypoint / error-integrator scheme) breaks control here — reaching the
target is a *hold* state, not a reset trigger, and zeroing `q_des` on reach would fling
the arm back to `0`/nominal mid-episode. The only valid reset trigger is the episode
boundary.

### 4.2 PD actuator

`_apply_action` (`:888–889`) writes the accumulated targets via
`self._robot.set_joint_position_target(self._joint_pos_targets, joint_ids=self._albc_joint_ids)`.

The joints are driven by an `ImplicitActuatorCfg` in the robot asset
(`marinelab/assets/albc/albc.py:198–201`). `ω_n` = natural frequency, `J` = arm
moment of inertia used in the second-order calc below:

| Field | Value | Note |
|---|---|---|
| stiffness (Kp) | 100.0 | `ω_n ≈ 57.7 rad/s` with `J ≈ 0.15 kg·m²` |
| damping (Kd) | 3.0 | damping ratio ≈ 0.7 (near-critical) |
| `effort_limit_sim` | 13.0 Nm | PhysX hard cap, above the 9.5 Nm motor stall used by the `arm_torque` constraint |
| `velocity_limit_sim` | 3.1 rad/s | measured XW540-T260 no-load plateau (2026-07-06), PhysX hard cap |

**Two distinct arm bounds, easy to confuse:** the 13.0 Nm / 3.1 rad/s figures
are **PhysX hard caps** on the actuator. The constraint terms `arm_torque`
(`limit_nm=9.5`) and `arm_joint_vel` (`limit_rad_per_s=2.8`) are **soft cost
budgets** on the *measured* torque/velocity — they penalize, they do not
clip. A policy can exceed 2.8 rad/s (paying constraint cost) up to the 3.1
rad/s physical cap. Do not treat the constraint limit as a physical limit.

**Kp/Kd basis is theoretical, not hardware-measured — no sim↔hardware gain
mapping exists.** `ω_n ≈ 57.7 rad/s` / damping-ratio-0.7 (table above) come
from a second-order calc assuming `J ≈ 0.15 kg·m²` (`albc.py:198–201`), not a
step-response measurement — the file names no motor model.

Real hardware is a Dynamixel XW540-T260 with its own ~1 kHz internal PID
(`sim-to-real.md:13,19`); no code maps sim `ImplicitActuatorCfg` gains to its
register-space gains (registers aren't SI units, conversion is per-model),
and the required step-response system ID is an open TODO (`sim-to-real.md:308–309`).

Sim continuous-PD vs. real discrete-PID (1 kHz, integer registers, PWM
saturation, firmware filters) is a **structural** gap DR cannot cover — same
class as the thruster deadband/quadratic curve (§5.3).

**Joint gain DR (per-env at reset only, not per-step, not DORAEMON-curriculum, range
fixed):** applied by `randomize_joint_gains` (`mdp/events.py:473–485`) in `albc_env.py:1558–1567` when `rand_cfg.enable`.

| Field | Range | Type | Location |
|---|---|---|---|
| Stiffness (Kp) | `[30, 150]` | absolute, overwrites nominal 100 | `config.py:192–193` |
| Damping (Kd) | `[0.3, 7.0]` | absolute, overwrites nominal 3 | `config.py:192–193` |
| `joint_effort_limit_range` | `[0.7, 1.0]` | multiplicative scale | `config.py:195` |
| Joint friction (static) | `[0, 0.03]` | additive | `config.py:196–197` |
| Joint friction (viscous) | `[0, 0.2]` | additive | `config.py:196–197` |

Stiffness/damping DR is an **absolute range** overwriting nominal 100/3, not a scaled
window around it. Both were formerly the "Hard range"; the 2026-07-07 merge dropped
the separate default/easy class (never instantiated on any training path), so there is
no separate default anymore. A joint fault separately scales effort limit by per-env
health (`faults.apply_joint_health`, `faults.py:80`).

---

## 5. Thruster path — filter → curve → coefficient → TAM

Thruster dims `self._actions[:, 2:]` go to the marinelab `ThrusterModel`
(`marinelab/core/thruster.py`). `_pre_physics_step` runs once per env step, so it
advances the filter by `step_dt`, not `physics_dt`, there (`albc_env.py:661–664`;
fixed 2026-07-12, `fab864f`), and reads the resulting wrench in `_apply_action`
(`:916`), adding it to the hydrodynamic force before writing to the body.

### 5.1 First-order filter (asymmetric time constants)

`apply_dynamics` (`thruster.py:123`) clamps the command to `[-1, 1]` (the thruster's
*own* clamp, independent of §3.2) and runs a first-order lag with **direction-dependent**
time constants — spin-up is slower than spin-down:

```python
# dispatch (albc_env.py:661-664): once per env step, so dt = step_dt not physics_dt
if self._thruster is not None:
    self._thruster.apply_dynamics(self._actions[:, 2:], self.step_dt)

# apply_dynamics body (thruster.py:123): own [-1,1] clamp + direction-dependent lag
if self._act_noise_std is not None and self._act_noise_std > 0.0:
    commands = commands * (1.0 + torch.randn_like(commands) * self._act_noise_std)
target_state = commands.clamp(-1.0, 1.0)
tau   = torch.where(target_state > self._state, tau_up, tau_down)   # 0.1 up / 0.05 down
alpha = dt / tau
self._state = self._state + alpha * (target_state - self._state)
```

The noise line is the thruster side of the same optional per-step actuation-noise
channel as §4.1 (`ActuationNoiseCfg.thruster_noise_std`), off by default — when off,
`_act_noise_std` is `None` and the snippet's tail four lines are the whole function.
`self._state ∈ [-1, 1]` is the normalized filtered command — this is the ESC-lag
model. With DR, `tau_up/tau_down` and `thrust_coeff` are per-env
(`config.py:218–219`; `randomize_parameters`, `thruster.py:234`).

### 5.2 Command shaping → force → clamp → TAM

`compute_wrench` (`thruster.py:179`) turns the filtered state into a body wrench:

```python
command          = self._thrust_command()                 # identity, or thrust curve (§5.3)
thrust_magnitude = command * thrust_coeff                 # per-env if DR, else 40.0
[thrust_magnitude = thrust_magnitude * health]            # fault path, before clamp (§5.4)
thrust_magnitude = thrust_magnitude.clamp(-max_thrust, max_thrust)   # +-50 N
body_wrench      = einsum("ij,nj->ni", allocation_matrix, thrust_magnitude)  # 6x6 TAM
forces  = body_wrench[:, :3]
torques = body_wrench[:, 3:]
```

**The live allocation matrix is column-reordered from the raw sim/TAM.yaml order to
the robot firmware ESC channel order:**

1. `config.py` keeps the original sim-thruster matrix as `_BASE_ALLOCATION_MATRIX`
   (`:80–87`, columns T0–T5, verbatim from `TAM.yaml`/`actuators.xacro`).
2. It derives the matrix `ThrusterModel` actually uses,
   `ALBCThrusterCfg.allocation_matrix` (`:131–133`), by permuting those columns with
   `_reorder_columns(_BASE_ALLOCATION_MATRIX, _ESC_CHANNEL_ORDER)` (`:97–106`), where
   `_ESC_CHANNEL_ORDER = (4, 0, 1, 5, 2, 3)` (`:94`).
3. Physics is invariant under a column permutation; what changes is which physical
   thruster each **action index** now drives — action dims `[2:8]` map to firmware
   channels `m0..m5`, not to the raw `T0..T5` sim order.

The table below is the live (post-reorder) matrix, `m0..m5`:

| Row | DOF | m0 | m1 | m2 | m3 | m4 | m5 | Layout |
|---|---|---|---|---|---|---|---|---|
| Fx | surge | 0 | 0.707 | -0.707 | 0 | 0.707 | -0.707 | 4 horizontal (45° vectored) |
| Fy | sway | 0 | -0.707 | -0.707 | 0 | 0.707 | 0.707 | " |
| Fz | heave | 1 | 0 | 0 | 1 | 0 | 0 | 2 vertical |
| Mx | roll | 0 | 0.007 | 0.007 | 0 | -0.007 | -0.007 | small arm |
| My | pitch | 0.145 | 0.007 | -0.007 | -0.145 | 0.007 | -0.007 | vertical pair dominates |
| Mz | yaw | 0 | 0.144 | 0.144 | 0 | 0.144 | 0.144 | horizontal quad |

The tiny roll arm (0.007 m) is the reason a large payload CoG offset can exceed roll
TAM authority — the HardDR `payload_cog_offset_xy_radius` was cut 0.15→0.08 for
exactly this reason (`config.py:201–207`): `4 × 50 N × 0.007 m = 1.4 Nm` of roll
authority vs. a 3 kg payload at 0.15 m producing ~4.5 Nm.

### 5.3 Optional non-linear thrust curve (off by default)

`_thrust_command` (`thruster.py:155`) is the identity when
`cfg.enable_thrust_curve` is False — the default, so `compute_wrench` is
byte-identical to the linear model. When enabled it applies a BlueROV T200
fidelity model **in normalized command space** (merged into `main` at `20b7ae1`,
originally developed on the now-deleted `exp/thruster-curve` branch):

- **Deadband**: `|state| < thrust_deadband (0.075)` → 0, modeling the T200 ESC
  PWM deadzone around neutral.
- **Signed-square**: outside the deadband, `sign(state) * state²`, matching the
  quadratic propeller law (thrust ∝ ω², ω ∝ command, where `ω` is propeller
  angular velocity).

Output stays in `[-1, 1]`, so the downstream `* thrust_coeff` range is unchanged.
This is a structural non-linearity DR cannot emulate (a multiplicative scale cannot
create a zero-region or a quadratic shape) — see the sim-to-real audit. It is an
off-by-default toggle (`getattr` fallback → byte-identical), not baseline behavior.

### 5.4 Optional per-thruster fault (off by default)

`ThrusterModel.__init__` takes `enable_fault` (`thruster.py:41`) — off by default
(`FaultInjectionCfg.enable=False`, `config.py:319`). Mechanism, when enabled:

1. Allocates a per-env per-thruster health buffer `∈ [0, 1]` (`:88–91`).
2. `compute_wrench` multiplies health into the *unsaturated* magnitude **before** the
   ±50 N clamp (`:194–195`) — a degraded thruster gets reduced peak force, not a cutoff.
3. `set_thruster_health` (`:214`) injects it; the env samples via
   `faults.sample_thruster_health` (`faults.py:27`) and pushes it in at reset.

When `enable_fault` is False, no buffer is allocated and the multiply is skipped
(byte-identical). Fault is FTC-research infrastructure, distinct from DR — a fault is
component *failure*, DR is a valid-but-different vehicle. `_init_thrusters`
(`albc_env.py:401–422`) wires `enable_fault=self.cfg.fault.enable` and
`enable_actuation_noise=self.cfg.actuation_noise.enable` (§4.1/§5.1) into the
`ThrusterModel` constructor.

**Fault, thrust curve, and actuation noise are all plain `main`-branch toggles.** All
three landed via the merges listed in the top branch note; none require a special
branch checkout, and none are mutually exclusive — they compose in pipeline order
curve → coeff → health → clamp.

---

## 6. Action feedback into the observation

The action does not just leave the network — it re-enters the next observation two
ways (both part of the 69D `o_t`):

1. **Filtered thruster state (6D)** in the current proprioception. `compute_policy_obs`
   (`mdp/observations.py:69`) reads `env._thruster.state` — the *filtered* first-order
   state (§5.1), labeled *"6D: filtered thruster output"* (`:83`), **not** the raw
   command. This mimics ESC feedback the real robot would report.
2. **Full 8D action history (16D)** in the temporal history. `_get_hist_features`
   (`albc_env.py:544–584`) records `self._prev_actions` (the 8D action that produced
   the current state) into the ring buffer; `_get_observations` slices the newest
   `hist_action_len=2` steps → `8 × 2 = 16D` (`:1068,1085`).

So the policy is partly closed-loop on its own recent actions. The full 69D
composition is tabulated in `main-network-architecture.md` §2.1; here the point is
only *which parts are action-derived*.

---

## 7. Where to change what (action knob map)

| Knob | Value | Location (file:line) |
|---|---|---|
| action_space | 8 (2 arm + 6 thruster) | `config.py:377` |
| delta_scale (arm per-step) | 0.10 | `config.py:437` |
| nominal_joint_pos (arm init target) | (0.0, π/2) | `config.py:433` |
| arm actuator Kp / Kd | 100.0 / 3.0 | `marinelab/assets/albc/albc.py:198–199` |
| arm effort / velocity cap (PhysX) | 13.0 Nm / 3.1 rad/s | `albc.py:200–201` |
| thruster count / max_thrust | 6 / 50.0 N | `config.py:126–127` |
| thrust_coefficient | 40.0 | `config.py:128` |
| time_constant_up / down | 0.1 / 0.05 | `config.py:129–130` |
| allocation matrix (6×6 TAM, ESC-reordered) | see §5.2 | `config.py:80–133` |
| `clip_actions` (vecenv clamp) | `agent_cfg.clip_actions`, currently `None` → no-op | `scripts/train.py:256`, `vecenv_wrapper.py:153`, `rl_cfg.py:181` |
| env action clamp | `[-1, 1]` (always) | `albc_env.py:524` |
| thruster command clamp | `[-1, 1]` (always) | `thruster.py:141` |
| `enable_thrust_curve` / `thrust_deadband` | False / 0.075 | `marinelab/assets/uuv_cfg.py:143,148` |
| `enable_fault` / thruster_health | False | `config.py:319`; `thruster.py:41,194` |
| control_decimation (arm PD rate) | 1 | `config.py:431` |
| thruster/joint DR scales | see cfg | `config.py:192–197` (joint), `218–219` (thruster) |

---

## 8. Notes, standing, and limitations

- **The `[-1, 1]` bound is an interpretation, not a squash.** Standard for
  PPO/TRPO: the network emits a raw Gaussian mean, and the environment interprets the
  range (here via `clamp`). SAC-style tanh-squashing (with the log-prob Jacobian
  correction) is *not* used and would be a different algorithm. The MLP last layer is
  linear (`last_activation=None`); no `act()` clamping. (Same finding as
  `main-network-architecture.md` §8.)
- **The external clamp does not break credit assignment.** The policy gradient uses
  `log pi(a_raw | o)`, the raw un-clamped sampled action, so the update always
  credits what the policy actually emitted — there is no gradient/env inconsistency
  from clamping per se.
- **But it does distort exploration.** Clamping *collapses* the out-of-range region:
  `a = 1.5` and `a = 3.5` both saturate to `1.0`, so the env cannot distinguish them,
  and the wasted probability mass produces a structural downward pressure on
  `log_std` (§3.3, `exploration-and-noise.md` §11).
- **Tanh-squashing (SAC-style) would avoid this** by keeping all mass in `(-1, 1)`
  with a smooth gradient, at the cost of the log-prob Jacobian correction and a
  different algorithm class. This project stays on the external-clamp path and
  offsets the side-effect with the entropy bonus and per-dim `min_std` floor
  (`exploration-and-noise.md` §3.1 and §4).
- **Two clamps are redundant-by-design, not a bug.** Clamp #1 (vecenv, optional)
  and clamp #2 (env buffer, always) both target `[-1, 1]`; the env clamp is the
  authoritative one, the wrapper clamp is a library-level guard that is a no-op when
  `clip_actions is None`.
- **The arm target integrator is unbounded on purpose.** No wrap to `[-π, π]`, no
  clamp to joint limits — the joints are continuous-rotation, and drift is a
  *constraint* problem (`joint1_position_cost`, `cumulative_yaw_cost`), not a clamp.
  Treating it as a bug and adding a clamp would silently change the control authority.
- **Fault, thrust curve, and actuation noise are independent toggles, not mutually
  exclusive.** All three (§5.3, §5.4, and the per-step command-noise channel noted
  in §4.1/§5.1) live on marinelab `main`, each off by default
  (`ThrusterCfg.enable_thrust_curve`, `FaultInjectionCfg.enable`,
  `ActuationNoiseCfg.enable`), and compose in pipeline order curve → coeff →
  health → clamp. There is no branch split left to track.
- This is a static code-structure reference. Whether the policy actually *uses* its
  full action range, or whether the thruster filter lag matters for a given maneuver,
  are runtime-dynamics questions for eval/analysis, not this document.

---

## Source files

- `constrained_albc/envs/main/encoder/actor_critic_encoder.py` — `act()` / `act_inference()` (no clamp), actor obs assembly
- `constrained_albc/envs/main/encoder/_policy_base.py` — global `log_std`, Gaussian `_update_distribution`
- `constrained_albc/envs/main/albc_env.py` — `_update_action_buffers` (clamp #2), `_apply_joint_pd_action` (delta integrator), `_apply_action` (PD + wrench), `_get_hist_features` (action history), `_pre_physics_step` (dispatch)
- `constrained_albc/envs/main/config.py` — `action_space`, `delta_scale`, `ALBCThrusterCfg` (TAM, coeff, tau), `FaultInjectionCfg`
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` (filtered thruster_state feedback)
- `constrained_albc/envs/main/mdp/faults.py` — `sample_thruster_health`, `apply_joint_health`
- `marinelab/core/thruster.py` — `apply_dynamics` (first-order filter), `_thrust_command` (curve), `compute_wrench` (coeff, health, clamp, TAM). Imported directly (`albc_env.py:406`; the `marinelab.physics` shim was removed 2026-07 — `marinelab.core` is the only import path now).
- `marinelab/assets/albc/albc.py` — `ImplicitActuatorCfg` for the arm joints
- `isaaclab/source/isaaclab_rl/isaaclab_rl/rsl_rl/vecenv_wrapper.py` — `clip_actions` (clamp #1)
