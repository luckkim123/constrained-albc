# Main Network Architecture (`envs/main`)

> **Scope**: Neural-network architecture of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`). This is the
> attitude-only ALBC policy (roll/pitch + yaw-rate, no linear-velocity command),
> with an 8D action (2D arm + 6D thruster), 69D actor observation, and 27D
> privileged observation.
>
> This is a code-level reference verified against disk on the
> `exp/joint1-constraint-redesign` branch. The network code
> (`encoder/`, `agents/`, `algorithms/`, `runners/`) is byte-identical to `main`
> on this branch — only the constraint definitions differ (see §6). The legacy
> full-DOF variant (`envs/full_dof/`, `Isaac-ConstrainedALBC-Full-*-v0`, 87D obs /
> 24D privileged) is a different network and is **not** described here.
>
> **한국어 버전**: [`main-network-architecture.ko.md`](main-network-architecture.ko.md).
> 두 파일 중 하나를 고치면 다른 하나도 동기화할 것 (이 영어 문서가 SSOT).

---

## 1. Overview

The policy is a teacher actor-critic in the RMA/HORA family with an **asymmetric
critic** plus a **separate multi-head cost critic**. An **encoder** compresses the
27D privileged physics vector `p_t` into a 9D latent `z`; the **actor** acts on the
69D observation `o_t` plus `z` (blind to `p_t`); the **reward critic** and **cost
critic** both see the full information (`o_t + z + p_t`, 105D) directly.

```
ENV obs dict  ->  {"policy": o_t (69D),  "privileged": p_t (27D)}

ENCODER  (input = p_t 27D, NOT the full observation)
  p_t(27D) -> static min-max normalize -> [-1, 1]   # HORA-style, deterministic, no running stat
          -> MLP[256, 128, 64]  (elu)
          -> LayerNorm(9)                            # pre-softsign
          -> softsign  ->  z (9D)                    # encoder_latent_dim = 9

ACTOR  (input 78D)
  cat[ EmpiricalNorm(o_t)(69D), z_raw(9D) ]          # only o_t is normalized; z is already softsign-bounded
          -> MLP[256, 128, 64]  (elu)
          -> action_mean (8D = 2D arm + 6D thruster) # no output activation on the action
  std = exp(global log_std[8]) -> expand             # state-INDEPENDENT
        init 0.7; clamped post-update by ConstraintTRPO

CRITIC  (asymmetric, input 105D, critic_uses_z = True)
  cat[ o_t(69D), z(9D), p_t(27D) ] (raw)             # value gradient flows back into the encoder through z
          -> MLP[512, 256, 128]  (elu) -> value (1D)

COST CRITIC  (multi-head, K = num_constraints)
  cat[ o_t(69D), z(9D), p_t(27D) ] (same 105D input)
          -> MLP[512, 256, 128]  (elu) -> cost_values (K)   # one scalar head per constraint
