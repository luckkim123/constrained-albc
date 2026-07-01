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
> **Branch note.** The physical-parameter facts below track marinelab `main`
> (the default install target; local `main` = `8364cd6`). Two unmerged marinelab
> experiment branches each touch the thruster model in opposite directions — the
> per-thruster fault path (`origin/main`, commit `0c882df`) and the non-linear
> thrust curve (`exp/thruster-curve`, commit `d34debc`, off-by-default). Both are
> flagged in §6/§7 so the document stays correct regardless of which is checked
> out.

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

**Key design choices.** (a) The Gaussian is *unbounded*; `[-1, 1]` is an
*interpretation contract* enforced by the env, not a policy-side squashing (this is
the PPO/TRPO norm, unlike SAC's tanh). (b) The same 8D vector drives two completely
different dynamics: the arm dims are a **position-delta integrator** (a leak-free
accumulator on PD targets), while the thruster dims are a **force low-pass filter**
(first-order ESC lag). (c) The observation feeds back the *filtered* thruster state,
not the raw command, so the policy sees an ESC-feedback-like signal.

---

## 2. Action space — 8D

`action_space = 8` (`config.py:303`), split as `[2D arm delta, 6D thruster]`.

| Index | Component | Interpretation | Downstream |
|---|---|---|---|
| `[0:2]` | arm joint delta | `q_des += delta_scale * a` (`delta_scale=0.10`, `config.py:360`) | accumulated PD position targets on `ALBC_JOINT_NAMES` (2 joints) |
| `[2:8]` | thruster commands (T0–T5) | first-order-filtered to `state ∈ [-1,1]`, then scaled and TAM-allocated | body-frame 6-DOF wrench via the 6×6 allocation matrix |

The 2 arm joints (`albc_joint_names`) are **continuous rotation motors** — there are
no physical position limits, so the delta target is never wrapped (§4). The 6
thrusters follow the ALBC ROS control package TAM (`config.py:90–97`).

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
(state-independent); its clamp, entropy behavior, and literature standing live in
`main-network-architecture.md` §4 and §8. They are **out of scope here** — this
document starts once a sampled `a` exists.

### 3.2 Clamp #1 — vecenv wrapper (`clip_actions`, may be a no-op)

`RslRlVecEnvWrapper.step()` clamps *before* handing actions to the env
(`isaaclab_rl/rsl_rl/vecenv_wrapper.py:151–154`):

```python
if self.clip_actions is not None:
    actions = torch.clamp(actions, -self.clip_actions, self.clip_actions)
```

The value comes from `agent_cfg.clip_actions` at wrapper construction
(`scripts/train.py:292`: `RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)`).
When `clip_actions is None`, this is a no-op and only clamp #2 applies.

### 3.3 Clamp #2 — env action buffer (always)

`ALBCEnv._update_action_buffers()` (`albc_env.py:452`), called at the top of
`_pre_physics_step`, unconditionally clamps and rotates the 3-deep action history:

```python
self._prev_prev_actions = self._prev_actions.clone()
self._prev_actions       = self._actions.clone()
self._actions            = actions.clone().clamp(-1.0, 1.0)
```

This clamp is the one that always holds. **Consequence for exploration:** because
the policy std is unbounded and only the *input to physics* is clamped, a large
`log_std` wastes probability mass on out-of-range samples that saturate at ±1 —
which is one structural reason the std tends to shrink (see the entropy-collapse
discussion in the network doc). The clamp is a hard saturation, not a smooth
squash, so gradients do not flow back through the boundary.

---

## 4. Arm path — delta integrator → PD

`_pre_physics_step` slices `arm_actions = self._actions[:, :2]` and, gated by the
control decimation, calls `_apply_joint_pd_action` (`albc_env.py:558–560`):

```python
arm_actions = self._actions[:, :2]
if self._control_step_counter % self.cfg.control_decimation == 0:
    self._apply_joint_pd_action(arm_actions)
```

### 4.1 Delta accumulation (unbounded)

`_apply_joint_pd_action` (`:567–578`) is a **leak-free position integrator**:

```python
self._joint_pos_targets += self._delta_scale * actions   # delta_scale = 0.10
```

With `a ∈ [-1, 1]` and `delta_scale = 0.10`, the per-step target change is at most
**0.10 rad/step** (≈ 0.08 rad at typical action magnitudes, per the code comment).
This delta parameterization is deliberate: it limits per-step position change and so
prevents PD actuator saturation from a step command.

**`_joint_pos_targets` is never wrapped or clamped.** The only three writes are:
init to nominal (`:278`, `nominal_joint_pos = (0.0, π/2)`), the `+=` accumulation
(`:578`), and reset to the measured joint position (`:1315`). None clamps. The joints
are continuous rotation motors, so the target integrator grows unbounded by design;
joint1 cable wrapping is protected by the `joint1_position_cost` **constraint**
(budget on `|θ_cum| > 4π`), *not* by clamping the target. (This is exactly why the
joint1 anti-drift work is a constraint-redesign problem, not a clamp: see
`main-network-architecture.md` §5.1 and the joint1 campaign docs.)

### 4.2 PD actuator

`_apply_action` (`:780`) writes the accumulated targets:

```python
self._robot.set_joint_position_target(self._joint_pos_targets, joint_ids=self._albc_joint_ids)
```

The joints are driven by an `ImplicitActuatorCfg` in the robot asset
(`marinelab/assets/albc/albc.py:196–202`):

| Field | Value | Note |
|---|---|---|
| stiffness (Kp) | 100.0 | `ω_n ≈ 57.7 rad/s` with `J ≈ 0.15 kg·m²` |
| damping (Kd) | 3.0 | damping ratio ≈ 0.7 (near-critical) |
| `effort_limit_sim` | 13.0 Nm | PhysX hard cap, above the 9.5 Nm motor stall used by the `arm_torque` constraint |
| `velocity_limit_sim` | 6.28 rad/s | 2π, PhysX hard cap |

**Two distinct arm bounds, easy to confuse.** The 13.0 Nm / 6.28 rad/s figures are
**PhysX hard caps** on the actuator. The constraint terms `arm_torque`
(`limit_nm=9.5`) and `arm_joint_vel` (`limit_rad_per_s=4.189`) are **soft cost
budgets** on the *measured* torque/velocity — they penalize, they do not clip. A
policy can exceed 4.189 rad/s (paying constraint cost) up to the 6.28 rad/s physical
cap. Do not treat the constraint limit as a physical limit.

DR randomizes the joint gains/effort/friction per env at reset (`config.py:126–131,
183–184`); a joint fault scales the effort limit by per-env health
(`faults.apply_joint_health`, `faults.py:80`).

---

## 5. Thruster path — filter → curve → coefficient → TAM

Thruster dims `self._actions[:, 2:]` go to the marinelab `ThrusterModel`
(`marinelab/core/thruster.py`). The env advances the filter every physics step in
`_pre_physics_step` (`albc_env.py:562–563`):

```python
if self._thruster is not None:
    self._thruster.apply_dynamics(self._actions[:, 2:], self.physics_dt)
```

and reads the resulting wrench in `_apply_action` (`:806`), adding it to the
hydrodynamic force before writing to the body.

### 5.1 First-order filter (asymmetric time constants)

`apply_dynamics` (`thruster.py:97`) clamps the command to `[-1, 1]` (the thruster's
*own* clamp, independent of §3.2) and runs a first-order lag with **direction-dependent**
time constants — spin-up is slower than spin-down:

```python
target_state = commands.clamp(-1.0, 1.0)
tau   = torch.where(target_state > self._state, tau_up, tau_down)   # 0.1 up / 0.05 down
alpha = dt / tau
self._state = self._state + alpha * (target_state - self._state)
```

`self._state ∈ [-1, 1]` is the normalized filtered command — this is the ESC-lag
model. With DR, `tau_up/tau_down` and `thrust_coeff` are per-env
(`config.py:140–141`; `randomize_parameters`, `thruster.py:175`).

### 5.2 Command shaping → force → clamp → TAM

`compute_wrench` (`thruster.py:134`) turns the filtered state into a body wrench:

```python
command          = self._thrust_command()                 # identity, or thrust curve (§5.3)
thrust_magnitude = command * thrust_coeff                 # per-env if DR, else 40.0
thrust_magnitude = thrust_magnitude.clamp(-max_thrust, max_thrust)   # +-50 N
[thrust_magnitude = thrust_magnitude * health]            # fault path, marinelab main only (§5.4)
body_wrench      = einsum("ij,nj->ni", allocation_matrix, thrust_magnitude)  # 6x6 TAM
forces  = body_wrench[:, :3]
torques = body_wrench[:, 3:]
```

The 6×6 allocation matrix (`config.py:90–97`) maps 6 per-thruster forces to a
body-frame 6-DOF wrench:

| Row | DOF | T0 | T1 | T2 | T3 | T4 | T5 | Layout |
|---|---|---|---|---|---|---|---|---|
| Fx | surge | 0.707 | -0.707 | 0.707 | -0.707 | 0 | 0 | 4 horizontal (45° vectored) |
| Fy | sway | -0.707 | -0.707 | 0.707 | 0.707 | 0 | 0 | " |
| Fz | heave | 0 | 0 | 0 | 0 | 1 | 1 | 2 vertical |
| Mx | roll | 0.007 | 0.007 | -0.007 | -0.007 | 0 | 0 | small arm |
| My | pitch | 0.007 | -0.007 | 0.007 | -0.007 | 0.145 | -0.145 | vertical pair dominates |
| Mz | yaw | 0.144 | 0.144 | 0.144 | 0.144 | 0 | 0 | horizontal quad |

The tiny roll arm (0.007 m) is the reason a large payload CoG offset can exceed roll
TAM authority — the HardDR `payload_cog_offset_xy_radius` was cut 0.15→0.08 for
exactly this reason (`config.py:174–180`): `4 × 50 N × 0.007 m = 1.4 Nm` of roll
authority vs. a 3 kg payload at 0.15 m producing ~4.5 Nm.

### 5.3 Optional non-linear thrust curve (`exp/thruster-curve`, off by default)

`_thrust_command` (`thruster.py:122`) is the identity when
`cfg.enable_thrust_curve` is False — the default and the `main`-branch behavior, so
`compute_wrench` is byte-identical to the linear model. When enabled (only present on
the `exp/thruster-curve` branch), it applies a BlueROV T200 fidelity model **in
normalized command space**:

- **Deadband**: `|state| < thrust_deadband (0.075)` → 0, modeling the T200 ESC
  PWM deadzone around neutral.
- **Signed-square**: outside the deadband, `sign(state) * state²`, matching the
  quadratic propeller law (thrust ∝ ω², ω ∝ command).

Output stays in `[-1, 1]`, so the downstream `* thrust_coeff` range is unchanged.
This is a structural non-linearity DR cannot emulate (a multiplicative scale cannot
create a zero-region or a quadratic shape) — see the sim-to-real audit. It is an
off-by-default toggle (`getattr` fallback → byte-identical), not baseline behavior.

### 5.4 Optional per-thruster fault (marinelab `main`, off by default)

On marinelab `main`, `ThrusterModel.__init__` takes `enable_fault`
(`thruster.py:41`); when True it allocates a per-env per-thruster health buffer
`∈ [0, 1]` (`:83–84`), and `compute_wrench` multiplies health into the *unsaturated*
magnitude **before** the ±50 N clamp (`:148–149`) so a degraded thruster has a
reduced peak force. `set_thruster_health` (`:168`) injects it; the env samples it via
`faults.sample_thruster_health` (`faults.py:27`) and pushes it in at reset. When
`enable_fault` is False, no buffer is allocated and the multiply is skipped
(byte-identical). Fault is off by default (`FaultInjectionCfg.enable=False`,
`config.py:266`); it is FTC-research infrastructure, distinct from DR (a fault =
component *failure*, DR = a valid-but-different vehicle).

> **Working-tree caveat.** The `exp/thruster-curve` branch (§5.3) was forked before
> the fault commit, so its `thruster.py` has **no** `enable_fault` parameter. If that
> branch is checked out while `config.py:432` still declares `fault: FaultInjectionCfg`
> and `_init_thrusters` passes `enable_fault=...` (`albc_env.py:357`), the constructor
> would reject the kwarg. That is a branch-divergence artifact, not the shipped
> `main` state; both experiment branches are slated to converge to `main`.

---

## 6. Action feedback into the observation

The action does not just leave the network — it re-enters the next observation two
ways (both part of the 69D `o_t`):

1. **Filtered thruster state (6D)** in the current proprioception. `compute_policy_obs`
   (`mdp/observations.py:68`) reads `env._thruster.state` — the *filtered* first-order
   state (§5.1), labeled *"6D: filtered thruster output"* (`:82`), **not** the raw
   command. This mimics ESC feedback the real robot would report.
2. **Full 8D action history (16D)** in the temporal history. `_get_hist_features`
   (`albc_env.py:486–495`) records `self._prev_actions` (the 8D action that produced
   the current state) into the ring buffer; `_get_observations` slices the newest
   `hist_action_len=2` steps → `8 × 2 = 16D` (`:975`).

So the policy is partly closed-loop on its own recent actions. The full 69D
composition is tabulated in `main-network-architecture.md` §2.1; here the point is
only *which parts are action-derived*.

---

## 7. Where to change what (action knob map)

| Knob | Value | Location (file:line) |
|---|---|---|
| action_space | 8 (2 arm + 6 thruster) | `config.py:303` |
| delta_scale (arm per-step) | 0.10 | `config.py:360` |
| nominal_joint_pos (arm init target) | (0.0, π/2) | `config.py:359` |
| arm actuator Kp / Kd | 100.0 / 3.0 | `marinelab/assets/albc/albc.py:196–202` |
| arm effort / velocity cap (PhysX) | 13.0 Nm / 6.28 rad/s | `albc.py:196–202` |
| thruster count / max_thrust | 6 / 50.0 N | `config.py:85–86` |
| thrust_coefficient | 40.0 | `config.py:87` |
| time_constant_up / down | 0.1 / 0.05 | `config.py:88–89` |
| allocation matrix (6×6 TAM) | see §5.2 | `config.py:90–97` |
| `clip_actions` (vecenv clamp) | `agent_cfg.clip_actions` | `scripts/train.py:292`, `vecenv_wrapper.py:151` |
| env action clamp | `[-1, 1]` (always) | `albc_env.py:452` |
| thruster command clamp | `[-1, 1]` (always) | `thruster.py:108` |
| `enable_thrust_curve` / `thrust_deadband` | False / 0.075 (`exp/thruster-curve`) | `marinelab/assets/uuv_cfg.py:143,148` |
| `enable_fault` / thruster_health | False (`main`) | `config.py:266`; `thruster.py:41,149` |
| control_decimation (arm PD rate) | 1 | `config.py:357` |
| thruster/joint DR scales | see cfg | `config.py:126–131,140–141,183–187` |

---

## 8. Notes, standing, and limitations

- **The `[-1, 1]` bound is an interpretation, not a squash.** Standard for
  PPO/TRPO: the network emits a raw Gaussian mean, and the environment interprets the
  range (here via `clamp`). SAC-style tanh-squashing (with the log-prob Jacobian
  correction) is *not* used and would be a different algorithm. The MLP last layer is
  linear (`last_activation=None`); no `act()` clamping. (Same finding as
  `main-network-architecture.md` §8.)
- **Two clamps are redundant-by-design, not a bug.** Clamp #1 (vecenv, optional)
  and clamp #2 (env buffer, always) both target `[-1, 1]`; the env clamp is the
  authoritative one, the wrapper clamp is a library-level guard that is a no-op when
  `clip_actions is None`.
- **The arm target integrator is unbounded on purpose.** No wrap to `[-π, π]`, no
  clamp to joint limits — the joints are continuous-rotation, and drift is a
  *constraint* problem (`joint1_position_cost`, `cumulative_yaw_cost`), not a clamp.
  Treating it as a bug and adding a clamp would silently change the control authority.
- **Thruster fault vs. thrust curve are mutually exclusive across the two live
  experiment branches** (§5.3–5.4) only because those branches were forked at
  different points; on `main` the fault path is present and the curve is absent. This
  document's default narrative is marinelab `main`.
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
- `marinelab/core/thruster.py` — `apply_dynamics` (first-order filter), `_thrust_command` (curve), `compute_wrench` (coeff, clamp, health, TAM). Note: `albc_env.py:350` imports it via the deprecated `marinelab.physics` shim, which re-exports `marinelab.core`; the real source is `core/`.
- `marinelab/assets/albc/albc.py` — `ImplicitActuatorCfg` for the arm joints
- `isaaclab/source/isaaclab_rl/isaaclab_rl/rsl_rl/vecenv_wrapper.py` — `clip_actions` (clamp #1)
