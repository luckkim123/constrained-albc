---
title: "FTC investigation 2026-07-25: m4 loss halves pure-yaw ceiling (util x2) while roll/pitch stay buoyancy-dominated; literature + composition risks; verdict MEASURE-FIRST (deterministic m4-kill eval before any FTC training)"
tags: ["fault-tolerant-control", "ftc", "thruster-fault", "authority-gap", "TAM", "yaw", "buoyancy", "thruster_util", "doraemon", "literature-review", "measure-first", "handoff"]
created: 2026-07-25T06:49:57.904689
updated: 2026-07-25T08:10:08.945701
sources: ["handoff-2026-07-24-ftc", "authority_gap.py-260725", "oms-scholar-researcher-surveys-260725"]
links: ["real_robot_has_2_faulted_thrusters_user_judges_buoyancy_restorin.md", "tam_vertical_single_motor_dual_esc_measured_2026_07_05.md", "tam_columns_must_match_robot_firmware_esc_channel_order_reorder.md", "plant_fix_needs_apply_before_retrain_main_hull_volume_0_009_0_00.md", "thruster_util_is_the_binding_constrainttrpo_constraint_in_7_of_7.md", "per_env_heavy_tail_analysis_current_capability_hard_ceiling_and.md", "an_off_doraemon_channel_that_costs_return_stalls_the_curriculum.md", "eval_metric_units_and_decision_floors_os_env_mean_is_percent_of.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-experiment
blocked-on: "MEASURE-FIRST eval DONE 2026-07-25 (H1 confirmed, GO). Remaining: design fault-DR training arm via exp-design (human-gated); performance_lb recalibration number from training-side return, not this tracking eval"
---

# FTC investigation 2026-07-25: m4 loss halves pure-yaw ceiling (util x2) while roll/pitch stay buoyancy-dominated; literature + composition risks; verdict MEASURE-FIRST (deterministic m4-kill eval before any FTC training)

Synthesis of the FTC handoff mission (/workspace/.sp/plans/2026-07-24-fault-tolerant-control-handoff.md), executed 2026-07-25. Companion hardware-fact page: [[real_robot_has_2_faulted_thrusters_user_judges_buoyancy_restorin]].

[FINDING] Fault identity (working hypothesis, NEEDS USER CONFIRMATION): the 2 faulted channels are m3 (redundant dual-ESC channel of the SINGLE physical vertical motor; m0 drives the same motor at full speed) and m4 (horizontal front-right).
[EVIDENCE: 2026-07-05 watertank measurements -- [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]] (m3 intermittent, per-unit contact fault) and [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]] 2026-07-05 checkpoint (m4 HW-faulty, unmeasurable); the 2026-07-24 user report "2 of 6 faulted" names no channels]
[CONFIDENCE: MEDIUM -- two independently recorded HW faults match the count, but the user has not confirmed these are the two]

[FINDING] Authority gap quantified from the live TAM: roll/pitch attitude is buoyancy-dominated on the real plant and the faults change it ~nothing; the entire fault cost concentrates on YAW. Real-plant thruster roll/pitch authority ~1.1 N.m (4 x 0.007 arm x 40 N effective bound; vertical pitch differential physically nonexistent -- one motor) vs buoyancy restoring ~5.2*sin(theta) N.m (W~104 N, BG=0.05 m). Yaw: restoring contributes ZERO; healthy pure-yaw ceiling 23.0 N.m (all 4 horizontal saturated); with m4 dead the unique Fx=Fy=0 solution uses ONLY the surviving diagonal pair m2+m5 -> ceiling 11.5 N.m (-50%) with per-thruster peak utilization x2.00 at equal Mz (force-leaking "dirty" yaw: 17.3 N.m, -25%, util x1.33; m1 contributes ZERO to pure yaw when m4 is dead). m3-dead costs the real plant ~nothing (redundant ESC channel). All C(6,2)=15 pairs computed; m3+m4 is among the mildest pairs for the attitude-only task.
[EVIDENCE: envs/main/config.py _BASE_ALLOCATION_MATRIX + _ESC_CHANNEL_ORDER (horizontal rows measured 2026-07-06); numpy session computation (authority_gap.py, 2026-07-25); weights/BG from the buoyancy audit in [[plant_fix_needs_apply_before_retrain_main_hull_volume_0_009_0_00]]]
[CONFIDENCE: HIGH for the TAM arithmetic; MEDIUM for real-plant transfer (horizontal 0.007 Mx/My coupling is unverified sim carry-over)]

