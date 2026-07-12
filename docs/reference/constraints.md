# Constraints (`envs/main`)

> Verified against commit c5a8a08.

> **Scope**: The constraint system of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`), the attitude-only
> ALBC policy. Ten IPO constraints ship on this task — **5 probabilistic** (binary
> violation-probability budgets) + **5 average** (expected-magnitude budgets) —
> defined in `envs/main/config.py` and consumed by `ConstraintTRPO` in
> `envs/_core/algorithms/constraint_trpo.py`.
>
> This is a code-level reference verified against disk. The legacy full-DOF variant
> (`envs/full_dof/`, `Isaac-ConstrainedALBC-Full-*-v0`) reuses the same constraint
> list constant but is a different task and is **not** described here.

---

## 0. Key symbols

| Symbol | Meaning | Value |
|---|---|---|
| $K$ | number of constraint terms | 10 (§3) |
| $\pi$, $\pi_i$ | current policy / rollout policy at iterate $i$ (importance-sampling reference in §4.1, §4.4) | — |
| `ratio` | importance ratio $\pi(a\mid s)/\pi_i(a\mid s)$ in the surrogate objectives | — |
| $D_k$ | per-step cost budget for term $k$ | `config.py:57-72` |
| $d_k$ | discounted budget, $d_k = D_k/(1-\gamma_c)$ | `constraint_trpo.py:146-151` |
| $\gamma_c$ / $\lambda_c$ | cost discount / GAE lambda (`cost_gamma`/`cost_lam`) | `0.99` / `0.95` |
| $\hat{J}_{C_k}$ | mean discounted cost return — GAE($\lambda_c$) estimate, not raw MC sum | §4.3 |
| $d_k^{i}$ | IPO adaptive threshold, $\max(d_k,\ \hat J_{C_k}+\alpha d_k)$ | §4.2 |
| $\alpha$ (`barrier_alpha`) | IPO threshold slack — **not** DORAEMON's `alpha` feasibility floor (§6, same name, different mechanism) | 0.05 (§4.1) |
| $t$ (`barrier_t`) | IPO barrier sharpness | 100.0 (§4.1) |
| $\delta_{\max}$ (`max_kl`) | TRPO trust-region KL budget | 0.005 (§4.4) |
| $A(s,a)$ | reward (policy) advantage, standardized (`storage.advantages`) | used in the §4.4 surrogate reward term (`constraint_trpo.py:467,475`) |
| $\hat{A}^C_k$ | per-constraint ($K$-vector) cost advantage, standardized (`cost_advantages_flat`) | used in `cost_surr_k` (§4.1/§4.3, `constraint_trpo.py:476`) |
| $H$ / $\beta_{\text{ent}}$ | policy entropy / its coefficient (`entropy_coef` scalar, `entropy_coef_per_dim` wins when non-empty, §4.5) | entropy bonus in the §4.4 surrogate (`constraint_trpo.py:486-499`) |

Shared terms (ConstraintTRPO, IPO, TRPO, DORAEMON, ALBC, `p_t`/`o_t`/`z`): see [glossary.md](glossary.md).

---

## 1. Overview

Three layers, cleanly separated: **definitions** decide what each cost measures, **optimization**
decides how a cost budget is enforced, **wiring** decides which budgets/hyperparameters reach a run.

| Layer | File | Role |
|---|---|---|
| Definitions (cost functions) | `mdp/constraints.py` | 10 per-step cost functions, each returning a `(num_envs,)` non-negative tensor; `compute_all_costs()` stacks them into `(num_envs, K)` every step (`constraints.py:326-332`) |
| Optimization (ConstraintTRPO + IPO log-barrier) | `constraint_trpo.py` | folds an interior-point log-barrier on the $K$ cost budgets into the TRPO surrogate — no separate Lagrangian dual, no projection step; a single joint scalar drives the natural-gradient step |
| Wiring (budgets) | `config.py` | binds each cost function to $D_k$ and a name; the algorithm rescales to $d_k = D_k/(1-\gamma_c)$ (`constraint_trpo.py:146-151`) and compares it to the batch's mean discounted cost return |

```
cost function f_k(state)  ->  compute_all_costs -> costs (num_envs, K)   [mdp/constraints.py]
        |
        v  per-step cost, one column per constraint
cost GAE (cost_gamma, cost_lam)  ->  J_hat_C_k  (mean discounted cost return, K-vector)
        |
        v
IPO adaptive threshold:  d_k^i = max(d_k, J_hat_C_k + alpha * d_k)         [constraint_trpo.py:320-322]
        |
        v
barrier margin_k = d_k^i - cost_surr_k          # plain difference, NOT / d_k
barrier = -sum_k log(margin_k.clamp(min=1e-8)) / barrier_t                  [constraint_trpo.py:468-484]
        |
        v
surrogate L = -E[A * ratio]  +  barrier  -  entropy_bonus                   [constraint_trpo.py:475,500]
        |
        v
TRPO natural-gradient step under a pure-KL trust region (barrier curvature NOT in Fisher)
```

**`ConstraintTRPO` contains zero code that distinguishes probabilistic from average
constraints** — all $K$ columns flow through byte-identical GAE, standardization,
adaptive-threshold, and barrier code. The prob/avg split lives entirely in *how each cost signal
is computed* (`mdp/constraints.py`) and in *documentation convention* (`config.py`), never in
how the optimizer consumes it.

---

## 2. Constraint taxonomy — probabilistic vs average

The 10 shipped constraints split 5 + 5, expressed only by list order and inline comments in
`config.py` (`# --- Probabilistic (5) ---` above `[0:5]`, `# --- Average (5) ---` above
`[5:10]`; `config.py:56`, `config.py:65`). There is **no** `is_probabilistic`/`kind`/`type`
field on `ConstraintTermCfg` — its only fields are `func`, `params`, `budget`, `name`
(`constraints.py:50-57`).

