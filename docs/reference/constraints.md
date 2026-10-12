# Constraints (`envs/main`)

> **Scope**: The constraint system of the default task `Isaac-ConstrainedALBC-TRPO-v0`
> (`constrained_albc/envs/main/`), the attitude-only ALBC policy. Ten IPO constraints ship on
> this task, **4 probabilistic** (binary violation-probability budgets) + **6 average**
> (expected-magnitude budgets), defined in `envs/main/config.py` (`_MAIN_CONSTRAINT_TERMS`) with
> cost functions in `envs/main/mdp/constraints.py`, and consumed by `ConstraintTRPO` in
> `constrained_albc/algorithms/constraint_trpo.py`.
>
> This is a code-level reference. Run-specific experiment results are not recorded here.

---

## 0. Key symbols

| Symbol | Meaning | Value |
|---|---|---|
| $K$ | number of constraint terms | 10 (§3) |
| $\pi$, $\pi_i$ | current policy / rollout policy at iterate $i$ | n/a |
| `ratio` | importance ratio $\pi(a\mid s)/\pi_i(a\mid s)$ in the surrogate objectives | n/a |
| $D_k$ | per-step cost budget for term $k$ | `_MAIN_CONSTRAINT_TERMS` in `config.py` |
| $d_k$ | discounted budget, $d_k = D_k/(1-\gamma_c)$ | computed in `ConstraintTRPO.__init__` |
| $\gamma_c$ / $\lambda_c$ | cost discount / GAE lambda (`cost_gamma`/`cost_lam`) | `0.99` / `0.95` |
| $\hat{J}_{C_k}$ | mean discounted cost return, a GAE($\lambda_c$) estimate rather than a raw Monte-Carlo sum | §4.3 |
| $d_k^{i}$ | IPO adaptive threshold, $\max(d_k,\ \hat J_{C_k}+\alpha d_k)$ | §4.2 |
| $\alpha$ (`barrier_alpha`) | IPO threshold slack, **not** DORAEMON's `alpha` feasibility floor (§6) | 0.05 (§4.1) |
| $t$ (`barrier_t`) | IPO barrier sharpness | 100.0 (§4.1) |
| $\delta_{\max}$ (`max_kl`) | TRPO trust-region KL budget | 0.005 (§4.4) |
| $A(s,a)$ | reward (policy) advantage, standardized | surrogate reward term (§4.4) |
| $\hat{A}^C_k$ | per-constraint ($K$-vector) cost advantage, standardized | `cost_surr_k` (§4.1, §4.3) |
| $H$ / $\beta_{\text{ent}}$ | policy entropy / its coefficient (the per-dim coefficients win when set, §4.5) | entropy bonus in the §4.4 surrogate |

Shared terms (ConstraintTRPO, IPO, TRPO, DORAEMON, ALBC): see [glossary.md](glossary.md).

---

## 1. Overview

Three layers, cleanly separated: **definitions** decide what each cost measures, **optimization**
decides how a cost budget is enforced, **wiring** decides which budgets/hyperparameters reach a run.

| Layer | File | Role |
|---|---|---|
| Definitions (cost functions) | `mdp/constraints.py` | per-step cost functions, each returning a `(num_envs,)` non-negative tensor; `compute_all_costs()` stacks them into `(num_envs, K)` every step |
| Optimization (ConstraintTRPO + IPO log-barrier) | `constraint_trpo.py` | folds an interior-point log-barrier on the $K$ cost budgets into the TRPO surrogate, with no separate Lagrangian dual and no projection step; a single joint scalar drives the natural-gradient step |
| Wiring (budgets) | `config.py` | binds each cost function to $D_k$ and a name; the algorithm rescales to $d_k = D_k/(1-\gamma_c)$ and compares it to the batch's mean discounted cost return |

