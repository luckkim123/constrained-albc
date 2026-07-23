---
title: "Restated in absolute degrees against this repo's own reference scales, the retra"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T04:54:21.766685
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Restated in absolute degrees against this repo's own reference scales, the retra

Restated in absolute degrees against this repo's own reference scales, the retrain cost is negligible and the plant gain is large. This is the correction the `tam_plant_correctness_fix` wiki page already applied once to a percentage-framed claim on a small base. - retrain `roll.ss_error` +0.110 deg = **9.6%** of one obs-noise sigma - retrain `pitch.ss_error` +0.117 deg = 10.2% of one sigma - plant `roll.os_env_mean` -3.934 deg = **78.7%** of the 5-deg settling gate

[EVIDENCE: `config.py:271` `_OBS_NOISE_STD` euler = 0.02 rad = 1.146 deg; `config.py:292` `_OBS_BIAS_MAG` euler = +-0.02 rad; `constraints.py:222` `rp_vel_settling` gate = 0.087 rad = 5 deg]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
