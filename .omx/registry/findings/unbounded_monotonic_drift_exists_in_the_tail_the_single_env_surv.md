---
title: "Unbounded monotonic drift exists in the tail: the single env surviving all 155 s"
tags: ["auto-captured", "trpo_main_teacher_260525_232805"]
created: 2026-07-12T18:26:43.465984
updated: 2026-07-12T18:26:43.465984
sources: ["experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Unbounded monotonic drift exists in the tail: the single env surviving all 155 s

Unbounded monotonic drift exists in the tail: the single env surviving all 155 s ramps its joint1 command one-directionally to 743 rad = 118 revolutions, wrapping the physical joint 20 times.

[EVIDENCE: data_none.npz env19 — joint1_target net −743.5 rad; joint1_pos range [−6.28,6.28] with 20 seam wraps; monotone negative]
[CONFIDENCE: HIGH]

source report: experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md