```
cost function f_k(state)  ->  compute_all_costs -> costs (num_envs, K)   [mdp/constraints.py]
        |
        v  per-step cost, one column per constraint
cost GAE (cost_gamma, cost_lam)  ->  J_hat_C_k  (mean discounted cost return, K-vector)
        |
        v
IPO adaptive threshold:  d_k^i = max(d_k, J_hat_C_k + alpha * d_k)
        |
        v
barrier margin_k = d_k^i - cost_surr_k          # plain difference, NOT / d_k
barrier = -sum_k log(margin_k.clamp(min=1e-8)) / barrier_t
        |
        v
surrogate L = -E[A * ratio]  +  barrier  -  entropy_bonus
        |
        v
TRPO natural-gradient step under a pure-KL trust region (barrier curvature NOT in Fisher)
```

`ConstraintTRPO` contains no code that distinguishes probabilistic from average constraints:
all $K$ columns flow through the same GAE, standardization, adaptive-threshold, and barrier
code. The probabilistic/average split lives entirely in how each cost signal is computed
(`mdp/constraints.py`), never in how the optimizer consumes it.

---

## 2. Constraint taxonomy: probabilistic vs average

The 10 shipped constraints split 4 + 6, expressed only by list order and inline comments in
`config.py`. There is no `is_probabilistic`/`kind` field on `ConstraintTermCfg`; its only fields
are `func`, `params`, `budget`, `name`.

| Category | Cost signal | Budget $D_k$ meaning | Feasibility target |
|---|---|---|---|
| Probabilistic (4) | binary indicator $\mathbb{1}[\text{violated}] \in \{0,1\}$ | maximum violation *probability* | $\mathbb{E}[\mathbb{1}] \le D_k$ |
| Average (6) | continuous non-negative cost | maximum *expected magnitude* | $\mathbb{E}[\text{cost}] \le D_k$ |

Both categories are the same constrained-MDP object $\mathbb{E}[\sum_t \gamma_c^t c_k(s_t,a_t)]
\le d_k$; they differ only in what the per-step cost $c_k$ is. A probabilistic $c_k$ is a
$\{0,1\}$ indicator, so its discounted sum reads as a violation probability; an average $c_k$ is
a continuous magnitude, so the budget reads as an allowed mean level.

One consequence: the binary indicators' cost-advantage columns have near-zero variance, so
standardization floor-clamps the std to `min=1.0` to keep them from blowing up (§4.3).

---

## 3. The 10 constraint terms

Values are those of `_MAIN_CONSTRAINT_TERMS` in `config.py`. Discounted budget
$d_k = D_k / (1 - \gamma_c)$ with $\gamma_c = 0.99$, so $d_k = 100 \cdot D_k$.

The Paper column is the name used in the paper's constraint table (`table_constraints`).

| # | Name | Paper | Function | Key param / threshold | Budget $D_k$ | Type | Physically limits |
|---|---|---|---|---|---:|---|---|
| 0 | `attitude` | $c_{\mathrm{tilt}}$ | `attitude_limit_cost` | `limit=1.396` rad (80°) | 0.01 | prob | roll/pitch magnitude |
| 1 | `arm_torque` | $c_{\tau}$ | `torque_limit_cost` | `limit_nm=9.5` | 0.08 | prob | arm joint torque |
| 2 | `arm_joint_vel` | $c_{\dot\gamma}$ | `velocity_limit_cost` | `limit_rad_per_s=2.15` | 0.02 | prob | arm joint speed |
| 3 | `joint1_pos` | $c_{\mathrm{j1}}$ | `joint1_position_cost` | `limit_rad=4*pi` (720°) | 0.01 | prob | joint-1 cable winding |
| 4 | `thruster_util` | $c_{\mathrm{thr}}$ | `thruster_utilization_cost` | (no params) | 0.40 | avg | thruster authority use |
| 5 | `rp_rate` | $c_{\omega}$ | `rp_rate_cost` | `soft_threshold=0.5` rad/s | 0.10 | avg | roll/pitch angular rate |
| 6 | `yaw_rate` | $c_{\dot\psi}$ | `yaw_rate_cost` | `soft_threshold=0.55` rad/s | 0.10 | avg | yaw angular rate |
| 7 | `rp_vel_settling` | $c_{\omega,s}$ | `rp_vel_settling_cost` | `settling_threshold=0.087` (5°) | 0.20 | avg | roll/pitch settling |
| 8 | `yaw_settling` | $c_{\dot\psi,s}$ | `yaw_settling_cost` | `settling_threshold=0.087` (5°) | 0.20 | avg | yaw settling |
| 9 | `manipulability` | $c_{w_m}$ | `manipulability_cost` | `w_threshold=0.3` | 0.05 | avg | arm manipulability floor |

