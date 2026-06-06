---
title: "DON'T trust an engine's empty/zero output — cross-check the raw TB tag set first"
tags: ["engine-gap", "verification", "analyze_training", "anti-pattern", "tb-tags", "absorbed-into-skill"]
created: 2026-06-06T09:20:27.469761
updated: 2026-06-06T09:46:28.288343
sources: ["diagnose-20260606-180317"]
links: []
category: debugging
confidence: high
schemaVersion: 1
---

# DON'T trust an engine's empty/zero output — cross-check the raw TB tag set first

Hard-won 2026-06-06: running analyze_training.py is NOT the same as USING it. The engine printed 'constraints=0, budgets=()' and an EMPTY constraint table; I copied that into the report as truth and even wrote a false engine-gap ('reward 8-term decomposition unavailable'). Both were WRONG. EventAccumulator on the SAME teacher TB showed 134 scalar tags: Reward 8 (att_rp/lin_vel/yaw_vel/torque/thruster/smoothness/bias/total ALL present), Constraint 21 (margin/* + viol/* + barrier_penalty), DORAEMON 41, Track 14, Dynamics 9, Term 6. The engine's table was empty only because it scans for Constraint/cost_return_* but this workspace logs Constraint/margin/* + Constraint/viol/* (a naming mismatch). LESSON (rule 03 'verify implementation not name', 'no premature assertion'): when an analysis engine reports zero/empty for a metric group, do NOT conclude 'data absent' — first dump the raw tag set (EventAccumulator: ea.Tags()['scalars']) and confirm whether the data exists but the tool's prefix/name assumption missed it. An empty engine cell is a hypothesis ('tool found nothing'), not a finding ('nothing there'). Procedure: (1) engine run -> (2) if any group reads 0/empty, list raw TB prefixes -> (3) if tags exist, extract them by code-exec AND file an engine-gap for the naming mismatch -> (4) only assert 'absent' after the raw dump confirms it. Re-visit: diagnose-20260606-180317 (the report this caught was still too thin; 3rd pass owed).

---

## Update (2026-06-06T09:46:28.288343)

[ABSORBED INTO SKILL 2026-06-06] This lesson is now a hard step in the exp-analyze skill, so future sessions get it by default rather than re-learning it. exp-analyze SKILL.md (omx commit 0de5710, branch feat/engine-output-verify) gained a 'Verify the engine's output — an empty cell is a HYPOTHESIS, not a fact' section right after the run-the-engine MUST: when a group reads 0/empty, dump ea.Tags()['scalars'], grep the prefix; if the tags exist, extract via 'omx reduce tb-final' + file an engine-gap, and only genuinely-absent tags justify 'no data'. The completeness gate was also tightened: 'the engine reported it empty' is NOT a valid reason to mark a group N/A — it must pass this cross-check first. The underlying naming mismatch that triggered this lesson is itself now FIXED in the engine (see engine_gap_analyze_training_py_emits_no_reward_8_term_decomposit, [STATUS] implemented): analyze_training.py discovers Constraint/margin/* + viol/* and prints constraints=10 on the teacher run. So this anti-pattern is closed on both ends — the engine no longer mis-scans, and the skill cross-checks if any engine ever does again.