| Category | Cost signal | Budget $D_k$ meaning | Feasibility target |
|---|---|---|---|
| Probabilistic (5) | binary indicator $\mathbb{1}[\text{violated}] \in \{0,1\}$ | maximum violation *probability* | $\mathbb{E}[\mathbb{1}] \le D_k$ |
| Average (5) | continuous non-negative cost | maximum *expected magnitude* | $\mathbb{E}[\text{cost}] \le D_k$ |

Both categories are the same constrained-MDP object $\mathbb{E}[\sum_t \gamma_c^t c_k(s_t,a_t)]
\le d_k$; they differ only in what the per-step cost $c_k$ is. A probabilistic $c_k$ is a
$\{0,1\}$ indicator, so its discounted sum reads as a violation probability; an average $c_k$ is
a continuous magnitude, so the budget reads as an allowed mean level.

**The "different treatment" is not in the optimizer.** The docstring at `constraints.py:14-24`
numbers `[0]-[4]` probabilistic and `[5]-[9]` average; that ordering plus the cost-function math
(indicator vs continuous) is the entire distinction — `compute_all_costs`
(`constraints.py:326-332`) does `torch.stack([t.func(...) for t in cfg.terms], dim=-1)`,
identical treatment of all 10 terms.

One consequence: the binary indicators' cost-advantage columns have near-zero variance, so
standardization floor-clamps std to `min=1.0` to keep them from blowing up (§4.3).

---

## 3. The 10 constraint terms

All values verbatim from `config.py:57-72`. Discounted budget $d_k = D_k / (1 - \gamma_c)$ with
$\gamma_c = 0.99$, so $d_k = 100 \cdot D_k$.

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

A comment directly above the list records prior surgery: `thruster_rate` was removed
("structurally incompatible with `entropy_coef>0`: noise alone violates 5x") and `thruster_sat`
was reverted to `thruster_util` (average, budget 0.40, "original form") — `config.py:53-54`.

### 3.1 Probabilistic terms (`[0:5]`)

Each returns a $\{0,1\}$ indicator; the discounted-sum budget is a violation probability.

- **`attitude`** — $\mathbb{1}[\lvert\text{roll}\rvert > \text{limit} \ \lor\
  \lvert\text{pitch}\rvert > \text{limit}]$, $\text{limit}=1.396$ rad.
- **`arm_torque`** — $\mathbb{1}[\max_j \lvert\tau_j\rvert > 9.5\,\text{Nm}]$.
- **`arm_joint_vel`** — $\mathbb{1}[\max_j \lvert\dot q_j\rvert > 2.8\,\text{rad/s}]$.
- **`joint1_pos`** — $\mathbb{1}[\lvert\theta_1\rvert > 4\pi]$, i.e. joint-1 absolute angle past
  the $\pm 4\pi$ rail.
- **`cumul_yaw`** — $\mathbb{1}[\lvert\theta_{\text{yaw,cum}}\rvert > 8\pi]$, accumulated
  (unwrapped) yaw.

### 3.2 Average terms (`[5:10]`)

Each returns a continuous non-negative cost; the discounted-sum budget is an expected magnitude.

- **`thruster_util`** — `thruster_utilization_cost` takes **no configurable threshold** (it
  relies on `ConstraintTermCfg.params` default `{}`, `constraints.py:55`). Per its docstring
  (`constraints.py:20`) it returns the per-env maximum absolute normalized thruster state,
  $\max_i \lvert s_i \rvert$. This is the single control-authority channel among the 10.
- **`rp_rate`** — soft-thresholded roll/pitch angular-rate cost, hinged at $0.5$: cost accrues
  only above the soft threshold.
- **`yaw_rate`** — soft-thresholded yaw-rate cost, hinged at $0.55$.
- **`rp_vel_settling`** — the mean roll/pitch angular rate $(\lvert p \rvert + \lvert q
  \rvert)/2$, masked to be nonzero only when the attitude error is within
  `settling_threshold=0.087` rad ($5\,\text{deg}$) of target: cost is zero during transit (att
  error $>$ threshold) and active during settling (att error $\le$ threshold). The name matches
  the implementation (`constraints.py:206-228`). Note the caveat that `settling_threshold` gates
  on the *attitude error*, not on the angular velocity itself.
- **`manipulability`** — hinged below a manipulability floor `w_threshold=0.3`; cost accrues
  when the arm's manipulability measure drops below the floor.

**`max`-inside-average is theoretically consistent, not a category error.**
`thruster_util`/`rp_rate` reduce with a spatial `max` ($\max_i\lvert s_i\rvert$, $\max(\lvert
p\rvert,\lvert q\rvert)$) *inside* the per-step cost (`rp_vel_settling` uses `mean`;
`yaw_rate`/`manipulability` are single-quantity, no reduction needed).

