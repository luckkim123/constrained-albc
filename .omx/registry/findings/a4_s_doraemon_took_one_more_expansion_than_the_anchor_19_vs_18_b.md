---
title: "A4's DORAEMON took ONE MORE expansion than the anchor (19 vs 18): both runs take"
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

# A4's DORAEMON took ONE MORE expansion than the anchor (19 vs 18): both runs take

A4's DORAEMON took ONE MORE expansion than the anchor (19 vs 18): both runs take every expansion at exactly the 0.12 KL cap, but A4's gate additionally fired at iter 250, where the anchor's first expansion was at 500. A4 therefore trained in, and was examined on, a WIDER DR box.

[EVIDENCE: TB DORAEMON/kl_step nonzero steps — A4 at 250..4750 (19 values, all 0.12), anchor at 500..4750 (18 values, all 0.12); terminal Beta differs from the anchor by max 3.44e-01 (dist_a) / 1.29e+00 (dist_b)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
