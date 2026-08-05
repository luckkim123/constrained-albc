---
title: "Arm B is a dictionary-only control, not a Koopman result: it fitted no operator, so citing its NULL as evidence against Koopman is an indefensible overclaim"
tags: []
created: 2026-08-05T09:35:22.787654
updated: 2026-08-05T09:35:22.787654
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Arm B is a dictionary-only control, not a Koopman result: it fitted no operator, so citing its NULL as evidence against Koopman is an indefensible overclaim

Arm B (trpo_koopmanB_260804_202709) appended 7 hand-designed observables to the policy obs: sin/cos of roll, sin/cos of pitch, and the signed-quadratic body rates p|p|, q|q|, r|r| (72 -> 79). No K matrix exists anywhere in that code path. The implementation is a pure obs-builder edit in envs/main/mdp/observations.py compute_marine_features, and its own docstring states the intent: every column is a pointwise function of channels the policy already observes, so it adds no information, deliberately, since the surviving hypothesis is optimization geometry.

Koopman has two parts and both are required. The lifting (the dictionary of observables) is NECESSARILY NONLINEAR - a linear lift of a nonlinear system stays just as nonlinear. What becomes linear is the TIME EVOLUTION in the lifted space: psi(x_t+1) = K psi(x_t), with K a matrix. Minimal illustration: x_t+1 = x_t squared is nonlinear, but under the nonlinear lift psi = log x it becomes psi_t+1 = 2 psi_t, a linear operator. Koopman trades a higher-dimensional, nonlinearly-computed representation for a linear evolution rule.

Arm B shipped only the first part. The Koopman-specific testable content is the linear operator, and it was absent from the only training run the line ever produced.

Therefore:
- WRONG: Koopman lifting was tested and did not help.
- RIGHT: adding a fixed nonlinear basis of already-observed signals to the policy input did not help and cost transient quality (overshoot 7.96 -> 13.74 pp, pitch rise time +23 percent, worst at the EASIEST DR level).

The plan pre-registered this scope limit before the run, in section 5: a null here is evidence about this dictionary at 2000-5000 iters single-seed, not about lifting in general. The verdict record stands unchanged; only its CITATION scope is being corrected.

Mechanistic reason the dictionary alone could not help here: a nonlinear basis earns its keep when the downstream consumer is LINEAR (a least-squares operator fit, a linear MPC, a linear observer). Arm B fed it to an MLP policy, which can already synthesise sin(roll) or p|p| internally. The result was no gain plus wider input, which cost transient quality.

Where this bites: any paper text that cites arm B, and the koopman-lifting PLAN status block. A reviewer will ask whether an operator was ever fitted, and the honest answer is no. Retained as the low anchor arm of the reopened 5-arm study (programs/koopman-lifting/PLAN.md section 12).