The "average" of an average constraint is the *temporal* expectation $\mathbb{E}[\sum_t
\gamma_c^t c_k]$ — `max` only shapes the per-step signal $c_k$, so the bound is a
**time-averaged peak** ($\mathbb{E}[\max_i]$, not $\max_i\mathbb{E}$, not a hard "never exceed at
any step" bound) that tolerates brief spikes because the discounted average smooths them.

### 3.3 Experiment-only joint1 term (not shipped)

One extra average cost function exists for the joint1-anti-drift experiment line (§7); it is not
in the shipped 10 (`constraints.py:26-29`):

- **`joint1_cumulative_cost`** — $\lvert q^{\text{des}}_1 - q^{\text{nom}}_1 \rvert$, the
  unwrapped running command displacement (`constraints.py:271`, using `env._joint_pos_targets[:,
  0] - env._nominal_joint_pos[0]`). It is now the sole joint1 anti-drift mechanism: the
  wrapped-instantaneous constraint (formerly "arm A", `joint1_centering_cost`) and the
  reward-side centering penalty were both removed 2026-07.

### 3.4 Threshold provenance and the actuator hard-cap layering

Constraint thresholds are **not one uniform kind of hyperparameter** — they split into two
groups with opposite tuning rules.

**Hard safety rails (physically grounded)** — tune only toward the **true physical value**
(measurement/sysid-driven), never toward reward:

| Constraint | Soft threshold | PhysX hard cap | Basis |
|---|---|---|---|
| `attitude` | 1.396 rad (80°) | — | tilt safety |
| `arm_torque` | `limit_nm=9.5` Nm | `effort_limit_sim=13.0` Nm | arm motor **stall torque** |
| `arm_joint_vel` | `2.8` rad/s | `velocity_limit_sim=3.1` rad/s | measured XW540-T260 no-load plateau, 2026-07-06 |
| `joint1_pos` | $4\pi$ (12.566 rad) | — | cable-wrap rail |
| `cumul_yaw` | $8\pi$ (25.133 rad) | — | tether-wrap rail |

Both arm rails sit **inside** the PhysX hard caps (`9.5<13.0`, `2.8<3.1`;
`marinelab/.../albc/albc.py:200-201`): the soft IPO constraint bites before the hard clamp
(intended layering), leaving a live band above threshold where the indicator can still fire (§9:
`arm_torque` $\hat J_C/d_k=0.407$ fires; `arm_joint_vel` $0.031$ deep slack).

**Invariant: soft threshold must stay inside the hard cap** — inverting it silently kills the
constraint. The `velocity_limit_sim` $6.28\to3.1$ retrain (match real XW540 arm) paired with
lowering `limit_rad_per_s` $4.189\to2.8$ (2026-07-12) preserves `2.8<3.1` and avoids that trap.
Fix: omx wiki `arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt.md`.

**Soft shaping thresholds (judgment-chosen)** — behavior/comfort envelopes, not safety limits;
**are** legitimate experimental tuning targets:

| Constraint | Threshold | Budget $D_k$ |
|---|---|---|
| `rp_rate` | 0.5 | 0.10 |
| `yaw_rate` | 0.55 | 0.10 |
| `rp_vel_settling` | 0.087 | 0.20 |
| `manipulability` | 0.3 | 0.05 |

The threshold sets *where* cost starts and $D_k$ sets *how much* is tolerated — co-tune
(threshold, budget) per constraint rather than budget alone. Tuning the budget of a constraint
whose threshold sits far from the operating point is a no-op (§9: 9/10 constraints slack, so
most tuning changes nothing until it actually pushes the constraint toward binding) — argues for
**one-constraint-at-a-time** co-tuning against a baseline on this 1-GPU sequential rig, not a
joint grid sweep over a mostly-flat surface (one cliff at `thruster_util`).

**`cumul_yaw` headroom (recorded, low priority).** $8\pi$ (4 rev) $\approx3.3\times$ the
observed operating peak ($\sim1.22$ rev, §9 fully inert). A trim to $6\pi$ (3 rev) stays inert
(safe no-op); a *bind-intended* value would need $\lesssim2.5\pi$ and should weigh whether it
fights normal yaw maneuvering.

---

## 4. ConstraintTRPO optimization

Algorithm body: `envs/_core/algorithms/constraint_trpo.py`. `ConstraintTRPO` is a standalone algorithm
(aliased `ALBCConstraintTRPO`, `rsl_rl_ppo_cfg.py:25`), not an `rsl_rl.PPO` subclass.

**Provenance — NORBC's "Modified IPO", implemented faithfully (not a bespoke hybrid).** Kim et
al., "Not Only Rewards But Also Constraints: Applications on Legged Robot Locomotion",
arXiv:2308.12517v4, 2024 (KAIST Hwangbo lab), named in the module docstring (`constraint_trpo.py:16-18`).

| This codebase | NORBC |
|---|---|
| $d_k = D_k/(1-\gamma_c)$ | Eq. (8) |
| trust-region barrier objective (raw $\hat J_{C_k}$ level + standardized cost surrogate, §4.1/§4.3) | Eq. (10) |
| adaptive threshold $d_k^{i} = \max(d_k,\ \hat J_{C_k}+\alpha d_k)$ | Eq. (11) |
| multi-head cost critic | shared-backbone cost value |

The one divergence: NORBC's PPO step is swapped for a TRPO step — NORBC's own stated choice
(stable improvement + feasibility *checking*, not enforcement). So the two theoretical "soft
spots" documented below (barrier saturation cap §4.1; raw-vs-standardized margin §4.3) are
**NORBC's deliberate design, not implementation defects**. Detail + the independent-review
resolution: omx wiki `constrainttrpo_faithful_norbc_modified_ipo_kim_2024_arxiv_2308_1.md`.

### 4.1 IPO log-barrier

The interior-point objective (module docstring form):

$$
\begin{aligned}
\max_{\pi}\quad & \mathbb{E}\!\left[A(s,a)\right] + \frac{1}{t}\sum_{k} \log\!\left(d_k^{i} - \hat{J}_{C_k}\right) \\
\text{s.t.}\quad & \mathrm{KL}\!\left(\pi \,\|\, \pi_i\right) \le \delta_{\max} \\
\text{where}\quad & d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right)
\end{aligned}
$$

