---
title: "Despite the weaker policy, A4 expanded MORE (19 vs 18) because its gate fired at"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Despite the weaker policy, A4 expanded MORE (19 vs 18) because its gate fired at

Despite the weaker policy, A4 expanded MORE (19 vs 18) because its gate fired at iter 250 where the anchor's did not — an early-training difference, before the policy quality gap opened. The extra expansion is therefore an artifact of early dynamics, not a reward for competence.

[EVIDENCE: TB DORAEMON/kl_step step list — A4 first nonzero at 250, anchor at 500; success_rate at those iterations]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
