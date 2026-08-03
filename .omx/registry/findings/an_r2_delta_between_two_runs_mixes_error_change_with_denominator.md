---
title: "An R2 DELTA between two runs mixes error change with denominator change whenever their eval env draws differ -- decompose it before reporting the headline"
tags: ["latent", "r2", "denominator", "methodology", "student", "eval"]
created: 2026-08-03T13:53:27.506570
updated: 2026-08-03T13:53:27.506570
sources: ["diagnose-20260803-223517"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# An R2 DELTA between two runs mixes error change with denominator change whenever their eval env draws differ -- decompose it before reporting the headline

This is the FOURTH time the same denominator class has bitten this campaign, and the first time it
bit a DELTA rather than a level. Record it as a standing check.

R2 = 1 - MSE/Var. When two runs draw DIFFERENT eval env sets, Var(l_true) itself moves between them,
so an R2 delta is NOT a pure statement about prediction quality. In B2-vs-control at hard:

  sum(MSE) 0.5566 -> 0.4996 (-10.2%)   the real improvement
  sum(Var) 0.6120 -> 0.6626 (+8.3%)    the denominator drifting
  aggregate R2 +0.0905 -> +0.2460      delta +0.1555, which reads as the whole story

  B2's MSE measured against the CONTROL's denominator = +0.1837
  -> error-only contribution +0.0931 (60%), denominator contribution +0.0624 (40%)

So 40% of the headline was the denominator. Per-dim it is worse: d3's R2 rose +0.3874 while its MSE
got 23.6% WORSE -- a pure artifact that reads as the second-best dimension in the set.

THE CHECK, before reporting any cross-run R2 delta:
1. Compare the dr_* per-env draw arrays in the two data_<level>.npz. Identical -> the denominator is
   shared and the delta is clean. Different -> do step 2.
2. Recompute the treatment's MSE against the BASELINE's denominator. Report that error-only number
   alongside the raw delta, per dim and in aggregate.
3. Sanity-check every per-dim R2 rise against its own MSE direction. A dim whose R2 rose while its
   MSE rose is a denominator artifact, not an improvement.

Prior members of this class, for pattern recognition: the B1b correction (a ratio read against the
wrong target, reversing the d4 verdict); ranking dims by R2 when the worst R2 belonged to the
smallest denominator (d2 is the BEST-tracked dim at MSE 0.0016 yet has a negative R2); and 38d979e,
where a duplicated eval-side forward dropped normalization. Same family: the metric was believed
rather than decomposed.

