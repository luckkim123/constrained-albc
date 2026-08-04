---
title: "The correct baseline eval is `static_260804_145821`, not the campaign's original"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-04T07:04:05.217247
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The correct baseline eval is `static_260804_145821`, not the campaign's original

The correct baseline eval is `static_260804_145821`, not the campaign's originally-recorded `static_260804_130704` — the two were produced by DIFFERENT instruments, and the older one is pre-fix.

[EVIDENCE: commit `9eac3a8` ("Fix cross-run eval pairing: per-level reseed in run_static") landed 15:09; eval `static_260804_145821` ran 14:58-15:07 with that hunk as working-tree state, `static_260804_130704` ran 13:07-13:15 before it. The empirical discriminator is the soft-level draw comparison against X1, which ran on the committed post-fix HEAD: X1 vs `145821` = 24/24 identical, X1 vs `130704` = 1/24]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
