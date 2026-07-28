---
title: "The per-step reward decomposition is essentially unchanged by the plant swap — R"
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

# The per-step reward decomposition is essentially unchanged by the plant swap — R

The per-step reward decomposition is essentially unchanged by the plant swap — Reward/att_rp 7.005 vs 6.966, Reward/yaw_vel 1.959 vs 1.995, Reward/bias -0.0062 vs -0.0088, Reward/smoothness -0.0173 vs -0.0168, Reward/thruster -0.0269 vs -0.0245, Reward/torque -0.0541 vs -0.0531 (HydroRC vs E-int, final-window means) — training-side reward is blind to the eval-side transient regression, the same DR-averaged-reward-cannot-see-corner-behavior pattern this family has shown before.

[EVIDENCE: tb_final.py final-window means over both runs TB event files, tags Reward/att_rp yaw_vel bias smoothness thruster torque; total reward 260.38 vs 260.5 from launch.log iteration 4999 blocks]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

The per-step reward decomposition is essentially unchanged by the plant swap — Reward/att_rp 7.005 vs 6.966, Reward/yaw_vel 1.959 vs 1.995, Reward/bias -0.0062 vs -0.0088, Reward/smoothness -0.0173 vs -0.0168, Reward/thruster -0.0269 vs -0.0245, Reward/torque -0.0541 vs -0.0531 (HydroRC vs E-int, final-window means) — training-side reward is blind to the eval-side transient regression, the same DR-averaged-reward-cannot-see-corner-behavior pattern this family has shown before.

[EVIDENCE: tb_final.py final-window means over both runs TB event files, tags Reward/att_rp yaw_vel bias smoothness thruster torque; total reward 260.38 vs 260.5 from launch.log iteration 4999 blocks]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

The per-step reward decomposition is essentially unchanged by the plant swap — Reward/att_rp 7.005 vs 6.966, Reward/yaw_vel 1.959 vs 1.995, Reward/bias -0.0062 vs -0.0088, Reward/smoothness -0.0173 vs -0.0168, Reward/thruster -0.0269 vs -0.0245, Reward/torque -0.0541 vs -0.0531 (HydroRC vs E-int, final-window means) — training-side reward is blind to the eval-side transient regression, the same DR-averaged-reward-cannot-see-corner-behavior pattern this family has shown before.

[EVIDENCE: tb_final.py final-window means over both runs TB event files, tags Reward/att_rp yaw_vel bias smoothness thruster torque; total reward 260.38 vs 263.98 from the iteration-4999/5000 blocks of the HydroRC launch.log and the E-int resumed-segment (rs2350) launch.log]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
