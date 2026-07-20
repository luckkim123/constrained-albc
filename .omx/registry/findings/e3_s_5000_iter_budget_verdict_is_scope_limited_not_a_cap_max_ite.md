---
title: "e3's '5000-iter budget' verdict is scope-limited, NOT a cap: max_iterations is a DR-EXPANSION knob (step_interval clock) and the real ceiling is the Beta a=b=1 config bound, not compute"
tags: ["doraemon", "curriculum-budget", "max-iterations", "num-envs", "dgx", "scale-up", "e3", "config-ceiling", "p-a6", "user-decision", "extend8k", "result-recorded", "exam-comparability", "correction"]
created: 2026-07-16T05:58:47.795144
updated: 2026-07-20T03:32:10.598463
sources: ["diagnose-20260714-084409", "diagnose-20260720-115818", "diagnose-20260720-123142"]
links: ["performance_lb_recon_needs_zero_new_rollouts_doraemon_state_pt_a.md", "decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema.md", "extend8k_8000_iter_confirms_e3_extending_past_5000_iters_is_net_.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "REMAINING SCOPE ONLY: DGX scale-up (larger num_envs AND max_iterations). The same-plant 'does extending past 5000 help' half is ANSWERED (verdict rests on the fair none level) -- do not re-run that arm."
---

# e3's '5000-iter budget' verdict is scope-limited, NOT a cap: max_iterations is a DR-EXPANSION knob (step_interval clock) and the real ceiling is the Beta a=b=1 config bound, not compute

# USER DECISION (2026-07-16): no iteration cap; DGX scale-up is planned

The user rejects the `teacher_baseline_opt` campaign README's "budget 쟁점 종결 — 5000 iter 확정"
and intends to train on an NVIDIA DGX with much larger `max_iterations` AND `num_envs`. This page
records why the evidence never licensed a cap, and what actually bounds a scaled run.

# Why e3 does NOT license a budget cap

e3 (`trpo_e3_extend10k_260713_224822`) concluded "the campaign KEEPS the 5000-iter run budget /
extending is net-harmful". That verdict is sound FOR WHAT e3 RAN, and over-generalized as a standing
rule. Four scope limits, all from e3's own report:

[FINDING] e3 was never a clean single-variable budget probe: DORAEMON's clock is ITERATIONS, so
raising `max_iterations` mechanically raises the number of curriculum expansions
(`n_expansions = max_iterations / step_interval`, step_interval=250). Budget was the KNOB; the
TREATMENT was DR-width expansion. e3's own section 0 measures the result: its end-of-training DR is
4.7x wider on ocean_current_strength (0.055 -> 0.261), plus wider on every other curriculum param.
[EVIDENCE: doraemon.py:416 `if self._step_count % self.cfg.step_interval != 0: return` (gate);
doraemon.py:43 step_interval="RL iterations between DORAEMON updates"; envs/main/config.py:544
step_interval=250; e3 report diagnose-20260714-084409 section 0 DR-std table]
[CONFIDENCE: HIGH]

[FINDING] The campaign's comparability gate (README section 2) covers only the EVAL confound (each run
graded on its own learned DR, so only `none` is a fair exam). It does NOT cover the TRAINING confound:
e3's policy is the optimum of a DIFFERENT (much wider) training distribution, so even the "fair none"
comparison is not "same config, different budget" -- it is "different final DR distribution". A
nominal-physics regression is the expected robustness/nominal trade of a wider training distribution.
[EVIDENCE: e3 report section 0 (DR 4.7x wider) vs README section 2 (handles eval confound only)]
[CONFIDENCE: HIGH]

[FINDING] Every subsystem that long training could plausibly break stayed healthy through iter 14998 --
the ONLY failure was the curriculum. So e3 is evidence about DORAEMON, not about training length.
[EVIDENCE: e3 report section 5 TRPO line_search 1.00 / KL on target; section 6 critic value 1.07,
cost_val 0.89 converged; section 7 encoder z_std 0.37, softsign full range, non-collapsed; section 8
all 10 IPO constraints satisfied; section 9 DORAEMON success 0.368 < alpha=0.5, oscillated then
contracted = the sole pathology]
[CONFIDENCE: HIGH]

