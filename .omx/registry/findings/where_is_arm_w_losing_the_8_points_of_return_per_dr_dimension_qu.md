---
title: "Where is Arm W losing the 8 points of return: per-DR-dimension quintile decomposition (M3)"
tags: ["doraemon", "curriculum", "feasibility", "diagnosis"]
created: 2026-08-10T02:35:14.326657
updated: 2026-08-10T02:35:14.326657
sources: ["arXiv:2311.01885"]
links: []
category: debugging
confidence: medium
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: needs-experiment
---

# Where is Arm W losing the 8 points of return: per-DR-dimension quintile decomposition (M3)

OPEN LEAD, opened 2026-08-10 after M2 eliminated exploration as the cause of Arm W's failure.

The question. Arm W (trpo_rampw_kl006_s30_260809_161913) ended with Train/mean_reward 241.69 against performance_lb 250.0 and 0/21 curriculum dims saturated, while the reference run held 258.56 and locked 21/21. Both reached the same maximum DR width on ocean_current_strength (0.2887) and carried statistically identical action noise (see exploration_is_not_coupled_to_curriculum_width_dr_grew_10_29x_wh). So the deficit is in the return itself. The open question is WHERE the return is lost: is it spread evenly across the randomization box, or is one dimension's upper range physically infeasible and dragging the mean under the floor?

The test. Bucket episodes by the DR value actually sampled for each env into quintiles, per dimension, and read mean episode return per bucket. Existing rollout logs; no training run required. The 21 declared dims are the candidates, with ocean_current_strength, payload_cog_offset_xy_u, water_density and fault_severity the priors (largest measured widening, 10-29x over it 5000-18205).

Decision rule, fixed before looking:
- If one or two dimensions show their top quintile far below the rest (order of 200 versus 250+) while the remaining buckets sit above the floor, the bottleneck is a specific infeasible range and the fix is a ceiling cap on that dimension, NOT more iterations, NOT exploration, NOT a lower performance_lb.
- If the return deficit is spread roughly evenly across every dimension's quintiles, the specific-dimension hypothesis is rejected and the remaining candidate is a global plant or reward-scale issue.

Why this is the right next probe. It is the same diagnosis the DORAEMON authors reached on their own failing environments: they attribute Walker2D and Swimmer degradation to "the agent's exposure to harder/infeasible parameters, which destabilize training" (arXiv:2311.01885). Their remedy was to track the best-performing checkpoint rather than to change exploration - which is also what the selection pass now running does for us.

Related decision already on the table: D5, the T200 command-to-thrust bench plus XW540-T260 step response, is the only path that would RAISE the DR ceiling rather than cap it. If M3 identifies an infeasible thruster-side range, D5 becomes the follow-on rather than an independent item.

Not yet started. Blocked on nothing - the workstation is busy with the Arm W selection pass and the 2-way finalist until roughly 13:20 KST on 2026-08-10, and the DGX is running Arm D, but M3 itself needs no GPU beyond reading logged rollouts.