[FINDING] Tension resolution ("buoyancy dominates" vs "thruster_util binding 7/7"): both are true on DISJOINT axes. Buoyancy covers roll/pitch (faults do not touch it); the binding max-based thruster_util constraint is attacked exactly and only on the yaw channel, where m4 loss doubles the peak utilization needed for the same Mz. Whether that matters depends on the task's actual yaw-torque demand vs the halved ceiling -- not derivable from training aggregates, directly measurable by eval.
[EVIDENCE: [[thruster_util_is_the_binding_constrainttrpo_constraint_in_7_of_7]] (J_C/d_k 0.81-0.94; constraint = max over 6 of |state|, budget 0.40, constraints.py:187-202); authority computation above]
[CONFIDENCE: HIGH]

[FINDING] Sim fidelity boundary: only horizontal (m4-class) faults can be injected FAITHFULLY in the current sim. The sim vertical rows model two independent heave/pitch-differential channels (My +/-0.145) refuted by hardware (single motor, dual ESC, left-right mount) -- killing m3 in sim manufactures a fake pitch-authority loss that does not exist on the real robot. Vertical fault fidelity is blocked on the vertical TAM rewrite (open needs-apply-before-retrain item).
[EVIDENCE: [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]]; config.py:86-95 OPEN comment]
[CONFIDENCE: HIGH]

[FINDING] Infrastructure status: FTC step-1 infra is COMPLETE and dormant since 2026-06-14 (constrained-albc 3e37365 + marinelab thruster health): per-thruster health in ThrusterModel, FaultInjectionCfg (thruster/sensor/joint; default off, byte-identical), reset-time sampling in albc_env, eval.py --fault flag, npz fault_thruster_{0..5} recording, failure<->fault analysis join. Missing for the measurement: a DETERMINISTIC per-thruster mask (current sampling is i.i.d. Bernoulli only) -- a small additive extension. Missing for fault-conditioned training: thruster health is in neither the policy obs (thruster ESC-feedback obs = filtered command, health-blind) nor the 28D privileged obs.
[EVIDENCE: code read this session: marinelab/core/thruster.py, envs/main/mdp/faults.py, config.py:333-366, albc_env.py:1576-1583, analysis/eval.py --fault; research-order plan in [[per_env_heavy_tail_analysis_current_capability_hard_ceiling_and_]] ((1) infra -> (2) fault eval -> (3) FTC training: step 1 done)]
[CONFIDENCE: HIGH]

