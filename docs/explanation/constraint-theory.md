# Theoretical Analysis (NORBC Constrained RL)

Results of analyzing the theoretical consistency of the ALBC codebase against the Constrained RL theory of the NORBC paper. Analysis date: 2026-03-05.

> File paths in this doc predate the repo split — current code lives in
> `constrained_albc/envs/_core/algorithms/constraint_trpo.py` (shared by both env
> packages via import shims) and `constrained_albc/envs/{main,full_dof}/mdp/constraints.py`
> (still an equivalent pair per variant — `main` is the default attitude-only task,
> `full_dof` is the legacy variant). The theory analysis
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

- PBRS (potential-based reward shaping): theory background only -- optimal policy preservation is a property of the technique in general, but PBRS is not present in the current reward code. No PBRS code exists anywhere in the repo (`rewards.py` is 259 lines; grep for `PBRS`/`potential-based reward`/`reward.shaping` finds no matches).
- Crossover at ~20 deg: net reward negative beyond 20 deg error. No PBRS mitigation exists in current code (design observation, unaddressed).
- Constrained Env: reward-side `joint_velocity_weight=0`, `joint_oscillation_weight=0` (zeroed to avoid double-counting with the matching cost functions)

---

## 3. NORBC Constraint System (Grade: A-)

### 3.1 ConstraintTRPO Algorithm

| Component | Location | Verdict |
|-----------|----------|---------|
| Fisher-Vector Product | `constraint_trpo.py:368-379` (`_fisher_vector_product`) | Correct (double backprop + cg_damping) |
| Conjugate Gradient | `constraint_trpo.py:381-400` (`_conjugate_gradient`) | Correct (Polak-Ribiere, rdotr < 1e-10) |
| Surrogate Loss | `constraint_trpo.py:475` (`reward_surr`, in `surrogate()`, `:471-500`) | Correct sign |
| KL Divergence | `constraint_trpo.py:343-348` (`_gaussian_kl`) | Standard Gaussian KL |
| TRPO Step Size | `constraint_trpo.py:559,564` (`shs`, `step_dir`) | sqrt(2*max_kl / g^T F^{-1} g) |
| Log-Barrier | `constraint_trpo.py:477,484` (`margin`, `barrier`, in `surrogate()`, `:471-500`) | -log(margin)/t, correct |
| Cost Surrogate (IPO) | `constraint_trpo.py:476` (`cost_surrs`, in `surrogate()`, `:471-500`) | E[ratio * cost_adv] / (1 - cost_gamma) |
| Barrier Schedule | `constraint_trpo.py:64,119` (constructor default, default 100.0); used `:484`, logged `:638-639` | Fixed constant, no anneal schedule (not "Linear t: 1.0 -> 50.0") |
| Cost GAE | `constraint_trpo.py:295-314` (`_compute_cost_returns`) | K independent TD(lambda) passes |
| Gradient Flow | 3-group separation | Actor(TRPO), Encoder(deferred Adam), Value(mini-batch Adam) |

### 3.2 Design Observations (Tier 2)

#### Line Search Acceptance Condition

The `_line_search()` method in `constraint_trpo.py` (`:402-424`) accepts a backtracking candidate when both hold
in a single combined check (`:420`):

1. `(old_loss - new_loss) > 0` -- the surrogate loss decreased (reward improved, net of the barrier penalty that
   is already folded into that same loss).
2. `kl <= max_kl * line_search_kl_margin` (default 1.5, `kl_limit` computed at `:414`).

There is no separate cost-margin rejection check and no `line_search_cost_margin` field in the current code. IPO
cost-feasibility is instead enforced implicitly through the log-barrier term inside `surrogate()`
(`constraint_trpo.py:477,484`): a candidate that pushes a cost too close to its budget inflates the barrier term,
which raises `new_loss` and fails condition 1 on its own, without a dedicated third check.

| Config field | Value | Rationale |
|:---|:---|:---|
| `line_search_kl_margin` | 1.5x (`constraint_trpo.py:63`, default) | The TRPO natural-gradient step already targets `max_kl`; the line search's slightly looser margin avoids overly conservative steps. Standard TRPO uses 1.0x -- IPO's cost-feasibility check is an additional safeguard here. |

`line_search_kl_margin` is configurable via the constructor. `line_search_cost_margin` does not exist in the
current implementation.

#### Adaptive Threshold (Barrier Alpha)

The adaptive threshold is driven by a single config field, `barrier_alpha` (constructor param
`constraint_trpo.py:65`, default 0.02; stored as `self._barrier_alpha`, `:120`), fed directly into
`_compute_adaptive_thresholds()` (`:320-322`):

```
d_k^i = max(d_k, J_C_k + barrier_alpha * d_k)
```

There is no EMA smoothing and no split into separate `adaptive_threshold_scale` / `adaptive_ema_alpha` fields --
neither exists in the current code. The threshold is recomputed fresh from the current-iteration mean cost return
every update call (`_compute_adaptive_thresholds(mean_cost_returns)`, `:460`); a lower `barrier_alpha` yields a
tighter, more conservative threshold and vice versa.

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
- PBRS: theory background only, not present in current reward code
- ConstraintTRPO (NORBC): TRPO + IPO + Cost GAE + Barrier all correct
- Cost Critic: matches paper's multi-head cost value function
- Environment integration: double-counting prevention, cost flow correct

### Tier 2 Design Observations: 3

1. **Reward crossover at ~20 deg** -- no PBRS mitigation in current code (unaddressed)
2. **Line search constants** -- `line_search_kl_margin` is configurable; no separate `line_search_cost_margin` field exists (cost feasibility is folded into the surrogate loss's barrier term instead)
3. **adaptive threshold** -- single `barrier_alpha` config field, no EMA smoothing; `adaptive_threshold_scale`/`adaptive_ema_alpha` do not exist in current code

### Tier 3 Minor Observations: 3

4. Terminal reward timing (Isaac Lab standard pattern)
5. No explicit action rate penalty (joint_oscillation cost serves indirect role)
6. Attitude error double noise (conservative design choice)
