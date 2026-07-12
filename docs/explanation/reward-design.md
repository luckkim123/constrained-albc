# Reward Design Rationale

> **Status**: 2026-07-12 | **Source**: `constrained_albc/envs/main/mdp/rewards.py`,
> `constrained_albc/envs/main/mdp/constraints.py`, `constrained_albc/envs/main/config.py`

This is rationale, not reference — every formula, weight, and numeric value lives in
[`reference/reward.md`](../reference/reward.md) (the reward terms) and
[`reference/constraints.md`](../reference/constraints.md) (the constraint costs). This page only
answers *why* the current `envs/main` (attitude-only ALBC) design looks the way it does.

## Why the tracking terms are shaped the way they are

The two tracking terms, `att_rp` and `yaw_vel`, share one kernel: a bounded exponential reward
that peaks at zero error, combined with a quadratic penalty that grows with error. Both halves of
that kernel share a structural weakness at exactly the point that matters most — right at the
target. The exponential's slope and the quadratic's slope both vanish as the error goes to zero,
so once the policy is close to the target it stops receiving any gradient telling it to close the
remaining gap: a dead zone around the setpoint. See `reference/reward.md` §2 for the kernel
definition.

An unbounded linear penalty is the obvious fix (constant gradient everywhere, including at zero),
but it was tried and disabled: the codebase records that it caused its own dead zone rather than
fixing the original one, and it stays off in every shipped configuration. The mitigation actually
in use is a bounded saturating penalty instead — a non-vanishing gradient at zero error like the
linear term, but capped at large error instead of growing without bound, so it cannot fight the
exponential term's own large-error behavior the way the unbounded linear term did. That fix
currently lives only on `yaw_vel`; `att_rp` keeps the same dead zone as an acknowledged, still-open
gap rather than an oversight — the kernel already carries an alternative saturating shape available
to close it later.

`att_rp` additionally up-weights roll error over pitch error. This is not an arbitrary tuning
choice: the vehicle's thruster allocation gives roll far less torque authority than pitch, so under
an identical reward gradient a naive symmetric penalty would leave roll harder to correct than
pitch purely because the actuators are weaker on that axis. Up-weighting roll spends more reward
gradient exactly where the vehicle has less physical leverage to earn it, instead of letting the
reward silently favor whichever axis happens to be easier to actuate. See `reference/reward.md`
§4.1 for the exact weighting and its grounding in the thruster allocation matrix.

## Why some limits are constraints, not reward penalties

Not every "the vehicle should stay within X" requirement lives in the scalar reward. Energy and
smoothness costs — torque, thruster usage, action smoothness, sustained tracking bias — are reward
penalties, tuned like the tracking terms by a weight that trades off against the rest of the
reward sum. A separate set of physical and operational limits — attitude and rate ceilings, torque
and joint-position limits, thruster utilization headroom, accumulated yaw, manipulability, and
others — are wired as constraint costs consumed by the IPO log-barrier inside ConstraintTRPO
instead (see `reference/constraints.md`).

The distinction is about what kind of guarantee each mechanism gives:

| Mechanism | Guarantee | Miscalibration failure mode |
|:---|:---|:---|
| Reward penalty | Discourages a behavior in proportion to its weight vs. every other term in the sum | Too small -> the limit gets crossed once the tracking gradient outweighs it; too large -> tracking is sacrificed broadly, and the trade-off must be re-balanced by hand whenever another term's weight changes |
| Constraint cost (IPO barrier) | Enforces an explicit violation budget directly through the barrier term, independent of reward weighting | — |

Limits that must hold regardless of reward tuning are constraints; behaviors that should merely be
discouraged in the aggregate are reward penalties.

## Why the settling cost is gated, not always-on

One constraint, the roll/pitch angular-rate settling cost, only activates once the vehicle is
already close to its target attitude — it is zero while the vehicle is still far from target and
turns on only during settling. This is deliberate: angular velocity is exactly what the vehicle
needs in order to reach the target attitude in the first place, so an always-on penalty on angular
rate would fight the attitude-tracking reward during the approach, penalizing the very motion
required to converge. Gating the cost to the near-target regime lets it do its intended job —
suppressing residual oscillation and overshoot once the vehicle has essentially arrived — without
opposing the transit motion that gets it there. See `reference/constraints.md` §3.2 for the cost
definition and its exact gating threshold.

## Related

- [`reference/reward.md`](../reference/reward.md) — all six reward terms, weights, and the
  dt-scaling mechanism (SSOT for reward formulas/values)
- [`reference/constraints.md`](../reference/constraints.md) — all ten constraint costs, budgets,
  and the ConstraintTRPO+IPO mechanism (SSOT for constraint formulas/values)
- [`reference/main-network-architecture.md`](../reference/main-network-architecture.md) —
  encoder/actor/critic and where the reward and constraint signals feed into training
