---
title: "The m4-dead injector genuinely bit in every measured cell, so the advantage is n"
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

# The m4-dead injector genuinely bit in every measured cell, so the advantage is n

The m4-dead injector genuinely bit in every measured cell, so the advantage is not a silent no-op.

[EVIDENCE: per-level npz — `fault_thruster_4` == 0 in 64/64 envs and `fault_thruster_{0,1,2,3,5}` == 1.0 at none/soft/medium/hard; the healthy arm records scalar provenance `fault_injection` == False and the dead arm == True]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
