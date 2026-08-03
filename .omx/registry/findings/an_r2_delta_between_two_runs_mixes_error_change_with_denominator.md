---
title: "An R2 DELTA between two runs mixes error change with denominator change whenever their eval env draws differ -- decompose it before reporting the headline"
tags: ["latent", "r2", "denominator", "methodology", "student", "eval"]
created: 2026-08-03T13:53:27.506570
updated: 2026-08-03T15:01:33.114893
sources: ["diagnose-20260803-223517"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
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

---

## Update (2026-08-03T14:52:19.970816)

## Fifth instance, 2026-08-03, and the first where the artifact HID a loss

Previous instances of this trap all ran one way: the denominator moved in the flattering
direction and manufactured an apparent gain. The obs4 widened-encoder arm (WIDE, GRU 256)
against B2 (GRU 128) is the mirror image, which is why it is worth recording separately.

| quantity | value |
|:--|--:|
| B2 aggregate hard R2 | +0.2460 |
| WIDE aggregate hard R2 | +0.2296 |
| raw delta | -0.0164 (-0.31 sigma: reads as "no change") |
| WIDE error scored on B2's denominator | +0.1440 |
| **error-only delta** | **-0.1020** |
| denominator-only contribution | +0.0856 |
| sum(MSE) | 0.4996 -> 0.5672, **+13.5%** |
| sum(Var) | 0.6626 -> 0.7362, +11.1% |

Reading the ratio alone would have recorded this arm as "no change" and left the
capacity-crowding hypothesis alive. The denominator-free `sum(MSE)` is what showed a 13.5%
regression and refuted it.

## The rule, restated for both directions

Never report an R2 delta between two runs without the decomposition. Score the second run's
error on the FIRST run's denominator and report all three numbers: raw delta, error-only
delta, denominator contribution. This is now a standing check for every cross-run R2 in this
campaign, in both directions — a small raw delta is as suspect as a large one.

The denominators move because the arms draw INDEPENDENT env sets whenever anything changes
the torch RNG stream. That includes changes that touch no env config at all: `gru_hidden`
alters the parameter count and therefore desynchronises the draws.

---

## Update (2026-08-03T15:01:33.114893)

## Scope correction to the "Fifth instance" heading above

An independent review flagged the ordinal as uncited, and it is. No exhaustive campaign tally
has ever been compiled, so "fifth" is an impression rather than a count. What IS on record and
citable: the Phase C report's d3 finding (R2 +0.3874 while MSE worsened 23.6%) and its aggregate
finding (~40% of the headline denominator-driven), both in `diagnose-20260803-223517`, plus this
widened-encoder instance.

The substantive point is unaffected and is the reason the page exists: decompose every cross-run
R2 delta before reporting it. What the correction removes is only the claim to know how many
times it has bitten.

