---
title: "The dominant failure mode the anchor suffers is a HEAVY TAIL, not a DC bias — an"
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-27T05:49:10.587769
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The dominant failure mode the anchor suffers is a HEAVY TAIL, not a DC bias — an

The dominant failure mode the anchor suffers is a HEAVY TAIL, not a DC bias — and that is exactly what fault-DR removes. Distinguishing the two matters because the mean delta alone would understate it.

[EVIDENCE: CV = `ss_error_std`/`ss_error`, healthy -> m4-dead, `none` level]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

The dominant failure mode the anchor suffers is a HEAVY TAIL, not a DC bias — and that is exactly what fault-DR removes, which the mean delta alone would understate.

[EVIDENCE: CV = `ss_error_std`/`ss_error`, healthy -> m4-dead at `none` — roll anchor 0.73 -> 3.34, Arm A 0.45 -> 0.48, Arm B 0.29 -> 0.30; pitch anchor 0.22 -> 4.28, Arm A 0.27 -> 0.26, Arm B 0.15 -> 0.22; roll `ss_jitter` anchor 0.34 -> 1.10 deg, Arm A 0.21 -> 0.37, Arm B 0.20 -> 0.30; the anchor repeats the signature at `medium` (roll 0.77 -> 3.96, pitch 0.45 -> 4.38)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

The dominant failure mode the anchor suffers is a HEAVY TAIL, not a DC bias — and that is exactly what fault-DR removes, which the mean delta alone would understate.

[EVIDENCE: CV = `ss_error_std`/`ss_error`, healthy -> m4-dead at `none` — roll anchor 0.73 -> 3.34, Arm A 0.45 -> 0.48, Arm B 0.29 -> 0.30; pitch anchor 0.22 -> 4.28, Arm A 0.27 -> 0.26, Arm B 0.15 -> 0.22; roll `ss_jitter` anchor 0.34 -> 1.10 deg, Arm A 0.21 -> 0.37, Arm B 0.20 -> 0.30; the anchor repeats the signature at `medium` (roll 0.77 -> 3.96, pitch 0.45 -> 4.38)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
