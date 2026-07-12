# Constraints (`envs/main`)

> Verified against commit c5a8a08.

> **Scope**: The constraint system of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`), the attitude-only
> ALBC policy. Ten IPO constraints ship on this task — **5 probabilistic** (binary
> violation-probability budgets) + **5 average** (expected-magnitude budgets) —
> defined in `envs/main/config.py` and consumed by `ConstraintTRPO` in
> `algorithms/constraint_trpo.py`.
>
> This is a code-level reference verified against disk. The legacy full-DOF variant
> (`envs/full_dof/`, `Isaac-ConstrainedALBC-Full-*-v0`) reuses the same constraint
> list constant but is a different task and is **not** described here.

---

## 1. Overview

The constraint system is three layers with a clean separation: **definitions**
decide what each cost measures, **optimization** decides how a cost budget is
enforced, and **wiring** decides which budgets and hyperparameters reach a run.

1. **Definitions (cost functions).** `mdp/constraints.py` holds 10 per-step cost
   functions. Each returns a `(num_envs,)` non-negative cost tensor. `compute_all_costs()`
   stacks them into a single `(num_envs, K)` tensor every step
   (`constraints.py:326-332`).
2. **Optimization (ConstraintTRPO + IPO log-barrier).** `constraint_trpo.py`
   folds an interior-point log-barrier on the K cost budgets directly into the
   TRPO surrogate objective. There is no separate Lagrangian dual, no projection
   step — a single joint scalar drives the natural-gradient step.
3. **Wiring (budgets).** `config.py` binds each cost function to a per-step budget
   $D_k$ and a name; the algorithm rescales that to a discounted budget
   $d_k = D_k / (1 - \gamma_c)$ (`constraint_trpo.py:146-151`) and compares it to
   the batch's mean discounted cost return.

```
cost function f_k(state)  ->  compute_all_costs -> costs (num_envs, K)   [mdp/constraints.py]
        |
        v  per-step cost, one column per constraint
cost GAE (cost_gamma, cost_lam)  ->  J_hat_C_k  (mean discounted cost return, K-vector)
        |
        v
IPO adaptive threshold:  d_k^i = max(d_k, J_hat_C_k + alpha * d_k)         [constraint_trpo.py:306-308]
        |
        v
barrier margin_k = d_k^i - cost_surr_k          # plain difference, NOT / d_k
barrier = -sum_k log(margin_k.clamp(min=1e-8)) / barrier_t                  [constraint_trpo.py:454-464]
        |
        v
surrogate L = -E[A * ratio]  +  barrier  -  entropy_bonus                   [constraint_trpo.py:461,480]
        |
        v
TRPO natural-gradient step under a pure-KL trust region (barrier curvature NOT in Fisher)
```

The crucial structural fact: `ConstraintTRPO` contains **zero** code that
distinguishes probabilistic from average constraints. All K columns flow through
byte-identical GAE, standardization, adaptive-threshold, and barrier code. The
prob/avg split lives entirely in *how each cost signal is computed* upstream
(`mdp/constraints.py`) and in *documentation convention* (`config.py`), never in
how the optimizer consumes it.

---

## 2. Constraint taxonomy — probabilistic vs average

The 10 shipped constraints split 5 + 5. The split is expressed only by list order
and inline comments in `config.py` — `# --- Probabilistic (5) ---` above entries
`[0:5]` and `# --- Average (5) ---` above entries `[5:10]`
(`config.py:56`, `config.py:65`). There is **no** `is_probabilistic`/`kind`/`type`
field on `ConstraintTermCfg`; its only fields are `func`, `params`, `budget`, `name`
(`constraints.py:50-57`).

| Category | Cost signal | Budget $D_k$ meaning | Feasibility target |
|---|---|---|---|
| Probabilistic (5) | binary indicator $\mathbb{1}[\text{violated}] \in \{0,1\}$ | maximum violation *probability* | $\mathbb{E}[\mathbb{1}] \le D_k$ |
| Average (5) | continuous non-negative cost | maximum *expected magnitude* | $\mathbb{E}[\text{cost}] \le D_k$ |

Mathematically, both categories are the same constrained-MDP object
$\mathbb{E}[\sum_t \gamma_c^t c_k(s_t,a_t)] \le d_k$ — they differ only in what the
per-step cost $c_k$ is. A probabilistic constraint's $c_k$ is a $\{0,1\}$ indicator,
so its discounted sum is (up to the $\gamma_c$ discount) a violation count, and the
budget reads as a probability. An average constraint's $c_k$ is a continuous
magnitude, so the budget reads as an allowed mean level.

**The mechanism that treats them "differently" is not in the optimizer.** The
docstring at `constraints.py:14-24` numbers `[0]-[4]` as probabilistic and `[5]-[9]`
as average; that ordering plus the underlying cost-function math (indicator vs
continuous) is the entire distinction. At runtime `compute_all_costs`
(`constraints.py:326-332`) does `torch.stack([t.func(...) for t in cfg.terms], dim=-1)`
— identical treatment of all 10 terms. One consequence worth noting for the binary
indicators: their per-constraint cost-advantage columns have near-zero variance, so
the standardization step floor-clamps std to `min=1.0` specifically to keep those
binary channels from blowing up (see Section 4).

---

## 3. The 10 constraint terms

All values verbatim from `config.py:57-72`. Discounted budget $d_k = D_k / (1 - \gamma_c)$
with $\gamma_c = 0.99$, so $d_k = 100 \cdot D_k$.

