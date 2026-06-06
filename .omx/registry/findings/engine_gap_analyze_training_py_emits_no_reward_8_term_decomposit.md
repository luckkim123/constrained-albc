---
title: "engine-gap: analyze_training.py emits no reward 8-term decomposition scalars"
tags: ["engine-gap", "reward-decomposition", "analyze_training", "constraint-naming", "CORRECTION", "implemented"]
created: 2026-06-06T09:15:01.438112
updated: 2026-06-06T09:46:07.076418
sources: ["diagnose-20260606-180317"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: analyze_training.py emits no reward 8-term decomposition scalars

[ENGINE-GAP] analyze_training.py (.omx/profile) diagnoses reward only as plateau/changepoint/regime + a diagnostic-panel VIEW; it never emits the 8 reward terms (att_rp/lin_vel/yaw_vel/bias/smoothness/thruster/torque/total) as final SCALARS. So a report cannot make a code-exec [CONFIDENCE: HIGH] claim about WHICH reward term the policy favoured (the per-term confirmation of an eval trade) without going to raw TB by hand -- which the omx lane forbids. This is distinct from the SKILL-side vocab-completeness gap (engine_gap_omx_cli_skill_gaps... GAP 4): that one is 'the skill does not REQUIRE coverage', this one is 'the engine cannot SUPPLY the scalars even if required'. [WHERE] .omx/profile/analyze_training.py TIER3 block (add a reward-decomposition section reading the Reward/* TB tags -> final-window mean per term) OR a new omx reduce format 'tb_final' that returns named final-window scalars for a tag list. [SPEC] emit final-window (last ~200 iter) mean for each Reward/* tag so a report can cite e.g. 'Reward/att_rp 5.38->4.50' from code-exec, not memory. [EVIDENCE] diagnose-20260606-180317: all 3 reports' section 5 had to footnote 'reward 8-term decomposition not emitted as scalars'; the known E1 finding 'att_rp 5.38->4.50' could not be re-verified through the engine this pass. [STATUS] proposed.

---

## Update (2026-06-06T09:20:27.837743)

[CORRECTION 2026-06-06] The original claim on this page ('reward 8-term decomposition is unavailable') is FALSE. The teacher TB has all 8 Reward/* tags + 21 Constraint/* tags among 134 scalars (EventAccumulator-verified). They ARE extractable by code-exec. The REAL engine-gap is narrower: (a) analyze_training.py's constraint discovery keys off Constraint/cost_return_* / barrier_margin_* / d_k_* but this workspace uses Constraint/margin/* + Constraint/viol/* + Constraint/barrier_penalty -> engine prints constraints=0 + empty table though 10 constraints are logged; (b) no engine block emits the Reward/* terms as final-window scalars. [WHERE] .omx/profile/analyze_training.py: constraint prefix scan (~L565 Constraint/cost_return_*, _margin_at_floor ~L382) -> add margin/viol naming; new TIER3 reward-decomposition block reading Reward/* final-window mean. Cleaner: an 'omx reduce' tb_final format returning named final-window scalars for any tag list (unblocks both). [SPEC] (1) constraint table populates from Constraint/margin/* + Constraint/viol/*; (2) reward-decomp block emits per-term final-window mean so a report cites e.g. 'Reward/att_rp 5.38->4.50' from code-exec not memory. [STATUS] proposed.

---

## Update (2026-06-06T09:46:07.076418)

[STATUS] implemented (2026-06-06). Both halves of the CORRECTION spec are now done.

(a) Constraint naming — FIXED in .omx/profile/analyze_training.py (commit f391aa6, this workspace repo). New _discover_constraint_names() unions legacy Constraint/cost_return_* with this repo's Constraint/margin/<name> + Constraint/viol/<name>; _constraint_margin()/_constraint_violation() read margin/viol (margin<0 == OVER) or derive from cost_return-d_k for back-compat. format_tier2, the [CONFIG] constraints= line (was the literal 'constraints=0' source at ~L1609), the panel builder, and _find_diverging_costs all route through it. VERIFIED on the real teacher run trpo_main_teacher_260525_232805: 'constraints=10 (from TB: arm_joint_vel, arm_torque, attitude, cumul_yaw, joint1_pos, manipulability, rp_rate, rp_vel_settling, thruster_util, yaw_rate)' with a full TIER2 table (attitude m=1.00 viol=-1.00, yaw_rate m=8.39, ...). 7 headless tests in test_constraint_naming.py.

(b) Reward 8-term scalars — DELIVERED as the 'cleaner' option the spec named: new 'omx reduce tb-final' verb in omx-core (commit 76d2eca on branch feat/engine-output-verify, NOT yet merged to omx main). Pure fn final_window_means(series, tags, window=200) returns named final-window means for any tag list; an absent tag LOUD-fails (lists available) rather than returning 0. VERIFIED end-to-end: 'omx reduce tb-final --tag Reward/att_rp ... --tag Reward/total' on the teacher TB returns att_rp=5.3395, lin_vel=1.8920, yaw_vel=1.0917, torque=-0.0883, thruster=-0.0920, smoothness=-0.1248, bias=-0.0851, total=7.9330 — matching the raw-TB cross-check exactly. A report now cites reward terms from code-exec, not memory.

Also fixed: the skill-side guard (exp-analyze SKILL.md, commit 0de5710) so an engine's empty/0 cell is cross-checked against raw TB before being asserted as 'no data' — see don_t_trust_an_engine_s_empty_zero_output. omx-core 418 passed/1 skipped, ruff clean.
