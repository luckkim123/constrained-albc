---
title: "engine-gap: analyze_training.py emits no reward 8-term decomposition scalars"
tags: ["engine-gap", "reward-decomposition", "analyze_training", "constraint-naming", "CORRECTION", "implemented", "constraint", "reward", "naming", "verification", "anti-pattern", "tb-tags", "absorbed-into-skill", "debugging"]
created: 2026-06-06T09:15:01.438112
updated: 2026-07-23T07:42:44.558584
sources: ["diagnose-20260606-180317", "diagnose-20260606-183657"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
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

---

## Merged from engine_gap_confirmed_analyze_training_py_constraint_reward_prefi.md (2026-07-06T02:16:31.477399)

# engine-gap CONFIRMED: analyze_training.py constraint+reward prefix mismatch (code lines)

[ENGINE-GAP] analyze_training.py reports constraints=0 and no reward decomposition because of TWO hardcoded-prefix mismatches, re-confirmed this session by code line + EventAccumulator dump (134 TB tags). [WHERE] .omx/profile/analyze_training.py (a copy of the ~/oh-my-experiments reference adapter -- fix the source, sync the copy). Constraint: line 313 'if not tag.startswith("Constraint/cost_return_")' + lines 384/385 barrier_margin_/d_k_ -- but TB logs Constraint/margin/* (11) + Constraint/viol/* (10) + Constraint/barrier_penalty. Reward: line 761 scans 'Episode_Reward/*' and line 884 SKIP_PREFIXES includes 'Episode_Reward/' -- but TB logs Reward/* (8 terms: att_rp/lin_vel/yaw_vel/torque/thruster/smoothness/bias/total). [SPEC] generalize constraint discovery to also scan Constraint/margin/* + Constraint/viol/* (keep cost_return_ working); add a reward block emitting Reward/* 8-term final-window means in TIER3. [EVIDENCE] teacher TB has all 21 Constraint/ + 8 Reward/ tags; engine printed constraints=0 and no reward table. [STATUS] proposed (a separate session is implementing; metrics.yaml is already correct and needs NO change). cf don-t-trust-an-engine-s-empty-zero-output-cross-check-the-raw-tb engine-gap-analyze-training-py-emits-no-reward-8-term-decomposit.


---

## Merged from don_t_trust_an_engine_s_empty_zero_output_cross_check_the_raw_tb.md (2026-07-06T02:16:31.477399)

# DON'T trust an engine's empty/zero output — cross-check the raw TB tag set first

Hard-won 2026-06-06: running analyze_training.py is NOT the same as USING it. The engine printed 'constraints=0, budgets=()' and an EMPTY constraint table; I copied that into the report as truth and even wrote a false engine-gap ('reward 8-term decomposition unavailable'). Both were WRONG. EventAccumulator on the SAME teacher TB showed 134 scalar tags: Reward 8 (att_rp/lin_vel/yaw_vel/torque/thruster/smoothness/bias/total ALL present), Constraint 21 (margin/* + viol/* + barrier_penalty), DORAEMON 41, Track 14, Dynamics 9, Term 6. The engine's table was empty only because it scans for Constraint/cost_return_* but this workspace logs Constraint/margin/* + Constraint/viol/* (a naming mismatch). LESSON (rule 03 'verify implementation not name', 'no premature assertion'): when an analysis engine reports zero/empty for a metric group, do NOT conclude 'data absent' — first dump the raw tag set (EventAccumulator: ea.Tags()['scalars']) and confirm whether the data exists but the tool's prefix/name assumption missed it. An empty engine cell is a hypothesis ('tool found nothing'), not a finding ('nothing there'). Procedure: (1) engine run -> (2) if any group reads 0/empty, list raw TB prefixes -> (3) if tags exist, extract them by code-exec AND file an engine-gap for the naming mismatch -> (4) only assert 'absent' after the raw dump confirms it. Re-visit: diagnose-20260606-180317 (the report this caught was still too thin; 3rd pass owed).

---

## Update (2026-06-06T09:46:28.288343)

[ABSORBED INTO SKILL 2026-06-06] This lesson is now a hard step in the exp-analyze skill, so future sessions get it by default rather than re-learning it. exp-analyze SKILL.md (omx commit 0de5710, branch feat/engine-output-verify) gained a 'Verify the engine's output — an empty cell is a HYPOTHESIS, not a fact' section right after the run-the-engine MUST: when a group reads 0/empty, dump ea.Tags()['scalars'], grep the prefix; if the tags exist, extract via 'omx reduce tb-final' + file an engine-gap, and only genuinely-absent tags justify 'no data'. The completeness gate was also tightened: 'the engine reported it empty' is NOT a valid reason to mark a group N/A — it must pass this cross-check first. The underlying naming mismatch that triggered this lesson is itself now FIXED in the engine (see engine_gap_analyze_training_py_emits_no_reward_8_term_decomposit, [STATUS] implemented): analyze_training.py discovers Constraint/margin/* + viol/* and prints constraints=10 on the teacher run. So this anti-pattern is closed on both ends — the engine no longer mis-scans, and the skill cross-checks if any engine ever does again.

---

## Update (2026-07-23T07:42:44.558584)

2026-07-23 curation: status set to resolved -- body confirms implemented 2026-06-06 and absorbed into the exp-analyze skill; sibling engine-gap pages use this field.
