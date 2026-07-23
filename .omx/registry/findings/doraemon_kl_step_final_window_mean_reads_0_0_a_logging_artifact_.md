---
title: "DORAEMON/kl_step final-window mean reads 0.0 -- a logging artifact, not a stalled curriculum"
tags: ["doraemon", "tensorboard", "gotcha", "kl_step"]
created: 2026-07-23T04:55:17.552058
updated: 2026-07-23T04:55:17.552058
sources: ["diagnose-20260723-134359"]
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# DORAEMON/kl_step final-window mean reads 0.0 -- a logging artifact, not a stalled curriculum

GOTCHA: 'omx reduce tb-final --window 200' on DORAEMON/kl_step returns 0.0 for every run, which reads as 'the curriculum stopped stepping'. It has not. EVIDENCE (raw EventAccumulator dump, buoyanchor s30): DORAEMON/kl_step has n=5000 samples of which only 19 are non-zero -- the tag is written ONLY at the ~20 curriculum update points implied by step_interval=250 over 5000 iters, and a trailing-200 window contains no update point. Contrast DORAEMON/success_rate: 4776 of 5000 non-zero, reads 0.808 at iter 4999. CHECK INSTEAD: read the non-zero subsequence, or read curriculum_trajectory.json (the Beta a/b snapshots) which shows the curriculum state directly. This is the 'engine empty cell is a HYPOTHESIS not a fact' rule applied to a trailing-window reducer: a sparse tag's window mean is meaningless, not evidence of absence. Re-visit: analysis diagnose-20260723-134359 section 'doraemon'.
