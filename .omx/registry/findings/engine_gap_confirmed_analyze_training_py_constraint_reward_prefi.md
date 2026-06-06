---
title: "engine-gap CONFIRMED: analyze_training.py constraint+reward prefix mismatch (code lines)"
tags: ["engine-gap", "analyze_training", "constraint", "reward", "naming"]
created: 2026-06-06T09:44:05.218907
updated: 2026-06-06T09:44:05.218907
sources: ["diagnose-20260606-183657"]
links: ["don_t_trust_an_engine_s_empty_zero_output_cross_check_the_raw_tb.md", "engine_gap_analyze_training_py_emits_no_reward_8_term_decomposit.md"]
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap CONFIRMED: analyze_training.py constraint+reward prefix mismatch (code lines)

[ENGINE-GAP] analyze_training.py reports constraints=0 and no reward decomposition because of TWO hardcoded-prefix mismatches, re-confirmed this session by code line + EventAccumulator dump (134 TB tags). [WHERE] .omx/profile/analyze_training.py (a copy of the ~/oh-my-experiments reference adapter -- fix the source, sync the copy). Constraint: line 313 'if not tag.startswith("Constraint/cost_return_")' + lines 384/385 barrier_margin_/d_k_ -- but TB logs Constraint/margin/* (11) + Constraint/viol/* (10) + Constraint/barrier_penalty. Reward: line 761 scans 'Episode_Reward/*' and line 884 SKIP_PREFIXES includes 'Episode_Reward/' -- but TB logs Reward/* (8 terms: att_rp/lin_vel/yaw_vel/torque/thruster/smoothness/bias/total). [SPEC] generalize constraint discovery to also scan Constraint/margin/* + Constraint/viol/* (keep cost_return_ working); add a reward block emitting Reward/* 8-term final-window means in TIER3. [EVIDENCE] teacher TB has all 21 Constraint/ + 8 Reward/ tags; engine printed constraints=0 and no reward table. [STATUS] proposed (a separate session is implementing; metrics.yaml is already correct and needs NO change). cf [[don-t-trust-an-engine-s-empty-zero-output-cross-check-the-raw-tb]] [[engine-gap-analyze-training-py-emits-no-reward-8-term-decomposit]].
