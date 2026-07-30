---
title: "Yaw is the weakest fault-robustness axis and sits modestly below Arm A, but this"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Yaw is the weakest fault-robustness axis and sits modestly below Arm A, but this

Yaw is the weakest fault-robustness axis and sits modestly below Arm A, but this is the pre-existing signature of the yaw channel rather than a composition cost, because Arm A itself fell below 5x on yaw at `none` while being recorded as the 5-12x attitude win.

[EVIDENCE: E-int yaw advantage none 3.01x / medium 5.30x / hard 6.32x vs Arm A yaw 4.00x / 6.77x / 6.72x (anchor deltas 0.092/0.149/0.168 over Arm A 0.023/0.022/0.025); proposal line 17 grounds D-b on attitude, not yaw]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
