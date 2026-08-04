---
title: "eval static cross-run pairing requires per-level reseed"
tags: ["eval", "pairing", "reseed", "instrument", "provenance"]
created: 2026-08-04T06:11:01.239350
updated: 2026-08-04T07:04:39.486139
sources: ["diagnose-20260804-154122"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# eval static cross-run pairing requires per-level reseed

Cross-run paired comparison via eval.py static was silently UNPAIRED before 2026-08-04: --doraemon-dr-from pins only the DR distribution, while per-env draws come from the global torch RNG, whose stream offset depends on how much weight-init the policy build consumes (72D vs 76D actor, student GRU differ) - 23/24 dr_* keys differed at soft/medium/hard. Fix (commit 9eac3a8): per-level torch.manual_seed(seed + level_index) in run_static right before each level rollout, mirroring segmented mode. Verified 4-way (E-int / obs76fault / C3 / gen-2 evals static_260804_14*): 24/24 dr/fault keys elementwise identical at all 4 DR levels. Consequence: the paired precondition of DECISION_FLOORS is now actually satisfiable for teacher-vs-student and cross-teacher comparisons - any paired verdict computed from evals BEFORE this fix (different builds) is unpaired and must be re-run, not reused. Protocol: same --seed, same --doraemon-dr-from, eval.py at or after 9eac3a8.

---

## Update (2026-08-04T07:04:39.486139)

HOW TO DATE AN AMBIGUOUS EVAL (added 2026-08-04 from X1 analysis). An eval that ran while the reseed hunk sat in the WORKING TREE, before commit 9eac3a8 was made, records a clean pre-fix git sha and cannot be classified from mtime or sha alone. Do not reason from timestamps -- classify it empirically against a KNOWN post-fix eval: compare the dr_* / fault arrays at the SOFT level (not none). A post-fix eval matches 24/24; a pre-fix eval matches 1/24. The none level cannot discriminate because the reseed uses seed + level_index, so index 0 reproduces the old single seeding and BOTH classes match 24/24 there. Worked example: Phase E eval static_260804_145821 (ran 14:58-15:07, before the 15:09 commit) was proven post-fix this way against X1 eval static_260804_152454, which ran on the committed HEAD -- 24/24 at soft vs 1/24 for the older static_260804_130704. That saved a redundant 9-minute re-eval AND, more importantly, corrected the baseline: the campaign-recorded Phase E hard aggregate latent R2 of -0.078 comes from the PRE-fix eval; the paired value is -0.1044.
