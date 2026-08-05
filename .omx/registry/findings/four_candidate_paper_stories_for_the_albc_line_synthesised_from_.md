---
title: "Four candidate paper stories for the ALBC line, synthesised from 55 substantive wiki decisions 2026-08-05"
tags: []
created: 2026-08-05T09:35:50.294553
updated: 2026-08-05T09:35:50.294553
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Four candidate paper stories for the ALBC line, synthesised from 55 substantive wiki decisions 2026-08-05

Context: the owner wants a paper (not submitted anywhere yet; the IROS 2026 attempt was never submitted and its notes at references/iros_2026/ are stale from January, superseded by the TAM fix, buoyfix, the teacher campaign, obs4 and student distillation). The wiki holds 69 decision pages; removing 14 engine-gap tooling entries leaves 55 substantive results. The backlog is empty (both needs-experiment and needs-apply-before-retrain return zero rows), so the experimental program is at a natural stopping point. These 55 results cluster into four coherent stories.

STORY A - OBSERVABILITY. Claim: what the policy can observe, chosen for real-sensor deployability, was the dominant lever, not the algorithm. Evidence: two independent interventions moving the same way - bias_ema (69 -> 72D) cut steady-state roll error 68 percent and pitch 29 percent at the DR-fair none point and additionally cleared a DORAEMON feasibility stall; obs4 (72 -> 76D) passed H1 with margin and bought hard-DR tail and spread. Both are computable from real sensors. Negative controls available: arm B (a nonlinear basis of ALREADY-observed signals) hurt, and privileged fault obs was not adopted. Message sharpens to: NEW information helps, re-encoding existing signals or supplying non-deployable signals does not. Likely writable with zero additional runs. Koopman appears here only as the arm B negative control, and only under the corrected citation scope (see the arm_b_is_a_dictionary_only_control page).

STORY B - CURRICULUM MECHANICS. Claim: the knobs of an automatic DR curriculum do not do what their names say. Evidence: max_iterations is a DR-EXPANSION clock, not a training budget (5000 -> 8000 regressed, and the cause was wider DR not more optimisation); performance_lb sets the success-rate PEAK, so a reported DORAEMON success of 0.97 reflects a low bar rather than a good policy; DORAEMON alpha is a feasibility floor not an expansion lever; the HARDER curriculum generalised WORST out of distribution. Counter-intuitive and methodologically useful. Reviewer risk: is this DORAEMON-specific or general, which invites a second-platform reproduction demand. No Koopman content.

STORY C - DISTILLATION PROXY REBUTTAL. Claim: latent reconstruction fidelity is a poor proxy for closed-loop performance in privileged distillation. Evidence: X1 tail-split lifted hard aggregate latent R2 from -0.1044 to +0.0645 and moved no control metric - and crucially the reason is known, that delta is only a 6.69 percent RMSE cut so a sub-floor control change was PREDICTED (state it as a measured poor exchange rate, NOT as decoupling, which was retracted); lambda_latent swept over [0,4] with no decision-grade control effect and lambda=1 a measured local optimum; meanwhile GRU memory plus corrected DAgger mixing compounded so that C3 became the first student to beat its teacher by a decision floor, i.e. the gain came from somewhere other than reconstruction accuracy. Most novel scientifically, since privileged-distillation papers routinely report reconstruction error as the headline metric and nobody has priced the exchange rate. This is the ONE story where Koopman lives as a genuine comparison arm (does imposing linear latent dynamics change the picture).

STORY D - FAULT TOLERANCE. Claim: a UVMS with genuinely faulted thrusters can be held by fault-DR alone, without explicit fault detection. Evidence: fault-DR adopted with 5-12x less m4-dead degradation and zero terminations; counter-intuitively, RAISING trained fault severity made m4-dead rejection 2.9-5.5x WORSE while buying a 2.50x curriculum speedup; privileged fault obs was not adopted, so tolerating beats knowing. Strong motivation because the real vehicle has 2 of 6 thrusters faulted. Caveat a reviewer will raise: training exposure is independent Bernoulli per thruster at p=0.10, so the count is Binomial(6, 0.1) with no cap - exactly-2 faults, the real robot's condition, is only 9.8 percent of envs, and 3-or-more is 1.6 percent. The real operating point sits in the lower tail of the training distribution. Real-tank validation likely demanded. No Koopman content.

Bearing on the Koopman line: Koopman contributes one result (arm B NULL) against 55 already earned. If paper contribution is the goal, harvesting is higher-yield than opening a new axis; the reopened Koopman study is justified only as an OPTIONAL venue-tier upgrade whose null must cost the main paper nothing (programs/koopman-lifting/PLAN.md section 12.5).
