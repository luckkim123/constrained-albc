---
title: "eval static cross-run pairing requires per-level reseed"
tags: []
created: 2026-08-04T06:11:01.239350
updated: 2026-08-04T06:11:01.239350
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# eval static cross-run pairing requires per-level reseed

Cross-run paired comparison via eval.py static was silently UNPAIRED before 2026-08-04: --doraemon-dr-from pins only the DR distribution, while per-env draws come from the global torch RNG, whose stream offset depends on how much weight-init the policy build consumes (72D vs 76D actor, student GRU differ) - 23/24 dr_* keys differed at soft/medium/hard. Fix (commit 9eac3a8): per-level torch.manual_seed(seed + level_index) in run_static right before each level rollout, mirroring segmented mode. Verified 4-way (E-int / obs76fault / C3 / gen-2 evals static_260804_14*): 24/24 dr/fault keys elementwise identical at all 4 DR levels. Consequence: the paired precondition of DECISION_FLOORS is now actually satisfiable for teacher-vs-student and cross-teacher comparisons - any paired verdict computed from evals BEFORE this fix (different builds) is unpaired and must be re-run, not reused. Protocol: same --seed, same --doraemon-dr-from, eval.py at or after 9eac3a8.