In code the barrier is built per update (`constraint_trpo.py:468-484`):

$$
\begin{aligned}
\text{margin}_k &= \underbrace{(d_k^{i} - \hat{J}_{C_k})}_{\text{barrier\_base}} - \text{cost\_surr}_k \\
\text{cost\_surr}_k &= \frac{1}{1-\gamma_c}\,\mathbb{E}\!\left[\text{ratio}\cdot \hat{A}^{C}_k\right] \\
\text{barrier} &= -\frac{1}{t}\sum_k \log\!\big(\text{margin}_k.\text{clamp}(\min=10^{-8})\big)
\end{aligned}
$$

Two implementation facts matter:

1. **`margin` is a plain difference, never normalized by $d_k$** — no $\hat{J}_C/d_k$ division
   anywhere in the file.
2. **The two margin terms share a scale but not an explicit scaling factor in code.**
   `barrier_base = adaptive_d_k - mean_cost_returns` carries no explicit $1/(1-\gamma_c)$;
   `cost_surr` is scaled by `inv_one_minus_gamma` (`constraint_trpo.py:476`). Both already live
   on the discounted-return scale via the budget rescale $d_k=D_k/(1-\gamma_c)$.

**`clamp(min=1e-8)` caps the barrier so it never literally reaches $\pm\infty$** — saturates at
$-\log(10^{-8})/t \approx 18.42/100 \approx 0.184$ per constraint, so a step whose
reward-surrogate gain exceeds ~0.184 walks straight through the boundary.

Not present in NORBC's Eq. (9)/(10); softens the interior-point "cannot cross" property near the
boundary, but consistent with NORBC's soft, near-satisfaction design and self-correcting since
the adaptive threshold re-anchors on the raw cost return every iteration. (An earlier verbal
claim that the barrier "diverges to $+\infty$ and auto-rejects the step" was wrong — the clamp
caps it.)

**Runtime constants — constructor default vs agent cfg.** The cfg is what every trained run
actually uses, via `RslRlConstraintTRPOAlgorithmCfg` dispatch to the constructor kwarg:

| Field | Constructor default | Agent cfg (effective) | Drift |
|---|---|---|---|
| `barrier_t` | 100.0 (`:64`) | 100.0 (`rsl_rl_ppo_cfg.py:227`) | none |
| `barrier_alpha` | 0.02 (`:65`) | **0.05** (`rsl_rl_ppo_cfg.py:228`) | 0.02 is dead once the cfg supplies the field |

Some earlier notes reported 0.02 (or a since-superseded wiki page) — code truth is **0.05**. When
in doubt, read the resolved per-run `params/agent.yaml`, not the class signature.

### 4.2 Adaptive threshold and the violations diagnostic

The adaptive threshold is recomputed every update from the current batch's mean cost returns
(`constraint_trpo.py:320-322`, called at `:460`):

$$
d_k^{i} = \max\!\left(d_k,\; \hat{J}_{C_k} + \alpha\, d_k\right), \qquad
\hat{J}_{C_k} = \big(\text{mean cost return}\big)_k.\text{clamp}(\min=0)
$$

The reported `violations` monitoring metric compares $\hat{J}_{C_k}$ against the **raw** budget
$d_k$, *not* the adaptive threshold: `violations = (mean_cost_returns - self.d_k)`
(`constraint_trpo.py:461`). `adaptive_d_k` is used only inside the barrier margin (`:468`) and
the logged barrier margin (`:463`).

### 4.3 Feasibility, GAE, and standardization

- **Cost GAE.** Per-constraint advantages use the same recursive $\delta/\lambda$-return formula
  as reward GAE but with `cost_gamma=0.99`, `cost_lam=0.95`, a vectorized $K$-dim accumulator
  run reverse in time, followed by a non-finite sanitize that zeros any constraint column
  containing NaN/Inf across the rollout (`constraint_trpo.py:295-314`). `cost_gamma` must be
  strictly $< 1$ or the constructor raises `ValueError` (`:144-145`).
- **Feasibility level is an estimator, not the true return.** Every feasibility judgment
  (`mean_cost_returns` → `barrier_base`, `violations`, adaptive threshold;
  `constraint_trpo.py:460,461,468`) reads the **GAE($\lambda_c$) return** `cost_returns =
  cost_advantage + cost_value` (`:305`), *not* a raw Monte-Carlo sum — it inherits the
  `cost_lam=0.95` bias and the cost critic's estimation error.
- **Consequence.** An *under-estimating* cost critic makes the barrier read **feasible** when the
  true cost already exceeds budget — a risk inherent to critic-based constrained RL generally,
  not a code defect.
- **Time-out bootstrapping.** On time-out (not termination) the per-constraint cost is
  bootstrapped with `cost_gamma` and the per-constraint value vector, mirroring the reward-side
  bootstrap on the cost channel (`constraint_trpo.py:276-282`).
- **Per-constraint cost-advantage standardization (NORBC Sec IV-B).** Each of the $K$
  cost-advantage columns is independently mean/std-normalized across the flattened batch dim,
  std floor-clamped to **`min=1.0`** — not the usual `1e-8` epsilon — because binary constraints
  can have near-zero std, causing $10^8$ amplification (inline comment,
  `constraint_trpo.py:449-452`). Reward advantages use the ordinary `1e-8` guard in stock rsl_rl's
  `rollout_storage.py` (`compute_returns`, `normalize_advantage=True`); the in-algorithm
  re-standardization was removed 2026-07-12 as redundant.