| # | Name | Function | Key param / threshold | Budget $D_k$ | Type | Physically limits |
|---|---|---|---|---:|---|---|
| 0 | `attitude` | `attitude_limit_cost` | `limit=1.396` rad (80°) | 0.01 | prob | roll/pitch magnitude |
| 1 | `arm_torque` | `torque_limit_cost` | `limit_nm=9.5` | 0.08 | prob | arm joint torque |
| 2 | `arm_joint_vel` | `velocity_limit_cost` | `limit_rad_per_s=2.8` | 0.02 | prob | arm joint speed |
| 3 | `joint1_pos` | `joint1_position_cost` | `limit_rad=4*pi` (12.566) | 0.01 | prob | joint-1 absolute angle |
| 4 | `cumul_yaw` | `cumulative_yaw_cost` | `limit_rad=8*pi` (25.133) | 0.01 | prob | accumulated yaw rotation |
| 5 | `thruster_util` | `thruster_utilization_cost` | (no params) | 0.40 | avg | thruster authority use |
| 6 | `rp_rate` | `rp_rate_cost` | `soft_threshold=0.5` | 0.10 | avg | roll/pitch angular rate |
| 7 | `yaw_rate` | `yaw_rate_cost` | `soft_threshold=0.55` | 0.10 | avg | yaw angular rate |
| 8 | `rp_vel_settling` | `rp_vel_settling_cost` | `settling_threshold=0.087` | 0.20 | avg | roll/pitch settling |
| 9 | `manipulability` | `manipulability_cost` | `w_threshold=0.3` | 0.05 | avg | arm manipulability floor |

