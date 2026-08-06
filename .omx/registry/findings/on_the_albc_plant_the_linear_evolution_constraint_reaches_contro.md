---
title: "On the ALBC plant the linear-evolution constraint reaches control and costs it: arm C is beaten by its own nonlinear twin in 51 of 72 cells"
tags: ["koopman", "linearity", "control", "arm-c", "verdict", "albc"]
created: 2026-08-06T02:58:58.616382
updated: 2026-08-06T02:58:58.616382
sources: ["experiments/rsl_rl/albc_trpo_teacher/koopman_linearity/README.md", ".omx/programs/koopman-lifting/PLAN.md#12.10"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# On the ALBC plant the linear-evolution constraint reaches control and costs it: arm C is beaten by its own nonlinear twin in 51 of 72 cells

SOURCE: campaign koopman_linearity README.md, judged 2026-08-06, PLAN 12.10. Three arms, each 5000 iters at 4096 envs seed 30, all handed the SAME 5 channels (a frozen module's 25-step-ahead prediction of roll/pitch/p/q/r) and differing only in the module: learned lift + learned LINEAR operator (arm C), the same lift with the operator swapped for an MLP (the twin), and a frozen RANDOM lift + linear operator. Gates first: survival 100 pct for every arm at every DR level; pairing 96/96 against the baseline and 96/96 arm-to-arm. No arm beats the E-int baseline -- worse in 58/72, 55/72 and 57/72 cells for C, twin and random against 40/72 for arm B. The result that matters: arm C and the twin SEPARATE, and the LINEAR arm is the worse one -- C worse than the twin in 51/72 cells with 15 floor crossings, att_norm ss_error +0.233 / +0.410 / +0.554 deg at soft / medium / hard against a 0.1 floor and ss_error_std +0.799 / +1.908 at medium / hard against 0.6. Two controls rule out the obvious confounds. It is NOT a prediction-quality difference: on the five fed channels the two frozen modules score 39.4 pct and 39.5 pct against the persistence null, indistinguishable, while their outputs correlate only 0.60 to 0.99 per channel, so the channels differ in content rather than accuracy. And it is NOT the cost of widening the observation: C and the twin widen it identically by 5 dims from the same module family, and arm B widens it MORE by 7 dims while regressing LESS. PLAN 12.5 verdict is outcome 3 -- a methods subsection as a controlled negative, never a primary contribution, and the main paper does not wait on it. Pre-registered prediction 1 (arm C does not clear the control bar) CONFIRMED; prediction 2 (C and the twin do not separate) REFUTED at the control level, having already been refuted at the prediction level in PLAN 12.8. Bounds: n=1 per arm, single seed, screening floors; the twin is the CONTROL and is itself worse than baseline, so the claim is that the linear constraint costs, not that this stack should adopt the twin.
