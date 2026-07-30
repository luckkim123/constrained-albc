---
title: "The binding constraint is the mechanism that would suppress fault compensation i"
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

# The binding constraint is the mechanism that would suppress fault compensation i

The binding constraint is the mechanism that would suppress fault compensation if it tightened, so its NOT tightening removes budget saturation as an explanation for the fault-rejection loss and leaves the loss unexplained by the constraint layer.

[EVIDENCE: wiki `ftc_investigation_2026_07_25_m4_loss_halves_pure_yaw_ceiling_uti` composition-risk 2 ("thruster_util fights compensation -- the constraint is max-based and binding, and m4-dead yaw needs x2.00 peak utilization, so the IPO barrier actively suppresses exactly the compensating behavior"); measured J_C/d_k moved 0.902 -> 0.890, i.e. away from binding]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

The binding constraint is the mechanism that would suppress fault compensation if it tightened, so its NOT tightening removes budget saturation as an explanation for the fault-rejection loss and leaves the loss unexplained by the constraint layer.

[EVIDENCE: wiki `ftc_investigation_2026_07_25_m4_loss_halves_pure_yaw_ceiling_uti` composition-risk 2 ("thruster_util fights compensation -- the constraint is max-based and binding, and m4-dead yaw needs x2.00 peak utilization, so the IPO barrier actively suppresses exactly the compensating behavior"); measured J_C/d_k moved 0.902 -> 0.890, i.e. away from binding]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
