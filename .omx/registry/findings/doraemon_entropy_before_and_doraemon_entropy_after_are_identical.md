---
title: "`DORAEMON/entropy_before` and `DORAEMON/entropy_after` are identical to each oth"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-23T07:42:43.943074
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# `DORAEMON/entropy_before` and `DORAEMON/entropy_after` are identical to each oth

`DORAEMON/entropy_before` and `DORAEMON/entropy_after` are identical to each other and across both runs (-22.7017), confirming the logged entropy pair is a static readout in this config rather than a per-update measurement — it cannot be used to judge curriculum movement.

[EVIDENCE: TB last-200-iter means, DORAEMON/entropy_before == DORAEMON/entropy_after == -22.7017 for A3 and anchor alike]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md

---

## Update (2026-07-23T07:42:43.943074)

2026-07-23 curation: attempted recategorize session-log -> debugging (code-level TB logging quirk: DORAEMON/entropy_before == entropy_after always, a static readout not a per-update value; true for the whole config).
