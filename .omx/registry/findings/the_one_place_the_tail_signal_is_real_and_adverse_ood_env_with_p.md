---
title: "The one place the tail signal is real and adverse: ood #env with peak |error_rol"
tags: ["auto-captured", "trpo_e1_latdr_260713_124923"]
created: 2026-07-13T10:08:21.544030
updated: 2026-07-13T10:08:21.544030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The one place the tail signal is real and adverse: ood #env with peak |error_rol

The one place the tail signal is real and adverse: ood #env with peak |error_roll| > 20° rises from 1 (baseline) to 5 (e1) — e1 has MORE extreme-outlier envs under OOD despite its milder distribution, hinting the delay hurts worst-case robustness.

[EVIDENCE: data_ood.npz per-env peak|error_roll|>20deg count e1 5 vs baseline 1; low power (64 env, single seed)]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
