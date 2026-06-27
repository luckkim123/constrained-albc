---
title: "DORAEMON slow DR expansion: separate kl_step from ess_ratio to find cause"
tags: ["doraemon", "dr-curriculum", "diagnosis"]
created: 2026-06-27T09:04:10.974301
updated: 2026-06-27T09:04:10.974301
sources: ["diagnose-20260627-175826"]
links: []
category: debugging
confidence: medium
schemaVersion: 1
---

# DORAEMON slow DR expansion: separate kl_step from ess_ratio to find cause

When DORAEMON success_rate plateaus (~0.36) and the engine flags 'DR expanding too slowly', do NOT stop at the symptom. Split the cause with two TB tokens (omx reduce tb-final window=200): DORAEMON/kl_step and DORAEMON/ess_ratio. If ess_ratio is healthy (here 0.629, well-conditioned IS weights) while kl_step ~0.0 (here exactly 0.0), the curriculum is NOT failing to reweight -- it is CHOOSING near-zero update steps (a chosen-step issue, not degenerate-reweighting). Also pull DORAEMON/entropy_before (here -24.997, a tight high-dim ~17-param DR distribution). This separation tells you whether to touch the IS estimator (no, if ess_ratio healthy) or the step-size/expansion schedule (yes). Run trpo_ee_action_260627_094127, analysis diagnose-20260627-175826 (doraemon section). Policy still generalized to OOD 100% survival despite the slow expansion.
