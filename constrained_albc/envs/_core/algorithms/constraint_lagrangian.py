# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Lagrangian constrained TRPO — arm N1 of program `paper-ablation-5000`.

Why this arm exists. The comparison table has arms that turn IPO OFF (`TRPO-NoIPO`,
"no-both") but not one arm that enforces the same constraints by a DIFFERENT mechanism,
so the claim "IPO beats the standard alternative" has no control group at all
(PLAN.md §3-2 N1). The Lagrangian multiplier method is that alternative: it is the
de-facto standard baseline in the safe-RL literature (Stooke et al., arXiv:2007.03964).

What actually differs from `ConstraintTRPO`. Exactly one term. The parent computes the
per-constraint cost surrogates, standardizes the cost advantages, fits the cost critic
and runs the TRPO step; all of that is inherited untouched, so the two arms share the
same K=10 constraint list, the same budgets, the same cost GAE and the same trust
region. Only `_constraint_penalty` is swapped -- an IPO log-barrier here becomes a
linear penalty `sum_k lambda_k * cost_surr_k` -- plus a dual ascent step on the
multipliers after each policy update. Anything else that diverged would confound the
comparison the arm was built to make.

Dual parameterization. The multipliers are kept as unconstrained `nu` and mapped
through softplus, so `lambda >= 0` holds by construction instead of by a clamp that
would silently stick at zero and kill the gradient. `lambda_max` bounds them from
above; that bound is a safety device, not a tuning knob -- see the failure mode below.

The failure mode to watch, named in PLAN.md §4-1. TRPO's line search accepts a step
only if the surrogate improves, and a large `lambda` makes the constraint term dominate
the objective, so every backtrack can fail and the policy simply stops moving -- with
no error, and with plausible-looking reward curves from a frozen policy. Two things
guard it and both must be read, not assumed: `lambda_max` caps the penalty, and
`ConstraintTRPO` already records `_last_line_search_success` every iteration. That
metric is the pre-registered read-out for this arm: a run whose line-search success
rate collapses has failed, whatever its reward curve says.

Untuned by design. `lagrangian_lr` and `lagrangian_max` below are starting points, not
measured values. No run has used this class yet.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

from .constraint_trpo import ConstraintTRPO


class ConstraintLagrangian(ConstraintTRPO):
    """ConstraintTRPO with the IPO barrier replaced by Lagrangian multipliers."""

    def __init__(
        self,
        *args,
        lagrangian_lr: float = 0.01,
        lagrangian_init: float = 0.0,
        lagrangian_max: float = 10.0,
        **kwargs,
    ) -> None:
        """
        Args:
            lagrangian_lr: Dual ascent step size on the raw multipliers `nu`.
            lagrangian_init: Initial `nu`. 0.0 means `lambda = softplus(0) = 0.693`,
                i.e. the run starts with the constraints already weighted rather than
                from an unconstrained policy it then has to drag back.
            lagrangian_max: Upper clamp on `lambda`. Bounds the line-search failure
                mode described in the module docstring.
        """
        super().__init__(*args, **kwargs)
        self._lag_lr = float(lagrangian_lr)
        self._lag_max = float(lagrangian_max)
        # Unconstrained duals; lambda = softplus(nu) is non-negative by construction.
        # A plain tensor, not an nn.Parameter: these are ascended by hand in
        # _dual_ascent() and must never receive gradient from the policy surrogate.
        self._nu = torch.full((self.num_constraints,), float(lagrangian_init), device=self.device)
        self._last_lambdas: list[float] = [0.0] * self.num_constraints

    def _constraint_penalty(self, cost_surrs: torch.Tensor, barrier_base: torch.Tensor) -> torch.Tensor:
        """Linear Lagrangian penalty in place of the parent's log barrier.

        `barrier_base` is the parent's IPO static margin and has no meaning here: the
        Lagrangian enforces the budget through the dual variable, which is updated from
        the measured cost return in `_dual_ascent`, not through a per-iteration margin.

        The multipliers are detached constants for this term -- the policy gradient must
        flow through `cost_surrs` only. Ascending `nu` here instead would couple the dual
        update to the line-search backtracks, which evaluate the surrogate several times
        per iteration and would multiply the dual step by an arbitrary factor.
        """
        del barrier_base
        with torch.no_grad():
            lam = F.softplus(self._nu).clamp(max=self._lag_max)
            self._last_lambdas = lam.tolist()
        penalty = (lam * cost_surrs).sum()
        # Reuses the parent's monitoring slot so existing logging shows this arm's
        # constraint penalty in the same place; the name says "barrier" for that reason.
        self._last_barrier_penalty = penalty.item()
        return penalty

    def update(self) -> dict[str, float]:
        """Parent update, then one dual ascent step on the measured violation."""
        metrics = super().update()
        self._dual_ascent()
        return metrics

    def _dual_ascent(self) -> None:
        """`nu <- nu + lr * (mean_cost_return - budget)`, once per policy update.

        Ascent on the violation: a constraint over its budget raises its own multiplier
        until the policy is pushed back under, and one comfortably inside its budget
        decays toward zero and stops taxing the reward. Runs after the TRPO step so the
        violation is measured against the policy that was actually just produced.

        The lower clamp on `nu` is numerical, not a design choice: softplus underflows
        to exactly 0 far below -20, and a multiplier pinned at hard zero can never
        recover if the constraint is violated later.
        """
        if self.num_constraints == 0:
            return
        violation = self._last_mean_cost_returns - self.d_k
        self._nu.add_(self._lag_lr * violation)
        self._nu.clamp_(min=-20.0)
