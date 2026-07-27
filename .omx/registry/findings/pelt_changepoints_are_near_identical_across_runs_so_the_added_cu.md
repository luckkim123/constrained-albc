---
title: "PELT changepoints are near-identical across runs, so the added curriculum dimens"
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

# PELT changepoints are near-identical across runs, so the added curriculum dimens

PELT changepoints are near-identical across runs, so the added curriculum dimension did not perturb the optimisation trajectory shape.

[EVIDENCE: engine `[TRENDS] reward` — anchor `changepoints: iter 396, 3499`, Arm A `376, 3493`,]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

PELT changepoints are near-identical across runs, so the added curriculum dimension did not perturb the optimisation trajectory shape.

[EVIDENCE: engine `[TRENDS] reward` — anchor `changepoints: iter 396, 3499`, Arm A `376, 3493`, Arm B `361, 3498`; all three report `phase: warmup(1)->plateau(7)`, `plateau: YES since ~10%`, stability cv 0.011-0.012]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

PELT changepoints are near-identical across runs, so the added curriculum dimension did not perturb the optimisation trajectory shape.

[EVIDENCE: engine `[TRENDS] reward` — anchor `changepoints: iter 396, 3499`, Arm A `376, 3493`, Arm B `361, 3498`; all three report `phase: warmup(1)->plateau(7)`, `plateau: YES since ~10%`, stability cv 0.011-0.012]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md
