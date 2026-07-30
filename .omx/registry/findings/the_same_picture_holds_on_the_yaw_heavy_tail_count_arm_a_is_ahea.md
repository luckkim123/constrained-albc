---
title: "The same picture holds on the yaw heavy-tail count: Arm A is ahead 4/4 and is th"
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-30T03:54:24.726456
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The same picture holds on the yaw heavy-tail count: Arm A is ahead 4/4 and is th

The same picture holds on the yaw heavy-tail count: Arm A is ahead 4/4 and is the only arm whose own vs-anchor delta stays under the floor at every level, but the A-B gap itself is again below floor — so yaw removes a counter-argument to H2 rather than proving H2.

[EVIDENCE: paired delta of yaw `n_gt20` (envs of 64) — anchor +27.5 / +22.5 / +22.0 / +20.5 (REAL at 4/4); Arm A +9.0 / +9.5 / +9.5 / +9.5 (BELOW-FLOOR at 4/4); Arm B +15.0 (REAL) / +13.5 / +13.5 / +14.5; the A-B gap is -6.0 / -4.0 / -4.0 / -5.0 envs against a 15-env floor, i.e. BELOW-FLOOR at 4/4]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md

---

## Merged from the_same_ordering_holds_on_the_yaw_heavy_tail_count_and_there_ar.md (2026-07-30T03:54:24.726456)

# The same ordering holds on the yaw heavy-tail count, and there Arm A stays under

The same ordering holds on the yaw heavy-tail count, and there Arm A stays under the pre-registered floor at every level while Arm B crosses it — so the fault-critical axis favours the SIMPLER arm, independently of the attitude sign-flip.

[EVIDENCE: paired delta of yaw `n_gt20` (envs of 64) — anchor +27.5 / +22.5 / +22.0 / +20.5 (REAL at 4/4); Arm A +9.0 / +9.5 / +9.5 / +9.5 (BELOW-FLOOR at 4/4); Arm B +15.0 (REAL) / +13.5 / +13.5 / +14.5]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md
