---
title: "The anchor's encoder was using the dropped dims heavily, so this was live signal"
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

# The anchor's encoder was using the dropped dims heavily, so this was live signal

The anchor's encoder was using the dropped dims heavily, so this was live signal rather than dead weight the slimming would harmlessly shed. | dropped parameter | anchor active z dims | anchor max z range | |---|---|---| | Lin Vel U | 9/9 | 0.5951 | | Lin Vel V | 9/9 | 0.6852 | | Lin Vel W | 8/9 | 0.8563 | | Quad Damp Roll | 7/9 | 0.6693 |

[EVIDENCE: `encoder_tools.py sweep` on trpo_biasema_260715_142543/model_4999.pt, per-parameter active-dim counts at the range>0.05 threshold]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
