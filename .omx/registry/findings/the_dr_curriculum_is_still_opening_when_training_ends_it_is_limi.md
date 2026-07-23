---
title: "The DR curriculum is still opening when training ends — it is limited by the ite"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T06:44:07.820188
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The DR curriculum is still opening when training ends — it is limited by the ite

The DR curriculum is still opening when training ends — it is limited by the iteration budget, not by the box bounds and not by `performance_lb`. | iter | mean a | mean b | |--:|--:|--:| | 0 | 12.900 | 27.600 | | 1000 | 10.033 | 20.816 | | 2000 | 5.920 | 11.793 | | 3000 | 3.584 | 6.668 | | 4000 | 2.261 | 3.767 | | 4750 | 1.670 | 2.469 | Monotonic and still moving at the last snapshot. At iter 4750, 0 of 20 params have reached the `a=b=1` full-width box bound; the 17 physical params sit at a=b between 1.57 and 2.66 on all three seeds, and the three one-sided params (`payload_cog_offset_xy_u`, `ocean_current_strength`, `obs_noise_scale`) sit at a=1, b=6-11.

[EVIDENCE: `curriculum_trajectory.json`, anchor s30, mean Beta parameters over the 20 DR params]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

The DR curriculum is still opening when training ends — it is limited by the iteration budget, not by the box bounds and not by `performance_lb`. | iter | mean a | mean b | |--:|--:|--:| | 0 | 12.900 | 27.600 | | 1000 | 10.033 | 20.816 | | 2000 | 5.920 | 11.793 | | 3000 | 3.584 | 6.668 | | 4000 | 2.261 | 3.767 | | 4750 | 1.670 | 2.469 | Monotonic and still moving at the last snapshot. At iter 4750, 0 of 20 params have reached the `a=b=1` full-width box bound; the 17 physical params sit at a=b between 1.57 and 2.66 on all three seeds, and the three one-sided params (`payload_cog_offset_xy_u`, `ocean_current_strength`, `obs_noise_scale`) sit at a=1, b=6-11.

[EVIDENCE: `curriculum_trajectory.json`, anchor s30, mean Beta parameters over the 20 DR params]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
