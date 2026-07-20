---
title: "extend8k (8000-iter) confirms e3: extending past 5000 iters is net-negative on the FIXED-DR exam, an axis trade, and confounded by DR-width expansion"
tags: ["e3", "curriculum-budget", "max-iterations", "doraemon", "transient-trade", "axis-decorrelation", "budget-confound"]
created: 2026-07-20T03:14:17.892347
updated: 2026-07-20T03:14:17.892347
sources: ["diagnose-20260720-115818"]
links: ["e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite.md", "e3_extend10k_regressed_the_policy_training_budget_is_not_the_p7.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# extend8k (8000-iter) confirms e3: extending past 5000 iters is net-negative on the FIXED-DR exam, an axis trade, and confounded by DR-width expansion

A fresh from-scratch 8000-iter run of the adopted biasema config (trpo_biasema_extend8k_260716_162849) vs its 5000-iter sibling (trpo_biasema_260715_142543), graded on the SAME fixed none/soft/medium/hard exam (both plain static, neither --doraemon-dr-from), gives the e3 budget question real single-config data. See [[e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite]] and [[e3_extend10k_regressed_the_policy_training_budget_is_not_the_p7_]].

CONCLUSION: extending 5000->8000 delivered NO net win. On the clean fixed-DR exam it is an AXIS TRADE: roll steady-state ss_error improved at all levels (none 0.215->0.171 -21%, soft -25%, medium -16%, hard -11%) but pitch regressed at all levels (+34% to +52%) and yaw regressed (+30% to +109%, tiny absolute). The load-bearing regression is roll TRANSIENT overshoot at low DR: roll n_gt20 (mean env count with peak>20deg) none 4.3->61.3 (14x), soft 7->45.3 -- floor down, spike up, the same signature as e2 (trpo_e2_biasobs_260713_173456). Survival saturated 100% both runs (non-discriminating). EVIDENCE: eval static_260717_005643 (8k) vs static_260715_192701 (5000) summary.json; analysis diagnose-20260720-115818 generalization section.

CONFOUND (why this is not a clean budget test): max_iterations drives DORAEMON's expansion clock (step_interval=250, config.py:544), so 5000->8000 = +12 curriculum expansions. The treatment was WIDER DR, not more compute: DORAEMON/entropy_before -22.70->-18.20, DR ocean_current 0.06->0.22 (3.7x, engine TIER3). success_rate 0.88->0.79 reflects the harder (wider) exam, NOT policy regression (ess_ratio 0.76->1.00 = curriculum comfortable). Training-side, reward plateaued at iter ~400 (~5%, engine [TREND]) and final Train/mean_reward is LOWER (272.46->265.36, -2.6%) -- the extra 3000 iters bought DR width, not objective gain. Consistent with the user's DGX-scale-up caveat that budget alone is not the lever; the config ceiling / plant fidelity is. Comparator-selection rule: for a cross-run budget comparison use the fixed-level self-exam, NOT the --doraemon-dr-from shared exam (the 5000-run's static_260716_160156 grades on another run's learned DR and is not comparable).