```

**Key design choices.**
1. The encoder input is the privileged physics vector (unobservable on the real
   robot), not the observation — `z` tells the actor *what physics this environment
   has*.
2. The critic is asymmetric: it reads privileged information directly (105D) while
   the actor only gets the compressed `z` (78D). Because `critic_uses_z = True`,
   the value-loss gradient flows back through `z` into the encoder, so the encoder
   is trained by both the policy and the value signal.
3. The encoder lives in the **TRPO natural-gradient parameter group** (with the
   actor and `log_std`), not the Adam value group — decoupling it caused a
   measured ~85% encoder-gradient drop (code comment).

---

## 2. Observation and action dimensions

All dimensions below are verified against disk and enforced at runtime by an
assertion in `albc_env.py` (the env raises `ValueError` if the assembled obs does
not equal `observation_space = 69`).

### 2.1 Actor observation — 69D (`o_t`)

| Block | Composition | Dim |
|---|---|---:|
| Current proprioception | ang_cmd(3) + euler(3) + ang_vel(3) + joint_pos(2) + joint_vel(2) + manipulability(1) + thruster_state(6) | 20 |
| Joint/body history | (joint_err 4 + body_err 6) x 3 steps (`hist_len=3`) | 30 |
| Action history | full_action 8 x 2 steps (`hist_action_len=2`) | 16 |
| Integral error | leaky integrator [roll, pitch, yaw_rate] | 3 |
| **Total** | | **69** |

Source: `mdp/observations.py:compute_policy_obs()` (20D current) +
`albc_env.py:_get_observations()` (46D history + 3D integral). `policy_obs_dim=69`
at `agents/rsl_rl_ppo_cfg.py:138`.

### 2.2 Privileged observation — 27D (`p_t`)

Simulator-only ground truth (the domain-randomized physics parameters plus the
measured linear velocity, which has no real-robot sensor — there is no DVL).

| Group | Composition | Dim |
|---|---|---:|
| Hydrodynamics | volume(1) + CoG(3) + CoB(3) | 7 |
| Dynamic response | Ixx + linear/quadratic damping (roll) + body_mass + added_mass (surge) | 5 |
| Payload | mass(1) + CoG offset(3) | 4 |
| Actuator | Kp + Kd + thrust_coeff + time_constant_up | 4 |
| Environment | water_density(1) + ocean current velocity (3) | 4 |
| Measured velocity | body linear velocity u, v, w | 3 |
| **Total** | | **27** |

Source: `mdp/observations.py:compute_privileged_obs()`. The first 24D are DR
params; the last 3D is measured body linear velocity, critic-only — excluded from
`o_t` precisely because the real robot cannot measure it. `privileged_dim=27` at
`agents/rsl_rl_ppo_cfg.py:139`.

### 2.3 Action — 8D

| Index | Component | Mapping |
|---|---|---|
| `[0:2]` | arm joint delta (2D) | `q_des += 0.10 * a` (accumulated PD targets on `ALBC_JOINT_NAMES`) |
| `[2:8]` | thruster commands (6D) | T0-T5, fed to `ThrusterModel.apply_dynamics()`, allocated via the 6x6 TAM into a body-frame 6-DOF wrench |

Raw action is clamped to `[-1, 1]` before use (`albc_env.py`). The actor MLP emits
the action mean directly — **no output activation** (no tanh/softsign on the
action; softsign is applied only to the latent `z`).

### 2.4 Routing into the network

`_get_observations()` returns `{"policy": (N, 69), "privileged": (N, 27)}`. The
encoder consumes `privileged`; the actor consumes `policy + z`; the critic and cost
critic consume `policy + z + privileged`. The asymmetric split is **not** done
through the rsl-rl `obs_groups` path — both groups are declared
`["policy", "privileged"]` and the policy class slices them internally using the
`policy_obs_dim=69` and `privileged_dim=27` cfg fields.

---

## 3. Network layers (cfg -> dimensions)

The runtime network is built by flattening `_ALBCPolicyCfg` (in
`agents/rsl_rl_ppo_cfg.py`) to a dict, then `OnPolicyRunner` resolves
`class_name="ALBCActorCriticEncoder"` (`:153`) via `eval()` and passes the rest as
kwargs.

| Component | Input | Hidden | Output | Activation | cfg line |
|---|---|---|---|---|---|
| Encoder | 27 (`privileged_dim`) | [256, 128, 64] | 9 (`encoder_latent_dim`) | elu + LayerNorm + softsign | hidden `:130`, latent `:134`, act `:135` |
| Actor | 78 = 69 + 9 | [256, 128, 64] | 8 (`num_actions`) | elu | `:126`, act `:128` |
| Critic | 105 = 69 + 9 + 27 | [512, 256, 128] | 1 | elu | `:127`, act `:128` |
| Cost critic | 105 (same) | [512, 256, 128] | K | elu | `:160` |

- only `o_t` (69D) gets EmpiricalNorm in the actor; `z` is fed raw.
- `critic_uses_z=True` (`:154`) makes the critic input 105D (96D when False).
- `encoder_output_norm=True` (`:155`) adds the LayerNorm before softsign.
- the cost critic is only built when `num_constraints > 0`.

**Fields that actually decide the shape (live wires):** `policy_obs_dim=69`
(`:138`), `privileged_dim=27` (`:139`), `encoder_latent_dim=9` (`:134`),
`critic_uses_z=True` (`:154`), `encoder_output_norm=True` (`:155`),
`num_constraints` (auto-synced from the env, see §6), and the four `*_hidden_dims`
lists. Fields like `init_noise_std=0.7` (`:123`) and the `*_normalization` flags do
not change layer shapes.

**Encoder input normalization** is static min-max (HORA-style), not
`EmpiricalNormalization` (`encoder_obs_normalization=False`, `:136`): the cfg passes
a 27-element `_PRIV_OBS_LOWER` / `_PRIV_OBS_UPPER` and the encoder computes
`(2*p_t - (U+L)) / (U-L)`. It is deterministic with no running statistics, which
avoids `z` drift / KL spikes.

### 3.1 Class hierarchy

`PolicyBase(nn.Module)` is the common base (obs-group parsing, dim checks,
critic / cost_critic construction, the global `log_std` and Gaussian). Its
`forward()` raises `NotImplementedError`; the live entry points are
`act() / act_inference() / evaluate() / evaluate_costs()`. Two subclasses inherit
from it **as siblings**:

- `ActorCriticEncoder(PolicyBase)` — the encoder teacher policy (production
  default, `class_name="ALBCActorCriticEncoder"`).
- `ActorCriticAsymConstrained(PolicyBase)` — the NoEncoder ablation (actor sees
  only the 69D `o_t`, critic is `cat([o_t, p_t]) = 96D`,
  `class_name="ALBCActorCriticAsymConstrained"`, `:296`).

`ActorCriticAsymConstrained` does **not** inherit from `ActorCriticEncoder`.

---

## 4. Actor std handling

`std` is a **single global `log_std` parameter** (state-INDEPENDENT), broadcast
across the batch: `log_std = nn.Parameter(num_actions)`, `std = exp(log_std)`. There
is no per-state std head — `state_dependent_std` is not set in any `envs/main` cfg
(the per-state std head is a separate, unmerged experiment branch
`exp/attitude-only-state-std`).

| Field | Value | cfg line |
|---|---|---|
| init_noise_std | 0.7 | `:123` |
| min_std / max_std (clamp ceiling/floor) | 0.05 / 2.0 | `:221` / `:222` |
| min_std_per_dim (arm=0.10, thruster=0.05) | (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05) | `:225` |
| entropy_coef (scalar) | 0.003 | `:212` |
| entropy_coef_per_dim (arm=0.01, thruster=0.001) | (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001) | `:218` |

The clamp is **not** inside the policy class — `ConstraintTRPO` clamps `log_std`
per dimension after every update (see §5).

---

## 5. ConstraintTRPO + IPO update

Algorithm body: `algorithms/constraint_trpo.py`
(`class_name="ALBCConstraintTRPO"`, `:177`). Objective (from the module docstring):

```
maximize  E[A(s,a)] + (1/t) * sum_k log(d_k^i - J_hat_Ck)
s.t.      KL(pi || pi_i) <= delta
where     d_k^i = max(d_k, J_Ck + alpha * d_k)
```

Per-update flow:

```
ROLLOUT -> reward GAE + per-constraint cost GAE (K constraints, cost storage shape (T,N,K))
  |
