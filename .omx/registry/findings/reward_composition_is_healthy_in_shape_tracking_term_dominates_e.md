---
title: "Reward composition is healthy in shape (tracking term dominates, every penalty ~"
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

# Reward composition is healthy in shape (tracking term dominates, every penalty ~

Reward composition is healthy in shape (tracking term dominates, every penalty ~1% of total) but the episode return plateaus at ~197 — well below the baseline's ~247 scale, the ~10% delay tax that drives the curriculum stall (§7).

[EVIDENCE: analyze_training.py TIER 3 Reward att_rp 6.06 + yaw_vel 0.79 vs penalties |x|<=0.04; TIER 1 reward=197.29; [TRENDS] reward plateau-since-5%, cv=0.028, changepoints 376/3411]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