[FINDING] e3's starting condition was adversarial-by-construction and its budget was double the design:
it RESUMED an already-converged teacher whose DORAEMON was already sitting at the alpha=0.5 floor
(zero headroom), and a `--max_iterations 10000` under `--resume` is relative-not-absolute, so it ran
+10000 (iter 4999 -> 14998) instead of the designed +5000.
[EVIDENCE: e3 report line 5 "BUDGET DEVIATION (disclosed)"; probe design = resume baseline model_4999.pt]
[CONFIDENCE: HIGH]

CORRECT SCOPE OF e3: "giving MORE budget to an already-converged teacher that is ALREADY at the alpha
floor causes DORAEMON to over-widen, oscillate, and regress the policy." NOT "do not exceed 5000 iters."

# SUPERSEDED: more-iters is the sanctioned primary lever, and the probe already ran

[FINDING] `perflb200_final_dr_anatomy...` (2026-07-15, one day AFTER the campaign README) reverses the
practical guidance: more-iters is the PRIMARY, safest lever (max_iterations 5000 -> ~8-10k), because
success ended 0.71 >> alpha 0.5 with 3 params still feasibly climbing = headroom exists BEFORE the
over-widen regime. The e3 backfire is reconciled, not contradicted: e3 had no headroom, perflb200 does.
[EVIDENCE: wiki perflb200_final_dr_anatomy_17_bulk_params_at_config_ceiling_unif "Lever assessment":
"more-iters is the PRIMARY, safest lever"]
[CONFIDENCE: HIGH]

[FINDING] The more-iters probe HAS ALREADY RUN and did not backfire:
`teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227` (8000 iters) ended at success 0.4955
= the DESIGNED alpha=0.5 equilibrium, NOT e3's sub-alpha over-widen (0.368 then contract).
[EVIDENCE: wiki performance_lb_recon_needs_zero_new_rollouts... measured table, n=2000 buffer_returns
per run: perflb200-moreiters(8000it) p25 134.8 / median 199.2 / lb 200 / success 0.4955]
[CONFIDENCE: HIGH]

# What actually bounds a DGX scale-up (it is NOT the budget)

[FINDING] The real ceiling is the CONFIG BOUND, not compute. DR width is capped by the Beta
concentration clamp `a,b in [1.0, 500.0]`; `a=b=1.0` = uniform = the full configured physical range,
and the per-param physical span (`min_bound`/`max_bound` in `_PARAM_DEFS`) is what the unit-interval
Beta draw maps onto. perflb200 already has 17 of 20 params AT that ceiling. Those 17 cannot be widened
by ANY number of iterations -- only P-A6 (config HardDR bound widening) moves them. Compute buys only
the 3 remaining TIME-limited params (ocean_current_strength, obs_noise_scale, payload_cog_offset_xy_u),
which were still climbing at ~+0.08/1k and only 16-18% expanded at run end.
[EVIDENCE: doraemon.py:86-87 _MIN_BETA_PARAM=1.0/_MAX_BETA_PARAM=500.0, clipped at set_flat_params
:189-193 and SLSQP results :646,:725; BetaDistribution.sample :147-159 maps into [min_bound,max_bound];
wiki perflb200_final_dr_anatomy: 17 bulk params near-uniform (1.6,1.6) at config ceiling, 3 params
TIME-limited with positive last-1k slope]
[CONFIDENCE: HIGH]

