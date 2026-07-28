---
title: "DC steady-state tracking is intact at `none` while the breach is transient-shape"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# DC steady-state tracking is intact at `none` while the breach is transient-shape

DC steady-state tracking is intact at `none` while the breach is transient-shaped: roll ss_error moves +1.9% (within bound), pitch ss_error -15.7% (improvement), yaw ss_error +18.8% (breach), and roll n_gt20 jumps 0 -> 18.67 envs with roll os_env_mean 8.18 -> 17.96 pp (= 5.39 deg mean overshoot on the 30-deg step). | gate metric | E-int | HydroRC | paired delta | bound 16.8% | |:--|--:|--:|--:|:--| | roll ss_error (deg) | 0.4277 | 0.4358 | +1.9% | within | | pitch ss_error (deg) | 0.2132 | 0.1798 | -15.7% | improvement (never fires) | | yaw ss_error (rad/s) | 0.006186 | 0.007346 | +18.8% | BREACH | | roll n_gt20 (envs) | 0.00 | 18.67 | 0 -> 18.67 | BREACH (zero baseline: any increase) |

[EVIDENCE: none-level roll/pitch/yaw ss_error and roll n_gt20 fields of experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075343/summary.json and experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260727_235736/summary.json; yaw absolute delta +0.001160 rad/s = +0.066 deg/s]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

DC steady-state tracking is intact at `none` while the breach is transient-shaped: roll ss_error moves +1.9% (within bound), pitch ss_error -15.7% (improvement), yaw ss_error +18.8% (breach), and roll n_gt20 jumps 0 -> 18.67 envs with roll os_env_mean 8.18 -> 17.96 pp (= 5.39 deg mean overshoot on the 30-deg step). | gate metric | E-int | HydroRC | paired delta | bound 16.8% | |:--|--:|--:|--:|:--| | roll ss_error (deg) | 0.4277 | 0.4358 | +1.9% | within | | pitch ss_error (deg) | 0.2132 | 0.1798 | -15.7% | improvement (never fires) | | yaw ss_error (rad/s) | 0.006186 | 0.007346 | +18.8% | BREACH | | roll n_gt20 (envs) | 0.00 | 18.67 | 0 -> 18.67 | BREACH (zero baseline: any increase) |

[EVIDENCE: none-level roll/pitch/yaw ss_error and roll n_gt20 fields of experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075343/summary.json and experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260727_235736/summary.json; yaw absolute delta +0.001160 rad/s = +0.066 deg/s]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

DC steady-state tracking is intact at `none` while the breach is transient-shaped: roll ss_error moves +1.9% (within bound), pitch ss_error -15.7% (improvement), yaw ss_error +18.8% (breach), and roll n_gt20 jumps 0 -> 18.67 envs with roll os_env_mean 8.18 -> 17.96 pp (= 5.39 deg mean overshoot on the 30-deg step). | gate metric | E-int | HydroRC | paired delta | bound 16.8% | |:--|--:|--:|--:|:--| | roll ss_error (deg) | 0.4277 | 0.4358 | +1.9% | within | | pitch ss_error (deg) | 0.2132 | 0.1798 | -15.7% | improvement (never fires) | | yaw ss_error (rad/s) | 0.006186 | 0.007346 | +18.8% | BREACH | | roll n_gt20 (envs) | 0.00 | 18.67 | 0 -> 18.67 | BREACH (zero baseline: any increase) |

[EVIDENCE: none-level roll/pitch/yaw ss_error and roll n_gt20 fields of experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075343/summary.json and experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260727_235736/summary.json; yaw absolute delta +0.001160 rad/s = +0.066 deg/s]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
