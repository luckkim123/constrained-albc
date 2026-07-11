---
title: "reward.md §6 (error buffers / reward call site / dt-scaling) theory review: conditionally sound; the one real exposure is B4 (reward*dt with FIXED gamma = Tallec's dt-invariance pathology, horizon dt/(1-gamma)=2.0s) but LATENT since no run changes step_dt; B5 'contradiction' refuted (actor scale-invariant vs DORAEMON performance_lb raw-return gate = consumer distinction)"
tags: ["albc", "envs-main", "reward", "dt-scaling", "discount-factor", "time-discretization", "theory-review", "performance-lb", "doraemon", "angle-wrap", "latency-dr", "experiment-lead"]
created: 2026-07-11T07:09:40.543016
updated: 2026-07-11T07:09:40.543016
sources: []
links: ["bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h.md", "reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o.md", "yaw_command_is_rate_not_angle_inherited_design_defensible_only_i.md"]
category: decision
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# reward.md §6 (error buffers / reward call site / dt-scaling) theory review: conditionally sound; the one real exposure is B4 (reward*dt with FIXED gamma = Tallec's dt-invariance pathology, horizon dt/(1-gamma)=2.0s) but LATENT since no run changes step_dt; B5 'contradiction' refuted (actor scale-invariant vs DORAEMON performance_lb raw-return gate = consumer distinction)

Theoretical review of reward.md §6 (error buffers / reward call site / `k*dt` scaling), envs/main `Isaac-ConstrainedALBC-TRPO-v0`. Code-verified 2026-07-11 branch exp/latency-dr, literature-grounded (2 document-specialist sweeps, opened-source-only). Full report: `/workspace/.sp/plans/REVIEW_reward_error_buffer_dt_scaling.md`. THEORY/LITERATURE review, not a run analysis — no training data, no code change. Sister of the bias-term review [[bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h]].