[FINDING] `num_envs` is CURRICULUM-NEUTRAL and untested at scale: `step_interval` (an iteration
counter) and `kl_ub` (per-update KL trust region) are both independent of `num_envs`, so raising
num_envs changes neither curriculum cadence nor expansion step size. Its real effect is on the
EpisodeBuffer: the 2000-slot ring fills and turns over faster, so the IS estimate is drawn from
fresher episodes (closer to prev_dist = favourable for IS validity), and the `min_episodes=200`
first-update gate stops being a meaningful floor. No run has ever tested a large num_envs, so this
is reasoned from code, not measured.
[EVIDENCE: doraemon.py:416 step_count is an iteration counter incremented per step() call regardless
of num_envs; doraemon.py:44 buffer_size=2000, :399-404 min_episodes=200 early-return;
albc_env.py:1425-1442 record_episodes batches whatever envs terminated; _estimate_success_rate
doraemon.py:486-504 uses the whole buffer]
[CONFIDENCE: MED]

[FINDING] There is NO abort/guard for a prolonged sub-alpha regime -- a scaled DGX run needs an
EXTERNAL monitor. The engine only reacts automatically (contract via the inverted problem, mode=-2
keep-narrower, mode=-3 revert-to-prev, or an ESS-based revert) and emits nothing louder than a
logger.warning. This has already burned one full run: e1 stayed pinned at mode=-2 with success 0.09
vs alpha 0.5 for the ENTIRE run, silently, and needed a human config fix to un-stall.
[EVIDENCE: no abort/early_stop/raise on success<alpha in doraemon.py/albc_env.py/runner;
doraemon.py:430-467 reactive branches only (mode -2 :444-445, mode -3 :446-449, ESS revert :462-467);
wiki the_curriculum_stalled_in_the_infeasible_branch_for_the_entire_r (e1 trpo_e1_latdr_260713_124923)]
[CONFIDENCE: HIGH]

# Decision / next experiment (lead)

DECISION: the "5000-iter cap" is RETIRED as a standing rule (user, 2026-07-16). Treat
`max_iterations` as a DR-EXPANSION knob, not a training-length knob -- the question is never "how long
to train" but "does headroom exist above alpha at the current lb".

Launch conditions for the DGX scale-up:
- GO signal = success_rate comfortably above alpha at the current `performance_lb` with the
  deployment-relevant params still climbing (the perflb200 signature), NOT the e3 signature
  (already-at-floor, converged).
- ABORT signature (from `doraemon_over_widens...`): success crosses below alpha 0.5 and STAYS, DR mean
  reverses/contracts. Since no in-code guard exists, arm a wandb alert on `DORAEMON/success_rate` and
  `DORAEMON/mode` BEFORE launching a long run.
- Expect compute to buy only the 3 TIME-limited params. If the goal is the 17 ceiling'd ones, the
  lever is P-A6 config-bound widening and NO amount of DGX time substitutes for it.
- `num_envs` scale-up is curriculum-neutral by code reading but has never been measured; if it is
  raised at the same time as max_iterations, the run is a 2-variable change and its DR outcome will
  not be attributable. Prefer raising them in separate runs if the DR anatomy is what is being judged.
- Recalibrate `performance_lb` to the corrected-plant p25 FIRST (P-A2) -- lb sets where the alpha
  equilibrium lands, and it is free (see
  [[performance_lb_recon_needs_zero_new_rollouts_doraemon_state_pt_a]]).

---

## Update (2026-07-20T03:15:55.292239)

## Audit re-scope (2026-07-20, backlog audit)

The RETROSPECTIVE half of this page is settled: the "5000-iter cap" is retired, and the validating probe
it names (`trpo_perflb200-moreiters_260715_195227`, 8000 iters, success 0.4955 = the designed alpha
equilibrium) has run without backfire. A second 8k run has since happened as well
(`trpo_biasema_extend8k_260716_162849`).

Its listed PREREQUISITE is also satisfied: P-A2 (performance_lb recalibration) resolved on 2026-07-16 --
p25 computed from the `doraemon_state.pt` buffer with zero new rollouts, verdict "keep lb=250"
([[decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema]], `config.py:544`). Caveat: the
proper no-DR App A.1 measurement remains never-done.

REMAINING SCOPE -- this page stays open ONLY for the forward-looking ask: launch the DGX scale-up under
the stated GO/ABORT conditions. Verified not done: no DGX-scale run exists anywhere in the experiments
tree (largest is 8000 iters at standard `num_envs`), and P-A6 (HardDR config-bound widening) has no run
at all. Keep the two variables separate -- raising `num_envs` and `max_iterations` in one run makes the
DR outcome unattributable.

