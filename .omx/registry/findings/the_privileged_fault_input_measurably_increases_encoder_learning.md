---
title: "The privileged fault input measurably increases encoder learning signal: Arm B's"
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

# The privileged fault input measurably increases encoder learning signal: Arm B's

The privileged fault input measurably increases encoder learning signal: Arm B's encoder gradient norm is 2.0x the anchor's and Arm A's, and its update step 1.5-1.8x.

[EVIDENCE: `Policy/encoder_grad_norm` 0.0751 (B) vs 0.0377 (anchor) / 0.0371 (A);]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

The privileged fault input measurably increases encoder learning signal: Arm B's encoder gradient norm is 2.0x the anchor's and Arm A's, and its update step 1.5-1.8x.

[EVIDENCE: `Policy/encoder_grad_norm` 0.0751 (B) vs 0.0377 (anchor) / 0.0371 (A); `Grad/enc_step` 0.00271 (B) vs 0.00176 (anchor) / 0.00154 (A)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

The privileged fault input measurably increases encoder learning signal: Arm B's encoder gradient norm is 2.0x the anchor's and Arm A's, and its update step 1.5-1.8x.

[EVIDENCE: `Policy/encoder_grad_norm` 0.0751 (B) vs 0.0377 (anchor) / 0.0371 (A); `Grad/enc_step` 0.00271 (B) vs 0.00176 (anchor) / 0.00154 (A)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
