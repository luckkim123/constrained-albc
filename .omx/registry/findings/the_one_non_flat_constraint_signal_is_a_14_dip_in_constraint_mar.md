---
title: "The one non-flat constraint signal is a -14% dip in `Constraint/margin/thruster_"
tags: ["auto-captured"]
created: 2026-08-14T08:13:07.299190
updated: 2026-08-14T08:13:07.299190
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The one non-flat constraint signal is a -14% dip in `Constraint/margin/thruster_

The one non-flat constraint signal is a -14% dip in `Constraint/margin/thruster_util` confined to the 7250-8000 window — exactly the saturation boundary — which fully recovers by 8750. It precedes the eval regression rather than accompanying it, so it does not explain the 9000 excursion.

[EVIDENCE: table above; `DORAEMON/kl_step` reaches 0 in the same window]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
