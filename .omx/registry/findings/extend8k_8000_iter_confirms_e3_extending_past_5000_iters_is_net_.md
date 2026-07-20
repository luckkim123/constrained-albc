---
title: "extend8k (8000-iter) confirms e3: extending past 5000 iters is net-negative on the FIXED-DR exam, an axis trade, and confounded by DR-width expansion"
tags: ["e3", "curriculum-budget", "max-iterations", "doraemon", "transient-trade", "axis-decorrelation", "budget-confound", "metric-semantics", "overshoot", "correction", "exam-comparability", "doraemon-dr"]
created: 2026-07-20T03:14:17.892347
updated: 2026-07-20T03:32:10.505687
sources: ["diagnose-20260720-115818", "diagnose-20260720-122425", "diagnose-20260720-123142"]
links: ["e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite.md", "e3_extend10k_regressed_the_policy_training_budget_is_not_the_p7.md", "engine_gap_heavy_tail_json_pct_peak_gt_thresh_exceeds_100_at_ood.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
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

---

## Update (2026-07-20T03:25:22.063639)

METRIC-SEMANTICS CORRECTION (2026-07-20, analysis diagnose-20260720-122425 supersedes diagnose-20260720-115818): the earlier wording of this page described n_gt20 as 'mean env count with roll peak > 20 DEG'. That is WRONG. Verified in code (constrained_albc/analysis/_analyze/recompute_metrics.py:112-122): os_signed = sign*(peak_env - cur_tgt)/step_mag*100 is per-env OVERSHOOT as a PERCENT of the target step magnitude, and n_gt20 = int(np.sum(os_clip > 20.0)) counts envs whose OVERSHOOT exceeds 20 PERCENT -- not a 20-degree peak. The decimal value comes from averaging the per-target-step integer count over the eval's target steps.

THE FINDING ITSELF IS UNCHANGED AND NOW BETTER EVIDENCED. The cleaner primary metric is os_env_mean (overshoot %), which shows the regression directly at every DR level: roll os_env_mean 5000->8k none 17.02->26.99 (+59%), soft 16.08->23.65 (+47%), medium 15.24->20.83 (+37%), hard 15.41->19.92 (+29%); os_env_q90 none 18.80->28.79, hard 25.89->33.03. The n_gt20 14x jump (4.3->61.3 at none) is the SAME distribution seen through the 20%-overshoot threshold -- confirmation, not independent evidence. Corroborating shape: the eval Overshoot panel puts extend8k roll at ~27% at none, above the 20% reference line.

REUSABLE LESSON: n_gt20 / n_gt40 / n_us_lt_minus20 are OVERSHOOT-PERCENT threshold counts, NOT angle thresholds. Do not read the '20' as degrees in any future report. Related: [[engine_gap_heavy_tail_json_pct_peak_gt_thresh_exceeds_100_at_ood]] (a different, already resolved-by-refactor bug in the percent field).

---

## Update (2026-07-20T03:32:10.505687)

EXAM-COMPARABILITY CORRECTION (2026-07-20, analysis diagnose-20260720-123142 supersedes diagnose-20260720-122425/115818). The earlier wording claimed both runs were 'graded on the SAME fixed none/soft/medium/hard exam because neither used --doraemon-dr-from'. That is WRONG. eval.py static defaults --doraemon-dr to True (eval.py:118 BooleanOptionalAction; eval.py:1131-1135 -> load_doraemon_dr(run_dir); dr_config.py:206 'hard range = learned mean +/- 2*std'), so EACH run was graded on ITS OWN final learned DORAEMON distribution. Not passing --doraemon-dr-from only means no THIRD run's DR was used; it does NOT make the exam common. Per [[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]], only the none level (fixed nominal physics) is a fair cross-run comparison; soft/medium/hard are run-relative.

WHAT SURVIVES (all of the verdict): every headline number sits on the FAIR none level -- roll ss_error 0.215->0.171 (-21%), pitch 0.195->0.296 (+52%), roll os_env_mean 17.02->26.99 (+59%), roll n_gt20 4.3->61.3. The axis trade and the transient-overshoot regression are therefore established on identical nominal physics and stand unchanged.

WHAT CHANGES: the soft/medium/hard rows are no longer evidence. The bias is one-sided and computable: extend8k's curriculum ended WIDER (entropy_before -18.20 vs -22.70), so it sat the HARDER exam there -- its roll improvement at those levels is UNDERSTATED and its pitch/yaw regression OVERSTATED. In particular the 'overshoot damage is monotone-largest at nominal (+59% none -> +29% hard)' gradient must NOT be cited as evidence that damage concentrates at nominal: the gradient is confounded by exam difficulty.

REUSABLE LESSON: 'both plain static / neither used --doraemon-dr-from' is NOT a comparability argument. To get a common exam you must pass --doraemon-dr-from <ref run> (shared exam) or --no-doraemon-dr (static DR cfg). Otherwise restrict cross-run claims to none.
