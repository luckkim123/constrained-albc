# Theoretical Analysis (NORBC Constrained RL)

Results of analyzing the theoretical consistency of the ALBC codebase against the Constrained RL theory of the NORBC paper.
Analysis date: 2026-03-05.

> File paths in this doc predate the repo split — current code lives in
> `constrained_albc/envs/{main,full_dof}/` (`algorithms/constraint_trpo.py`,
> `mdp/constraints.py`; both env packages carry an equivalent pair — `main` is the
> default attitude-only task, `full_dof` is the legacy variant). The theory analysis
> itself (ConstraintTRPO, IPO, cost-GAE, barrier) remains valid for the current
> implementation.

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

- PBRS (`rewards.py:375`): Optimal policy preservation guaranteed
- Crossover at ~20 deg: net reward negative beyond 20 deg error. PBRS mitigates.
- Constrained Env: `joint_velocity_weight=0`, `joint_oscillation_weight=0` prevents double-counting with cost functions

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

**KL margin (1.5x)**: Since the TRPO natural gradient already targets max_kl,
the line search gives a slight margin to prevent overly conservative steps.
Standard TRPO uses 1.0, but IPO's cost feasibility check serves as an additional safeguard.

**Cost margin (0.5x)**: Allow consuming at most half of the remaining constraint budget in a single step.
A conservative strategy that guarantees the possibility of recovering from a constraint violation in the next step.

Both constants have been parameterized to be configurable (2026-03-05).

#### Adaptive Alpha Separation

Split `adaptive_threshold_alpha` into two roles:
- `adaptive_threshold_scale`: the threshold scale in `target = max(d_k, j_c_k + scale * d_k)`
- `adaptive_ema_alpha`: the EMA smoothing coefficient `d_k_adaptive = (1-a)*old + a*target`

The split enables independent tuning:
- High EMA alpha + low threshold scale = fast adaptation, conservative threshold
- Low EMA alpha + high threshold scale = slow adaptation, aggressive threshold

Default: `adaptive_ema_alpha=None` (preserves the existing behavior, uses the `adaptive_threshold_alpha` value).

---

## 4. Domain Randomization (Grade: A)

A physically reasonable range. For details, see `DOMAIN_RANDOMIZATION.md`.

---

## 5. Encoder/Adaptation Gradient Flow (Grade: A)

- Phase 1 Encoder: z_gt stop-gradient, encoder learns regression
- Phase 2 Adaptation: z_hat.detach() blocks PPO gradient, only aux loss trains adapt_tconv
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
