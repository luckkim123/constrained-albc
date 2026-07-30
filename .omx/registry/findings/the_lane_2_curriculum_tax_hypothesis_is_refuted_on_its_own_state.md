---
title: "The Lane-2 curriculum-tax hypothesis is refuted on its own stated metric: adding"
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

# The Lane-2 curriculum-tax hypothesis is refuted on its own stated metric: adding

The Lane-2 curriculum-tax hypothesis is refuted on its own stated metric: adding the static band on top of fault DR did not slow the 21-dim curriculum, which reached statistically the same fault_severity as fault DR alone, and curriculum success recovered to the anchor level rather than staying at the band-only run depressed value.

[EVIDENCE: `DORAEMON/mean/fault_severity` last logged 0.0770 (7.70% of range) for E-int vs Arm A 0.0771 (7.71%); `doraemon_success_rate` 0.8155 vs anchor 0.8139 and B0c 0.73; `DORAEMON/ess_ratio` 0.7731 vs anchor 0.7648]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
