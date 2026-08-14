---
title: "The profile's `doraemon` group declares `doraemon_success_rate`, which is absent"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The profile's `doraemon` group declares `doraemon_success_rate`, which is absent

The profile's `doraemon` group declares `doraemon_success_rate`, which is absent from every event file; the real tag is `DORAEMON/success_rate`.

[EVIDENCE: by-name check over both runs' 138 scalar tags — `doraemon_success_rate` ABSENT in both, `DORAEMON/success_rate` present with final-50 means 0.81044 and 0.91889]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
