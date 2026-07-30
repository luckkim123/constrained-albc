---
title: "The pre-registered Isaac paired non-regression gate FAILS, so per the proposal r"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The pre-registered Isaac paired non-regression gate FAILS, so per the proposal r

The pre-registered Isaac paired non-regression gate FAILS, so per the proposal rule the recenter does NOT proceed to the Stonefish readout and the H1/H2 deployment discrimination is NOT reached. Two of four gate metrics breach: roll n_gt20 goes 0 -> 18.67 envs (decisive — also clears the PLAN 11.6 REAL floor of 15 envs from a zero baseline) and yaw ss_error degrades +18.8% against the 16.8% provisional paired bound (marginal alone, but yaw degrades at every DR level: +18.8/+23.4/+24.3/+31.8% at none/soft/medium/hard, a consistent direction rather than one-level noise). Outcome path per the proposal: revise nominals (e.g. partial recenter); the E-int final-teacher verdict (H1) is unchanged by this probe.

[EVIDENCE: gate rule verbatim in proposals/next-20260727-174905.md (Isaac-side non-regression gate paragraph); gate inputs experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075343/summary.json none-level vs experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260727_235736/summary.json none-level; PLAN.md 11.6 item 3 floors ss_error 0.10 deg / os 10 pp / n_gt20 15 envs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

The pre-registered Isaac paired non-regression gate FAILS, so per the proposal rule the recenter does NOT proceed to the Stonefish readout and the H1/H2 deployment discrimination is NOT reached. Two of four gate metrics breach: roll n_gt20 goes 0 -> 18.67 envs (decisive — also clears the PLAN 11.6 REAL floor of 15 envs from a zero baseline) and yaw ss_error degrades +18.8% against the 16.8% provisional paired bound (marginal alone, but yaw degrades at every DR level: +18.8/+23.4/+24.3/+31.8% at none/soft/medium/hard, a consistent direction rather than one-level noise). Outcome path per the proposal: revise nominals (e.g. partial recenter); the E-int final-teacher verdict (H1) is unchanged by this probe.

[EVIDENCE: gate rule verbatim in proposals/next-20260727-174905.md (Isaac-side non-regression gate paragraph); gate inputs experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075343/summary.json none-level vs experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260727_235736/summary.json none-level; PLAN.md 11.6 item 3 floors ss_error 0.10 deg / os 10 pp / n_gt20 15 envs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

The pre-registered Isaac paired non-regression gate FAILS, so per the proposal rule the recenter does NOT proceed to the Stonefish readout and the H1/H2 deployment discrimination is NOT reached. Two of four gate metrics breach: roll n_gt20 goes 0 -> 18.67 envs (decisive — also clears the PLAN 11.6 REAL floor of 15 envs from a zero baseline) and yaw ss_error degrades +18.8% against the 16.8% provisional paired bound (marginal alone, but yaw degrades at every DR level: +18.8/+23.4/+24.3/+31.8% at none/soft/medium/hard, a consistent direction rather than one-level noise). Outcome path per the proposal: revise nominals (e.g. partial recenter); the E-int final-teacher verdict (H1) is unchanged by this probe.

[EVIDENCE: gate rule verbatim in proposals/next-20260727-174905.md (Isaac-side non-regression gate paragraph); gate inputs experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075343/summary.json none-level vs experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260727_235736/summary.json none-level; PLAN.md 11.6 item 3 floors ss_error 0.10 deg / os 10 pp / n_gt20 15 envs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
