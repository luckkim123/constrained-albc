---
title: "The encoder is alive and unsaturated in both runs, so the fault-rejection loss i"
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

# The encoder is alive and unsaturated in both runs, so the fault-rejection loss i

The encoder is alive and unsaturated in both runs, so the fault-rejection loss is not an encoder-collapse artifact.

[EVIDENCE: `tb_final.py --window 200` against the `metrics.yaml` thresholds z_std<0.1 LOW, |z|>0.95 SAT, grad<1e-4 DEAD]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
