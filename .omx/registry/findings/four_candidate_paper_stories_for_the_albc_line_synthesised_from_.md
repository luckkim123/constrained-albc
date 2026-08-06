---
title: "Four candidate paper stories for the ALBC line, synthesised from 55 substantive wiki decisions 2026-08-05"
tags: ["koopman", "paper-planning", "paper-story", "linearity-constraint", "distillation-proxy", "negative-control", "phase2-verdict"]
created: 2026-08-05T09:35:50.294553
updated: 2026-08-06T08:57:26.632388
sources: ["experiments/rsl_rl/albc_trpo_teacher/koopman_linearity/README.md", ".omx/programs/koopman-lifting/PLAN.md"]
links: []
category: reference
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Four candidate paper stories for the ALBC line, synthesised from 55 substantive wiki decisions 2026-08-05

Context: the owner wants a paper (not submitted anywhere yet; the IROS 2026 attempt was never submitted and its notes at references/iros_2026/ are stale from January, superseded by the TAM fix, buoyfix, the teacher campaign, obs4 and student distillation). The wiki holds 69 decision pages; removing 14 engine-gap tooling entries leaves 55 substantive results. The backlog is empty (both needs-experiment and needs-apply-before-retrain return zero rows), so the experimental program is at a natural stopping point. These 55 results cluster into four coherent stories.

STORY A - OBSERVABILITY. Claim: what the policy can observe, chosen for real-sensor deployability, was the dominant lever, not the algorithm. Evidence: two independent interventions moving the same way - bias_ema (69 -> 72D) cut steady-state roll error 68 percent and pitch 29 percent at the DR-fair none point and additionally cleared a DORAEMON feasibility stall; obs4 (72 -> 76D) passed H1 with margin and bought hard-DR tail and spread. Both are computable from real sensors. Negative controls available: arm B (a nonlinear basis of ALREADY-observed signals) hurt, and privileged fault obs was not adopted. Message sharpens to: NEW information helps, re-encoding existing signals or supplying non-deployable signals does not. Likely writable with zero additional runs. Koopman appears here only as the arm B negative control, and only under the corrected citation scope (see the arm_b_is_a_dictionary_only_control page).

STORY B - CURRICULUM MECHANICS. Claim: the knobs of an automatic DR curriculum do not do what their names say. Evidence: max_iterations is a DR-EXPANSION clock, not a training budget (5000 -> 8000 regressed, and the cause was wider DR not more optimisation); performance_lb sets the success-rate PEAK, so a reported DORAEMON success of 0.97 reflects a low bar rather than a good policy; DORAEMON alpha is a feasibility floor not an expansion lever; the HARDER curriculum generalised WORST out of distribution. Counter-intuitive and methodologically useful. Reviewer risk: is this DORAEMON-specific or general, which invites a second-platform reproduction demand. No Koopman content.

STORY C - DISTILLATION PROXY REBUTTAL. Claim: latent reconstruction fidelity is a poor proxy for closed-loop performance in privileged distillation. Evidence: X1 tail-split lifted hard aggregate latent R2 from -0.1044 to +0.0645 and moved no control metric - and crucially the reason is known, that delta is only a 6.69 percent RMSE cut so a sub-floor control change was PREDICTED (state it as a measured poor exchange rate, NOT as decoupling, which was retracted); lambda_latent swept over [0,4] with no decision-grade control effect and lambda=1 a measured local optimum; meanwhile GRU memory plus corrected DAgger mixing compounded so that C3 became the first student to beat its teacher by a decision floor, i.e. the gain came from somewhere other than reconstruction accuracy. Most novel scientifically, since privileged-distillation papers routinely report reconstruction error as the headline metric and nobody has priced the exchange rate. This is the ONE story where Koopman lives as a genuine comparison arm (does imposing linear latent dynamics change the picture).

