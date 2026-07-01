---
title: "engine-gap: flat-target eval records joint1 trajectory but renders no drift plot"
tags: ["engine-gap", "eval", "flat-target", "joint1"]
created: 2026-06-30T06:56:43.444102
updated: 2026-06-30T06:56:43.444102
sources: ["diagnose-20260627-192853", "diagnose-20260629-234023"]
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# engine-gap: flat-target eval records joint1 trajectory but renders no drift plot

[ENGINE-GAP] static --flat-target writes joint1_cmd/joint1_target/joint1_pos into data_<level>.npz (commit 4fd53e0) but renders NO joint1-drift PNG -- the eval only emits attitude/yaw/error plots, so the drift signal the flat-target mode exists to show is invisible without a hand-written plot. [WHERE] constrained_albc/analysis/eval.py run_static plot-generation block (the section that saves summary_*.png / traj_*.png after the DR-level loop); add a joint1-drift figure when args_cli.flat_target is set. [SPEC] when flat_target: render a 2-panel fig -- (a) env-mean joint1_target(t) per DR level with std band (shows settle-then-flat = no drift), (b) violin/hist of final joint1_target per env per level (shows settle-position distribution). Save as joint1_drift_flat.png in the eval dir. [EVIDENCE] this analysis had to generate joint1_drift_flat.png by hand from the npz because the eval produced none; the drift conclusion (settle 4.7-7.8s, drift-after-settle<=0.086, bimodal settle |final|>1rad 40-56%) all came from a manual script. [STATUS] proposed.

---

## Update (2026-06-29T14:47:28.119331)

[ENGINE-GAP] STILL OPEN as of diagnose-20260629-234023 (re-confirmed). static --flat-target writes joint1_cmd/joint1_target/joint1_pos/joint1_cum into data_<level>.npz but renders NO joint1-drift PNG -- only attitude/yaw/error plots. [WHERE] constrained_albc/analysis/eval.py run_static plot-generation block (after the DR-level loop); add a joint1-drift figure when args_cli.flat_target. [SPEC] when flat_target render 2-panel: (a) env-mean joint1_cum(t) per DR level + std band + +-4pi lines (settle-then-flat = no drift), (b) violin of per-env |final joint1_cum| AND of final joint1_target (settle-position distribution -- exposes bimodal park). Save joint1_drift_flat.png in eval dir. [EVIDENCE] this analysis (and the 2026-06-27 prior) both had to hand-generate the drift+settle plots from npz because the eval produced none. [STATUS] proposed.
