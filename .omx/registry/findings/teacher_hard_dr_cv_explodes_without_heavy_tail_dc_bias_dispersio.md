---
title: "teacher hard-DR: CV explodes without heavy-tail (DC-bias dispersion)"
tags: ["roll", "heavy-tail", "CV", "hard-DR", "env-variance"]
created: 2026-06-05T10:09:40.828564
updated: 2026-06-05T10:09:40.828564
sources: ["20260605-190606-diagnose"]
links: ["heavy_tail_vs_sample_mean_divergence_are_independent.md"]
category: pattern
confidence: high
schemaVersion: 1
---

# teacher hard-DR: CV explodes without heavy-tail (DC-bias dispersion)

Under hard DR the teacher's env-to-env CV (ss_error_std/ss_error) explodes while NO heavy-tail forms and mean stays low. CV roll 0.84(none)->2.65(hard), yaw 0.008->3.05, vz 0.00->2.35, att_norm 0.85->2.38 (omx reduce summarize --cv-field ss_error on summary.json). BUT pct_peak_gt_thresh=0% on all att/lin-vel axes (eval_adapter heavy-tail; roll peak_max hard=11.36deg < 20deg). So the spread is per-env DC-bias dispersion, NOT a few catastrophic envs. Mechanism to move for hard-DR robustness = per-env CV, not mean. See analysis 20260605-190606-diagnose teacher 260525_232805. Confirms wiki [[heavy_tail_vs_sample_mean_divergence_are_independent]].
