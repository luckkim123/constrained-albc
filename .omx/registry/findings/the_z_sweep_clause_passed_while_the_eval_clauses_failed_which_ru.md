---
title: "The z_sweep clause PASSED while the eval clauses failed, which rules out the obv"
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

# The z_sweep clause PASSED while the eval clauses failed, which rules out the obv

The z_sweep clause PASSED while the eval clauses failed, which rules out the obvious alternative explanation: the encoder did not lose the ability to represent its inputs, it lost an input worth representing.

[EVIDENCE: `encoder_tools.py sweep` on model_4999.pt of both runs — A4 minimum active-dim count 3/9 (Payload CoG Z), anchor has a strictly worse case at 0/9 (Joint Stiffness)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
