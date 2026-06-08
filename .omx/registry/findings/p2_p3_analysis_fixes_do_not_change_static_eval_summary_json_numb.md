---
title: "P2/P3 analysis fixes do NOT change static-eval summary.json numbers (only plots/other modes)"
tags: ["eval", "recompute", "static", "p2", "p3", "regression"]
created: 2026-06-08T03:26:24.790801
updated: 2026-06-08T03:26:24.790801
sources: ["diagnose-20260608-120155 dr_harder replot"]
links: ["static_eval_plots_regenerate_sim_free_from_npz_reconstruct_segme.md"]
category: reference
confidence: high
schemaVersion: 1
---

# P2/P3 analysis fixes do NOT change static-eval summary.json numbers (only plots/other modes)

When the eval analysis code is updated, check WHICH path changed before re-evaluating: the dr_harder campaign uses STATIC eval (recompute path), and the 2026-06-07 fixes do NOT touch it. Verified by old-vs-new diff on teacher: re-running recompute on the same npz produced 0 changed numeric fields. Why: P3 (5b732d0) edits switching.py + _eval_dr/metrics.py (periodic/segmented/switching modes) -- P3-3 actually aligned those to the recompute form, so recompute was already correct. P2 (7ce60c8) edits eval_plots.py only (display: yaw rad/s->deg/s, OOD render, lin_vel error bars) -- changes PLOTS not summary.json numbers; the static summary_*.png from recompute_plots.py was unchanged since 2026-06-06. dr_config (476c785) edits the OOD DR BUILDER (GPU-eval-time) -- irrelevant once data_ood.npz already exists. CONCLUSION: a 'plot code changed, re-evaluate dr_harder' request means REGENERATE PLOTS (sim-free, see [[static_eval_plots_regenerate_sim_free_from_npz_reconstruct_segme]]), NOT recompute summary numbers (unchanged) and NOT re-run GPU eval (npz already current incl OOD 5-level). So prior report NUMERIC conclusions stay valid; only figures (yaw deg/s, OOD level, error bars) needed correction.
