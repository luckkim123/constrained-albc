---
title: "The trajectory variance bands widen monotonically with DR (hard/OOD widest) — th"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The trajectory variance bands widen monotonically with DR (hard/OOD widest) — th

The trajectory variance bands widen monotonically with DR (hard/OOD widest) — the visual signature of the §8.1 env-to-env heavy-tail — and control-action magnitude scales none<soft<medium<hard (more effort under harder physics).

[EVIDENCE: summary.json ss_error_std rises with DR — roll 0.143(none)->1.282(hard), att_norm 0.124->1.538; plots/traj_error.png corroborates the band-widening + action-magnitude ordering none<soft<medium<hard]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

The trajectory variance bands widen monotonically with DR (hard/OOD widest) — the visual signature of the §8.1 env-to-env heavy-tail — and control-action magnitude scales none<soft<medium<hard (more effort under harder physics).

[EVIDENCE: summary.json ss_error_std rises with DR — roll 0.143(none)->1.282(hard), att_norm 0.124->1.538; plots/traj_error.png corroborates the band-widening + action-magnitude ordering none<soft<medium<hard]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
