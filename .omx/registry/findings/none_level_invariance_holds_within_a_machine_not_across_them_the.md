---
title: "none-level invariance holds within a machine, not across them: the same checkpoint moved 4 percent when re-scored on a different GPU, while a same-machine control reproduced exactly"
tags: ["eval", "machine", "reproducibility", "cross-machine", "methodology", "none-level"]
created: 2026-08-09T06:41:36.015298
updated: 2026-08-09T06:41:36.015298
sources: ["diagnose-20260809-142000"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# none-level invariance holds within a machine, not across them: the same checkpoint moved 4 percent when re-scored on a different GPU, while a same-machine control reproduced exactly

`none` is the campaign's invariant exam level (DR_SCALE["none"] = 0.0), and it reproduces to four
decimals — on the SAME machine. Across machines it does not, and the size of the shift is large
enough to swallow the effects this campaign routinely calls REAL.

MEASURED 2026-08-09, re-scoring two checkpoints on the workstation (RTX 4070) under one anchor:

  RunA trpo_iterbudget_s30 model_9998   none 0.5070 -> 0.5070   EXACT (always evaluated on the workstation)
  16k  trpo_dgx16k_s30     model_7500   none 0.4968 -> 0.4767   -4.0% (recorded value was produced on the DGX GB10)

Same checkpoint file, same seed 42, same 64 scenarios, same saturated anchor. The only difference for
the second row is which GPU ran the rollout. The control is the first row: a checkpoint whose
recorded value came from the same machine reproduces exactly, so this is not eval-instrument drift in
general — it is a machine term.

KEEP THE TWO MACHINE AXES SEPARATE. This is an EVAL-machine term (which GPU ran the exam). The
campaign's standing +109% figure is a TRAINED-machine term (which GPU produced the weights) and is a
different claim; this measurement neither confirms nor refutes it. What it does establish is a ~4%
noise floor on `none` under ANY cross-machine comparison, which is the same order as several deltas
this campaign has quoted as findings.

CONSEQUENCE FOR PROTOCOL. Never compare a recorded `none` score produced on machine X against a fresh
one produced on machine Y. Re-score BOTH sides on ONE machine, in one batch, before reading any
cross-run delta — the re-score is ~10 min per checkpoint and removes the term entirely. The same rule
that already applies to the DR anchor applies to the machine: it is part of the exam.

SOURCE: .omx/programs/dgx-final-teacher/PLAN.md gate G0 (RESULT block, by-product 2); evals
static_260809_150721 / static_260809_151752 vs the recorded values in
teacher_envscale_dgx/.../analysis/diagnose-20260809-142000/report.md section "tracking".

