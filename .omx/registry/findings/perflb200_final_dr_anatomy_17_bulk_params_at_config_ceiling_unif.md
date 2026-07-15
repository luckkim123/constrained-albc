---
title: "perflb200 final DR anatomy: 17 bulk params at config ceiling (uniform), 3 deployment-relevant params (ocean_current/obs_noise/payload_cog) are TIME-limited not feasibility-limited"
tags: ["doraemon", "dr-difficulty", "perflb200", "deployment-ood", "curriculum-budget"]
created: 2026-07-15T05:54:12.790886
updated: 2026-07-15T05:54:12.790886
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
---

# perflb200 final DR anatomy: 17 bulk params at config ceiling (uniform), 3 deployment-relevant params (ocean_current/obs_noise/payload_cog) are TIME-limited not feasibility-limited

# Context

User question (2026-07-15): is perflb200's final DR hard enough, or did it stop too easy
(deployment-OOD risk)? User's read: "success rose to ~0.9 then declining = normal? difficulty
seems EASIER than baseline; increasing iters or kl_ub would make it just right." This finding
reconciles that read against code-exec evidence and prior wiki
(`doraemon_alpha_is_a_feasibility_floor...`, `doraemon_over_widens_then_oscillates...`,
`kl_ub_up_and_per_difficulty_learning_are_antagonistic...`).

[FINDING] The success 0.97->0.71 decline is the DESIGNED alpha closed-loop equilibrium
(DORAEMON expanding DR), NOT degradation — user's "normal pattern?" read is CORRECT.
[EVIDENCE: TB DORAEMON/success_rate perflb200 = peak 0.968@it1235 -> monotone decline -> 0.706@it4999;
prior page doraemon_alpha_is_a_feasibility_floor confirms this shape IS the alpha=0.5 equilibrium]
[CONFIDENCE: HIGH]

[FINDING] Difficulty is INVERTED vs the user's read: perflb200 DR is WIDER/HARDER than baseline,
not easier. success_rate is lb-relative (fraction of rollouts >= performance_lb on the CURRENT DR),
so it is NOT a cross-run difficulty measure — the higher perflb success (0.71 vs 0.40) comes from the
lower bar (200 vs 250) AND a wider DR, not an easier task.
[EVIDENCE: doraemon_state.pt Beta(dist_a,dist_b): perflb 17/20 params ~= (1.6,1.6) = near-uniform =
full config range; baseline ~= (3-5) center-peaked = CONTRACTED (re-stall pulled DR inward). Reached
xi ranges: perflb added_mass [0.503,1.498] full vs baseline [0.559,1.489]; perflb inertia [0.404,1.996]
full vs baseline [0.508,1.970]]
[CONFIDENCE: HIGH]

[FINDING] perflb200 final-DR anatomy splits in two: 17 bulk params are at the config CEILING (uniform,
flat), while the 3 deployment-relevant params (ocean_current_strength, obs_noise_scale,
payload_cog_offset_xy_u) are TIME-limited not feasibility-limited — still climbing fast at run end,
only 16-18% expanded.
[EVIDENCE: TB DORAEMON/mean, last-1k slope]
- ocean_current_strength: mean end 0.162, slope +0.081/1k (accelerating)
- obs_noise_scale:        mean end 0.157, slope +0.080/1k (accelerating)
- payload_cog_offset_xy_u: mean end 0.182, slope +0.088/1k (accelerating)
- added_mass_scale (bulk): mean 0.999, slope +0.0008/1k (flat, at ceiling)
- inertia_scale (bulk):    mean 1.206, slope -0.0037/1k (flat, at center)
[CONFIDENCE: HIGH]

[FINDING] Lever assessment for closing the residual deployment gap (the 3 climbing params):
more-iters is the PRIMARY, safest lever; kl_ub is documented-antagonistic; neither helps the 17
ceiling'd params (only P-A6 config-bound widening does). Success ended 0.71 >> alpha 0.5 with the 3
params feasibly climbing => headroom exists before the over-widen regime, so a MODERATE iter extension
should continue healthy expansion.
[EVIDENCE: 3 params climbing feasibly (success 0.71 > alpha, positive slope) = time-limited;
prior page doraemon_over_widens_then_oscillates = converged teacher + EXTRA budget over-widened ->
oscillated -> contracted -> success 0.368 < alpha @10k (documented backfire if pushed too far);
prior page kl_ub_up_and_per_difficulty_learning_are_antagonistic = raising kl_ub speeds expansion but
degrades per-difficulty learning; our_doraemon...kl_ub_is_the_speed_bottleneck = kl_ub is step-SIZE]
[CONFIDENCE: HIGH]

# Decision / next experiment (lead)

DECISION: performance_lb=200 CONFIRMED as standing setting (user affirmed; my earlier "no need to
adjust" was wrong). The residual deployment-OOD gap is concentrated in exactly 3 params
(ocean current / sensor noise / payload CoG-xy) that are TIME-limited, so:

- PRIMARY lever = perflb200 more-iters continuation (single variable: max_iterations 5000 -> ~8-10k),
  targeting the 3 climbing params toward deployment-realistic difficulty. GUARD with the over-widen
  abort signature (success crosses below alpha 0.5 and stays, DR mean reverses/contracts) from
  `doraemon_over_widens...`. Ideally recalibrate lb to a measured corrected-plant p25 first (P-A2).
- kl_ub bump = faster but antagonistic to per-difficulty learning (riskier); prefer more small steps
  (iters) over bigger steps (kl_ub) for the same expansion.
- The 17 ceiling'd params need P-A6 (physical-span review + widen config HardDR bounds), NOT iters/kl_ub,
  and only if measured hardware variation exceeds the current config bounds.

Discriminator for the more-iters probe: do the 3 param means reach ~ceiling AND does the fair-'none'
tracking floor improve or degrade? If they climb and the floor holds/improves => adopt the extended
budget; if success crosses below alpha and DR contracts => over-widen regime, revert (budget-conditional
per kl_ub_up...budget_conditional).

