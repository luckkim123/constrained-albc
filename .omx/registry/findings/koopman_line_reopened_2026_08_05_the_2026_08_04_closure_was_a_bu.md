---
title: "Koopman line REOPENED 2026-08-05: the 2026-08-04 closure was a budget decision under a control-performance goal, and no training arm ever fitted a Koopman operator"
tags: []
created: 2026-08-05T08:52:56.878202
updated: 2026-08-05T08:52:56.878202
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Koopman line REOPENED 2026-08-05: the 2026-08-04 closure was a budget decision under a control-performance goal, and no training arm ever fitted a Koopman operator

The Koopman line is REOPENED as of 2026-08-05. The 2026-08-04 LINE CLOSED verdict is retained as a record of what was decided, not of what was measured, and arm B's NULL is NOT re-litigated.

Two facts drive the reopen, both pre-registered in the program plan rather than found afterwards.

1. No Koopman OPERATOR was ever fitted in a training arm. Arm B (trpo_koopmanB_260804_202709) shipped the dictionary half only: 7 hand-designed observables appended to the policy obs, with no K matrix anywhere in the code. The Koopman-specific content is the linear evolution operator, and it was absent. The plan says so itself in section 5: a null there is evidence about this dictionary at 2000-5000 iters single-seed, not about lifting in general.

2. The clause that closed the line is a BUDGET decision. Section 8 exit clause 2 reads: arm B returns NULL and no one is willing to spend the >=15 GPU-h that arm C's control set costs. It was taken under the then-current owner directive in section 1, a cheap side-bet on control gains.

The objective changed on 2026-08-05: paper contribution is now primary and control performance secondary. That re-prices the control set. Under a control goal the nonlinear twin and the random expansion are overhead paid to attribute a win. Under a paper goal they ARE the experiment, because the linear-versus-nonlinear latent-dynamics question is open everywhere in the literature (research doc section 6 item 2 calls our control-arm pair the first direct test) and no published work isolates it, KIPPO included.

Roster status: 5 arms, 2 complete. Baseline E-int and arm B (NULL, retained as the low anchor) are done. Remaining are arm C (learned dictionary plus learned K, frozen before RL), the nonlinear twin (same size, same losses, K replaced by an MLP - this is the load-bearing arm), and the random expansion control.

Sequencing is cheap-first and binding: Phase 0b instrumentation (--save-action, about 10 lines, 0.25 GPU-h) then the offline A4 fit study (0 GPU) with a kill gate - if the learned lift's multi-step prediction error is not separable from the random-expansion control offline, stop before spending the 15 GPU-h. Only then the 3 training runs, and only on explicit owner approval.

A paper-inclusion decision rule is pre-registered in plan section 12.5 with four outcomes, so that a flat null costs the main paper nothing beyond one limitations paragraph. The main paper does not wait on this line and does not depend on it.

Open design decision before arm C can be specified (plan 12.7): where the linearity is consumed. If phi_x output is merely concatenated to the policy input, K never acts at inference and the arm degenerates toward arm B with a learned basis.

Full detail: .omx/programs/koopman-lifting/PLAN.md section 12.
