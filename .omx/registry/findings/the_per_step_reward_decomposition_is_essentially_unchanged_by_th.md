---
title: "The per-step reward decomposition is essentially unchanged by the plant swap — R"
tags: ["auto-captured", "correction", "e-int", "hydrorc", "withdrawn-draft"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T09:10:53.909208
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md", "diagnose-20260728-081953"]
links: []
category: session-log
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
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

---

## Update (2026-07-28T09:10:53.909208)

# CORRECTION 2026-07-28: the E-int reward referent in the two EARLIER blocks is a withdrawn draft figure

This page was auto-captured from three reports of the same HydroRC run. Two of them
(`diagnose-20260728-081212`, `diagnose-20260728-081242`) were DRAFTS that were withdrawn during
independent review, and their blocks above cite E-int's final reward as **260.5**. That number is
the reward at E-int's CRASH point (iter ~2390 of the original `trpo_eint_s30_260727_160913`
segment), not its final value.

The value of record is **263.98** — E-int's true final reward, read from the iteration-4999/5000
block of the RESUMED segment `trpo_eint_s30_rs2350_260727_195102`. It already appears in the third
(latest) block above, which came from the surviving report `diagnose-20260728-081953`.

Read top-down, this page therefore shows 260.5 twice before reaching the correct 263.98. Nothing is
deleted — the wiki is append-merge and the chronology is the record — but any downstream use must
take 263.98. The HydroRC-vs-E-int reward delta is -1.4% (260.38 vs 263.98), not the -0.05% the
withdrawn figure implied.

[EVIDENCE: independent report-reviewer round 1 on diagnose-20260728-081953 raised this exact defect (E-int final reward cited as the crash-time 260.5 instead of the true 263.98); it was fixed by re-authoring the report from the generator, and round 2 returned APPROVE with 0 findings. Recorded in PLAN teacher-final-closeout section 12.2, HydroRC row]
[CONFIDENCE: HIGH]

