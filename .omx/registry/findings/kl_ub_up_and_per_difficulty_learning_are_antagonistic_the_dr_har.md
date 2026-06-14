---
title: "kl_ub up and per-difficulty learning are antagonistic; the dr_harder verdict is budget-conditional"
tags: ["kl_ub", "max_iterations", "doraemon", "curriculum", "attitude", "dr-harder", "budget-conditional", "untested", "trade-off"]
created: 2026-06-14T04:16:59.583923
updated: 2026-06-14T04:16:59.583923
sources: []
links: ["dr_harder_campaign_synthesis_speed_kills_attitude_center_shift_o.md", "kl_ub_0_12_trades_attitude_for_translation_e1_dr_harder.md", "our_doraemon_original_both_entropy_max_center_can_move_kl_ub_is_.md", "doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step_.md"]
category: decision
confidence: high
schemaVersion: 1
---

# kl_ub up and per-difficulty learning are antagonistic; the dr_harder verdict is budget-conditional

# kl_ub up and per-difficulty learning are antagonistic; the dr_harder verdict is budget-conditional

Sharpens the dr_harder synthesis after a user challenge (2026-06-14): "isn't kl_ub-up wrecking attitude just because the REACHED difficulty went up? and can't I fix it by also raising update-step / max_iter so each difficulty level gets enough learning?"

TWO points, kept distinct -- one CONFIRMED, one a NAMED GAP.

## 1. CONFIRMED (already in wiki, restated for the challenge): difficulty is NOT the cause; SPEED is.
The user's "it's just higher difficulty" intuition is reasonable but FALSIFIED by the E1-vs-E2 orthogonal factorial. E1 (kl_ub 0.06->0.12) and E2 (ocean nominal 0.0->0.3) reach the SAME final ocean coverage (mean 0.421 vs 0.409) yet OPPOSITE attitude outcomes (E1 roll/pitch hard +34/+69% WORSE; E2 +8/-17%, attitude KEPT). Same reached difficulty, opposite attitude => the attitude-killer is the EXPANSION SPEED (kl_ub), not the reached difficulty. See [[dr_harder_campaign_synthesis_speed_kills_attitude_center_shift_o]] and [[kl_ub_0_12_trades_attitude_for_translation_e1_dr_harder]]. The deterministic E4 control made this causal, not seed.

## 2. NEW MECHANISM (the part NOT previously pinned): kl_ub-up and "learn each difficulty more" are ANTAGONISTIC, not composable.
All dr_harder runs were LOCKED at max_iterations=5000, num_steps_per_env=64 (DESIGN.md sec 0, user lock; verified in E1 config/agent.yaml). So E1 = "expand 2x faster on the SAME total budget" => fewer gradient steps spent per unit of difficulty. That is the actual reason "the actor can't keep up -> entropy collapse" (existing pages note the symptom; this names the cause).

Consequence for the user's proposal: raising kl_ub to "increase the per-step difficulty jump" pulls AGAINST "let each difficulty be learned more". They are opposite directions on a fixed budget -- kl_ub-up makes each expansion a BIGGER jump within the same (unchanged) dwell window, so the policy is under-trained relative to the harder distribution. So the user's own second alternative ("leave kl_ub and update-step, raise max_iter only") is the mechanistically COHERENT one: keep the slow trust region (high dwell-time per level) and just buy more total climb. kl_ub-up + max_iter-up partially cancel.

REFINEMENT (2026-06-14, code-verified): dwell-time is actually owned by a SEPARATE cfg field `step_interval` (RL iters between DORAEMON updates, default 250), NOT by kl_ub. kl_ub = step SIZE, step_interval = dwell-TIME, max_iterations / step_interval = number of expansions. Full 3-lever breakdown with code lines: [[doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step_.md]]. The antagonism conclusion here stands; the precise mechanism is "bigger jump per fixed dwell", not "shorter dwell".

## 3. The dr_harder "don't raise kl_ub" verdict is BUDGET-CONDITIONAL, not absolute.
The campaign's recommendation against kl_ub-up holds ONLY under the fixed 5000-iter lock. The campaign NEVER tested kl_ub-up compensated by a larger iteration budget. This exact gap is already noted as design option (c) "MORE iterations at baseline kl_ub ... (the user's E1-discussion hypothesis -- UNTESTED)" in [[our_doraemon_original_both_entropy_max_center_can_move_kl_ub_is_.md]], which also has raw-TB proof that ocean mean is still MONOTONICALLY CLIMBING (not plateaued) at iter 5000 -- so "more time reaches farther" is mechanistically plausible, just unmeasured.

## NET (for the next experiment design)
- Do NOT read the dr_harder pages as "kl_ub is forbidden". Read them as "on a FIXED 5000-iter budget, kl_ub-up buys reach by spending attitude".
- The untested cell is: raise the difficulty target (performance_lb, or DORAEMON variance from nominal=0) and/or extend max_iter, while keeping kl_ub LOW so per-difficulty dwell-time stays high. That combination was never run.
- attitude_only baseline v2 (lb=250, kl_ub=0.12) is the post-campaign settling point; whether its kl_ub=0.12 carries the E1 attitude penalty or is rescued by lb/other conditions is itself worth checking against E1 directly (NOT yet done).

VERIFIED: E1 config/agent.yaml (max_iterations 5000, num_steps_per_env 64, kl_ub 0.12, performance_lb 90.0); DESIGN.md sec 0 budget lock; README.md sec "Run list"/"core results"; cross-checked against existing pages cited above. Source challenge: user, 2026-06-14.

