# Main Network Architecture (`envs/main`)

> Verified against commit c5a8a08.

> **Scope**: Neural-network architecture of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`). This is the
> attitude-only ALBC policy (roll/pitch + yaw-rate, no linear-velocity command),
> with an 8D action (2D arm + 6D thruster), 69D actor observation, and 28D
> privileged observation.
>
> This is a code-level reference verified against disk. The legacy full-DOF
> variant (`envs/full_dof/`, `Isaac-ConstrainedALBC-Full-*-v0`, 87D obs / 24D
> privileged) is a different network and is **not** described here.

---

## 1. Overview

The policy is a teacher actor-critic in the RMA/HORA family: an **encoder**
compresses the 28D privileged physics vector into a 9D latent `z`; the **actor**
acts on the 69D observation plus `z`; an **asymmetric critic** sees the full
privileged information directly. The algorithm is `ConstraintTRPO` (a standalone
algorithm, not an `rsl_rl.PPO` subclass) with an IPO log-barrier on cost
constraints.

```
ENV obs dict  ->  {"policy": o_t (69D),  "privileged": p_t (28D)}

ENCODER  (input = p_t 28D, NOT the full observation)
  p_t(28D) -> static min-max normalize -> [-1, 1]   # HORA-style, deterministic, no running stat
          -> MLP[256, 128, 64]  (elu)
          -> LayerNorm(9)                            # pre-softsign
          -> softsign  ->  z (9D)                    # encoder_latent_dim = 9

ACTOR  (input 78D)
  cat[ EmpiricalNorm(o_t)(69D), z_raw(9D) ]          # only o_t is normalized; z is already softsign-bounded
          -> MLP[256, 128, 64]  (elu)
          -> action_mean (8D = 2D arm + 6D thruster)
  std = exp(global log_std[8]) -> expand             # state-INDEPENDENT
        init 0.7; clamped post-update by ConstraintTRPO

CRITIC  (asymmetric, input 106D, critic_uses_z = True)
  cat[ o_t(69D), z(9D), p_t(28D) ] (raw)             # value gradient flows back into the encoder through z
          -> MLP[512, 256, 128]  (elu) -> value (1D)

COST CRITIC  (multi-head, K = num_constraints)
  cat[ o_t(69D), z(9D), p_t(28D) ] (same 106D input)
          -> MLP[512, 256, 128]  (elu) -> cost_values (K)   # one head per constraint
