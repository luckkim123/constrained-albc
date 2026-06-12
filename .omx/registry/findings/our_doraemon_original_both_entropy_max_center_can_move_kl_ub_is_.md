---
title: "Our DORAEMON == original (both entropy-max); center CAN move, kl_ub is the speed bottleneck"
tags: ["doraemon", "nominal", "center", "entropy_max", "kl_ub", "target_uniform", "dr-harder", "design", "correction"]
created: 2026-06-07T08:53:11.935492
updated: 2026-06-07T08:53:11.935492
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# Our DORAEMON == original (both entropy-max); center CAN move, kl_ub is the speed bottleneck

# Our DORAEMON == original (both entropy-max); center CAN move, kl_ub is the speed bottleneck

CORRECTS an earlier wrong page ("our DORAEMON cannot move the center / original uses min-KL-to-target and we stripped it"). That was a misread. The truth:

ORIGINAL DORAEMON (gabrieletiboni/doraemon, references/doraemon) objective = `min KL(phi_proposed || phi_target)` (doraemon.py:809-822) where `target_distr` is ALWAYS the UNIFORM distribution (lsdr.py:701 docstring "target uniform distribution"; doraemon.py:591 logs "Maximum entropy achievable: target_distr.entropy()"; line 644 "test on max entropy distribution"). Because uniform IS the max-entropy distribution, `min KL(phi||uniform)` is MATHEMATICALLY EQUIVALENT to maximizing entropy. The paper title is literally "Domain Randomization via Entropy Maximization" (ICLR 2024).

OUR DORAEMON (marinelab/marinelab/algorithms/doraemon.py) objective = `max entropy s.t. success>=alpha, KL<=kl_ub` (`_optimize_entropy`, doraemon.py:595-602). This is the SAME thing expressed directly as entropy-max instead of KL-to-uniform. We did NOT strip a mechanism; we used the equivalent direct form. doraemon.py docstring line 6 confirms: "DORAEMON: Domain Randomization with Entropy Maximization (ICLR 2024)".

CENTER CAN MOVE -- in both. Both optimize a AND b freely (original beta_from_stacked; ours get/set_flat_params [a0,b0,a1,b1,...], doraemon.py:184-194). Maximizing entropy drives Beta(a,b) toward a~=b, i.e. toward the uniform CENTER 0.5, so mu shifts as a side effect of widening. There is NO constraint pinning mu to nominal beyond initialization (nominal only sets the START point, doraemon.py:131).

So why did teacher's ocean_current_strength only reach mean 0.118 from nominal 0.0? NOT because the center can't move -- because moving it is SLOW under the per-step trust region kl_ub=0.06 and the 5000-iter budget. Raw TB proof (2026-06-07): ocean mean is MONOTONICALLY CLIMBING and still accelerating at the end, never plateaued:
- teacher (kl_ub 0.06, nom 0.0): 0.010 -> 0.030 -> 0.058 -> 0.118 (still rising at iter 5000).
- E1 (kl_ub 0.12, nom 0.0): 0.010 -> 0.048 -> 0.130 -> 0.421 -- 2x trust region => center moved 3.6x FARTHER from the same start. kl_ub IS the center-shift SPEED lever.
- E2 (kl_ub 0.06, nom 0.3): 0.300 -> 0.327 -> 0.357 -> 0.409 -- a START-POINT jump, reaching ~same endpoint as E1 (0.41) but with healthy ess (0.886 vs E1 0.769).

E1 and E2 are NOT "two faces of a missing capability". They are two ways to reach the same ~0.41 ocean coverage in 5000 iters: E1 widens faster (actor can't keep up -> entropy collapse + ess drop), E2 jumps the start (ess stays healthy but actor overfits the shifted-low band). Both still end in the EASY half ([0,1], uniform center 0.5) because 5000 iters at these settings isn't enough to reach 0.5; 15/16 non-ocean params likewise end width-only at their easy nominal because they were never given a harder start nor extra time.

DESIGN IMPLICATION: there is NO engine bug to fix and NOTHING to "restore". To get strong-current coverage the levers are: (a) raise kl_ub (faster center shift, but E1 shows the actor breaks), (b) shift nominal start (E2, but overfits), (c) MORE iterations at baseline kl_ub so the same monotone climb reaches further (the user's E1-discussion hypothesis -- untested), or (d) some combination, separated to avoid confounds. Code modification, if any, belongs to whichever next experiment tests these -- not a standalone fix.

VERIFIED: code read 2026-06-07 (ours doraemon.py:6/131/184-194/595-602; original doraemon.py:419/591/644/809-822, lsdr.py:701); raw TB ocean-mean trajectories above. Related: ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder, kl_ub_0_12_trades_attitude_for_translation_e1_dr_harder, dr_harder_campaign_synthesis_speed_kills_attitude_center_shift_o.

