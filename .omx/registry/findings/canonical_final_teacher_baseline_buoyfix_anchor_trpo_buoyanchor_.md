---
title: "CANONICAL final teacher baseline = buoyfix anchor trpo_buoyanchor (biasema 72D-obs config on post-TAM + neutral-buoyancy plant, workstation seed 30); remaining work is small tweak-tests against it; B0c is the one open lever that can still change it"
tags: ["final-baseline", "teacher-baseline", "buoyfix", "biasema", "anchor", "reference", "user-decision", "frozen-config", "b0c", "closeout", "ftc", "tweak-tests"]
created: 2026-07-24T11:20:28.867389
updated: 2026-07-24T11:20:28.867389
sources: ["trpo_buoyanchor_s30_260722_134743", "report-consolidated-260724", "user-decision-2026-07-24"]
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite.md", "roll_transient_is_worst_at_none_dr_and_improves_monotonically_as.md", "experiment_idea_latency_transport_delay_dr_sensor_obs_control_ac.md", "thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban.md", "reward_sigma_integral_obs_gate_coupling_reward_md_7_theory_revie.md", "real_robot_has_2_faulted_thrusters_user_judges_buoyancy_restorin.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# CANONICAL final teacher baseline = buoyfix anchor trpo_buoyanchor (biasema 72D-obs config on post-TAM + neutral-buoyancy plant, workstation seed 30); remaining work is small tweak-tests against it; B0c is the one open lever that can still change it

CANONICAL DESIGNATION (user decision 2026-07-24): the FINAL teacher baseline is the buoyfix anchor. All remaining work -- FTC and small tweak-tests (a few parameters, DR ranges, nominal-value nudges) -- is measured AGAINST this baseline, then the teacher is wrapped up. This page is the durable reference for "what is the final baseline config".

## The baseline (code-verified fingerprint, from the run's own config)

[FINDING] Final teacher baseline = the buoyfix anchor run family trpo_buoyanchor_s30/s31/s32 (group teacher_baseline_buoyfix, experiment_name albc_trpo_teacher). It is the ADOPTED biasema config trained on the corrected plant. Identity fingerprint:
- Task: Isaac-ConstrainedALBC-TRPO-v0 (envs/main, attitude-only). num_envs 4096. Screening seed 30 (s31/s32 give the 3-seed noise floor). WORKSTATION-trained.
- Observation: observation_space 72, use_bias_ema_obs true, bias_ema_alpha 0.99 (the P-B1 / f42a67f adoption).
- Plant: main hull volume 0.0079 (neutral buoyancy fix) + buoy volume 0.00268 (unchanged) + post-TAM allocation-matrix fix. So plant = post-TAM AND neutral-buoyancy (TWO corrections).
- Algorithm/budget: ConstraintTRPO + IPO + asymmetric critic + DORAEMON; max_iterations 5000, step_interval 250, kl_ub 0.12, performance_lb 250, encoder_latent_dim 9, entropy_coef 0.003, min_std 0.05 (+ per-dim tuples). Ocean current enabled, max_thrust 50.0 nominal.
[EVIDENCE: run config trpo_buoyanchor_s30_260722_134743/config/{env.yaml,agent.yaml} read 2026-07-24 -- observation_space:72, use_bias_ema_obs:true, volume:0.0079/0.00268, max_iterations:5000, entropy_coef:0.003, min_std:0.05, encoder_latent_dim:9, seed:30, num_envs:4096; config.py:431 use_bias_ema_obs default True; config.py:544 step_interval 250; performance_lb 250]
[CONFIDENCE: HIGH]

## Why this is the baseline (provenance)

[FINDING] It is the terminus of the teacher campaign, not an arbitrary pick: (1) plant accuracy was the real win -- the buoyancy recentre + TAM fix collapsed the hard-DR roll heavy-tail and cut nominal overshoot ~-3.93pp; (2) biasema was the best CONFIG probe (adopted, won all ss_error cells on the shared-anchor eval) while the 5 Stage-A single-variable mechanism probes were 0/5; (3) the retrain-on-corrected-plant delta was sub-threshold (~9.6% of the 1.146deg euler obs noise), so the anchor is SOUND. See report /workspace/.sp/reports/teacher-campaign-consolidated-260724/report.ko.md.
[EVIDENCE: consolidated report sections 4/6; wiki thruster_util_is_the_binding_constrainttrpo_constraint_in_7_of_7, penalty_vs_objective_exchange_rate_deg_of_attitude_error_bought_]
[CONFIDENCE: HIGH]

## Caveats attached to the designation (do not lose these)

- [CAVEAT] biasema was adopted as a CONFIG BUNDLE; the causal isolation of the bias_ema observation ALONE is NOT established (the adopted P-B1 run also had wider training DR across 20/20 params). Fine for choosing the baseline; a paper claim "bias_ema obs improves X" needs a cleaner isolation. See report section 2.
- [CAVEAT] "Final" is final UNLESS campaign B0c changes it: B0c = max_thrust +/-15% per-env DR band, the one remaining tuning lever, and it targets the single binding constraint thruster_util. B0c NULL -> anchor IS final; B0c adopted -> final = anchor + B0c. See [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]].
- [CAVEAT] Machine isolation: the final model trains on the WORKSTATION. A DGX-trained model is not comparable (measured +109% same-config same-seed machine term); the dgxseed30/31/32 runs are a separate, non-comparable set. See [[e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite]].

## Remaining work is small tweak-tests measured against THIS baseline

[FINDING] The teacher is in closeout: remaining experiments are low-intensity tweak-tests against this baseline, then wrap up. The roster lives in the open backlog / program-status (SSOT for tracking), and every one of them uses this anchor as its none-fair reference and its seed-noise floor. Candidates currently open: B0c (max_thrust +/-15% DR); nominal-corner exposure for the unsolved none-worst roll transient ([[roll_transient_is_worst_at_none_dr_and_improves_monotonically_as]]); latency/transport-delay DR ([[experiment_idea_latency_transport_delay_dr_sensor_obs_control_ac]]); thruster nonlinear curve / deadband ([[thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban]]); reward-sigma integral-gate R1/R6 ([[reward_sigma_integral_obs_gate_coupling_reward_md_7_theory_revie]]); and FTC (fault-tolerant control for the real robot's 2 faulted thrusters -- separate-session handoff at /workspace/.sp/plans/2026-07-24-fault-tolerant-control-handoff.md, see [[real_robot_has_2_faulted_thrusters_user_judges_buoyancy_restorin]]). Discipline: queue-only launch (human gate), none-only cross-run comparison, single-seed screening, baseline-tag + exp/<topic> branch isolation before any code-modifying tweak.
[EVIDENCE: omx open backlog 2026-07-24; .claude/rules/02-03]
[CONFIDENCE: HIGH]

