---
title: "The DORAEMON gate is live and correctly calibrated — it is not inert and not pin"
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

# The DORAEMON gate is live and correctly calibrated — it is not inert and not pin

The DORAEMON gate is live and correctly calibrated — it is not inert and not pinned. | run | success_rate | ess_ratio | entropy_before | mode | |:--|--:|--:|--:|--:| | anchor s30 | 0.81 | 0.78 | -22.77 | 0.00 | | anchor s31 | 0.81 | 0.77 | -24.82 | 0.00 | | anchor s32 | 0.70 | 0.80 | -24.75 | 0.00 | | Arm N 8192 | 0.74 | 0.77 | -23.54 | 0.00 | | dgxseed30 | 0.80 | 0.76 | -26.07 | 0.00 | | dgxseed31 | 0.81 | 0.79 | -24.60 | 0.00 | | dgxseed32 | 0.85 | 0.78 | -22.50 | 0.00 | `config.py:531-543` records `performance_lb=250` as calibrated to the p25 of the measured episode return distribution with a target starting `success_rate` of ~0.65; the measured end-of-run values 0.70-0.85 straddle the DORAEMON paper's ~0.8 guidance. `entropy_before` rises from -45.88 at iter 0 to -22.8 at 4999, i.e. cumulative difficulty is still accumulating.

[EVIDENCE: engine + `omx reduce tb-final`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

The DORAEMON gate is live and correctly calibrated — it is not inert and not pinned. | run | success_rate | ess_ratio | entropy_before | mode | |:--|--:|--:|--:|--:| | anchor s30 | 0.81 | 0.78 | -22.77 | 0.00 | | anchor s31 | 0.81 | 0.77 | -24.82 | 0.00 | | anchor s32 | 0.70 | 0.80 | -24.75 | 0.00 | | Arm N 8192 | 0.74 | 0.77 | -23.54 | 0.00 | | dgxseed30 | 0.80 | 0.76 | -26.07 | 0.00 | | dgxseed31 | 0.81 | 0.79 | -24.60 | 0.00 | | dgxseed32 | 0.85 | 0.78 | -22.50 | 0.00 | `config.py:531-543` records `performance_lb=250` as calibrated to the p25 of the measured episode return distribution with a target starting `success_rate` of ~0.65; the measured end-of-run values 0.70-0.85 straddle the DORAEMON paper's ~0.8 guidance. `entropy_before` rises from -45.88 at iter 0 to -22.8 at 4999, i.e. cumulative difficulty is still accumulating.

[EVIDENCE: engine + `omx reduce tb-final`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
