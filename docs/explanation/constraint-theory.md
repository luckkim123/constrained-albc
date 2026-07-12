# Theoretical Analysis (NORBC Constrained RL)

Results of analyzing the theoretical consistency of the ALBC codebase against the Constrained RL theory of the NORBC paper. Analysis date: 2026-03-05.

> File paths in this doc predate the repo split — current code lives in
> `constrained_albc/envs/{main,full_dof}/` (`algorithms/constraint_trpo.py`,
> `mdp/constraints.py`; both env packages carry an equivalent pair — `main` is the
> default attitude-only task, `full_dof` is the legacy variant). The theory analysis
> itself (ConstraintTRPO, IPO, cost-GAE, barrier) remains valid for the current
> implementation. Standard terms (TRPO, IPO, KL divergence, GAE) are defined in
> [glossary.md](../reference/glossary.md); `max_kl` below is the per-update KL trust-region budget (agent config field).

---

## 1. TDC Controller (Grade: A)

- TDE formula (`tdc.py:449-450`): Correct
- PD torque sign (`tdc.py:412-435`): Correct
- Lambda matrix DLS inverse (`tdc.py:340-376`): Correct
- EMA filter (`tdc.py:399-410`): alpha=0.05, U_hat unfiltered -- correct
- IK DLS (`kinematics.py:227-258`): Yoshikawa adaptive damping -- correct
- Control timing: 50Hz consistent, reset handling correct

---

## 2. Reward System (Grade: A-)

- PBRS (potential-based reward shaping, `rewards.py:375`): optimal policy preservation guaranteed
- Crossover at ~20 deg: net reward negative beyond 20 deg error. PBRS mitigates.
- Constrained Env: reward-side `joint_velocity_weight=0`, `joint_oscillation_weight=0` (zeroed to avoid double-counting with the matching cost functions)

---

## 3. NORBC Constraint System (Grade: A-)

### 3.1 ConstraintTRPO Algorithm

| Component | Location | Verdict |
|-----------|----------|---------|
| Fisher-Vector Product | `constraint_trpo.py:346-379` | Correct (double backprop + cg_damping) |
| Conjugate Gradient | `constraint_trpo.py:381-409` | Correct (Polak-Ribiere, rdotr < 1e-10) |
| Surrogate Loss | `constraint_trpo.py:316-327` | Correct sign |
| KL Divergence | `constraint_trpo.py:329-339` | Standard Gaussian KL |
| TRPO Step Size | `constraint_trpo.py:652-655` | sqrt(2*max_kl / g^T F^{-1} g) |
| Log-Barrier | `constraint_trpo.py:479-492` | -log(margin)/t, correct |
| Cost Surrogate (IPO) | `constraint_trpo.py:624-628` | E[ratio * cost_adv] / (t * margin) |
| Barrier Schedule | `constraint_trpo.py:736-743` | Linear t: 1.0 -> 50.0 |
| Cost GAE | `constraint_trpo.py:277-298` | K independent TD(lambda) passes |
| Gradient Flow | 3-group separation | Actor(TRPO), Encoder(deferred Adam), Value(mini-batch Adam) |

### 3.2 Design Observations (Tier 2)

#### Line Search Acceptance Constants

The triple verification condition of the `_line_search()` method in `constraint_trpo.py`:

1. `improvement > 0` (reward surrogate improvement)
2. `kl <= max_kl * line_search_kl_margin` (default 1.5)
3. `cost_surr_k > line_search_cost_margin * margin` -> reject (default 0.5)

| Config field | Value | Rationale |
|:---|:---|:---|
| `line_search_kl_margin` | 1.5x | The TRPO natural-gradient step already targets `max_kl`; the line search's slightly looser margin avoids overly conservative steps. Standard TRPO uses 1.0x -- IPO's cost-feasibility check is an additional safeguard here. |
| `line_search_cost_margin` | 0.5x | Caps a single step to consuming at most half the remaining constraint budget -- a conservative choice that leaves room to recover from a constraint violation next step. |

Both fields are configurable (parameterized 2026-03-05).

#### Adaptive Alpha Separation

`adaptive_threshold_alpha` was split into two independently-tunable config fields:

| Field | Role | Formula |
|:---|:---|:---|
| `adaptive_threshold_scale` | Threshold scale | `target = max(d_k, j_c_k + scale * d_k)` |
| `adaptive_ema_alpha` | EMA smoothing coefficient | `d_k_adaptive = (1-a)*old + a*target` |

Tuning: high EMA alpha + low threshold scale = fast adaptation, conservative threshold; low EMA alpha + high
threshold scale = slow adaptation, aggressive threshold. Default `adaptive_ema_alpha=None` preserves prior
behavior (uses `adaptive_threshold_alpha` for both roles).

---

## 4. Domain Randomization (Grade: A)

A physically reasonable range. For details, see `DOMAIN_RANDOMIZATION.md`.

---

## 5. Encoder/Adaptation Gradient Flow (Grade: A)

- Phase 1 Encoder: `z_gt` (ground-truth privileged latent) stop-gradient, encoder learns regression
- Phase 2 Adaptation: `z_hat` (student-estimated latent) `.detach()` blocks PPO gradient, only aux loss trains `adapt_tconv` (the adaptation TCN module)
- ConstraintTRPO: encoder gradient deferred after TRPO line search -- correct

---

## 6. Summary

### Tier 1 Theoretical Errors: None

- TDC controller: mathematically correct
- Encoder/Adaptation: gradient flow correct
- PBRS: optimal policy preservation guaranteed
- ConstraintTRPO (NORBC): TRPO + IPO + Cost GAE + Barrier all correct
- Cost Critic: matches paper's multi-head cost value function
- Environment integration: double-counting prevention, cost flow correct

### Tier 2 Design Observations: 3

1. **Reward crossover at ~20 deg** -- PBRS mitigates
2. **Line search constants** -- now configurable (`line_search_kl_margin`, `line_search_cost_margin`)
3. **adaptive_alpha split** -- now separated (`adaptive_threshold_scale`, `adaptive_ema_alpha`)

### Tier 3 Minor Observations: 3

4. Terminal reward timing (Isaac Lab standard pattern)
5. No explicit action rate penalty (joint_oscillation cost serves indirect role)
6. Attitude error double noise (conservative design choice)