`cumulative_yaw_cost` (a $\mathbb{1}[\lvert\theta_{\text{yaw,cum}}\rvert > \text{limit}]$ indicator
on accumulated yaw) is still defined in `mdp/constraints.py` but is not in the shipped list;
with a yaw heading command the tether-wrap limit is an operational concern. The env's
`_cumulative_yaw` tracking and the `Episode/cumul_yaw_deg` log remain as a diagnostic.

A comment above the list in `config.py` records prior surgery: `thruster_rate` was removed
(structurally incompatible with `entropy_coef>0`) and `thruster_sat` was reverted to
`thruster_util` (average, budget 0.40, original form).

### 3.1 Probabilistic terms (`[0:4]`)

Each returns a $\{0,1\}$ indicator; the discounted-sum budget is a violation probability.

- **`attitude`**: $\mathbb{1}[\lvert\text{roll}\rvert > \text{limit} \ \lor\
  \lvert\text{pitch}\rvert > \text{limit}]$, $\text{limit}=1.396$ rad.
- **`arm_torque`**: $\mathbb{1}[\max_j \lvert\tau_j\rvert > 9.5\,\text{Nm}]$ on the post-clamp
  applied torque.
- **`arm_joint_vel`**: $\mathbb{1}[\max_j \lvert\dot q_j\rvert > 2.15\,\text{rad/s}]$.
- **`joint1_pos`**: $\mathbb{1}[\lvert\theta_1\rvert > 4\pi]$, i.e. joint-1 absolute angle past
  the $\pm 4\pi$ rail.

### 3.2 Average terms (`[4:10]`)

Each returns a continuous non-negative cost; the discounted-sum budget is an expected magnitude.

- **`thruster_util`**: takes no configurable threshold. Returns the per-env maximum absolute
  thruster state, $\max_i \lvert s_i \rvert$, the single control-authority channel among the 10.
- **`rp_rate`**: $\max(0,\ \max(\lvert p\rvert,\lvert q\rvert) - 0.5)$, roll/pitch body angular
  rate above the soft threshold.
- **`yaw_rate`**: $\max(0,\ \lvert\omega_z\rvert - 0.55)$, yaw rate above the soft threshold.
  0.55 rad/s caps the slew toward a heading target, so a $\pi$ turn takes at least 5.7 s.
- **`rp_vel_settling`**: $(\lvert p \rvert + \lvert q \rvert)/2$, masked to be nonzero only when
  $\max(\lvert e_{\text{roll}}\rvert,\lvert e_{\text{pitch}}\rvert) \le 0.087$ rad (5°). The mask
  gates on the attitude error, not on the angular velocity itself.
- **`yaw_settling`**: $\lvert\omega_z\rvert$, masked to be nonzero only when the wrapped heading
  error $\lvert e_{\text{yaw}}\rvert \le 0.087$ rad. It damps yaw oscillation about the target
  without opposing the turn toward it.
- **`manipulability`**: $\max(0,\ w_{\text{thr}} - w)$ with `w_threshold=0.3`, where $w$ is the
  normalized Yoshikawa manipulability index; cost accrues when the arm approaches a singularity.

`thruster_util` and `rp_rate` reduce with a spatial `max` inside the per-step cost, while
`rp_vel_settling` uses a mean and `yaw_rate`/`yaw_settling`/`manipulability` are single-quantity.
The "average" of an average constraint is the temporal expectation $\mathbb{E}[\sum_t
\gamma_c^t c_k]$, so a `max` only shapes the per-step signal and the bound is a time-averaged
peak that tolerates brief spikes, not a hard never-exceed bound.

### 3.3 Experiment-only joint1 term (not shipped)

One extra average cost function exists for joint1 anti-drift (§7) and is not in the shipped 10:

