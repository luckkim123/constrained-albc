---
title: "Repeat-eval instrument noise on in-loop latent R2: 0.027 at hard, 0.22 at none"
tags: ["latent", "r2", "instrument", "noise", "calibration", "eval", "decision-floor"]
created: 2026-08-04T07:04:56.243640
updated: 2026-08-04T07:04:56.243640
sources: ["diagnose-20260804-154122"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Repeat-eval instrument noise on in-loop latent R2: 0.027 at hard, 0.22 at none

Measured 2026-08-04 by re-evaluating the SAME student checkpoint (Phase E trpo_sdobs76_c3_gruselect_s30_260804_124951, student_999.pt) under two eval builds -- static_260804_130704 (pre-reseed-fix) and static_260804_145821 (post-fix). Aggregate in-loop latent R2 = 1 - sumMSE/sumVar over pooled (time x env) samples from latent_LEVEL.npz. Repeat deltas: none -0.2190 (R2 -1.5802 -> -1.7992), soft -0.0399, medium -0.0009, hard -0.0266.

WHY IT MATTERS. The campaign screens student arms on hard aggregate R2 against a 2-sigma_diff bar of 0.107 (sigma_diff = 0.0533 from 400 half-splits of 64 envs). The hard repeat noise of 0.0266 is one quarter of that bar, so the screening threshold is NOT swallowed by instrument noise -- a hard R2 delta above ~0.107 is real. Use 0.0266 as the practical floor below which a hard R2 difference is indistinguishable from re-running the same checkpoint.

AND THE none LEVEL IS NOW EMPIRICALLY DEAD, not just theoretically. Repetition alone moves the none aggregate by 0.219, twice the decision threshold, because its denominator collapses (per-dim Var_total spans ~2163x). This is direct evidence for the standing rule that the none aggregate R2 must never be used in a decision -- previously argued from the denominator, now measured.

DECOMPOSE BEFORE QUOTING. At hard the two evals moved sumMSE -0.0638 and sumVar -0.0734 nearly in proportion, which is exactly why R2 barely shifted. A real effect has the opposite signature (X1: sumMSE -0.0823 while sumVar ROSE +0.0161). Always report sumMSE and sumVar alongside any R2 delta.
