---
title: "The sample (median-attitude) env hugs the mean trajectory at every DR level — no"
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

# The sample (median-attitude) env hugs the mean trajectory at every DR level — no

The sample (median-attitude) env hugs the mean trajectory at every DR level — no axis-decorrelation: the median-att env is also typical on the trajectory, the healthy-baseline pattern (contrast with intervention runs where the sample line diverges from the mean, signalling axes trained independently). So the §8.1 heavy tail is a per-env DC-offset spread, not the policy tracking axes out of step.

[EVIDENCE: plots/traj_attitude.png — sample env-14 dashed line overlaps the actual-mean solid line for roll and pitch at none/soft/medium/hard/ood]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

The sample (median-attitude) env hugs the mean trajectory at every DR level — no axis-decorrelation: the median-att env is also typical on the trajectory, the healthy-baseline pattern (contrast with intervention runs where the sample line diverges from the mean, signalling axes trained independently). So the §8.1 heavy tail is a per-env DC-offset spread, not the policy tracking axes out of step.

[EVIDENCE: plots/traj_attitude.png — sample env-14 dashed line overlaps the actual-mean solid line for roll and pitch at none/soft/medium/hard/ood]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