```

**Key design choices.** The encoder input is the privileged physics vector
(unobservable on the real robot), not the observation — `z` tells the actor *what
physics this environment has*. The critic is asymmetric: it reads privileged
information directly (106D) while the actor only gets the compressed `z` (78D).
Because `critic_uses_z = True`, the value loss gradient flows back through `z`
into the encoder, so the encoder is trained by both the policy and the value
signal.

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
`albc_env.py:_get_observations()` (history + integral).

### 2.2 Privileged observation — 28D (`p_t`)

Simulator-only ground truth (the domain-randomized physics parameters plus the
measured linear velocity, which has no real-robot sensor — there is no DVL).
Union layout (2026-07-12): Ixx and linear damping roll were removed vs the old
27D layout; buoy volume/mass and control-action delay were added.

| Group | Composition | Dim |
|---|---|---:|
| Hydrodynamics | volume(1) + CoG(3) + CoB(3) | 7 |
| Dynamic response | quadratic damping (roll) + body_mass + added_mass (surge) | 3 |
| Payload | mass(1) + CoG offset(3) | 4 |
| Actuator | Kp + Kd + thrust_coeff + time_constant_up | 4 |
| Environment | water_density(1) + ocean current velocity (3) | 4 |
| Buoy | buoy volume(1) + buoy body_mass(1) | 2 |
| Latency | control-action delay (normalized steps, 0 when off) | 1 |
| Measured velocity | body linear velocity u, v, w | 3 |
| **Total** | | **28** |

Source: `mdp/observations.py:compute_privileged_obs()`. Linear velocity is
excluded from `o_t` precisely because the real robot cannot measure it; it
appears only in `p_t`.

### 2.3 Action — 8D

| Index | Component | Mapping |
|---|---|---|
| `[0:2]` | arm joint delta (2D) | `q_des += 0.10 * a` (accumulated PD targets on `ALBC_JOINT_NAMES`) |
| `[2:8]` | thruster commands (6D) | T0-T5, fed to `ThrusterModel.apply_dynamics()`, allocated via the 6x6 TAM into a body-frame 6-DOF wrench |

Raw action is clamped to `[-1, 1]` before use (`albc_env.py`).

### 2.4 Routing into the network

`_get_observations()` returns `{"policy": (N, 69), "privileged": (N, 28)}`. The
encoder consumes `privileged`; the actor consumes `policy + z`; the critic
consumes `policy + z + privileged`. The asymmetric split is **not** done through
the rsl-rl `obs_groups` path — both groups are declared `["policy", "privileged"]`
and the policy class slices them internally using the `policy_obs_dim=69` and
`privileged_dim=28` cfg fields.

---

## 3. Network layers (cfg -> dimensions)

The runtime network is built by flattening `_ALBCPolicyCfg` (in
`agents/rsl_rl_ppo_cfg.py`) to a dict, then `OnPolicyRunner` resolves
`class_name="ALBCActorCriticEncoder"` via `eval()` and passes the rest as kwargs.

| Component | Input | Hidden | Output | Activation | Notes |
|---|---|---|---|---|---|
| Encoder | 28 (`privileged_dim`) | [256, 128, 64] (`encoder_hidden_dims`) | 9 (`encoder_latent_dim`) | elu + LayerNorm + softsign | `encoder_output_norm=True` adds the LayerNorm |
| Actor | 78 = 69 + 9 | [256, 128, 64] (`actor_hidden_dims`) | 8 (`num_actions`) | elu | only `o_t` (69D) gets EmpiricalNorm |
| Critic | 106 = 69 + 28 + 9 | [512, 256, 128] (`critic_hidden_dims`) | 1 | elu | `critic_uses_z=True`; no normalization |
| Cost critic | 106 (same) | [512, 256, 128] (`cost_critic_hidden_dims`) | K | elu | only built when `num_constraints > 0` |

**Fields that actually decide the shape (live wires):** `policy_obs_dim=69`,
`privileged_dim=28`, `encoder_latent_dim=9`, `critic_uses_z=True`,
`encoder_output_norm=True`, `num_constraints` (auto-synced from the env), and the
four `*_hidden_dims` lists. Fields like `init_noise_std=0.7` and the
`*_normalization` flags do not change layer shapes.

**Encoder input normalization** is static min-max (HORA-style), not
`EmpiricalNormalization`: the encoder computes `(2*p_t - (U+L)) / (U-L)`. It is
deterministic with no running statistics, which avoids `z` drift / KL spikes.

The bounds `[U, L]` are **derived from the DR config** at runner build time
(`derive_priv_obs_bounds_from_dr()` in `envs/main/utils/priv_obs_bounds.py`,
injected by `ConstraintEncoderRunner.__init__` like the `num_constraints`
auto-sync), so bound = DR range exactly (margin 0) and a DR change auto-syncs.
The old hardcoded `_PRIV_OBS_LOWER/UPPER` in `agents/rsl_rl_ppo_cfg.py` remain
only as a construct-time fallback (still imported by `student/teacher.py`); they
had drifted from DR (payload-mass overflow, stale CoG-xy radius) — the reason for
the derivation refactor. A terminal `_assert_bounds_match_dr()` fails loud if a
future DR change desyncs the derived bounds. (Branch `exp/dr-derived-norm-bounds`,
audit item B1; see `docs/plans/2026-06-30-dr-derived-priv-obs-normalization-bounds.md`.)

### 3.1 Class hierarchy

`PolicyBase(nn.Module)` is the common base (obs-group parsing, dim checks,
critic / cost_critic construction, the global `log_std` and Gaussian). Two
subclasses inherit from it **as siblings**:

- `ActorCriticEncoder(PolicyBase)` — the encoder teacher policy (production
  default, `class_name="ALBCActorCriticEncoder"`).
- `ActorCriticAsymConstrained(PolicyBase)` — the NoEncoder ablation (actor sees
  only the 69D `o_t`, critic is `cat([o_t, p_t]) = 97D`).

`ActorCriticAsymConstrained` does **not** inherit from `ActorCriticEncoder`.

---

## 4. ConstraintTRPO + IPO update

Algorithm body: `algorithms/constraint_trpo.py`. Objective (from the module
docstring):

$$
\begin{aligned}
\max_{\pi}\quad & \mathbb{E}\!\left[A(s,a)\right] + \frac{1}{t}\sum_{k} \log\!\left(d_k^{i} - \hat{J}_{C_k}\right) \\
\text{s.t.}\quad & \mathrm{KL}\!\left(\pi \,\|\, \pi_i\right) \le \delta \\
\text{where}\quad & d_k^{i} = \max\!\left(d_k,\; J_{C_k} + \alpha\, d_k\right)
\end{aligned}
$$

Per-update flow:

```
ROLLOUT -> reward GAE + per-constraint cost GAE (K constraints)
  |