<details>
<summary>Why the barrier margin mixes a raw level with a standardized delta — NORBC Eq. (10) verbatim, not a code bug</summary>

`barrier_base` uses the unstandardized `mean_cost_returns`, while `cost_surr` uses the
standardized advantage (`:468` vs `:476`). NORBC relies on the *zero-mean* half to keep the
problem always feasible at `ratio=1`: then $\mathbb{E}[\hat{A}^C_k]\approx 0$, so
$\text{margin}_k \approx d_k^i - \hat{J}_{C_k} \ge \alpha d_k > 0$ and the $\log$ is always
defined at the start of each update. The *std* half is NORBC's gradient-conditioning trick for
stacking 10+ constraints stably.

Practical consequence: a constraint whose runtime cost-advantage std exceeds 1 gets a slightly
**more permissive** effective boundary (the barrier responds in standardized units while the
budget is raw) — this is therefore **dormant unless some constraint's cost-adv std actually
exceeds 1**, an empirical run-data question, not a bug to patch. Whether standardization
strictly voids NORBC's near-satisfaction guarantee is a critique of NORBC itself, out of scope
for this codebase.

</details>

### 4.4 TRPO trust-region step

The natural-gradient step operates on the **single combined surrogate scalar**
(`constraint_trpo.py:475,500`):

$$
L = -\,\mathbb{E}\!\left[A\cdot \text{ratio}\right] \;+\; \text{barrier} \;-\; \beta_{\text{ent}}\, H
$$

- **Gradient group.** $g = \nabla_\theta L$ over $\theta = (\text{actor}, \text{encoder},
  \log\sigma)$.
- **Fisher-vector product uses pure KL curvature only** — a double backprop through the Gaussian
  KL between old and new policy, plus Tikhonov damping $Fv + \lambda_{\text{cg}} v$
  (`constraint_trpo.py:368-379`). The barrier's curvature **never** enters the Fisher — the KL
  trust region does not "know" about the constraint geometry.
- **Conjugate gradient.** Solves $F x = g$ with `cg_iters=10` and an early-exit residual
  tolerance `1e-10` (`:381-400`).
- **Step size.** $\Delta\theta = -\sqrt{\delta_{\max} / (\tfrac{1}{2}\tilde g^\top g)}\,\tilde
  g$; the update aborts (returns `False`, no step) if $\tfrac{1}{2}\tilde g^\top g \le 0$ or
  non-finite, or if the step direction contains NaN/Inf (`:559-567`).
- **Line search.** Backtracking, shrink factor `0.5`, max 10 backtracks; accepts a step iff the
  surrogate strictly decreases **and** realized $\mathrm{KL} \le \delta_{\max}\cdot
  \text{line\_search\_kl\_margin}$ with margin `1.5` (`:413-421`) — **looser** than the
  $\delta_{\max}$ used to size the initial step, so an accepted step can exceed the nominal
  trust-region radius by up to 50%. On exhaustion, params revert to `old_params`.

**True trust-region values** (same constructor-vs-cfg drift pattern as §4.1): `max_kl` = 0.002
ctor (`:43`) vs **0.005** cfg (`rsl_rl_ppo_cfg.py:201`) — drift, 2.5x looser, agent cfg wins.
`cg_damping=0.1` and `line_search_kl_margin=1.5` agree between constructor and cfg (no drift).

### 4.5 std clamping

After every `_trpo_step` (unconditional on line-search success), `log_std` is clamped
(`constraint_trpo.py:504-511`). At runtime the **per-dim floor branch is the one exercised**,
because `min_std_per_dim` is non-empty. The entropy bonus follows the same pattern: a scalar
field and a per-dim field both exist, and the per-dim field wins whenever non-empty (default) —
the scalar is dead at runtime.

| Field (scalar) | Scalar value | Per-dim field | Per-dim value (effective) |
|---|---|---|---|
| `min_std` | 0.05 agent-cfg (**dead**); constructor default 0.01 | `min_std_per_dim` | `(0.10, 0.10, 0.05×6)` — arm dims (0,1) floor 0.10, thruster dims (2-7) floor 0.05 (`rsl_rl_ppo_cfg.py:246`); `max_std=2.0` |
| `entropy_coef` | 0.003 (**dead**, `rsl_rl_ppo_cfg.py:233`) | `entropy_coef_per_dim` | `(0.01, 0.01, 0.001×6)` (`rsl_rl_ppo_cfg.py:239`) |

Constructor scalar defaults (`min_std=0.01`, `min_std_per_dim=()`) would take the scalar branch,
but the agent cfg overrides both — per-dim always wins.

### 4.6 Cost critic

**Parameter-group split — two disjoint groups, two different update rules.**

| Group | Members | Update rule |
|---|---|---|
| Policy | actor + encoder + `log_std` | TRPO natural gradient — no Adam, no optimizer object |
| Value | `value_prefixes` match: `critic.` / `cost_critic.` / `value_backbone.` / `reward_head.` / `cost_head.` | Adam at `value_lr` (`constraint_trpo.py:160-186`) |

`log_std` is deliberately kept in the policy group so the KL trust region bounds noise changes;
the encoder stays in the policy group because decoupling it dropped encoder gradients ~85% (code
comment, `:154-158`).

**Single multi-head cost critic.** One network producing a $K$-dimensional vector per
observation (`evaluate_costs()`), not $K$ separate networks. Reward and cost critics update
jointly in one backward pass: $\text{total} = \text{value\_loss\_coef}\cdot L_V +
\text{cost\_value\_loss\_coef}\cdot L_{V_C}$, both coefficients `1.0`
(`constraint_trpo.py:611-621`).

