---
title: "The DR distribution's own entropy independently confirms the width gap: P-B1's s"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The DR distribution's own entropy independently confirms the width gap: P-B1's s

The DR distribution's own entropy independently confirms the width gap: P-B1's sampling distribution is markedly higher-entropy than the reference's, and the curriculum has settled (entropy_before == entropy_after on both runs, i.e. the final logged step applied no further widening).

[EVIDENCE: TB final scalars: `DORAEMON/entropy_before` -22.7017 (P-B1) vs -29.2431 (REF); `DORAEMON/entropy_after` -22.7017 vs -29.2431 (identical to `entropy_before` on each run)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The DR distribution's own entropy independently confirms the width gap: P-B1's sampling distribution is markedly higher-entropy than the reference's, and the curriculum has settled (entropy_before == entropy_after on both runs, i.e. the final logged step applied no further widening).

[EVIDENCE: TB final scalars: `DORAEMON/entropy_before` -22.7017 (P-B1) vs -29.2431 (REF); `DORAEMON/entropy_after` -22.7017 vs -29.2431 (identical to `entropy_before` on each run)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
