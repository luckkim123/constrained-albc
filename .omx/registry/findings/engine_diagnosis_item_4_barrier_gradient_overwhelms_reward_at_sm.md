---
title: "Engine `[DIAGNOSIS]` item 4 (\"barrier gradient overwhelms reward at small margin"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Engine `[DIAGNOSIS]` item 4 ("barrier gradient overwhelms reward at small margin

Engine `[DIAGNOSIS]` item 4 ("barrier gradient overwhelms reward at small margins; consider increasing barrier_t") should NOT be acted on: it is the magnitude-only generic heuristic this workspace has already characterised, and every paired cross-check clears it — the barrier's last value is -0.1278 against a reward total of 9.30 (1.4%), all ten margins are satisfied, and the line search accepted the step.

[EVIDENCE: engine `[TIER 2]` `barrier_penalty last=-0.1278 spikes(>0.01)=1 max=0.140` vs `[TIER 3] Rewards total=9.30`; all 10 `viol` negative; wiki `engine_generic_flags_entropy_collapse_barrier_spike_reward_plate`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
