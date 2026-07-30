---
title: "E-ftc1 took one barrier spike that Arm A never took, and the engine raises it as"
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

# E-ftc1 took one barrier spike that Arm A never took, and the engine raises it as

E-ftc1 took one barrier spike that Arm A never took, and the engine raises it as a distinct diagnosis — a transient where the IPO barrier gradient overwhelmed the reward at a small margin.

[EVIDENCE: `Constraint/barrier_penalty` last -0.1237 (E-ftc1) vs -0.1223 (Arm A); engine `spikes(>0.01)=1 max=0.345` vs `spikes(>0.01)=0 max=-0.044`; E-ftc1 alone carries [DIAGNOSIS] 4 "Barrier penalty spikes (>0.1)"]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

E-ftc1 took one barrier spike that Arm A never took, and the engine raises it as a distinct diagnosis — a transient where the IPO barrier gradient overwhelmed the reward at a small margin.

[EVIDENCE: `Constraint/barrier_penalty` last -0.1237 (E-ftc1) vs -0.1223 (Arm A); engine `spikes(>0.01)=1 max=0.345` vs `spikes(>0.01)=0 max=-0.044`; E-ftc1 alone carries [DIAGNOSIS] 4 "Barrier penalty spikes (>0.1)"]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
