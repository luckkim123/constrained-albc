---
title: "joint1_cumulative IPO constraint generalizes (drift bounded at OOD) while the attitude tracker does not (roll OOD heavy-tail)"
tags: ["joint1", "OOD", "heavy-tail", "roll", "generalization", "drift"]
created: 2026-06-27T19:33:37.468693
updated: 2026-06-27T19:33:37.468693
sources: ["diagnose-20260628-042815"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# joint1_cumulative IPO constraint generalizes (drift bounded at OOD) while the attitude tracker does not (roll OOD heavy-tail)

In Arm B (trpo_cumul_constraint_260627_231709), the joint1 drift objective and the attitude tracker decouple at OOD. Drift stays bounded out-of-distribution (drift_slope OOD 2.2e-4 rad/s, final_abs p95 0.177 rad < budget 0.224), but roll ss_error becomes a genuine heavy-tail: per-env steady-state |roll err| OOD env-median 0.36 deg vs env-mean 3.87 deg (mean/median=10.6x), worst env 63 deg, 17/64 envs >1deg — a TAIL effect (mean>>median, rule03), NOT a population DC-shift (median barely above hard's 0.31). The tail does not align with any single physical DR factor (max Spearman-rank rho 0.30 for cog_y/payload_cog_z) = multi-factor OOD extrapolation. LESSON: a binding average-constraint can generalize OOD even when the per-step tracker's tail blows up; diagnose them separately (per-env npz steady-state, last 40% window). Evidence: report diagnose-20260628-042815 §generalization, data_ood.npz.
