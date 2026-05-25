# Theoretical Analysis (NORBC Constrained RL)

NORBC 논문의 Constrained RL 이론을 기준으로 ALBC 코드베이스의 이론적 정합성을 분석한 결과.
분석 일자: 2026-03-05.

> File paths in this doc predate the repo split — current code lives in
> `constrained_albc/envs/constrained_full_albc/` (`algorithms/constraint_trpo.py`,
> `mdp/constraints.py`). The theory analysis itself (ConstraintTRPO, IPO, cost-GAE,
> barrier) remains valid for the current implementation.

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

`constraint_trpo.py` `_line_search()` 메서드의 3중 검증 조건:

1. `improvement > 0` (reward surrogate improvement)
2. `kl <= max_kl * line_search_kl_margin` (default 1.5)
3. `cost_surr_k > line_search_cost_margin * margin` -> reject (default 0.5)

**KL margin (1.5x)**: TRPO natural gradient가 이미 max_kl을 타겟으로 하므로,
line search에서는 약간의 여유를 줘서 과도하게 보수적인 step을 방지.
표준 TRPO는 1.0을 쓰나, IPO의 cost feasibility check이 추가 안전장치 역할.

**Cost margin (0.5x)**: 한 step에서 남은 constraint budget의 최대 절반만 소비 허용.
보수적 전략으로, 다음 step에서 constraint violation 복구 가능성 보장.

두 상수 모두 설정 가능하도록 파라미터화 완료 (2026-03-05).

#### Adaptive Alpha Separation

`adaptive_threshold_alpha`를 두 역할로 분리:
- `adaptive_threshold_scale`: `target = max(d_k, j_c_k + scale * d_k)` 에서 threshold 스케일
- `adaptive_ema_alpha`: EMA smoothing 계수 `d_k_adaptive = (1-a)*old + a*target`

분리를 통해 독립적 튜닝 가능:
- 높은 EMA alpha + 낮은 threshold scale = 빠른 적응, 보수적 threshold
- 낮은 EMA alpha + 높은 threshold scale = 느린 적응, 공격적 threshold

기본값: `adaptive_ema_alpha=None` (기존 동작 유지, `adaptive_threshold_alpha` 값 사용).

---

## 4. Domain Randomization (Grade: A)

물리적으로 합리적인 범위. 상세 내용은 `DOMAIN_RANDOMIZATION.md` 참조.

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
