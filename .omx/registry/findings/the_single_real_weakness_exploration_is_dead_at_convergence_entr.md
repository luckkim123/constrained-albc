---
title: "The single real weakness: exploration is dead at convergence. Entropy has collap"
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-14T16:41:28.339995
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The single real weakness: exploration is dead at convergence. Entropy has collap

The single real weakness: exploration is dead at convergence. Entropy has collapsed and noise_std sits on its floor, so DORAEMON cannot ratchet difficulty further.

[EVIDENCE: engine TIER 1 + TB final-window means; DIAGNOSIS "Entropy collapse + low noise -> exploration dead"]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