- **`joint1_cumulative_cost`**: $\lvert q^{\text{des}}_1 - q^{\text{nom}}_1 \rvert$, the unwrapped
  running command displacement (`env._joint_pos_targets[:, 0] - env._nominal_joint_pos[0]`). It
  is the sole joint1 anti-drift mechanism besides the `joint1_pos` indicator; there is no
  reward-side centering penalty.

### 3.4 Soft thresholds and the actuator hard caps

Constraint thresholds fall into two groups.

**Hard safety rails** (physically grounded):

| Constraint | Soft threshold | PhysX hard cap (`albc.py`) |
|---|---|---|
| `attitude` | 1.396 rad (80°) | none |
| `arm_torque` | `limit_nm=9.5` Nm | `effort_limit_sim=13.0` Nm (above the motor stall torque) |
| `arm_joint_vel` | `2.15` rad/s | `velocity_limit_sim=2.40` rad/s (the deployed driver speed cap) |
| `joint1_pos` | $4\pi$ (12.566 rad) | none (cable-wrap rail) |

Both arm rails sit **inside** the PhysX hard caps (`9.5 < 13.0`, `2.15 < 2.40`), so the soft
constraint bites before the hard clamp. This ordering must hold: a soft threshold above its hard
cap is silently dead, because PhysX clamps first and the cost can never fire.

**Soft shaping thresholds** (behavior envelopes, not safety limits):

| Constraint | Threshold | Budget $D_k$ |
|---|---|---|
| `rp_rate` | 0.5 | 0.10 |
| `yaw_rate` | 0.55 | 0.10 |
| `rp_vel_settling` | 0.087 | 0.20 |
| `yaw_settling` | 0.087 | 0.20 |
| `manipulability` | 0.3 | 0.05 |

The threshold sets where cost starts and $D_k$ sets how much is tolerated, so the two should be
tuned together per constraint rather than the budget alone.

---

## 4. ConstraintTRPO optimization

Algorithm body: `constrained_albc/algorithms/constraint_trpo.py`. `ConstraintTRPO` is a
standalone algorithm (aliased `ALBCConstraintTRPO` in `rsl_rl_ppo_cfg.py`), not an `rsl_rl.PPO`
subclass.

**Provenance.** The method follows the "Modified IPO" of Kim et al., "NORBC", IROS 2024 (named
in the module docstring): discounted budgets $d_k = D_k/(1-\gamma_c)$, a log-barrier on the
cost surrogates with an adaptive threshold $d_k^{i} = \max(d_k,\ \hat J_{C_k}+\alpha d_k)$,
per-constraint cost-advantage standardization, and a multi-head cost critic. The one divergence
is that the PPO step is replaced by a TRPO step.

### 4.1 IPO log-barrier

The interior-point objective (module docstring form):

$$
\begin{aligned}
\max_{\pi}\quad & \mathbb{E}\!\left[A(s,a)\right] + \frac{1}{t}\sum_{k} \log\!\left(d_k^{i} - \hat{J}_{C_k}\right) \\
\text{s.t.}\quad & \mathrm{KL}\!\left(\pi \,\|\, \pi_i\right) \le \delta_{\max} \\
\text{where}\quad & d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right)
\end{aligned}
$$

In code the barrier is built per update:

$$
\begin{aligned}
\text{margin}_k &= \underbrace{(d_k^{i} - \hat{J}_{C_k})}_{\text{barrier\_base}} - \text{cost\_surr}_k \\
\text{cost\_surr}_k &= \frac{1}{1-\gamma_c}\,\mathbb{E}\!\left[\text{ratio}\cdot \hat{A}^{C}_k\right] \\
\text{barrier} &= -\frac{1}{t}\sum_k \log\!\big(\text{margin}_k.\text{clamp}(\min=10^{-8})\big)
\end{aligned}
$$

Two implementation facts matter:

1. `margin` is a plain difference, never normalized by $d_k$.
2. `barrier_base = adaptive_d_k - mean_cost_returns` carries no explicit $1/(1-\gamma_c)$, while
   `cost_surr` is scaled by it. Both already live on the discounted-return scale through the
   budget rescale $d_k=D_k/(1-\gamma_c)$.