A comment directly above the list records prior surgery: `thruster_rate` was
removed ("structurally incompatible with `entropy_coef>0`: noise alone violates 5x")
and `thruster_sat` was reverted to `thruster_util` (average, budget 0.40, "original
form") — `config.py:53-54`.

### 3.1 Probabilistic terms (`[0:5]`)

Each returns a $\{0,1\}$ indicator; the discounted-sum budget is a violation
probability.

- **`attitude`** — $\mathbb{1}[\lvert\text{roll}\rvert > \text{limit} \ \lor\ \lvert\text{pitch}\rvert > \text{limit}]$, $\text{limit}=1.396$ rad.
- **`arm_torque`** — $\mathbb{1}[\max_j \lvert\tau_j\rvert > 9.5\,\text{Nm}]$.
- **`arm_joint_vel`** — $\mathbb{1}[\max_j \lvert\dot q_j\rvert > 2.8\,\text{rad/s}]$.
- **`joint1_pos`** — $\mathbb{1}[\lvert\theta_1\rvert > 4\pi]$, i.e. joint-1 absolute angle past the $\pm 4\pi$ rail.
- **`cumul_yaw`** — $\mathbb{1}[\lvert\theta_{\text{yaw,cum}}\rvert > 8\pi]$, accumulated (unwrapped) yaw.

### 3.2 Average terms (`[5:10]`)

Each returns a continuous non-negative cost; the discounted-sum budget is an
expected magnitude.

- **`thruster_util`** — `thruster_utilization_cost` takes **no configurable
  threshold** (it relies on `ConstraintTermCfg.params` default `{}`, `constraints.py:55`).
  Per its docstring (`constraints.py:20`) it returns the per-env maximum absolute
  normalized thruster state, $\max_i \lvert s_i \rvert$. This is the single
  control-authority channel among the 10.
- **`rp_rate`** — soft-thresholded roll/pitch angular-rate cost, hinged at
  $0.5$: cost accrues only above the soft threshold.
- **`yaw_rate`** — soft-thresholded yaw-rate cost, hinged at $0.55$.
- **`rp_vel_settling`** — the mean roll/pitch angular rate $(\lvert p \rvert + \lvert q \rvert)/2$,
  masked to be nonzero only when the attitude error is within `settling_threshold=0.087` rad
  ($5\,\text{deg}$) of target: cost is zero during transit (att error $>$ threshold) and active
  during settling (att error $\le$ threshold). The name matches the implementation
  (`constraints.py:206-228`). Note the caveat that `settling_threshold` gates on the *attitude
  error*, not on the angular velocity itself.
- **`manipulability`** — hinged below a manipulability floor `w_threshold=0.3`;
  cost accrues when the arm's manipulability measure drops below the floor.

The two multi-component average costs (`thruster_util`, `rp_rate`) reduce with a spatial
`max` ($\max_i \lvert s_i\rvert$, $\max(\lvert p\rvert,\lvert q\rvert)$) *inside* the
per-step cost — this is theoretically consistent, not a category error. The "average" of an
average constraint is the temporal/stochastic expectation $\mathbb{E}[\sum_t \gamma_c^t c_k]$;
the `max` only shapes the per-step signal $c_k$. So `max`-inside-average bounds a
**time-averaged peak** — a *soft* peak that tolerates brief spikes because the discounted
average smooths them. It is $\mathbb{E}[\max_i]$, **not** $\max_i \mathbb{E}$ and **not** a
hard "never exceed at any step" bound (that would need a probabilistic indicator).
`rp_vel_settling` uses a `mean` and `yaw_rate`/`manipulability` are single-quantity, so `max`
appears only where a multi-component reduction is needed.

### 3.3 Experiment-only joint1 term (not shipped)

One extra average cost function exists for the joint1-anti-drift experiment line
(Section 7); it is not in the shipped 10 (`constraints.py:26-29`):

- **`joint1_cumulative_cost`** — $\lvert q^{\text{des}}_1 - q^{\text{nom}}_1 \rvert$,
  the unwrapped running command displacement (`constraints.py:271`, using
  `env._joint_pos_targets[:, 0] - env._nominal_joint_pos[0]`). It is now the sole
  joint1 anti-drift mechanism: the wrapped-instantaneous constraint (formerly
  "arm A", `joint1_centering_cost`) and the reward-side centering penalty were
  both removed 2026-07.

### 3.4 Threshold provenance and the actuator hard-cap layering

Constraint thresholds are **not one uniform kind of hyperparameter** — they split into two
groups with opposite tuning rules.

- **Hard safety rails (physically grounded).** `attitude` (80° tilt safety), `arm_torque`
  (`limit_nm=9.5` = the arm motor **stall torque**), `arm_joint_vel` (`2.8` rad/s), `joint1_pos`
  ($4\pi$ cable-wrap rail), `cumul_yaw` ($8\pi$ tether-wrap rail). The two arm rails sit **inside**
  the asset's PhysX hard caps — `effort_limit_sim=13.0` Nm and `velocity_limit_sim=3.1` rad/s
  (measured XW540-T260 no-load plateau, 2026-07-06) (`marinelab/.../albc/albc.py:200-201`). So
  `9.5 < 13.0` and `2.8 < 3.1`: the **soft IPO constraint bites before the hard clamp** (intended
  layering), and the constraint stays alive because there is a live band above the threshold where
  the indicator can fire (matches §9: `arm_torque` $\hat J_C/d_k = 0.407$ fires; `arm_joint_vel`
  $0.031$ deep slack). **Invariant: the soft threshold must stay inside the hard cap.** Inverting
  it silently kills the constraint — the `velocity_limit_sim` $6.28 \to 3.1$ retrain (to match the
  real XW540 arm) was applied together with lowering `limit_rad_per_s` $4.189 \to 2.8$
  (2026-07-12), so `2.8 < 3.1` keeps the soft-inside-hard layering and avoids the dead-constraint
  trap. Fix documented in omx wiki
  `arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt.md`. Tune a rail only toward
  its **true physical value** (measurement/sysid-driven), never toward reward.
- **Soft shaping thresholds (judgment-chosen).** `rp_rate` (`0.5`), `yaw_rate` (`0.55`),
  `rp_vel_settling` (`0.087`), `manipulability` (`0.3`). These set where a graded hinge penalty
  begins — behavior/comfort envelopes, not safety limits — and **are** legitimate experimental
  tuning targets. Because the threshold sets *where* cost starts and the budget $D_k$ sets *how
  much* is tolerated, the two are coupled: co-tune (threshold, budget) per constraint rather than
  budget alone. Tuning the budget of a constraint whose threshold sits far from the operating
  point is a no-op — §9 shows 9/10 constraints slack, so most such tuning changes nothing until
  the change actually pushes the constraint toward binding. On a 1-GPU sequential rig this argues
  for **one-constraint-at-a-time** co-tuning measured against a baseline, not a joint grid sweep
  over a mostly-flat response surface (one cliff at `thruster_util`).

**`cumul_yaw` headroom (recorded, low priority).** $8\pi$ (4 rev) is $\approx 3.3\times$ the
observed operating peak ($\sim 1.22$ rev, §9 fully inert). A cosmetic trim to $6\pi$ (3 rev) stays
inert — a behavioral no-op safe to ride any future config touch; a *bind-intended* value would need
$\lesssim 2.5\pi$ and should weigh whether it fights normal yaw maneuvering.

---

## 4. ConstraintTRPO optimization

Algorithm body: `algorithms/constraint_trpo.py`. `ConstraintTRPO` is a standalone
algorithm (aliased `ALBCConstraintTRPO`, `rsl_rl_ppo_cfg.py:25`), not an `rsl_rl.PPO`
subclass.

**Provenance — this is NORBC's "Modified IPO", implemented faithfully (not a bespoke
hybrid).** The whole optimizer follows Kim et al., "Not Only Rewards But Also
Constraints: Applications on Legged Robot Locomotion", arXiv:2308.12517v4, 2024 (KAIST
Hwangbo lab), named in the module docstring (`constraint_trpo.py:16-18`). The mapping is
one-to-one: discounted budget $d_k = D_k/(1-\gamma_c)$ = NORBC Eq. (8); the trust-region
barrier objective with a **raw** $\hat{J}_{C_k}$ level plus a **standardized** cost
surrogate (§4.1, §4.3) = NORBC Eq. (10); the adaptive threshold
$d_k^i = \max(d_k, \hat{J}_{C_k} + \alpha d_k)$ = NORBC Eq. (11); the multi-head cost
critic = NORBC's shared-backbone cost value. NORBC swaps IPO's original PPO step for a
TRPO step (its stated choice — stable improvement + feasibility *checking*, not
enforcement). So the two theoretical "soft spots" documented below (the barrier
saturation cap in §4.1 and the raw-vs-standardized margin in §4.3) are NORBC's
**deliberate design, not implementation defects**. Detail + the independent-review
resolution: wiki `constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1.md`.

### 4.1 IPO log-barrier

The interior-point objective (module docstring form):

$$
\begin{aligned}
\max_{\pi}\quad & \mathbb{E}\!\left[A(s,a)\right] + \frac{1}{t}\sum_{k} \log\!\left(d_k^{i} - \hat{J}_{C_k}\right) \\
\text{s.t.}\quad & \mathrm{KL}\!\left(\pi \,\|\, \pi_i\right) \le \delta_{\max} \\
\text{where}\quad & d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right)
\end{aligned}
$$

In code the barrier is built per update (`constraint_trpo.py:454-464`):

