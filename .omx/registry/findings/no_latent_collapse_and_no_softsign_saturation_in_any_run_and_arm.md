---
title: "No latent collapse and no softsign saturation in any run, and Arm B's latent is "
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-27T05:49:10.587769
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# No latent collapse and no softsign saturation in any run, and Arm B's latent is 

No latent collapse and no softsign saturation in any run, and Arm B's latent is the widest-spread of the three.

[EVIDENCE: `Encoder/z_std` 0.3868 (A) / 0.4157 (B) / 0.3950 (anchor), all far above the profile's 0.1 LOW threshold; `Encoder/z_min`/`z_max` bounded by [-0.728, 0.733], inside the +/-0.95 SAT threshold]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

No latent collapse and no softsign saturation in any run, and Arm B's latent is the widest-spread of the three.

[EVIDENCE: `Encoder/z_std` 0.3868 (A) / 0.4157 (B) / 0.3950 (anchor), all far above the profile's 0.1 LOW threshold; `Encoder/z_min`/`z_max` bounded by [-0.728, 0.733], inside the +/-0.95 SAT threshold]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