`clamp(min=1e-8)` caps the barrier so it never literally reaches infinity: it saturates at
$-\log(10^{-8})/t \approx 0.184$ per constraint, so a step whose reward-surrogate gain exceeds
that cap can cross the constraint boundary. The code comment marks the clamp as a numerical
guard that is not part of the NORBC formulation; the adaptive threshold re-anchors on the raw
cost return every iteration.

**Runtime constants: constructor default vs agent cfg.** The agent cfg
(`RslRlConstraintTRPOAlgorithmCfg` in `rsl_rl_ppo_cfg.py`) is what trained runs use:

| Field | Constructor default | Agent cfg (effective) |
|---|---|---|
| `barrier_t` | 100.0 | 100.0 |
| `barrier_alpha` | 0.02 | **0.05** |

When in doubt, read the resolved per-run `params/agent.yaml`, not the class signature.

### 4.2 Adaptive threshold and the violations diagnostic

The adaptive threshold is recomputed every update from the current batch's mean cost returns:

$$
d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right), \qquad
\hat{J}_{C_k} = \big(\text{mean cost return}\big)_k.\text{clamp}(\min=0)
$$

The logged `violations` metric compares $\hat{J}_{C_k}$ against the **raw** budget $d_k$, not the
adaptive threshold: `violations = mean_cost_returns - d_k`. The adaptive threshold is used only
inside the barrier margin and the logged barrier margin.

### 4.3 Feasibility, GAE, and standardization

- **Cost GAE.** Per-constraint advantages use the same recursive $\delta/\lambda$-return formula
  as reward GAE with `cost_gamma=0.99`, `cost_lam=0.95`, a vectorized $K$-dim accumulator run
  in reverse time, followed by a sanitize step that zeros any constraint column containing
  NaN/Inf. `cost_gamma` must be strictly $< 1$ or the constructor raises `ValueError`.
- **Feasibility level is an estimator.** `mean_cost_returns` (and so `barrier_base`,
  `violations`, the adaptive threshold) reads the GAE($\lambda_c$) return
  `cost_returns = cost_advantage + cost_value`, not a raw Monte-Carlo sum, so it inherits the
  `cost_lam` bias and the cost critic's estimation error. An under-estimating cost critic makes
  the barrier read feasible when the true cost already exceeds budget; this is inherent to
  critic-based constrained RL.
- **Time-out bootstrapping.** On time-out (not termination) the per-constraint cost is
  bootstrapped with `cost_gamma` and the per-constraint value vector.
- **Per-constraint cost-advantage standardization.** Each of the $K$ cost-advantage columns is
  independently mean/std-normalized across the flattened batch, with the std floor-clamped to
  `min=1.0` (not a `1e-8` epsilon) because binary constraints can have near-zero std, which
  would amplify by $10^8$.

The barrier margin mixes a raw level (`barrier_base` uses unstandardized `mean_cost_returns`)
with a standardized delta (`cost_surr` uses the standardized advantage). At `ratio=1` the
standardized advantage has zero mean, so $\text{margin}_k \approx d_k^i - \hat{J}_{C_k} \ge
\alpha d_k > 0$ and the log is defined at the start of every update. A constraint whose runtime
cost-advantage std exceeds 1 therefore gets a slightly more permissive effective boundary.

### 4.4 TRPO trust-region step

The natural-gradient step operates on the single combined surrogate scalar:

$$
L = -\,\mathbb{E}\!\left[A\cdot \text{ratio}\right] \;+\; \text{barrier} \;-\; \beta_{\text{ent}}\, H
$$

- **Gradient group.** $g = \nabla_\theta L$ over $\theta = (\text{actor}, \text{encoder},
  \log\sigma)$, with the gradient norm clipped to `max_grad_norm` before conjugate gradient.
- **Fisher-vector product uses pure KL curvature only**: a double backprop through the Gaussian
  KL between old and new policy, plus damping $Fv + \lambda_{\text{cg}} v$. The barrier's
  curvature never enters the Fisher, so the KL trust region does not know about the constraint
  geometry.