update():
  - IPO adaptive thresholds (raise threshold on violation, avoid -log blow-up)
  - build surrogate, take a natural-gradient TRPO step (see equations below)
  - clamp log_std to [log min_std, log max_std]  (per-dim)
  - Adam MSE on critic + cost_critic (num_learning_epochs x num_mini_batches)
```

The natural-gradient step inside `update()`:

$$
\begin{aligned}
\text{IPO threshold:}\quad & d_k^{i} = \max\!\left(d_k,\; J_{C_k} + \alpha\, d_k\right) \\
\text{surrogate:}\quad & L = -\,\mathbb{E}\!\left[A\cdot r\right] \;-\; \frac{1}{t}\sum_k \log(\text{margin}_k) \;-\; \beta_{\text{ent}}\, H \\
\text{gradient:}\quad & g = \nabla_{\theta} L \quad \text{over } \theta = (\text{actor},\, \text{encoder},\, \log\sigma),\quad \lVert g \rVert \le 1.0 \\
\text{natural grad:}\quad & \tilde{g} = F^{-1} g \;\;(\text{CG, } \texttt{cg\_iters}=10),\quad Fv = \nabla^2_{\theta}\,\mathrm{KL}(\mathcal{N})\,v + \lambda_{\text{cg}}\, v \\
\text{step:}\quad & \Delta\theta = -\sqrt{\frac{\delta_{\max}}{\tfrac{1}{2}\,\tilde{g}^{\top} g}}\;\tilde{g} \\
\text{line search:}\quad & \text{accept iff } \Delta L > 0 \ \text{and}\ \mathrm{KL} \le 1.5\,\delta_{\max}\quad(\text{backtrack} \times 10)
\end{aligned}
$$

where $r$ is the importance ratio, $H$ the policy entropy, $\beta_{\text{ent}}$ the
entropy coefficient, $\lambda_{\text{cg}}$ the CG damping, and $\delta_{\max}=\texttt{max\_kl}$.

**Parameter-group split** (by name prefix): names matching
`("critic.", "cost_critic.", ...)` go to an **Adam** optimizer (`value_lr`); all
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

**Std clamp.** `std` is the single global `log_std` parameter (not
state-dependent). After every update, `ConstraintTRPO` clamps `log_std` per
dimension: floor `min_std_per_dim = (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05,
0.05)` (arm dims = 0.10, thruster dims = 0.05), ceiling `max_std = 2.0`;
`init_noise_std = 0.7`.

### 4.1 Key hyperparameters

| Group | Values |
|---|---|
| Trust region / KL | `max_kl=0.005`, `cg_iters=10`, `cg_damping=0.1`, `line_search_max_backtracks=10`, `line_search_shrink_factor=0.5`, `line_search_kl_margin=1.5` |
| IPO barrier | `barrier_t=100.0`, `barrier_alpha=0.05` (both fixed — no scheduling) |
| Critic (Adam) | `num_learning_epochs=5`, `num_mini_batches=4`, `value_lr=1e-3`, `value_loss_coef=1.0`, `cost_value_loss_coef=1.0`, `max_grad_norm=1.0` |
| GAE | `gamma=0.99`, `lam=0.95`, `cost_gamma=0.99`, `cost_lam=0.95` |
| Entropy | `entropy_coef_per_dim = (0.01, 0.01, 0.001 x6)` (arm = 0.01, thruster = 0.001) |

`num_constraints` (K) is auto-synced by `constraint_encoder_runner.py` from the
env's constraints cfg before `super().__init__()`, so the placeholder `0` in the
policy cfg is overwritten at runtime; `cost_critic` is only built when K > 0.

---

## 5. Cost critic and constraints (K)

A separate cost critic network **exists**, and it is a **single multi-head MLP**
(not one network per constraint):

- **Architecture**: identical 106D asymmetric input (`cat[o_t, z, p_t]`), hidden
  `[512, 256, 128]`, activation `elu` — same shape as the reward critic but with K
  scalar outputs. Built only when `num_constraints > 0`, else `None`
  (`_policy_base.py`). cfg `cost_critic_hidden_dims` at `rsl_rl_ppo_cfg.py:181`.
- **Heads**: K scalar outputs, one head per constraint (`evaluate_costs()` returns
  K values from the same critic_obs). Cost returns/advantages are shaped `(T,N,K)`.
- **Naming convention**: the `cost_critic.*` prefix is what routes it to the Adam
  value optimizer instead of the TRPO natural-gradient group.

**`num_constraints` (K) is runtime-resolved.** The static cfg default is `0`
placeholder (`rsl_rl_ppo_cfg.py:180`); `constraint_encoder_runner.py` overwrites it from
`len(cfg.constraints.terms)` before `super().__init__()`, so `cost_critic` is sized
correctly at build time.

### 5.1 K on this branch

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

## 6. Where to change what (next-experiment knob map)

Unless noted, all in `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py`.

| Architecture knob | Value | Location (file:line) |
|---|---|---|
| actor hidden | [256, 128, 64] | `:145` |
| critic hidden | [512, 256, 128] | `:146` |
| cost_critic hidden | [512, 256, 128] | `:181` |
| actor/critic activation | elu | `:147` |
| encoder hidden | [256, 128, 64] | `:149` |
| encoder activation | elu | `:154` |
| encoder_latent_dim (z) | 9 | `:153` |
| encoder_output_norm (pre-softsign LayerNorm) | True | `:174` |
| encoder static min-max bounds | DR-derived (`derive_priv_obs_bounds_from_dr`), fallback `_PRIV_OBS_LOWER/UPPER` | `utils/priv_obs_bounds.py` |
| encoder_obs_normalization | False | `:155` |
| critic_uses_z (106D vs 97D) | True | `:173` |
| init_noise_std | 0.7 | `:142` |
| min_std / max_std (algo clamp) | 0.05 / 2.0 | `:242` / `:243` |
| min_std_per_dim | (0.10, 0.10, 0.05 x6) | `:246` |
| entropy_coef / per_dim | 0.003 / (0.01 x2, 0.001 x6) | `:233` / `:239` |
| max_kl / cg_iters / cg_damping | 0.005 / 10 / 0.1 | `:201-203` |
| barrier_t / barrier_alpha (IPO) | 100.0 / 0.05 | `:227` / `:228` |
| num_constraints (auto-sync K) | 0 -> runtime 10 (11 with joint1 arm) | `:180` (real K = `config.py` constraint terms) |
| policy_obs_dim / privileged_dim | 69 / 28 | `:157` / `:158` |
| joint1 constraint arm / budget (`exp/joint1-constraint-redesign` branch) | "none" / 0.05 | `envs/main/config.py` |

All line numbers above are in `agents/rsl_rl_ppo_cfg.py` unless noted otherwise.

---

## 7. Notes and limitations

- **`state_dependent_std` does not exist in `envs/main`.** `std` is a single
  global `log_std` parameter broadcast across the batch. The per-state std head
  is a separate, unmerged experiment branch (`exp/attitude-only-state-std`); it
  is not part of `main`.
- **No encoder auxiliary losses.** No reconstruction/KL/contrastive head on the
  encoder; the only inference hook is a default-disabled z-ablation
  (`mode=None`). This matches the project rule (reconstruction loss failed: the
  decoder ignored `z` and `z` collapsed).
- The exact runtime `K` (number of constraints) and the physical meaning of each
  `_PRIV_OBS_LOWER/UPPER` entry are defined in the env config / `mdp/`; only the
  length (28) was cross-checked here.
- This is a static code-structure reference. Runtime learning dynamics (e.g.
  whether `z` collapses) are a separate diagnostic concern — use
  `analysis/encoder_tools.py sweep`.

---

## 8. Design rationale and literature standing

Conclusions from a 2026-06-30 code + literature walk-through of the policy head
(std parameterization, action output, entropy). Each row records whether the
choice is a field standard or a project-specific extension, so future work knows
what rests on consensus vs. on our own measurements.

| Choice | Standing | Evidence |
|---|---|---|
| Global state-independent `log_std` | **Standard** for on-policy PPO/TRPO | "37 Implementation Details of PPO" (state-independent, init 0); HORA `self.sigma = nn.Parameter`; rsl_rl `state_dependent_std=False` default. State-dependent std is the SAC norm, not TRPO. |
| Linear action output (no tanh/clamp) | **Standard** for PPO/TRPO | raw Gaussian mean + env-side `[-1,1]` interpretation; tanh-squashing is a SAC trait (needs Jacobian correction). `MLP` last layer is linear (`last_activation=None`); `act()` does no clamping. |
| `min_std` floor / `max_std` cap | **Project-custom** (not in rsl_rl upstream) | floor = prevents premature std collapse / preserves exploration; cap = prevents divergence. Similar floors seen in some robot-RL repos (e.g. MoE-Loco "clip min std 0.05") but no standardized recipe. Applied after the TRPO step in `constraint_trpo.py`. |
| Entropy bonus added to TRPO | **Non-standard** (standard for PPO, not pure TRPO) | EnTRPO (arXiv:2110.13373) positions "TRPO + entropy regularization" as a *novelty* — if it were standard it would not be a paper. PPO routinely uses a positive `entropy_coef` (rsl_rl 0.01, IsaacLab AnymalB 0.005). |
| Per-dim entropy / min_std (arm vs thruster) | **Project-custom** | task-specific: arm dims collapse faster (by iter ~1404), so they get a stronger entropy push (0.01 vs 0.001) and a higher floor (0.10 vs 0.05). |

### 8.1 Why entropy collapses despite TRPO

A common misconception is that TRPO's KL trust region *prevents* entropy
collapse. It does not — the trust region bounds the **size** of each step, not
its **direction**. If the objective's gradient points toward smaller std at every
step, each step stays small but the policy walks steadily toward zero entropy;
the trust region only slows the descent. Two pressures push std down here:

1. **Surrogate (advantage).** Policy gradient raises the probability of
   high-advantage actions; for a Gaussian, concentrating probability on a chosen
   action *is* shrinking std. This is the structural PPO/TRPO-common pressure the
   trust region cannot block.
2. **IPO log-barrier (project-specific amplifier).** A large std occasionally
   samples constraint-violating actions, which shrinks the constraint margin
   `d_k - hat{J}_{C_k}` and lowers the barrier term `log(...)`. The barrier
   therefore adds pressure to reduce std so the policy stops sampling risky
   actions — i.e. constraints make the policy "cautious" (lower noise).

Because pure TRPO has only pressure 1 while we have 1 + 2, our entropy collapses
*faster* than vanilla TRPO, which is why a (project-custom) entropy bonus is
needed. Measured: `entropy_coef=0` -> noise collapses to 0.12; `entropy_coef=0.003`
-> noise recovers to 0.55. Pressure 2 is a mechanism inference plus general
constrained-RL literature support (constraints suppress exploration: ESB-CPO
arXiv:2302.14339; safe-RL review arXiv:2508.09128); it is **not** isolated by a
controlled experiment — see the deferred test in
`docs/plans/2026-06-30-entropy-collapse-ipo-barrier-experiment.md`.

---

## Source files

- `constrained_albc/envs/main/encoder/_policy_base.py` — `PolicyBase`, global `log_std`, Gaussian, critic/cost_critic
- `constrained_albc/envs/main/encoder/actor_critic_encoder.py` — encoder, actor, asymmetric critic wiring
- `constrained_albc/envs/main/encoder/actor_critic_asym_constrained.py` — NoEncoder ablation policy
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — ConstraintTRPO + IPO
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — runner, `num_constraints` auto-sync
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `_ALBCPolicyCfg`, all dimensions and hyperparameters
- `constrained_albc/envs/main/config.py` — `ALBCEnvCfg`, observation/action space
- `constrained_albc/envs/main/albc_env.py` — obs assembly, action application
- `constrained_albc/envs/main/mdp/observations.py` — `compute_policy_obs` / `compute_privileged_obs`