STORY D - FAULT TOLERANCE. Claim: a UVMS with genuinely faulted thrusters can be held by fault-DR alone, without explicit fault detection. Evidence: fault-DR adopted with 5-12x less m4-dead degradation and zero terminations; counter-intuitively, RAISING trained fault severity made m4-dead rejection 2.9-5.5x WORSE while buying a 2.50x curriculum speedup; privileged fault obs was not adopted, so tolerating beats knowing. Strong motivation because the real vehicle has 2 of 6 thrusters faulted. Caveat a reviewer will raise: training exposure is independent Bernoulli per thruster at p=0.10, so the count is Binomial(6, 0.1) with no cap - exactly-2 faults, the real robot's condition, is only 9.8 percent of envs, and 3-or-more is 1.6 percent. The real operating point sits in the lower tail of the training distribution. Real-tank validation likely demanded. No Koopman content.

Bearing on the Koopman line: Koopman contributes one result (arm B NULL) against 55 already earned. If paper contribution is the goal, harvesting is higher-yield than opening a new axis; the reopened Koopman study is justified only as an OPTIONAL venue-tier upgrade whose null must cost the main paper nothing (programs/koopman-lifting/PLAN.md section 12.5).

---

## Update (2026-08-06T08:57:26.632388)

## UPDATE 2026-08-06 -- the Koopman line is CLOSED; the inventory line above is superseded

The bearing paragraph above ("Koopman contributes one result, arm B NULL, against 55 already
earned") was written 2026-08-05, before Phase 2 ran. The 5-arm roster is now COMPLETE and the line
carries a verdict. Authority: `.omx/programs/koopman-lifting/PLAN.md` section 12.10; result SSOT
`experiments/rsl_rl/albc_trpo_teacher/koopman_linearity/README.md` (figure `arms_comparison.png`).

VERDICT, pre-registered outcome 3. No arm beats the E-int baseline: worse in 58/72 measured cells
(arm C, learned lift + learned LINEAR operator), 57/72 (random frozen lift), 55/72 (nonlinear
twin), against 40/72 for arm B. But arm C and the twin SEPARATE decisively and the LINEAR arm is
the worse of the two -- C loses to the twin in 51/72 cells with 15 floor crossings, including
att_norm ss_error at soft/medium/hard (+0.233 / +0.410 / +0.554 deg against a 0.1 deg floor).
Gates: survival 100 percent for every arm at every DR level; pairing 96/96 vs baseline and 96/96
arm-to-arm. So on this plant the linear-evolution constraint DOES reach control, and it costs.
Same direction the offline study measured, where relaxing linearity improved multi-step prediction
in 10 of 10 configurations at 4.6-31.9 sigma.

Bearing on each story, revised:

- STORY A, B, D -- UNCHANGED. A still cites Koopman only as the arm B negative control, and only
  under the corrected scope (arm B fitted no operator). B and D still carry zero Koopman content.
  Three of the four stories give the Phase 2 study no space at all, so the harvesting argument in
  the paragraph above still holds and is now better supported: four arms bought one methods-grade
  negative.
- STORY C -- STRENGTHENED, and this is the only revision that changes anything. Phase 2 supplies a
  sharper form of C's own claim. C currently argues from X1: better latent accuracy moved no
  control metric, at a measured exchange rate of 6.69 percent RMSE. Phase 2 adds the converse.
  Arm C and the twin score 39.4 and 39.5 percent against the persistence null on the five channels
  the policy actually receives -- indistinguishable ACCURACY -- while their outputs correlate only
  0.60-0.99 per channel and their control differs in 51/72 cells. Same accuracy, different control.
  That is a stronger statement than "more accuracy buys nothing".
  Caveat that bounds it: Phase 2 is TEACHER-side on-policy RL with an auxiliary input channel, not
  STUDENT-side privileged distillation. The setting differs, so this is supporting evidence for a
  subsidiary paragraph, never headline evidence for C. Further bounds: n = 1 per arm, single seed,
  screening floors, no replicate on any arm.

Paper action per the pre-registered PLAN section 12.5 rule for outcome 3 is a methods subsection as
a controlled negative, never a primary contribution, and the main paper does not wait on it.

STATE OF THE PAPER DECISION ITSELF, checked 2026-08-06: STILL UNDECIDED. No story on this page has
been selected -- no decision page picks one, no `.oms/` paper project exists anywhere in the
workspace, and the only prior attempt, `references/iros_2026`, remains the stale January material
this page already described. Koopman inclusion is therefore a DOWNSTREAM question: pick the story
first and the answer follows from the per-story bearing above.