$$
\begin{aligned}
\text{margin}_k &= \underbrace{(d_k^{i} - \hat{J}_{C_k})}_{\text{barrier\_base}} - \text{cost\_surr}_k \\
\text{cost\_surr}_k &= \frac{1}{1-\gamma_c}\,\mathbb{E}\!\left[\text{ratio}\cdot \hat{A}^{C}_k\right] \\
\text{barrier} &= -\frac{1}{t}\sum_k \log\!\big(\text{margin}_k.\text{clamp}(\min=10^{-8})\big)
\end{aligned}
$$

Two implementation facts matter. First, **`margin` is a plain difference, never
normalized by $d_k$** — there is no $\hat{J}_C / d_k$ division anywhere in the file.
Second, the two terms of the margin are on the **same discounted-cost scale but are
not multiplied by the same factor in code**: `barrier_base = adaptive_d_k - mean_cost_returns`
carries no explicit $1/(1-\gamma_c)$, while `cost_surr` is scaled by
`inv_one_minus_gamma` at `constraint_trpo.py:462` (both `mean_cost_returns` and
`adaptive_d_k` already live on the discounted-return scale via the budget rescale
$d_k = D_k/(1-\gamma_c)$). The `clamp(min=1e-8)` caps the barrier so it can never
literally reach $-\infty$/$+\infty$ even at/past infeasibility — concretely it
**saturates at $-\log(10^{-8})/t \approx 18.42/100 \approx 0.184$ per constraint**, so a
step whose reward-surrogate gain exceeds ~0.184 walks straight through the boundary.
This clamp is a numerical guard **not present in NORBC's Eq. (9)/(10)**; it silently
softens the interior-point "cannot cross" property near the boundary rather than
enforcing it hard. That is consistent with NORBC's soft, near-satisfaction design (no
hard per-step bound is claimed) and is self-correcting because the adaptive threshold
re-anchors on the raw cost return every iteration. (An earlier verbal claim in this
campaign that the barrier "diverges to $+\infty$ and auto-rejects the step" was wrong —
the clamp caps it.)

**barrier_t / barrier_alpha — the true runtime values (doc-drift warning).**
`barrier_t = 100.0` in both the class constructor default (`constraint_trpo.py:64`)
and the agent cfg (`rsl_rl_ppo_cfg.py:217`) — no drift. **`barrier_alpha` has a
confirmed drift**: the constructor default is `0.02` (`constraint_trpo.py:65`) but
the agent cfg — the value that actually reaches every trained run — is `0.05`
(`rsl_rl_ppo_cfg.py:218`). The `RslRlConstraintTRPOAlgorithmCfg` field is dispatched
to the constructor kwarg at build time, so **the effective value is 0.05, and the
0.02 constructor default is dead** whenever the cfg supplies the field. Some earlier
notes reported 0.02 (or a since-superseded 0.05-vs-0.02 wiki page); the code truth
is **0.05, injected from the agent cfg**. When in doubt, read the resolved per-run
`params/agent.yaml`, not the class signature.

### 4.2 Adaptive threshold and the violations diagnostic

The adaptive threshold is recomputed every update from the current batch's mean
cost returns (`constraint_trpo.py:306-308`, called at `:446`):

$$
d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right), \qquad
\hat{J}_{C_k} = \big(\text{mean cost return}\big)_k.\text{clamp}(\min=0)
$$

The reported `violations` monitoring metric compares $\hat{J}_{C_k}$ against the
**raw** budget $d_k$, *not* the adaptive threshold: `violations = (mean_cost_returns - self.d_k)`
(`constraint_trpo.py:447`). `adaptive_d_k` is used only inside the barrier margin
(`:454`) and the logged barrier margin (`:449`).

### 4.3 Feasibility, GAE, and standardization

- **Cost GAE.** Per-constraint advantages use the same recursive
  $\delta/\lambda$-return formula as reward GAE but with `cost_gamma=0.99`,
  `cost_lam=0.95`, a vectorized K-dim accumulator, run reverse in time, followed by
  a non-finite sanitize that zeros any constraint column containing NaN/Inf across
  the rollout (`constraint_trpo.py:285-300`). `cost_gamma` must be strictly $< 1$
  or the constructor raises `ValueError` (`:143-144`).
- **Feasibility level is an estimator, not the true return (coupling to the cost critic).**
  The cost return that drives every feasibility judgment — `mean_cost_returns`, which feeds
  `barrier_base`, `violations`, and the adaptive threshold (`constraint_trpo.py:443,447,454`) —
  is the **GAE($\lambda_c$) return** `cost_returns = cost_advantage + cost_value` (`:291`),
  *not* a raw Monte-Carlo discounted cost sum. So the constraint-satisfaction check inherits
  both the `cost_lam=0.95` bias and the cost critic's estimation error. This mirrors the reward
  side, but the consequence differs: a biased reward value only costs policy-gradient efficiency,
  whereas an *under-estimating* cost critic makes the barrier read **feasible** when the true
  cost return already exceeds the budget — an estimator-driven constraint-violation risk inherent
  to this design (shared by all critic-based constrained RL), not a code defect.
- **Time-out bootstrapping.** On time-out (not termination) the per-constraint
  cost is bootstrapped with `cost_gamma` and the per-constraint value vector,
  mirroring the reward-side bootstrap but on the cost channel
  (`constraint_trpo.py:264-266`).