- **Conjugate gradient.** Solves $F x = g$ with `cg_iters=10` and an early exit when the
  residual norm squared falls below `1e-10`.
- **Step size.** $\Delta\theta = -\sqrt{\delta_{\max} / (\tfrac{1}{2}\tilde g^\top g)}\,\tilde
  g$ with $\tilde g = F^{-1}g$; the update is skipped if $\tfrac{1}{2}\tilde g^\top g \le 0$,
  or non-finite, or if the step direction contains NaN/Inf.
- **Line search.** Backtracking with shrink factor `0.5` and at most 10 backtracks; a step is
  accepted iff the surrogate strictly decreases and realized $\mathrm{KL} \le \delta_{\max}\cdot
  \text{line\_search\_kl\_margin}$ with margin `1.5`. The margin is looser than the
  $\delta_{\max}$ used to size the initial step, so an accepted step can exceed the nominal
  radius by up to 50%. On exhaustion the parameters revert to the old values.

**Trust-region values** (constructor vs agent cfg): `max_kl` is 0.002 in the constructor and
**0.005** in the agent cfg, which wins. `cg_damping=0.1` and `line_search_kl_margin=1.5` agree
between the two.

### 4.5 std clamping and entropy

After every `_trpo_step`, `log_std` is clamped (regardless of line-search success). Both the
std floor and the entropy coefficient exist as a scalar and as a per-dim field; the per-dim
field wins whenever it is non-empty, which the agent cfg always sets, so the scalars are dead
at runtime.

| Field (scalar) | Scalar value | Per-dim field | Per-dim value (effective) |
|---|---|---|---|
| `min_std` | 0.05 (agent cfg); constructor default 0.01 | `min_std_per_dim` | `(0.10, 0.10, 0.05 x 6)`: arm dims floor 0.10, thruster dims floor 0.05; `max_std=2.0` |
| `entropy_coef` | 0.003 | `entropy_coef_per_dim` | `(0.01, 0.01, 0.001 x 6)` |

### 4.6 Cost critic

**Two disjoint parameter groups, two update rules.**

| Group | Members | Update rule |
|---|---|---|
| Policy | actor + encoder + `log_std` | TRPO natural gradient, no optimizer object |
| Value | parameters whose names start with `critic.` / `cost_critic.` / `value_backbone.` / `reward_head.` / `cost_head.` | Adam at `value_lr` |

`log_std` is kept in the policy group so the KL trust region bounds noise changes. The encoder
stays in the policy group; a code comment records that decoupling it dropped encoder gradients
by about 85%.

**Single multi-head cost critic.** One network producing a $K$-dimensional vector per
observation (`evaluate_costs()`), not $K$ separate networks. Reward and cost critics update
jointly in one backward pass: $\text{total} = \text{value\_loss\_coef}\cdot L_V +
\text{cost\_value\_loss\_coef}\cdot L_{V_C}$, both coefficients `1.0`. The per-constraint MSE is
averaged over the batch and then over the $K$ constraints.

`critic` (scalar) and `cost_critic` ($K$-dim) are independent MLPs with disjoint parameters and
no shared trunk, so the backward pass does not couple their gradients. One thing does couple
them: the value update applies a single `clip_grad_norm_(value_params, max_grad_norm=1.0)` over
the union of both critics' parameters, so a large cost-critic gradient shrinks the reward
critic's step as well.

---

## 5. Reading the logged margin

The optimizer stores an absolute margin; any binding/slack judgment must normalize by $d_k$
first. The discounted budgets $d_k = 100 \cdot D_k$ span a 40x range across the 10 constraints
(`attitude` $d_k=1.0$ from $D_k=0.01$, vs `thruster_util` $d_k=40.0$ from $D_k=0.40$), so a
constraint deep in slack with a large budget shows a large absolute margin while one near its
budget with a small budget shows a small one. The normalized quantity is

$$
\frac{\hat{J}_{C_k}}{d_k} = 1 - \frac{\text{margin}_k}{d_k},
$$

