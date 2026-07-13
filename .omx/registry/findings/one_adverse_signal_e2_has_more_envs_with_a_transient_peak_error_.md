---
title: "One adverse signal: e2 has MORE envs with a transient peak |error_roll| > 20deg "
tags: ["auto-captured", "trpo_e2_biasobs_260713_173456"]
created: 2026-07-13T13:47:17.958008
updated: 2026-07-13T13:47:17.958008
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# One adverse signal: e2 has MORE envs with a transient peak |error_roll| > 20deg 

One adverse signal: e2 has MORE envs with a transient peak |error_roll| > 20deg (6 vs 3) despite lower steady-state — observability may trade a slightly worse worst-case transient for better steady-state tracking.

[EVIDENCE: data_hard.npz per-env peak|error_roll|>20deg count e2 6 vs baseline 3 (transient max over trajectory; steady-state median e2 0.147 << 20)]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