- **Per-constraint cost-advantage standardization (NORBC Sec IV-B).** Each of the
  K cost-advantage columns is independently mean/std-normalized across the flattened
  batch dim, with the std floor-clamped to **`min=1.0`** (`constraint_trpo.py:437-438`).
  This is a deliberate anti-amplification choice, not the usual `1e-8` epsilon: the
  inline comment (`:436`) reads `# clamp(min=1.0): binary constraints can have
  near-zero std, causing 1e8 amplification.` Reward advantages are standardized
  separately with the ordinary `1e-8` guard (`:424-426`).
  - **The barrier margin therefore mixes a raw level with a standardized delta — and
    this is NORBC Eq. (10) verbatim, not a code bug.** `barrier_base` uses the
    unstandardized `mean_cost_returns`, while `cost_surr` uses the standardized advantage
    (`:454` vs `:462`). NORBC relies on the *zero-mean* half to keep the problem always
    feasible at `ratio=1`: then $\mathbb{E}[\hat{A}^C_k]\approx 0$, so
    $\text{margin}_k \approx d_k^i - \hat{J}_{C_k} \ge \alpha d_k > 0$ and the $\log$ is
    always defined at the start of each update. The *std* half is NORBC's
    gradient-conditioning trick for stacking 10+ constraints stably. The practical
    consequence — a constraint whose runtime cost-advantage std exceeds 1 gets a slightly
    **more permissive** effective boundary (the barrier responds in standardized units
    while the budget is raw) — is therefore **dormant unless some constraint's cost-adv
    std actually exceeds 1**, an empirical run-data question, not a bug to patch. Whether
    standardization strictly voids NORBC's near-satisfaction guarantee is a critique of
    NORBC itself, out of scope for this codebase.

### 4.4 TRPO trust-region step

The natural-gradient step operates on the **single combined surrogate scalar**
(`constraint_trpo.py:461,480`):

$$
L = -\,\mathbb{E}\!\left[A\cdot \text{ratio}\right] \;+\; \text{barrier} \;-\; \beta_{\text{ent}}\, H
$$

- **Gradient group.** $g = \nabla_\theta L$ over $\theta = (\text{actor}, \text{encoder}, \log\sigma)$.
- **Fisher-vector product uses pure KL curvature only** — a double backprop through
  the Gaussian KL between old and new policy, plus Tikhonov damping
  $Fv + \lambda_{\text{cg}} v$ (`constraint_trpo.py:354-365`). The barrier's
  curvature **never** enters the Fisher, so the KL trust region does not "know"
  about the constraint geometry.
- **Conjugate gradient.** Solves $F x = g$ with `cg_iters=10` and an early-exit
  residual tolerance `1e-10` (`:367-386`).
- **Step size.** $\Delta\theta = -\sqrt{\delta_{\max} / (\tfrac{1}{2}\tilde g^\top g)}\,\tilde g$;
  the update aborts (returns `False`, no step) if $\tfrac{1}{2}\tilde g^\top g \le 0$
  or non-finite, or if the step direction contains NaN/Inf (`:539-547`).
- **Line search.** Backtracking, shrink factor `0.5`, max 10 backtracks; accepts a
  step iff the surrogate strictly decreases **and** realized
  $\mathrm{KL} \le \delta_{\max}\cdot \text{line\_search\_kl\_margin}$ with margin
  `1.5` (`:400-410`). Note the acceptance bound is **looser** than the $\delta_{\max}$
  used to size the initial step, so an accepted step can exceed the nominal
  trust-region radius by up to 50%. On exhaustion, params revert to `old_params`.

**True trust-region values.** `max_kl` also drifts: constructor default `0.002`
(`constraint_trpo.py:43`) vs agent cfg `0.005` (`rsl_rl_ppo_cfg.py:191`) — the agent
cfg (0.005, 2.5× looser) wins. `cg_damping=0.1` and `line_search_kl_margin=1.5`
agree between constructor and cfg (no drift).

### 4.5 std clamping

After every `_trpo_step` (unconditional on line-search success), `log_std` is
clamped (`constraint_trpo.py:485-491`). At runtime the **per-dim floor branch is the
one exercised**, because `min_std_per_dim` is non-empty:

$$
\text{min\_std\_per\_dim} = (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05), \qquad \text{max\_std} = 2.0
$$

Arm dims (indices 0,1) floor at `0.10`; thruster dims (2-7) floor at `0.05`
(`rsl_rl_ppo_cfg.py:236`). The scalar `min_std=0.05` agent-cfg field is **dead** at
runtime whenever `min_std_per_dim` is non-empty (which it is by default) — only the
per-dim tensor is applied. The constructor's scalar defaults (`min_std=0.01`,
`min_std_per_dim=()`) would take the scalar branch, but the cfg overrides both.

The entropy bonus follows the same per-dim-wins pattern: agent-cfg
`entropy_coef_per_dim = (0.01, 0.01, 0.001×6)` (`rsl_rl_ppo_cfg.py:229`) overrides
the scalar `entropy_coef=0.003` (`:223`), which is therefore also dead at runtime.

### 4.6 Cost critic

- **Parameter-group split.** Two disjoint groups. The **policy group**
  (actor + encoder + `log_std`) is updated by the TRPO natural gradient — no Adam,
  no optimizer object; `log_std` is deliberately included so the KL trust region
  bounds noise changes, and the encoder is kept in this group because decoupling it
  dropped encoder gradients ~85% (code comment, `constraint_trpo.py:154-158`). The
  **value group** (matched by the `value_prefixes` tuple `critic.` / `cost_critic.` /
  `value_backbone.` / `reward_head.` / `cost_head.`) is updated
  by Adam at `value_lr` (`:160-186`).
