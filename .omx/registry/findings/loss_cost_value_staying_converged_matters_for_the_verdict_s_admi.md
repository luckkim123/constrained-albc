---
title: "`Loss/cost_value` staying converged matters for the verdict's admissibility — a "
tags: ["auto-captured", "trpo_ftc1sevinit_s30_260729_105510"]
created: 2026-07-29T08:24:32.720137
updated: 2026-07-29T08:24:32.720137
sources: ["experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `Loss/cost_value` staying converged matters for the verdict's admissibility — a 

`Loss/cost_value` staying converged matters for the verdict's admissibility — a non-converging cost critic would make the constraint advantages noise and IPO unreliable, which would confound any constraint-side reading below.

[EVIDENCE: `metrics.yaml` cost_value rationale ("if it does not converge, constraint advantages are noise and IPO misbehaves"); both values are order-1 and stable across the final 200 iters]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
