---
title: "The nominal cost that IS real sits on Arm A's roll transient, and it is Arm-A-sp"
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

# The nominal cost that IS real sits on Arm A's roll transient, and it is Arm-A-sp

The nominal cost that IS real sits on Arm A's roll transient, and it is Arm-A-specific (so it is a seed/run property, not a fault-DR property — Arm B moved the opposite way).

[EVIDENCE: summary.json `none`/roll]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

The nominal cost that IS real sits on Arm A's roll transient, and it is Arm-A-specific — Arm B moved the opposite way, so this reads as a run/seed property rather than a property of fault-DR itself.

[EVIDENCE: summary.json `none`/roll — `n_gt20` anchor 12, Arm A 39, Arm B 0 of 64 envs (|d| = 27 and 12 against a 15-env floor); `os_env_q90` anchor 16.8 pp, Arm A 26.0 pp, Arm B 13.4 pp]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

The nominal cost that IS real sits on Arm A's roll transient, and it is Arm-A-specific — Arm B moved the opposite way, so this reads as a run/seed property rather than a property of fault-DR itself.

[EVIDENCE: summary.json `none`/roll — `n_gt20` anchor 12, Arm A 39, Arm B 0 of 64 envs (|d| = 27 and 12 against a 15-env floor); `os_env_q90` anchor 16.8 pp, Arm A 26.0 pp, Arm B 13.4 pp]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