Per-constraint MSE is `.mean(dim=0)` over the batch → $K$-vector → `.mean()` across constraints
→ scalar (`:616-617`). Critic-head activation detail lives in the policy class
`ALBCActorCriticEncoder`, not here — see the network-architecture reference.

**Separate networks, one shared gradient clip (the reward/cost coupling).** `self.critic`
(scalar) and `self.cost_critic` ($K$-dim) are **independent** MLPs, disjoint parameters, no
shared backbone (`envs/_core/encoder/_policy_base.py:86,91` — the `value_backbone.` prefix is a
classification catch, not an actual shared trunk). Disjoint parameters mean `total.backward()`
does not cross-couple their gradients ($\partial L_{V_C}/\partial\theta_{\text{reward
critic}}=0$).

**One thing does couple them:** the value update applies a single
`clip_grad_norm_(self._value_params, max_grad_norm=1.0)` over the **union** of both critics'
parameters (`:621-625`). The cost critic has $K=10$ heads regressing rare-event returns and can
dominate the combined norm — when the union exceeds `1.0`, the clip scales *both* critics down
together, letting a noisy cost critic throttle the reward critic's step.

Flagged as a real coupling, not proven harmful (needs a runtime value-group grad-norm check to
confirm it bites).

---

## 5. Constraint-margin normalization ($\hat{J}_C / d_k$)

**The optimizer stores an absolute margin; any binding/slack judgment must normalize by $d_k$
first.** This is an analysis rule, not a code behavior: the barrier uses the absolute margin
correctly (§4.1), but a human or engine reading `Constraint/margin/<name>` off TensorBoard must
divide by $d_k$ first to compare across constraints.

The discounted budgets $d_k = 100 \cdot D_k$ span a **40×** range across the 10 constraints
(`attitude` $d_k=1.0$ from $D_k=0.01$, vs `thruster_util` $d_k=40.0$ from $D_k=0.40$), so a
constraint deep in slack with a large budget shows a large absolute margin while a constraint
near its budget with a small budget shows a small one — reading the raw margin inverts the
conclusion.

The correct normalized quantity is

$$
\frac{\hat{J}_{C_k}}{d_k} = 1 - \frac{\text{margin}_k}{d_k},
$$

valid **only in the slack regime**, where the adaptive floor has not engaged, i.e. where
`Constraint/viol/<name> == -Constraint/margin/<name>` exactly (`constraint_trpo.py:461` vs
`:463`). When $\hat{J}_{C_k} + \alpha d_k > d_k$ the adaptive threshold engages and $d_k^i \ne
d_k$, breaking that identity.

**Experimental finding — a real teacher-run report misread the binding channel**
(`report.md:174,180`):

| Constraint | Read as (from raw margin) | Actual $\hat J_C/d_k$ | Regime |
|---|---|---|---|
| `attitude` | looked binding (small absolute margin) | 0.003 | deepest slack |
| `cumul_yaw` | looked binding (small absolute margin) | 0.000 | deepest slack |
| `thruster_util` | looked slack (large absolute margin — large budget) | ≈0.87 | genuinely binding |

**The engine now normalizes** (since commit `4ff9ea1`, 2026-06-07):
`.omx/profile/analyze_training.py` computes `_constraint_binding_ratio` (`:416-430`, $1 -
\text{margin}/d_k$) and prints a `JC/dk=` column that flags the binding channel by max ratio
(`:809`, `:820`), pinned by `test_constraint_margin_norm.py`.

The low-level `_constraint_margin()` helper (`:370-379`) still returns the raw absolute margin;
its consumer (`:803`) normalizes it. Like the manual formula, the engine ratio is exact only in
the slack regime and saturates at $1-\alpha = 0.95$ for a genuinely-binding channel (it consumes
the frozen margin). Source: omx wiki
`constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md`.

---

## 6. DORAEMON and constraints

DORAEMON is the domain-randomization curriculum (mechanics live in marinelab; only its
interaction with the constraint/feasibility machinery is documented here). The main env
overrides four fields (`config.py:527`): `DoraemonCfg(enable=True, kl_ub=0.12,
performance_lb=250.0, step_interval=250)`. `step_interval=250` sets how often the curriculum
updates.

**`success` definition.** `success = accumulated_episode_return >= performance_lb`, computed in
`albc_env.py` (`_episode_return_accum += reward`; `config.py:515` comment).

**`alpha` is a feasibility floor, not a DR lever — and is unrelated to `barrier_alpha` (§0,
§4.1) despite the shared name.** It gates whether a curriculum-difficulty step is *accepted*; it
does not widen randomization. DORAEMON's `alpha` is cited as `0.5` in the config reasoning
comment (`config.py:521`); the literal field default comes from marinelab's `DoraemonCfg`
(unverified in the read files).

**Experimental finding.** Raising `alpha` `0.50 -> 0.75` (E5, run `trpo_260606_225859`) was a
near-null intervention: `success_rate` stayed saturated at `0.96-0.99` the whole run, so the
floor never gated a step. The actually-binding constraint on DR-expansion speed is the
per-update trust-region KL (`kl_ub`, pinned at 0.06 in that run). To widen robustness, move
`kl_ub` or DR variance directly, **not** the success floor. Source: omx wiki
`doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md`.

**`performance_lb` and `kl_ub` were raised together by design** (`config.py:514-526`):
`performance_lb` `68.0 -> 250.0`, `kl_ub` `0.06 -> 0.12`. Calibrated from a recon run
(`trpo_baseline_260608_160453`, 1146 iter) DORAEMON episode-return distribution: min=81.9,
p5=227, p25=250 (chosen `lb`), median=264, p95=291.