valid only in the slack regime where the adaptive floor has not engaged, i.e. where
`Constraint/viol/<name> == -Constraint/margin/<name>` exactly. When $\hat{J}_{C_k} + \alpha d_k
> d_k$ the adaptive threshold engages and $d_k^i \ne d_k$, which breaks that identity.

---

## 6. DORAEMON and constraints

DORAEMON is the domain-randomization curriculum (mechanics in
[domain-randomization-and-doraemon.md](domain-randomization-and-doraemon.md)). Its `alpha` is a
feasibility floor on the estimated success rate (default 0.5): it gates whether a
curriculum-difficulty step is accepted. It is unrelated to `barrier_alpha` despite the shared
name. Success is `accumulated_episode_return >= performance_lb`; the base config sets
`DoraemonCfg(enable=True, kl_ub=0.12, performance_lb=250.0, step_interval=250)`.

---

## 7. joint1 anti-drift experiment

An off-by-default toggle can append an 11th constraint term for joint-1 anti-drift.

| Field (on `ALBCEnvCfg`) | Default | Meaning |
|---|---|---|
| `joint1_constraint_arm` | `"none"` | one of `{"none", "B"}` |
| `joint1_constraint_budget` | `0.05` | per-step average budget $D_k$ for the joint1 term |

`apply_joint1_constraint_arm()` (`mdp/constraints.py`) reads the arm: `"none"` is a no-op; `"B"`
appends a `joint1_cumulative_cost` term named `joint1_cumulative`; anything else raises
`ValueError`. It appends via `env_cfg.constraints.terms = [*env_cfg.constraints.terms, term]`
without mutating the shared module-level list.

It is called from `ALBCEnv.__init__`, not from a cfg `__post_init__`: Hydra's overrides land
after the cfg `__post_init__` but before `ALBCEnv.__init__` runs, so a `__post_init__` call
would always see `"none"` and silently produce a baseline duplicate. With `"none"` the shipped
10-term set is untouched.

---

## 8. Logging / metrics

Constraint metrics are emitted once per training iteration by
`ConstraintEncoderRunner._log_constraint_metrics`
(`constrained_albc/algorithms/runners/constraint_encoder_runner.py`). The algorithm keeps
running state (`_last_violations`, `_last_barrier_margins`, `_last_barrier_penalty`) read only
for this logging.

| Metric | Meaning |
|---|---|
| `Constraint/viol/<name>` | $\hat{J}_{C_k} - d_k$ against the raw discounted budget; negative means slack |
| `Constraint/margin/<name>` | $d_k^i - \hat{J}_{C_k}$ (adaptive-threshold margin); absolute, not $d_k$-normalized |
| `Constraint/barrier_penalty` | aggregate scalar barrier penalty (no per-constraint suffix) |
| `Policy/line_search_success` | line-search accept flag this update |
| `Policy/entropy` | mean policy entropy |

The `<name>` suffix is the constraint's configured name (`ALBCConstraintCfg.constraint_names`),
falling back to the numeric index. DORAEMON curriculum metrics use a separate `DORAEMON/*`
namespace.

---

## Source files

- `constrained_albc/envs/main/mdp/constraints.py`: the cost functions, `ConstraintTermCfg`, `ALBCConstraintCfg`, `compute_all_costs`, `apply_joint1_constraint_arm` (`{none, B}`)
- `constrained_albc/envs/main/config.py`: `_MAIN_CONSTRAINT_TERMS` (the shipped 10 budgets), `doraemon`, joint1 toggles
- `constrained_albc/envs/main/config_noconstraint.py`: `ALBCNoConstraintEnvCfg` (empty constraint list, TRPO-NoIPO / PPO-Enc ablations)
- `constrained_albc/algorithms/constraint_trpo.py`: ConstraintTRPO + IPO barrier, adaptive threshold, cost GAE, TRPO step, std clamp, cost critic
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py`: `RslRlConstraintTRPOAlgorithmCfg` (runtime `barrier_alpha`, `max_kl`, std and entropy values)
- `constrained_albc/algorithms/runners/constraint_encoder_runner.py`: `_log_constraint_metrics`, `num_constraints` auto-sync
