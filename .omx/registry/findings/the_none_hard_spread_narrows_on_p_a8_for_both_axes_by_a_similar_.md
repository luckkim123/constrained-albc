---
title: "The none->hard spread NARROWS on P-A8 for both axes by a similar magnitude (roll"
tags: ["auto-captured", "trpo_perflb200-moreiters_260715_195227"]
created: 2026-07-15T19:00:13.758977
updated: 2026-07-16T07:19:42.517477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The none->hard spread NARROWS on P-A8 for both axes by a similar magnitude (roll

The none->hard spread NARROWS on P-A8 for both axes by a similar magnitude (roll 4.2x->3.3x, pitch 5.9x->4.2x), but this metric is confounded by the run-relative-DR issue above — P-A8's `hard` box samples fully-uniform-ceiling physics while the reference's `hard` box was mid-expansion, so the spread comparison mixes a genuine generalization signal with a DR-width difference.

[EVIDENCE: eval/static_260716_034515 vs eval/static_260715_141532 summary.json, none vs hard, roll+pitch]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md

---

## Update (2026-07-16T07:19:42.517477)

The none->hard spread NARROWS on P-A8 for both axes by a similar magnitude (roll 4.2x->3.3x, pitch 5.9x->4.2x), but this metric is confounded by the run-relative-DR issue above — P-A8's `hard` box samples fully-uniform-ceiling physics while the reference's `hard` box was mid-expansion, so the spread comparison mixes a genuine generalization signal with a DR-width difference.

[EVIDENCE: eval/static_260716_034515 vs eval/static_260715_141532 summary.json, none vs hard, roll+pitch]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md