- **Single multi-head cost critic.** The cost critic is **one** network producing a
  K-dimensional vector per observation (`evaluate_costs()`), **not** K separate
  networks. Reward and cost critics are updated jointly in one backward pass:
  $\text{total} = \text{value\_loss\_coef}\cdot L_V + \text{cost\_value\_loss\_coef}\cdot L_{V_C}$,
  both coefficients `1.0` (`constraint_trpo.py:591-605`). The per-constraint MSE is
  `.mean(dim=0)` over the batch giving a K-vector, then `.mean()` across constraints
  to a scalar (`:596-597`). Any activation detail of the critic heads lives in the
  policy class `ALBCActorCriticEncoder`, not in this file — see the network-architecture
  reference.
- **Separate networks, one shared gradient clip (the reward/cost coupling).** `self.critic`
  (scalar reward value) and `self.cost_critic` (K-dim) are two **independent** MLPs with
  disjoint parameters — no shared backbone (`encoder/_policy_base.py:86,91`); the
  `value_backbone.` entry in `value_prefixes` is a classification catch, not an actual shared
  trunk in `ALBCActorCriticEncoder`. Because the parameters are disjoint, the joint
  `total.backward()` does not cross-couple their gradients ($\partial L_{V_C}/\partial\,\theta_{\text{reward critic}} = 0$).
  **One thing does couple them:** the value update applies a *single*
  `clip_grad_norm_(self._value_params, max_grad_norm=1.0)` over the **union** of both critics'
  parameters (`constraint_trpo.py:601-605`). The cost critic has $K=10$ heads regressing
  rare-event returns, so its gradient can dominate the combined norm; when the union norm
  exceeds `1.0` the clip scales *both* critics down by the same factor, letting a noisy cost
  critic throttle the reward critic's effective step. A real coupling between two otherwise-
  independent networks — flagged, not proven harmful (needs a runtime value-group grad-norm
  check to confirm it bites).

---

## 5. Constraint-margin normalization ($\hat{J}_C / d_k$)

**The optimizer stores an absolute margin; any binding/slack judgment must
normalize by $d_k$ first.** This is an analysis rule, not a code behavior: the
barrier uses the absolute margin correctly (Section 4.1), but a human or engine
reading `Constraint/margin/<name>` off TensorBoard must divide by $d_k$ to compare
across constraints.

Why it flips sign: the discounted budgets $d_k = 100 \cdot D_k$ span a **40×** range
across the 10 constraints (`attitude` $d_k = 1.0$ from $D_k=0.01$, vs `thruster_util`
$d_k = 40.0$ from $D_k=0.40$). A constraint deep in slack but with a large budget
has a large absolute margin; a constraint near its budget but with a small budget
has a small absolute margin. Reading the raw margin therefore inverts the
conclusion.

The correct normalized quantity is

$$
\frac{\hat{J}_{C_k}}{d_k} = 1 - \frac{\text{margin}_k}{d_k},
$$

valid **only in the slack regime**, where the adaptive floor has not engaged, i.e.
where `Constraint/viol/<name> == -Constraint/margin/<name>` exactly
(`constraint_trpo.py:447` vs `:449`). When
$\hat{J}_{C_k} + \alpha d_k > d_k$ the adaptive threshold engages and $d_k^i \ne d_k$,
breaking that identity.

**Experimental finding (labeled as such).** A real teacher-run report
(`report.md:174,180`) misread `attitude` and `cumul_yaw` as a "binding family"
because their absolute margins looked numerically small — when in fact
$\hat{J}_C/d_k = 0.003$ and $0.000$ respectively (the *deepest* slack), while the
genuinely binding `thruster_util` ($\hat{J}_C/d_k \approx 0.87$) has a *large*
absolute margin simply because its budget is large. The engine normalizes since commit `4ff9ea1`
(2026-06-07): `.omx/profile/analyze_training.py` computes `_constraint_binding_ratio`
(`:416-430`, $1 - \text{margin}/d_k$) and prints a `JC/dk=` column that flags the
binding channel by max ratio (`:809`, `:820`), pinned by
`test_constraint_margin_norm.py`. The low-level `_constraint_margin()` helper
(`:370-379`) still returns the raw absolute margin, which its consumer (`:803`)
normalizes. Like the manual formula, the engine ratio is exact only in the slack
regime and saturates at $1-\alpha = 0.95$ for a genuinely-binding channel (it
consumes the frozen margin). Source: omx wiki
`constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md`.

---

## 6. DORAEMON and constraints

DORAEMON is the domain-randomization curriculum. Its interaction with the
constraint/feasibility machinery is the point here; the DR mechanics live in
marinelab. The main env overrides four fields
(`config.py:527`): `DoraemonCfg(enable=True, kl_ub=0.12, performance_lb=250.0, step_interval=250)`.

