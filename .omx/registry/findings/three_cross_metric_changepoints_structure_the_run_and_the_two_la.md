---
title: "Three cross-metric changepoints structure the run, and the two late ones coincid"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Three cross-metric changepoints structure the run, and the two late ones coincid

Three cross-metric changepoints structure the run, and the two late ones coincide with the window in which sigma settles onto its final level: iter 3476 pairs the noise floor with a reward drop and iter 3555 pairs an entropy drop with a success-rate drop — the anchor has NO coincident changepoints at all. No intermediate eval exists at those iterations, so connecting them to the final-checkpoint eval regression is inference, not measurement.

[EVIDENCE: engine `[CHANGEPOINTS]` (PELT, 2+ coincident) — A2 iter 382 mean_noise_std(down)+barrier_penalty(down), iter 3476 mean_noise_std(down)+mean_reward(down), iter 3555 entropy(down)+success_rate(down); anchor "no coincident changes (all single-metric)"; `eval/` holds one eval, at `model_4999.pt`]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
