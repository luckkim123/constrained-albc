---
title: "Iteration count, not DR width, drives the nominal roll transient; the wider DR b"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-20T17:13:19.523263
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Iteration count, not DR width, drives the nominal roll transient; the wider DR b

Iteration count, not DR width, drives the nominal roll transient; the wider DR box is a weak mitigator, i.e. the opposite sign from the hypothesis under test. The point estimates below are single-seed per cell with no replication and therefore no noise bound, and the ref5k->A1 edge additionally inherits the row-1 leak (A1 ended 0.66 nats wider than ref5k, Beta b ~5.5 vs ~6.4), so part of the +13.52 attributed to iterations could belong to that residual width difference. The SIGN of both effects is robust (the -3.56 width edge is width-only at held iterations, and 13.52 pts dwarfs the leak); the MAGNITUDES are provisional.

[EVIDENCE: `eval/static_*/summary.json` `none/roll/os_env_mean`, three runs; leak size from the manipulation-check section (0.66 nats of 4.5)]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
