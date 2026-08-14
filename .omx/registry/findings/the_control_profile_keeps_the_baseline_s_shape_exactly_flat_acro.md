---
title: "The control profile keeps the baseline's shape exactly: flat across none/soft/me"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-05T09:49:50.734092
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The control profile keeps the baseline's shape exactly: flat across none/soft/me

The control profile keeps the baseline's shape exactly: flat across none/soft/medium with a roll-only spike at hard, overshoot DECLINING with DR strength and never approaching the 20 pp guide.

[EVIDENCE: numbers from `summary.json` of eval `static_260804_152454` — roll `ss_error` 0.3146/0.3715/0.3177/0.8550 deg with pitch 0.2605-0.3696, roll `os_env_mean` falling 11.069/8.503/7.822/7.682 pp as DR strengthens, roll `us_env_mean` 0.000/0.136/0.053/1.020 pp; the SHAPE reading is from `summary_attitude.png`, whose six panels are flat across none/soft/medium with a roll-only spike in the hard bar and an Overshoot panel that never approaches its 20 pp guide line]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

The control profile keeps the baseline's shape exactly: flat across none/soft/medium with a roll-only spike at hard, overshoot DECLINING with DR strength and never approaching the 20 pp guide.

[EVIDENCE: numbers from `summary.json` of eval `static_260804_152454` — roll `ss_error` 0.3146/0.3715/0.3177/0.8550 deg with pitch 0.2605-0.3696, roll `os_env_mean` falling 11.069/8.503/7.822/7.682 pp as DR strengthens, roll `us_env_mean` 0.000/0.136/0.053/1.020 pp; the SHAPE reading is from `summary_attitude.png`, whose six panels are flat across none/soft/medium with a roll-only spike in the hard bar and an Overshoot panel that never approaches its 20 pp guide line]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
