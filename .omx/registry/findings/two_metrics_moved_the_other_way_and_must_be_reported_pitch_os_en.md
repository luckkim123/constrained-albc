---
title: "Two metrics moved the OTHER way and must be reported: pitch `os_env_mean` improv"
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

# Two metrics moved the OTHER way and must be reported: pitch `os_env_mean` improv

Two metrics moved the OTHER way and must be reported: pitch `os_env_mean` improved 9-29% at every level, and yaw `os_env_mean` at `none` essentially vanished (0.013 vs 3.593). A4 overshoots less on those channels while tracking far worse — consistent with a slower, less confident policy rather than a better one, since yaw `ss_error` simultaneously worsened 70%.

[EVIDENCE: summary.json pitch/yaw os_env_mean vs ss_error across all levels]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