With `lb=68` sitting *below* the minimum return, `success = return >= 68` was always `1` — the
feasibility constraint ($\hat G \ge \alpha$) was **inert**, and the curriculum widened DR
unconstrained (no self-pacing feedback). `lb=250` (p25) puts starting `success_rate` at ~0.65 —
above `alpha=0.5` so the distribution still expands, but the signal is live again instead of
pinned at 1; chosen below the median so a reward plateau cannot drag `success_rate` to 0.

`kl_ub` was doubled to widen the distribution fast enough to compensate for the slower expansion
the raised `lb` induces — the two levers move together by design: `lb` alone makes DR easier,
`kl_ub` alone leaves `success_rate` pinned at 1.

---

## 7. joint1 anti-drift experiment

An off-by-default toggle can append an **11th** constraint term to test joint-1 anti-drift.

| Field (on `ALBCEnvCfg`) | Default | Meaning |
|---|---|---|
| `joint1_constraint_arm` | `"none"` | one of `{"none", "B"}` (`config.py:580`) |
| `joint1_constraint_budget` | `0.05` | per-step average budget $d_k$ for the joint1 term (`config.py:581`) |

**Materialization path.** `apply_joint1_constraint_arm()` (`constraints.py:279-299`) reads the
arm: `"none"` is a no-op; `"B"` appends a `joint1_cumulative_cost` term (name
`joint1_cumulative`); anything else raises `ValueError` (including the former `"A"`, which no
longer exists). It appends via `env_cfg.constraints.terms = [*env_cfg.constraints.terms, term]`.

**Why it is called from `ALBCEnv.__init__`, not a cfg `__post_init__`.** The call site is
`albc_env.py:128`, inside `ALBCEnv.__init__` (after payload-viz and DR-sampler init). This is
deliberate: hydra's `update_class_from_dict` override lands *after* the cfg `__post_init__` but
*before* `ALBCEnv.__init__` runs (`constraints.py:279-291`, `albc_env.py:123-127`). Putting the
call in `__post_init__` would always observe `arm="none"` and silently produce a
baseline-duplicate run instead of arm B.

**Sole anti-drift mechanism.** Arm B (`joint1_cumulative_cost`) is now the only joint1
anti-drift mechanism in the codebase. Both the reward-side centering penalty and the
wrapped-instantaneous constraint (formerly "arm A") were removed 2026-07, so the earlier "set
the reward's centering coefficient to 0.0 to avoid double-counting" requirement no longer
applies — there is nothing left to double-count against.

**Off by default = byte-identical.** With `arm="none"` (the default),
`apply_joint1_constraint_arm` returns immediately, the shipped 10-term set is untouched, and $K$
stays at 10. Enabling arm B adds exactly one cost-critic head; the MLP layer counts, dims, and
activations are unchanged.

### Experimental findings (arm B)

| Finding | Evidence | Source (omx wiki) |
|---|---|---|
| **Never binds under station-keeping.** In a flat-target station-keeping task the joint1-cumulative constraint essentially never binds: the policy naturally parks around **0.36 revolutions**, deeply inside the $\pm4\pi$ (2-rev) rail; violation metric ≈ **-0.9997** (near-full headroom) every iteration; peak $\lvert\theta_{\text{cum}}\rvert$ never exceeds ~1.22 rev across any of 4 DR difficulty levels (0/64 envs $>4\pi$). | run `trpo_joint1_cumul_rot_260629_183545` | `joint1_cumulative_rotation_constraint_never_binds_policy_parks_a.md` |
| **Generalizes OOD even while not binding.** Despite never binding under station-keeping, the same constraint line keeps cumulative rotational drift bounded out-of-distribution (drift slope $2.2\times10^{-4}$ rad/s, p95 final $\lvert\text{drift}\rvert=0.177$ rad $<0.224$ rad budget), even while the unrelated attitude tracker develops a genuine OOD heavy tail (roll steady-state error env-median 0.36° vs env-mean 3.87°, worst env 63°). | run `trpo_cumul_constraint_260627_231709` | `joint1_cumulative_ipo_constraint_generalizes_drift_bounded_at_oo.md` |

**Caveats (flagged, not reconciled):**

- The "never binds" wiki page frames the term as a probabilistic
  $\mathbb{1}[\lvert\theta_{\text{cum}}\rvert>4\pi]\le0.01$ constraint, whereas the shipped-code
  function `joint1_cumulative_cost` is an *average* $\lvert
  q^{\text{des}}_1-q^{\text{nom}}_1\rvert$ cost — the same experiment line spans two variants
  across runs; the substance (never binds) holds regardless.
- The "generalizes OOD" page calls it a "binding average-constraint" while the companion page
  above documents the same line as never binding — the discrepancy is in the source knowledge
  (likely "binding" used loosely to mean "active/present"), flagged rather than reconciled here.

---

## 8. Logging / metrics

Constraint metrics are emitted once per training iteration by
`ConstraintEncoderRunner._log_constraint_metrics` (invoked from the overridden `log()`, gated on
`self._should_log`; `envs/_core/runners/constraint_encoder_runner.py:259-261`). The algorithm keeps per-step
running state (`_last_violations`, `_last_barrier_margins`, `_last_barrier_penalty`) read only
for this logging (`constraint_trpo.py:129-133`).

| Metric | Meaning |
|---|---|
| `Constraint/viol/<name>` | $\hat{J}_{C_k} - d_k$ against the **raw** discounted budget (`constraint_trpo.py:461`); negative = slack |
| `Constraint/margin/<name>` | $d_k^i - \hat{J}_{C_k}$ (adaptive-threshold margin, `:463`); **absolute**, not $d_k$-normalized |
| `Constraint/barrier_penalty` | aggregate scalar barrier penalty (no per-constraint suffix) |
| `Policy/line_search_success` | line-search accept rate this update |
| `Policy/entropy` | mean policy entropy |

