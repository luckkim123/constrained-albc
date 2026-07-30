---
title: "The pre-registered `a`-drift H2 signature does not fire, exactly as the DESIGN.m"
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

# The pre-registered `a`-drift H2 signature does not fire, exactly as the DESIGN.m

The pre-registered `a`-drift H2 signature does not fire, exactly as the DESIGN.md mid-run resolution anticipated: `a` fell but `b` fell faster, so the mean rose monotonically.

[EVIDENCE: `curriculum_trajectory.json` `fault_severity`, `a` 2.3130 -> 1.2102 while `b` 27.6870 -> 5.0634; the mean is monotonically non-decreasing over the last 13 updates]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

The pre-registered `a`-drift H2 signature does not fire, exactly as the DESIGN.md mid-run resolution anticipated: `a` fell but `b` fell faster, so the mean rose monotonically.

[EVIDENCE: `curriculum_trajectory.json` `fault_severity`, `a` 2.3130 -> 1.2102 while `b` 27.6870 -> 5.0634; the mean is monotonically non-decreasing over the last 13 updates]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
