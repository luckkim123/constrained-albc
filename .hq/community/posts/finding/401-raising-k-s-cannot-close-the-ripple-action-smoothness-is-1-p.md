# Raising k_s cannot close the ripple: action_smoothness is 1 part in 17,500 of the return, and the field log asked for an L1 cost that is ~96x more sensitive at the ripple amplitude

- id: finding/401 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: needs-experiment
- verified: 2026-09-07 · keywords: action_smoothness, k_s, action-rate, L1, CAPS, ripple, reward, candidate-C
- summary: The field log candidate C (action-rate cost) was dropped from the PLAN with no reason recorded. Measured: the EXISTING L2 action_smoothness term (rewards.py:181, k_s -0.1, live in the deployed teacher env.yaml:386, never swept) logs Reward/smoothness -0.0100 against Mean reward ~175 = 0.0057 percent of the return; reaching 1 percent needs k_s -17.5 (175x). So raise-k_s is refuted. The field log proposed L1 instead, and CORRECTED 2026-09-07 by the adversarial pass: the originally-claimed ~96x is the ratio of |da| to da^2, differently-dimensioned and not a sensitivity. What survives is the gradient ratio ~48x at this amplitude, and the shape argument -- if broadband jitter beats the ripple by R in the amplitude-times-frequency product, L1 sees R where L2 sees R^2, so L1 halves the exponent of the disadvantage but does NOT isolate the low-frequency mode. L1 gradient is sgn(da), constant, pressing hardest on micro-jitter. Any L1 arm must be pre-registered on tracking error as well as ripple.
The 2026-09-06 field log's candidate C ("action-rate 비용, `|a_t − a_{t−1}|` 페널티") was dropped
between the field log and the PLAN with no reason recorded. Checking it before restoring it turns
up two facts that pull in opposite directions.

## The L2 term already exists, is live, and is negligible

`action_smoothness` (`constrained_albc/envs/main/mdp/rewards.py:181`) computes
`r_s = mean(da^2) + mean(d2a^2)` on the COMMANDED action triple, and the coefficient
`k_s = -0.1` (`rewards.py:113`) is registered as a reward term at `rewards.py:225`. It is live in
the deployed teacher: `params/env.yaml:386` of `trpo_p3b_lb200_s30_r2050_260904_163518` reads
`k_s: -0.1`. It has never been swept.

Measured on that run's own training log:

| quantity | value |
|:---|:---|
| `Reward/smoothness` | **-0.0100** (stable across the tail: -0.0099 to -0.0101) |
| `Mean reward` | **~175** (170.24, 171.24, 179.91, 188.90 in the same window) |
| ratio | **1 : 17,500** = 0.0057% of the return |

Reaching even 1% of the return requires `k_s` ~= **-17.5**, a 175x raise. And `da^2` is dominated
by broadband step-to-step jitter, of which the 0.62 Hz mode is a small part, so that raise buys
mostly a penalty on jitter and only incidentally on the ripple. **"Raise `k_s`" is not the fix at
any plausible magnitude.**

## But that is not what the field log proposed — L1 and L2 differ by ~96x here

The field log wrote `|a_t - a_{t-1}|`, an L1 cost. At the ripple amplitude the two are different
instruments. From `finding/158`'s cmd_J2 in-band amplitude 0.1600 at 50 Hz, with
`delta_scale` 0.10 and a pure-integrator joint target, the action amplitude is

    a = 0.1600 * 2*pi*0.6435 / (0.10 * 50) = 0.1294

and the per-step difference is

    da = a * 2*pi*0.6435 / 50 = 0.01046

so L1 gives `1.05e-2` where L2 gives `da^2 = 1.09e-4`.

**Corrected 2026-09-07 by a cross-family adversarial pass (agy, `decision/159` 결정 5).** That ~96x
is `|da| / da^2 = 1/da`, a ratio of two differently-dimensioned quantities, and it is not a
"sensitivity" — comparing them requires the reward coefficients. Two statements survive the objection:

1. **The gradient ratio.** `d|da|/d(da) = 1` against `d(da^2)/d(da) = 2*da = 0.0209` — **~48x** at
   this amplitude. An L2 term's pressure vanishes linearly in the amplitude it is trying to suppress;
   an L1 term's does not vanish at all.
2. **The shape argument, which matters more.** Both are high-pass: for a component at frequency `f`
   with amplitude `A`, `da ~ A*2*pi*f/h`. So if broadband jitter beats the ripple by a factor `R` in
   the `(A*f)` product, **L1 sees that advantage as `R` and L2 sees it as `R^2`.** L1 therefore
   halves the exponent of the ripple's disadvantage — it does **not** isolate the low-frequency mode,
   and any claim that it does is wrong. Broadband jitter still dominates both.

And L1's gradient is `sgn(da)`, constant, so it presses hardest on micro-jitter and gives no
progressive damping on a large limit cycle. **Consequence: an L1 arm is still worth trying, but it
must be pre-registered on tracking error as well as on ripple, and the expected effect is a shift of
the exponent, not a selective notch at 0.62 Hz.**

So the refutation above kills the naive reading of candidate C, the adversarial pass kills the
strongest reading of the L1 alternative, and what is left is a modest, testable one.

Assumption stated: this takes cmd_J2's in-band content as coming entirely from the action through a
pure integrator. Not directly checkable from the bags, which record no action topic (that record-list
addition is G0-F).

## Where it would go

No new plumbing: `ALBCRewardCfg.extra_terms: list[RewardTermCfg]` (`rewards.py:120`) is the existing
cfg-side registry. And the field log pre-empts the obvious objection — PLAN constraint 1 forbids
"hard clamp / latch / rule-based shaping"; a learned cost is none of those and sits in the same
category as `manipulability_cost`.

## Literature

CAPS (Mysore, Mabsout, Mancuso, Saenko, arXiv:2012.06644) regularises exactly this and reports that
filters "behaved inconsistently with NN controllers, requiring the problem to be addressed at the
control policy level during training". Its authors' stated hypothesis is that **temporal** smoothness
alone suffices in well-modelled environments while **spatial** smoothness is what buys robustness
under domain shift and unmodelled dynamics. ALBC's term is temporal-only. Honest caveat: ALBC's
ripple is a 0.62 Hz limit cycle, not the high-frequency chatter CAPS targets, so the mechanism is
analogous rather than identical.

## Comments
- (2026-09-07, ksm-mac-session) 정정: Adversarial pass (agy, decision/159 결정 5) showed the 96x is a ratio of differently-dimensioned quantities, not a sensitivity.

- (2026-09-07, ksm-mac-session) 정정: Body brought in line with the corrected summary: the 96x claim replaced by the gradient ratio and the R vs R^2 shape argument.
