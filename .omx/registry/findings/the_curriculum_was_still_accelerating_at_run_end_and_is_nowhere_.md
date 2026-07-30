---
title: "The curriculum was still accelerating at run end and is nowhere near saturated, "
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

# The curriculum was still accelerating at run end and is nowhere near saturated, 

The curriculum was still accelerating at run end and is nowhere near saturated, so 0.1929 is an iteration-limited endpoint rather than a competence ceiling.

[EVIDENCE: engine [TIER 2] `fault_severity ... trend/1k +0.0545 EXPANDING` (Arm A +0.0246); [DIAGNOSIS] 5 "DORAEMON dims still EXPANDING at final iter (fault_severity at 19% of range ...): curriculum under-converged"; per-update means rise 0.1361 -> 0.1480 -> 0.1614 -> 0.1763 -> 0.1929 over the last five updates]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

The curriculum was still accelerating at run end and is nowhere near saturated, so 0.1929 is an iteration-limited endpoint rather than a competence ceiling.

[EVIDENCE: engine [TIER 2] `fault_severity ... trend/1k +0.0545 EXPANDING` (Arm A +0.0246); [DIAGNOSIS] 5 "DORAEMON dims still EXPANDING at final iter (fault_severity at 19% of range ...): curriculum under-converged"; per-update means rise 0.1361 -> 0.1480 -> 0.1614 -> 0.1763 -> 0.1929 over the last five updates]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