The `<name>` suffix is the constraint's configured name (`ALBCConstraintCfg.constraint_names`,
`constraints.py:76-77`), falling back to the numeric index. Namespace: a 2-level
`Constraint/<type>/<name>` hierarchy for viol/margin plus the flat `Constraint/barrier_penalty`;
DORAEMON curriculum metrics use a separate `DORAEMON/*` namespace and policy diagnostics a
`Policy/*` namespace.

**Anomaly thresholds** flagged by the analysis engine (`analyze_training.py` `ANOMALY_RULES`):

| Rule | Condition | Severity | Note |
|---|---|---|---|
| Line search | `line_search_success < 0.5` | FAIL | "TRPO line search failing. Cost gradient may dominate. Check barrier_t and constraint budgets." |
| Barrier | `barrier_penalty > 0.1` | SPIKE | |
| Entropy | `entropy < 0` | COLLAPSED | |
| Noise std | `noise_std < 0.25` | LOW | |
| Noise std | `noise_std >= 0.95` | CEILING | |
| Encoder z spread | `z_std < 0.1` | LOW | |
| Gradient | `grad_norm < 1e-4` | DEAD | |
| Roll | `roll_deg > 20` | HIGH | |
| Pitch | `pitch_deg > 25` | HIGH | |
| Encoder z saturation | `Encoder/z_min < -0.98` / `Encoder/z_max > 0.98` (`analyze_training.py:41-42`) | — | **Correction to a stale wiki note**: engine code uses $\pm0.98$, not the $\pm0.95$ some notes state |
| Thruster util | `thruster_util_max > 0.95` | — | cited in the wiki as a saturation anomaly but has **no matching `ANOMALY_RULES` entry** in engine code — treat as an analysis heuristic, not a code-encoded rule |

---

## 9. Which constraints actually bind (experimental findings)

Everything here is an **experimental result** from prior analysis runs, kept separate from the
code definitions above — not code invariants, just what specific runs showed.

**Only `thruster_util` binds (teacher run):**

| Constraint | $\hat J_C/d_k$ | Regime |
|---|---:|---|
| `thruster_util` | 0.869–0.870 | **binding** |
| `rp_vel_settling` | 0.455 | slack |
| `arm_torque` | 0.407 | slack |
| `rp_rate` | 0.319 | slack |
| `yaw_rate` | 0.138 | slack |
| `manipulability` | 0.038 | deep slack |
| `arm_joint_vel` | 0.031 | deep slack |
| `joint1_pos` | 0.005 | deep slack |
| `attitude` | 0.003 | deep slack |
| `cumul_yaw` | 0.000 | fully inert |

Source: omx wiki `constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md`.
(Teacher-run binding figure is ~0.87 — no supported 0.94-in-the-teacher value; the 0.944 below
is the E6 budget-halving run, not the teacher.)

**Budget ×0.5 starves authority (E6).** Halving all 10 budgets: only `thruster_util` responded,
pushing further into binding; the other 9 stayed slack. That single additional bind starved
control authority:

| Metric | Teacher run | E6 (budgets ×0.5) |
|---|---|---|
| `thruster_util` $\hat J_C/d_k$ | 0.869 | 0.944 |
| Reward/total (per-step) | 7.96 | 3.68 (-54%) |
| lin_vel reward | positive | negative (channel since removed) |
| policy entropy | stable | collapsed (crosses 0 at iter 2289 — anomaly, not seen in teacher run) |

**Rule:** tightening a control-authority channel (thruster) is destructive. Computed in the
slack regime ($\hat{J}_C = d_k - \text{margin}$), so it is `barrier_alpha`-independent (holds at
0.02 or 0.05). Source: omx wiki
`constraint_budget_x0_5_binds_only_thruster_util_authority_starva.md`.

**The feasibility constraint was inert when `success = return >= 68`.** With the old
`performance_lb=68` below the minimum episode return, `success` was pinned at 1, the DORAEMON
feasibility constraint never fired, and the curriculum widened DR without self-pacing feedback —
the exact motivation for the `lb 68 -> 250` / `kl_ub 0.06 -> 0.12` recalibration in §6.

---

## Source files

- `constrained_albc/envs/main/mdp/constraints.py` — 10 shipped cost functions + 1
  experiment-only joint1 term, `ConstraintTermCfg`, `ALBCConstraintCfg`, `compute_all_costs`,
  `apply_joint1_constraint_arm` (2-way `{none, B}`)
- `constrained_albc/envs/main/config.py` — `ALBCEnvCfg`, `_FULL_DOF_CONSTRAINT_TERMS` (the
  shipped 10 budgets), DORAEMON overrides, joint1 toggles
- `constrained_albc/envs/main/config_noconstraint.py` — `ALBCNoConstraintEnvCfg` (terms=[],
  TRPO-NoIPO / PPO-Enc ablations)
- `constrained_albc/envs/_core/algorithms/constraint_trpo.py` — ConstraintTRPO + IPO barrier,
  adaptive threshold, cost GAE, TRPO step, std clamp, cost critic
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `RslRlConstraintTRPOAlgorithmCfg`
  (runtime barrier_alpha/max_kl/std/entropy values)
- `constrained_albc/envs/_core/runners/constraint_encoder_runner.py` — `_log_constraint_metrics`,
  `num_constraints` auto-sync
- `.omx/profile/analyze_training.py` — `ANOMALY_RULES`, `_constraint_margin`
