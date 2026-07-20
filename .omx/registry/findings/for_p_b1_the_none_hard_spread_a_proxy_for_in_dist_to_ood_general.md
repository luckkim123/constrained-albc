---
title: "For P-B1, the none->hard spread (a proxy for in-dist-to-OOD generalization gap, "
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-16T07:19:42.517477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# For P-B1, the none->hard spread (a proxy for in-dist-to-OOD generalization gap, 

For P-B1, the none->hard spread (a proxy for in-dist-to-OOD generalization gap, since `ood` is absent this eval) widens more than the reference's: roll ss_error grows 0.215->0.928 (4.3x) for P-B1 vs 0.664->0.717 (1.08x) for the reference. This is consistent with the DR-anatomy confound (P-B1's own `hard` box is objectively wider/harder than the reference's `hard` box), not necessarily a generalization regression under MATCHED difficulty — the metric is not separable from the DR-width confound with this eval alone.

[EVIDENCE: summary.json none vs hard, both runs, roll axis]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md

---

## Update (2026-07-16T07:19:42.517477)

For P-B1, the none->hard spread (a proxy for in-dist-to-OOD generalization gap, since `ood` is absent this eval) widens more than the reference's: roll ss_error grows 0.215->0.928 (4.3x) for P-B1 vs 0.664->0.717 (1.08x) for the reference. This is consistent with the DR-anatomy confound (P-B1's own `hard` box is objectively wider/harder than the reference's `hard` box), not necessarily a generalization regression under MATCHED difficulty — the metric is not separable from the DR-width confound with this eval alone.

[EVIDENCE: summary.json none vs hard, both runs, roll axis]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