- **`alpha` is a feasibility floor, not a DR lever.** DORAEMON's `alpha`
  (cited as `0.5` in the config reasoning comment, `config.py:521`; the literal
  field default comes from marinelab's `DoraemonCfg`, unverified in the read files)
  gates whether a curriculum-difficulty step is *accepted* — it does not directly
  widen randomization. **Experimental finding:** raising `alpha` `0.50 -> 0.75` (E5,
  run `trpo_260606_225859`) was a near-null intervention because `success_rate`
  stayed saturated at `0.96-0.99` the whole run, so the floor never gated a step.
  The actually-binding constraint on DR-expansion speed is the per-update
  trust-region KL (`kl_ub`, pinned at 0.06 in that run). To widen robustness you
  must move `kl_ub` or DR variance directly, **not** the success floor. Source: omx
  wiki `doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md`.

- **`performance_lb` and `kl_ub` were raised together by design**
  (`config.py:514-526`). `performance_lb` went `68.0 -> 250.0` and `kl_ub` went
  `0.06 -> 0.12`. The calibration used a recon run (`trpo_baseline_260608_160453`,
  1146 iter): its DORAEMON episode-return distribution was
  min=81.9 / p5=227 / p25=250 / median=264 / p95=291. With `lb=68` sitting *below*
  the minimum return, `success = return >= 68` was always `1`, so the feasibility
  constraint ($\hat G \ge \alpha$) was **inert** and the curriculum widened DR
  unconstrained (no self-pacing feedback). `lb=250` (p25) puts starting
  `success_rate` at ~0.65 — above `alpha=0.5` so the distribution still expands, but
  the signal is live again instead of pinned at 1; chosen below the median so a
  reward plateau cannot drag `success_rate` to 0. `kl_ub` was doubled to widen the
  distribution fast enough to compensate for the slower expansion the raised `lb`
  induces. The two levers move together by design: `lb` alone makes DR easier,
  `kl_ub` alone leaves `success_rate` pinned at 1.

- **`success` definition.** `success = accumulated_episode_return >= performance_lb`,
  computed in `albc_env.py` (`_episode_return_accum += reward`; `success = return >= performance_lb`;
  `config.py:515` comment).

`step_interval = 250` sets how often the curriculum updates.

---

## 7. joint1 anti-drift experiment

An off-by-default toggle can append an **11th** constraint term to test joint-1
anti-drift. Two fields on `ALBCEnvCfg`:

- `joint1_constraint_arm: str = "none"` — one of `{"none", "B"}` (`config.py:580`).
- `joint1_constraint_budget: float = 0.05` — per-step average budget $d_k$ for the
  joint1 term (`config.py:581`).

**Materialization path.** `apply_joint1_constraint_arm()` (`constraints.py:279-299`)
reads the arm; `"none"` is a no-op; `"B"` appends a `joint1_cumulative_cost` term
(name `joint1_cumulative`); anything else raises `ValueError` (including the
former `"A"`, which no longer exists). It appends via
`env_cfg.constraints.terms = [*env_cfg.constraints.terms, term]`.

**Why it is called from `ALBCEnv.__init__`, not a cfg `__post_init__`.** The call
site is `albc_env.py:128`, inside `ALBCEnv.__init__` (after payload-viz and
DR-sampler init). This is deliberate: hydra's `update_class_from_dict` override lands
*after* the cfg `__post_init__` but *before* `ALBCEnv.__init__` runs
(`constraints.py:279-291`, `albc_env.py:123-127`). Putting the call in
`__post_init__` would always observe `arm="none"` and silently produce a
baseline-duplicate run instead of arm B.

**Sole anti-drift mechanism.** Arm B (`joint1_cumulative_cost`) is now the only
joint1 anti-drift mechanism in the codebase. Both the reward-side centering
penalty and the wrapped-instantaneous constraint (formerly "arm A") were removed
2026-07, so the earlier "set the reward's centering coefficient to 0.0 to avoid
double-counting" requirement no longer applies — there is nothing left to
double-count against.

**Behavior — never binds under station-keeping (experimental finding).** In a
flat-target station-keeping task the joint1-cumulative constraint essentially never
binds: the policy naturally parks around **0.36 revolutions**, deeply inside the
$\pm 4\pi$ (2-rev) rail, with the violation metric sitting at **-0.9997** (near-full
headroom) every iteration and peak $\lvert\theta_{\text{cum}}\rvert$ never exceeding
~1.22 rev across any of 4 DR difficulty levels (0/64 envs $> 4\pi$). Source: omx wiki
`joint1_cumulative_rotation_constraint_never_binds_policy_parks_a.md` (run
`trpo_joint1_cumul_rot_260629_183545`). *Caveat:* the wiki run there frames the term
as a probabilistic $\mathbb{1}[\lvert\theta_{\text{cum}}\rvert > 4\pi] \le 0.01$
constraint, whereas the shipped-code function `joint1_cumulative_cost` is an
*average* $\lvert q^{\text{des}}_1 - q^{\text{nom}}_1 \rvert$ cost — the same
experiment line spans two variants across runs; the substance (never binds) holds.

**Generalizes OOD even while not binding (experimental finding).** Despite never
binding under station-keeping, the same constraint line keeps cumulative rotational
drift bounded out-of-distribution (drift slope $2.2\times 10^{-4}$ rad/s, p95 final
$\lvert\text{drift}\rvert = 0.177$ rad $< 0.224$ rad budget) even while the unrelated
attitude tracker develops a genuine OOD heavy tail (roll steady-state error env-median
0.36° vs env-mean 3.87°, worst env 63°). Source: omx wiki
`joint1_cumulative_ipo_constraint_generalizes_drift_bounded_at_oo.md` (run
`trpo_cumul_constraint_260627_231709`). *Caveat:* this page calls it a "binding
average-constraint" while the companion page above documents the same line as never
binding — the discrepancy is in the source knowledge (likely "binding" used loosely
to mean "active/present"), flagged rather than reconciled here.

**Off by default = byte-identical.** With `arm="none"` (the default),
`apply_joint1_constraint_arm` returns immediately, the shipped 10-term set is
untouched, and K stays at 10. Enabling arm B adds exactly one cost-critic head; the
MLP layer counts, dims, and activations are unchanged.

---

## 8. Logging / metrics

Constraint metrics are emitted once per training iteration by
`ConstraintEncoderRunner._log_constraint_metrics` (invoked from the overridden
`log()`, gated on `self._should_log`; `constraint_encoder_runner.py:248-250`). The
algorithm keeps per-step running state (`_last_violations`, `_last_barrier_margins`,
`_last_barrier_penalty`) read only for this logging (`constraint_trpo.py:129-133`).

| Metric | Meaning |
|---|---|
| `Constraint/viol/<name>` | $\hat{J}_{C_k} - d_k$ against the **raw** discounted budget (`constraint_trpo.py:447`); negative = slack |
| `Constraint/margin/<name>` | $d_k^i - \hat{J}_{C_k}$ (adaptive-threshold margin, `:449`); **absolute**, not $d_k$-normalized |
| `Constraint/barrier_penalty` | aggregate scalar barrier penalty (no per-constraint suffix) |
| `Policy/line_search_success` | line-search accept rate this update |
| `Policy/entropy` | mean policy entropy |

The `<name>` suffix is the constraint's configured name
(`ALBCConstraintCfg.constraint_names`, `constraints.py:76-77`), falling back to the
numeric index. The namespace is a 2-level `Constraint/<type>/<name>` hierarchy for
viol/margin plus the flat `Constraint/barrier_penalty`; DORAEMON curriculum metrics
use a separate `DORAEMON/*` namespace and policy diagnostics a `Policy/*` namespace.

**Anomaly thresholds** flagged by the analysis engine
(`analyze_training.py` `ANOMALY_RULES`): `line_search_success < 0.5` FAIL
("TRPO line search failing. Cost gradient may dominate. Check barrier_t and constraint budgets."),
`barrier_penalty > 0.1` SPIKE;
plus general RL-health rules `entropy < 0` COLLAPSED, `noise_std < 0.25` LOW /
`>= 0.95` CEILING, `z_std < 0.1` LOW, `grad_norm < 1e-4` DEAD, `roll_deg > 20` HIGH,
`pitch_deg > 25` HIGH. **Correction to a stale wiki note:** the encoder-latent
saturation rule uses `Encoder/z_min < -0.98` / `Encoder/z_max > 0.98` in the actual
engine code (`analyze_training.py:41-42`), **not** the $\pm 0.95$ some notes state.
`thruster_util_max > 0.95` is cited in the wiki as a saturation anomaly but has no
matching `ANOMALY_RULES` entry in the engine code — treat it as an analysis heuristic,
not a code-encoded rule.

---

## 9. Which constraints actually bind (experimental findings)

Everything in this section is an **experimental result** from prior analysis runs,
kept deliberately separate from the code definitions above. Do not treat these as
code invariants; they are what specific runs showed.

**Only `thruster_util` binds.** Of the 10 shipped constraints, only `thruster_util`
reaches its discounted budget in practice — $\hat{J}_C/d_k \approx 0.869\text{-}0.870$
in the teacher run. The other 9 sit in slack, several deeply so:
`rp_vel_settling` 0.455, `arm_torque` 0.407, `rp_rate` 0.319, `yaw_rate` 0.138
(slack); `manipulability` 0.038, `arm_joint_vel` 0.031, `joint1_pos` 0.005,
`attitude` 0.003 (deep slack); `cumul_yaw` 0.000 ("fully inert"). Source: omx wiki
`constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md`. (Note: the
binding figure in the teacher run is ~0.87; there is no supported 0.94-in-the-teacher
value — the 0.944 figure below is the E6 budget-halving run, not the teacher.)

**Budget ×0.5 starves authority.** The E6 experiment halved all 10 budgets. Only
`thruster_util` responded, pushing *further* into binding ($\hat{J}_C/d_k$ rose
$0.869 \to 0.944$); the other 9 stayed slack. That single additional bind on the
control-authority channel caused authority starvation: per-step reward fell 54%
(Reward/total 7.96 -> 3.68), lin_vel reward went negative (the lin_vel reward
channel has since been removed), and policy entropy collapsed (crossing 0 at
iter 2289, an anomaly never seen in the teacher run).
**Rule:** tightening a control-authority channel (thruster) is destructive. Source:
omx wiki `constraint_budget_x0_5_binds_only_thruster_util_authority_starva.md`. This
binding conclusion is computed in the slack regime ($\hat{J}_C = d_k - \text{margin}$),
so it is `barrier_alpha`-independent and holds at either 0.02 or 0.05.

**The feasibility constraint was inert when `success = return >= 68`.** With the old
`performance_lb=68` sitting below the minimum episode return, `success` was pinned at
1, the DORAEMON feasibility constraint never fired, and the curriculum widened DR
without self-pacing feedback — the exact motivation for the `lb 68 -> 250` /
`kl_ub 0.06 -> 0.12` recalibration in Section 6.

---

## Source files

- `constrained_albc/envs/main/mdp/constraints.py` — 10 shipped cost functions + 1 experiment-only joint1 term, `ConstraintTermCfg`, `ALBCConstraintCfg`, `compute_all_costs`, `apply_joint1_constraint_arm` (2-way `{none, B}`)
- `constrained_albc/envs/main/config.py` — `ALBCEnvCfg`, `_FULL_DOF_CONSTRAINT_TERMS` (the shipped 10 budgets), DORAEMON overrides, joint1 toggles
- `constrained_albc/envs/main/config_noconstraint.py` — `ALBCNoConstraintEnvCfg` (terms=[], TRPO-NoIPO / PPO-Enc ablations)
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — ConstraintTRPO + IPO barrier, adaptive threshold, cost GAE, TRPO step, std clamp, cost critic
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `RslRlConstraintTRPOAlgorithmCfg` (runtime barrier_alpha/max_kl/std/entropy values)
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — `_log_constraint_metrics`, `num_constraints` auto-sync
- `.omx/profile/analyze_training.py` — `ANOMALY_RULES`, `_constraint_margin`
