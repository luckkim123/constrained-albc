---
title: "The actor's BEHAVIOUR did change, however: `Policy/clip_fraction` nearly doubled"
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

# The actor's BEHAVIOUR did change, however: `Policy/clip_fraction` nearly doubled

The actor's BEHAVIOUR did change, however: `Policy/clip_fraction` nearly doubled (0.0151 vs 0.0078, +94.9%), meaning A4's policy drives actions into the [-1,1] bound about twice as often. This is the actor-side counterpart of the `thruster_util` margin collapse (6.14 -> 2.77) and the deeper thruster reward penalty (-25.2%) reported below — the same behaviour seen through three independent instruments.

[EVIDENCE: TB last-200-iter mean of Policy/clip_fraction (defined at `constraint_trpo.py:436` as the fraction of actions saturating the action bound); `analyze_training.py` TIER 2 thruster_util margin; TB Reward/thruster]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