VERDICT: §6 mechanism is CONDITIONALLY SOUND. 10 questions (A1-D10): 8 "no problem", 2 "conditional" (A3 rate-command design is a separate review's concern; B4 dt-gamma pathology is LATENT). The whole design is complete UNDER the premise "dt is a fixed constant" — and that premise currently holds (verified: no run changes step_dt).

THE ONE REAL THEORETICAL EXPOSURE = B4 (dt-scaling <-> gamma <-> optimal-policy invariance):
- CODE FACT: reward scaled `value*weight*dt` (`rewards.py:232`, single point, k is PER-SECOND); step_dt=0.02 (=sim.dt 0.005 x decimation 4, inherited from DirectRLEnv, albc never assigns); gamma=0.99 FIXED, dt-independent (`rsl_rl_ppo_cfg.py:211,389`; cost_gamma=0.99 :217); normalize_value=False.
- `Sum r_k*dt ~ integral r dt` (left Riemann sum) is correct AND is Isaac Lab's own built-in convention: `RewardManager.compute()` docstring says it multiplies weight by dt "to balance rewards w.r.t. the chosen time-step" (official docs, direct-fetched). So `k*dt` is framework-baked, not a project choice. Framework does NOT touch gamma.
- PATHOLOGY (Tallec, Blier, Ollivier, "Making Deep Q-learning Robust to Time Discretization", ICML 2019, arXiv:1901.09732 — paper body direct-fetched twice, consistent): dt-invariance of the discounted objective requires BOTH `r_dt := dt*r` AND `gamma_dt := gamma^dt`. With gamma FIXED, the physical planning horizon `dt/(1-gamma)` is NOT dt-invariant (shrinks to 0 as dt->0 => "increasingly short-sighted"; in the fine limit the advantage signal that discriminates actions vanishes, Q-learning ceases to exist). Our code does (a) reward*dt but NOT (b) gamma^dt = EXACTLY the named pathology.
- QUANT: dt=0.02, gamma=0.99 => horizon = 0.02/0.01 = 2.0 s, effective continuous discount rate rho = -ln(0.99)/0.02 = 0.50/s. If decimation change made dt=0.01, horizon halves to 1.0 s (rho=1.005/s) => optimal policy CHANGES (predicted by the paper's formula, not numerical noise).
- ANSWER to "does changing dt/decimation change the optimal policy?": conditional on scaling choice. Under naive reward-only scaling (our case): YES. Fix = gamma -> gamma^(dt_new/dt_old) alongside reward*dt (Tallec's prescription; claimed sufficient, not proven the ONLY fix).
- WHY IT'S LATENT (not an active bug): NO run changes step_dt. latency-DR (this branch) DRs only integer control_delay_steps (action lag via DelayBuffer), NOT sim.dt/decimation/step_dt — time discretization is fixed 50 Hz across every run. De Asis & Sutton (RLC 2024, arXiv:2406.14951, abstract) identify a related left-vs-right Riemann-sum inconsistency but state it is "no loss of generality" when dt is FIXED -> also inert for us. So B4 is a DOCUMENTED TRAP for a future dt-changing experiment (control-frequency ablation), not a present defect.

B5 (prompt's hypothesized contradiction) — REFUTED, it is a CONSUMER DISTINCTION already captured:
- The apparent contradiction: performance_lb=250 is calibrated to the ABSOLUTE return scale (raw-return p25), so `k*dt` change breaks it; yet the wiki says reward absolute scale is INVARIANT to the ConstraintTRPO actor.
- Resolution: different consumers. ACTOR is scale-invariant (advantage standardized (A-mu)/sigma cancels uniform scaling, AND natural-grad renormalized to max_kl trust region => doubly invariant). DORAEMON success gate `success=(return >= performance_lb)` compares RAW un-normalized return => scale-DEPENDENT. The `reward_absolute_scale_is_invariant...` note ITSELF lists this as leak-path #3 ("DORAEMON success ... raw episode return, never normalized"). So the note never claimed lb-invariance; it claimed actor-invariance. dt-scaling touches exactly leak-path #3. See [[reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o]].
- ACTION RULE (compounds the note's): any experiment that rescales reward (global k, OR dt change) must re-calibrate performance_lb by the same factor, else reward-scale confounds DR-curriculum difficulty (rule02 minimum-change-revert).

OTHER VERDICTS (all "no problem", worth the record):
- A1/A2 angle wrap `atan2(sin,cos)` = canonical shortest-signed-distance wrap (Wikipedia atan2 direct; +-pi branch-cut exists but real-angle inputs never hit (0,0)). Necessity QUANT-verified: cmd=+179deg, state=-179deg => naive raw=+358deg, err^2=39.0 vs wrapped 0.00122 (4-order blow-up); exp kernel naive underflows to 0 vs wrapped 0.94; quad penalty naive -32.5 (false huge negative for a 2deg error). Justification logically sound.
- A3 wrap asymmetry (rp wrapped, yaw not): correct GIVEN yaw is a rate command (rate is aperiodic, wrap N/A). But the asymmetry is downstream of the rate-command choice, which a separate review found is a historical residue [[yaw_command_is_rate_not_angle_inherited_design_defensible_only_i]].
- B6 single dt-scaling point = correct laziness (no term can miss dt). No term needs a different dt power: yaw rate error goes THROUGH the exp kernel (normalized to [0,1]) BEFORE dt, so "double-dt on an already-rate quantity" does not arise.
- C7 termination_penalty OUTSIDE dt (added post-compute, no *dt, shipped 0.0): correct (a one-time event is not a rate). Latent dt-coupling: if dt changes, the 7 rate-terms scale ~dt but termination stays fixed => relative weight shifts. Harmless now (penalty=0 + dt fixed); flag for enable-termination-AND-change-dt experiments.
- C8 sign convention: 7 tracked terms return non-neg magnitude, sign in weight k; termination uses direct sign (outside the term loop). Minor readability divergence, not a bug.
- D9 shared error buffer (_att_rp_err/_yaw_rate_err feeds reward kernel + integral-obs + bias-EMA): single source = enforced agreement on wrap/sign/units (good DRY invariant); flip side = changing the error definition (e.g. yaw->angle) propagates to all 3. Document the coupling; the alternative (3 independent computations) is worse (drift risk).
- D10 three consumers treat dt differently (integral: err*dt; EMA: no dt; reward: err^2 then dt) = JUSTIFIED by what each quantity IS: integral=time-integral of a rate (needs dt), EMA=dimensionless exponential average (no dt), reward=per-second rate (needs dt). Subtlety: EMA's alpha window is STEP-defined (~100 steps), so it too silently assumes dt fixed — consistent with the whole-design premise.

RECOMMENDATIONS (doc-only; NO code change warranted under the dt-fixed premise):
- R1 [HIGH] reward.md §6: add the "dt is a fixed constant" premise + a warning that any dt/decimation-changing experiment must (a) scale gamma -> gamma^(dt_new/dt_old) AND (b) re-calibrate performance_lb by the reward-scale factor. Grounds: Tallec (horizon) + reward_absolute_scale note (lb).
- R2 [MED] §6 note: the shared-buffer 3-consumer coupling (D9) — changing yaw to an angle command hits reward+integral-obs+bias-EMA simultaneously.
- R3 [LOW] §6.2 note: termination sign-convention divergence (C8) + its dt-scale relative-weight coupling (C7).
- NO structural change: wrap, single scaling point, 3-consumer dt-asymmetry all theoretically justified; the single dt-scaling point is correct laziness — touching it risks regression.
- CODE-CHANGE PROMPT VALUE: none. Only pull a code prompt (gamma^dt + performance_lb re-cal) IF a dt-changing experiment is actually designed.

LITERATURE GRADES (opened-source-only): [primary/direct] Tallec et al. ICML 2019 (arXiv:1901.09732, body 2x), Isaac Lab RewardManager docs (weight*dt convention), atan2 wrap (Wikipedia). [abstract-only] De Asis & Sutton RLC 2024 (arXiv:2406.14951, "no loss of generality when dt fixed"), Kalyanakrishnan et al. frame-skip 2021 (arXiv:2102.03718 — but DISCRETE Atari, continuous-control generalization UNVERIFIED), Lee/Leok/McClamroch SO(3) ACC 2011 (arXiv:1010.1725, partial), Schuck et al. SO(3)-primer ICLR 2026 (arXiv:2510.11103). UNCONFIRMED: Fossen 2011 marine handbook (rate-squared tracking-cost standard — 2ndary cite only), Mysore Neuroflight 2021 (reward formula, PDF extract failed). Euler-singularity critiques (Lee, Schuck) target LARGE-angle trajectory tracking, NOT our small-angle attitude-hold reward — do NOT over-read them as "Euler is broken here".

