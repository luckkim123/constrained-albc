---
title: "Ranking caveat: `Policy/clip_fraction` is NOT the largest relative training-side"
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

# Ranking caveat: `Policy/clip_fraction` is NOT the largest relative training-side

Ranking caveat: `Policy/clip_fraction` is NOT the largest relative training-side move — an exhaustive scan of all 136 common TB tags puts `Term/too_fast_ang` (+243%), `Dynamics/joint/effort_sat` (+229%), `Dynamics/joint/vel_sat` (+152%) and `Encoder/z_mean` (+113%) above it. Those four all sit on near-zero bases (e.g. 0.00104 vs 0.00030), so their percentages are arithmetically large but physically small; clip_fraction and the critic losses are the largest moves with a meaningful absolute base. No single "largest hit" claim is made here.

[EVIDENCE: exhaustive last-200-iter mean comparison over all 136 TB scalar tags common to both runs, excluding DORAEMON/Episode/Curriculum/Metrics prefixes]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
