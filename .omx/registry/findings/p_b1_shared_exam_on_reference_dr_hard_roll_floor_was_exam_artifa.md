---
title: "P-B1 shared-exam on reference DR: hard-roll floor was exam artifact, transient peak trade survives (H2/e2)"
tags: ["doraemon-dr-from", "shared-exam", "bias-ema", "heavy-tail", "comparability", "e2"]
created: 2026-07-16T07:48:02.124587
updated: 2026-07-16T07:48:02.124587
sources: ["diagnose-20260716-164016"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# P-B1 shared-exam on reference DR: hard-roll floor was exam artifact, transient peak trade survives (H2/e2)

First shared-exam eval in the workspace (eval static_260716_160156): P-B1 (trpo_biasema_260715_142543) graded on the REFERENCE trpo_baseline_260714_192020 learned DR via --doraemon-dr-from. This IS the 'NEW FIRST DEMONSTRATION' the comparability lead needed (the e4-motivated probe was retired by the user's e4 rejection).

ANCHOR VERIFIED (stronger than the none sanity gate, which is anchor-invariant): data_hard.npz dr_* box (23 keys) matches the reference eval EXACTLY (mismatch 0.00000) and differs from P-B1's own-DR eval static_260715_192701 (7.90261). Both policies faced identical per-env physics.

VERDICT H2 / e2 signature: P-B1's apparent hard-roll regression SPLITS. The DC-bias floor part was an exam artifact -- on the reference anchor P-B1 scores hard roll ss_error 0.5950 vs REF 0.7167 (17% BETTER, not the 0.9277 its self-exam reported). The transient-peak part is real -- hard roll n_gt20 8.667 exceeds REF 6.667, the ONLY cell family P-B1 loses at any DR level. P-B1 wins every ss_error cell (up to -67.7% at none) and every tail cell except hard. Survival 100% all levels both policies.

BINDING SCOPE LIMIT (from cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov): common exam removes the MEASUREMENT confound only. P-B1's learned DR is wider on 20/20 params (variance ratio mean 2.23x, median 1.75x; widest: payload_cog_offset_xy_u 5.80x, obs_noise_scale 4.48x, ocean_current 3.69x; DORAEMON/entropy_before -22.70 vs -29.24 independently confirms). So 'trade is real' = it survives a fair exam; it is NOT yet attributed to the bias-EMA observation. Separating obs-effect from training-DR-effect needs the curriculum-replay arm (--replay_curriculum). Attribute to the adopted-config bundle, never bias_ema alone. Full analysis: report diagnose-20260716-164016.
