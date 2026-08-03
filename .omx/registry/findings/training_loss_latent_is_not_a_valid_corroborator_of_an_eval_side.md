---
title: "Training loss_latent is NOT a valid corroborator of an eval-side latent result: the widened-encoder arm moved them in opposite directions"
tags: []
created: 2026-08-03T14:52:19.860832
updated: 2026-08-03T14:52:19.860832
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# Training loss_latent is NOT a valid corroborator of an eval-side latent result: the widened-encoder arm moved them in opposite directions

## The measurement

Four student arms distilled from the same E-int teacher, hard-DR eval, 2026-08-03:

| arm | train `loss_latent` (trailing-50) | eval `sum(MSE)` at hard |
|:--|--:|--:|
| C3 (128, no extra obs) | 0.004842 | 0.5453 |
| CTL (dim=0 control) | 0.004859 | 0.5566 |
| B2 (128 + 4 channels) | 0.004572 | 0.4996 |
| WIDE (256 + 4 channels) | **0.004154** (best) | **0.5672** (worst of the extra-obs arms) |

WIDE has the lowest training loss of all four and the highest eval latent error of the
extra-obs arms. The two signals point in opposite directions on the same axis.

## Why they can diverge

DAgger runs at a fixed beta of 0.5, so the training states are half teacher-driven. The eval
is fully student-driven closed loop. A higher-capacity encoder fits the mixed distribution
better and transfers worse — an ordinary distribution-shift result, but one that is invisible
if only one of the two numbers is read.

## What this retires

The Phase C report (`diagnose-20260803-223517`) cited B2's `loss_latent` at -5.9% as
INDEPENDENT corroboration of its eval `R2` gain. That inference is not valid: this arm shows
the same signal agreeing in direction while the eval disagrees, so agreement carries no
information. Phase C's verdict is unaffected (it was INCONCLUSIVE on the latent axis), but
no future report in this campaign should cite the training loss as evidence for an eval-side
latent claim.

Use the training loss for what it does measure: whether the optimisation ran, converged, and
is comparable across arms. Not for whether the student generalises.

