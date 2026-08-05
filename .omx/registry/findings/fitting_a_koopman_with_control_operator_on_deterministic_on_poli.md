---
title: "Fitting a Koopman-with-control operator on deterministic on-policy rollouts cannot identify B, and a richer dictionary makes it worse"
tags: ["koopman", "system-id", "identifiability", "excitation", "eval", "methodology"]
created: 2026-08-05T10:17:27.849382
updated: 2026-08-05T10:17:27.849382
sources: ["constrained_albc/analysis/eval.py", ".omx/programs/koopman-lifting/PLAN.md#12.8"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Fitting a Koopman-with-control operator on deterministic on-policy rollouts cannot identify B, and a richer dictionary makes it worse

SOURCE: measured on the E-int static eval rollouts, 2026-08-05, PLAN 12.8 reading 6 and commit a0daf23. eval.py steps the DETERMINISTIC inference policy, so u = pi(o) exactly, and a ridge fit finds u is 96.5 pct linearly predictable from the raw 72D obs at DR none (92.6 to 94.6 pct across levels). When u is linear in the lifted state z, the term B u equals B C z and is absorbable into A, so B is not identified and the fitted operator is valid only along that policy's own closed loop. The counter-intuitive part: this gets WORSE as the dictionary gets better. u R2 rises monotonically with lift width and with learning, 0.965 for the raw obs up to 0.9828 for a learned lift of width 128 -- a richer basis explains the deterministic policy better, so more of B u becomes absorbable. Anyone fitting a Koopman-with-control model on on-policy rollouts should expect identifiability to degrade exactly as they improve the basis. The fix is action excitation: eval.py static --excite-std 0.10 (band-limited, dedicated RNG generator so DR draws stay paired) drops u R2 to about 0.74 at every DR level while terminating zero envs.
