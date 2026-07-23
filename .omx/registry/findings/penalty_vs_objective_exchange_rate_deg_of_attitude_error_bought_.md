---
title: "Penalty-vs-objective exchange rate (deg of attitude error bought per penalty term) is the rescaling evidence, not the 1% reward share; all four penalties together buy only 0.125 deg"
tags: ["reward", "penalty", "rescaling", "exchange-rate", "tuning", "constraint-trpo", "envs-main"]
created: 2026-07-20T03:00:37.061166
updated: 2026-07-23T06:37:45.315633
sources: []
links: ["next_experiment_workflow_pick_a_baseline_train_once_then_re_tune.md", "reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o.md", "real_robot_deployment_vibration_differential_diagnosis_by_sim_to.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
---

# Penalty-vs-objective exchange rate (deg of attitude error bought per penalty term) is the rescaling evidence, not the 1% reward share; all four penalties together buy only 0.125 deg

The "penalty terms are ~1% of Reward/total so they do not fight the objective" finding (baseline
trpo_baseline_260713_031325 report §2) is DIRECTIONALLY right but argued from the WRONG quantity.
Reward-value share is not decision influence. The decision-relevant quantity is the EXCHANGE RATE:
how much of the objective (attitude error) the policy can buy by giving the penalty up entirely.

## The computation (baseline operating point, code-verified rewards.py:108-118, 129-162)

r_att = k_att * (exp(-e^2 / 2 sigma^2) - q e^2), k_att=9.0, sigma=0.10, q=0.833.
Inverting the reported final-200 value att_rp=6.22 gives the operating error e = 0.0849 rad = 4.87 deg
(independently consistent with the project's known ~5 deg attitude regime -- a useful sanity check that
the reward decomposition and the eval SS error describe the same policy).

At that point dr_att/de = -54.6 reward per radian. Dividing each penalty's final-200 magnitude by it:

| penalty term | final-200 | worth, in attitude error |
|---|---|---|
| torque     | -0.042 | 0.044 deg |
| thruster   | -0.028 | 0.029 deg |
| smoothness | -0.024 | 0.025 deg |
| bias       | -0.025 | 0.026 deg |
| ALL FOUR   | -0.119 | **0.125 deg** |

So the policy would trade away EVERY shaping penalty in exchange for 0.125 deg of attitude error --
roughly 2.5% of the 4.87 deg it actually holds, and far inside env-to-env spread. The penalties are
not merely small in the sum; they are below the objective's own noise floor as a decision criterion.
Order-of-magnitude only (local linearization of a saturating kernel at one operating point), but the
conclusion is scale-robust: it would take a ~10-100x ratio change before a penalty buys a degree.

## Why the exchange rate and not the percentage

A term's reward SHARE and its GRADIENT share are different numbers, and only the second one moves the
policy. A term can hold 1% of the value while sitting where its own gradient is large (or vice versa) --
here att_rp is near e ~ sigma, which is exactly where the exp kernel's gradient PEAKS (rewards.py:12
comment), so the tracking term is at maximum pull while the quadratic penalties are at their weakest.
The percentage argument would have been equally "true" in a case where the penalties dominated behavior.
Compute the exchange rate before concluding a term is inert, and state a penalty's weight in objective
units (degrees, m/s), not in percent-of-total.

## Consequence for a rescaling experiment

This makes a penalty-rescaling experiment justified in principle, but it is exactly phase 2 of the
already-recorded two-phase plan ([[next_experiment_workflow_pick_a_baseline_train_once_then_re_tune]]),
so it must obey that page's couplings -- above all: only term RATIOS reach the ConstraintTRPO actor
(global scaling is a no-op plus a DORAEMON performance_lb confound,
[[reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o]]).

Open counter-argument that must be settled BEFORE launching: torque and thruster effort are ALSO covered
by the constraint layer, and those constraints report large slack in the same baseline (thruster_util
margin 7.79, arm_torque 7.29 -- 10 constraints all satisfied). The constrained formulation has therefore
already DECLINED to push on effort, deliberately. Raising the reward penalties is a preference change
(efficiency / smoothness / real-robot vibration), not a safety fix, and it buys its effect by spending
attitude accuracy. So the experiment needs a measured deficiency as its motivation (e.g. ss_jitter, or
deployment vibration -- note [[real_robot_deployment_vibration_differential_diagnosis_by_sim_to]] already
exonerates the action_smoothness term for vibration), not the aesthetic observation that 1% looks small.
Without that, it is the "generic solution without evidence" anti-pattern (.claude/rules/03).

---

## Update (2026-07-23T06:37:45.315633)

CLOSED 2026-07-23 (plan consolidation, Z10 gate): the page's own gate (a MEASURED deficiency motivating rescale) answers itself -- no measured ss_jitter/vibration deficiency exists; the four penalties total ~1.4% of reward (-0.12 vs ~8.8, diagnose-20260723-134359) and the constraint layer already declines to push on effort. Lead closes resolved-by-gate. Reactivation edge: measured deployment vibration / jitter deficiency.
