---
title: "Overshoot (% of step) decreases as DR hardens while rise time lengthens slightly"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Overshoot (% of step) decreases as DR hardens while rise time lengthens slightly

Overshoot (% of step) decreases as DR hardens while rise time lengthens slightly (a damping-like trend; the mechanism is not verified against the DR config here); the large per-step error spikes in the trajectory plot are the ±15–30° step commands, which settle to <1° within ~1–2 s.

[EVIDENCE: summary.json os_env_mean roll 29.9%->18.0% none->hard, rise_time 0.32->0.40 s; plots/traj_error.png (15° spike per step, settles <1°)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

Overshoot (% of step) decreases as DR hardens while rise time lengthens slightly (a damping-like trend; the mechanism is not verified against the DR config here); the large per-step error spikes in the trajectory plot are the ±15–30° step commands, which settle to <1° within ~1–2 s.

[EVIDENCE: summary.json os_env_mean roll 29.9%->18.0% none->hard, rise_time 0.32->0.40 s; plots/traj_error.png (15° spike per step, settles <1°)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
