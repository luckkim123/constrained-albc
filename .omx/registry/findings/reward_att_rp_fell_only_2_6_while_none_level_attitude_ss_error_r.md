---
title: "`Reward/att_rp` fell only 2.6% while `none`-level attitude ss_error rose 74-95%,"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-23T07:42:43.780310
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# `Reward/att_rp` fell only 2.6% while `none`-level attitude ss_error rose 74-95%,

`Reward/att_rp` fell only 2.6% while `none`-level attitude ss_error rose 74-95%, so the training reward is a poor proxy for the deployed tracking quality of this intervention — the same lesson A2 produced from the opposite direction.

[EVIDENCE: TB Reward/att_rp 6.8793 vs 7.0624 against summary.json none/roll and none/pitch ss_error deltas]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md

---

## Update (2026-07-23T07:42:43.780310)

2026-07-23 curation: attempted recategorize session-log -> pattern (durable cross-run lesson: training Reward/att_rp is a poor proxy for eval attitude tracking quality; confirmed independently by A2 and A4 moving in opposite directions). No existing pattern page covers this reward-vs-eval proxy mismatch.
