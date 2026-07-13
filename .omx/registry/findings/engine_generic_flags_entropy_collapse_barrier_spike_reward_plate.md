---
title: "engine generic flags (entropy-collapse / barrier-spike / reward-plateau) are benign for a converged teacher"
tags: ["analyze_training", "diagnosis", "entropy", "barrier", "plateau", "clip_fraction"]
created: 2026-07-12T23:46:27.626318
updated: 2026-07-12T23:46:27.626318
sources: ["diagnose-20260713-081707"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# engine generic flags (entropy-collapse / barrier-spike / reward-plateau) are benign for a converged teacher

analyze_training.py emits three generic-heuristic DIAGNOSIS flags that fire on a HEALTHY converged teacher and must NOT be read as defects without a code-exec cross-check: (1) 'entropy collapse -> exploration dead' fires because entropy goes negative at convergence (expected) — cross-check Policy/clip_fraction: if |a|>=1 saturation is low (baseline 0.005) the policy is NOT saturating actions, so exploration is fine (this is also the Lead-2 init_noise_std gate datum). (2) 'reward plateaued last 30% / converged early' fires when reward saturates while DORAEMON keeps hardening DR — cross-check DORAEMON/success_rate (baseline ~0.47, still climbing) + entropy_before rising = curriculum still advancing, not a stall. (3) 'barrier penalty spikes >0.1' fires on Constraint/barrier_penalty magnitude alone — cross-check vs Reward/total (baseline -0.127 = ~1.6% of 7.74) and Constraint/margin/* (all >0 = satisfied); small vs reward + margins satisfied = benign. Rule: an engine generic flag is a HYPOTHESIS; confirm/deny with the paired code-exec metric before writing it as a finding. Evidence: analysis diagnose-20260713-081707.
