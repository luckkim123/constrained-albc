---
title: "The hard/OOD dispersion is a genuine heavy tail, confirmed on the raw per-env da"
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

# The hard/OOD dispersion is a genuine heavy tail, confirmed on the raw per-env da

The hard/OOD dispersion is a genuine heavy tail, confirmed on the raw per-env data (not inferred from CV): the worst env's steady roll error is 23× (hard) / 29× (ood) the median env's, and the top 6 of 64 envs (~9%) hold ~half the total error, while the median env stays ~0.2°.

[EVIDENCE: data_none/medium/hard/ood.npz per-env median |error_roll| — max/median 5.7x(none)->20.5x(medium)->23.2x(hard)->29.2x(ood); top-6/64 share 27%(none)->49%(hard)->51%(ood)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

The hard/OOD dispersion is a genuine heavy tail, confirmed on the raw per-env data (not inferred from CV): the worst env's steady roll error is 23× (hard) / 29× (ood) the median env's, and the top 6 of 64 envs (~9%) hold ~half the total error, while the median env stays ~0.2°.

[EVIDENCE: data_none/medium/hard/ood.npz per-env median |error_roll| — max/median 5.7x(none)->20.5x(medium)->23.2x(hard)->29.2x(ood); top-6/64 share 27%(none)->49%(hard)->51%(ood)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