update():
  - IPO adaptive thresholds:  d_k^i = max(d_k, J_Ck + alpha*d_k)   # raise threshold on violation, avoid -log blow-up
  - surrogate = -E[adv*ratio]  +  (-sum log(margin)/t)  +  (-entropy bonus)
       g = grad(surrogate) over policy_params (actor + encoder + log_std);  clip |g| <= 1.0
       nat_grad = CG(F^-1 g, cg_iters=10);  FVP: F*v = grad^2 KL(Normal)*v + cg_damping*v
       step = -sqrt(max_kl / (0.5 * nat_grad^T g)) * nat_grad
       line search: accept iff delta_surrogate > 0 AND KL <= max_kl * 1.5  (backtrack x10)
  - clamp log_std to [log min_std, log max_std]  (per-dim)
  - Adam MSE on critic + cost_critic (num_learning_epochs x num_mini_batches)
```

**Parameter-group split** (by name prefix): names matching
`("critic.", "cost_critic.")` go to an **Adam** optimizer (`value_lr`); all
other params — actor MLP, `encoder.*`, and the bare `log_std` — go to the
**TRPO natural-gradient** group. The encoder is deliberately kept in the policy
group (decoupling it caused a measured ~85% encoder-gradient drop, per a code
comment); `log_std` is in the policy group so the KL trust region damps entropy
collapse.

**FVP / log_std.** The Fisher-vector product computes a pure KL Hessian on the
`Normal(action_mean, action_std)` distribution. Since `action_std = exp(log_std)`,
`log_std` **does** contribute to the Fisher curvature and to the surrogate KL — it
is not "logging-only". The `_sigma_param_offset` index merely slices the sigma
component out of the flat step for logging.

### 5.1 Key hyperparameters

| Group | Values | cfg line |
|---|---|---|
| Trust region / KL | `max_kl=0.005`, `cg_iters=10`, `cg_damping=0.1`, line-search backtracks=10, shrink=0.5, kl_margin=1.5 | `:180-184` |
| IPO barrier | `barrier_t=100.0`, `barrier_alpha=0.05` (both fixed — no scheduling) | `:206` / `:207` |
| Critic (Adam) | `num_learning_epochs=5`, `num_mini_batches=4`, `value_lr=1e-3`, `value_loss_coef=1.0`, `cost_value_loss_coef=1.0`, `max_grad_norm=1.0` | — |
| GAE | `gamma=0.99`, `lam=0.95`, `cost_gamma=0.99`, `cost_lam=0.95` | — |

---

## 6. Cost critic and constraints (K)

A separate cost critic network **exists**, and it is a **single multi-head MLP**
(not one network per constraint):

- **Architecture**: identical 105D asymmetric input (`cat[o_t, z, p_t]`), hidden
  `[512, 256, 128]`, activation `elu` — same shape as the reward critic but with K
  scalar outputs. Built only when `num_constraints > 0`, else `None`
  (`_policy_base.py`). cfg `cost_critic_hidden_dims` at `:160`.
- **Heads**: K scalar outputs, one head per constraint (`evaluate_costs()` returns
  K values from the same critic_obs). Cost returns/advantages are shaped `(T,N,K)`.
- **Naming convention**: the `cost_critic.*` prefix is what routes it to the Adam
  value optimizer instead of the TRPO natural-gradient group.

**`num_constraints` (K) is runtime-resolved.** The static cfg default is `0`
placeholder (`:159`); `constraint_encoder_runner.py` overwrites it from
`len(cfg.constraints.terms)` before `super().__init__()`, so `cost_critic` is sized
correctly at build time.

### 6.1 K on this branch

On `main` and with `joint1_constraint_arm="none"` (the default), **K = 10**
(5 probabilistic + 5 average), defined in `envs/main/config.py` constraint terms.

On the `exp/joint1-constraint-redesign` branch, `config.py` adds an
**off-by-default** joint1 anti-drift constraint:

- `joint1_constraint_arm: str = "none"` (one of `"none"`, `"A"`, `"B"`),
  `joint1_constraint_budget: float = 0.05` (per-step average budget `d_k`).
- When set to `"A"` or `"B"`, `apply_joint1_constraint_arm()` (called from
  `ALBCEnv.__init__`, not a cfg `__post_init__`) appends one extra constraint term
  → **K = 11**, so the cost critic gets **one additional head**.
- `"B"` selects `joint1_cumulative_cost` (average of the commanded integrator);
  `"A"` selects the measured-angle variant.

The MLP layer counts, dims, and activations are **unchanged** by the constraint
choice — only the cost-critic output width (K) moves.

---

## 7. Where to change what (next-experiment knob map)

Unless noted, all in `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py`.

| Architecture knob | Value | Location (file:line) |
|---|---|---|
| actor hidden | [256, 128, 64] | `:126` |
| critic hidden | [512, 256, 128] | `:127` |
| cost_critic hidden | [512, 256, 128] | `:160` |
| actor/critic activation | elu | `:128` |
| encoder hidden | [256, 128, 64] | `:130` |
| encoder activation | elu | `:135` |
| encoder_latent_dim (z) | 9 | `:134` |
| encoder_output_norm (pre-softsign LayerNorm) | True | `:155` |
| encoder static min-max bounds | `_PRIV_OBS_LOWER/UPPER` | bounds defined in same file |
| encoder_obs_normalization | False | `:136` |
| critic_uses_z (105D vs 96D) | True | `:154` |
| init_noise_std | 0.7 | `:123` |
| min_std / max_std (algo clamp) | 0.05 / 2.0 | `:221` / `:222` |
| min_std_per_dim | (0.10, 0.10, 0.05 x6) | `:225` |
| entropy_coef / per_dim | 0.003 / (0.01 x2, 0.001 x6) | `:212` / `:218` |
| max_kl / cg_iters / cg_damping | 0.005 / 10 / 0.1 | `:180-182` |
| barrier_t / barrier_alpha (IPO) | 100.0 / 0.05 | `:206` / `:207` |
| num_constraints (auto-sync K) | 0 -> runtime 10 (11 with joint1 arm) | `:159` (real K = `config.py` constraint terms) |
| policy_obs_dim / privileged_dim | 69 / 27 | `:138` / `:139` |
| joint1 constraint arm / budget (`exp/joint1-constraint-redesign` branch) | "none" / 0.05 | `envs/main/config.py` |

---

## 8. Notes and limitations

- **`state_dependent_std` does not exist in `envs/main`.** `std` is a single
  global `log_std` parameter broadcast across the batch. The per-state std head
  is a separate, unmerged experiment branch (`exp/attitude-only-state-std`).
- **No encoder auxiliary losses.** No reconstruction/KL/contrastive head on the
  encoder; the only inference hook is a default-disabled z-ablation
  (`mode=None`). This matches the project rule (reconstruction loss failed: the
  decoder ignored `z` and `z` collapsed).
- The exact runtime `K` and the physical meaning of each `_PRIV_OBS_LOWER/UPPER`
  entry are defined in the env config / `mdp/`; only the lengths (27 priv, 10/11
  constraints) were cross-checked here.
- This is a static code-structure reference. Runtime learning dynamics (e.g.
  whether `z` collapses) are a separate diagnostic concern — use
  `analysis/encoder_tools.py sweep`.

---

## Source files

- `constrained_albc/envs/main/encoder/_policy_base.py` — `PolicyBase`, global `log_std`, Gaussian, critic/cost_critic construction
- `constrained_albc/envs/main/encoder/actor_critic_encoder.py` — encoder, actor, asymmetric critic wiring
- `constrained_albc/envs/main/encoder/actor_critic_asym_constrained.py` — NoEncoder ablation policy
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — ConstraintTRPO + IPO
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — runner, `num_constraints` auto-sync
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `_ALBCPolicyCfg`, all dimensions and hyperparameters
- `constrained_albc/envs/main/config.py` — `ALBCEnvCfg`, observation/action space, joint1 constraint arm (`exp/joint1-constraint-redesign` branch)
- `constrained_albc/envs/main/albc_env.py` — obs assembly, action application
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` / `compute_privileged_obs`
- `constrained_albc/envs/main/mdp/constraints.py` — constraint terms (K), `apply_joint1_constraint_arm` (`exp/joint1-constraint-redesign` branch)