[FINDING] Literature verdict (two citation-verified surveys, oms scholar-researcher agents, 2026-07-25): (a) closest-topology classical result -- Choi & Kondo, hovering AUV with 4 horizontal + 2 vertical thrusters (OCEANS'10 IEEE Sydney 2010, doc 5603565; journal: Advanced Robotics 28(4):245-256, 2014) -- is TASK-DEPENDENT: horizontal-plane tracking survives on 3 thrusters, omnidirectional maneuvers degrade; our narrower attitude-only task (yaw + heave from thrusters) leans recoverable. (b) Every classical paper with a strong recovery guarantee assumes >=8 actuators (Podder & Sarkar, RAS 34(1):39-52, 2001, ODIN 8 thrusters; Ismail et al. 2014 needs 12+; BlueROV2-Heavy 8-thruster arXiv:2504.16037) -- 1.6-2.5x our effective 5; classical re-allocation FTC also presupposes an allocation layer our direct per-thruster policy does not have (8D action fixed by design, gradient-vanishing rationale). (c) RL: single fault-agnostic policies succeed on single-actuator-loss (Sharma et al. arXiv:2109.10488 quadrotor SAC; Okamoto et al. arXiv:2111.10005 ACDR, hard-to-easy severity curriculum beats easy-to-hard), BUT fault-CONDITIONED routing beats monolithic (Turrisi et al. arXiv:2606.25965 MoE), and a full-PDF-verified 2026 result (Xu et al. arXiv:2606.02280) shows continuous-latent RMA-style adaptation -- the same mechanism as our privileged encoder -- structurally fails on discrete actuator-dropout events (needs explicit fault conditioning or a discrete latent axis). (d) UUV-specific precedent exists: the Lagattu/Chaffre/Sammut cluster (ICRA 2025, IEEE 11128023, BlueROV2 real-hardware DRL reallocation without explicit FDI; ANZCC 2024, IEEE 10432828, non-diagnosable thruster faults; IJRR 2026, DOI 10.1177/02783649261451002, physical AUV) -- SEMI-VERIFIED (paywalled; bibliographic existence confirmed, full method not read); their reallocation mechanism presupposes spare healthy-thruster authority that our binding-constraint regime lacks.
[EVIDENCE: agent surveys this session with per-citation live web verification; paywalled items retained as existence-only claims]
[CONFIDENCE: HIGH for verified items; MEDIUM for semi-verified (paywalled) items]

[FINDING] Composition risks for any future fault TRAINING arm (why the verdict is MEASURE-FIRST, not GO): (1) DORAEMON stall -- an off-curriculum channel costing ~10% return pins the run at mode -2 for the whole run (e1 latency precedent), so train-time fault injection needs performance_lb recalibration (MEASURED, not guessed) or promotion to a curriculum dim (Bernoulli faults fit the Beta-continuous sampler poorly, same problem as integer delay); (2) thruster_util fights compensation -- the constraint is max-based and binding, and m4-dead yaw needs x2.00 peak utilization, so the IPO barrier actively suppresses exactly the compensating behavior (any budget redesign would confound the comparison); (3) discrete-fault representation -- the continuous 9D latent is the wrong prior for a discrete dropout (Xu et al. above), pointing at fault-conditioned privileged obs (+6D health) rather than DR-only; (4) the student channel is currently broken -- the buoyfix student's latent already collapses on EXISTING env params (in-loop env-var reconstruction ~8-16%, 2026-07-24 diagnostic), so fault inference through that channel is not deployable until the observability retrain lands.
[EVIDENCE: [[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_]]; constraints.py:187-202; program-status note 2026-07-24 (latent-underdispersion-diagnostic)]
[CONFIDENCE: HIGH]

[NEXT -- RECOMMENDATION: MEASURE-FIRST] Do NOT start FTC training now. The user's proceed-without-FTC baseline decision stands unrefuted for roll/pitch and unproven for yaw. The one measurement that settles it: eval-only deterministic fault injection on the anchor checkpoint (trpo_buoyanchor_s30) -- m4 health=0 in ALL envs vs healthy, static eval, all DR levels, ZERO training. Eval is deterministic (repeat runs give identical metrics), so any delta is signal; pre-register absolute floors per [[eval_metric_units_and_decision_floors_os_env_mean_is_percent_of_]]. Below floors -> NO-GO recorded with evidence, baseline proceeds as-is. Above floors on yaw -> design a fault-training arm that addresses risks (1)-(4) explicitly. Prerequisites: user confirms fault identity (m3+m4 hypothesis); instrument = deterministic per-thruster mask extension (additive, off-by-default byte-identical). Proposal drafted via exp-design, human-gated, never auto-launched.

---

## Update (2026-07-25T07:37:50.622103)

[DECISION 2026-07-25 -- user] Direction CONFIRMED: proceed to fault-as-DR robustness training (randomized per-env thruster/sensor/joint faults during training -> single fault-agnostic policy, no fault in obs, no FDI on the real robot). The MEASURE-FIRST verdict is now a SEQUENCING step, not a go/no-go gate: the cheap m4-kill eval (proposal FTC-m4 / next-20260725-155325) runs FIRST to measure the fault return-cost, which is the input needed to recalibrate DORAEMON performance_lb and avoid the e1-style curriculum stall in the training arm.
[EVIDENCE: user statement 2026-07-25 -- "학습 환경에서 랜덤하게 확률적으로 고장" + confirmed m3+m4 fault identity is correct but "굳이 알 필요 없다" (irrelevant to randomized-DR training)]
[CONFIDENCE: HIGH -- user domain decision]

[FINDING] The requested capability ALREADY EXISTS and is dormant (FaultInjectionCfg + ActuationNoiseCfg, config.py:347-387, built 2026-06-14, default off). The user's five cases map 1:1: healthy (thruster_fail_prob), partial degradation + full death (thruster_health_range 0.0-0.5), sensor noise (sensor_noise_scale_range), actuation noise (ActuationNoiseCfg). No new fault mechanism needs building for the training arm -- only the design decisions below.
[EVIDENCE: code read 2026-07-25 -- envs/main/config.py:347-387, mdp/faults.py:27-44, marinelab/core/thruster.py:197-201]
[CONFIDENCE: HIGH]

[NEXT -- fault-DR training arm design constraints (the four composition risks, now the design spec)] (1) DORAEMON stall: fault is off-curriculum static DR that costs return; promote fault-severity to a _PARAM_DEFS curriculum dim OR recalibrate performance_lb from the MEASURED fault-on return (eval FTC-m4 supplies the number). (2) Controllability + sim-fidelity bound on the fault distribution: keep all-fail probability ~0; VERTICAL faults (m0/m3) are sim-unfaithful (single motor modeled as two independent channels) so restrict faithful fault-DR to the horizontal channels (m1,m2,m4,m5) until the vertical TAM rewrite lands. (3) binding thruster_util constraint suppresses the surviving-thruster over-drive that fault compensation needs -- constraint budget may need rethinking for the fault-on regime (isolate carefully, minimum-change). (4) robustness-vs-nominal cost: fault-DR will likely shave healthy-case attitude tracking (the insurance premium). Sequenced AFTER the FTC-m4 eval.
[CONFIDENCE: HIGH for the mechanisms; the training-arm proposal itself is exp-design's job, human-gated]

---

## Update (2026-07-25T08:10:08.945701)

[RESULT 2026-07-25 -- FTC-m4 eval RAN and returned decisively] The MEASURE-FIRST probe (proposal next-20260725-155325) executed: deterministic m4 health=0 in all 64 envs vs healthy, anchor trpo_buoyanchor_s30 model_4999.pt, same eval commit (3e01f22, exp/ftc-fault-eval), seed 42, static, all 4 DR levels. Bite-checks PASS (npz fault_thruster_4==0 all envs / others 1.0; faulted != healthy overwhelmingly). Result dirs: experiments/.../trpo_buoyanchor_s30_260722_134743/eval/static_260725_164839 (healthy) + static_260725_165657 (m4-dead, carries ftc_m4_healthy_vs_dead.png + FTC_M4_README.md).

[FINDING] H1 CONFIRMED at ALL 4 DR levels and ALL axes: the fault-unaware anchor policy degrades materially when m4 dies. Not absorbed. GO for fault-DR robustness training (the user's plan is validated by direct measurement, not assumed).
[EVIDENCE: none-level healthy->m4-dead: roll ss_error 0.539->1.909 deg (+1.37, floor 0.10), pitch 0.219->1.209 (+0.99), yaw ss_error 0.0057->0.0976 rad/s (17x, +0.092, floor 0.0017), yaw os_env_mean 2.69->24.68 pp (+21.98, floor 10), yaw n_gt20 0->27.5 envs (floor 15). Every DR level breaches. att_norm ss_error none 0.63->2.44 (~4x). summary.json both arms]
[CONFIDENCE: HIGH -- deterministic eval, clean same-commit A/B, m4 is a horizontal channel with the 2026-07-06 MEASURED TAM (faithful, unlike vertical m3)]

[FINDING] Yaw is the hardest-hit axis, exactly as the authority analysis predicted (m4 loss halves the pure-yaw ceiling 23.0->11.5 N.m, peak util x2 on the surviving diagonal pair m2+m5). Yaw breaches on all three metrics (ss_error, os, n_gt20) at all 4 levels; the 17x none-level yaw ss_error jump is the actuator-authority mechanism made visible.
[EVIDENCE: authority computation (wiki, this page above) + eval yaw deltas +0.037..+0.168 rad/s across levels]
[CONFIDENCE: HIGH]

[FINDING -- REFUTES a prior user assessment] "Buoyancy restoring dominates, so the 2 thruster faults are low-impact for the attitude-only task" is FALSE for TRACKING. Roll/pitch tracking degrades heavily under m4-dead (none roll 0.54->1.91 deg, pitch 0.22->1.21; hard roll 0.68->3.17). The buoyancy restoring provides STABILITY (survival stays 92-100%, the vehicle does not tumble) but NOT tracking accuracy: the fault-unaware policy issues commands calibrated to a healthy TAM, so with m4 dead the realized wrench is wrong on every axis it drives, and its yaw-compensation over-drive of m2+m5 spills coupling into roll/pitch. Stability != tracking. The low-impact hypothesis held only for "does it stay upright", not for "does it track".
[EVIDENCE: eval roll/pitch ss_error deltas all >= floor at all levels; survival_pct healthy 100% vs m4-dead 94/100/95/92% (none/soft/medium/hard)]
[CONFIDENCE: HIGH for the measurement; the mechanism (policy TAM-mismatch + yaw-compensation coupling) is a code-level inference, MED-HIGH]

[CAVEAT] This tracking eval does NOT directly give the episode-RETURN cost needed to recalibrate DORAEMON performance_lb for the fault-DR training arm (summary.json logs tracking error + survival, not RL return). The return-cost number still must come from the fault-DR training arm's early return (or a reward-logged eval). The eval settled the "is the fault real" gate (YES); the performance_lb figure is the remaining training-design input. Also: fresh healthy differs from a 2026-07-24 eval by max 0.124 deg ss_error (different prior eval settings/command-box era) -- the trustworthy A/B is the same-commit healthy vs faulted, not vs older evals.

[NEXT] Design the fault-DR robustness training arm via exp-design (human-gated launch), addressing the four recorded composition risks (DORAEMON stall / binding thruster_util / discrete-fault representation / broken student channel). Faithful fault-DR restricted to horizontal channels (m1,m2,m4,m5) until the vertical TAM rewrite lands. Instrument for deterministic single-thruster eval is committed (3e01f22).

