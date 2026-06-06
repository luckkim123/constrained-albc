---
title: "exp-analyze MUST run analyze_training.py for training-side diagnosis"
tags: ["analyze", "engine", "MUST", "exp-analyze", "training-dynamics", "adapter", "SS-error", "attitude", "DR"]
created: 2026-06-06T09:21:55.402055
updated: 2026-06-06T09:21:55.402055
sources: ["diagnose-20260606-173330", "omx-engine-skip-failure-fix-2026-06-06"]
links: ["training_log_analysis_engine_reference_adapter.md"]
category: decision
confidence: high
schemaVersion: 1
---

# exp-analyze MUST run analyze_training.py for training-side diagnosis

DECISION: when analyzing a training run, exp-analyze MUST run the profile's training-log engine .omx/profile/analyze_training.py (--tier 3 --deep) and ground the report in its [DIAGNOSIS]/[TREND]/changepoint/plateau/regime output. Hand-extracting TB final scalars INSTEAD of running the engine is forbidden.

WHY (evidence): on 2026-06-06 a dr-harder report (analysis diagnose-20260606-173330) was written by reading TB final values by hand and SKIPPING analyze_training.py (1620 lines). It covered ~29/51 vocab tokens yet cited ZERO engine diagnosis, so it missed the engine's time-series findings that CANNOT be reconstructed from end values: phase warmup->plateau (plateau since ~10%), PELT changepoints (iter 434, 3324; cross-metric iter 250 reward-up/entropy-down), HMM regime, lead-lag (lin_vel->mean_reward). Verified by actually running it: python3 .omx/profile/analyze_training.py <run>/train --tier 3 --deep on trpo_main_teacher_260525_232805.

HOW TO FIND THE ENGINE (this is why the failure happened): a conclusion-only wiki query ('SS error attitude DR') does NOT surface the engine how-to page training_log_analysis_engine_reference_adapter.md (its tags adapter/analyze/engine share no vocabulary with a symptom query). So query for TOOLING first (pass A: 'analysis engine reference adapter how to analyze'), THEN for conclusions (pass B). See [[training-log-analysis-engine-reference-adapter]].

ENFORCEMENT: omx report-coverage (added 2026-06-06) reads profile groups + engine_markers and loud-fails a report that skipped a diagnostic group or cited no engine marker. The exp-analyze SKILL.md now (a) MUSTs the engine run before analysis, (b) queries tooling in a first pass, (c) runs report-coverage in the When-done gate.
