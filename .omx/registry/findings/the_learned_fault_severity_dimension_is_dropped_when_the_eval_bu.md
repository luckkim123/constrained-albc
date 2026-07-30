---
title: "The learned `fault_severity` dimension is dropped when the eval builds its DR le"
tags: ["auto-captured", "trpo_ftc1sevinit_s30_260729_105510"]
created: 2026-07-29T08:24:32.720137
updated: 2026-07-29T12:20:47.836515
sources: ["experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The learned `fault_severity` dimension is dropped when the eval builds its DR le

The learned `fault_severity` dimension is dropped when the eval builds its DR levels, so all four levels carry the same fault condition set only by the CLI flags — the fault delta is therefore uncontaminated by the box-width difference.

[EVIDENCE: both eval logs print `[WARN] DomainRandomizationCfg has no field 'fault_severity'` during DORAEMON-DR load, i.e. the dim has no `DomainRandomizationCfg` target]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

The learned `fault_severity` dimension is dropped when the eval builds its DR levels, so all four levels carry the same fault condition set only by the CLI flags — the fault delta is therefore uncontaminated by the box-width difference.

[EVIDENCE: both eval logs print `[WARN] DomainRandomizationCfg has no field 'fault_severity'` during DORAEMON-DR load, i.e. the dim has no `DomainRandomizationCfg` target]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