---

## Update (2026-07-20T03:19:56.704000)

RESULT RECORDED 2026-07-20 (extend8k, analysis diagnose-20260720-115818): the same-plant half of this lead is ANSWERED. A fresh from-scratch 8000-iter run (trpo_biasema_extend8k_260716_162849) vs its 5000-iter sibling (trpo_biasema_260715_142543), both graded on the SAME fixed none/soft/medium/hard exam, shows extending is NET-NEGATIVE: an axis trade, not an improvement. roll ss_error improved at all levels (-11% to -25%) but pitch regressed +34% to +52%, yaw +30% to +109%, and roll transient overshoot blew up 14x at low DR (n_gt20 none 4.3->61.3). Reward plateaued at iter ~400 and final Train/mean_reward FELL 272.46->265.36 (-2.6%).

This page's core claim is CONFIRMED, not refuted: max_iterations really is a DR-expansion knob, and extend8k measured the expansion directly -- +12 curriculum expansions (3000 extra iters / step_interval=250, config.py:544), DORAEMON/entropy_before -22.70->-18.20, DR ocean_current 0.06->0.22 (3.7x). The success_rate drop 0.88->0.79 is the wider exam, not policy regression (ess_ratio 0.76->1.00). So 'extending' on this plant buys DR width at the cost of the objective.

WHAT REMAINS OPEN (the only reason this stays needs-experiment): the DGX scale-up arm -- larger num_envs AND max_iterations together on different hardware. extend8k varied ONLY iterations at fixed num_envs, so it says nothing about whether more PARALLEL samples per expansion changes the trade. Do NOT re-run the same-plant iteration-only arm. Full detail: [[extend8k_8000_iter_confirms_e3_extending_past_5000_iters_is_net__]].

---

## Update (2026-07-20T03:32:10.598463)

EXAM-COMPARABILITY CORRECTION (2026-07-20, analysis diagnose-20260720-123142 supersedes diagnose-20260720-122425/115818). The earlier wording claimed both runs were 'graded on the SAME fixed none/soft/medium/hard exam because neither used --doraemon-dr-from'. That is WRONG. eval.py static defaults --doraemon-dr to True (eval.py:118 BooleanOptionalAction; eval.py:1131-1135 -> load_doraemon_dr(run_dir); dr_config.py:206 'hard range = learned mean +/- 2*std'), so EACH run was graded on ITS OWN final learned DORAEMON distribution. Not passing --doraemon-dr-from only means no THIRD run's DR was used; it does NOT make the exam common. Per [[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]], only the none level (fixed nominal physics) is a fair cross-run comparison; soft/medium/hard are run-relative.

WHAT SURVIVES (all of the verdict): every headline number sits on the FAIR none level -- roll ss_error 0.215->0.171 (-21%), pitch 0.195->0.296 (+52%), roll os_env_mean 17.02->26.99 (+59%), roll n_gt20 4.3->61.3. The axis trade and the transient-overshoot regression are therefore established on identical nominal physics and stand unchanged.

WHAT CHANGES: the soft/medium/hard rows are no longer evidence. The bias is one-sided and computable: extend8k's curriculum ended WIDER (entropy_before -18.20 vs -22.70), so it sat the HARDER exam there -- its roll improvement at those levels is UNDERSTATED and its pitch/yaw regression OVERSTATED. In particular the 'overshoot damage is monotone-largest at nominal (+59% none -> +29% hard)' gradient must NOT be cited as evidence that damage concentrates at nominal: the gradient is confounded by exam difficulty.

REUSABLE LESSON: 'both plain static / neither used --doraemon-dr-from' is NOT a comparability argument. To get a common exam you must pass --doraemon-dr-from <ref run> (shared exam) or --no-doraemon-dr (static DR cfg). Otherwise restrict cross-run claims to none.
